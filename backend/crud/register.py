# import select
# from sqlalchemy.engine import result
import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import HTTPException, security, UploadFile
from jwt import InvalidTokenError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, result
from models.user import User
from models.notification import NotificationSetting
from schemas.user import SchemasRegister, SchemasUserData, SchemasLogin, SchemasChangeNotice
from utils import security


# 根据用户名查询数据库
async def get_user_by_id(id: int, db: AsyncSession):
    query = select(User).where(User.id == id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

# 根据id查notice表
async def get_notice_by_id(id: int, db: AsyncSession):
    query = select(NotificationSetting).where(NotificationSetting.user_id == id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 判断该邮箱是否已经注册过
async def check_user_if_open(userdata:SchemasRegister,db:AsyncSession):
    query = select(User.id).where(
        (User.email == userdata.email) | (User.name == userdata.name)
    ).limit(1)
    result=await db.execute(query)
    return result.scalar_one_or_none() is not None
# 创建用户
async def create_user(userdata:SchemasRegister,db:AsyncSession):
    # 加密密码
    hashed_password = security.get_hash_password(userdata.password)
    user=User(name=userdata.name,email=userdata.email,password_hash=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# 创建token未完善
# async def create_token(user_id:int,db:AsyncSession):
#     # 生成token+设置过期时间-> 查询数据库当前用户是否有token？有：更新，没有：添加
#     token=str(uuid.uuid4())
#     return token

from datetime import datetime, timedelta, timezone

import jwt


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY or SECRET_KEY.startswith("replace_with_"):
    raise RuntimeError("请在 backend/.env 中配置安全的 SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


def create_token(user_id: int) -> str:
    expire_time = datetime.now(timezone.utc) + timedelta(
        days=TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),  # JWT 规范中建议使用字符串
        "exp": expire_time,
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return token


# 登入
async def authenticate_user(userdata:SchemasLogin,db:AsyncSession):
    result=select(User).where(User.email==userdata.email)
    res=await db.execute(result)
    user=res.scalar_one_or_none()

    if not user:
        return None
    if not security.verify_password(userdata.password,user.password_hash):
        return None
    return user




# 根据token查用户 --使用jwt token验证因为是可以根据jwt token解密得到用户id从而得到对应用户的数据

def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        return None



# 更新用户信息：检查是否命中，获取更新后的用户返回
async def update_user_by_id(id:int,user_data:SchemasUserData,db:AsyncSession):
    # update(User).where().values(字段=值)
    # user_data是pydantic需要解包
    #没有设置值的不更新
    query=update(User).where(User.id==id).values(**user_data.model_dump(exclude_unset=True))
    result=await db.execute(query)
    await db.commit()

    if result.rowcount==0:
        raise HTTPException(status_code=404, detail="用户不存在")

    updated_user=await get_user_by_id(id,db)
    return updated_user


# 改密码-》先验证再改
async def Chage_Password(user:User,old_password:str,new_password:str,db:AsyncSession):
    if not security.verify_password(old_password,user.password_hash):
        return False
    hashed_new_password = security.get_hash_password(new_password)
    user.password_hash = hashed_new_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True


# 获取通知设置

async def Get_NotificationSetting_BY_User(id:int,db:AsyncSession):
    notice = select(NotificationSetting).where(NotificationSetting.user_id==id)
    result = await db.execute(notice)
    return result.scalar_one_or_none()


# 更新通知设置
async def Update_NotificationSetting(id:int,notice_data:SchemasChangeNotice,db:AsyncSession):
    query=update(NotificationSetting).where(NotificationSetting.user_id==id).values(**notice_data.model_dump(exclude_unset=True))
    result=await db.execute(query)
    await db.commit()

    if result.rowcount==0:
        raise HTTPException(status_code=404,detail="")
    # 根据id查用户
    updated_notice=await get_notice_by_id(id,db)
    return updated_notice


# 头像
async def update_avatar_by_user(
    user: User,
    file: UploadFile,
    db: AsyncSession,
    base_url: str,
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="只能上传图片文件",
        )

    suffix = Path(file.filename or "").suffix.lower()

    allowed_suffixes = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    }

    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=400,
            detail="不支持的图片格式",
        )

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="图片不能超过5MB",
        )

    avatar_dir = Path(__file__).resolve().parent.parent / "uploads" / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)

    old_avatar = user.avatar

    filename = f"{user.id}_{uuid.uuid4().hex}{suffix}"
    file_path = avatar_dir / filename

    file_path.write_bytes(content)

    user.avatar = (
        f"{base_url.rstrip('/')}/uploads/avatars/{filename}"
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 删除旧头像
    if old_avatar:
        old_filename = Path(
            urlparse(old_avatar).path
        ).name

        old_file_path = avatar_dir / old_filename

        if (
            old_file_path.exists()
            and old_file_path != file_path
        ):
            old_file_path.unlink()

    return user

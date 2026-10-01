"""Account HTTP endpoints: the HTTP layer delegates to ``crud.register``."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File,Request
from sqlalchemy.ext.asyncio import AsyncSession

from crud.register import (
    authenticate_user,
    create_user,
    check_user_if_open, Chage_Password, update_user_by_id, create_token, update_avatar_by_user,
)

from models.user import User
from schemas.user import PasswordUpdateRequest
from config.database import get_db
from schemas.user import SchemasRegister, SchemasLogin, SchemasUserData
from utils.jwt import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/register")
async def register(userdata: SchemasRegister, db: AsyncSession = Depends(get_db)):
    if await check_user_if_open(userdata, db):
        raise HTTPException(409, "邮箱或用户名已注册")
    user = await create_user(userdata, db)
    await db.refresh(user)
    token = create_token(user.id)
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": token,
            "userInfo": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "avatar": user.avatar,
                "phone": user.phone,
                "company": user.company,
            }
        }
    }


@router.post("/login")
async def login(userdata: SchemasLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(userdata, db)
    if not user:
        raise HTTPException(401, "邮箱或密码错误")
    token = create_token(user.id)
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": token,
            "userInfo": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "avatar": user.avatar,
                "phone": user.phone,
                "company": user.company,
            }
        }
    }


@router.get("/info")
async def info(user: User = Depends(get_current_user)):
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "phone": user.phone,
            "company": user.company,
        }
    }


@router.put("/update")
async def update_user(
        userdata: SchemasUserData,
        user: User = Depends(get_current_user),

        db: AsyncSession = Depends(get_db),
):
    await update_user_by_id(user.id, userdata, db)
    await db.commit()
    await db.refresh(user)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "phone": user.phone,
            "company": user.company,
        }
    }


@router.put("/password")
async def update_password(
        payload: PasswordUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    if not await Chage_Password(user, payload.oldPassword, payload.newPassword, db):
        raise HTTPException(400, "当前密码错误")
    await db.commit()
    return {
        "code": 200,
        "message": "密码修改成功",
        "data": None
    }


@router.post("/avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await update_avatar_by_user(
        user=user,
        file=file,
        db=db,
        base_url=str(request.base_url),
    )

    return {
        "code": 200,
        "message": "头像上传成功",
        "data": {
            "id": updated_user.id,
            "email": updated_user.email,
            "name": updated_user.name,
            "avatar": updated_user.avatar,
            "phone": updated_user.phone,
            "company": updated_user.company,
        },
    }
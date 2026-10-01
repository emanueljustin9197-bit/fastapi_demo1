
from fastapi import Depends, HTTPException, status, Header

from sqlalchemy.ext.asyncio import AsyncSession

from crud.register import decode_token, get_user_by_id
from models.user import User
from config.database import get_db



async def get_current_user(
    authorization: str=Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    # Bearer xxxxx
    # token=authorization.split(" ")[1]
    token = authorization.replace("Bearer ", "")
    user_id = decode_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已停用")
    return user
from collections.abc import AsyncGenerator
import os
from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "mysql+aiomysql://root:change_me@127.0.0.1:3306/online_form?charset=utf8mb4",
)


# 所有 Model 必须共同继承这个 Base
class Base(DeclarativeBase):
    pass


async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
)


AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session

            # 保留你的统一提交方式
            await session.commit()

        except Exception:
            await session.rollback()
            raise

        finally:
            await session.close()

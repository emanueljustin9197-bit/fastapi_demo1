"""Request bodies for user and account endpoints."""
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean


class SchemasRegister(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=32)
    name: str = Field(min_length=1, max_length=100)


class SchemasLogin(BaseModel):
    email: str
    password: str


class SchemasUserData(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    avatar: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class PasswordUpdateRequest(BaseModel):
    oldPassword: str
    newPassword: str = Field(min_length=6, max_length=32)


class SchemasChangeNotice(BaseModel):
    responseNotice: bool = False
    expirationNotice: bool = False
    exportNotice: bool = False


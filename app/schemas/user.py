from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    hashed_password: str


class UserCreate(UserBase):
    pass


class User(UserBase):

    class Config:
        from_attributes = True

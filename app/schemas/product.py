from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductBase(BaseModel):
    name: str
    description: Optional[str]
    area: Optional[str]
    regions: Optional[str]
    ingredients: Optional[str]


class ProductCreate(ProductBase):
    date_added: datetime
    user_id: int


class ProductUpdate(ProductBase):
    name: Optional[str]


class ProductMain(ProductCreate):

    class Config:
        from_attributes = True

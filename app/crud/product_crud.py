from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Product
from app.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductMain,
)


class ProductCRUD:

    @staticmethod
    def create(db: Session, obj_in: ProductCreate) -> Product:
        db_obj = Product(
            name=obj_in.name,
            description=obj_in.description,
            area=obj_in.area,
            regions=obj_in.regions,
            ingredients=obj_in.ingredients,
            date_added=obj_in.date_added,
            user_id=obj_in.user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get(db: Session, id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == id).first()

    @staticmethod
    def get_multi(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Product]:
        query = db.query(Product)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, db_obj: Product, obj_in: ProductUpdate) -> Product:
        obj_data = obj_in.model_dump()
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def search(
        db: Session,
        search_term: Optional[str] = None,
        filters: Optional[Dict[str, str]] = None,
        sorting: Optional[Dict[str, str]] = None,
    ) -> List[Product]:
        query = db.query(Product)
        if search_term:
            search_term = f"%{search_term}%"
            query = query.filter(
                Product.name.ilike(search_term) |
                Product.ingredients.ilike(search_term)
            )
        if filters:
            for column, value in filters.items():
                if hasattr(Product, column):
                    if column == "user_id":
                        query = query.filter(getattr(Product, column) == value)
                    elif column == "area":
                        query = query.filter(Product.area.ilike(value))
                    elif column == "region":
                        query = query.filter(Product.region.ilike(value))
        if sorting:
            fields = {
                "name": Product.name,
                "ingredients": Product.ingredients,
                "area": Product.area,
                "date_added": Product.date_added,
            }
            for column, value in sorting.items():
                if hasattr(Product, column):
                    if value == "asc":
                        query = query.order_by(fields[column])
                    else:
                        query = query.order_by(desc(fields[column]))
        return query.all()

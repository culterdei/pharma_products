from typing import Optional
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import (
    UserCreate,
)
from app.utils import get_password_hash, verify_password 


class UserCRUD:

    @staticmethod
    def create(db: Session, obj_in: UserCreate) -> User:
        db_obj = User(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get(db: Session, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        user = UserCRUD.check_user(db, username)
        if not user:
            return None
        is_valid = verify_password(password, user.hashed_password)
        if not is_valid:
            return None
        return user

    @staticmethod
    def check_user(db: Session, username: str) -> Optional[User]:
        user = db.query(User).filter(User.username == username).first()
        return user

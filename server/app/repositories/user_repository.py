"""
All database queries related to the User model.
No business logic here — only SQL. No HTTP concepts.
"""

from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()


def update_user_password(db: Session, user_id: int, new_hashed_password: str) -> None:
    db.query(User).filter(User.id == user_id).update({"hashed_password": new_hashed_password})
    db.commit()


def set_force_password_change(db: Session, user_id: int, value: bool) -> None:
    db.query(User).filter(User.id == user_id).update({"force_password_change": value})
    db.commit()


def set_user_active_status(db: Session, user_id: int, is_active: bool) -> None:
    db.query(User).filter(User.id == user_id).update({"is_active": is_active})
    db.commit()


def save_new_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

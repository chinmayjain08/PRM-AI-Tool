from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id                    = Column(Integer, primary_key=True, index=True)
    username              = Column(String(50), unique=True, nullable=False)
    email                 = Column(String(100), unique=True, nullable=False)
    full_name             = Column(String(100), nullable=False)
    hashed_password       = Column(String, nullable=False)
    role                  = Column(String(20), nullable=False)   # ADMIN | MANAGER | EMPLOYEE
    is_active             = Column(Boolean, default=True)
    force_password_change = Column(Boolean, default=True)
    created_at            = Column(DateTime, server_default=func.now())

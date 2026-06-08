"""
One-time bootstrap script. Creates the first Admin account and default
system config. Safe to run multiple times (idempotent).

Usage:
    python seed.py
"""

import sys
import os

# Add current folder to sys.path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.system_config import SystemConfig


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL    = "admin@prm.local"
DEFAULT_ADMIN_PASSWORD = "Admin@1234"


def create_first_admin(db) -> None:
    admin_exists = db.query(User).filter(User.role == "ADMIN").first()
    if admin_exists:
        print("Admin account already exists. Skipping.")
        return

    admin = User(
        username              = DEFAULT_ADMIN_USERNAME,
        email                 = DEFAULT_ADMIN_EMAIL,
        full_name             = "System Admin",
        hashed_password       = hash_password(DEFAULT_ADMIN_PASSWORD),
        role                  = "ADMIN",
        is_active             = True,
        force_password_change = True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin account created.")
    print(f"  Username : {DEFAULT_ADMIN_USERNAME}")
    print(f"  Password : {DEFAULT_ADMIN_PASSWORD}")
    print(f"  -> You will be asked to change this password on first login.")


def create_default_system_config(db) -> None:
    config_exists = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if config_exists:
        print("System config already exists. Skipping.")
        return

    config = SystemConfig(id=1)
    db.add(config)
    db.commit()
    print("Default system config created.")


def main() -> None:
    db = SessionLocal()
    try:
        create_first_admin(db)
        create_default_system_config(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

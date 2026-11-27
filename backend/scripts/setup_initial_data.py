"""
IdeaScope – Seed reference data and create main admin.
Owner: Member 2 (Sufiyaan Imran)

Run as: python -m scripts.setup_initial_data
Idempotent: running it twice changes nothing.
"""

from __future__ import annotations

import sys

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.seed_data import CATEGORY_NAMES, SDG_NAMES
from app.core.security import hash_password
from app.models.category import Category
from app.models.sdg import SDG
from app.models.user import User


def seed_reference_data(db: Session) -> None:
    """Upsert the 12 categories and 17 SDGs. Updates name if it changed."""
    for cat_id, name in CATEGORY_NAMES.items():
        cat = db.get(Category, cat_id)
        if cat is None:
            db.add(Category(id=cat_id, name=name))
            print(f"  [created] category {cat_id}: {name}")
        elif cat.name != name:
            cat.name = name
            print(f"  [updated] category {cat_id}: {name}")
        else:
            print(f"  [exists]  category {cat_id}: {name}")

    for number, name in SDG_NAMES.items():
        sdg = db.get(SDG, number)
        if sdg is None:
            db.add(SDG(number=number, name=name))
            print(f"  [created] SDG {number}: {name}")
        elif sdg.name != name:
            sdg.name = name
            print(f"  [updated] SDG {number}: {name}")
        else:
            print(f"  [exists]  SDG {number}: {name}")

    db.commit()


def create_main_admin(db: Session) -> None:
    """Create the main admin if one does not already exist."""
    if not settings.main_admin_email or not settings.main_admin_password:
        print("ERROR: MAIN_ADMIN_EMAIL and MAIN_ADMIN_PASSWORD must be set in .env")
        sys.exit(1)

    from sqlalchemy import select

    existing = db.scalar(select(User).where(User.is_main_admin == True))  # noqa: E712
    if existing:
        print(f"  [exists]  main admin: {existing.username} ({existing.email})")
        return

    admin = User(
        username="admin",
        full_name="Main Admin",
        email=settings.main_admin_email,
        password_hash=hash_password(settings.main_admin_password),
        role="admin",
        is_main_admin=True,
        must_change_password=True,
    )
    db.add(admin)
    db.commit()
    print(f"  [created] main admin: admin ({settings.main_admin_email})")


if __name__ == "__main__":
    print("=== IdeaScope: setup_initial_data ===")
    db = SessionLocal()
    try:
        print("\n-- Seeding reference data --")
        seed_reference_data(db)
        print("\n-- Creating main admin --")
        create_main_admin(db)
        print("\nDone.")
    finally:
        db.close()

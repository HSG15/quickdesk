import sys
from pathlib import Path

# Ensure backend directory is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import engine, SessionLocal, Base
from app.models.user import User
from app.core.security import get_password_hash


DEMO_USERS = [
    {
        "name": "Alice Support (Agent)",
        "email": "agent@quickdesk.com",
        "password": "agent123",
        "role": "agent",
    },
    {
        "name": "Bob Employee (IT User)",
        "email": "employee@quickdesk.com",
        "password": "employee123",
        "role": "employee",
    },
    {
        "name": "Charlie Finance (Employee)",
        "email": "charlie@quickdesk.com",
        "password": "employee123",
        "role": "employee",
    },
]


def seed_users():
    """
    Seeds default development users into PostgreSQL.
    Idempotent: checks for existing emails before inserting, never duplicates.
    """
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    created_count = 0
    skipped_count = 0

    try:
        for user_data in DEMO_USERS:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"  [SKIPPED] User already exists: {user_data['email']} ({existing.role})")
                skipped_count += 1
            else:
                hashed = get_password_hash(user_data["password"])
                new_user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    password_hash=hashed,
                    role=user_data["role"],
                )
                db.add(new_user)
                created_count += 1
                print(f"  [CREATED] Seeded user: {user_data['email']} ({user_data['role']})")

        db.commit()
        print(f"\nSeed complete: {created_count} users created, {skipped_count} skipped.")
    except Exception as e:
        db.rollback()
        print(f"\nSeed failed with error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("==================================================")
    print(" QuickDesk Seed Script — Users & Authentication   ")
    print("==================================================")
    seed_users()
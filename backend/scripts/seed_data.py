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
    {
        "name": "Hari (Agent)",
        "email": "hari@quickdesk.com",
        "password": "agent123",
        "role": "agent",
    }
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
    updated_count = 0

    try:
        for user_data in DEMO_USERS:
            hashed = get_password_hash(user_data["password"])
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                existing.name = user_data["name"]
                existing.role = user_data["role"]
                existing.password_hash = hashed
                print(f"  [UPDATED] User credentials sync'd: {user_data['email']} ({existing.role})")
                updated_count += 1
            else:
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
        print(f"\nUsers seed complete: {created_count} users created, {updated_count} updated.")
    except Exception as e:
        db.rollback()
        print(f"\nSeed failed with error: {e}")
        raise
    finally:
        db.close()

    # Also automatically index the knowledge base so a single seed script prepares the full system
    print("\n--------------------------------------------------")
    print(" Indexing Knowledge Base Articles into Chroma DB  ")
    print("--------------------------------------------------")
    try:
        from app.services.rag_service import index_knowledge_base
        kb_res = index_knowledge_base()
        print(f"  • Articles processed: {kb_res['articles_indexed']}")
        print(f"  • Chunks indexed: {kb_res['chunks_indexed']}")
        print("Knowledge base index is ready!\n")
    except Exception as e:
        print(f"Knowledge base indexing notice: {e}")


if __name__ == "__main__":
    print("==================================================")
    print(" QuickDesk Seed Script — Users & Knowledge Base   ")
    print("==================================================")
    seed_users()
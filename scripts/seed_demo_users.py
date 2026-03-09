"""Seed demo users for local development.

Usage:
  ENABLE_DEMO_SEED=true python scripts/seed_demo_users.py
"""

from app import app, db, seed_demo_users


def main():
    with app.app_context():
        db.create_all()
        created_count = seed_demo_users()
        print(f"Demo seed complete. Added {created_count} user(s).")


if __name__ == '__main__':
    main()

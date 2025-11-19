#!/usr/bin/env python3
"""Simple script to dump database contents (users & policies).
Respects DB_URL env (defaults to sqlite db/app.db). Usage:
    python view_db.py
or set
    export DB_URL=postgresql://postgres:password@host:5432/insurance
"""
import os
from sqlalchemy import select
from db.database import SessionLocal, engine, Base
from db.models import UserORM, PolicyORM

# Ensure tables exist (safe if already created)
Base.metadata.create_all(bind=engine)

def dump():
    with SessionLocal() as db:
        users = db.execute(select(UserORM)).scalars().all()
        policies = db.execute(select(PolicyORM)).scalars().all()
        print("Users (count=%d):" % len(users))
        for u in users:
            print(f"  - {u.username} (role={u.role})")
        print("Policies (count=%d):" % len(policies))
        for p in policies:
            print(f"  - #{p.id} {p.name} owner={p.owner} details={p.details}")

if __name__ == "__main__":
    print("DB_URL=", os.getenv("DB_URL"))
    dump()

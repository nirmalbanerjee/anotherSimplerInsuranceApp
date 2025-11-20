#!/usr/bin/env python3
"""Simple script to dump database contents (users & policies).
Respects DB_URL env (defaults to sqlite db/app.db). Usage:
    python view_db.py
or set
    export DB_URL=postgresql://postgres:password@host:5432/insurance
"""
import os, sys, argparse
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db.models import UserORM, PolicyORM

def resolve_db_url(cli_path: str | None):
    env_url = os.getenv("DB_URL")
    if env_url:
        return env_url
    if cli_path:
        return f"sqlite:///{cli_path}"
    candidates = [
        os.path.join("db", "app.db"),
        os.path.join("backend", "app.db"),
        "app.db",
    ]
    for c in candidates:
        if os.path.exists(c):
            return f"sqlite:///{c}"
    return "sqlite:///db/app.db"  # default (may create empty)

# Engine is created later inside dump(); no global create_all needed.

def dump(db_url):
    eng = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {})
    SessionLocal = sessionmaker(bind=eng)
    Base.metadata.create_all(bind=eng)
    with SessionLocal() as db:
        users = db.execute(select(UserORM)).scalars().all()
        policies = db.execute(select(PolicyORM)).scalars().all()
        print(f"Database: {db_url}")
        if not users and not policies:
            print("(empty database or wrong DB_URL)")
        print("Users (count=%d):" % len(users))
        for u in users:
            print(f"  - {u.username} (role={u.role})")
        print("Policies (count=%d):" % len(policies))
        for p in policies:
            print(f"  - #{p.id} {p.name} owner={p.owner} details={p.details}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View DB contents")
    parser.add_argument("--db", help="Path to sqlite file (overrides DB_URL)")
    args = parser.parse_args()
    db_url = resolve_db_url(args.db)
    dump(db_url)

# Local Development Guide

## Structure
```
backend/  # FastAPI API
frontend/ # React UI (served on port 3023)
db/       # Database config & ORM models
```

## Prerequisites
- Python 3.11
- Node.js 18+
- Docker (optional for containerized run)

## Backend (Local Python)
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
# Swagger: http://localhost:8000/docs
```
Default DB: SQLite db/app.db
Set Postgres:
```bash
export DB_URL=postgresql://postgres:password@localhost:5432/insurance
```

## Frontend
Simple static HTML + React via CDN OR Docker serve.
Local static:
```bash
cd frontend
npx serve . -l 3023
# Visit http://localhost:3023
```

## Docker Compose
```bash
docker compose build
docker compose up -d
# Frontend: http://localhost:3023
# Backend:  http://localhost:8000/docs
# Postgres: 5432
```
Stop:
```bash
docker compose down
```

## Tests
```bash
cd backend
pytest -q
```
All tests should pass (auth & CRUD scenarios).

## Environment Variables
Create `.env` (used manually):
```
DB_URL=postgresql://postgres:postgres@db:5432/insurance
SECRET_KEY=replace_me
```

## Common Issues
- 403 editing: must be admin.
- 422 policy create: missing fields.
- Token expiration: re-login after 30 min.

## Inspect Database
```bash
python view_db.py
# For Postgres
DB_URL=postgresql://postgres:password@localhost:5432/insurance python view_db.py
```

## Logging
Log file: `backend/logs/app.log` (rotates at 500KB, keeps 3 backups).
To view live:
```bash
tail -f backend/logs/app.log
```
Set custom log dir:
```bash
export LOG_DIR=/tmp/insurance_logs
python -m uvicorn backend.main:app --reload --port 8000
```

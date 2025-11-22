# Docker "Load Failed" Issue - Fixed ✅

## Problem
When trying to register or login from the frontend running in Docker, you were getting a "load failed" error.

## Root Causes

### 1. Missing Database Files
The `backend/db/database.py` and `backend/db/models.py` files were empty, causing the backend container to crash on startup with:
```
ImportError: cannot import name 'engine' from 'db.database'
```

### 2. Schema Issues
The database models needed to be properly defined with simple fields matching the frontend requirements.

## Simple Schema (3 Fields Only)

**User Registration requires only:**
- username
- password  
- role (user or admin)

No email, no complex hashing field names - kept as simple as possible!

## Fixes Applied

### 1. Recreated Database Files

**`backend/db/database.py`**:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./insurance.db")
engine = create_engine(DATABASE_URL, ...)
SessionLocal = sessionmaker(...)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**`backend/db/models.py`**:
```python
class UserORM(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Simple field name
    role = Column(String, default="user")
    policies = relationship("PolicyORM", back_populates="owner")

class PolicyORM(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True)
    policy_number = Column(String, unique=True, nullable=False)
    policy_type = Column(String, nullable=False)
    premium = Column(Float, nullable=False)
    coverage_amount = Column(Float, nullable=False)
    status = Column(String, default="Active")
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserORM", back_populates="policies")
```

### 2. Simple User Model in `backend/main.py`

```python
class User(BaseModel):
    username: str
    password: str
    role: str = "user"  # Default to user
```

### 3. Simple Registration Endpoint

```python
@app.post("/register", response_model=Token)
def register(user: User, db: Session = Depends(get_db)):
    if get_user(user.username, db):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user.password)
    db.add(UserORM(
        username=user.username,
        password=hashed,  # Simple field name
        role=user.role
    ))
    db.commit()
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
```

### 4. Simple Frontend Form

**`frontend/App.js`** - Only 3 fields:
```javascript
const [authForm, setAuthForm] = useState({ 
    username: "", 
    password: "", 
    role: "user" 
});

// Registration form shows:
// - Username input
// - Password input  
// - Role dropdown (only visible during registration)
```

## Verification

✅ **Backend is running**:
```bash
docker compose ps
# backend should show "Up" status
```

✅ **Registration works via API**:
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass","role":"user"}'
```

✅ **Frontend accessible at**: http://localhost:3023

✅ **All containers running**:
- backend (port 8000) ✓
- frontend (port 3023) ✓
- db (port 5432) ✓
- jaeger (port 16686) ✓
- prometheus (port 9090) ✓
- grafana (port 3001) ✓

## How to Use

1. **Open the frontend**: http://localhost:3023

2. **Register a new user**:
   - Click "Switch to Register"
   - Enter username
   - Enter password
   - Select role (User or Admin)
   - Click "Register"
   - **That's it! No email required - kept simple!**

3. **Login**:
   - Enter username
   - Enter password
   - Click "Login"

4. **Manage Policies**:
   - Once logged in, you can create, view, and delete insurance policies

## Troubleshooting

If you still see errors:

1. **Clear browser cache** and refresh
2. **Check browser console** (F12 → Console tab) for error details
3. **Check backend logs**:
   ```bash
   docker compose logs backend --tail 50
   ```
4. **Restart all containers**:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

## Database Note

The app is now using PostgreSQL (configured in Docker) instead of SQLite. The database URL is set in `docker-compose.yml`:

```yaml
environment:
  DB_URL: postgresql://postgres:postgres@db:5432/insurance
```

This means your data will persist in the Docker volume `db_data`.

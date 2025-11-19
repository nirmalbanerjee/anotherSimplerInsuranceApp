# Simple Insurance App Backend
# FastAPI + SQLite + JWT

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
import datetime

# --- Config ---
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# --- Models ---
class User(BaseModel):
    username: str
    password: str
    role: str  # 'admin' or 'user'

class InsurancePolicy(BaseModel):
    id: Optional[int]
    name: str
    details: str
    owner: str

class InsurancePolicyCreate(BaseModel):
    name: str
    details: str

class InsurancePolicyUpdate(BaseModel):
    name: Optional[str] = None
    details: Optional[str] = None
    owner: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    
class LoginBody(BaseModel):
    username: str
    password: str

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        details TEXT,
        owner TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Auth ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app = FastAPI(title="Insurance API", description="Simple insurance CRUD app", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, password, role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "password": row[1], "role": row[2]}
    return None

def authenticate_user(username, password):
    user = get_user(username)
    if not user or not verify_password(password, user["password"]):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# --- Routes ---
@app.post("/register", response_model=Token)
def register(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user.password)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (user.username, hashed, user.role))
    conn.commit()
    conn.close()
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login-json", response_model=Token)
def login_json(body: LoginBody):
    user = authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/policies", response_model=List[InsurancePolicy])
def get_policies(user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user["role"] == "admin":
        c.execute("SELECT id, name, details, owner FROM policies")
    else:
        c.execute("SELECT id, name, details, owner FROM policies WHERE owner=?", (user["username"],))
    rows = c.fetchall()
    conn.close()
    return [InsurancePolicy(id=row[0], name=row[1], details=row[2], owner=row[3]) for row in rows]

@app.post("/policies", response_model=InsurancePolicy)
def create_policy(policy: InsurancePolicyCreate, user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO policies (name, details, owner) VALUES (?, ?, ?)", (policy.name, policy.details, user["username"]))
    policy_id = c.lastrowid
    conn.commit()
    conn.close()
    return InsurancePolicy(id=policy_id, name=policy.name, details=policy.details, owner=user["username"])

@app.put("/policies/{policy_id}", response_model=InsurancePolicy)
def update_policy(policy_id: int, policy: InsurancePolicy, user: dict = Depends(get_current_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE policies SET name=?, details=?, owner=? WHERE id=?", (policy.name, policy.details, policy.owner, policy_id))
    conn.commit()
    conn.close()
    return InsurancePolicy(id=policy_id, name=policy.name, details=policy.details, owner=policy.owner)

@app.patch("/policies/{policy_id}", response_model=InsurancePolicy)
def patch_policy(policy_id: int, patch: InsurancePolicyUpdate, user: dict = Depends(get_current_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, details, owner FROM policies WHERE id=?", (policy_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Policy not found")
    current = {"id": row[0], "name": row[1], "details": row[2], "owner": row[3]}
    new_name = patch.name if patch.name is not None else current["name"]
    new_details = patch.details if patch.details is not None else current["details"]
    new_owner = patch.owner if patch.owner is not None else current["owner"]
    c.execute("UPDATE policies SET name=?, details=?, owner=? WHERE id=?", (new_name, new_details, new_owner, policy_id))
    conn.commit()
    conn.close()
    return InsurancePolicy(id=policy_id, name=new_name, details=new_details, owner=new_owner)

@app.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, user: dict = Depends(get_current_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM policies WHERE id=?", (policy_id,))
    conn.commit()
    conn.close()
    return {"detail": "Deleted"}

# --- API Docs ---
# FastAPI provides Swagger UI at /docs and OpenAPI at /openapi.json

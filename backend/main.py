# Simple Insurance App Backend
# FastAPI + SQLite + JWT

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import datetime
import os, sys, logging
from logging.handlers import RotatingFileHandler
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # add project root to path
from db.database import engine, Base, get_db  # noqa: E402
from db.models import UserORM, PolicyORM  # noqa: E402

# --- Config ---
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# DB config now in db/database.py
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# --- Models ---
class User(BaseModel):
    username: str
    password: str
    role: str

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

# ORM models moved to db/models.py

# --- DB Setup ---
Base.metadata.create_all(bind=engine)

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

# --- Logging ---
LOG_DIR = os.getenv("LOG_DIR", os.path.join(os.path.dirname(__file__), "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, "app.log")
handler = RotatingFileHandler(log_path, maxBytes=500_000, backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger("insurance")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"START {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"END {request.method} {request.url.path} status={response.status_code}")
    return response

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# get_db imported from db/database.py

def get_user(username, db: Session):
    row = db.query(UserORM).filter(UserORM.username==username).first()
    if row:
        return {"username": row.username, "password": row.password, "role": row.role}
    return None

def authenticate_user(username, password, db: Session):
    user = get_user(username, db)
    if not user or not verify_password(password, user["password"]):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    user = get_user(username, db)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# --- Routes ---
@app.post("/register", response_model=Token)
def register(user: User, db: Session = Depends(get_db)):
    if get_user(user.username, db):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user.password)
    db.add(UserORM(username=user.username, password=hashed, role=user.role))
    db.commit()
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login-json", response_model=Token)
def login_json(body: LoginBody, db: Session = Depends(get_db)):
    user = authenticate_user(body.username, body.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/policies", response_model=List[InsurancePolicy])
def get_policies(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(PolicyORM)
    if user["role"] != "admin":
        q = q.filter(PolicyORM.owner==user["username"])
    rows = q.all()
    return [InsurancePolicy(id=r.id, name=r.name, details=r.details or "", owner=r.owner) for r in rows]

@app.post("/policies", response_model=InsurancePolicy)
def create_policy(policy: InsurancePolicyCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    row = PolicyORM(name=policy.name, details=policy.details, owner=user["username"])
    db.add(row)
    db.commit()
    db.refresh(row)
    return InsurancePolicy(id=row.id, name=row.name, details=row.details or "", owner=row.owner)

@app.put("/policies/{policy_id}", response_model=InsurancePolicy)
def update_policy(policy_id: int, policy: InsurancePolicy, user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(PolicyORM).filter(PolicyORM.id==policy_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")
    row.name = policy.name
    row.details = policy.details
    row.owner = policy.owner
    db.commit()
    db.refresh(row)
    return InsurancePolicy(id=row.id, name=row.name, details=row.details or "", owner=row.owner)

@app.patch("/policies/{policy_id}", response_model=InsurancePolicy)
def patch_policy(policy_id: int, patch: InsurancePolicyUpdate, user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(PolicyORM).filter(PolicyORM.id==policy_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")
    if patch.name is not None:
        row.name = patch.name
    if patch.details is not None:
        row.details = patch.details
    if patch.owner is not None:
        row.owner = patch.owner
    db.commit()
    db.refresh(row)
    return InsurancePolicy(id=row.id, name=row.name, details=row.details or "", owner=row.owner)

@app.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(PolicyORM).filter(PolicyORM.id==policy_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(row)
    db.commit()
    return {"detail": "Deleted"}

# --- API Docs ---
# FastAPI provides Swagger UI at /docs and OpenAPI at /openapi.json

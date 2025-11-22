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
import os, sys, logging, json, uuid, time
from logging.handlers import RotatingFileHandler
from opentelemetry import trace
# Import Prometheus process collectors for CPU/Memory metrics
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import ProcessCollector, GCCollector
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # add project root to path
from db.database import engine, Base, get_db  # noqa: E402
from db.models import UserORM, PolicyORM  # noqa: E402
try:
    from backend.telemetry import (
        instrument_app, get_metrics_endpoint, record_auth_event,
        record_policy_operation, record_http_request
    )
    TELEMETRY_ENABLED = True
except ImportError:
    TELEMETRY_ENABLED = False

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
    role: str = "user"

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

# --- OpenTelemetry Instrumentation ---
if TELEMETRY_ENABLED:
    instrument_app(app)

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
class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, 'request_id'):
            base['request_id'] = record.request_id
        if hasattr(record, 'path'):
            base['path'] = record.path
        if hasattr(record, 'method'):
            base['method'] = record.method
        if hasattr(record, 'status_code'):
            base['status_code'] = record.status_code
        if hasattr(record, 'status_text'):
            base['status_text'] = record.status_text
        if hasattr(record, 'duration_ms'):
            base['duration_ms'] = record.duration_ms
        if hasattr(record, 'username'):
            base['username'] = record.username
        if hasattr(record, 'role'):
            base['role'] = record.role
        if hasattr(record, 'client_ip'):
            base['client_ip'] = record.client_ip
        if hasattr(record, 'user_agent'):
            base['user_agent'] = record.user_agent
        if hasattr(record, 'request_size'):
            base['request_size'] = record.request_size
        if hasattr(record, 'body_excerpt'):
            base['body_excerpt'] = record.body_excerpt
        return json.dumps(base)
formatter = JsonFormatter()
handler.setFormatter(formatter)
logger = logging.getLogger("insurance")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

@app.middleware("http")
async def log_requests(request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()
    rec_start = logging.LogRecord(name=logger.name, level=logging.INFO, pathname=__file__, lineno=0, msg="request.start", args=(), exc_info=None)
    rec_start.request_id = request_id
    rec_start.path = request.url.path
    rec_start.method = request.method
    # metadata
    rec_start.client_ip = request.client.host if request.client else None
    rec_start.user_agent = request.headers.get('user-agent')
    # Attempt body read (non-streaming small bodies)
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b''
    rec_start.request_size = len(body_bytes)
    # mask password fields if present
    body_text = body_bytes.decode('utf-8', errors='ignore')
    if 'password' in body_text:
        body_masked = body_text.replace('password', 'pwd')
    else:
        body_masked = body_text
    rec_start.body_excerpt = body_masked[:120]
    logger.handle(rec_start)
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    level = logging.ERROR if hasattr(response, 'status_code') and response.status_code >= 400 else logging.INFO
    rec_end = logging.LogRecord(name=logger.name, level=level, pathname=__file__, lineno=0, msg="request.end", args=(), exc_info=None)
    rec_end.request_id = request_id
    rec_end.path = request.url.path
    rec_end.method = request.method
    rec_end.status_code = response.status_code
    # Map common codes to phrases; fallback generic
    status_map = {
        200: "OK", 201: "Created", 204: "No Content",
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
        422: "Unprocessable Entity", 500: "Internal Server Error"
    }
    rec_end.status_text = status_map.get(response.status_code, "")
    rec_end.duration_ms = duration_ms
    # Add user context if token available
    username = None
    role = None
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get('sub')
            role = payload.get('role')
        except Exception:
            pass
    rec_end.username = username
    rec_end.role = role
    rec_end.client_ip = rec_start.client_ip
    rec_end.user_agent = rec_start.user_agent
    rec_end.request_size = rec_start.request_size
    rec_end.body_excerpt = rec_start.body_excerpt
    logger.handle(rec_end)
    # Record Prometheus metrics if enabled
    if TELEMETRY_ENABLED:
        duration_sec = (time.time() - start)
        record_http_request(request.method, request.url.path, response.status_code, duration_sec)
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
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "insurance-api"}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    if TELEMETRY_ENABLED:
        return get_metrics_endpoint()()
    return {"error": "Telemetry not enabled"}

@app.post("/register", response_model=Token)
def register(user: User, db: Session = Depends(get_db)):
    if get_user(user.username, db):
        if TELEMETRY_ENABLED:
            record_auth_event("register_failed", user.role)
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user.password)
    db.add(UserORM(username=user.username, password=hashed, role=user.role))
    db.commit()
    if TELEMETRY_ENABLED:
        record_auth_event("register_success", user.role)
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        if TELEMETRY_ENABLED:
            record_auth_event("login_failed", "unknown")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if TELEMETRY_ENABLED:
        record_auth_event("login_success", user["role"])
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login-json", response_model=Token)
def login_json(body: LoginBody, db: Session = Depends(get_db)):
    user = authenticate_user(body.username, body.password, db)
    if not user:
        if TELEMETRY_ENABLED:
            record_auth_event("login_failed", "unknown")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if TELEMETRY_ENABLED:
        record_auth_event("login_success", user["role"])
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/policies", response_model=List[InsurancePolicy])
def get_policies(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if TELEMETRY_ENABLED:
        record_policy_operation("list", user["role"])
    q = db.query(PolicyORM)
    if user["role"] != "admin":
        q = q.filter(PolicyORM.owner==user["username"])
    rows = q.all()
    return [InsurancePolicy(id=r.id, name=r.name, details=r.details or "", owner=r.owner) for r in rows]

@app.post("/policies", response_model=InsurancePolicy)
def create_policy(policy: InsurancePolicyCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if TELEMETRY_ENABLED:
        record_policy_operation("create", user["role"])
    
    row = PolicyORM(
        name=policy.name, 
        details=policy.details, 
        owner=user["username"]
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return InsurancePolicy(id=row.id, name=row.name, details=row.details or "", owner=row.owner)

@app.put("/policies/{policy_id}", response_model=InsurancePolicy)
def update_policy(policy_id: int, policy: InsurancePolicy, user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    if TELEMETRY_ENABLED:
        record_policy_operation("update", user["role"])
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
    if TELEMETRY_ENABLED:
        record_policy_operation("patch", user["role"])
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
    if TELEMETRY_ENABLED:
        record_policy_operation("delete", user["role"])
    row = db.query(PolicyORM).filter(PolicyORM.id==policy_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(row)
    db.commit()
    return {"detail": "Deleted"}

@app.get("/debug/error500")
def trigger_error():
    """Debug endpoint to test 500 error handling and logging"""
    raise Exception("Intentional server error for testing")

# --- API Docs ---
# FastAPI provides Swagger UI at /docs and OpenAPI at /openapi.json

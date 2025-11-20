# Insurance App API Documentation

## Base URL
Local development base: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`
OpenAPI JSON: `http://localhost:8000/openapi.json`

## Authentication
JWT Bearer tokens. Obtain token from register or login.
Include header: `Authorization: Bearer <token>` for protected endpoints.

## Endpoints Summary
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /register | No | Register new user (role: user/admin) |
| POST | /login-json | No | Login via JSON body |
| POST | /login | No | Login via form-encoded (OAuth2PasswordRequestForm) |
| GET | /policies | Yes | List policies (admin: all, user: own) |
| POST | /policies | Yes | Create a policy (name, details) owner auto-set |
| PUT | /policies/{id} | Admin | Full replace (name, details, owner) |
| PATCH | /policies/{id} | Admin | Partial update (any subset of name, details, owner) |
| DELETE | /policies/{id} | Admin | Delete policy |

## Detailed Endpoint Specs
### 1. Register
POST /register
Request (JSON):
```json
{ "username": "alice", "password": "pass", "role": "user" }
```
Response (200):
```json
{ "access_token": "<JWT>", "token_type": "bearer" }
```
Errors: 400 Username already exists

### 2. Login (JSON)
POST /login-json
Request:
```json
{ "username": "alice", "password": "pass" }
```
Response: same as register
Errors: 400 Incorrect username or password

### 3. Login (Form)
POST /login (Content-Type: application/x-www-form-urlencoded)
Body fields: `username`, `password`
Response: same as register

### 4. List Policies
GET /policies
Headers: Authorization bearer token
Response (user): only own policies
Response (admin): all policies
```json
[ { "id": 1, "name": "Life", "details": "Life coverage", "owner": "alice" } ]
```

### 5. Create Policy
POST /policies
Request:
```json
{ "name": "Health", "details": "Health coverage" }
```
Response:
```json
{ "id": 7, "name": "Health", "details": "Health coverage", "owner": "alice" }
```

### 6. Replace Policy (Admin)
PUT /policies/{id}
Request:
```json
{ "id": 7, "name": "Health Plus", "details": "Expanded", "owner": "alice" }
```
Response similar body.

### 7. Patch Policy (Admin)
PATCH /policies/{id}
Request (partial):
```json
{ "details": "Updated details" }
```
Response updated resource.

### 8. Delete Policy (Admin)
DELETE /policies/{id}
Response:
```json
{ "detail": "Deleted" }
```
Errors: 404 Policy not found

## Curl Examples
```bash
# Register user
curl -X POST http://localhost:8000/register -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass","role":"user"}'

# Login user
TOKEN=$(curl -s -X POST http://localhost:8000/login-json -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pass"}' | sed 's/.*"access_token":"\([^"]*\)".*/\1/')

# Create policy
curl -X POST http://localhost:8000/policies -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" -d '{"name":"Life","details":"Life coverage"}'

# List policies
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/policies
```

## Notes
- Use `/docs` to interact via Swagger UI.
- Tokens expire in 30 minutes by default.
- Admin role needed for PUT/PATCH/DELETE.

## Troubleshooting
- 401: Missing/invalid token.
- 403: Insufficient role (need admin).
- 422: Validation error (missing required fields).
- Reset database: delete `backend/app.db` then restart server.

## Run
Backend:
```bash
cd backend
/Users/nirmalbanerjee/anotherSimplerInsuranceApp/.venv/bin/python -m uvicorn main:app --reload
```
Frontend:
```bash
cd frontend
npx serve .
```

## Documentation Split
Detailed guides:
- Local development: `README.local.md`
- AWS deployment: `README.aws.md`

## Containerized Deployment (Docker Compose)
Ports:
- Frontend: 3000
- Backend API: 8000
- Postgres DB: 5432

### Run Locally with Docker Compose (Ports: frontend 3023, backend 8000, db 5432)
```bash
docker compose build
docker compose up -d
# Frontend: http://localhost:3000
# Backend Swagger: http://localhost:8000/docs
```
Stop:
```bash
docker compose down
```

### Environment Variables
See `.env.example` and set `DB_URL`, `SECRET_KEY` as needed.

### Migration Note
Current SQLAlchemy models auto-create tables. For production, later add Alembic.

## AWS Deployment Outline
1. Create an RDS Postgres instance (security group allowing backend ECS task access on 5432).
2. Store `DB_URL` & `SECRET_KEY` in AWS SSM Parameter Store or Secrets Manager.
3. Build & push images:
```bash
docker build -t yourrepo/insurance-backend:latest -f backend/Dockerfile .
docker build -t yourrepo/insurance-frontend:latest -f frontend/Dockerfile .
docker push yourrepo/insurance-backend:latest
docker push yourrepo/insurance-frontend:latest
```
4. Provision ECS (Fargate) services:
   - Task 1: backend (port 8000) env points to RDS DB_URL.
   - Task 2: frontend (port 3000) env REACT_APP_API_URL points to backend ALB URL.
5. Use an Application Load Balancer:
   - Listener 80/443 -> target group frontend.
   - (Optional) Add path routing `/api/*` to backend target group.
6. Configure auto scaling and CloudWatch logs.
7. Restrict inbound to DB from backend security group only.

## AWS EC2 + RDS Deployment Steps
1. RDS Postgres: create instance (e.g., db.t3.micro) database name `insurance` user `postgres` password set.
2. Security Groups:
   - RDS SG: inbound 5432 from EC2 backend SG only.
   - EC2 SG: inbound 22 (your IP), 80/443 (public), optionally 3000 if exposing frontend separately.
3. EC2 Instance: Amazon Linux 2023 or Ubuntu 22.04.
4. Install Docker:
```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
# relogin
```
5. Clone repo:
```bash
git clone https://github.com/YOURUSER/YOURREPO.git
cd YOURREPO
```
6. Create `.env` with production values:
```
DB_URL=postgresql://postgres:<PASSWORD>@<RDS_ENDPOINT>:5432/insurance
SECRET_KEY=<long_random_string>
```
7. Update `docker-compose.yml` if needed to remove db service (since using RDS) and backend DB_URL from env.
8. Run containers:
```bash
docker compose up -d --build
```
9. Reverse Proxy (optional): install nginx to route domain to backend/frontend.
10. HTTPS: use Certbot or ACM + ALB for TLS termination.

## Running Tests
Local:
```bash
cd backend
pytest -q
```
Tests cover:
- Registration & login success.
- User policy CRUD limits (403 on delete).
- Admin patch & delete flow.

### Verbose Test Mode & Request Summary
Pytest is configured (see `pytest.ini`) to emit live logs for each request with `request.start` / `request.end`. Error HTTP status codes (>=400) appear at ERROR level. At session end a summary line is printed:
```
[request summary] total=<count> errors=<error_count> avg_duration_ms=<avg>
```
Run verbosely:
```bash
pytest
```
Log format in file (`backend/logs/app.log`) is structured JSON with keys: ts, level, request_id, path, method, status_code, duration_ms.

To add more tests create files under `backend/tests/` using `TestClient`.

## Using Separate Production DB
Remove `db` service from compose and set `DB_URL` to RDS Postgres. Ensure password secret stored in AWS SSM.

## Cleanup
Stop containers:
```bash
docker compose down
```
Remove volumes:
```bash
docker compose down -v
```

## Health Checks
- Backend: GET /policies (requires auth) or root `/docs` (returns 200).
- DB: Postgres native monitoring via RDS.

## Production Hardening Suggestions
- Use a stronger `SECRET_KEY`.
- Enable HTTPS (ALB + ACM cert).
- Add rate limiting / logging middleware.
- Replace auto table creation with migrations.

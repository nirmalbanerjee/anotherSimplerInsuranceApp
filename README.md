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

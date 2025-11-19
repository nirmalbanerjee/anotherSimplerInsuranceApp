# AWS Deployment Guide

## Overview
Deploy three tiers: Frontend (port 3023), Backend API (port 8000), Managed Postgres (RDS).

## Option A: ECS Fargate (Recommended)
1. Create ECR repositories: `insurance-backend`, `insurance-frontend`.
2. Build & push images:
```bash
docker build -t insurance-backend -f backend/Dockerfile .
docker tag insurance-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/insurance-backend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/insurance-backend:latest

docker build -t insurance-frontend -f frontend/Dockerfile .
docker tag insurance-frontend:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/insurance-frontend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/insurance-frontend:latest
```
3. RDS Postgres instance (set master password, note endpoint).
4. Secrets/Parameters: store `DB_URL`, `SECRET_KEY` in SSM Parameter Store.
5. Create ECS task definitions:
   - Backend container: image backend, port 8000, env from SSM (DB_URL, SECRET_KEY).
   - Frontend container: image frontend, port 3023, env `REACT_APP_API_URL` pointing to backend ALB URL.
6. ALB setup:
   - Listener 80/443 -> target group frontend (port 3023).
   - Optional path rule `/api/*` -> backend target group (port 8000).
7. Security Groups:
   - ALB SG: inbound 80/443 public.
   - Backend SG: inbound 8000 from ALB SG only.
   - Frontend SG: inbound 3023 from ALB SG only (or public if direct).
   - RDS SG: inbound 5432 from Backend SG only.
8. Auto Scaling: configure scaling policies based on CPU for both services.
9. CloudWatch Logs: enable container logs for troubleshooting.

## Option B: EC2 + Docker Compose
1. Launch EC2 (Amazon Linux 2023) with security group allowing 22, 80, 443, 3023 (frontend), 8000 (backend) if direct.
2. Install Docker & git.
3. Clone repo; remove `db` service from `docker-compose.yml` (using RDS instead).
4. Create `.env` with:
```
DB_URL=postgresql://postgres:<PASSWORD>@<RDS_ENDPOINT>:5432/insurance
SECRET_KEY=<LONG_RANDOM>
```
5. Run:
```bash
docker compose up -d --build
```
6. (Optional) Add Nginx reverse proxy mapping `/` to frontend, `/api/` to backend.

## Health Checks
- Backend: `GET /policies` (needs auth) or `/docs` for 200.
- Frontend: Root returns HTML.
- DB: Use RDS monitoring (CPU, connections).

## Logging & Monitoring
- Enable ALB access logs (S3 bucket).
- CloudWatch log groups per task.
- Optionally integrate AWS X-Ray for tracing backend requests.

## Backup & Migrations
- Enable automated RDS backups.
- Future: add Alembic migrations before scaling.

## Security Notes
- Rotate `SECRET_KEY` periodically.
- Enforce HTTPS via ACM certificate.
- Restrict SGs to minimum necessary.
- Consider WAF on ALB for basic protection.

## Updating
Rebuild & push new images, update ECS service (force new deployment) or pull on EC2 and `docker compose up -d` again.

# Amrutam Telemedicine Backend

Production-oriented reference implementation for Amrutam's telemedicine platform.

## Stack
- Python 3.12 + FastAPI
- PostgreSQL 16
- Redis 7
- SQLAlchemy 2 + Alembic-ready structure
- JWT access tokens + RBAC
- Idempotency keys for booking/payment writes
- Docker Compose
- Pytest + GitHub Actions
- Structured logging + Prometheus metrics + OpenTelemetry hooks

## Quick start
```bash
cp .env.example .env
docker compose up --build
```
API: http://localhost:8000  
Swagger: http://localhost:8000/docs  
Health: http://localhost:8000/health

Run tests:
```bash
pip install -r requirements.txt
pytest -q
```

## Core endpoints
- `POST /auth/register`
- `POST /auth/login`
- `GET /doctors?specialty=&q=`
- `POST /doctors/{doctor_id}/slots`
- `GET /doctors/{doctor_id}/slots`
- `POST /consultations/book` — requires `Idempotency-Key`
- `GET /consultations/{id}`
- `POST /consultations/{id}/complete`
- `POST /consultations/{id}/prescriptions`
- `GET /admin/analytics`

## Production notes
This is a compact take-home implementation. For production deployment:
1. Put the API behind an API gateway/load balancer.
2. Use managed PostgreSQL with Multi-AZ and PITR.
3. Use managed Redis.
4. Store secrets in a cloud secret manager/KMS.
5. Run workers for notifications, analytics and payment reconciliation.
6. Export metrics/logs/traces to the organization's observability platform.
7. Enable PostgreSQL encryption at rest, TLS in transit, automated backups and quarterly restore drills.

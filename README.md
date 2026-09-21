# Amrutam Telemedicine Backend

Production-oriented backend implementation for Amrutam's telemedicine platform.

## Live Deployment

* **Live API:** [Amrutam Telemedicine API](https://amrutam-s-telemedicine-system.onrender.com)
* **Swagger Documentation:** [API Docs](https://amrutam-s-telemedicine-system.onrender.com/docs)
* **OpenAPI Schema:** [OpenAPI JSON](https://amrutam-s-telemedicine-system.onrender.com/openapi.json)
* **Health Check:** [Health](https://amrutam-s-telemedicine-system.onrender.com/health)
* **Metrics:** [Metrics](https://amrutam-s-telemedicine-system.onrender.com/metrics)

## Stack

* Python 3.13 + FastAPI
* PostgreSQL 16
* Redis 7
* SQLAlchemy 2
* Alembic-ready database structure
* JWT access tokens + RBAC
* Idempotency keys for booking/payment writes
* Docker + Docker Compose
* Pytest + GitHub Actions
* Structured logging
* Prometheus metrics
* OpenTelemetry hooks

## Architecture

The backend is designed around a stateless FastAPI API layer with PostgreSQL for persistent data, Redis for caching and coordination, and observability components for metrics, logs, and traces.

```text
Client
  |
  v
FastAPI API
  |
  +------------------+
  |                  |
  v                  v
PostgreSQL          Redis
  |
  v
Domain Data

        |
        v
Observability
Metrics / Logs / Traces
```

Detailed architecture documentation is available in:

```text
docs/ARCHITECTURE.md
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/AshmitaPramanick-12/Amrutam-s-telemedicine-system.git
cd Amrutam-s-telemedicine-system
```

### 2. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

For Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add the required local configuration to `.env`.

**Do not commit `.env` to Git.**

### 3. Start with Docker Compose

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Health:

```text
http://localhost:8000/health
```

## Run Without Docker

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

## Tests

Run the test suite with:

```bash
pytest -q
```

For verbose output:

```bash
pytest -v
```

Tests are located in:

```text
tests/
```

## Core Endpoints

### Authentication

```text
POST /auth/register
POST /auth/login
```

### Doctors

```text
GET  /doctors?specialty=&q=
POST /doctors/{doctor_id}/slots
GET  /doctors/{doctor_id}/slots
```

### Consultations

```text
POST /consultations/book
GET  /consultations/{id}
POST /consultations/{id}/complete
POST /consultations/{id}/prescriptions
```

The booking endpoint uses an `Idempotency-Key` to protect against duplicate booking requests.

### Administration

```text
GET /admin/analytics
```

### Observability

```text
GET /health
GET /metrics
```

## API Documentation

FastAPI provides interactive Swagger documentation:

```text
/docs
```

The generated OpenAPI specification is available at:

```text
/openapi.json
```

A standalone OpenAPI specification is also included:

```text
openapi.yaml
```

## Security

Security considerations include:

* JWT-based authentication
* Role-based access control
* Password hashing
* Request validation
* Idempotency protection for critical writes
* Environment-based secret management
* Secure handling of configuration
* Audit logging considerations
* Dependency security
* OWASP-oriented threat mitigation

The threat model is documented in:

```text
docs/THREAT_MODEL.md
```

The actual `.env` file is excluded from Git using `.gitignore`.

## Reliability and Scalability

The design considers the target requirement of approximately **100,000 daily consultations**.

Key strategies include:

* Stateless API services
* PostgreSQL transactions
* Connection pooling
* Redis caching and coordination
* Idempotent write operations
* Concurrency-safe booking design
* Horizontal API scaling
* Asynchronous processing for suitable background workloads
* Database indexing and query optimization
* Retry and backoff strategies

## Observability

The backend includes:

* Health checks
* Prometheus-compatible metrics
* Structured application logging
* OpenTelemetry instrumentation hooks

Metrics are exposed through:

```text
GET /metrics
```

## CI/CD

GitHub Actions configuration is located at:

```text
.github/workflows/ci.yml
```

The CI pipeline installs dependencies and runs automated tests to validate changes.

## Docker

Build the application image:

```bash
docker build -t amrutam-telemedicine .
```

Run the container:

```bash
docker run -p 8000:8000 amrutam-telemedicine
```

Or use Docker Compose:

```bash
docker compose up --build
```

## Project Structure

```text
amrutam-telemedicine-backend/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   └── test_api.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── THREAT_MODEL.md
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .env.example
├── .gitignore
├── .python-version
├── Dockerfile
├── docker-compose.yml
├── openapi.yaml
├── requirements.txt
└── README.md
```

## Production Notes

This is a compact take-home implementation. For a production deployment:

1. Put the API behind an API gateway or load balancer.
2. Use managed PostgreSQL with Multi-AZ deployment and point-in-time recovery.
3. Use managed Redis.
4. Store secrets in a cloud secret manager/KMS.
5. Run background workers for notifications, analytics, and payment reconciliation.
6. Export metrics, logs, and traces to the organization's observability platform.
7. Enable PostgreSQL encryption at rest and TLS in transit.
8. Configure automated backups and regularly test database restoration.
9. Apply database migrations through a controlled deployment process.
10. Implement rate limiting and centralized security monitoring at the gateway layer.

## Documentation

Additional technical documentation:

```text
docs/ARCHITECTURE.md
docs/THREAT_MODEL.md
openapi.yaml
```

## Assignment Deliverables

| Requirement           | Location                           |
| --------------------- | ---------------------------------- |
| Backend source code   | `app/`                             |
| Tests                 | `tests/`                           |
| OpenAPI specification | `openapi.yaml`                     |
| API documentation     | `/docs`                            |
| Architecture document | `docs/ARCHITECTURE.md`             |
| Threat model          | `docs/THREAT_MODEL.md`             |
| CI pipeline           | `.github/workflows/ci.yml`         |
| Docker configuration  | `Dockerfile`, `docker-compose.yml` |
| Environment template  | `.env.example`                     |
| Live deployment       | Render                             |

## Repository

[GitHub Repository](https://github.com/AshmitaPramanick-12/Amrutam-s-telemedicine-system.git)

## Author

**Ashmita Pramanick**

B.Tech Information Technology — 2026

# IntelliHall Backend

FastAPI-based REST API for the IntelliHall complaint management system.

## Tech Stack
- **Framework**: FastAPI 0.115
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Database**: PostgreSQL 16 (via asyncpg)
- **Validation**: Pydantic v2

## Project Structure

```
backend/
├── app/
│   ├── main.py              # App entry point
│   ├── ai/                  # AI/ML module (future)
│   ├── api/v1/              # API routes
│   ├── core/                # Config, security, logging
│   ├── db/                  # SQLAlchemy base + session
│   ├── models/              # ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── utils/               # Shared utilities
├── alembic/                 # DB migrations
├── uploads/                 # File uploads
└── requirements.txt
```

## Getting Started

```bash
# Copy env file and configure
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

## API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/v1/health

# IntelliHall

> Smart Hostel Complaint Management System — powered by AI

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| State | Zustand, React Query |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| AI | (Scikit-learn / Transformers — planned) |
| DevOps | Docker, docker-compose |

## Project Structure

```
IntelliHall/
├── frontend/          # Next.js 15 App Router (TypeScript)
├── backend/           # FastAPI REST API
├── docs/              # Architecture diagrams and docs
└── docker-compose.yml # Full-stack orchestration
```

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd IntelliHall

# 2. Set up environment files
cp frontend/.env.local.example frontend/.env.local
cp backend/.env.example backend/.env

# 3. Start everything with Docker
docker-compose up --build

# OR run individually:

# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
```

## Services

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

## Documentation

See [`docs/architecture.md`](./docs/architecture.md) for the full system architecture.

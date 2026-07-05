# IntelliHall — High-Level Architecture

## System Overview

IntelliHall is a smart hostel complaint management system that combines a modern web frontend, a RESTful API backend, an AI/ML inference module, and a PostgreSQL database.

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT (Browser)                       │
│          Next.js 15 · TypeScript · Tailwind CSS · shadcn/ui     │
│          Zustand (state) · React Query (data fetching)          │
└─────────────────────┬──────────────────────────────────────────┘
                      │ HTTPS / REST (Axios)
┌─────────────────────▼──────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│   /api/v1/...   ·   CORS   ·   JWT Auth   ·   Static Files     │
│                                                                 │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐ │
│  │  API Layer   │  │ Service Layer │  │     AI Module        │ │
│  │  (routers,   │→ │ (business     │  │  Priority Prediction │ │
│  │   endpoints) │  │  logic)       │  │  Duplicate Detection │ │
│  └──────────────┘  └───────┬───────┘  │  Category Predict.   │ │
│                             │          └──────────────────────┘ │
│                    ┌────────▼────────┐                          │
│                    │  Data Layer     │                          │
│                    │  SQLAlchemy 2.0 │                          │
│                    │  Alembic        │                          │
│                    └────────┬────────┘                          │
└─────────────────────────────┼──────────────────────────────────┘
                              │ asyncpg
┌─────────────────────────────▼──────────────────────────────────┐
│                     PostgreSQL 16                               │
│           UUID PKs · created_at · updated_at                   │
└────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### Frontend (`frontend/`)
| Folder | Purpose |
|---|---|
| `app/` | Next.js App Router pages and route-group layouts |
| `components/ui/` | shadcn/ui primitive components |
| `components/shared/` | Reusable application-level components |
| `lib/` | Axios instance, React Query client, cn() utility |
| `store/` | Zustand global state stores |
| `hooks/` | Custom React hooks |
| `services/` | API call functions (thin wrappers over Axios) |
| `constants/` | Enums and app-wide constants |
| `types/` | Shared TypeScript interfaces |
| `utils/` | Pure helper functions |
| `assets/` | Images and SVG icons |

### Backend (`backend/app/`)
| Folder | Purpose |
|---|---|
| `api/v1/` | FastAPI route handlers |
| `ai/` | ML model loaders and inference services |
| `core/` | Settings, security, logging |
| `db/` | SQLAlchemy Base, session, UUID/timestamp mixins |
| `models/` | ORM domain models |
| `schemas/` | Pydantic v2 request/response schemas |
| `services/` | Business logic (decoupled from routes) |
| `utils/` | Shared utility functions |

## Diagrams
See the `diagrams/` folder for visual architecture diagrams.
- `diagrams/system_overview.drawio` — System architecture (to be created)
- `diagrams/complaint_flow.drawio` — Complaint lifecycle flowchart (to be created)
- `diagrams/er_diagram.drawio` — Entity-relationship diagram (to be created)

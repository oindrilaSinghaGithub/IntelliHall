# 🏛️ IntelliHall

> **AI-powered Hall Maintenance & Wellbeing Management Platform for IIT Kharagpur**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat&logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Project Overview

IntelliHall is a full-stack web platform that digitises the entire maintenance complaint lifecycle for residential halls at IIT Kharagpur. Before IntelliHall, the hall office ran on paper slips, WhatsApp messages, and verbal follow-ups — making it impossible to track complaint status, enforce accountability, or measure resolution time.

IntelliHall replaces that with a structured, role-based workflow:

- **Students** raise complaints from their room or common areas, track real-time status, and confirm repairs via a digital completion slip.
- **Hall Admins** verify complaints, assign maintenance workers, manage schedules, and close resolved tickets.
- **The system** provides a full audit trail, in-app notifications, and a printable PDF work schedule — with AI prioritisation planned for a future release.

---

## ✨ Features

### 👨‍🎓 Student

| Feature | Description |
|---|---|
| Register & Login | JWT-based authentication with bcrypt password hashing |
| Hall Selection | Choose residential hall during registration |
| Hall Verification | Admin approves or rejects hall affiliation; student sees live status |
| Raise Complaint | Submit maintenance requests with title, description, category, priority, location, images, and preferred visit time |
| Complaint Tracking | View full complaint detail including current status and all transitions |
| Status Timeline | Chronological audit trail of every status change with actor and remarks |
| Student Confirmation | Confirm or reject a completed repair; rejection automatically reopens the complaint |
| Complaint History | Paginated list of all past and active complaints with filters |
| In-App Notifications | Real-time bell with unread count; notified when complaint is scheduled or repair is complete |

### 🛡️ Hall Admin

| Feature | Description |
|---|---|
| Hall Verification Queue | Review pending student hall affiliations; approve or reject with optional reason |
| Complaint Queue | Paginated, filterable list of all hall complaints with sort options |
| Complaint Verification | Advance complaint from `submitted` → `verified` |
| Worker Assignment | Schedule a visit with worker name, type, visit date, time slot, and remarks |
| Status Management | Drive complaints through the full FSM: verify → schedule → in-progress → complete → close |
| Completion Slip | Auto-generated digital record capturing work done and worker details |
| Student Confirmation Review | See whether the student confirmed or rejected; student comment visible |
| Close Complaint | Close only after student confirms; system enforces this guard |
| Maintenance Schedule Dashboard | View all scheduled and in-progress visits for the hall with filters |
| PDF Schedule Export | Download a printable PDF grouped by worker (powered by ReportLab) |
| In-App Notifications | Notified when a student confirms or rejects a repair |

### 🤖 AI / Smart Features

| Feature | Description |
|---|---|
| AI Priority Prediction | On complaint submission, the system automatically predicts the priority level using a rule-based weighted scoring model. The student's selected priority is preserved; the AI prediction is stored separately alongside a confidence score. Both students and hall admins can see the AI-predicted priority and confidence score on the complaint detail view. |

---

## 🔄 Complaint Workflow

```
Student Registration
        │
        ▼
Hall Verification (Admin approves / rejects)
        │
        ▼
Complaint Submitted  ──────────────────────────────────┐
        │                                               │
        ▼                                               │
     Verified  (Admin)                                  │
        │                                               │
        ▼                                               │
    Scheduled  (Admin assigns worker + date)            │ Visit Failed
        │                                               │ (Room Locked)
        ▼                                               │
  Work In Progress  (Admin starts work)                 │
        │                                               │
        ▼                                               │
    Completed  ──► auto-transition ──────────────────── ┘
        │
        ▼
Awaiting Student Confirmation
   ┌────┴────┐
   │         │
Confirm    Reject (comment required)
   │         │
   ▼         ▼
Closed    Reopened ──► auto-transition ──► Verified
                        (Admin re-schedules)
```

**Key invariants enforced by the system:**
- Scheduling requires `worker_name`, `worker_type`, and `scheduled_date` — missing fields return HTTP 422.
- Marking complete requires `work_done` text — missing returns HTTP 422.
- Closing requires student confirmation status = `confirmed` — otherwise HTTP 400.
- Rejection requires a non-empty comment — otherwise HTTP 400.

---

## 🛠️ Tech Stack

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| [Next.js](https://nextjs.org) | 16.2 | App Router, SSR, routing |
| [React](https://react.dev) | 19 | UI framework |
| [TypeScript](https://typescriptlang.org) | 5 | Type safety |
| [Tailwind CSS](https://tailwindcss.com) | 4 | Utility-first styling |
| [shadcn/ui](https://ui.shadcn.com) | — | Accessible component library (Radix UI) |
| [TanStack Query](https://tanstack.com/query) | 5 | Server state, caching, mutations |
| [Zustand](https://zustand-demo.pmnd.rs) | 5 | Client auth state |
| [React Hook Form](https://react-hook-form.com) | 7 | Form state management |
| [Zod](https://zod.dev) | 4 | Schema validation |
| [Axios](https://axios-http.com) | 1 | HTTP client with interceptors |
| [date-fns](https://date-fns.org) | 4 | Date formatting |
| [Recharts](https://recharts.org) | 3 | Charts (analytics — planned) |
| [Sonner](https://sonner.emilkowal.ski) | 2 | Toast notifications |
| [Lucide React](https://lucide.dev) | 1 | Icon library |

### Backend

| Technology | Version | Purpose |
|---|---|---|
| [FastAPI](https://fastapi.tiangolo.com) | 0.115 | Async REST API framework |
| [SQLAlchemy](https://sqlalchemy.org) | 2.0 | Async ORM with mapped columns |
| [Pydantic](https://docs.pydantic.dev) | 2.10 | Request/response validation |
| [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | 2.6 | Environment variable management |
| [Alembic](https://alembic.sqlalchemy.org) | 1.14 | Database migrations |
| [asyncpg](https://magicstack.github.io/asyncpg/) | 0.30 | Async PostgreSQL driver |
| [python-jose](https://github.com/mpdavis/python-jose) | 3.3 | JWT token encoding/decoding |
| [passlib](https://passlib.readthedocs.io) | 1.7 | bcrypt password hashing |
| [ReportLab](https://www.reportlab.com) | 4.2 | PDF generation for schedule export |
| [Uvicorn](https://www.uvicorn.org) | 0.32 | ASGI server |

### Database & Infrastructure

| Technology | Purpose |
|---|---|
| PostgreSQL 16 | Primary relational database |
| Docker + docker-compose | Full-stack containerised deployment |

### AI Architecture

The AI priority prediction layer is isolated from the rest of the application and follows a strict separation of concerns:

```
Complaint (submitted by student)
         ↓
ComplaintService  (orchestrates prediction on complaint creation)
         ↓
PriorityPredictor  (rule-based weighted scoring; returns predicted_priority + confidence)
         ↓
Repository  (persists student_priority, predicted_priority, ai_confidence)
         ↓
Database  (Complaint table — three dedicated columns)
```

The AI layer is fully isolated behind the `PriorityPredictor` interface. It can later be replaced by an ML model or an LLM without any changes to the API endpoints or the frontend — only the internals of `priority_predictor.py` need to change.

---

## 📁 Project Structure

```
IntelliHall/
├── docker-compose.yml              # Full-stack orchestration
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial.py             # users + halls tables
│   │       ├── 0002_complaint_domain.py    # complaints, images, history
│   │       ├── 0003_seed_halls.py          # IIT KGP hall seed data
│   │       ├── 0004_hall_verification.py   # verification workflow
│   │       ├── 0005_fix_admin_verification.py
│   │       ├── 0006_maintenance_workflow.py # assignments, slips, notifications
│   │       └── 0007_ai_priority_prediction.py # adds predicted_priority, ai_confidence columns
│   └── app/
│       ├── main.py                 # FastAPI app, CORS, router mount
│       ├── ai/
│       │   ├── priority_predictor.py   # Rule-based weighted scoring; returns predicted priority + confidence
│       │   └── utils.py               # Shared helpers for the AI module
│       ├── core/
│       │   ├── config.py           # Pydantic settings
│       │   ├── security.py         # JWT encode/decode, password hashing
│       │   └── logging.py
│       ├── db/
│       │   ├── base.py             # DeclarativeBase, TimestampedBase mixin
│       │   └── session.py          # Async session factory
│       ├── models/
│       │   ├── enums.py            # All domain enumerations
│       │   ├── user.py
│       │   ├── hall.py
│       │   ├── complaint.py        # Complaint, ComplaintImage, StatusHistory
│       │   ├── assignment.py       # ComplaintAssignment (worker scheduling)
│       │   ├── completion_slip.py  # CompletionSlip (digital repair record)
│       │   └── notification.py
│       ├── schemas/                # Pydantic request/response models
│       │   ├── auth.py
│       │   ├── complaint.py
│       │   ├── assignment.py
│       │   ├── completion_slip.py
│       │   ├── schedule.py
│       │   ├── notification.py
│       │   ├── hall.py
│       │   ├── user.py
│       │   └── verification.py
│       ├── repositories/           # Pure DB access layer (no business logic)
│       │   ├── complaint_repository.py
│       │   ├── assignment_repository.py
│       │   ├── completion_slip_repository.py
│       │   ├── notification_repository.py
│       │   ├── hall_repository.py
│       │   └── user_repository.py
│       ├── services/               # Business logic layer
│       │   ├── auth_service.py
│       │   ├── complaint_service.py
│       │   ├── hall_service.py
│       │   ├── notification_service.py
│       │   ├── schedule_service.py  # Schedule listing + ReportLab PDF export
│       │   └── verification_service.py
│       └── api/v1/
│           ├── router.py           # Central router registration
│           ├── dependencies/
│           │   ├── auth.py         # get_current_user dependency
│           │   └── halls.py        # require_hall_admin dependency
│           └── endpoints/
│               ├── auth.py
│               ├── complaints.py   # CRUD + status FSM + confirm/reject
│               ├── halls.py        # Hall CRUD + complaints sub-route
│               ├── schedule.py     # GET schedule + PDF export
│               ├── notifications.py
│               ├── verification.py
│               └── health.py
│
└── frontend/
    ├── next.config.ts
    ├── package.json
    └── src/
        ├── app/                    # Next.js App Router pages
        │   ├── page.tsx            # Landing page
        │   ├── login/
        │   ├── register/
        │   ├── profile/
        │   └── dashboard/
        │       ├── page.tsx        # Student dashboard
        │       ├── complaints/     # Student complaint list + detail + new
        │       └── admin/
        │           ├── page.tsx    # Admin dashboard
        │           ├── complaints/ # Admin complaint queue + detail
        │           ├── schedule/   # Maintenance schedule + PDF export
        │           └── verifications/
        ├── components/
        │   ├── admin/              # AssignmentDialog, CompletionDialog, ScheduleTable
        │   ├── shared/             # ComplaintCard, NotificationBell, StudentConfirmationCard, AIPriorityBadge, …
        │   │   └── ai-priority-badge.tsx  # Displays AI-predicted priority + confidence to students and admins
        │   └── ui/                 # shadcn/ui primitives
        ├── hooks/                  # use-complaints, use-schedule, use-notifications, …
        ├── services/               # Axios API client wrappers
        ├── types/                  # TypeScript interfaces (complaint, notification, …)
        └── store/                  # Zustand auth store
```

---

## 🗄️ Database

### Complaint Model — AI Fields

Migration `0007_ai_priority_prediction.py` adds three columns to the `complaints` table:

| Column | Type | Description |
|---|---|---|
| `student_priority` | `VARCHAR` | The priority level explicitly chosen by the student when raising the complaint |
| `predicted_priority` | `VARCHAR` (nullable) | The priority level predicted by the AI module at submission time |
| `ai_confidence` | `FLOAT` (nullable) | Confidence score for the prediction in the range `0.0 – 1.0`; `NULL` if prediction was skipped |

Both the student-selected and AI-predicted values are stored independently, so admins always have full context when triaging.

---

## 🚀 Installation

### Prerequisites

- **Node.js** ≥ 20
- **Python** 3.12
- **PostgreSQL** 16
- **Git**

---

### 1. Clone the repository

```bash
git clone https://github.com/oindrilaSinghaGithub/IntelliHall.git
cd IntelliHall
```

---

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and fill in values
cp .env.example .env
```

Edit `.env` — see [Environment Variables](#-environment-variables) below.

---

### 3. Database setup

Create the database in PostgreSQL:

```sql
CREATE DATABASE intellihall;
```

Run all Alembic migrations:

```bash
# From backend/
alembic upgrade head
```

This applies all 7 migrations, creating tables for users, halls, complaints, assignments, completion slips, notifications, and AI prediction columns, and seeds the IIT KGP hall list.

---

### 4. Run the backend

```bash
# From backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API is available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

### 5. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local   # or create manually — see below
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

### 6. Run the frontend

```bash
# From frontend/
npm run dev
```

App is available at `http://localhost:3000`

---

### 7. Docker (alternative — full stack)

```bash
# From project root
docker-compose up --build
```

This starts PostgreSQL, runs migrations, and launches both the backend and frontend.

---

## 🌐 Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI (API docs) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/api/v1/health |

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description | Example |
|---|---|---|---|
| `DATABASE_URL` | ✅ | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/intellihall` |
| `SECRET_KEY` | ✅ | JWT signing secret — use a random 32+ char string | `openssl rand -hex 32` |
| `FRONTEND_URL` | ✅ | Allowed CORS origin | `http://localhost:3000` |
| `BACKEND_URL` | ✅ | Backend base URL (for internal references) | `http://localhost:8000` |
| `UPLOAD_DIR` | ✅ | Directory for uploaded complaint images | `uploads` |
| `MODEL_DIR` | ✅ | Directory for AI model files (future use) | `app/ai/models` |
| `LOG_LEVEL` | — | Python logging level | `INFO` |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description | Example |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Base URL of the FastAPI backend | `http://localhost:8000/api/v1` |

---

## 📸 Screenshots

> Screenshots will be added here once the deployment environment is finalised.

| Screen | Preview |
|---|---|
| 🏠 Landing Page | *(coming soon)* |
| 🔑 Login / Register | *(coming soon)* |
| 👨‍🎓 Student Dashboard | *(coming soon)* |
| 📝 Raise Complaint Form | *(coming soon)* |
| 📋 Complaint Detail & Timeline | *(coming soon)* |
| ✅ Student Confirmation Card | *(coming soon)* |
| 🛡️ Admin Dashboard | *(coming soon)* |
| 📅 Maintenance Schedule | *(coming soon)* |
| 📄 PDF Schedule Export | *(coming soon)* |
| 🔔 Notification Bell | *(coming soon)* |
| 🏛️ Hall Verification Queue | *(coming soon)* |

---

## 🤖 AI Features

### ✔ AI Priority Prediction *(Implemented)*

When a student submits a complaint, the system automatically predicts the appropriate priority level:

- **Rule-based weighted scoring** — The `PriorityPredictor` analyses complaint category, description keywords, location, and historical patterns using a deterministic weighted scoring model. No external API or model file is required.
- **Confidence score** — Every prediction ships with a `0.0–1.0` confidence value, surfaced in the UI via the `AIPriorityBadge` component so students and admins can gauge reliability at a glance.
- **Explainable AI** — The scoring logic is fully transparent and readable in `priority_predictor.py`; no black-box inference.
- **Non-destructive** — The student's chosen priority is always preserved. The AI prediction is stored in a separate column (`predicted_priority`) alongside `ai_confidence`. Admins can compare both values when triaging complaints.
- **Easily replaceable** — The `PriorityPredictor` class is the only integration point. Swapping the rule-based engine for an ML model or LLM requires changes only inside `priority_predictor.py`; the API and frontend remain unchanged.

---

### Coming Soon

| Feature | Status |
|---|---|
| 🔍 AI Auto Categorization | *Coming Soon* — Automatically suggest complaint category from free-text description |
| 🪞 Duplicate Complaint Detection | *Coming Soon* — Flag semantically similar open complaints before submission |
| 📷 Image-based Classification | *Coming Soon* — Infer category and severity from uploaded complaint photos |
| 📊 Predictive Maintenance Analytics | *Coming Soon* — Surface recurring failure patterns and flag at-risk fixtures before complaints are raised |

---

## 🔮 Future Enhancements

These features are **not yet implemented** and are planned for future milestones:

| Feature | Description |
|---|---|
| 📱 QR-based Complaint Registration | Scan a QR code at a broken fixture to pre-fill location and category |
| 📧 Email / SMS Notifications | Push alerts via email and SMS in addition to in-app notifications |
| 📊 Analytics Dashboard | Charts and metrics for complaint volume, resolution time, worker performance |
| 🔧 Worker Mobile Interface | Lightweight mobile view for maintenance workers to update job status in the field |
| 📷 Image Upload | Upload complaint images directly to cloud storage |
| 🌐 Multi-language Support | Hindi and regional language interface options |

---

## 👥 Contributors

| Name | GitHub | Role |
|---|---|---|
| Oindrila Singha | [@oindrilaSinghaGithub](https://github.com/oindrilaSinghaGithub) | Full-stack lead |
| Kavya Rai | [@Vya234](https://github.com/Vya234) | Full-stack |
| Khushi Kumari | [@Khushi-Kumari030](https://github.com/Khushi-Kumari030) | Frontend |


---

## 📄 License

```
MIT License

Copyright (c) 2024 IntelliHall Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<div align="center">
  Built with ❤️ at IIT Kharagpur
</div>

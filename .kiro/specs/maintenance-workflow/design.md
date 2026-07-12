# Design Document

## Overview

This feature extends IntelliHall's complaint management system by adding worker assignment,
digital completion slips, student confirmation, schedule management, and PDF export. The
implementation follows the existing backend layered architecture (models → repositories →
services → endpoints) and the frontend layered architecture (types → services → hooks →
pages/components) without introducing new frameworks or patterns.

## Architecture

### Backend

```
app/models/          ← ORM models
  + assignment.py       (ComplaintAssignment)
  + completion_slip.py  (CompletionSlip)
  + notification.py     (Notification)
  ~ complaint.py        (add relationships)
  ~ enums.py            (add MASON, CLEANING_STAFF, REOPENED, StudentConfirmationStatus)

app/repositories/    ← Pure DB access
  + assignment_repository.py
  + completion_slip_repository.py
  + notification_repository.py

app/services/        ← Business logic
  ~ complaint_service.py   (extend update_status FSM; add confirm_repair, reject_repair)
  + notification_service.py
  + schedule_service.py

app/schemas/         ← Pydantic I/O
  + assignment.py       (AssignmentCreate, AssignmentRead)
  + completion_slip.py  (CompletionSlipRead, WorkDoneRequest)
  + notification.py     (NotificationRead, paginated wrapper)
  ~ complaint.py        (extend StatusUpdateRequest and ComplaintRead)

app/api/v1/endpoints/
  ~ complaints.py  (add confirm, reject, completion-slip endpoints)
  + schedule.py    (GET /halls/{hall_id}/schedule and /export)
  + notifications.py

app/api/v1/router.py ← register new routers

alembic/versions/0006_maintenance_workflow.py
backend/requirements.txt ← add reportlab
```

### Frontend

```
src/types/
  ~ complaint.ts        (new enum values, new interfaces)
  + notification.ts

src/services/
  ~ complaint.ts        (add confirm, reject, getCompletionSlip)
  + schedule.ts
  + notification.ts

src/hooks/
  ~ use-complaints.ts   (add confirm/reject mutations)
  + use-schedule.ts
  + use-notifications.ts

src/components/admin/
  + assignment-dialog.tsx
  + completion-dialog.tsx
  + schedule-table.tsx

src/components/shared/
  + student-confirmation-card.tsx
  + notification-bell.tsx

src/app/dashboard/admin/
  ~ page.tsx            (add schedule quick-link)
  ~ complaints/[id]/page.tsx  (integrate dialogs)
  + schedule/page.tsx

src/app/dashboard/complaints/
  ~ page.tsx            (add confirmation banner)
```

## Components and Interfaces

### New Pydantic Schemas

**`AssignmentCreate`** (in `StatusUpdateRequest` for `scheduled` transition):
```python
worker_name: str           # required
worker_type: MaintenanceType  # required
scheduled_date: date       # required
scheduled_time: str | None # optional, e.g. "10:00-12:00"
admin_remarks: str | None  # optional
```

**Extended `StatusUpdateRequest`** in `app/schemas/complaint.py`:
```python
class StatusUpdateRequest(BaseModel):
    new_status: ComplaintStatus
    remarks: str | None = None
    # Assignment fields (required only when new_status == SCHEDULED)
    worker_name: str | None = None
    worker_type: MaintenanceType | None = None
    scheduled_date: date | None = None
    scheduled_time: str | None = None
    # Completion fields (required only when new_status == COMPLETED)
    work_done: str | None = None
```

**`CompletionSlipRead`**:
```python
id, complaint_id, hall_id, room_number,
worker_name, worker_type, completion_date, work_done,
admin_remarks, student_comment,
student_confirmation_status, student_confirmation_time,
created_at, updated_at
```

**`ScheduleItemRead`**:
```python
complaint_id, complaint_title, room_number, category, status,
visit_date, scheduled_time, worker_name, worker_type, admin_remarks
```

**`NotificationRead`**:
```python
id, complaint_id, message, is_read, created_at
```

### New API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/complaints/{id}/completion-slip` | student (own) or admin (own hall) | Fetch completion slip |
| POST | `/complaints/{id}/confirm` | student (own complaint) | Confirm repair |
| POST | `/complaints/{id}/reject` | student (own complaint) | Reject repair |
| GET | `/halls/{hall_id}/schedule` | hall admin | List scheduled work |
| GET | `/halls/{hall_id}/schedule/export` | hall admin | Download PDF |
| GET | `/notifications/` | any authenticated | List own notifications |
| PATCH | `/notifications/{id}/read` | any authenticated | Mark one read |
| PATCH | `/notifications/read-all` | any authenticated | Mark all read |

### Frontend Component Interfaces

**`AssignmentDialog`**:
```typescript
interface AssignmentDialogProps {
  complaintId: string
  open: boolean
  onClose: () => void
  onSuccess: (complaint: Complaint) => void
}
```

**`CompletionDialog`**:
```typescript
interface CompletionDialogProps {
  complaintId: string
  open: boolean
  onClose: () => void
  onSuccess: (complaint: Complaint) => void
}
```

**`StudentConfirmationCard`**:
```typescript
interface StudentConfirmationCardProps {
  complaint: Complaint
  onConfirmed: () => void
  onRejected: () => void
}
```

**`NotificationBell`**:
```typescript
// No props — reads from useUnreadCount() and useNotifications() hooks
```

## Data Models

### ComplaintAssignment

```python
class ComplaintAssignment(TimestampedBase):
    __tablename__ = "complaint_assignments"
    complaint_id: Mapped[str]           # FK → complaints.id, UNIQUE
    worker_name: Mapped[str]            # VARCHAR(255) NOT NULL
    worker_type: Mapped[MaintenanceType]
    scheduled_date: Mapped[date]        # DATE NOT NULL
    scheduled_time: Mapped[str | None]  # VARCHAR(50)
    admin_remarks: Mapped[str | None]   # TEXT
    complaint: Mapped["Complaint"]      # back_populates="assignment"
```

### CompletionSlip

```python
class CompletionSlip(TimestampedBase):
    __tablename__ = "completion_slips"
    complaint_id: Mapped[str]              # FK unique
    hall_id: Mapped[str]                   # FK, denormalized for schedule queries
    room_number: Mapped[str | None]
    worker_name: Mapped[str]
    worker_type: Mapped[MaintenanceType]
    completion_date: Mapped[datetime]
    work_done: Mapped[str]                 # TEXT NOT NULL
    admin_remarks: Mapped[str | None]
    student_comment: Mapped[str | None]
    student_confirmation_status: Mapped[str]  # default "pending"
    student_confirmation_time: Mapped[datetime | None]
    complaint: Mapped["Complaint"]         # back_populates="completion_slip"
```

### Notification

```python
class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str]                   # UUID PK
    user_id: Mapped[str]              # FK → users.id
    complaint_id: Mapped[str | None]  # FK → complaints.id, SET NULL
    message: Mapped[str]              # TEXT NOT NULL
    is_read: Mapped[bool]             # default False
    created_at: Mapped[datetime]      # UTC
```

### Updated Status FSM

```
SUBMITTED → VERIFIED                             (admin)
VERIFIED → SCHEDULED                             (admin + assignment required)
SCHEDULED → IN_PROGRESS                          (admin)
IN_PROGRESS → COMPLETED (auto → WAITING_STUDENT_CONFIRMATION)  (admin + work_done required)
WAITING_STUDENT_CONFIRMATION → CLOSED            (admin, only if confirmed by student)
WAITING_STUDENT_CONFIRMATION → REOPENED → VERIFIED  (auto, when student rejects)
ANY → VISIT_FAILED_ROOM_LOCKED                   (admin)
```

## Correctness Properties

### Property 1: Assignment Uniqueness
One active assignment per complaint is enforced by a UNIQUE constraint on `complaint_id` in `complaint_assignments`. Re-scheduling deletes the old record and inserts a new one.

**Validates: Requirements 1.4, 1.5**

### Property 2: Completion Slip Uniqueness
UNIQUE constraint on `complaint_id` in `completion_slips` ensures only one slip per complaint.

**Validates: Requirements 3.1**

### Property 3: No Skip Transitions
The existing `_TRANSITIONS` dict is extended and all transitions must pass `_is_valid_transition()`. No status can be skipped.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 4: Student Ownership Check
`confirm_repair` and `reject_repair` verify `complaint.created_by == current_user.id` before making any changes.

**Validates: Requirements 4.1, 4.2**

### Property 5: Admin Close Guard
`update_status` for CLOSED checks `student_confirmation_status == "confirmed"` or raises HTTP 400.

**Validates: Requirements 5.1, 5.2**

### Property 6: Notification Safety
Notification exceptions are caught and logged without rolling back the complaint status transaction.

**Validates: Requirements 8.1, 8.2**

## Error Handling

| Scenario | HTTP Status | Message |
|----------|-------------|---------|
| Schedule without worker fields | 422 | Pydantic validation error listing missing fields |
| Mark complete without work_done | 422 | Pydantic validation error |
| Reject without comment | 400 | "A comment is required when rejecting a repair." |
| Close before student confirms | 400 | "Complaint cannot be closed: student confirmation is still pending or rejected." |
| Wrong transition | 400 | "Invalid status transition: 'X' → 'Y'. Allowed: ..." |
| Student acts on another's complaint | 403 | "You do not have permission to act on this complaint." |
| Completion slip not found | 404 | "Completion slip not found for this complaint." |
| Hall not matched | 403 | "You can only manage complaints from your own hall." |

## Testing Strategy

- **Unit (service layer)**: Test each new branch in `ComplaintService.update_status` — scheduling with/without fields, completion auto-transition, close guard, confirm, reject.
- **Integration**: Use an in-memory or test PostgreSQL database with the migrations applied; test full lifecycle end-to-end.
- **PDF**: Assert that `schedule_service.export_pdf()` returns bytes starting with `%PDF`.
- **Frontend**: Component tests for `AssignmentDialog` (validation), `StudentConfirmationCard` (confirm/reject flows), and `NotificationBell` (unread count display).

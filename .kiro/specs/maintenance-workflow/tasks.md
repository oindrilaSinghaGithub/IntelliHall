# Implementation Plan: Maintenance Assignment, Digital Completion Slip & Work Schedule

## Overview

Implementation is ordered so that each layer depends only on the layer below it.
Database schema comes first, then models, repositories, schemas, services, endpoints, and finally
the frontend. Tasks 1-6 are backend-only. Tasks 7-12 are frontend-only. Task 13 covers final
verification of the end-to-end workflow.

## Tasks

- [ ] 1. Extend enums: add `MASON`, `CLEANING_STAFF` to `MaintenanceType`; add `REOPENED` to `ComplaintStatus`; add new `StudentConfirmationStatus` enum (`PENDING`, `CONFIRMED`, `REJECTED`) in `app/models/enums.py`.

- [ ] 2. Create `app/models/assignment.py` with `ComplaintAssignment(TimestampedBase)` — fields: `complaint_id` (FK unique), `worker_name`, `worker_type` (MaintenanceType enum), `scheduled_date` (Date), `scheduled_time` (nullable VARCHAR 50), `admin_remarks` (nullable Text). Add `assignment` relationship (uselist=False, lazy=selectin) to `Complaint` model.

- [ ] 3. Create `app/models/completion_slip.py` with `CompletionSlip(TimestampedBase)` — fields: `complaint_id` (FK unique), `hall_id` (FK), `room_number`, `worker_name`, `worker_type`, `completion_date` (TIMESTAMPTZ), `work_done` (Text NOT NULL), `admin_remarks`, `student_comment`, `student_confirmation_status` (String default "pending"), `student_confirmation_time`. Add `completion_slip` relationship (uselist=False, lazy=selectin) to `Complaint` model.

- [ ] 4. Create `app/models/notification.py` with `Notification` (plain `Base`, no TimestampedBase) — fields: `id` (UUID PK), `user_id` (FK ON DELETE CASCADE), `complaint_id` (FK nullable ON DELETE SET NULL), `message` (Text), `is_read` (Boolean default False), `created_at` (TIMESTAMPTZ server-default now). Update `app/db/base.py` to import all three new models.

- [ ] 5. Create `alembic/versions/0006_maintenance_workflow.py` with upgrade() that: (a) adds `mason` and `cleaning_staff` to `maintenancetype` PG enum, (b) adds `reopened` to `complaintstatus` PG enum, (c) creates `complaint_assignments` table with all columns and indexes, (d) creates `completion_slips` table with all columns and indexes, (e) creates `notifications` table with indexes. Downgrade drops the three tables (documents that PG enum value removal requires manual steps).

- [ ] 6. Create `app/repositories/assignment_repository.py` with: `upsert(session, complaint_id, data)` that deletes any existing row for that complaint then inserts new one; `get_by_complaint_id(session, complaint_id)`.

- [ ] 7. Create `app/repositories/completion_slip_repository.py` with: `create(session, data)`, `get_by_complaint_id(session, complaint_id)`, `update(session, slip, fields_dict)`.

- [ ] 8. Create `app/repositories/notification_repository.py` with: `create(session, user_id, complaint_id, message)`, `list_for_user(session, user_id, page, page_size, unread_only)` returning `(list, total)`, `mark_read(session, notification_id, user_id)`, `mark_all_read(session, user_id)`.

- [ ] 9. Create `app/schemas/assignment.py` with `AssignmentCreate` (worker_name required, worker_type required, scheduled_date required, scheduled_time optional, admin_remarks optional) and `AssignmentRead` (+ id, complaint_id, created_at, updated_at, from_attributes=True). Create `app/schemas/completion_slip.py` with `CompletionSlipRead` (all fields, from_attributes=True). Create `app/schemas/notification.py` with `NotificationRead` and `PaginatedNotificationResponse`.

- [ ] 10. Update `app/schemas/complaint.py`: extend `StatusUpdateRequest` with optional fields `worker_name`, `worker_type`, `scheduled_date`, `scheduled_time`, `admin_remarks`, `work_done`; add `assignment: AssignmentRead | None` and `completion_slip: CompletionSlipRead | None` to `ComplaintRead`.

- [ ] 11. Create `app/services/notification_service.py` with `NotificationService.send(session, user_id, complaint_id, message)` — creates DB record, catches all exceptions and logs them so notification failures never abort the main transaction.

- [ ] 12. Create `app/services/schedule_service.py` with: `list_schedule(session, hall_id, filters, current_user)` — joins complaints + assignments where status in (SCHEDULED, IN_PROGRESS), applies optional filters, returns `list[ScheduleItemRead]`; `export_pdf(schedule_items, hall_name, export_date)` — uses reportlab to generate PDF bytes grouped by worker with room, complaint, visit date/time, and remarks.

- [ ] 13. Update `app/services/complaint_service.py` — extend `update_status`: for SCHEDULED transition validate worker fields and call `AssignmentRepository.upsert`, update `complaint.current_assignee` and `complaint.maintenance_type`, send student notification; for COMPLETED transition validate `work_done` present, create `CompletionSlip`, store status as `waiting_student_confirmation` (not `completed`), write two history entries, send student notification; for CLOSED transition check `completion_slip.student_confirmation_status == "confirmed"` or raise HTTP 400.

- [ ] 14. Add `ComplaintService.confirm_repair(session, complaint_id, current_user, comment)`: verify caller is complaint creator and status is `waiting_student_confirmation`; update slip to confirmed with timestamp and comment; send hall admin notification.

- [ ] 15. Add `ComplaintService.reject_repair(session, complaint_id, current_user, comment)`: verify caller is complaint creator, comment not empty, status is `waiting_student_confirmation`; update slip to rejected; write two history entries (`waiting_student_confirmation → reopened`, `reopened → verified`); set complaint status to VERIFIED; send hall admin notification with student comment.

- [ ] 16. Add `GET /api/v1/complaints/{id}/completion-slip`, `POST /api/v1/complaints/{id}/confirm`, and `POST /api/v1/complaints/{id}/reject` endpoints to `app/api/v1/endpoints/complaints.py`. Confirm/reject bodies: `{ "comment": "..." }` (comment optional for confirm, required for reject).

- [ ] 17. Create `app/api/v1/endpoints/schedule.py` with: `GET /halls/{hall_id}/schedule` (requires hall_admin, returns list of ScheduleItemRead with optional query filters); `GET /halls/{hall_id}/schedule/export` (requires hall_admin, calls schedule_service.export_pdf, returns StreamingResponse with application/pdf).

- [ ] 18. Create `app/api/v1/endpoints/notifications.py` with: `GET /notifications/` (paginated, authenticated user), `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`. Register both new routers in `app/api/v1/router.py` and add `reportlab` to `backend/requirements.txt`.

- [ ] 19. Update `src/types/complaint.ts`: add `"mason"` and `"cleaning_staff"` to `MaintenanceType`; add `"reopened"` to `ComplaintStatus`; add `StudentConfirmationStatus` type; add `ComplaintAssignment` and `CompletionSlip` interfaces; add optional `assignment` and `completion_slip` fields to `Complaint`. Create `src/types/notification.ts` with `Notification` and `PaginatedNotificationResponse` interfaces.

- [ ] 20. Update `src/services/complaint.ts`: add `confirmRepair(id, comment?)`, `rejectRepair(id, comment)`, `getCompletionSlip(id)` functions; update `updateComplaintStatus` to accept the extended payload shape (worker assignment fields + work_done). Create `src/services/schedule.ts` with `getSchedule(hallId, params?)` and `exportSchedulePdf(hallId, params?)` (returns Blob for download). Create `src/services/notification.ts` with `getNotifications(params?)`, `markNotificationRead(id)`, `markAllRead()`.

- [ ] 21. Update `src/hooks/use-complaints.ts`: add `useConfirmRepair()` and `useRejectRepair()` React Query mutation hooks with cache invalidation. Create `src/hooks/use-schedule.ts` with `useSchedule(hallId, filters?)` query and `useExportSchedule()` mutation. Create `src/hooks/use-notifications.ts` with `useNotifications()`, `useUnreadCount()` (refetchInterval 30000ms), `useMarkNotificationRead()`, `useMarkAllRead()`.

- [ ] 22. Create `src/components/admin/assignment-dialog.tsx`: modal with Worker Name (text input required), Worker Type (select with all 9 types, required), Visit Date (date input required), Time Slot (text optional), Remarks (textarea optional). Validates all required fields client-side. On submit calls `updateComplaintStatus` with `new_status: "scheduled"` + assignment fields. Shows loading state.

- [ ] 23. Create `src/components/admin/completion-dialog.tsx`: modal with Work Done (textarea required, describes what was repaired) and Admin Remarks (textarea optional). Shows note: "The complaint will automatically move to Awaiting Student Confirmation." On submit calls `updateComplaintStatus` with `new_status: "completed"` + `work_done`.

- [ ] 24. Create `src/components/admin/schedule-table.tsx`: table with columns Visit Date, Worker, Type, Room, Complaint Title, Status, Category. Filter bar with date picker, worker name text, worker type select, category select. Row click navigates to complaint detail.

- [ ] 25. Update the complaint detail page at `src/app/dashboard/admin/complaints/[id]/page.tsx` to: trigger `AssignmentDialog` when admin selects `scheduled` from status dropdown; trigger `CompletionDialog` when admin selects `completed`; show an "Assignment" info section when `complaint.assignment` is present; show a "Completion Slip" section when `complaint.completion_slip` is present.

- [ ] 26. Create `src/app/dashboard/admin/schedule/page.tsx`: fetches data with `useSchedule`; renders `ScheduleTable`; "Export PDF" button calls `useExportSchedule`, creates temporary anchor element with blob URL to trigger download; loading skeleton while fetching; nav back to admin dashboard.

- [ ] 27. Update `src/app/dashboard/admin/page.tsx`: add a quick-link card for "Work Schedule" linking to `/dashboard/admin/schedule` using `CalendarDays` or `Wrench` icon from lucide-react.

- [ ] 28. Create `src/components/shared/student-confirmation-card.tsx`: prominent card shown when `complaint.status === "waiting_student_confirmation"`. Shows complaint title, room, worker name and type (from completion slip), and work done. "Confirm Repair" button (green) with optional comment input; "Report Issue" button (destructive red) opens modal with mandatory comment textarea. Uses `useConfirmRepair` and `useRejectRepair` hooks.

- [ ] 29. Update `src/app/dashboard/complaints/page.tsx`: at the top of the list, show `StudentConfirmationCard` for every complaint with `status === "waiting_student_confirmation"`. Update `src/components/shared/complaint-card.tsx` to show a "⚠ Confirm Required" badge when status is `waiting_student_confirmation`.

- [ ] 30. Create `src/components/shared/notification-bell.tsx`: bell icon button showing red badge with unread count from `useUnreadCount()`. Click toggles a dropdown with last 10 notifications from `useNotifications()`. Each item shows message, relative time, link to complaint. "Mark all read" action at bottom calls `useMarkAllRead()`. Update `src/components/shared/navbar.tsx` to include `NotificationBell` for both student and admin views.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "wave": 1,
      "tasks": [1],
      "description": "Enum extensions — no dependencies"
    },
    {
      "wave": 2,
      "tasks": [2, 3, 4],
      "description": "New ORM models — depend on updated enums (task 1)"
    },
    {
      "wave": 3,
      "tasks": [5],
      "description": "Alembic migration — depends on all models being defined (tasks 1-4)"
    },
    {
      "wave": 4,
      "tasks": [6, 7, 8],
      "description": "Repositories — depend on migration (task 5)"
    },
    {
      "wave": 5,
      "tasks": [9, 10],
      "description": "Pydantic schemas — depend on repositories and models (tasks 1-8)"
    },
    {
      "wave": 6,
      "tasks": [11, 12],
      "description": "New services — depend on schemas and repositories (tasks 6-10)"
    },
    {
      "wave": 7,
      "tasks": [13, 14, 15],
      "description": "Updated complaint service — depends on new services (tasks 11-12)"
    },
    {
      "wave": 8,
      "tasks": [16, 17, 18],
      "description": "API endpoints — depend on services (tasks 13-15)"
    },
    {
      "wave": 9,
      "tasks": [19, 20],
      "description": "Frontend types and services — depend on finalized API (task 18)"
    },
    {
      "wave": 10,
      "tasks": [21],
      "description": "Frontend hooks — depend on services (task 20)"
    },
    {
      "wave": 11,
      "tasks": [22, 23, 24, 28],
      "description": "UI components — depend on hooks (task 21)"
    },
    {
      "wave": 12,
      "tasks": [25, 26, 29, 30],
      "description": "Pages — depend on components (tasks 22-24, 28)"
    },
    {
      "wave": 13,
      "tasks": [27],
      "description": "Admin dashboard link — depends on schedule page existing (task 26)"
    }
  ]
}
```

## Notes

- **Alembic enum extension**: PostgreSQL does not support removing enum values once added. The
  `downgrade()` function for migration 0006 drops the three new tables but cannot remove the added
  enum values. A comment in the migration documents this limitation.
- **COMPLETED vs WAITING_STUDENT_CONFIRMATION**: When the admin sends `new_status: "completed"`,
  the API stores the final status as `waiting_student_confirmation`. Two history rows are written:
  `in_progress → completed` and `completed → waiting_student_confirmation`. This preserves the
  intent (admin marked it done) while enforcing the student confirmation step.
- **PDF library**: `reportlab` is the chosen library. If it is already in `requirements.txt`, skip
  the addition. The PDF uses only basic `canvas` API to keep the implementation simple.
- **Notification failures**: Wrapped in try/except inside `NotificationService.send`. A failed
  notification must never roll back the complaint status change.
- **Re-scheduling**: If a complaint is re-scheduled after rejection (admin schedules again), the
  `upsert` in `AssignmentRepository` replaces the previous assignment row for that complaint_id.

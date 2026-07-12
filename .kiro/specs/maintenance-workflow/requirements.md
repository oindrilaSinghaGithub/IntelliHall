# Requirements Document

## Introduction

This feature enhances IntelliHall's complaint management system to digitize the full maintenance
workflow used in IIT Kharagpur hostels. Currently complaints can move through statuses, but the
backend lacks worker assignment, digital completion slips, student confirmation, schedule management,
and PDF export. This spec adds complete backend and frontend support for the lifecycle:

**Verified → Scheduled → Work In Progress → Completed → Awaiting Student Confirmation → Closed**

The backend is FastAPI + SQLAlchemy async + PostgreSQL + Alembic. The frontend is Next.js 14 with
React Query, Zustand, Tailwind CSS, and shadcn/ui. All new code must follow existing patterns.

## Requirements

### Requirement 1: Worker Assignment on Scheduling

**User Story:** As a Hall Admin, when I move a complaint from verified to scheduled, I must be
required to provide worker assignment details so the maintenance visit is properly tracked.

#### Acceptance Criteria

- [ ] 1.1 `PATCH /api/v1/complaints/{id}/status` with `new_status: "scheduled"` MUST require `worker_name` (string, non-empty) and `worker_type` (enum) in the request body. If either is absent, the API returns HTTP 422.
- [ ] 1.2 `worker_type` must accept: `electrician`, `plumber`, `carpenter`, `mason`, `cleaning_staff`, `civil`, `network`, `housekeeping`, `other`. The values `mason` and `cleaning_staff` are new additions to the existing `MaintenanceType` enum.
- [ ] 1.3 `scheduled_date` (date string, required) must be provided. `scheduled_time` (optional) and `admin_remarks` (optional) may also be supplied.
- [ ] 1.4 All assignment fields are stored in a new `complaint_assignments` table linked to the complaint.
- [ ] 1.5 If the complaint is not in `verified` status when scheduling is attempted, return HTTP 400 with a clear message.
- [ ] 1.6 The existing `current_assignee` and `maintenance_type` fields on the `complaints` table MUST also be populated from the assignment data for backwards compatibility.

### Requirement 2: Restricted Admin-Only Status Transitions

**User Story:** As a Hall Admin, I must be the only one who can move complaints through the
admin-controlled chain. Students must not trigger these transitions.

#### Acceptance Criteria

- [ ] 2.1 Only users with `role = hall_admin` may call `PATCH /complaints/{id}/status` for transitions in the admin chain: `submitted → verified → scheduled → in_progress → completed`.
- [ ] 2.2 When a Hall Admin marks a complaint `completed`, the system MUST automatically transition it to `waiting_student_confirmation` in the same request. The API stores it as `waiting_student_confirmation`, not `completed`.
- [ ] 2.3 The `closed` status transition may only be performed by a Hall Admin, and only when `student_confirmation_status` on the completion slip is `confirmed`.
- [ ] 2.4 All existing transition validations (hall scoping, FSM rules) remain in effect.

### Requirement 3: Digital Completion Slip

**User Story:** As a Hall Admin, after marking a repair complete, I want a digital record replacing
the paper slip that captures the work done, providing a permanent audit trail.

#### Acceptance Criteria

- [ ] 3.1 When a complaint transitions to `waiting_student_confirmation`, a `completion_slips` record is automatically created with: `complaint_id`, `hall_id`, `room_number`, `worker_name`, `worker_type`, `completion_date`, `work_done`, `admin_remarks`, `student_comment` (null), `student_confirmation_status` (default "pending"), `student_confirmation_time` (null).
- [ ] 3.2 `work_done` must be supplied in the request body when transitioning to `completed`. If absent, return HTTP 422.
- [ ] 3.3 The completion slip is exposed via `GET /api/v1/complaints/{id}/completion-slip`.
- [ ] 3.4 Only the complaint creator (student) or the hall admin of that hall may fetch the slip.

### Requirement 4: Student Confirmation

**User Story:** As a student, when a repair is marked complete, I want to confirm or reject the
repair from my dashboard so I can report if the issue persists.

#### Acceptance Criteria

- [ ] 4.1 `POST /api/v1/complaints/{id}/confirm` — Student confirms the repair. Only callable by the complaint creator. Complaint must be in `waiting_student_confirmation`. Optional `comment` field. Sets `student_confirmation_status = confirmed` and records timestamp.
- [ ] 4.2 `POST /api/v1/complaints/{id}/reject` — Student rejects the repair. Comment is mandatory. Sets `student_confirmation_status = rejected`. Automatically transitions the complaint: `waiting_student_confirmation → reopened → verified`. Notifies hall admin.
- [ ] 4.3 The student's complaints list page shows a prominent "Awaiting Your Confirmation" card for any complaint in `waiting_student_confirmation` status.
- [ ] 4.4 `ComplaintStatus` enum gains a `reopened` value. The final resting state after rejection is `verified` so the admin can re-schedule.

### Requirement 5: Admin Closing Logic

**User Story:** As a Hall Admin, I want to close a confirmed complaint to mark it as fully resolved.

#### Acceptance Criteria

- [ ] 5.1 `PATCH /complaints/{id}/status` with `new_status: "closed"` is only valid when `student_confirmation_status = confirmed` on the completion slip AND caller is hall_admin for that hall.
- [ ] 5.2 Attempting to close without student confirmation returns HTTP 400: "Complaint cannot be closed: student confirmation is still pending or rejected."

### Requirement 6: Upcoming Assigned Work Page

**User Story:** As a Hall Admin, I want a page showing all scheduled maintenance visits so I can
plan and coordinate the workload.

#### Acceptance Criteria

- [ ] 6.1 New endpoint `GET /api/v1/halls/{hall_id}/schedule` returns complaints with status `scheduled` or `in_progress` for the hall, including their assignment details.
- [ ] 6.2 Response includes per complaint: `visit_date`, `worker_name`, `worker_type`, `hall_id`, `room_number`, `complaint_title`, `status`, `category`, `complaint_id`.
- [ ] 6.3 Supports query filters: `scheduled_date` (exact date), `worker_name` (partial match), `worker_type` (enum), `category` (enum). All filters optional.
- [ ] 6.4 New frontend page at `/dashboard/admin/schedule` renders the schedule as a sortable table.
- [ ] 6.5 The admin dashboard includes a quick-link to the schedule page.

### Requirement 7: PDF Export of Work Schedule

**User Story:** As a Hall Admin, I want to export the current work schedule as a printable PDF to
share with maintenance workers.

#### Acceptance Criteria

- [ ] 7.1 New endpoint `GET /api/v1/halls/{hall_id}/schedule/export` returns a PDF file with `Content-Type: application/pdf` and `Content-Disposition: attachment`.
- [ ] 7.2 PDF groups entries by worker, showing hall, room, complaint title, visit date/time, and admin remarks.
- [ ] 7.3 The same query filters from Req 6.3 apply to narrow the export.
- [ ] 7.4 Frontend schedule page has an "Export PDF" button that triggers a browser file download.
- [ ] 7.5 The PDF library used is `reportlab`, added to `backend/requirements.txt`.

### Requirement 8: Notifications

**User Story:** As a student or admin, I want to be notified when the complaint status changes in
ways that require my attention.

#### Acceptance Criteria

- [ ] 8.1 Notify student (in-app DB notification) when: complaint is scheduled (include worker name and visit date), and when complaint transitions to `waiting_student_confirmation`.
- [ ] 8.2 Notify Hall Admin (in-app DB notification) when: student confirms a repair, and when student rejects a repair (include student comment).
- [ ] 8.3 Notifications stored in a `notifications` table: `id`, `user_id` (FK), `complaint_id` (FK nullable), `message` (text), `is_read` (bool, default false), `created_at`.
- [ ] 8.4 New endpoints: `GET /api/v1/notifications/` (paginated list), `PATCH /api/v1/notifications/{id}/read` (mark one), `PATCH /api/v1/notifications/read-all` (mark all).
- [ ] 8.5 Frontend shows an unread notification count badge in the nav bar for both student and admin.

### Requirement 9: Database Changes

**User Story:** As a system maintainer, I need all schema changes captured in a single clean
Alembic migration.

#### Acceptance Criteria

- [ ] 9.1 New enum values `mason` and `cleaning_staff` added to existing `maintenancetype` PostgreSQL enum.
- [ ] 9.2 New enum value `reopened` added to existing `complaintstatus` PostgreSQL enum.
- [ ] 9.3 New table `complaint_assignments`: `id` UUID PK, `complaint_id` UNIQUE FK, `worker_name`, `worker_type`, `scheduled_date` DATE, `scheduled_time` VARCHAR(50) nullable, `admin_remarks` TEXT nullable, `created_at`, `updated_at`.
- [ ] 9.4 New table `completion_slips`: `id` UUID PK, `complaint_id` UNIQUE FK, `hall_id` FK, `room_number` nullable, `worker_name`, `worker_type`, `completion_date` TIMESTAMPTZ, `work_done` TEXT, `admin_remarks` nullable, `student_comment` nullable, `student_confirmation_status` VARCHAR(20) default 'pending', `student_confirmation_time` nullable, `created_at`, `updated_at`.
- [ ] 9.5 New table `notifications`: `id` UUID PK, `user_id` FK, `complaint_id` FK nullable SET NULL, `message` TEXT, `is_read` BOOLEAN default false, `created_at` TIMESTAMPTZ.
- [ ] 9.6 A single Alembic migration `0006_maintenance_workflow.py` implements all changes with proper `upgrade()` and `downgrade()`.

## Glossary

- **Assignment**: The record of which worker is assigned to handle a complaint, including scheduled date.
- **Completion Slip**: Digital replacement for the paper slip; captures work done and student confirmation.
- **Student Confirmation**: The student's action of confirming or rejecting that a repair was completed satisfactorily.
- **Schedule**: The list of all scheduled/in-progress maintenance visits visible to the Hall Admin.
- **Reopened**: An intermediate complaint status used when a student rejects a repair, before it reverts to `verified`.
- **MaintenanceType**: Enum describing the type of maintenance worker (electrician, plumber, etc.).

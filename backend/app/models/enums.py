"""
IntelliHall — Domain Enumerations

Defines all SQLAlchemy-compatible Python enums used across ORM models.
Import from here rather than defining inline to keep models clean.
"""

import enum


# ---------------------------------------------------------------------------
# User enums
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    """
    Roles a user can hold within the system.

    - STUDENT    : A regular hall resident who can raise complaints.
    - HALL_ADMIN : A hall administrator who manages and resolves complaints.
    """

    STUDENT = "student"
    HALL_ADMIN = "hall_admin"


# ---------------------------------------------------------------------------
# Complaint enums
# ---------------------------------------------------------------------------


class ComplaintType(str, enum.Enum):
    """Whether the complaint relates to a personal room or a shared area."""

    PERSONAL = "personal"
    COMMON_AREA = "common_area"


class ComplaintCategory(str, enum.Enum):
    """Broad maintenance category that determines which team handles the work."""

    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    CARPENTRY = "carpentry"
    CIVIL = "civil"
    INTERNET = "internet"
    CLEANLINESS = "cleanliness"
    WATER = "water"
    FURNITURE = "furniture"
    OTHER = "other"


class ComplaintPriority(str, enum.Enum):
    """Urgency level assigned to a complaint."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintStatus(str, enum.Enum):
    """
    Lifecycle state of a complaint.

    Typical flow:
      SUBMITTED → VERIFIED → SCHEDULED → IN_PROGRESS
      → COMPLETED → WAITING_STUDENT_CONFIRMATION → CLOSED
      (or → VISIT_FAILED_ROOM_LOCKED → re-scheduled)
    """

    SUBMITTED = "submitted"
    VERIFIED = "verified"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING_STUDENT_CONFIRMATION = "waiting_student_confirmation"
    CLOSED = "closed"
    VISIT_FAILED_ROOM_LOCKED = "visit_failed_room_locked"


class MaintenanceType(str, enum.Enum):
    """Type of maintenance worker required to resolve the complaint."""

    ELECTRICIAN = "electrician"
    PLUMBER = "plumber"
    CARPENTER = "carpenter"
    CIVIL = "civil"
    NETWORK = "network"
    HOUSEKEEPING = "housekeeping"
    OTHER = "other"

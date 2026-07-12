# IntelliHall ORM Models
# All model classes must be imported here so that Alembic's autogenerate
# can detect every table when it inspects Base.metadata.
# Import order: independent models first, then dependent ones.

from app.models.enums import (  # noqa: F401
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
    HallVerificationStatus,
    MaintenanceType,
    StudentConfirmationStatus,
    UserRole,
)
from app.models.hall import Hall  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.complaint import (  # noqa: F401
    Complaint,
    ComplaintImage,
    ComplaintStatusHistory,
)
from app.models.assignment import ComplaintAssignment  # noqa: F401
from app.models.completion_slip import CompletionSlip  # noqa: F401
from app.models.notification import Notification  # noqa: F401

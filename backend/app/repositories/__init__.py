# IntelliHall — Repository Layer
# Repositories are responsible for database access only.
# No business logic or HTTP concerns belong here.

from app.repositories.complaint_repository import ComplaintRepository  # noqa: F401
from app.repositories.hall_repository import HallRepository  # noqa: F401
from app.repositories.user_repository import UserRepository  # noqa: F401

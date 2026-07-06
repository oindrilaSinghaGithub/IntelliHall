# IntelliHall — Repository Layer
# Repositories are responsible for database access only.
# No business logic or HTTP concerns belong here.

from app.repositories.complaint_repository import ComplaintRepository  # noqa: F401

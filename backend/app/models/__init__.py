# IntelliHall ORM Models
# All model classes must be imported here so that Alembic's autogenerate
# can detect every table when it inspects Base.metadata.
# Import order: independent models first, then dependent ones.

from app.models.enums import UserRole  # noqa: F401
from app.models.hall import Hall  # noqa: F401
from app.models.user import User  # noqa: F401

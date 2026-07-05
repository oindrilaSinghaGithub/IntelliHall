"""
IntelliHall — Domain Enumerations

Defines all SQLAlchemy-compatible Python enums used across ORM models.
Import from here rather than defining inline to keep models clean.
"""

import enum


class UserRole(str, enum.Enum):
    """
    Roles a user can hold within the system.

    - STUDENT    : A regular hall resident who can raise complaints.
    - HALL_ADMIN : A hall administrator who manages and resolves complaints.
    """

    STUDENT = "student"
    HALL_ADMIN = "hall_admin"

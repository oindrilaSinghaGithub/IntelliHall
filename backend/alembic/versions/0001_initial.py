"""create halls and users tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-06 01:14:00.000000

This migration creates the two foundational tables:
  - halls  : residential halls / hostels
  - users  : platform users (students and hall admins)

It also creates the `userrole` PostgreSQL ENUM type used by the users table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# sqlalchemy.dialects.postgresql.ENUM is used instead of the generic sa.Enum
# because sa.Enum's DDL compiler re-emits CREATE TYPE inline during
# op.create_table() if the type has not been tracked in the compiler's memo
# dict for the current session — even when create_type=False is set. That flag
# only suppresses the standalone .create() call on sa.Enum, not the implicit
# inline emission during table DDL.
#
# The PostgreSQL-native ENUM type unconditionally skips all DDL when
# create_type=False is set, giving full manual control over the type lifecycle.
# The type is created/dropped explicitly via op.execute(sa.text(...)), which
# routes correctly through the active async migration connection.
userrole_enum = PGEnum("student", "hall_admin", name="userrole", create_type=False)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # -- userrole ENUM -------------------------------------------------------
    # Use raw DDL instead of userrole_enum.create(op.get_bind(), ...) because
    # op.get_bind() is deprecated and returns None with async engines, which
    # causes the .create() call to silently no-op and then SQLAlchemy emits a
    # second CREATE TYPE during op.create_table(), producing DuplicateObjectError.
    op.execute(sa.text("CREATE TYPE userrole AS ENUM ('student', 'hall_admin')"))

    # -- halls ---------------------------------------------------------------
    op.create_table(
        "halls",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key."),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Full display name of the hall (e.g. 'Tagore Hall')."),
        sa.Column("code", sa.String(length=20), nullable=False, comment="Short uppercase identifier for the hall (e.g. 'TH')."),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_halls_id"), "halls", ["id"], unique=False)
    op.create_index(op.f("ix_halls_name"), "halls", ["name"], unique=True)
    op.create_index(op.f("ix_halls_code"), "halls", ["code"], unique=True)

    # -- users ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False, comment="UUID primary key."),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Full display name of the user."),
        sa.Column("email", sa.String(length=320), nullable=False, comment="Unique login e-mail address."),
        sa.Column("password_hash", sa.String(length=1024), nullable=False, comment="Bcrypt / argon2 hashed password — never store plaintext."),
        sa.Column("role", userrole_enum, nullable=False, comment="Role of the user within the system."),
        sa.Column("hall_id", sa.String(length=36), nullable=True, comment="FK to the hall this user belongs to."),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["hall_id"], ["halls.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_hall_id"), "users", ["hall_id"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_hall_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_halls_code"), table_name="halls")
    op.drop_index(op.f("ix_halls_name"), table_name="halls")
    op.drop_index(op.f("ix_halls_id"), table_name="halls")
    op.drop_table("halls")

    # Drop the enum type after both tables are gone (no column references it).
    # Same reasoning as upgrade(): use raw DDL instead of op.get_bind().
    op.execute(sa.text("DROP TYPE IF EXISTS userrole"))

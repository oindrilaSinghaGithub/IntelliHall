"""Add hall verification fields to users table

Revision ID: 0004_hall_verification
Revises: 0003_seed_halls
Create Date: 2026-07-12 12:00:00.000000

Changes
-------
1. Create ``hallverificationstatus`` PostgreSQL enum type
   (pending | approved | rejected)

2. ALTER TABLE users ADD COLUMN:
   - roll_number              VARCHAR(50)   nullable
   - room_number              VARCHAR(20)   nullable
   - hall_verification_status hallverificationstatus NOT NULL DEFAULT 'pending'
   - verified_by_admin_id     VARCHAR(36)   nullable, FK → users.id
   - hall_verified_at         TIMESTAMPTZ   nullable
   - hall_rejection_reason    VARCHAR(1000) nullable

3. Seed existing users as 'approved' so the new workflow does not
   disrupt any accounts that were created before this migration ran.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------
# Revision chain
# ---------------------------------------------------------------------------

revision: str = "0004_hall_verification"
down_revision: str | None = "0003_seed_halls"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # 1. Create the enum type
    hall_verification_status_enum = sa.Enum(
        "pending",
        "approved",
        "rejected",
        name="hallverificationstatus",
        create_type=True,
    )
    hall_verification_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add new columns to the users table
    op.add_column(
        "users",
        sa.Column(
            "roll_number",
            sa.String(50),
            nullable=True,
            comment="Student roll number (e.g. 21CS10001). Display only.",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "room_number",
            sa.String(20),
            nullable=True,
            comment="Student's room number within the hall (e.g. B-302).",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "hall_verification_status",
            sa.Enum(
                "pending",
                "approved",
                "rejected",
                name="hallverificationstatus",
                create_type=False,   # already created above
            ),
            nullable=False,
            server_default="pending",
            comment="Whether this student's hall affiliation has been verified.",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "verified_by_admin_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="FK to the Hall Admin who last approved/rejected this student.",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "hall_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp of the most recent verification action.",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "hall_rejection_reason",
            sa.String(1000),
            nullable=True,
            comment="Optional rejection reason set by the Hall Admin.",
        ),
    )

    # 3. Create index for verification status queries
    op.create_index(
        "ix_users_hall_verification_status",
        "users",
        ["hall_verification_status"],
    )

    # 4. Backfill existing users as 'approved' so they are not disrupted
    op.execute(
        "UPDATE users SET hall_verification_status = 'approved' "
        "WHERE hall_verification_status = 'pending'"
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    op.drop_index("ix_users_hall_verification_status", table_name="users")
    op.drop_column("users", "hall_rejection_reason")
    op.drop_column("users", "hall_verified_at")
    op.drop_column("users", "verified_by_admin_id")
    op.drop_column("users", "hall_verification_status")
    op.drop_column("users", "room_number")
    op.drop_column("users", "roll_number")

    # Drop the enum type only after all columns referencing it are gone
    sa.Enum(name="hallverificationstatus").drop(op.get_bind(), checkfirst=True)

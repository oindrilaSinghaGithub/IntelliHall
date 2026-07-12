"""Add maintenance workflow tables and enum values

Revision ID: 0006_maintenance_workflow
Revises: 0005_fix_admin_verification
Create Date: 2026-07-12 14:30:00.000000

Changes
-------
1. Add 'mason' and 'cleaning_staff' to maintenancetype enum
2. Add 'reopened' to complaintstatus enum
3. CREATE TABLE complaint_assignments
4. CREATE TABLE completion_slips
5. CREATE TABLE notifications
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision chain
# ---------------------------------------------------------------------------

revision: str = "0006_maintenance_workflow"
down_revision: str | None = "0005_fix_admin_verification"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # 1. Add new values to maintenancetype enum
    op.execute("ALTER TYPE maintenancetype ADD VALUE IF NOT EXISTS 'mason'")
    op.execute("ALTER TYPE maintenancetype ADD VALUE IF NOT EXISTS 'cleaning_staff'")

    # 2. Add new value to complaintstatus enum
    op.execute("ALTER TYPE complaintstatus ADD VALUE IF NOT EXISTS 'reopened'")

    # 3. Create complaint_assignments table
    op.create_table(
        "complaint_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("worker_name", sa.String(255), nullable=False),
        sa.Column(
            "worker_type",
            postgresql.ENUM(
                "electrician", "plumber", "carpenter", "mason", "cleaning_staff",
                "civil", "network", "housekeeping", "other",
                name="maintenancetype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.String(50), nullable=True),
        sa.Column("admin_remarks", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_complaint_assignments_complaint_id",
        "complaint_assignments",
        ["complaint_id"],
    )
    op.create_index(
        "ix_complaint_assignments_scheduled_date",
        "complaint_assignments",
        ["scheduled_date"],
    )

    # 4. Create completion_slips table
    op.create_table(
        "completion_slips",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "hall_id",
            sa.String(36),
            sa.ForeignKey("halls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("room_number", sa.String(20), nullable=True),
        sa.Column("worker_name", sa.String(255), nullable=False),
        sa.Column(
            "worker_type",
            postgresql.ENUM(
                "electrician", "plumber", "carpenter", "mason", "cleaning_staff",
                "civil", "network", "housekeeping", "other",
                name="maintenancetype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "completion_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("work_done", sa.Text(), nullable=False),
        sa.Column("admin_remarks", sa.Text(), nullable=True),
        sa.Column("student_comment", sa.Text(), nullable=True),
        sa.Column(
            "student_confirmation_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("student_confirmation_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_completion_slips_complaint_id",
        "completion_slips",
        ["complaint_id"],
    )
    op.create_index(
        "ix_completion_slips_hall_id",
        "completion_slips",
        ["hall_id"],
    )

    # 5. Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_complaint_id", "notifications", ["complaint_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("notifications")
    op.drop_table("completion_slips")
    op.drop_table("complaint_assignments")

    # Note: PostgreSQL does not support removing enum values once added.
    # The new enum values ('mason', 'cleaning_staff', 'reopened') will remain
    # in the database after downgrade. To fully remove them, you would need to:
    # 1. Drop all columns using the enum type
    # 2. Drop and recreate the enum type without those values
    # 3. Re-add the columns
    # This is not implemented here as it's complex and rarely needed in practice.

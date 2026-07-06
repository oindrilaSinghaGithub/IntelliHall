"""create complaint domain tables

Revision ID: 0002_complaint_domain
Revises: 0001_initial
Create Date: 2026-07-06 01:26:00.000000

Creates the complaint domain:
  - 5 new PostgreSQL ENUM types
  - complaints             table
  - complaint_images       table
  - complaint_status_history table
  - All FK constraints
  - All performance indexes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------

revision: str = "0002_complaint_domain"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# ENUM helpers
#
# PGEnum (sqlalchemy.dialects.postgresql.ENUM) is used instead of sa.Enum
# because the generic sa.Enum DDL compiler re-emits CREATE TYPE inline during
# op.create_table() when the type has not been recorded in the compiler's memo
# dict — even when create_type=False is set.  That flag only suppresses the
# standalone .create() call on sa.Enum; it does NOT suppress the implicit
# inline emission during table DDL.
#
# PGEnum unconditionally skips all DDL when create_type=False, giving full
# manual control over the type lifecycle.  Each type is created/dropped once
# via op.execute(sa.text(...)), which routes correctly through the active async
# migration connection (avoiding the deprecated op.get_bind() which returns
# None with async engines and silently no-ops .create()/.drop()).
# ---------------------------------------------------------------------------

complainttype_enum = PGEnum(
    "personal",
    "common_area",
    name="complainttype",
    create_type=False,
)

complaintcategory_enum = PGEnum(
    "electrical",
    "plumbing",
    "carpentry",
    "civil",
    "internet",
    "cleanliness",
    "water",
    "furniture",
    "other",
    name="complaintcategory",
    create_type=False,
)

complaintpriority_enum = PGEnum(
    "low",
    "medium",
    "high",
    "critical",
    name="complaintpriority",
    create_type=False,
)

complaintstatus_enum = PGEnum(
    "submitted",
    "verified",
    "scheduled",
    "in_progress",
    "completed",
    "waiting_student_confirmation",
    "closed",
    "visit_failed_room_locked",
    name="complaintstatus",
    create_type=False,
)

maintenancetype_enum = PGEnum(
    "electrician",
    "plumber",
    "carpenter",
    "civil",
    "network",
    "housekeeping",
    "other",
    name="maintenancetype",
    create_type=False,
)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # -- Create ENUM types (exactly once, before any table references them) --
    op.execute(sa.text("CREATE TYPE complainttype AS ENUM ('personal', 'common_area')"))
    op.execute(sa.text(
        "CREATE TYPE complaintcategory AS ENUM ("
        "'electrical', 'plumbing', 'carpentry', 'civil', 'internet', "
        "'cleanliness', 'water', 'furniture', 'other')"
    ))
    op.execute(sa.text(
        "CREATE TYPE complaintpriority AS ENUM ('low', 'medium', 'high', 'critical')"
    ))
    op.execute(sa.text(
        "CREATE TYPE complaintstatus AS ENUM ("
        "'submitted', 'verified', 'scheduled', 'in_progress', 'completed', "
        "'waiting_student_confirmation', 'closed', 'visit_failed_room_locked')"
    ))
    op.execute(sa.text(
        "CREATE TYPE maintenancetype AS ENUM ("
        "'electrician', 'plumber', 'carpenter', 'civil', 'network', "
        "'housekeeping', 'other')"
    ))

    # -- complaints ----------------------------------------------------------
    op.create_table(
        "complaints",
        # PK + timestamps (mirrors TimestampedBase)
        sa.Column(
            "id",
            sa.String(36),
            primary_key=True,
            nullable=False,
            comment="UUID primary key.",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        # Core fields
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
            comment="Short summary entered by the student.",
        ),
        sa.Column(
            "description",
            sa.Text,
            nullable=False,
            comment="Detailed description of the issue.",
        ),
        sa.Column(
            "complaint_type",
            complainttype_enum,
            nullable=False,
            comment="PERSONAL or COMMON_AREA.",
        ),
        sa.Column(
            "category",
            complaintcategory_enum,
            nullable=False,
            comment="Maintenance category.",
        ),
        sa.Column(
            "priority",
            complaintpriority_enum,
            nullable=False,
            server_default="medium",
            comment="Urgency level.",
        ),
        sa.Column(
            "status",
            complaintstatus_enum,
            nullable=False,
            server_default="submitted",
            comment="Current lifecycle status.",
        ),
        sa.Column(
            "maintenance_type",
            maintenancetype_enum,
            nullable=True,
            comment="Type of maintenance worker assigned.",
        ),
        sa.Column(
            "current_assignee",
            sa.String(255),
            nullable=True,
            comment="Name of the current assignee or contractor.",
        ),

        # Personal-complaint location
        sa.Column(
            "room_number",
            sa.String(20),
            nullable=True,
            comment="Room number for PERSONAL complaints.",
        ),

        # Common-area location
        sa.Column("block", sa.String(50), nullable=True),
        sa.Column("floor", sa.String(10), nullable=True),
        sa.Column("common_area", sa.String(100), nullable=True),
        sa.Column("qr_location_id", sa.String(100), nullable=True),

        # Scheduling
        sa.Column(
            "preferred_visit_time",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        # Foreign keys
        sa.Column(
            "hall_id",
            sa.String(36),
            sa.ForeignKey("halls.id", ondelete="CASCADE"),
            nullable=False,
            comment="Parent hall.",
        ),
        sa.Column(
            "created_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="Student who raised the complaint.",
        ),
    )

    # Single-column indexes
    op.create_index("ix_complaints_id",         "complaints", ["id"],         unique=False)
    op.create_index("ix_complaints_status",      "complaints", ["status"],     unique=False)
    op.create_index("ix_complaints_priority",    "complaints", ["priority"],   unique=False)
    op.create_index("ix_complaints_category",    "complaints", ["category"],   unique=False)
    op.create_index("ix_complaints_hall_id",     "complaints", ["hall_id"],    unique=False)
    op.create_index("ix_complaints_created_by",  "complaints", ["created_by"], unique=False)
    op.create_index("ix_complaints_created_at",  "complaints", ["created_at"], unique=False)

    # Composite indexes (from __table_args__ in the ORM model)
    op.create_index(
        "ix_complaints_hall_id_status",
        "complaints",
        ["hall_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_complaints_created_by_status",
        "complaints",
        ["created_by", "status"],
        unique=False,
    )

    # -- complaint_images ----------------------------------------------------
    op.create_table(
        "complaint_images",
        sa.Column(
            "id",
            sa.String(36),
            primary_key=True,
            nullable=False,
            comment="UUID primary key.",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            nullable=False,
            comment="Parent complaint.",
        ),
        sa.Column(
            "image_url",
            sa.String(1024),
            nullable=False,
            comment="URL to the stored image file.",
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="UTC timestamp when the image was uploaded.",
        ),
    )
    op.create_index(
        "ix_complaint_images_id",           "complaint_images", ["id"],           unique=False
    )
    op.create_index(
        "ix_complaint_images_complaint_id", "complaint_images", ["complaint_id"], unique=False
    )

    # -- complaint_status_history --------------------------------------------
    op.create_table(
        "complaint_status_history",
        sa.Column(
            "id",
            sa.String(36),
            primary_key=True,
            nullable=False,
            comment="UUID primary key.",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "complaint_id",
            sa.String(36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            nullable=False,
            comment="Parent complaint.",
        ),
        sa.Column(
            "previous_status",
            complaintstatus_enum,
            nullable=True,
            comment="Status before the transition (NULL for initial entry).",
        ),
        sa.Column(
            "new_status",
            complaintstatus_enum,
            nullable=False,
            comment="Status after the transition.",
        ),
        sa.Column(
            "updated_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="User who triggered this transition.",
        ),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="UTC time of the transition.",
        ),
    )
    op.create_index(
        "ix_csh_id",           "complaint_status_history", ["id"],           unique=False
    )
    op.create_index(
        "ix_csh_complaint_id", "complaint_status_history", ["complaint_id"], unique=False
    )
    op.create_index(
        "ix_csh_updated_by",   "complaint_status_history", ["updated_by"],   unique=False
    )
    op.create_index(
        "ix_csh_timestamp",    "complaint_status_history", ["timestamp"],     unique=False
    )


# ---------------------------------------------------------------------------
# Downgrade  — drop in reverse dependency order
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # complaint_status_history
    op.drop_index("ix_csh_timestamp",    table_name="complaint_status_history")
    op.drop_index("ix_csh_updated_by",   table_name="complaint_status_history")
    op.drop_index("ix_csh_complaint_id", table_name="complaint_status_history")
    op.drop_index("ix_csh_id",           table_name="complaint_status_history")
    op.drop_table("complaint_status_history")

    # complaint_images
    op.drop_index("ix_complaint_images_complaint_id", table_name="complaint_images")
    op.drop_index("ix_complaint_images_id",           table_name="complaint_images")
    op.drop_table("complaint_images")

    # complaints
    op.drop_index("ix_complaints_created_by_status", table_name="complaints")
    op.drop_index("ix_complaints_hall_id_status",    table_name="complaints")
    op.drop_index("ix_complaints_created_at",        table_name="complaints")
    op.drop_index("ix_complaints_created_by",        table_name="complaints")
    op.drop_index("ix_complaints_hall_id",           table_name="complaints")
    op.drop_index("ix_complaints_category",          table_name="complaints")
    op.drop_index("ix_complaints_priority",          table_name="complaints")
    op.drop_index("ix_complaints_status",            table_name="complaints")
    op.drop_index("ix_complaints_id",                table_name="complaints")
    op.drop_table("complaints")

    # ENUM types — drop in reverse creation order, after all tables are gone
    op.execute(sa.text("DROP TYPE IF EXISTS maintenancetype"))
    op.execute(sa.text("DROP TYPE IF EXISTS complaintstatus"))
    op.execute(sa.text("DROP TYPE IF EXISTS complaintpriority"))
    op.execute(sa.text("DROP TYPE IF EXISTS complaintcategory"))
    op.execute(sa.text("DROP TYPE IF EXISTS complainttype"))

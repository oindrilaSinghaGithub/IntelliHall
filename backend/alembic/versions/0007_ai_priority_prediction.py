"""Add AI priority prediction columns to complaints

Revision ID: 0007_ai_priority_prediction
Revises: 0006_maintenance_workflow
Create Date: 2026-07-15 14:00:00.000000

Changes
-------
1. ADD COLUMN complaints.predicted_priority  (complaintpriority enum, nullable)
2. ADD COLUMN complaints.ai_confidence       (DOUBLE PRECISION, nullable)

Both columns are nullable so existing complaint rows are not affected and
no back-fill is required.  The AI predictor will populate them going forward
on every new complaint submission.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision chain
# ---------------------------------------------------------------------------

revision: str = "0007_ai_priority_prediction"
down_revision: str | None = "0006_maintenance_workflow"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    # 1. Add predicted_priority column — reuses the existing complaintpriority enum type
    op.add_column(
        "complaints",
        sa.Column(
            "predicted_priority",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                "critical",
                name="complaintpriority",
                create_type=False,  # type already exists
            ),
            nullable=True,
            comment="AI-predicted urgency level (may differ from student-selected priority).",
        ),
    )

    # 2. Add ai_confidence column — plain float, no enum needed
    op.add_column(
        "complaints",
        sa.Column(
            "ai_confidence",
            sa.Float(),
            nullable=True,
            comment="Prediction confidence score in range [0.0, 1.0].",
        ),
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    op.drop_column("complaints", "ai_confidence")
    op.drop_column("complaints", "predicted_priority")

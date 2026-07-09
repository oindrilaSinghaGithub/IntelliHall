"""seed halls of residence alphabetically

Revision ID: 0003_seed_halls
Revises: 0002_complaint_domain
Create Date: 2026-07-09 18:06:00.000000

"""

from collections.abc import Sequence
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "0003_seed_halls"
down_revision: str | None = "0002_complaint_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Insert halls if they don't already exist, ordered alphabetically
    halls_to_insert = [
        {"name": "Azad Hall of Residence", "code": "AZAD"},
        {"name": "Meghnad Saha Hall of Residence", "code": "MSHR"},
        {"name": "Mother Teresa Hall of Residence", "code": "MTHR"},
        {"name": "Patel Hall of Residence", "code": "PATEL"},
        {"name": "Radha Krishna Hall of Residence", "code": "RKHR"},
        {"name": "Rajendra Prasad Hall of Residence", "code": "RPHR"},
        {"name": "Sarojini Naidu – Indira Gandhi Hall of Residence", "code": "SNIG"},
        {"name": "Sister Nivedita Hall of Residence", "code": "SNHR"},
    ]

    bind = op.get_bind()
    for hall in halls_to_insert:
        # Check if the hall already exists in the table to prevent duplication
        result = bind.execute(
            sa.text("SELECT id FROM halls WHERE name = :name"),
            {"name": hall["name"]},
        )
        if not result.fetchone():
            bind.execute(
                sa.text(
                    "INSERT INTO halls (id, name, code, created_at, updated_at) "
                    "VALUES (:id, :name, :code, :created_at, :updated_at)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "name": hall["name"],
                    "code": hall["code"],
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )


def downgrade() -> None:
    # Delete the seeded halls during downgrade
    halls_to_delete = [
        "Azad Hall of Residence",
        "Meghnad Saha Hall of Residence",
        "Mother Teresa Hall of Residence",
        "Patel Hall of Residence",
        "Radha Krishna Hall of Residence",
        "Rajendra Prasad Hall of Residence",
        "Sarojini Naidu – Indira Gandhi Hall of Residence",
        "Sister Nivedita Hall of Residence",
    ]
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM halls WHERE name IN :names"),
        {"names": tuple(halls_to_delete)},
    )

"""Fix Hall Admin hall_verification_status — set to approved

Revision ID: 0005_fix_admin_verification
Revises: 0004_hall_verification
Create Date: 2026-07-12 12:48:00.000000

Problem
-------
Migration 0004 backfilled ALL existing users to 'approved', which was
correct.  However, any Hall Admin who registered *after* 0004 was applied
(before this service-layer fix) would have been given 'pending' status
because the model default was PENDING.

This migration corrects all such rows so that:
  - All users with role = 'hall_admin'  → hall_verification_status = 'approved'
  - Students are left untouched.

This is idempotent: running it against a clean database or one where
admins are already 'approved' has no negative effect.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005_fix_admin_verification"
down_revision: str | None = "0004_hall_verification"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Set all Hall Admin accounts to 'approved', clearing rejection artefacts
    op.execute(
        """
        UPDATE users
        SET
            hall_verification_status = 'approved',
            hall_rejection_reason    = NULL
        WHERE
            role = 'hall_admin'
            AND hall_verification_status != 'approved'
        """
    )


def downgrade() -> None:
    # Reversing this would incorrectly set admins back to pending — not safe.
    # Intentional no-op: downgrade is not supported for data-fix migrations.
    pass

"""Stub for missing revision a19f54cd93ab

Revision ID: a19f54cd93ab
Revises: e3fbcccbe2c4
Create Date: 2025-12-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a19f54cd93ab'
down_revision = 'e3fbcccbe2c4'   # adjust only if you know a different parent revision
branch_labels = None
depends_on = None


def upgrade():
    # NO-OP stub: real migration file was lost but schema changes are already applied.
    # If you later restore the real migration, remove this stub.
    pass


def downgrade():
    pass

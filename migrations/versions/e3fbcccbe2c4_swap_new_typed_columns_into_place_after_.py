"""Swap new typed columns into place after backfill

Revision ID: e3fbcccbe2c4
Revises: 561ac1eeadcb
Create Date: <keep whatever alembic generated>
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3fbcccbe2c4'
down_revision = '561ac1eeadcb'
branch_labels = None
depends_on = None

def upgrade():
    # Drop old textual columns first (so we don't attempt an alter/cast)
    with op.batch_alter_table('workstation_asset') as batch_op:
        for col in ['cores', 'vram', 'storage_capacity1', 'storage_capacity2', 'po_date', 'warranty_start', 'warranty_expiry']:
            try:
                batch_op.drop_column(col)
            except Exception:
                # ignore if column missing
                pass

    # Rename new typed columns into place
    with op.batch_alter_table('workstation_asset') as batch_op:
        batch_op.alter_column('cores_new', new_column_name='cores')
        batch_op.alter_column('vram_new', new_column_name='vram')
        batch_op.alter_column('storage_capacity1_new', new_column_name='storage_capacity1')
        batch_op.alter_column('storage_capacity2_new', new_column_name='storage_capacity2')
        batch_op.alter_column('po_date_new', new_column_name='po_date')
        batch_op.alter_column('warranty_start_new', new_column_name='warranty_start')
        batch_op.alter_column('warranty_expiry_new', new_column_name='warranty_expiry')


def downgrade():
    # Reverse: rename typed columns back to *_new, then recreate textual columns as nullable text
    with op.batch_alter_table('workstation_asset') as batch_op:
        batch_op.alter_column('cores', new_column_name='cores_new')
        batch_op.alter_column('vram', new_column_name='vram_new')
        batch_op.alter_column('storage_capacity1', new_column_name='storage_capacity1_new')
        batch_op.alter_column('storage_capacity2', new_column_name='storage_capacity2_new')
        batch_op.alter_column('po_date', new_column_name='po_date_new')
        batch_op.alter_column('warranty_start', new_column_name='warranty_start_new')
        batch_op.alter_column('warranty_expiry', new_column_name='warranty_expiry_new')

    with op.batch_alter_table('workstation_asset') as batch_op:
        for col, typ in [('cores', sa.String(length=10)), ('vram', sa.String(length=10)),
                         ('storage_capacity1', sa.String(length=20)), ('storage_capacity2', sa.String(length=20)),
                         ('po_date', sa.String(length=20)), ('warranty_start', sa.String(length=20)),
                         ('warranty_expiry', sa.String(length=20))]:
            try:
                batch_op.add_column(sa.Column(col, typ, nullable=True))
            except Exception:
                pass

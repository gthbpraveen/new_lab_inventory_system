
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '561ac1eeadcb'
down_revision = '139d326004c2'  # keep whatever is already present in file
branch_labels = None
depends_on = None

def upgrade():
    # Add JSON/Text columns for processors/gpus
    try:
        op.add_column('workstation_asset', sa.Column('processors', postgresql.JSON(), nullable=True))
        op.add_column('workstation_asset', sa.Column('gpus', postgresql.JSON(), nullable=True))
    except Exception:
        op.add_column('workstation_asset', sa.Column('processors', sa.Text(), nullable=True))
        op.add_column('workstation_asset', sa.Column('gpus', sa.Text(), nullable=True))

    # Add filename & created_at (non-destructive)
    op.add_column('workstation_asset', sa.Column('po_invoice_filename', sa.String(length=250), nullable=True))
    op.add_column('workstation_asset', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Add NEW typed columns (suffix _new) — safe, no ALTER on existing data
    op.add_column('workstation_asset', sa.Column('cores_new', sa.Integer(), nullable=True))
    op.add_column('workstation_asset', sa.Column('vram_new', sa.Integer(), nullable=True))
    op.add_column('workstation_asset', sa.Column('storage_capacity1_new', sa.Integer(), nullable=True))
    op.add_column('workstation_asset', sa.Column('storage_capacity2_new', sa.Integer(), nullable=True))

    op.add_column('workstation_asset', sa.Column('po_date_new', sa.Date(), nullable=True))
    op.add_column('workstation_asset', sa.Column('warranty_start_new', sa.Date(), nullable=True))
    op.add_column('workstation_asset', sa.Column('warranty_expiry_new', sa.Date(), nullable=True))

    # workstation_assignment created_at if needed
    op.add_column('workstation_assignment', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    # drop what we added (reverse)
    op.drop_column('workstation_assignment', 'created_at')

    op.drop_column('workstation_asset', 'warranty_expiry_new')
    op.drop_column('workstation_asset', 'warranty_start_new')
    op.drop_column('workstation_asset', 'po_date_new')

    op.drop_column('workstation_asset', 'storage_capacity2_new')
    op.drop_column('workstation_asset', 'storage_capacity1_new')
    op.drop_column('workstation_asset', 'vram_new')
    op.drop_column('workstation_asset', 'cores_new')

    op.drop_column('workstation_asset', 'created_at')
    op.drop_column('workstation_asset', 'po_invoice_filename')

    try:
        op.drop_column('workstation_asset', 'gpus')
        op.drop_column('workstation_asset', 'processors')
    except Exception:
        pass

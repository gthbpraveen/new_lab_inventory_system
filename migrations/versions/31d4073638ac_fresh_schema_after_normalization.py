"""Fresh schema after normalization

Revision ID: 31d4073638ac
Revises: 
Create Date: 2025-08-06 11:17:44.854931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31d4073638ac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('remarks', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('mac_address', sa.String(length=50), nullable=True))
        batch_op.alter_column('manufacturer', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('model', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('location', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('po_date', existing_type=sa.VARCHAR(length=20), nullable=True)
        batch_op.alter_column('purchase_date', existing_type=sa.VARCHAR(length=20), nullable=True)
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=20), nullable=True)
        batch_op.alter_column('intender_name', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('quantity', existing_type=sa.INTEGER(), nullable=True)
        batch_op.alter_column('department_code', existing_type=sa.VARCHAR(length=100), nullable=True)
        batch_op.alter_column('assigned_by', existing_type=sa.VARCHAR(length=150), type_=sa.String(length=100), existing_nullable=True)
        batch_op.create_unique_constraint('uq_equipment_serial_number', ['serial_number'])  # ✅ named

    with op.batch_alter_table('equipment_history', schema=None) as batch_op:
        batch_op.alter_column('assigned_by', existing_type=sa.VARCHAR(length=120), type_=sa.String(length=100), existing_nullable=True)
        # ✅ Skip dropping FK blindly — only create FK
        batch_op.create_foreign_key('fk_equipment_history_assigned_to_roll', 'student', ['assigned_to_roll'], ['roll'])

    with op.batch_alter_table('workstation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mac_address', sa.String(length=50), nullable=True))
        batch_op.alter_column('roll', existing_type=sa.VARCHAR(length=20), nullable=False)
        batch_op.create_foreign_key('fk_workstation_roll', 'student', ['roll'], ['roll'])
        batch_op.drop_column('year')
        batch_op.drop_column('id')
        batch_op.drop_column('phone')
        batch_op.drop_column('course')
        batch_op.drop_column('email')
        batch_op.drop_column('name')
        batch_op.drop_column('faculty')
        batch_op.drop_column('staff_incharge')


def downgrade():
    with op.batch_alter_table('workstation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('staff_incharge', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('faculty', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('course', sa.VARCHAR(length=20), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.VARCHAR(length=20), nullable=True))
        batch_op.add_column(sa.Column('id', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('year', sa.VARCHAR(length=10), nullable=True))
        batch_op.drop_constraint('fk_workstation_roll', type_='foreignkey')
        batch_op.alter_column('roll', existing_type=sa.VARCHAR(length=20), nullable=True)
        batch_op.drop_column('mac_address')

    with op.batch_alter_table('equipment_history', schema=None) as batch_op:
        batch_op.drop_constraint('fk_equipment_history_assigned_to_roll', type_='foreignkey')
        batch_op.create_foreign_key('fk_equipment_history_equipment_id', 'equipment', ['equipment_id'], ['id'])  # fallback
        batch_op.alter_column('assigned_by', existing_type=sa.String(length=100), type_=sa.VARCHAR(length=120), existing_nullable=True)

    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.drop_constraint('uq_equipment_serial_number', type_='unique')
        batch_op.alter_column('assigned_by', existing_type=sa.String(length=100), type_=sa.VARCHAR(length=150), existing_nullable=True)
        batch_op.alter_column('department_code', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('quantity', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('intender_name', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=20), nullable=False)
        batch_op.alter_column('purchase_date', existing_type=sa.VARCHAR(length=20), nullable=False)
        batch_op.alter_column('po_date', existing_type=sa.VARCHAR(length=20), nullable=False)
        batch_op.alter_column('location', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('model', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.alter_column('manufacturer', existing_type=sa.VARCHAR(length=100), nullable=False)
        batch_op.drop_column('mac_address')
        batch_op.drop_column('remarks')

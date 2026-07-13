"""add route assignment status completed_at

Revision ID: 011
Revises: 22a74425feb4
Create Date: 2026-07-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '22a74425feb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vehicle_route_assignments', sa.Column('status', sa.String(), server_default='ACTIVE', nullable=False))
    op.add_column('vehicle_route_assignments', sa.Column('completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('vehicle_route_assignments', 'completed_at')
    op.drop_column('vehicle_route_assignments', 'status')

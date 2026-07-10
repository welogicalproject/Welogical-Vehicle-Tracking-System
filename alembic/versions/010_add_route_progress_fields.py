"""010 add route progress fields

Revision ID: 010
Revises: 009
Create Date: 2026-07-10

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vehicle_route_assignments", sa.Column("current_point_index", sa.Integer(), server_default="0", nullable=False))
    op.add_column("vehicle_route_assignments", sa.Column("progress_percentage", sa.Float(), server_default="0.0", nullable=False))
    op.add_column("vehicle_route_assignments", sa.Column("last_coordinate_index", sa.Integer(), server_default="0", nullable=False))
    op.add_column("vehicle_route_assignments", sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False))


def downgrade() -> None:
    op.drop_column("vehicle_route_assignments", "updated_at")
    op.drop_column("vehicle_route_assignments", "last_coordinate_index")
    op.drop_column("vehicle_route_assignments", "progress_percentage")
    op.drop_column("vehicle_route_assignments", "current_point_index")

"""Add planned routes tables

Revision ID: 008_add_planned_routes
Revises: 008_reconcile
Create Date: 2026-07-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008_add_planned_routes"
down_revision: Union[str, None] = "008_reconcile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create planned_routes table
    op.create_table(
        "planned_routes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_location", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.Column("estimated_duration", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="Pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planned_routes_id"), "planned_routes", ["id"], unique=False)

    # 2. Create planned_route_points table
    op.create_table(
        "planned_route_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["route_id"], ["planned_routes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planned_route_points_id"), "planned_route_points", ["id"], unique=False)

    # 3. Create vehicle_route_assignments table
    op.create_table(
        "vehicle_route_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["route_id"], ["planned_routes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicle_route_assignments_id"), "vehicle_route_assignments", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vehicle_route_assignments_id"), table_name="vehicle_route_assignments")
    op.drop_table("vehicle_route_assignments")
    op.drop_index(op.f("ix_planned_route_points_id"), table_name="planned_route_points")
    op.drop_table("planned_route_points")
    op.drop_index(op.f("ix_planned_routes_id"), table_name="planned_routes")
    op.drop_table("planned_routes")

"""Create trips table

Revision ID: 004_add_trips_table
Revises: 003_add_events_configs_commands
Create Date: 2026-06-26 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_add_trips_table"
down_revision: Union[str, None] = "003_add_events_configs_commands"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop enum type first to prevent duplicate type error during op.create_table
    op.execute("DROP TYPE IF EXISTS tripstatus CASCADE;")

    # Create trips table
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.Column("average_speed", sa.Float(), nullable=False),
        sa.Column("maximum_speed", sa.Float(), nullable=False),
        sa.Column("idle_time", sa.Float(), nullable=False),
        sa.Column("start_lat", sa.Float(), nullable=False),
        sa.Column("start_lon", sa.Float(), nullable=False),
        sa.Column("end_lat", sa.Float(), nullable=False),
        sa.Column("end_lon", sa.Float(), nullable=False),
        sa.Column("packet_count", sa.Integer(), nullable=False),
        sa.Column("overspeed_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "COMPLETED", "CANCELLED", name="tripstatus", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("fuel_used", sa.Float(), nullable=True),
        sa.Column("engine_hours", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # Create composite indexes
    op.create_index("ix_trips_vehicle_is_active", "trips", ["vehicle_id", "is_active"], unique=False)
    op.create_index("ix_trips_vehicle_start_time", "trips", ["vehicle_id", "start_time"], unique=False)
    op.create_index("ix_trips_vehicle_end_time", "trips", ["vehicle_id", "end_time"], unique=False)
    op.create_index(op.f("ix_trips_id"), "trips", ["id"], unique=False)


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index("ix_trips_vehicle_end_time", table_name="trips")
    op.drop_index("ix_trips_vehicle_start_time", table_name="trips")
    op.drop_index("ix_trips_vehicle_is_active", table_name="trips")
    op.drop_index(op.f("ix_trips_id"), table_name="trips")
    
    # Drop trips table
    op.drop_table("trips")

    # Drop TripStatus enum type safely
    op.execute("DROP TYPE IF EXISTS tripstatus CASCADE;")

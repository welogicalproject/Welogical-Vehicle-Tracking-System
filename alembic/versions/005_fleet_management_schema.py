"""Create drivers and assignments tables

Revision ID: 005_fleet_management_schema
Revises: 004_add_trips_table
Create Date: 2026-06-29 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_fleet_management_schema"
down_revision: Union[str, None] = "004_add_trips_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop enum type first to prevent duplicate type error
    op.execute("DROP TYPE IF EXISTS driverstatus CASCADE;")

    # 1. Create drivers table
    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_name", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("license_number", sa.String(), nullable=False),
        sa.Column("license_expiry", sa.DateTime(), nullable=False),
        sa.Column("emergency_contact", sa.String(), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "SUSPENDED", "INACTIVE", name="driverstatus", create_type=True), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_drivers_id"), "drivers", ["id"], unique=False)

    # 2. Create driver_assignments table
    op.create_table(
        "driver_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="Active"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_driver_assignments_id"), "driver_assignments", ["id"], unique=False)

    # 3. Add new columns to trips table
    op.add_column("trips", sa.Column("driver_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # Alter trips driver_id to be a foreign key pointing to drivers
    op.create_foreign_key("fk_trips_driver_id_drivers", "trips", "drivers", ["driver_id"], ["id"], ondelete="SET NULL")

def downgrade() -> None:
    # Drop foreign key constraint on trips
    op.drop_constraint("fk_trips_driver_id_drivers", "trips", type_="foreignkey")
    
    # Remove columns from trips
    op.drop_column("trips", "driver_snapshot")

    # Drop driver_assignments table
    op.drop_index(op.f("ix_driver_assignments_id"), table_name="driver_assignments")
    op.drop_table("driver_assignments")

    # Drop drivers table
    op.drop_index(op.f("ix_drivers_id"), table_name="drivers")
    op.drop_table("drivers")

    # Drop driverstatus enum
    op.execute("DROP TYPE IF EXISTS driverstatus CASCADE;")

"""Add metadata and status fields to vehicle table

Revision ID: 006_vehicle_metadata_and_status
Revises: 005_fleet_management_schema
Create Date: 2026-06-29 16:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_vehicle_metadata_and_status"
down_revision: Union[str, None] = "005_fleet_management_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add nullable new metadata columns to vehicles table for backward compatibility
    op.add_column("vehicles", sa.Column("vehicle_number", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("manufacturer", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("model", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("year", sa.Integer(), nullable=True))
    op.add_column("vehicles", sa.Column("vin", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("imei", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("sim_number", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("fuel_type", sa.String(), nullable=True))
    op.add_column("vehicles", sa.Column("capacity", sa.Float(), nullable=True))
    op.add_column("vehicles", sa.Column("status", sa.String(), nullable=False, server_default="Enabled"))
    op.add_column("vehicles", sa.Column("notes", sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column("vehicles", "notes")
    op.drop_column("vehicles", "status")
    op.drop_column("vehicles", "capacity")
    op.drop_column("vehicles", "fuel_type")
    op.drop_column("vehicles", "sim_number")
    op.drop_column("vehicles", "imei")
    op.drop_column("vehicles", "vin")
    op.drop_column("vehicles", "year")
    op.drop_column("vehicles", "model")
    op.drop_column("vehicles", "manufacturer")
    op.drop_column("vehicles", "vehicle_number")

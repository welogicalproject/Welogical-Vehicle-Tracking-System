"""Initial migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2026-06-23 11:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
# revision identifiers, used by Alembic.
revision = "001_initial_migration"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create vehicles table
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_uid", sa.String(), nullable=False),
        sa.Column("vehicle_name", sa.String(), nullable=False),
        sa.Column("vehicle_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    # Create indexes on vehicles
    op.create_index(op.f("ix_vehicles_id"), "vehicles", ["id"], unique=False)
    op.create_index(op.f("ix_vehicles_device_uid"), "vehicles", ["device_uid"], unique=True)

    # 2. Create locations table
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    # Create indexes on locations
    op.create_index(op.f("ix_locations_id"), "locations", ["id"], unique=False)
    op.create_index(op.f("ix_locations_vehicle_id"), "locations", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_locations_timestamp"), "locations", ["timestamp"], unique=False)

    # 3. Create raw_packets table
    op.create_table(
        "raw_packets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_uid", sa.String(), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("packet_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    # Create indexes on raw_packets
    op.create_index(op.f("ix_raw_packets_id"), "raw_packets", ["id"], unique=False)
    op.create_index(op.f("ix_raw_packets_device_uid"), "raw_packets", ["device_uid"], unique=False)
    op.create_index(op.f("ix_raw_packets_message_id"), "raw_packets", ["message_id"], unique=False)
    op.create_index(op.f("ix_raw_packets_created_at"), "raw_packets", ["created_at"], unique=False)


def downgrade() -> None:
    # Drop raw_packets indexes & table
    op.drop_index(op.f("ix_raw_packets_created_at"), table_name="raw_packets")
    op.drop_index(op.f("ix_raw_packets_message_id"), table_name="raw_packets")
    op.drop_index(op.f("ix_raw_packets_device_uid"), table_name="raw_packets")
    op.drop_index(op.f("ix_raw_packets_id"), table_name="raw_packets")
    op.drop_table("raw_packets")

    # Drop locations indexes & table
    op.drop_index(op.f("ix_locations_timestamp"), table_name="locations")
    op.drop_index(op.f("ix_locations_vehicle_id"), table_name="locations")
    op.drop_index(op.f("ix_locations_id"), table_name="locations")
    op.drop_table("locations")

    # Drop vehicles indexes & table
    op.drop_index(op.f("ix_vehicles_device_uid"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_id"), table_name="vehicles")
    op.drop_table("vehicles")
print("ALEMBIC MIGRATION LOADED")
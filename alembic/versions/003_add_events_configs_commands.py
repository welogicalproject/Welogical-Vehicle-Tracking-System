"""Create events, device_configs, device_commands, and command_logs tables

Revision ID: 003_add_events_configs_commands
Revises: 002_timezone_aware
Create Date: 2026-06-24 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.models.enums import CommandStatus

# revision identifiers, used by Alembic.
revision: str = "003_add_events_configs_commands"
down_revision: Union[str, None] = "002_timezone_aware"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type for CommandStatus safely (self-healing check)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'commandstatus') THEN
                CREATE TYPE commandstatus AS ENUM ('PENDING', 'SENT', 'EXECUTED', 'FAILED');
            END IF;
        END$$;
    """)

    # 1. Create events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("txn", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("msgid", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    # Create indexes on events table
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)
    op.create_index(op.f("ix_events_vehicle_id"), "events", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_events_txn"), "events", ["txn"], unique=False)
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_severity"), "events", ["severity"], unique=False)
    op.create_index(op.f("ix_events_msgid"), "events", ["msgid"], unique=False)
    op.create_index(op.f("ix_events_created_at"), "events", ["created_at"], unique=False)

    # 2. Create device_configs table
    op.create_table(
        "device_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("server_ip", sa.String(), nullable=True),
        sa.Column("server_port", sa.Integer(), nullable=True),
        sa.Column("apn", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=True),
        sa.Column("reporting_interval", sa.Integer(), nullable=True),
        sa.Column("speed_limit", sa.Float(), nullable=True),
        sa.Column("feature_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("firmware_version", sa.String(), nullable=True),
        sa.Column("hardware_version", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_id")
    )
    # Create indexes on device_configs table
    op.create_index(op.f("ix_device_configs_id"), "device_configs", ["id"], unique=False)
    op.create_index(op.f("ix_device_configs_vehicle_id"), "device_configs", ["vehicle_id"], unique=False)

    # 3. Create device_commands table
    op.create_table(
        "device_commands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("command_name", sa.String(), nullable=False),
        sa.Column("command_value", sa.String(), nullable=True),
        sa.Column("status", postgresql.ENUM('PENDING', 'SENT', 'EXECUTED', 'FAILED', name='commandstatus', create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    # Create indexes on device_commands table
    op.create_index(op.f("ix_device_commands_id"), "device_commands", ["id"], unique=False)
    op.create_index(op.f("ix_device_commands_vehicle_id"), "device_commands", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_device_commands_status"), "device_commands", ["status"], unique=False)

    # 4. Create command_logs table
    op.create_table(
        "command_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("command_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("status", postgresql.ENUM('PENDING', 'SENT', 'EXECUTED', 'FAILED', name='commandstatus', create_type=False), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["command_id"], ["device_commands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    # Create indexes on command_logs table
    op.create_index(op.f("ix_command_logs_id"), "command_logs", ["id"], unique=False)
    op.create_index(op.f("ix_command_logs_command_id"), "command_logs", ["command_id"], unique=False)
    op.create_index(op.f("ix_command_logs_vehicle_id"), "command_logs", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_command_logs_status"), "command_logs", ["status"], unique=False)
    op.create_index(op.f("ix_command_logs_created_at"), "command_logs", ["created_at"], unique=False)


def downgrade() -> None:
    # Drop command_logs table and indexes
    op.drop_index(op.f("ix_command_logs_created_at"), table_name="command_logs")
    op.drop_index(op.f("ix_command_logs_status"), table_name="command_logs")
    op.drop_index(op.f("ix_command_logs_vehicle_id"), table_name="command_logs")
    op.drop_index(op.f("ix_command_logs_command_id"), table_name="command_logs")
    op.drop_index(op.f("ix_command_logs_id"), table_name="command_logs")
    op.drop_table("command_logs")

    # Drop device_commands table and indexes
    op.drop_index(op.f("ix_device_commands_status"), table_name="device_commands")
    op.drop_index(op.f("ix_device_commands_vehicle_id"), table_name="device_commands")
    op.drop_index(op.f("ix_device_commands_id"), table_name="device_commands")
    op.drop_table("device_commands")

    # Drop device_configs table and indexes
    op.drop_index(op.f("ix_device_configs_vehicle_id"), table_name="device_configs")
    op.drop_index(op.f("ix_device_configs_id"), table_name="device_configs")
    op.drop_table("device_configs")

    # Drop events table and indexes
    op.drop_index(op.f("ix_events_created_at"), table_name="events")
    op.drop_index(op.f("ix_events_msgid"), table_name="events")
    op.drop_index(op.f("ix_events_severity"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_index(op.f("ix_events_txn"), table_name="events")
    op.drop_index(op.f("ix_events_vehicle_id"), table_name="events")
    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_table("events")

    # Drop commandstatus enum type safely
    op.execute("DROP TYPE IF EXISTS commandstatus CASCADE;")

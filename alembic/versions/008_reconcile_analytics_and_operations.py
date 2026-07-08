"""Reconcile analytics, operations, notifications, and commands schemas

Revision ID: 008_reconcile_analytics_and_operations
Revises: 007_add_route_cache_tables
Create Date: 2026-07-08 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "008_reconcile"
down_revision = "007_add_route_cache_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter device_commands table (PostgreSQL safe: rename columns and cast enums)
    op.alter_column("device_commands", "command_name", new_column_name="command_type")
    op.alter_column("device_commands", "command_value", new_column_name="payload")
    op.alter_column("device_commands", "executed_at", new_column_name="completed_at")

    # Add new columns
    op.add_column("device_commands", sa.Column("acknowledged_at", sa.DateTime(), nullable=True))
    op.add_column("device_commands", sa.Column("response", sa.Text(), nullable=True))
    op.add_column("device_commands", sa.Column("error_message", sa.Text(), nullable=True))

    # Convert status column from enum to sa.String safely using using clause
    op.alter_column(
        "device_commands", 
        "status",
        type_=sa.String(),
        existing_type=postgresql.ENUM(name="commandstatus"),
        postgresql_using="status::text"
    )

    # Create index on command_type
    op.create_index(op.f("ix_device_commands_command_type"), "device_commands", ["command_type"], unique=False)

    # 2. Create analytics_checkpoints table
    op.create_table(
        "analytics_checkpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pipeline_name", sa.String(), nullable=False),
        sa.Column("last_processed_location_id", sa.Integer(), nullable=False),
        sa.Column("last_run_timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pipeline_name")
    )
    op.create_index(op.f("ix_analytics_checkpoints_id"), "analytics_checkpoints", ["id"], unique=False)

    # 3. Create vehicle_daily_summaries table
    op.create_table(
        "vehicle_daily_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("distance_gps_km", sa.Float(), nullable=False),
        sa.Column("fuel_consumed_liters", sa.Float(), nullable=False),
        sa.Column("engine_runtime_hours", sa.Float(), nullable=False),
        sa.Column("driving_hours", sa.Float(), nullable=False),
        sa.Column("idle_hours", sa.Float(), nullable=False),
        sa.Column("max_speed", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_id", "date", name="uq_vehicle_date")
    )
    op.create_index(op.f("ix_vehicle_daily_summaries_id"), "vehicle_daily_summaries", ["id"], unique=False)
    op.create_index(op.f("ix_vehicle_daily_summaries_vehicle_id"), "vehicle_daily_summaries", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_vehicle_daily_summaries_date"), "vehicle_daily_summaries", ["date"], unique=False)

    # 4. Create fleet_daily_summaries table
    op.create_table(
        "fleet_daily_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_distance_km", sa.Float(), nullable=False),
        sa.Column("total_fuel_consumed_l", sa.Float(), nullable=False),
        sa.Column("total_engine_hours", sa.Float(), nullable=False),
        sa.Column("total_driving_hours", sa.Float(), nullable=False),
        sa.Column("total_idle_hours", sa.Float(), nullable=False),
        sa.Column("active_vehicles", sa.Integer(), nullable=False),
        sa.Column("fleet_max_speed", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date")
    )
    op.create_index(op.f("ix_fleet_daily_summaries_id"), "fleet_daily_summaries", ["id"], unique=False)
    op.create_index(op.f("ix_fleet_daily_summaries_date"), "fleet_daily_summaries", ["date"], unique=False)

    # 5. Create driver_daily_summaries table
    op.create_table(
        "driver_daily_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("distance_driven_km", sa.Float(), nullable=False),
        sa.Column("engine_hours", sa.Float(), nullable=False),
        sa.Column("driving_hours", sa.Float(), nullable=False),
        sa.Column("idle_hours", sa.Float(), nullable=False),
        sa.Column("fuel_used_l", sa.Float(), nullable=False),
        sa.Column("avg_fuel_economy_kpl", sa.Float(), nullable=False),
        sa.Column("max_speed_kmh", sa.Float(), nullable=False),
        sa.Column("avg_speed_kmh", sa.Float(), nullable=False),
        sa.Column("overspeed_count", sa.Integer(), nullable=False),
        sa.Column("overspeed_duration_sec", sa.Integer(), nullable=False),
        sa.Column("harsh_braking_count", sa.Integer(), nullable=False),
        sa.Column("harsh_acceleration_count", sa.Integer(), nullable=False),
        sa.Column("sharp_turn_count", sa.Integer(), nullable=False),
        sa.Column("ignition_cycles", sa.Integer(), nullable=False),
        sa.Column("refueling_count", sa.Integer(), nullable=False),
        sa.Column("safety_score", sa.Float(), nullable=False),
        sa.Column("eco_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("driver_id", "date", name="uq_driver_date")
    )
    op.create_index(op.f("ix_driver_daily_summaries_id"), "driver_daily_summaries", ["id"], unique=False)
    op.create_index(op.f("ix_driver_daily_summaries_driver_id"), "driver_daily_summaries", ["driver_id"], unique=False)
    op.create_index(op.f("ix_driver_daily_summaries_date"), "driver_daily_summaries", ["date"], unique=False)

    # 6. Create maintenance_summaries table
    op.create_table(
        "maintenance_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("remaining_service_distance_km", sa.Float(), nullable=False),
        sa.Column("remaining_service_days", sa.Integer(), nullable=False),
        sa.Column("estimated_next_service_date", sa.Date(), nullable=True),
        sa.Column("oil_life_pct", sa.Float(), nullable=False),
        sa.Column("brake_wear_pct", sa.Float(), nullable=False),
        sa.Column("tyre_health_pct", sa.Float(), nullable=False),
        sa.Column("battery_health_pct", sa.Float(), nullable=False),
        sa.Column("cooling_system_health", sa.String(), nullable=False),
        sa.Column("engine_health_index", sa.Float(), nullable=False),
        sa.Column("overall_vehicle_health_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_id", "date", name="uq_maintenance_date")
    )
    op.create_index(op.f("ix_maintenance_summaries_id"), "maintenance_summaries", ["id"], unique=False)
    op.create_index(op.f("ix_maintenance_summaries_vehicle_id"), "maintenance_summaries", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_maintenance_summaries_date"), "maintenance_summaries", ["date"], unique=False)

    # 7. Create vehicle_operations table
    op.create_table(
        "vehicle_operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("gps_lost", sa.Boolean(), nullable=False),
        sa.Column("low_fuel", sa.Boolean(), nullable=False),
        sa.Column("low_battery", sa.Boolean(), nullable=False),
        sa.Column("maintenance_due", sa.Boolean(), nullable=False),
        sa.Column("power_failure", sa.Boolean(), nullable=False),
        sa.Column("engine_overheat", sa.Boolean(), nullable=False),
        sa.Column("active_trip_id", sa.Integer(), nullable=True),
        sa.Column("current_driver_name", sa.String(), nullable=True),
        sa.Column("current_health_score", sa.Float(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_id")
    )
    op.create_index(op.f("ix_vehicle_operations_id"), "vehicle_operations", ["id"], unique=False)
    op.create_index(op.f("ix_vehicle_operations_vehicle_id"), "vehicle_operations", ["vehicle_id"], unique=True)

    # 8. Create fleet_operations_live table
    op.create_table(
        "fleet_operations_live",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicles_driving", sa.Integer(), nullable=False),
        sa.Column("vehicles_idling", sa.Integer(), nullable=False),
        sa.Column("vehicles_parked", sa.Integer(), nullable=False),
        sa.Column("vehicles_offline", sa.Integer(), nullable=False),
        sa.Column("active_trips", sa.Integer(), nullable=False),
        sa.Column("fleet_availability_pct", sa.Float(), nullable=False),
        sa.Column("fleet_utilization_pct", sa.Float(), nullable=False),
        sa.Column("vehicles_requiring_attention", sa.Integer(), nullable=False),
        sa.Column("critical_alerts_count", sa.Integer(), nullable=False),
        sa.Column("warning_alerts_count", sa.Integer(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_fleet_operations_live_id"), "fleet_operations_live", ["id"], unique=False)

    # 9. Create notification_histories table
    op.create_table(
        "notification_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("source_event_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_event_id"], ["events.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_notification_histories_id"), "notification_histories", ["id"], unique=False)
    op.create_index(op.f("ix_notification_histories_vehicle_id"), "notification_histories", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_notification_histories_driver_id"), "notification_histories", ["driver_id"], unique=False)
    op.create_index(op.f("ix_notification_histories_severity"), "notification_histories", ["severity"], unique=False)
    op.create_index(op.f("ix_notification_histories_created_at"), "notification_histories", ["created_at"], unique=False)
    op.create_index(op.f("ix_notification_histories_acknowledged"), "notification_histories", ["acknowledged"], unique=False)
    op.create_index(op.f("ix_notification_histories_resolved"), "notification_histories", ["resolved"], unique=False)


def downgrade() -> None:
    # 1. Drop newly created tables
    op.drop_table("notification_histories")
    op.drop_table("fleet_operations_live")
    op.drop_table("vehicle_operations")
    op.drop_table("maintenance_summaries")
    op.drop_table("driver_daily_summaries")
    op.drop_table("fleet_daily_summaries")
    op.drop_table("vehicle_daily_summaries")
    op.drop_table("analytics_checkpoints")

    # 2. Revert device_commands alterations
    op.drop_index(op.f("ix_device_commands_command_type"), table_name="device_commands")
    
    # Cast status column back to custom enum type
    op.alter_column(
        "device_commands", 
        "status",
        type_=postgresql.ENUM("PENDING", "SENT", "EXECUTED", "FAILED", name="commandstatus"),
        existing_type=sa.String(),
        postgresql_using="status::commandstatus"
    )

    # Drop columns
    op.drop_column("device_commands", "error_message")
    op.drop_column("device_commands", "response")
    op.drop_column("device_commands", "acknowledged_at")

    # Rename columns back
    op.alter_column("device_commands", "completed_at", new_column_name="executed_at")
    op.alter_column("device_commands", "payload", new_column_name="command_value")
    op.alter_column("device_commands", "command_type", new_column_name="command_name")

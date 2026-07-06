"""Add route cache tables

Revision ID: 007_add_route_cache_tables
Revises: 006_vehicle_metadata_and_status
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_add_route_cache_tables"
down_revision: Union[str, None] = "006_vehicle_metadata_and_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "route_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cache_key", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_api", sa.String(), nullable=False),
        sa.Column("provider_version", sa.String(), nullable=True),
        sa.Column("route_schema_version", sa.Integer(), nullable=False),
        sa.Column("travel_mode", sa.String(), nullable=False),
        sa.Column("routing_preference", sa.String(), nullable=True),
        sa.Column("polyline_quality", sa.String(), nullable=True),
        sa.Column("coordinate_precision", sa.Integer(), nullable=False),
        sa.Column("origin_lat_raw", sa.Float(), nullable=False),
        sa.Column("origin_lon_raw", sa.Float(), nullable=False),
        sa.Column("destination_lat_raw", sa.Float(), nullable=False),
        sa.Column("destination_lon_raw", sa.Float(), nullable=False),
        sa.Column("origin_lat_normalized", sa.Float(), nullable=False),
        sa.Column("origin_lon_normalized", sa.Float(), nullable=False),
        sa.Column("destination_lat_normalized", sa.Float(), nullable=False),
        sa.Column("destination_lon_normalized", sa.Float(), nullable=False),
        sa.Column("waypoint_hash", sa.String(), nullable=True),
        sa.Column("options_hash", sa.String(), nullable=False),
        sa.Column("request_hash", sa.String(), nullable=False),
        sa.Column("encoded_polyline", sa.String(), nullable=True),
        sa.Column("polyline_format", sa.String(), nullable=True),
        sa.Column("distance_meters", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("static_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("traffic_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("bounds", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("provider_response_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("invalidated_at", sa.DateTime(), nullable=True),
        sa.Column("invalidated_reason", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key"),
    )
    op.create_index(op.f("ix_route_cache_id"), "route_cache", ["id"], unique=False)
    op.create_index(op.f("ix_route_cache_cache_key"), "route_cache", ["cache_key"], unique=False)
    op.create_index(op.f("ix_route_cache_provider"), "route_cache", ["provider"], unique=False)
    op.create_index(op.f("ix_route_cache_provider_api"), "route_cache", ["provider_api"], unique=False)
    op.create_index(op.f("ix_route_cache_travel_mode"), "route_cache", ["travel_mode"], unique=False)
    op.create_index(op.f("ix_route_cache_origin_lat_normalized"), "route_cache", ["origin_lat_normalized"], unique=False)
    op.create_index(op.f("ix_route_cache_origin_lon_normalized"), "route_cache", ["origin_lon_normalized"], unique=False)
    op.create_index(op.f("ix_route_cache_destination_lat_normalized"), "route_cache", ["destination_lat_normalized"], unique=False)
    op.create_index(op.f("ix_route_cache_destination_lon_normalized"), "route_cache", ["destination_lon_normalized"], unique=False)
    op.create_index(op.f("ix_route_cache_waypoint_hash"), "route_cache", ["waypoint_hash"], unique=False)
    op.create_index(op.f("ix_route_cache_options_hash"), "route_cache", ["options_hash"], unique=False)
    op.create_index(op.f("ix_route_cache_request_hash"), "route_cache", ["request_hash"], unique=False)
    op.create_index(op.f("ix_route_cache_status"), "route_cache", ["status"], unique=False)
    op.create_index(op.f("ix_route_cache_created_at"), "route_cache", ["created_at"], unique=False)
    op.create_index("ix_route_cache_provider_api_status", "route_cache", ["provider", "provider_api", "status"], unique=False)
    op.create_index(
        "ix_route_cache_normalized_endpoints",
        "route_cache",
        [
            "origin_lat_normalized",
            "origin_lon_normalized",
            "destination_lat_normalized",
            "destination_lon_normalized",
        ],
        unique=False,
    )

    op.create_table(
        "trip_route_cache_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("route_cache_id", sa.Integer(), nullable=False),
        sa.Column("trip_fingerprint", sa.String(), nullable=True),
        sa.Column("route_source", sa.String(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["route_cache_id"], ["route_cache.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trip_route_cache_links_id"), "trip_route_cache_links", ["id"], unique=False)
    op.create_index("ix_trip_route_cache_links_trip_id", "trip_route_cache_links", ["trip_id"], unique=False)
    op.create_index(op.f("ix_trip_route_cache_links_route_cache_id"), "trip_route_cache_links", ["route_cache_id"], unique=False)
    op.create_index(op.f("ix_trip_route_cache_links_trip_fingerprint"), "trip_route_cache_links", ["trip_fingerprint"], unique=False)
    op.create_index(op.f("ix_trip_route_cache_links_is_current"), "trip_route_cache_links", ["is_current"], unique=False)
    op.create_index(op.f("ix_trip_route_cache_links_linked_at"), "trip_route_cache_links", ["linked_at"], unique=False)
    op.create_index(
        "uq_trip_route_cache_links_current_trip",
        "trip_route_cache_links",
        ["trip_id"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )

    op.create_table(
        "google_route_usage_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("cache_key", sa.String(), nullable=True),
        sa.Column("route_cache_id", sa.Integer(), nullable=True),
        sa.Column("trip_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["route_cache_id"], ["route_cache.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_google_route_usage_events_id"), "google_route_usage_events", ["id"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_period_month"), "google_route_usage_events", ["period_month"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_event_type"), "google_route_usage_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_cache_key"), "google_route_usage_events", ["cache_key"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_route_cache_id"), "google_route_usage_events", ["route_cache_id"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_trip_id"), "google_route_usage_events", ["trip_id"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_status"), "google_route_usage_events", ["status"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_error_code"), "google_route_usage_events", ["error_code"], unique=False)
    op.create_index(op.f("ix_google_route_usage_events_created_at"), "google_route_usage_events", ["created_at"], unique=False)
    op.create_index("ix_google_route_usage_events_month_type", "google_route_usage_events", ["period_month", "event_type"], unique=False)
    op.create_index("ix_google_route_usage_events_month_status", "google_route_usage_events", ["period_month", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_google_route_usage_events_month_status", table_name="google_route_usage_events")
    op.drop_index("ix_google_route_usage_events_month_type", table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_created_at"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_error_code"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_status"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_trip_id"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_route_cache_id"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_cache_key"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_event_type"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_period_month"), table_name="google_route_usage_events")
    op.drop_index(op.f("ix_google_route_usage_events_id"), table_name="google_route_usage_events")
    op.drop_table("google_route_usage_events")

    op.drop_index("uq_trip_route_cache_links_current_trip", table_name="trip_route_cache_links")
    op.drop_index(op.f("ix_trip_route_cache_links_linked_at"), table_name="trip_route_cache_links")
    op.drop_index(op.f("ix_trip_route_cache_links_is_current"), table_name="trip_route_cache_links")
    op.drop_index(op.f("ix_trip_route_cache_links_trip_fingerprint"), table_name="trip_route_cache_links")
    op.drop_index(op.f("ix_trip_route_cache_links_route_cache_id"), table_name="trip_route_cache_links")
    op.drop_index("ix_trip_route_cache_links_trip_id", table_name="trip_route_cache_links")
    op.drop_index(op.f("ix_trip_route_cache_links_id"), table_name="trip_route_cache_links")
    op.drop_table("trip_route_cache_links")

    op.drop_index("ix_route_cache_normalized_endpoints", table_name="route_cache")
    op.drop_index("ix_route_cache_provider_api_status", table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_created_at"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_status"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_request_hash"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_options_hash"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_waypoint_hash"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_destination_lon_normalized"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_destination_lat_normalized"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_origin_lon_normalized"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_origin_lat_normalized"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_travel_mode"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_provider_api"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_provider"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_cache_key"), table_name="route_cache")
    op.drop_index(op.f("ix_route_cache_id"), table_name="route_cache")
    op.drop_table("route_cache")

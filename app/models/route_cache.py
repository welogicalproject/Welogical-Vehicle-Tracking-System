from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RouteCache(Base):
    __tablename__ = "route_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, nullable=False, unique=True, index=True)

    provider = Column(String, nullable=False, default="google", index=True)
    provider_api = Column(String, nullable=False, default="routes", index=True)
    provider_version = Column(String, nullable=True)
    route_schema_version = Column(Integer, nullable=False, default=1)

    travel_mode = Column(String, nullable=False, default="DRIVE", index=True)
    routing_preference = Column(String, nullable=True)
    polyline_quality = Column(String, nullable=True)
    coordinate_precision = Column(Integer, nullable=False, default=5)

    origin_lat_raw = Column(Float, nullable=False)
    origin_lon_raw = Column(Float, nullable=False)
    destination_lat_raw = Column(Float, nullable=False)
    destination_lon_raw = Column(Float, nullable=False)
    origin_lat_normalized = Column(Float, nullable=False, index=True)
    origin_lon_normalized = Column(Float, nullable=False, index=True)
    destination_lat_normalized = Column(Float, nullable=False, index=True)
    destination_lon_normalized = Column(Float, nullable=False, index=True)

    waypoint_hash = Column(String, nullable=True, index=True)
    options_hash = Column(String, nullable=False, index=True)
    request_hash = Column(String, nullable=False, index=True)

    encoded_polyline = Column(String, nullable=True)
    polyline_format = Column(String, nullable=True)
    distance_meters = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    static_duration_seconds = Column(Integer, nullable=True)
    traffic_duration_seconds = Column(Integer, nullable=True)
    bounds = Column(JSONB, nullable=True)
    provider_response_summary = Column(JSONB, nullable=True)

    status = Column(String, nullable=False, default="pending", index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False)
    invalidated_at = Column(DateTime, nullable=True)
    invalidated_reason = Column(String, nullable=True)

    trip_links = relationship("TripRouteCacheLink", back_populates="route_cache", cascade="all, delete-orphan")
    usage_events = relationship("GoogleRouteUsageEvent", back_populates="route_cache")

    __table_args__ = (
        Index("ix_route_cache_provider_api_status", "provider", "provider_api", "status"),
        Index(
            "ix_route_cache_normalized_endpoints",
            "origin_lat_normalized",
            "origin_lon_normalized",
            "destination_lat_normalized",
            "destination_lon_normalized",
        ),
    )

    def __repr__(self):
        return f"<RouteCache id={self.id} provider='{self.provider}' status='{self.status}'>"


class TripRouteCacheLink(Base):
    __tablename__ = "trip_route_cache_links"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    route_cache_id = Column(Integer, ForeignKey("route_cache.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_fingerprint = Column(String, nullable=True, index=True)
    route_source = Column(String, nullable=False, default="cache_hit")
    is_current = Column(Boolean, nullable=False, default=True, index=True)
    linked_at = Column(DateTime, default=utc_now_naive, nullable=False, index=True)

    trip = relationship("Trip", back_populates="route_cache_links")
    route_cache = relationship("RouteCache", back_populates="trip_links")

    __table_args__ = (
        Index("ix_trip_route_cache_links_trip_id", "trip_id"),
        Index(
            "uq_trip_route_cache_links_current_trip",
            "trip_id",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
    )

    def __repr__(self):
        return f"<TripRouteCacheLink id={self.id} trip_id={self.trip_id} route_cache_id={self.route_cache_id}>"


class GoogleRouteUsageEvent(Base):
    __tablename__ = "google_route_usage_events"

    id = Column(Integer, primary_key=True, index=True)
    period_month = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    cache_key = Column(String, nullable=True, index=True)
    route_cache_id = Column(Integer, ForeignKey("route_cache.id", ondelete="SET NULL"), nullable=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)
    error_code = Column(String, nullable=True, index=True)
    metadata_json = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive, nullable=False, index=True)

    route_cache = relationship("RouteCache", back_populates="usage_events")
    trip = relationship("Trip")

    __table_args__ = (
        Index("ix_google_route_usage_events_month_type", "period_month", "event_type"),
        Index("ix_google_route_usage_events_month_status", "period_month", "status"),
    )

    def __repr__(self):
        return f"<GoogleRouteUsageEvent id={self.id} period='{self.period_month}' type='{self.event_type}'>"

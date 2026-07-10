export interface Vehicle {
  id: number;
  device_uid: string;
  vehicle_name: string;
  vehicle_type: string;
  created_at: string;
  last_seen: string | null;

  // Extended Metadata
  is_connected?: boolean;
  vehicle_number?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  year?: number | null;
  vin?: string | null;
  imei?: string | null;
  sim_number?: string | null;
  fuel_type?: string | null;
  capacity?: number | null;
  status?: string | null; // "Enabled", "Disabled", "Archived"
  notes?: string | null;
  current_driver?: Driver | null;
}

export interface Location {
  id: number;
  vehicle_id: number;
  latitude: number;
  longitude: number;
  speed: number;
  altitude: number;
  timestamp: string;
  extra_data?: Record<string, any> | null;
}

export interface RawPacket {
  id: number;
  device_uid: string | null;
  message_id: number | null;
  packet_data: Record<string, any>;
  created_at: string;
}

export interface SystemStats {
  total_vehicles: number;
  total_locations: number;
  total_raw_packets: number;
  vehicles_online: number;
  vehicles_idle: number;
  vehicles_offline: number;
  latest_timestamp: string | null;
}

export type VehicleStatus = "online" | "idle" | "offline";

export interface Event {
  id: number;
  vehicle_id: number;
  txn: string;
  event_type: string;
  description: string;
  severity: "Critical" | "Warning" | "Info";
  msgid: number | null;
  created_at: string;
  vehicle_name?: string;
  device_uid?: string;
}

export interface EventStats {
  critical: number;
  warning: number;
  info: number;
  today: number;
  total: number;
}

export interface DeviceConfig {
  id?: number;
  vehicle_id: number;
  server_ip: string | null;
  server_port: number | null;
  apn: string | null;
  timezone: string | null;
  reporting_interval: number | null;
  speed_limit: number | null;
  feature_flags: Record<string, any> | null;
  firmware_version: string | null;
  hardware_version: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface DeviceCommand {
  id: number;
  vehicle_id: number;

  // New field names (current backend contract)
  command_type: string;
  payload: string | null;

  // Legacy aliases — backend serialises both so old components still work
  command_name: string;
  command_value: string | null;

  // Status vocabulary: new lifecycle states
  status: "Queued" | "Sending" | "Delivered" | "Acknowledged" | "Executing" | "Completed" | "Failed" | "Timed Out" | "Cancelled"
        | "PENDING" | "SENT" | "EXECUTED";  // legacy values kept for safety

  // Timestamps (new names)
  created_at: string;
  sent_at: string | null;
  acknowledged_at: string | null;
  completed_at: string | null;

  // Legacy timestamp alias
  executed_at: string | null;

  // Result fields
  response: string | null;
  error_message: string | null;

  // Optional enrichment
  vehicle_name?: string;
}

export interface CommandLog {
  id: number;
  command_id: number;
  vehicle_id: number;
  status: string;
  message: string | null;
  created_at: string;
}

export interface VehicleTrackingSnapshot {
  vehicle: Vehicle;
  latest_location: Location | null;
  route_history: Location[];
  latest_event: Event | null;
  latest_command: DeviceCommand | null;
  device_config: DeviceConfig | null;
  health_status: "Healthy" | "Warning" | "Offline";
  movement_status: "Moving" | "Stopped" | "Offline";
  packet_count: number;
  current_driver?: Driver | null;
}

export interface Trip {
  id: number;
  vehicle_id: number;
  start_time: string;
  end_time: string;
  duration: number;
  distance: number;
  average_speed: number;
  maximum_speed: number;
  idle_time: number;
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
  packet_count: number;
  overspeed_count: number;
  status: "ACTIVE" | "COMPLETED" | "CANCELLED";
  is_active: boolean;
  driver_id: number | null;
  fuel_used: number | null;
  engine_hours: number | null;
  created_at: string;
  updated_at: string;
  // Dynamic fields added during listing
  vehicle_name?: string;
  device_uid?: string;
}

export interface StopEvent {
  start_time: string;
  end_time: string;
  duration: number;
  latitude: number;
  longitude: number;
}

export interface OverspeedEvent {
  timestamp: string;
  speed: number;
  latitude: number;
  longitude: number;
}

export interface TripSummary {
  trip_id: number;
  vehicle_id: number;
  duration: number;
  distance: number;
  average_speed: number;
  moving_time: number;
  idle_time: number;
  average_moving_speed: number;
  maximum_speed: number;
  packet_count: number;
  average_packet_interval: number;
  stop_count: number;
  longest_stop: number;
  overspeed_count: number;
  driving_score: number;
  stops: StopEvent[];
  overspeeds: OverspeedEvent[];
}

export interface ReplayPoint {
  timestamp: string;
  lat: number;
  lon: number;
  speed: number;
  heading: number | null;
  ignition: number | null;
  extra: Record<string, any> | null;
}

export interface ReplayResponse {
  trip_id: number;
  vehicle_id: number;
  points: ReplayPoint[];
  total_points: number;
  downsampled: boolean;
  downsample_ratio: number;
}

export interface Driver {
  id: number;
  driver_name: string;
  phone_number: string;
  email: string | null;
  license_number: string;
  license_expiry: string;
  emergency_contact: string;
  status: "ACTIVE" | "SUSPENDED" | "INACTIVE";
  created_at: string;
  current_vehicle?: {
    id: number;
    device_uid: string;
    vehicle_name: string;
    vehicle_type: string;
    vehicle_number?: string | null;
  } | null;
}

export interface DriverAssignment {
  id: number;
  vehicle_id: number;
  driver_id: number;
  assigned_at: string;
  released_at: string | null;
  status: "Active" | "Completed";
  driver?: Driver | null;
}

export interface TripGoogleRoute {
  id: number;
  cache_key: string;
  provider: string;
  provider_api: string;
  travel_mode: string;
  origin_lat_raw: number;
  origin_lon_raw: number;
  destination_lat_raw: number;
  destination_lon_raw: number;
  encoded_polyline: string | null;
  distance_meters: number | null;
  duration_seconds: number | null;
  status: string;
  created_at: string;
}

export interface PlannedRoutePoint {
  id: number;
  route_id: number;
  sequence_number: number;
  latitude: number;
  longitude: number;
}

export interface PlannedRoute {
  id: number;
  name: string;
  start_location: string;
  destination: string;
  distance: number;
  estimated_duration: number;
  status: string; // "Pending" | "Assigned" | "Running" | "Completed"
  created_at: string;
  updated_at: string;
  points: PlannedRoutePoint[];
}

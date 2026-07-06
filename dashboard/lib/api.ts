import { Vehicle, Location, RawPacket, SystemStats, Event, EventStats, DeviceConfig, DeviceCommand, CommandLog, VehicleTrackingSnapshot, Trip, TripSummary, ReplayResponse, Driver, DriverAssignment, TripGoogleRoute } from "../types";

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `HTTP error! Status: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // System Health and Stats
  getStats: (): Promise<SystemStats> => 
    request<SystemStats>("/system/stats"),

  // Vehicles
  getVehicles: (skip = 0, limit = 100): Promise<Vehicle[]> => 
    request<Vehicle[]>(`/vehicles?skip=${skip}&limit=${limit}`),

  getVehicle: (id: number): Promise<Vehicle> => 
    request<Vehicle>(`/vehicles/${id}`),

  getFleetTracking: (startTime?: string, endTime?: string, limitPerVehicle = 500): Promise<VehicleTrackingSnapshot[]> => {
    let path = `/vehicles/tracking/snapshots?limit_per_vehicle=${limitPerVehicle}`;
    if (startTime) path += `&start_time=${encodeURIComponent(startTime)}`;
    if (endTime) path += `&end_time=${encodeURIComponent(endTime)}`;
    return request<VehicleTrackingSnapshot[]>(path);
  },

  getVehicleTracking: (id: number, startTime?: string, endTime?: string, limitPerVehicle = 1000): Promise<VehicleTrackingSnapshot> => {
    let path = `/vehicles/${id}/tracking?limit_per_vehicle=${limitPerVehicle}`;
    if (startTime) path += `&start_time=${encodeURIComponent(startTime)}`;
    if (endTime) path += `&end_time=${encodeURIComponent(endTime)}`;
    return request<VehicleTrackingSnapshot>(path);
  },

  createVehicle: (vehicle: Omit<Vehicle, "id" | "created_at" | "last_seen">): Promise<Vehicle> => 
    request<Vehicle>("/vehicles", {
      method: "POST",
      body: JSON.stringify(vehicle),
    }),

  updateVehicle: (id: number, vehicle: Partial<Omit<Vehicle, "id" | "created_at" | "last_seen">>): Promise<Vehicle> => 
    request<Vehicle>(`/vehicles/${id}`, {
      method: "PUT",
      body: JSON.stringify(vehicle),
    }),

  deleteVehicle: (id: number): Promise<Vehicle> => 
    request<Vehicle>(`/vehicles/${id}`, {
      method: "DELETE",
    }),

  // Locations
  logLocation: (location: Omit<Location, "id">): Promise<Location> => 
    request<Location>("/locations", {
      method: "POST",
      body: JSON.stringify(location),
    }),

  getLatestLocation: (vehicleId: number): Promise<Location> => 
    request<Location>(`/locations/latest/${vehicleId}`),

  getLocationHistory: (
    vehicleId: number,
    startTime?: string,
    endTime?: string,
    skip = 0,
    limit = 100
  ): Promise<Location[]> => {
    let path = `/locations/history/${vehicleId}?skip=${skip}&limit=${limit}`;
    if (startTime) path += `&start_time=${encodeURIComponent(startTime)}`;
    if (endTime) path += `&end_time=${encodeURIComponent(endTime)}`;
    return request<Location[]>(path);
  },

  getAllLocations: (skip = 0, limit = 100): Promise<Location[]> =>
    request<Location[]>(`/locations?skip=${skip}&limit=${limit}`),

  // Raw Packets
  getRawPackets: (skip = 0, limit = 100): Promise<RawPacket[]> =>
    request<RawPacket[]>(`/vts/raw-packets?skip=${skip}&limit=${limit}`),

  // Events
  getEventsStats: (): Promise<EventStats> =>
    request<EventStats>("/events/stats"),

  getRecentEvents: (limit = 10): Promise<Event[]> =>
    request<Event[]>(`/events/recent?limit=${limit}`),

  getEvents: (
    vehicleId?: number,
    eventType?: string,
    severity?: string,
    skip = 0,
    limit = 100,
    sort?: string
  ): Promise<Event[]> => {
    let path = `/events?skip=${skip}&limit=${limit}`;
    if (vehicleId) path += `&vehicle_id=${vehicleId}`;
    if (eventType) path += `&event_type=${encodeURIComponent(eventType)}`;
    if (severity) path += `&severity=${severity}`;
    if (sort) path += `&sort=${sort}`;
    return request<Event[]>(path);
  },

  getVehicleEvents: (
    vehicleId: number,
    severity?: string,
    skip = 0,
    limit = 100
  ): Promise<Event[]> => {
    let path = `/events/${vehicleId}?skip=${skip}&limit=${limit}`;
    if (severity) path += `&severity=${severity}`;
    return request<Event[]>(path);
  },

  // Configurations
  getConfigurations: (skip = 0, limit = 100): Promise<DeviceConfig[]> =>
    request<DeviceConfig[]>(`/configurations?skip=${skip}&limit=${limit}`),

  getConfiguration: (vehicleId: number): Promise<DeviceConfig> =>
    request<DeviceConfig>(`/configurations/${vehicleId}`),

  createConfiguration: (config: DeviceConfig): Promise<DeviceConfig> =>
    request<DeviceConfig>("/configurations", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  updateConfiguration: (vehicleId: number, config: Partial<DeviceConfig>): Promise<DeviceConfig> =>
    request<DeviceConfig>(`/configurations/${vehicleId}`, {
      method: "PUT",
      body: JSON.stringify(config),
    }),

  deleteConfiguration: (vehicleId: number): Promise<DeviceConfig> =>
    request<DeviceConfig>(`/configurations/${vehicleId}`, {
      method: "DELETE",
    }),

  // Commands
  getCommands: (vehicleId?: number, status?: string, skip = 0, limit = 100): Promise<DeviceCommand[]> => {
    let path = `/commands?skip=${skip}&limit=${limit}`;
    if (vehicleId) path += `&vehicle_id=${vehicleId}`;
    if (status) path += `&status=${status}`;
    return request<DeviceCommand[]>(path);
  },

  getVehicleCommands: (vehicleId: number, status?: string, skip = 0, limit = 100): Promise<DeviceCommand[]> => {
    let path = `/commands/${vehicleId}?skip=${skip}&limit=${limit}`;
    if (status) path += `&status=${status}`;
    return request<DeviceCommand[]>(path);
  },

  queueCommand: (command: Omit<DeviceCommand, "id" | "status" | "created_at" | "sent_at" | "executed_at">): Promise<DeviceCommand> =>
    request<DeviceCommand>("/commands", {
      method: "POST",
      body: JSON.stringify(command),
    }),

  deleteCommand: (commandId: number): Promise<DeviceCommand> =>
    request<DeviceCommand>(`/commands/${commandId}`, {
      method: "DELETE",
    }),

  getCommandLogs: (commandId: number): Promise<CommandLog[]> =>
    request<CommandLog[]>(`/commands/${commandId}/logs`),

  // Trips & Replay Analytics
  getVehicleTrips: (
    vehicleId: number,
    startTime?: string,
    endTime?: string,
    status?: string,
    skip = 0,
    limit = 100
  ): Promise<Trip[]> => {
    let path = `/vehicles/${vehicleId}/trips?skip=${skip}&limit=${limit}`;
    if (startTime) path += `&start_time=${encodeURIComponent(startTime)}`;
    if (endTime) path += `&end_time=${encodeURIComponent(endTime)}`;
    if (status) path += `&status=${status}`;
    return request<Trip[]>(path);
  },

  rebuildVehicleTrips: (vehicleId: number): Promise<{ result: boolean; vehicle_id: number; trips_created: number; msg: string }> =>
    request<{ result: boolean; vehicle_id: number; trips_created: number; msg: string }>(
      `/vehicles/${vehicleId}/trips/rebuild`,
      { method: "POST" }
    ),

  getTripSummary: (vehicleId: number, tripId: number): Promise<TripSummary> =>
    request<TripSummary>(`/vehicles/${vehicleId}/trips/${tripId}/summary`),

  getTripReplay: (vehicleId: number, tripId: number, multiplier = 1): Promise<ReplayResponse> =>
    request<ReplayResponse>(`/vehicles/${vehicleId}/trips/${tripId}/replay?multiplier=${multiplier}`),

  getTripGeoJSON: (vehicleId: number, tripId: number): Promise<any> =>
    request<any>(`/vehicles/${vehicleId}/trips/${tripId}/geojson`),

  getTripExportUrl: (vehicleId: number, tripId: number): string =>
    `${BASE_URL}/vehicles/${vehicleId}/trips/${tripId}/export`,

  getTripGoogleRoute: (vehicleId: number, tripId: number): Promise<TripGoogleRoute> =>
    request<TripGoogleRoute>(`/vehicles/${vehicleId}/trips/${tripId}/google-route`),

  generateTripGoogleRoute: (vehicleId: number, tripId: number): Promise<TripGoogleRoute> =>
    request<TripGoogleRoute>(`/vehicles/${vehicleId}/trips/${tripId}/google-route`, {
      method: "POST",
    }),


  // Drivers & Assignments
  getDrivers: (skip = 0, limit = 100): Promise<Driver[]> =>
    request<Driver[]>(`/drivers?skip=${skip}&limit=${limit}`),

  createDriver: (driver: {
    driver_name: string;
    phone_number: string;
    email?: string | null;
    license_number: string;
    license_expiry: string; // ISO datetime string
    emergency_contact: string;
    status?: string;
    address?: string | null;
    notes?: string | null;
  }): Promise<Driver> =>
    request<Driver>("/drivers", {
      method: "POST",
      body: JSON.stringify(driver),
    }),

  assignDriver: (vehicleId: number, driverId: number): Promise<DriverAssignment> =>
    request<DriverAssignment>(`/vehicles/${vehicleId}/assign/${driverId}`, {
      method: "POST"
    }),

  releaseDriver: (vehicleId: number): Promise<DriverAssignment> =>
    request<DriverAssignment>(`/vehicles/${vehicleId}/release`, {
      method: "POST"
    }),

  getActiveAssignment: (vehicleId: number): Promise<DriverAssignment | null> =>
    request<DriverAssignment | null>(`/vehicles/${vehicleId}/assignments/active`),

  getVehicleAssignmentHistory: (vehicleId: number): Promise<DriverAssignment[]> =>
    request<DriverAssignment[]>(`/vehicles/${vehicleId}/assignments/history`),

  getDriverAssignmentHistory: (driverId: number): Promise<DriverAssignment[]> =>
    request<DriverAssignment[]>(`/drivers/${driverId}/assignments/history`),
};

import { RANGE_OPTIONS, RangeKey, VEHICLE_COLORS } from "../constants/tracking";
import { VehicleTrackingSnapshot } from "../types";

export function getVehicleColor(index: number) {
  return VEHICLE_COLORS[Math.max(0, index) % VEHICLE_COLORS.length];
}

export function toBackendDateTime(value: Date) {
  return value.toISOString().slice(0, 19);
}

export function toUtcIsoFromLocal(value: string) {
  if (!value) return undefined;
  return toBackendDateTime(new Date(value));
}

export function routeWindow(range: RangeKey, customStart: string, customEnd: string) {
  if (range === "custom") {
    return {
      start: toUtcIsoFromLocal(customStart),
      end: toUtcIsoFromLocal(customEnd),
    };
  }

  const option = RANGE_OPTIONS.find((item) => item.key === range);
  const end = new Date();
  const start = new Date(end.getTime() - (option?.minutes || 60) * 60_000);
  return { start: toBackendDateTime(start), end: toBackendDateTime(end) };
}

export function logTrackingDebug(label: string, payload: Record<string, unknown>) {
  if (process.env.NODE_ENV !== "production") {
    console.debug(`[tracking] ${label}`, payload);
  }
}

export function summarizeSnapshots(data: VehicleTrackingSnapshot[]) {
  return {
    snapshotCount: data.length,
    withLatestLocation: data.filter((snapshot) => Boolean(snapshot.latest_location)).length,
    withRouteHistory: data.filter((snapshot) => snapshot.route_history.length > 0).length,
    visibleVehicleIds: data.map((snapshot) => snapshot.vehicle.id),
    vehicleOptions: data
      .filter((snapshot) => Boolean(snapshot.latest_location))
      .map((snapshot) => ({
        id: snapshot.vehicle.id,
        name: snapshot.vehicle.vehicle_name,
        latitude: snapshot.latest_location?.latitude,
        longitude: snapshot.latest_location?.longitude,
      })),
  };
}

export function getPacketVal(snapshot: VehicleTrackingSnapshot | undefined, path: (string | number)[]) {
  let current: any = snapshot?.latest_location?.extra_data;
  for (const key of path) current = current?.[key];
  return current;
}

export function getStatus(lastSeen: string | null | undefined): "online" | "idle" | "offline" {
  if (!lastSeen) return "offline";
  const cleanSeen = lastSeen.endsWith("Z") ? lastSeen : `${lastSeen}Z`;
  const now = Date.now();
  const seen = new Date(cleanSeen).getTime();
  const diffSec = (now - seen) / 1000;
  if (diffSec < 300) return "online";
  if (diffSec < 1800) return "idle";
  return "offline";
}

export function getHeadingText(snapshot: VehicleTrackingSnapshot | undefined) {
  const dir = getPacketVal(snapshot, ["gps", "dir"]) ?? getPacketVal(snapshot, ["gps_details", "dir"]);
  if (typeof dir === "number") {
    const cardinals = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
    const index = Math.round(dir / 22.5) % 16;
    return `${cardinals[index]} (${dir}°)`;
  }
  return "N/A";
}

export function getLastUpdateText(snapshot: VehicleTrackingSnapshot | undefined) {
  if (snapshot?.latest_location?.timestamp) {
    const rawTs = snapshot.latest_location.timestamp;
    const cleanTs = rawTs.endsWith("Z") ? rawTs : `${rawTs}Z`;
    const date = new Date(cleanTs);
    const timeStr = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const diffMs = Date.now() - date.getTime();
    const diffSec = Math.max(0, Math.floor(diffMs / 1000));
    return `${timeStr} (${diffSec} sec ago)`;
  }
  return "N/A";
}

export function getGPSFixText(snapshot: VehicleTrackingSnapshot | undefined) {
  const fix = getPacketVal(snapshot, ["gps", "fix"]) ?? getPacketVal(snapshot, ["gps_details", "fix"]);
  const sat = getPacketVal(snapshot, ["gps", "sat"]) ?? getPacketVal(snapshot, ["gps_details", "sat"]);
  if (fix === "A") return `3D Fix (${sat ?? 0} Satellites)`;
  if (fix === "V") return "No Fix";
  return "N/A";
}

export function getBatteryVolt(snapshot: VehicleTrackingSnapshot | undefined) {
  const volt = getPacketVal(snapshot, ["pwr", "volt"]);
  if (typeof volt === "number") return `${(volt / 1000).toFixed(1)} V`;
  const analog = getPacketVal(snapshot, ["io", "analog", 0]);
  if (typeof analog === "number") return `${(analog / 1000).toFixed(1)} V`;
  return "N/A";
}

export function getMainVolt(snapshot: VehicleTrackingSnapshot | undefined) {
  const mvolt = getPacketVal(snapshot, ["pwr", "mvolt"]);
  return typeof mvolt === "number" ? `${mvolt.toFixed(1)} V` : "N/A";
}

export function getOdometerKm(snapshot: VehicleTrackingSnapshot | undefined) {
  const odo = getPacketVal(snapshot, ["gps", "odo"]) ?? getPacketVal(snapshot, ["gps_details", "odo"]);
  return typeof odo === "number" ? `${(odo / 1000).toFixed(1)} km` : "N/A";
}

export function getNetworkStatus(snapshot: VehicleTrackingSnapshot | undefined) {
  if (!snapshot) return "N/A";
  const status = getStatus(snapshot.vehicle.last_seen);
  return status === "online" ? "Good (4G)" : status === "idle" ? "Idle (3G)" : "Offline";
}

export function buildSpeedOverviewData(snapshots: VehicleTrackingSnapshot[]) {
  const allTimes = new Set<string>();
  snapshots.forEach((snapshot) => {
    snapshot.route_history.forEach((point) => {
      allTimes.add(new Date(point.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    });
  });

  return Array.from(allTimes).sort().slice(-8).map((time) => {
    const row: Record<string, any> = { time };
    snapshots.forEach((snapshot) => {
      const point = snapshot.route_history.find((candidate) => {
        const candidateTime = new Date(candidate.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        return candidateTime === time;
      });
      if (point) row[snapshot.vehicle.vehicle_name] = point.speed;
    });
    return row;
  });
}

export function exportSnapshotsCsv(snapshots: VehicleTrackingSnapshot[]) {
  const lines = snapshots.map((snapshot) => `${snapshot.vehicle.vehicle_name},${snapshot.vehicle.device_uid},${snapshot.latest_location?.latitude ?? ""},${snapshot.latest_location?.longitude ?? ""},${snapshot.latest_location?.speed ?? 0}`);
  const csvContent = "data:text/csv;charset=utf-8,Vehicle,UID,Latitude,Longitude,Speed\n" + lines.join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "vts_snapshots_export.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

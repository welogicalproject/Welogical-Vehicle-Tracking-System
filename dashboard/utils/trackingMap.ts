import { VehicleTrackingSnapshot } from "../types";
import { getVehicleColor } from "./tracking";

export { getVehicleColor };

export function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function asUtcDate(value: string) {
  return new Date(value.endsWith("Z") ? value : `${value}Z`);
}

export function getHeading(snapshot: VehicleTrackingSnapshot) {
  const latest = snapshot.latest_location;
  if (!latest) return 0;
  const fromGps = latest.extra_data?.gps?.dir ?? latest.extra_data?.gps_details?.dir;
  if (typeof fromGps === "number") return fromGps;

  const trail = snapshot.route_history;
  if (trail.length < 2) return 0;
  const a = trail[trail.length - 2];
  const b = trail[trail.length - 1];
  return (Math.atan2(b.longitude - a.longitude, b.latitude - a.latitude) * 180) / Math.PI;
}

export function metricValue(snapshot: VehicleTrackingSnapshot, path: string[], fallback = "N/A") {
  let current: any = snapshot.latest_location?.extra_data;
  for (const key of path) current = current?.[key];
  return current ?? fallback;
}

export function voltage(snapshot: VehicleTrackingSnapshot, source: "battery" | "main") {
  const data = snapshot.latest_location?.extra_data;
  if (source === "main") {
    const main = data?.pwr?.mvolt;
    return typeof main === "number" ? `${main} V` : "N/A";
  }

  const analog = data?.io?.analog?.[0];
  if (typeof analog === "number") return `${(analog / 1000).toFixed(2)} V`;
  const pwr = data?.pwr?.volt;
  return typeof pwr === "number" ? `${(pwr / 1000).toFixed(2)} V` : "N/A";
}

export function logMapDebug(label: string, payload: Record<string, unknown>) {
  if (process.env.NODE_ENV !== "production") {
    console.debug(`[FleetTrackingMap] ${label}`, payload);
  }
}

function toFiniteNumber(value: unknown) {
  const numberValue = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

export function locationPosition(location: VehicleTrackingSnapshot["latest_location"]) {
  if (!location) return null;
  const latitude = toFiniteNumber(location.latitude);
  const longitude = toFiniteNumber(location.longitude);
  if (latitude === null || longitude === null) return null;
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return null;
  return [latitude, longitude] as [number, number];
}

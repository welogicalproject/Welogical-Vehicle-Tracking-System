export type RangeKey = "15m" | "1h" | "6h" | "24h" | "7d" | "custom";

export const RANGE_OPTIONS: { key: RangeKey; label: string; minutes?: number }[] = [
  { key: "15m", label: "Last 15 Minutes", minutes: 15 },
  { key: "1h", label: "Last 1 Hour", minutes: 60 },
  { key: "6h", label: "Last 6 Hours", minutes: 360 },
  { key: "24h", label: "Last 24 Hours", minutes: 1440 },
  { key: "7d", label: "Last 7 Days", minutes: 10080 },
  { key: "custom", label: "Custom Date Range" },
];

export const VEHICLE_COLORS = ["#ef4444", "#eab308", "#10b981", "#a855f7", "#3b82f6", "#f97316", "#14b8a6"];

export const TRACKING_REFRESH_MS = 10000;
export const TRACKING_ROUTE_LIMIT = 2000;
export const RECENT_EVENTS_LIMIT = 25;

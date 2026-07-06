import { RECENT_EVENTS_LIMIT, TRACKING_ROUTE_LIMIT } from "../constants/tracking";
import { api } from "../lib/api";

export async function getTrackingDashboardData(start?: string, end?: string) {
  const [trackingData, stats, recentEvents] = await Promise.all([
    api.getFleetTracking(start, end, TRACKING_ROUTE_LIMIT),
    api.getStats().catch((error) => {
      console.error("Error fetching stats", error);
      return null;
    }),
    api.getRecentEvents(RECENT_EVENTS_LIMIT).catch((error) => {
      console.error("Error fetching recent events", error);
      return [];
    }),
  ]);

  return { trackingData, stats, recentEvents };
}

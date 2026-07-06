"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RangeKey, TRACKING_REFRESH_MS } from "../constants/tracking";
import { getTrackingDashboardData } from "../services/trackingService";
import { Event, SystemStats, VehicleTrackingSnapshot } from "../types";
import { buildSpeedOverviewData, logTrackingDebug, routeWindow, summarizeSnapshots } from "../utils/tracking";

export function useFleetTracking() {
  const [snapshots, setSnapshots] = useState<VehicleTrackingSnapshot[]>([]);
  const [visibleVehicleIds, setVisibleVehicleIds] = useState<number[]>([]);
  const [range, setRange] = useState<RangeKey>("15m");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [recentEvents, setRecentEvents] = useState<Event[]>([]);

  const loadData = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);

    try {
      const window = routeWindow(range, customStart, customEnd);
      const { trackingData, stats: statsRes, recentEvents: eventsRes } = await getTrackingDashboardData(window.start, window.end);

      logTrackingDebug("API response before setState", {
        requestWindow: window,
        response: trackingData,
        ...summarizeSnapshots(trackingData),
      });

      setSnapshots(trackingData);
      setStats(statsRes);
      setRecentEvents(eventsRes);
      setVisibleVehicleIds(trackingData.map((snapshot) => snapshot.vehicle.id));
      setError(null);
    } catch (err: any) {
      console.error("Failed to load tracking dashboard data", err);
      setError(err.message || "Failed to load fleet tracking data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [customEnd, customStart, range]);

  useEffect(() => {
    logTrackingDebug("snapshots state updated", summarizeSnapshots(snapshots));
  }, [snapshots]);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), TRACKING_REFRESH_MS);
    return () => clearInterval(interval);
  }, [loadData]);

  const fleetCounts = useMemo(() => ({
    total: snapshots.length,
    moving: snapshots.filter((item) => item.movement_status === "Moving").length,
    stopped: snapshots.filter((item) => item.movement_status === "Stopped").length,
    offline: snapshots.filter((item) => item.health_status === "Offline").length,
  }), [snapshots]);

  const speedOverviewData = useMemo(() => buildSpeedOverviewData(snapshots), [snapshots]);

  return {
    snapshots,
    visibleVehicleIds,
    setVisibleVehicleIds,
    range,
    setRange,
    customStart,
    setCustomStart,
    customEnd,
    setCustomEnd,
    loading,
    refreshing,
    error,
    stats,
    recentEvents,
    loadData,
    fleetCounts,
    speedOverviewData,
  };
}

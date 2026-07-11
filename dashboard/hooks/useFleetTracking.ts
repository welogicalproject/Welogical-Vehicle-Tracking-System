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

  useEffect(() => {
    const baseApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsUrl = baseApiUrl.replace(/^http/, "ws") + "/ws";
    
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let isCleanup = false;

    function connect() {
      if (isCleanup) return;
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log("[WS] Connected to backend");
        socket?.send("subscribe telemetry");
        socket?.send("subscribe vehicles");
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const { topic, data } = payload;

          if (topic === "telemetry") {
            const { vehicle_id, latitude, longitude, speed, timestamp, extra_data } = data;
            setSnapshots((prev) =>
              prev.map((s) => {
                if (s.vehicle.id === vehicle_id) {
                  const newPoint = {
                    id: Date.now(),
                    vehicle_id,
                    latitude,
                    longitude,
                    speed,
                    timestamp,
                    extra_data
                  };

                  const exists = s.route_history.some(
                    (p) => p.timestamp === timestamp || (Math.abs(p.latitude - latitude) < 0.000001 && Math.abs(p.longitude - longitude) < 0.000001)
                  );

                  const updatedHistory = exists ? s.route_history : [...s.route_history, newPoint];

                  return {
                    ...s,
                    latest_location: {
                      ...s.latest_location,
                      id: s.latest_location?.id || Date.now(),
                      vehicle_id,
                      latitude,
                      longitude,
                      speed,
                      altitude: s.latest_location?.altitude || 0,
                      timestamp,
                      extra_data
                    },
                    route_history: updatedHistory,
                    movement_status: speed > 0.1 ? "Moving" : "Idle",
                    health_status: "Healthy"
                  };
                }
                return s;
              })
            );
          } else if (topic === "vehicles") {
            loadData(true);
          }
        } catch (err) {
          console.error("[WS] Message parsing error:", err);
        }
      };

      socket.onclose = () => {
        console.log("[WS] Disconnected, reconnecting...");
        if (!isCleanup) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };

      socket.onerror = (err) => {
        console.error("[WS] Error:", err);
      };
    }

    connect();

    return () => {
      isCleanup = true;
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
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

"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { Vehicle, SystemStats, Event, EventStats, VehicleTrackingSnapshot } from "../types";
import { api } from "../lib/api";

interface FleetContextType {
  vehicles: Vehicle[];
  snapshots: VehicleTrackingSnapshot[];
  recentEvents: Event[];
  stats: SystemStats | null;
  eventsStats: EventStats | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  loadData: (silent?: boolean) => Promise<void>;
  setSnapshots: React.Dispatch<React.SetStateAction<VehicleTrackingSnapshot[]>>;
  deleteVehicleFromState: (vehicleId: number) => void;
}

const FleetContext = createContext<FleetContextType | undefined>(undefined);

export function FleetProvider({ children }: { children: React.ReactNode }) {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [snapshots, setSnapshots] = useState<VehicleTrackingSnapshot[]>([]);
  const [recentEvents, setRecentEvents] = useState<Event[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [eventsStats, setEventsStats] = useState<EventStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true);
    else setLoading(true);

    try {
      const [vehiclesRes, statsRes, evStatsRes, recentEvRes, trackingRes] = await Promise.all([
        api.getVehicles(0, 100).catch(() => []),
        api.getStats().catch(() => null),
        api.getEventsStats().catch(() => null),
        api.getRecentEvents(15).catch(() => []),
        api.getFleetTracking(undefined, undefined, 50).catch(() => []),
      ]);

      setVehicles(vehiclesRes);
      setStats(statsRes);
      setEventsStats(evStatsRes);
      setRecentEvents(recentEvRes);
      setSnapshots((prev) => {
        if (!prev || prev.length === 0) return trackingRes;
        return trackingRes.map((newSnap) => {
          const existing = prev.find((s) => s.vehicle.id === newSnap.vehicle.id);
          if (!existing) return newSnap;

          // Merge route history. Deduplicate by timestamp and sort chronologically.
          const historyMap = new Map<string, any>();
          existing.route_history.forEach((h) => {
            if (h.timestamp) historyMap.set(h.timestamp, h);
          });
          newSnap.route_history.forEach((h) => {
            if (h.timestamp) historyMap.set(h.timestamp, h);
          });
          const mergedHistory = Array.from(historyMap.values()).sort(
            (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          ).slice(-1000); // cap to 1000 points

          // Keep the newest latest_location based on timestamp
          let mergedLatest = newSnap.latest_location;
          if (existing.latest_location && newSnap.latest_location) {
            const existingTime = new Date(existing.latest_location.timestamp).getTime();
            const newTime = new Date(newSnap.latest_location.timestamp).getTime();
            if (existingTime > newTime) {
              mergedLatest = existing.latest_location;
            }
          } else if (existing.latest_location) {
            mergedLatest = existing.latest_location;
          }

          // Movement status
          const mergedMovement = mergedLatest?.speed && mergedLatest.speed > 0.1 ? "Moving" : (newSnap.movement_status || existing.movement_status);

          return {
            ...existing,
            vehicle: { ...existing.vehicle, ...newSnap.vehicle },
            latest_location: mergedLatest,
            route_history: mergedHistory,
            movement_status: mergedMovement,
            health_status: newSnap.health_status || existing.health_status,
          };
        });
      });
      setError(null);
    } catch (err: any) {
      console.error("[FleetContext] Failed to load data", err);
      setError(err.message || "Failed to load fleet data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const deleteVehicleFromState = useCallback((vehicleId: number) => {
    setVehicles((prev) => prev.filter((v) => v.id !== vehicleId));
    setSnapshots((prev) => prev.filter((s) => s.vehicle.id !== vehicleId));
    setRecentEvents((prev) => prev.filter((e) => e.vehicle_id !== vehicleId));
    setStats((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        total_vehicles: Math.max(0, prev.total_vehicles - 1),
      };
    });
  }, []);

  // Set up WebSocket connection globally
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
        console.log("[Global WS] Connected");
        socket?.send("subscribe telemetry");
        socket?.send("subscribe vehicles");
        socket?.send("subscribe events");
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
                    altitude: extra_data?.altitude || extra_data?.gps?.alt || 0,
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
                      altitude: s.latest_location?.altitude || extra_data?.altitude || extra_data?.gps?.alt || 0,
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
          } else if (topic === "vehicles" || topic === "events") {
            loadData(true);
          }
        } catch (err) {
          console.error("[Global WS] Parsing error:", err);
        }
      };

      socket.onclose = () => {
        console.log("[Global WS] Disconnected, reconnecting...");
        if (!isCleanup) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };

      socket.onerror = (err) => {
        console.error("[Global WS] Error:", err);
      };
    }

    connect();

    return () => {
      isCleanup = true;
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [loadData]);

  // Initial load
  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const value = useMemo(() => ({
    vehicles,
    snapshots,
    recentEvents,
    stats,
    eventsStats,
    loading,
    refreshing,
    error,
    loadData,
    setSnapshots,
    deleteVehicleFromState,
  }), [vehicles, snapshots, recentEvents, stats, eventsStats, loading, refreshing, error, loadData, deleteVehicleFromState]);

  return <FleetContext.Provider value={value}>{children}</FleetContext.Provider>;
}

export function useFleet() {
  const context = useContext(FleetContext);
  if (context === undefined) {
    throw new Error("useFleet must be used within a FleetProvider");
  }
  return context;
}

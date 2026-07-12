"use client";

import { useEffect, useMemo, useState } from "react";
import { RangeKey } from "../constants/tracking";
import { useFleet } from "../context/FleetContext";
import { buildSpeedOverviewData } from "../utils/tracking";

export function useFleetTracking() {
  const {
    snapshots,
    recentEvents,
    loading,
    refreshing,
    error,
    stats,
    loadData
  } = useFleet();

  const [visibleVehicleIds, setVisibleVehicleIds] = useState<number[]>([]);
  const [range, setRange] = useState<RangeKey>("15m");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  // Sync visible ids when snapshots change
  useEffect(() => {
    setVisibleVehicleIds(snapshots.map((s) => s.vehicle.id));
  }, [snapshots]);

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

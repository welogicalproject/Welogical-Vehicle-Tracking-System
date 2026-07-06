"use client";

import { useEffect, useMemo, useState } from "react";
import { Event, VehicleTrackingSnapshot } from "../types";
import { logTrackingDebug } from "../utils/tracking";

export type TrackingDetailTab = "live" | "status" | "history" | "events";

export function useVehicleSelection(snapshots: VehicleTrackingSnapshot[], recentEvents: Event[]) {
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | "all">("all");
  const [detailTab, setDetailTab] = useState<TrackingDetailTab>("live");

  const selectedSnapshot = useMemo(() => {
    if (selectedVehicleId === "all") return undefined;
    return snapshots.find((snapshot) => snapshot.vehicle.id === selectedVehicleId);
  }, [selectedVehicleId, snapshots]);

  const vehicleOptions = useMemo(() => snapshots.filter((snapshot) => snapshot.latest_location), [snapshots]);

  const displayedEvents = useMemo(() => {
    if (selectedVehicleId === "all") return recentEvents.slice(0, 5);
    return recentEvents.filter((event) => event.vehicle_id === selectedVehicleId).slice(0, 5);
  }, [recentEvents, selectedVehicleId]);

  useEffect(() => {
    logTrackingDebug("derived state", {
      snapshots: snapshots.length,
      vehicleOptions: vehicleOptions.map((snapshot) => ({
        id: snapshot.vehicle.id,
        name: snapshot.vehicle.vehicle_name,
        latitude: snapshot.latest_location?.latitude,
        longitude: snapshot.latest_location?.longitude,
      })),
      selectedVehicleId,
    });
  }, [selectedVehicleId, snapshots.length, vehicleOptions]);

  return {
    selectedVehicleId,
    setSelectedVehicleId,
    detailTab,
    setDetailTab,
    selectedSnapshot,
    vehicleOptions,
    displayedEvents,
  };
}

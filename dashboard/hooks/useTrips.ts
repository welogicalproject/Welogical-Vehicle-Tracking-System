import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { Trip, Vehicle } from "../types";
import { useFleet } from "../context/FleetContext";

export function useTrips(initialVehicleId: number | "all" = "all") {
  const { vehicles } = useFleet();
  const [vehicleId, setVehicleId] = useState<number | "all">(initialVehicleId);
  const [status, setStatus] = useState<string>("all");
  const [startTime, setStartTime] = useState<string>("");
  const [endTime, setEndTime] = useState<string>("");
  const [skip, setSkip] = useState<number>(0);
  const [limit, setLimit] = useState<number>(100);

  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [rebuilding, setRebuilding] = useState<boolean>(false);

  const loadTrips = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    try {
      // Determine vehicles to query
      let vehiclesToQuery: Vehicle[] = [];
      if (vehicleId === "all") {
        if (vehicles.length === 0) {
          const fetchedVehicles = await api.getVehicles(0, 100);
          vehiclesToQuery = fetchedVehicles;
        } else {
          vehiclesToQuery = vehicles;
        }
      } else {
        const singleVehicle = vehicles.find((v) => v.id === vehicleId);
        if (singleVehicle) {
          vehiclesToQuery = [singleVehicle];
        } else {
          // Fallback if vehicle not yet loaded
          const fetchedSingle = await api.getVehicle(vehicleId);
          vehiclesToQuery = [fetchedSingle];
        }
      }

      // Fetch trips for selected vehicles concurrently
      const statusFilter = status === "all" ? undefined : status;
      const tripPromises = vehiclesToQuery.map(async (v) => {
        try {
          const res = await api.getVehicleTrips(
            v.id,
            startTime || undefined,
            endTime || undefined,
            statusFilter
          );
          // Enrich with vehicle info
          return res.map((t) => ({
            ...t,
            vehicle_name: v.vehicle_name,
            device_uid: v.device_uid,
          }));
        } catch (err) {
          console.warn(`Failed to fetch trips for vehicle ID ${v.id}`, err);
          return [];
        }
      });

      const allTripsNested = await Promise.all(tripPromises);
      const mergedTrips = allTripsNested.flat();

      // Sort chronologically descending
      mergedTrips.sort(
        (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime()
      );

      setTrips(mergedTrips);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load trips.");
    } finally {
      setLoading(false);
    }
  }, [vehicleId, status, startTime, endTime, vehicles]);

  // Rebuild trips for a specific vehicle
  const rebuildTrips = useCallback(async (targetVehicleId: number) => {
    setRebuilding(true);
    try {
      const res = await api.rebuildVehicleTrips(targetVehicleId);
      if (res.result) {
        await loadTrips(true);
        return { success: true, count: res.trips_created, msg: res.msg };
      }
      return { success: false, msg: "Rebuild failed on backend." };
    } catch (err: any) {
      console.error(err);
      return { success: false, msg: err.message || "Error running rebuild process." };
    } finally {
      setRebuilding(false);
    }
  }, [loadTrips]);

  useEffect(() => {
    loadTrips();
  }, [vehicleId, status, startTime, endTime]);

  return {
    vehicleId,
    setVehicleId,
    status,
    setStatus,
    startTime,
    setStartTime,
    endTime,
    setEndTime,
    skip,
    setSkip,
    limit,
    setLimit,
    trips,
    vehicles,
    loading,
    error,
    rebuilding,
    loadTrips,
    rebuildTrips,
  };
}

"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Button } from "../ui/button";
import { Loader2, Route, CheckCircle, Navigation, MapPin, RefreshCw } from "lucide-react";

interface Point {
  id: number;
  route_id: number;
  sequence_number: number;
  latitude: number;
  longitude: number;
}

interface PlannedRouteResponse {
  id: number;
  name: string;
  start_location: string;
  destination: string;
  distance: number;
  estimated_duration: number;
  status: string;
  created_at: string;
  updated_at: string;
  points: Point[];
}

interface VehicleRoutesTabProps {
  vehicleId: number;
  currentLocation?: { latitude: number; longitude: number } | null;
}

export function VehicleRoutesTab({ vehicleId, currentLocation }: VehicleRoutesTabProps) {
  const [activeRoute, setActiveRoute] = useState<PlannedRouteResponse | null>(null);
  const [availableRoutes, setAvailableRoutes] = useState<PlannedRouteResponse[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null);
  const [loadingActive, setLoadingActive] = useState(false);
  const [loadingAvailable, setLoadingAvailable] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchActiveRoute = useCallback(async () => {
    setLoadingActive(true);
    try {
      const response = await fetch(`http://localhost:8000/vehicles/${vehicleId}/assigned-route`);
      if (response.status === 200) {
        const data = await response.json();
        setActiveRoute(data);
      } else if (response.status === 404) {
        setActiveRoute(null);
      } else {
        throw new Error("Failed to load active route");
      }
    } catch (err: any) {
      console.error(err);
      // Suppress network logs in UI unless critical
    } finally {
      setLoadingActive(false);
    }
  }, [vehicleId]);

  const fetchAvailableRoutes = useCallback(async () => {
    setLoadingAvailable(true);
    try {
      const response = await fetch("http://localhost:8000/routes");
      if (response.ok) {
        const data = await response.json();
        setAvailableRoutes(data);
      } else {
        throw new Error("Failed to load available routes");
      }
    } catch (err: any) {
      console.error(err);
      setError("Backend service is currently unavailable.");
    } finally {
      setLoadingAvailable(false);
    }
  }, []);

  useEffect(() => {
    fetchActiveRoute();
    fetchAvailableRoutes();
  }, [vehicleId, fetchActiveRoute, fetchAvailableRoutes]);

  // Polling for active route updates (e.g., when simulator updates status to Running/Completed)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchActiveRoute();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchActiveRoute]);

  const handleAssignRoute = async () => {
    if (!selectedRouteId) return;
    setAssigning(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/vehicles/${vehicleId}/assign-route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ route_id: selectedRouteId }),
      });
      if (!response.ok) {
        throw new Error("Failed to assign route");
      }
      setSelectedRouteId(null);
      await fetchActiveRoute();
    } catch (err: any) {
      setError(err.message || "Failed to assign route");
    } finally {
      setAssigning(false);
    }
  };

  // Helper to calculate progress on route
  const getProgress = () => {
    if (!activeRoute || !currentLocation || activeRoute.points.length === 0) {
      return { index: 0, percent: 0 };
    }

    let minDistance = Infinity;
    let closestIndex = 0;

    activeRoute.points.forEach((pt, i) => {
      const dLat = pt.latitude - currentLocation.latitude;
      const dLng = pt.longitude - currentLocation.longitude;
      const dist = Math.sqrt(dLat * dLat + dLng * dLng);
      if (dist < minDistance) {
        minDistance = dist;
        closestIndex = i;
      }
    });

    const total = activeRoute.points.length;
    const percent = total > 1 ? Math.round((closestIndex / (total - 1)) * 100) : 100;
    return { index: closestIndex, percent };
  };

  const progress = getProgress();

  // Status computation matching required states (Idle, Assigned, Running, Completed)
  const getVehicleStatus = () => {
    if (!activeRoute) return "Idle";
    if (activeRoute.status === "Completed") return "Completed";
    if (activeRoute.status === "Running" || progress.percent > 0) return "Running";
    return "Assigned";
  };

  const vehicleStatus = getVehicleStatus();

  return (
    <div className="space-y-4 p-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Assigned Route</span>
        <button
          onClick={() => {
            fetchActiveRoute();
            fetchAvailableRoutes();
          }}
          className="text-cyan-400 hover:text-cyan-300 p-1 rounded transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      {error && (
        <div className="text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded border border-rose-500/20">
          {error}
        </div>
      )}

      {loadingActive ? (
        <div className="flex items-center justify-center py-6 text-slate-400 text-xs">
          <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading route state...
        </div>
      ) : activeRoute ? (
        <div className="bg-[#0b0f19]/40 border border-[#1e294b]/60 rounded-xl p-3 flex flex-col gap-3">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-white font-bold text-sm">{activeRoute.name}</h4>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {activeRoute.start_location} → {activeRoute.destination}
              </span>
            </div>
            <span
              className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded border ${
                vehicleStatus === "Running"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 animate-pulse"
                  : vehicleStatus === "Completed"
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                  : vehicleStatus === "Assigned"
                  ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                  : "bg-slate-500/10 text-slate-400 border-slate-500/20"
              }`}
            >
              {vehicleStatus}
            </span>
          </div>

          <div className="border-t border-[#1e294b]/30 pt-2 space-y-2">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Distance</span>
              <span className="text-slate-200 font-semibold">{activeRoute.distance.toFixed(1)} km</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Est. Duration</span>
              <span className="text-slate-200 font-semibold">{Math.round(activeRoute.estimated_duration / 60)} mins</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Coordinate Progress</span>
              <span className="text-slate-200 font-mono font-semibold">
                {progress.index + 1} / {activeRoute.points.length}
              </span>
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between text-[10px] font-bold">
              <span className="text-slate-400">Completion</span>
              <span className="text-cyan-400">{progress.percent}%</span>
            </div>
            <div className="w-full bg-[#1b253b] h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-cyan-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${progress.percent}%` }}
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-[#0b0f19]/30 border border-[#1e294b]/30 rounded-xl p-4 text-center">
          <p className="text-slate-400 text-xs mb-3">No active route assignment found for this vehicle.</p>
          
          {availableRoutes.length > 0 ? (
            <div className="space-y-3">
              <select
                onChange={(e) => setSelectedRouteId(Number(e.target.value) || null)}
                defaultValue=""
                className="w-full bg-[#0b0f19] border border-slate-700 rounded p-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              >
                <option value="" disabled>Select route to assign...</option>
                {availableRoutes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.distance.toFixed(1)} km)
                  </option>
                ))}
              </select>
              <Button
                onClick={handleAssignRoute}
                disabled={assigning || !selectedRouteId}
                className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
              >
                {assigning ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Route className="h-3.5 w-3.5 mr-1" />}
                Assign Route
              </Button>
            </div>
          ) : (
            <p className="text-slate-500 text-[10px]">Create a planned route using the Trip Planner panel below.</p>
          )}
        </div>
      )}
    </div>
  );
}

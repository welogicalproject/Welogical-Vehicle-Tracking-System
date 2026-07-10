"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Button } from "../ui/button";
import { Loader2, Route, CheckCircle2, RefreshCw, AlertCircle } from "lucide-react";
import { PlannedRoute } from "../../types";
import { api } from "../../lib/api";

interface VehicleRoutesTabProps {
  vehicleId: number;
  currentLocation?: { latitude: number; longitude: number } | null;
}

// Status badge styling
function RoutStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    Running: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 animate-pulse",
    Completed: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    Assigned: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    Pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  };
  return (
    <span
      className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded border ${
        styles[status] ?? "bg-slate-500/10 text-slate-400 border-slate-500/20"
      }`}
    >
      {status}
    </span>
  );
}

export function VehicleRoutesTab({ vehicleId, currentLocation }: VehicleRoutesTabProps) {
  const [activeRoute, setActiveRoute] = useState<PlannedRoute | null>(null);
  const [availableRoutes, setAvailableRoutes] = useState<PlannedRoute[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null);
  const [loadingActive, setLoadingActive] = useState(false);
  const [loadingAvailable, setLoadingAvailable] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [assignSuccess, setAssignSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchActiveRoute = useCallback(async () => {
    setLoadingActive(true);
    try {
      // api.getAssignedRoute returns null on 404
      const data = await api.getAssignedRoute(vehicleId);
      setActiveRoute(data);
    } catch (err: any) {
      // Only surface unexpected errors
      console.error("Failed to fetch active route:", err);
    } finally {
      setLoadingActive(false);
    }
  }, [vehicleId]);

  const fetchAvailableRoutes = useCallback(async () => {
    setLoadingAvailable(true);
    try {
      const data = await api.getPlannedRoutes();
      setAvailableRoutes(data);
    } catch (err: any) {
      console.error("Failed to fetch available routes:", err);
      setError("Could not load available routes from backend.");
    } finally {
      setLoadingAvailable(false);
    }
  }, []);

  useEffect(() => {
    fetchActiveRoute();
    fetchAvailableRoutes();
  }, [vehicleId, fetchActiveRoute, fetchAvailableRoutes]);

  // Poll active route every 5 seconds to catch status changes (Running → Completed)
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
    setAssignSuccess(false);
    try {
      await api.assignRoute(vehicleId, selectedRouteId);
      setAssignSuccess(true);
      setSelectedRouteId(null);
      await fetchActiveRoute();
      // Reset success badge after a moment
      setTimeout(() => setAssignSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to assign route. Check vehicle status.");
    } finally {
      setAssigning(false);
    }
  };

  // Calculate closest coordinate index to current vehicle position
  const getProgress = () => {
    if (!activeRoute || activeRoute.points.length === 0) {
      return { index: 0, percent: 0 };
    }
    const index = activeRoute.current_point_index ?? 0;
    const percent = activeRoute.progress_percentage !== undefined ? Math.round(activeRoute.progress_percentage) : 0;
    return { index, percent };
  };

  const progress = getProgress();

  // Filter available routes to only show Pending/Assigned (not Completed)
  const assignableRoutes = availableRoutes.filter(
    (r) => r.status === "Pending" || r.status === "Assigned"
  );

  return (
    <div className="space-y-4 p-1">
      {/* Header row */}
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
          Assigned Route
        </span>
        <button
          onClick={() => {
            fetchActiveRoute();
            fetchAvailableRoutes();
          }}
          className="text-cyan-400 hover:text-cyan-300 p-1 rounded transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 p-2.5 rounded border border-rose-500/20">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {assignSuccess && (
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 p-2.5 rounded border border-emerald-500/20">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Route assigned successfully!
        </div>
      )}

      {/* Active route card */}
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
            <RoutStatusBadge status={activeRoute.status} />
          </div>

          <div className="border-t border-[#1e294b]/30 pt-2 space-y-2">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Distance</span>
              <span className="text-slate-200 font-semibold">{activeRoute.distance.toFixed(1)} km</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Est. Duration</span>
              <span className="text-slate-200 font-semibold">
                {Math.round(activeRoute.estimated_duration / 60)} mins
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Coordinate Progress</span>
              <span className="text-slate-200 font-mono font-semibold">
                {progress.index + 1} / {activeRoute.points.length}
              </span>
            </div>
          </div>

          {/* Progress bar */}
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
        /* No active route — show assignment panel */
        <div className="bg-[#0b0f19]/30 border border-[#1e294b]/30 rounded-xl p-4">
          <p className="text-slate-400 text-xs mb-3 text-center">No active route assignment found for this vehicle.</p>

          {loadingAvailable ? (
            <div className="flex items-center justify-center py-3 text-slate-400 text-xs">
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" /> Loading routes...
            </div>
          ) : assignableRoutes.length > 0 ? (
            <div className="space-y-3">
              <select
                value={selectedRouteId ?? ""}
                onChange={(e) => setSelectedRouteId(Number(e.target.value) || null)}
                className="w-full bg-[#0b0f19] border border-slate-700 rounded p-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="" disabled>Select route to assign...</option>
                {assignableRoutes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} — {r.start_location} → {r.destination} ({r.distance.toFixed(1)} km)
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
            <div className="text-center space-y-1">
              <p className="text-slate-500 text-[10px]">No planned routes available.</p>
              <p className="text-slate-600 text-[10px]">Create one using the Trip Planner panel below.</p>
            </div>
          )}
        </div>
      )}

      {/* Available routes list */}
      {availableRoutes.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">
            All Planned Routes ({availableRoutes.length})
          </span>
          <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1">
            {availableRoutes.map((r) => (
              <div
                key={r.id}
                className="bg-[#0b0f19]/40 border border-[#1e294b]/40 rounded-lg p-2.5 flex items-center justify-between gap-2"
              >
                <div className="min-w-0">
                  <span className="text-white text-xs font-semibold block truncate">{r.name}</span>
                  <span className="text-[10px] text-slate-500 block truncate">
                    {r.start_location} → {r.destination} · {r.distance.toFixed(1)} km · {Math.round(r.estimated_duration / 60)} min
                  </span>
                </div>
                <RoutStatusBadge status={r.status} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

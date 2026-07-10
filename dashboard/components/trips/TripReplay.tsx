import React, { useEffect, useState } from "react";
import { Trip, ReplayPoint, Vehicle, VehicleTrackingSnapshot, Location, TripGoogleRoute } from "../../types";
import { api } from "../../lib/api";
import { FleetTrackingMap } from "../fleet-tracking-map";
import { useTripReplay } from "../../hooks/useTripReplay";
import { Play, Pause, RotateCcw, Clock, Gauge, Activity } from "lucide-react";
import { Button } from "../ui/button";
import { formatDate } from "../../lib/date";

interface TripReplayProps {
  trip: Trip;
  points: ReplayPoint[];
  loading: boolean;
  vehicle: Vehicle | null;
}

export function TripReplay({ trip, points, loading, vehicle }: TripReplayProps) {
  const {
    isPlaying,
    currentIndex,
    setCurrentIndex,
    playbackSpeed,
    setPlaybackSpeed,
    play,
    pause,
    reset,
    currentPoint,
    currentPath,
    totalPoints,
  } = useTripReplay(points);

  const [snapshots, setSnapshots] = useState<VehicleTrackingSnapshot[]>([]);

  // Google Route States
  const [googleRoute, setGoogleRoute] = useState<TripGoogleRoute | null>(null);
  const [googleRouteLoading, setGoogleRouteLoading] = useState(false);
  const [googleRouteError, setGoogleRouteError] = useState<string | null>(null);
  const [googleRouteNotFound, setGoogleRouteNotFound] = useState(false);
  const [showGPSRoute, setShowGPSRoute] = useState(true);
  const [showGoogleRoute, setShowGoogleRoute] = useState(true);

  const fetchGoogleRoute = async () => {
    if (googleRoute || googleRouteLoading) return;
    setGoogleRouteLoading(true);
    setGoogleRouteError(null);
    setGoogleRouteNotFound(false);
    try {
      const data = await api.getTripGoogleRoute(trip.vehicle_id, trip.id);
      setGoogleRoute(data);
    } catch (err: any) {
      if (err.message && err.message.includes("404")) {
        setGoogleRouteNotFound(true);
      } else {
        setGoogleRouteError(err.message || "Failed to load Google snapped route.");
      }
    } finally {
      setGoogleRouteLoading(false);
    }
  };

  const handleGenerateRoute = async () => {
    setGoogleRouteLoading(true);
    setGoogleRouteError(null);
    setGoogleRouteNotFound(false);
    try {
      // POST request to trigger snap route generation
      await api.generateTripGoogleRoute(trip.vehicle_id, trip.id);
      // Refetch the cached route via GET
      const data = await api.getTripGoogleRoute(trip.vehicle_id, trip.id);
      setGoogleRoute(data);
      if (data && data.status === "success" && data.encoded_polyline) {
        setShowGoogleRoute(true);
      }
    } catch (err: any) {
      setGoogleRouteError(err.message || "Failed to generate Google snapped route.");
    } finally {
      setGoogleRouteLoading(false);
    }
  };

  // Automatically fetch Google Route cache on mount/trip change
  useEffect(() => {
    const autoFetch = async () => {
      setGoogleRouteLoading(true);
      setGoogleRouteError(null);
      setGoogleRouteNotFound(false);
      try {
        const data = await api.getTripGoogleRoute(trip.vehicle_id, trip.id);
        setGoogleRoute(data);
        if (data && data.status === "success" && data.encoded_polyline) {
          setShowGoogleRoute(true);
        }
      } catch (err: any) {
        if (err.message && err.message.includes("404")) {
          setGoogleRouteNotFound(true);
          setGoogleRoute(null);
        } else {
          setGoogleRouteError(err.message || "Failed to load Google snapped route.");
        }
      } finally {
        setGoogleRouteLoading(false);
      }
    };
    autoFetch();
  }, [trip.id, trip.vehicle_id]);

  // Build the mock snapshots array required by FleetTrackingMap
  useEffect(() => {
    if (!vehicle || !currentPoint) {
      setSnapshots([]);
      return;
    }

    // Map ReplayPoint to Location structure
    const latestLocation: Location = {
      id: -1,
      vehicle_id: trip.vehicle_id,
      latitude: currentPoint.lat,
      longitude: currentPoint.lon,
      speed: currentPoint.speed,
      altitude: 0,
      timestamp: currentPoint.timestamp,
      extra_data: {
        gps_details: {
          dir: currentPoint.heading,
        },
        io: {
          ign: currentPoint.ignition,
        },
      },
    };

    // Map currentPath array to Location history
    const historyLocations: Location[] = currentPath.map((pt, idx) => ({
      id: idx,
      vehicle_id: trip.vehicle_id,
      latitude: pt.lat,
      longitude: pt.lon,
      speed: pt.speed,
      altitude: 0,
      timestamp: pt.timestamp,
    }));

    const mockSnapshot: VehicleTrackingSnapshot = {
      vehicle: vehicle,
      latest_location: latestLocation,
      route_history: historyLocations,
      latest_event: null,
      latest_command: null,
      device_config: null,
      health_status: "Healthy",
      movement_status: currentPoint.speed >= 3 ? "Moving" : "Stopped",
      packet_count: totalPoints,
    };

    setSnapshots([mockSnapshot]);
  }, [vehicle, currentPoint, currentPath, trip, totalPoints]);

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <Clock className="h-6 w-6 animate-spin mx-auto mb-2 text-cyan-400" />
        Loading replay telemetry points...
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        No coordinate points logged for this trip replay.
      </div>
    );
  }

  return (
    <div className="space-y-4 text-left">
      {/* Map Layers Toggles */}
      <div className="flex flex-col md:flex-row gap-3 items-start md:items-center justify-between bg-slate-900/60 border border-[#1e294b]/60 rounded-xl p-3 shrink-0">
        <div className="flex flex-wrap items-center gap-6 w-full md:w-auto">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Map Layers</span>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-xs font-bold text-slate-200 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showGPSRoute}
                onChange={(e) => setShowGPSRoute(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20"
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" /> GPS Replay
              </span>
            </label>

            <label className="flex items-center gap-2 text-xs font-bold text-slate-200 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showGoogleRoute}
                onChange={(e) => setShowGoogleRoute(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-cyan-500/20"
                disabled={googleRouteNotFound || !googleRoute || googleRoute.status !== "success"}
              />
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" /> Google Route
              </span>
            </label>
          </div>
        </div>

        {/* Generate or Status display */}
        <div className="text-xs">
          {googleRouteLoading && (
            <span className="text-slate-400 flex items-center gap-1.5 animate-pulse font-semibold">
              <Clock className="h-3.5 w-3.5 animate-spin text-cyan-400" /> Snapping route...
            </span>
          )}
          {googleRouteNotFound && (
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold mr-1">Google Route not generated.</span>
              <Button
                size="sm"
                onClick={handleGenerateRoute}
                className="h-8 bg-cyan-700 hover:bg-cyan-600 text-white font-bold"
              >
                Generate Google Route
              </Button>
            </div>
          )}
          {googleRoute && googleRoute.status === "success" && (
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              ✓ Google Snapped
            </span>
          )}
          {googleRoute && googleRoute.status === "failed" && (
            <span className="text-amber-400 font-bold flex items-center gap-1">
              ⚠ snapped path unavailable
            </span>
          )}
          {googleRouteError && (
            <span className="text-red-400 font-semibold flex items-center gap-1">
              Failed: {googleRouteError}
            </span>
          )}
        </div>
      </div>

      {/* Map display */}
      <div className="relative border border-[#1e294b]/60 rounded-xl overflow-hidden bg-slate-950">
        {snapshots.length > 0 && (
          <FleetTrackingMap
            snapshots={snapshots}
            selectedVehicleId={trip.vehicle_id}
            visibleVehicleIds={[trip.vehicle_id]}
            heightClass="h-[250px] sm:h-[400px]"
            isMiniMap={true}
            googleRoutePolyline={googleRoute?.encoded_polyline}
            showGoogleRoute={showGoogleRoute && googleRoute?.status === "success"}
            showGPSRoute={showGPSRoute}
            routeColor="#3b82f6"
          />
        )}
      </div>

      {/* Control console bar */}
      <div className="glass-panel border border-[#1e294b]/60 rounded-xl p-4 flex flex-col gap-3">
        {/* Timeline Slider Progress */}
        <div className="flex items-center gap-4">
          <input
            type="range"
            min={0}
            max={totalPoints - 1}
            value={currentIndex}
            onChange={(e) => setCurrentIndex(Number(e.target.value))}
            className="w-full accent-cyan-400 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
          />
          <span className="text-[10px] font-mono text-slate-400 w-16 text-right shrink-0">
            {currentIndex + 1} / {totalPoints}
          </span>
        </div>

        {/* Playback Controls & Speed selector */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            {isPlaying ? (
              <Button size="sm" onClick={pause} className="h-8 flex items-center gap-1">
                <Pause className="h-4 w-4" /> Pause
              </Button>
            ) : (
              <Button size="sm" onClick={play} className="h-8 flex items-center gap-1">
                <Play className="h-4 w-4 fill-current" /> Play
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={reset}
              className="h-8 p-2 text-slate-400 hover:text-white"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>

          {/* Speed Multipliers */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              Speed:
            </span>
            {[1, 2, 5, 10].map((speed) => (
              <button
                key={speed}
                onClick={() => setPlaybackSpeed(speed)}
                className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                  playbackSpeed === speed
                    ? "bg-cyan-500 text-slate-950 font-black"
                    : "bg-[#0b0f19] border border-[#1e294b] text-slate-400 hover:text-white"
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>

        {/* Current point metrics overlay telemetry details */}
        {currentPoint && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-[#1e294b]/20 text-[11px]">
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Time</span>
              <span className="text-white font-mono">{formatDate(currentPoint.timestamp)}</span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Speed</span>
              <span className="text-cyan-400 font-mono font-bold">
                {currentPoint.speed.toFixed(1)} km/h
              </span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Coordinates</span>
              <span className="text-white font-mono">
                {currentPoint.lat.toFixed(5)}, {currentPoint.lon.toFixed(5)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Ignition</span>
              <span className="text-white">
                {currentPoint.ignition === 1 ? (
                  <span className="text-emerald-400 font-bold">ON</span>
                ) : (
                  <span className="text-slate-400">OFF</span>
                )}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Route Information Card */}
      {googleRoute && googleRoute.status === "success" && (
        <div className="border border-[#1e294b]/60 rounded-xl p-4 bg-slate-900/40 text-left text-xs space-y-3">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Google Route Snapped Details</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Provider</span>
              <span className="text-white font-semibold uppercase">{googleRoute.provider}</span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Status</span>
              <span className="text-emerald-400 font-bold uppercase">{googleRoute.status}</span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Distance</span>
              <span className="text-white font-mono">
                {googleRoute.distance_meters 
                  ? `${(googleRoute.distance_meters / 1000).toFixed(2)} km` 
                  : "N/A"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Duration</span>
              <span className="text-white font-mono">
                {googleRoute.duration_seconds 
                  ? `${Math.floor(googleRoute.duration_seconds / 60)} min ${googleRoute.duration_seconds % 60} sec` 
                  : "N/A"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block uppercase tracking-wider">Cache Status</span>
              <span className="text-cyan-400 font-bold">Cached</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

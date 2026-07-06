import React, { useEffect, useRef, useState } from "react";
import { VehicleTrackingSnapshot } from "../../types";
import { Button } from "../ui/button";
import { Loader2, Navigation, MapPin } from "lucide-react";

interface PlannedRouteSummary {
  distance_meters: number;
  duration_seconds: number;
  status: string;
  coordinates: { lat: number; lng: number }[];
}

interface TripPlannerPanelProps {
  selectedVehicleId: number | "all";
  snapshots: VehicleTrackingSnapshot[];
  onRoutePlanned: (summary: PlannedRouteSummary | null) => void;
}

export function TripPlannerPanel({
  selectedVehicleId,
  snapshots,
  onRoutePlanned,
}: TripPlannerPanelProps) {
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [summary, setSummary] = useState<PlannedRouteSummary | null>(null);

  const autocompleteRef = useRef<any>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const destinationCoords = useRef<{ lat: number; lng: number } | null>(null);

  // Initialize Google Places Autocomplete
  useEffect(() => {
    if (typeof window === "undefined" || !window.google || !window.google.maps || !window.google.maps.places) {
      return;
    }

    if (inputRef.current && !autocompleteRef.current) {
      autocompleteRef.current = new window.google.maps.places.Autocomplete(inputRef.current, {
        fields: ["geometry", "formatted_address"],
      });

      autocompleteRef.current.addListener("place_changed", () => {
        const place = autocompleteRef.current.getPlace();
        if (place.geometry && place.geometry.location) {
          destinationCoords.current = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng(),
          };
          setDestination(place.formatted_address || "");
        } else {
          destinationCoords.current = null;
        }
      });
    }
  }, []);

  if (selectedVehicleId === "all") {
    return null;
  }

  const activeSnap = snapshots.find((s) => s.vehicle.id === selectedVehicleId);
  const currentLoc = activeSnap?.latest_location;

  const handlePlanRoute = async () => {
    if (!currentLoc) {
      setError("Current vehicle location is unknown.");
      return;
    }
    if (!destinationCoords.current) {
      setError("Please select a valid destination from the dropdown.");
      return;
    }

    setLoading(true);
    setError(null);
    setSummary(null);

    try {
      const response = await fetch("http://localhost:8000/routes/snap-path", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          waypoints: [
            [currentLoc.latitude, currentLoc.longitude],
            [destinationCoords.current.lat, destinationCoords.current.lng],
          ],
          travel_mode: "DRIVE"
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to plan route.");
      }

      const data = await response.json();
      setSummary(data);
      onRoutePlanned(data);
    } catch (err: any) {
      setError(err.message || "An error occurred while planning the route.");
      onRoutePlanned(null);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setDestination("");
    if (inputRef.current) inputRef.current.value = "";
    destinationCoords.current = null;
    setSummary(null);
    setError(null);
    onRoutePlanned(null);
  };

  return (
    <div className="bg-[#131a2d] border border-slate-800 rounded-xl p-4 flex flex-col gap-4 mt-6">
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <Navigation className="h-5 w-5 text-indigo-400" />
        <h3 className="text-white font-bold tracking-wide">Trip Planner</h3>
      </div>

      <div className="space-y-3">
        {/* Current Location (Read Only) */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Current Location
          </label>
          <div className="flex items-center gap-2 bg-[#0b0f19] border border-slate-800 rounded p-2 text-sm text-slate-300">
            <MapPin className="h-4 w-4 text-emerald-400" />
            {currentLoc
              ? `${currentLoc.latitude.toFixed(5)}, ${currentLoc.longitude.toFixed(5)}`
              : "Unknown"}
          </div>
        </div>

        {/* Destination (Google Places) */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Destination
          </label>
          <input
            ref={inputRef}
            type="text"
            className="w-full bg-[#0b0f19] border border-slate-700 rounded p-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder="Search for a destination..."
            defaultValue={destination}
            onChange={(e) => setDestination(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="text-xs text-rose-400 bg-rose-500/10 p-2 rounded border border-rose-500/20">
          {error}
        </div>
      )}

      {/* Summary Card */}
      {summary && (
        <div className="bg-indigo-500/10 border border-indigo-500/20 rounded p-3 flex flex-col gap-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-400">Distance</span>
            <span className="text-white font-semibold">
              {(summary.distance_meters / 1000).toFixed(1)} km
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-400">Duration</span>
            <span className="text-white font-semibold">
              {Math.round(summary.duration_seconds / 60)} mins
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-400">ETA</span>
            <span className="text-white font-semibold text-emerald-400">
              {new Date(Date.now() + summary.duration_seconds * 1000).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-400">Route Type</span>
            <span className="text-indigo-400 font-semibold text-xs uppercase tracking-wide">
              Fastest
            </span>
          </div>
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <Button
          onClick={handlePlanRoute}
          disabled={loading || !currentLoc || !destination}
          className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Navigation className="h-4 w-4 mr-2" />}
          Plan Route
        </Button>
        {summary && (
          <Button
            onClick={handleClear}
            variant="outline"
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}

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
  const [routeName, setRouteName] = useState("");
  const [startLocation, setStartLocation] = useState("");
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [summary, setSummary] = useState<PlannedRouteSummary | null>(null);

  const startAutocompleteRef = useRef<any>(null);
  const startInputRef = useRef<HTMLInputElement>(null);
  const startCoords = useRef<{ lat: number; lng: number } | null>(null);

  const destAutocompleteRef = useRef<any>(null);
  const destInputRef = useRef<HTMLInputElement>(null);
  const destCoords = useRef<{ lat: number; lng: number } | null>(null);

  const activeSnap = selectedVehicleId !== "all" ? snapshots.find((s) => s.vehicle.id === selectedVehicleId) : null;
  const currentLoc = activeSnap?.latest_location;

  // Initialize Google Places Autocomplete
  useEffect(() => {
    if (typeof window === "undefined" || !window.google || !window.google.maps || !window.google.maps.places) {
      return;
    }

    if (startInputRef.current && !startAutocompleteRef.current) {
      startAutocompleteRef.current = new window.google.maps.places.Autocomplete(startInputRef.current, {
        fields: ["geometry", "formatted_address"],
      });

      startAutocompleteRef.current.addListener("place_changed", () => {
        const place = startAutocompleteRef.current.getPlace();
        if (place.geometry && place.geometry.location) {
          startCoords.current = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng(),
          };
          setStartLocation(place.formatted_address || "");
        } else {
          startCoords.current = null;
        }
      });
    }

    if (destInputRef.current && !destAutocompleteRef.current) {
      destAutocompleteRef.current = new window.google.maps.places.Autocomplete(destInputRef.current, {
        fields: ["geometry", "formatted_address"],
      });

      destAutocompleteRef.current.addListener("place_changed", () => {
        const place = destAutocompleteRef.current.getPlace();
        if (place.geometry && place.geometry.location) {
          destCoords.current = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng(),
          };
          setDestination(place.formatted_address || "");
        } else {
          destCoords.current = null;
        }
      });
    }
  }, []);

  const handleUseVehicleLocation = () => {
    if (currentLoc) {
      startCoords.current = { lat: currentLoc.latitude, lng: currentLoc.longitude };
      const text = `${currentLoc.latitude.toFixed(5)}, ${currentLoc.longitude.toFixed(5)}`;
      setStartLocation(text);
      if (startInputRef.current) {
        startInputRef.current.value = text;
      }
    }
  };

  const handlePlanRoute = async () => {
    if (!startCoords.current) {
      setError("Please select a valid start location.");
      return;
    }
    if (!destCoords.current) {
      setError("Please select a valid destination.");
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
            [startCoords.current.lat, startCoords.current.lng],
            [destCoords.current.lat, destCoords.current.lng],
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

  const handleSaveRoute = async () => {
    if (!routeName.trim()) {
      setError("Please enter a route name.");
      return;
    }
    if (!summary) return;

    setSaving(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/routes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: routeName,
          start_location: startLocation || "Custom Start",
          destination: destination || "Custom End",
          distance: summary.distance_meters / 1000,
          estimated_duration: summary.duration_seconds,
          points: summary.coordinates.map((c: any, i: number) => ({
            sequence_number: i,
            latitude: c.lat,
            longitude: c.lng
          }))
        })
      });

      if (!response.ok) {
        throw new Error("Failed to save route. Check API status.");
      }

      handleClear();
      alert("Route created and saved successfully!");
    } catch (err: any) {
      setError(err.message || "An error occurred while saving the route.");
    } finally {
      setSaving(false);
    }
  };

  const handleClear = () => {
    setRouteName("");
    setStartLocation("");
    setDestination("");
    if (startInputRef.current) startInputRef.current.value = "";
    if (destInputRef.current) destInputRef.current.value = "";
    startCoords.current = null;
    destCoords.current = null;
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
        {/* Route Name */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Route Name
          </label>
          <input
            type="text"
            className="w-full bg-[#0b0f19] border border-slate-700 rounded p-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder="e.g. Surat to Valsad Route"
            value={routeName}
            onChange={(e) => setRouteName(e.target.value)}
          />
        </div>

        {/* Start Location */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Start Location
            </label>
            {currentLoc && (
              <button
                onClick={handleUseVehicleLocation}
                className="text-[9px] text-cyan-400 hover:text-cyan-300 font-extrabold uppercase"
              >
                Use Vehicle Location
              </button>
            )}
          </div>
          <input
            ref={startInputRef}
            type="text"
            className="w-full bg-[#0b0f19] border border-slate-700 rounded p-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder="Search for start location..."
            defaultValue={startLocation}
            onChange={(e) => setStartLocation(e.target.value)}
          />
        </div>

        {/* Destination */}
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Destination
          </label>
          <input
            ref={destInputRef}
            type="text"
            className="w-full bg-[#0b0f19] border border-slate-700 rounded p-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder="Search for destination..."
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
        </div>
      )}

      <div className="flex flex-col gap-2 pt-2">
        <div className="flex gap-2">
          <Button
            onClick={handlePlanRoute}
            disabled={loading || !startLocation || !destination}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Navigation className="h-4 w-4 mr-2" />}
            Plan Route
          </Button>
          {(summary || startLocation || destination) && (
            <Button
              onClick={handleClear}
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Clear
            </Button>
          )}
        </div>
        {summary && (
          <Button
            onClick={handleSaveRoute}
            disabled={saving || !routeName.trim()}
            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <MapPin className="h-4 w-4 mr-2" />}
            Save & Publish Planned Route
          </Button>
        )}
      </div>
    </div>
  );
}

"use client";

import { FleetMap } from "../../components/tracking/FleetMap";
import { MiniRouteHistoryMap } from "../../components/tracking/MiniRouteHistoryMap";
import { QuickActionsCard } from "../../components/tracking/QuickActionsCard";
import { RecentEventsCard } from "../../components/tracking/RecentEventsCard";
import { SpeedChart } from "../../components/tracking/SpeedChart";
import { SystemAlertsCard } from "../../components/tracking/SystemAlertsCard";
import { TrackingToolbar } from "../../components/tracking/TrackingToolbar";
import { VehicleDetailsPanel } from "../../components/tracking/VehicleDetailsPanel";
import { VehicleStatusCard } from "../../components/tracking/VehicleStatusCard";
import { TripPlannerPanel } from "../../components/tracking/TripPlannerPanel";
import { useFleetTracking } from "../../hooks/useFleetTracking";
import { useVehicleSelection } from "../../hooks/useVehicleSelection";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";

function TrackingPageClient() {
  const {
    snapshots,
    visibleVehicleIds,
    range,
    setRange,
    customStart,
    setCustomStart,
    customEnd,
    setCustomEnd,
    loading,
    refreshing,
    error,
    recentEvents,
    loadData,
    fleetCounts,
    speedOverviewData,
  } = useFleetTracking();

  const {
    selectedVehicleId,
    setSelectedVehicleId,
    detailTab,
    setDetailTab,
    selectedSnapshot,
    vehicleOptions,
    displayedEvents,
  } = useVehicleSelection(snapshots, recentEvents);

  const [plannedRoute, setPlannedRoute] = useState<any>(null);

  const searchParams = useSearchParams();
  const router = useRouter();
  const urlVehicleId = searchParams.get("selectVehicleId");
  const isNewVehicle = searchParams.get("newVehicle") === "true";

  const [showInitLocation, setShowInitLocation] = useState(false);
  const [mapSelectionMode, setMapSelectionMode] = useState(false);
  const [clickedCoords, setClickedCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [confirmingLocation, setConfirmingLocation] = useState(false);

  // Sync urlVehicleId to selectedVehicleId
  useEffect(() => {
    if (urlVehicleId) {
      const vid = Number(urlVehicleId);
      if (!isNaN(vid) && selectedVehicleId !== vid) {
        setSelectedVehicleId(vid);
      }
    }
  }, [urlVehicleId, selectedVehicleId, setSelectedVehicleId]);

  // Open modal if we have a selectVehicleId in url and newVehicle=true
  useEffect(() => {
    if (isNewVehicle && selectedVehicleId !== "all") {
      setShowInitLocation(true);
    }
  }, [isNewVehicle, selectedVehicleId]);

  const handleSearchLocation = async () => {
    if (!searchQuery) return;
    setSearching(true);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=5`);
      const data = await res.json();
      setSearchResults(data);
    } catch (err) {
      console.error("Geocoding failed:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleConfirmLocation = async (lat: number, lng: number) => {
    if (selectedVehicleId === "all") return;
    setConfirmingLocation(true);
    try {
      const { api } = await import("../../lib/api");
      await api.logLocation({
        vehicle_id: Number(selectedVehicleId),
        latitude: lat,
        longitude: lng,
        speed: 0,
        altitude: 0,
        timestamp: new Date().toISOString(),
        extra_data: {
          txn: "A",
          msgkey: 0,
          gps_details: {
            fix: "A",
            sat: 12,
            dir: 0,
            odo: 0
          },
          io: {
            ign: 0
          }
        }
      });
      await loadData(true);
      setShowInitLocation(false);
      setMapSelectionMode(false);
      setClickedCoords(null);
      router.push(`/tracking?selectVehicleId=${selectedVehicleId}`);
    } catch (err) {
      console.error("Failed to initialize vehicle location:", err);
      alert("Failed to initialize starting location. Please try again.");
    } finally {
      setConfirmingLocation(false);
    }
  };

  const handleMapClick = (lat: number, lng: number) => {
    if (mapSelectionMode) {
      setClickedCoords({ lat, lng });
    }
  };

  return (
    <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 select-none bg-[#0b0f19] min-h-full">
      <TrackingToolbar
        snapshots={snapshots}
        vehicleOptions={vehicleOptions}
        selectedSnapshot={selectedSnapshot}
        selectedVehicleId={selectedVehicleId}
        range={range}
        customStart={customStart}
        customEnd={customEnd}
        refreshing={refreshing}
        onSelectVehicle={setSelectedVehicleId}
        onRangeChange={setRange}
        onCustomStartChange={setCustomStart}
        onCustomEndChange={setCustomEnd}
        onRefresh={() => loadData(true)}
      />

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        <div className="lg:col-span-3 space-y-6 flex flex-col">
          <FleetMap
            snapshots={snapshots}
            selectedVehicleId={selectedVehicleId}
            visibleVehicleIds={visibleVehicleIds}
            onSelectVehicle={setSelectedVehicleId}
            plannedRoute={plannedRoute?.coordinates || []}
            onMapClick={handleMapClick}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-6">
              <VehicleStatusCard counts={fleetCounts} loading={loading} />
              <SpeedChart data={speedOverviewData} snapshots={snapshots} />
            </div>

            <RecentEventsCard
              events={displayedEvents}
              selectedVehicleId={selectedVehicleId}
              onSelectVehicle={setSelectedVehicleId}
            />
          </div>
        </div>

        <div className="space-y-6">
          <VehicleDetailsPanel
            selectedVehicleId={selectedVehicleId}
            selectedSnapshot={selectedSnapshot}
            detailTab={detailTab}
            onDetailTabChange={setDetailTab}
            onSelectVehicle={setSelectedVehicleId}
          />

          <TripPlannerPanel
            selectedVehicleId={selectedVehicleId}
            snapshots={snapshots}
            onRoutePlanned={setPlannedRoute}
          />

          <MiniRouteHistoryMap
            selectedVehicleId={selectedVehicleId}
            selectedSnapshot={selectedSnapshot}
            snapshots={snapshots}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <QuickActionsCard snapshots={snapshots} />
        <SystemAlertsCard offlineCount={fleetCounts.offline} />
      </div>

      {/* Interactive Click on Map banner */}
      {mapSelectionMode && selectedSnapshot && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-[1000] bg-[#131a2d]/95 border border-cyan-500/50 rounded-xl px-6 py-3 shadow-2xl flex items-center gap-4 text-xs font-semibold text-white">
          <span className="flex items-center gap-1.5 animate-pulse text-cyan-400 font-bold">
            📍 Click anywhere on the map to set the initial location for {selectedSnapshot.vehicle.vehicle_name}
          </span>
          <button
            onClick={() => {
              setMapSelectionMode(false);
              setShowInitLocation(true);
            }}
            className="bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 px-2 py-1 rounded transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Confirmation prompt for map clicked coordinate */}
      {clickedCoords && selectedSnapshot && (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-[#070b13]/85 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-xs bg-[#131a2d] border border-[#1e294b] rounded-2xl p-5 shadow-2xl space-y-4 text-center">
            <h3 className="text-sm font-extrabold text-white">Confirm Starting Location</h3>
            <p className="text-xs text-slate-400">
              Set the starting position of <strong className="text-cyan-400">{selectedSnapshot.vehicle.vehicle_name}</strong> to:
            </p>
            <div className="bg-[#0b0f19] border border-[#1e294b]/60 rounded-lg p-2 font-mono text-[11px] text-slate-300">
              {clickedCoords.lat.toFixed(6)}, {clickedCoords.lng.toFixed(6)}
            </div>
            <div className="flex gap-2 justify-center pt-2">
              <button
                onClick={() => {
                  handleConfirmLocation(clickedCoords.lat, clickedCoords.lng);
                }}
                disabled={confirmingLocation}
                className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors flex-1"
              >
                {confirmingLocation ? "Saving..." : "Confirm"}
              </button>
              <button
                onClick={() => setClickedCoords(null)}
                className="bg-[#1b253b] hover:bg-[#253350] text-slate-400 hover:text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Choice Overlay Modal */}
      {showInitLocation && selectedSnapshot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#070b13]/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-[#131a2d] border border-[#1e294b] rounded-2xl p-6 shadow-2xl space-y-6 text-left">
            <div>
              <h3 className="text-lg font-extrabold text-white">Initialize Starting Location</h3>
              <p className="text-xs text-slate-400 mt-1">
                Configure the starting location for <span className="text-cyan-400 font-bold">{selectedSnapshot.vehicle.vehicle_name}</span> to register its marker and allow route planning.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {/* Option 1: Click on Map */}
              <button
                onClick={() => {
                  setShowInitLocation(false);
                  setMapSelectionMode(true);
                }}
                className="p-4 bg-[#0b0f19]/50 hover:bg-[#1b253b]/50 border border-[#1e294b]/60 hover:border-cyan-500/50 rounded-xl space-y-2 text-left transition-all"
              >
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-cyan-400">Method 1</span>
                <h4 className="text-xs font-bold text-white">Click on Map</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">Select any coordinate point visually directly on the Google Map.</p>
              </button>

              {/* Option 2: Default System Hub */}
              <button
                onClick={() => handleConfirmLocation(22.3072, 73.1812)}
                disabled={confirmingLocation}
                className="p-4 bg-[#0b0f19]/50 hover:bg-[#1b253b]/50 border border-[#1e294b]/60 hover:border-cyan-500/50 rounded-xl space-y-2 text-left transition-all disabled:opacity-40"
              >
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-cyan-400">Method 2</span>
                <h4 className="text-xs font-bold text-white">VTS Central Hub</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed">Default coordinates at system headquarters (Vadodara: 22.3072, 73.1812).</p>
              </button>
            </div>

            {/* Option 3: Address Search */}
            <div className="p-4 bg-[#0b0f19]/50 border border-[#1e294b]/60 rounded-xl space-y-3">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-cyan-400 block">Method 3</span>
              <h4 className="text-xs font-bold text-white">Search Address</h4>
              <p className="text-[10px] text-slate-400">Search for a starting city or address.</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. Vadodara, Ahmedabad, Mumbai"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearchLocation()}
                  className="flex-1 bg-[#070b13] border border-[#1e294b] text-xs text-white rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-400"
                />
                <button
                  onClick={handleSearchLocation}
                  disabled={searching}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition-colors"
                >
                  {searching ? "Searching..." : "Search"}
                </button>
              </div>

              {searchResults.length > 0 && (
                <div className="max-h-36 overflow-y-auto space-y-1.5 border-t border-[#1e294b]/40 pt-2">
                  {searchResults.map((result, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleConfirmLocation(Number(result.lat), Number(result.lon))}
                      disabled={confirmingLocation}
                      className="w-full text-left p-2 hover:bg-[#1b253b]/50 rounded text-[11px] text-slate-300 hover:text-white transition-colors border border-transparent hover:border-[#1e294b] flex flex-col"
                    >
                      <span className="font-bold truncate">{result.display_name}</span>
                      <span className="text-[9px] text-slate-500 font-mono mt-0.5">{Number(result.lat).toFixed(4)}, {Number(result.lon).toFixed(4)}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setShowInitLocation(false);
                  router.push(`/tracking?selectVehicleId=${selectedVehicleId}`);
                }}
                className="text-xs text-slate-400 hover:text-white font-bold px-4 py-2"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TrackingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center text-slate-400">
        Loading Map Tracker...
      </div>
    }>
      <TrackingPageClient />
    </Suspense>
  );
}

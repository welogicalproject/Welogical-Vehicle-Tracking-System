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
import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";

export default function TrackingPage() {
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
      router.push(`/tracking?selectVehicleId=${selectedVehicleId}`);
    } catch (err) {
      console.error("Failed to initialize vehicle location:", err);
      alert("Failed to initialize starting location. Please try again.");
    } finally {
      setConfirmingLocation(false);
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

      {showInitLocation && selectedSnapshot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#070b13]/80 backdrop-blur-md p-4">
          <div className="w-full max-w-md bg-[#131a2d]/90 border border-[#1e294b] rounded-2xl p-6 shadow-2xl space-y-6 text-left">
            <div>
              <h3 className="text-lg font-extrabold text-white">Initialize Starting Location</h3>
              <p className="text-xs text-slate-400 mt-1">
                Set an initial location for <span className="text-cyan-400 font-bold">{selectedSnapshot.vehicle.vehicle_name}</span> to register its marker and enable route planning.
              </p>
            </div>

            {/* Option 1 */}
            <div className="p-4 bg-[#0b0f19]/50 border border-[#1e294b]/60 rounded-xl space-y-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 block">Option 1</span>
              <h4 className="text-xs font-bold text-white">Use Default System Coordinates</h4>
              <p className="text-[11px] text-slate-400">Places the vehicle at the VTS Central Hub (Vadodara: 22.3072, 73.1812).</p>
              <button
                onClick={() => handleConfirmLocation(22.3072, 73.1812)}
                disabled={confirmingLocation}
                className="w-full bg-[#1b253b] hover:bg-[#253350] border border-[#1e294b] text-white font-bold text-xs py-2 rounded-lg transition-colors mt-2"
              >
                {confirmingLocation ? "Setting position..." : "Set Position to Hub"}
              </button>
            </div>

            {/* Option 2 */}
            <div className="p-4 bg-[#0b0f19]/50 border border-[#1e294b]/60 rounded-xl space-y-3">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 block">Option 2</span>
              <h4 className="text-xs font-bold text-white">Search Location</h4>
              <p className="text-[11px] text-slate-400">Search for a starting city or address.</p>
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

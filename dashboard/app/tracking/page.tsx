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
import { useState } from "react";

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

  return (
    <div className="p-6 space-y-6 select-none bg-[#0b0f19] min-h-full">
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
    </div>
  );
}

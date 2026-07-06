"use client";

import React, { use, useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  Car,
  Command,
  FileText,
  RefreshCw,
  Route,
  Settings,
  LineChart as LineChartIcon,
  Calendar,
} from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { cn } from "../../../lib/utils";
import { api } from "../../../lib/api";
import { Button } from "../../../components/ui/button";
import { DeviceCommand, Event, VehicleTrackingSnapshot } from "../../../types";
import { useVehicleDetailsPlayback } from "../../../hooks/useVehicleDetailsPlayback";
import { useTrips } from "../../../hooks/useTrips";
import { TripTable } from "../../../components/trips/TripTable";
import { TripDrawer } from "../../../components/trips/TripDrawer";
import { TripRebuildButton } from "../../../components/trips/TripRebuildButton";

// Subcomponents
import { OverviewTab } from "../../../components/vehicles/OverviewTab";
import { EventsTab } from "../../../components/vehicles/EventsTab";
import { CommandsTab } from "../../../components/vehicles/CommandsTab";
import { ConfigurationsTab } from "../../../components/vehicles/ConfigurationsTab";
import { RoutePlaybackTab } from "../../../components/vehicles/RoutePlaybackTab";
import { TelemetryChartsTab } from "../../../components/vehicles/TelemetryChartsTab";

interface PageProps {
  params: Promise<{ id: string }>;
}

type TabKey = "overview" | "events" | "commands" | "configurations" | "route" | "charts" | "trips";

const tabs: { key: TabKey; label: string; icon: any }[] = [
  { key: "overview", label: "Overview", icon: Car },
  { key: "events", label: "Events", icon: FileText },
  { key: "trips", label: "Trips History", icon: Calendar },
  { key: "commands", label: "Commands", icon: Command },
  { key: "configurations", label: "Configurations", icon: Settings },
  { key: "route", label: "Route Playback", icon: Route },
  { key: "charts", label: "Telemetry Charts", icon: LineChartIcon },
];

export default function VehicleDetailsPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const vehicleId = Number(resolvedParams.id);
  const searchParams = useSearchParams();

  const [snapshot, setSnapshot] = useState<VehicleTrackingSnapshot | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [commands, setCommands] = useState<DeviceCommand[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [eventSearch, setEventSearch] = useState("");
  const [eventPage, setEventPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Trips data hook and drawer state
  const { trips, loading: loadingTrips, loadTrips } = useTrips(vehicleId);
  const [selectedTrip, setSelectedTrip] = useState<any | null>(null);

  // Playback logic from custom hook
  const {
    playbackActive,
    setPlaybackActive,
    playbackIndex,
    setPlaybackIndex,
    activeSnapshot,
    routeStats,
  } = useVehicleDetailsPlayback(snapshot);

  const loadData = useCallback(
    async (silent = false) => {
      if (silent) setRefreshing(true);
      else setLoading(true);

      try {
        const end = new Date();
        const start = new Date(end.getTime() - 24 * 60 * 60_000);
        const [tracking, eventRows, commandRows] = await Promise.all([
          api.getVehicleTracking(vehicleId, start.toISOString(), end.toISOString(), 2000),
          api.getVehicleEvents(vehicleId, undefined, 0, 250),
          api.getVehicleCommands(vehicleId, undefined, 0, 250),
        ]);
        setSnapshot(tracking);
        setEvents(eventRows);
        setCommands(commandRows);
        setError(null);
      } catch (err: any) {
        setError(err.message || "Failed to load vehicle details.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [vehicleId]
  );

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Read URL query params to trigger route view / playback auto
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam === "route") {
      setActiveTab("route");
    }
    const playbackParam = searchParams.get("playback");
    if (playbackParam === "true") {
      setPlaybackActive(true);
    }
  }, [searchParams, setPlaybackActive]);

  return (
    <div className="space-y-6 p-6 lg:p-8 select-none">
      {/* View Title */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-[#1e294b]/60 pb-5">
        <div className="flex items-center gap-4">
          <Link
            href="/vehicles"
            className="rounded-lg border border-[#1e294b]/60 bg-[#131a2d]/40 p-2 text-slate-400 hover:bg-[#1e294b] hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div className="text-left">
            <h1 className="text-2xl font-bold text-white">
              {snapshot?.vehicle.vehicle_name || "Vehicle Profile"}
            </h1>
            <p className="text-xs text-slate-500 font-semibold tracking-wide mt-0.5">
              Asset ID: {vehicleId} &bull; Device UID: {snapshot?.vehicle.device_uid}
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 border border-[#1e294b]/60 bg-[#131a2d]"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
          Refresh Profile
        </Button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-300 font-semibold">
          {error}
        </div>
      )}

      {loading && !snapshot ? (
        <div className="py-16 text-center text-sm text-slate-400">Loading profile data...</div>
      ) : !snapshot ? (
        <div className="py-16 text-center text-sm text-slate-400">Asset profile not found.</div>
      ) : (
        <>
          {/* Tabs bar */}
          <div className="flex flex-wrap gap-2 border-b border-[#1e294b]/20 pb-4">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                onClick={() => {
                  setActiveTab(key);
                  if (key !== "route") setPlaybackActive(false);
                }}
                className={cn(
                  "inline-flex items-center rounded-lg border px-3 py-2 text-xs font-semibold transition-all",
                  activeTab === key
                    ? "border-cyan-400 bg-cyan-500/10 text-cyan-200"
                    : "border-[#1e294b]/60 bg-[#131a2d]/40 text-slate-400 hover:text-white"
                )}
              >
                <Icon className="mr-1.5 h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Overview tab */}
          {activeTab === "overview" && (
            <OverviewTab snapshot={snapshot} vehicleId={vehicleId} onAssignmentChange={() => loadData(true)} trips={trips} />
          )}

          {/* Events tab */}
          {activeTab === "events" && (
            <EventsTab
              events={events}
              eventSearch={eventSearch}
              setEventSearch={setEventSearch}
              eventPage={eventPage}
              setEventPage={setEventPage}
            />
          )}

          {/* Commands tab */}
          {activeTab === "commands" && <CommandsTab commands={commands} />}

          {/* Configurations tab */}
          {activeTab === "configurations" && <ConfigurationsTab snapshot={snapshot} />}

          {/* Route Playback tab */}
          {activeTab === "route" && (
            <RoutePlaybackTab
              snapshot={snapshot}
              activeSnapshot={activeSnapshot}
              playbackActive={playbackActive}
              setPlaybackActive={setPlaybackActive}
              playbackIndex={playbackIndex}
              setPlaybackIndex={setPlaybackIndex}
              routeStats={routeStats}
            />
          )}

          {/* Telemetry Charts tab */}
          {activeTab === "charts" && <TelemetryChartsTab snapshot={snapshot} />}

          {/* Trips tab */}
          {activeTab === "trips" && (
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="text-left">
                  <h3 className="text-lg font-bold text-white">Trips History</h3>
                  <p className="text-xs text-slate-400">Reconstruct and review past travel logs.</p>
                </div>
                <TripRebuildButton vehicleId={vehicleId} onRebuildComplete={loadTrips} />
              </div>
              <TripTable
                trips={trips}
                loading={loadingTrips}
                onSelectTrip={setSelectedTrip}
                hideVehicleColumn={true}
              />
            </div>
          )}
        </>
      )}

      {/* Trip Details Slide Drawer */}
      <TripDrawer
        trip={selectedTrip}
        onClose={() => setSelectedTrip(null)}
        vehicles={snapshot?.vehicle ? [snapshot.vehicle] : []}
      />
    </div>
  );
}

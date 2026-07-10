"use client";

import React, { useState } from "react";
import { useTrips } from "../../hooks/useTrips";
import { TripFilters } from "../../components/trips/TripFilters";
import { TripTable } from "../../components/trips/TripTable";
import { TripStatistics } from "../../components/trips/TripStatistics";
import { TripDrawer } from "../../components/trips/TripDrawer";
import { TripRebuildButton } from "../../components/trips/TripRebuildButton";
import { Calendar, Compass } from "lucide-react";

export default function TripsPage() {
  const {
    vehicleId,
    setVehicleId,
    status,
    setStatus,
    startTime,
    setStartTime,
    endTime,
    setEndTime,
    trips,
    vehicles,
    loading,
    error,
    loadTrips,
  } = useTrips("all");

  const [selectedTrip, setSelectedTrip] = useState<any | null>(null);

  const handleRefresh = () => {
    loadTrips();
  };

  const handleRebuildCompleted = () => {
    loadTrips();
  };

  return (
<<<<<<< HEAD
    <div className="p-4 sm:p-8 space-y-4 sm:space-y-6 max-w-[1600px] mx-auto select-none">
=======
    <div className="p-8 space-y-6 max-w-[1600px] mx-auto select-none">
>>>>>>> 57e7858 (Refactor VTS architecture and standalone simulator)
      {/* Header and Rebuild Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="text-left">
          <h2 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            <Compass className="h-6 w-6 text-cyan-400" />
            Trip Management Workspace
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Analyze vehicle trips, evaluate driving behavior scores, and replay geographic routes history.
          </p>
        </div>

        {/* Rebuild option visible only when a specific vehicle is selected */}
        {vehicleId !== "all" && (
          <TripRebuildButton
            vehicleId={Number(vehicleId)}
            onRebuildComplete={handleRebuildCompleted}
          />
        )}
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold text-left">
          {error}
        </div>
      )}

      {/* Aggregate Statistics Header */}
      <TripStatistics trips={trips} loading={loading} />

      {/* Filters Toolbar */}
      <TripFilters
        vehicleId={vehicleId}
        setVehicleId={setVehicleId}
        status={status}
        setStatus={setStatus}
        startTime={startTime}
        setStartTime={setStartTime}
        endTime={endTime}
        setEndTime={setEndTime}
        vehicles={vehicles}
        onRefresh={handleRefresh}
        refreshing={loading}
      />

      {/* Main Grid Trips List Table */}
      <TripTable
        trips={trips}
        loading={loading}
        onSelectTrip={setSelectedTrip}
      />

      {/* Detail Slide Drawer View */}
      <TripDrawer
        trip={selectedTrip}
        onClose={() => setSelectedTrip(null)}
        vehicles={vehicles}
      />
    </div>
  );
}

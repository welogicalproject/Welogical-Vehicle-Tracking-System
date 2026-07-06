"use client";

import React, { useEffect, useState, useCallback } from "react";
import { api } from "../../lib/api";
import { Vehicle, Location, RawPacket } from "../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";

// Extracted Components
import { ExplorerToolbar } from "../../components/explorer/ExplorerToolbar";
import { ExplorerPagination } from "../../components/explorer/ExplorerPagination";
import { VehiclesTable, LocationsTable, RawPacketsTable } from "../../components/explorer/ExplorerTables";

type ActiveTab = "vehicles" | "locations" | "packets";

export default function ExplorerPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("vehicles");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [packets, setPackets] = useState<RawPacket[]>([]);

  // Search states
  const [search, setSearch] = useState("");

  // Pagination states
  const [page, setPage] = useState(1);
  const limit = 15; // 15 records per page in database explorer view

  const loadData = useCallback(
    async (isSilent = false) => {
      if (!isSilent) setLoading(true);
      else setRefreshing(true);
      try {
        const skip = (page - 1) * limit;

        if (activeTab === "vehicles") {
          const res = await api.getVehicles(skip, limit);
          setVehicles(res);
        } else if (activeTab === "locations") {
          const res = await api.getAllLocations(skip, limit);
          setLocations(res);
        } else if (activeTab === "packets") {
          const res = await api.getRawPackets(skip, limit);
          setPackets(res);
        }
        setError(null);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to retrieve explorer records.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activeTab, page, limit]
  );

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Reset pagination on tab change
  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    setSearch("");
    setPage(1);
  };

  const handleNextPage = () => {
    setPage((p) => p + 1);
  };

  const handlePrevPage = () => {
    setPage((p) => Math.max(1, p - 1));
  };

  // Filter lists locally
  const filteredVehicles = vehicles.filter(
    (v) =>
      v.vehicle_name.toLowerCase().includes(search.toLowerCase()) ||
      v.device_uid.toLowerCase().includes(search.toLowerCase()) ||
      v.vehicle_type.toLowerCase().includes(search.toLowerCase())
  );

  const filteredLocations = locations.filter(
    (l) =>
      l.vehicle_id.toString().includes(search) ||
      l.latitude.toString().includes(search) ||
      l.longitude.toString().includes(search) ||
      l.speed.toString().includes(search)
  );

  const filteredPackets = packets.filter(
    (p) =>
      p.device_uid?.toLowerCase().includes(search.toLowerCase()) ||
      p.message_id?.toString().includes(search) ||
      p.id.toString().includes(search)
  );

  const isNextDisabled = () => {
    if (activeTab === "vehicles") return filteredVehicles.length < limit;
    if (activeTab === "locations") return filteredLocations.length < limit;
    return filteredPackets.length < limit;
  };

  return (
    <div className="p-8 space-y-8 select-none">
      {/* Action Header bar */}
      <ExplorerToolbar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        search={search}
        onSearchChange={setSearch}
        refreshing={refreshing}
        onRefresh={() => loadData(true)}
      />

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Explorer Content Table Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1e294b]/40 pb-4">
          <div className="text-left">
            <CardTitle className="text-white text-sm capitalize">{activeTab} Registry</CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Direct low-level database table columns viewer.
            </CardDescription>
          </div>

          {/* Pagination */}
          <ExplorerPagination
            page={page}
            onPrevPage={handlePrevPage}
            onNextPage={handleNextPage}
            nextDisabled={isNextDisabled()}
          />
        </CardHeader>

        <CardContent className="p-0">
          {loading && !refreshing ? (
            <div className="text-center py-12 text-slate-400 text-xs">Querying PostgreSQL rows...</div>
          ) : (
            <>
              {activeTab === "vehicles" && (
                <VehiclesTable vehicles={filteredVehicles} loading={loading} />
              )}

              {activeTab === "locations" && (
                <LocationsTable locations={filteredLocations} loading={loading} />
              )}

              {activeTab === "packets" && (
                <RawPacketsTable packets={filteredPackets} loading={loading} />
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

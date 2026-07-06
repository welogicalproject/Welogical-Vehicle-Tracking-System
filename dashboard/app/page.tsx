"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { api } from "../lib/api";
import { Vehicle, SystemStats, Event, EventStats } from "../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { EventDistributionChart } from "../components/charts";

// Dashboard Components
import { DashboardRefreshToolbar } from "../components/dashboard/DashboardRefreshToolbar";
import { StatsGrid } from "../components/dashboard/StatsGrid";
import { AlertsPriorityCounter } from "../components/dashboard/AlertsPriorityCounter";
import { FleetOperationsSummary } from "../components/dashboard/FleetOperationsSummary";
import { RecentEventsTable } from "../components/dashboard/RecentEventsTable";

export default function OverviewPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [eventsStats, setEventsStats] = useState<EventStats | null>(null);
  const [recentEvents, setRecentEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    try {
      const [statsRes, vehiclesRes, evStatsRes, recentEvRes] = await Promise.all([
        api.getStats().catch(() => null),
        api.getVehicles(0, 100).catch(() => []),
        api.getEventsStats().catch(() => null),
        api.getRecentEvents(10).catch(() => []),
      ]);

      setStats(statsRes);
      setVehicles(vehiclesRes);
      setEventsStats(evStatsRes);
      setRecentEvents(recentEvRes);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve dashboard telemetry data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial load and 10s auto-refresh
  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData(true); // Silent reload in background
    }, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleManualRefresh = () => {
    loadData(true);
  };

  // Compute status metrics
  const activeOnlineCount = stats ? stats.vehicles_online : 0;
  const activeIdleCount = stats ? stats.vehicles_idle : 0;
  const activeOfflineCount = stats ? stats.vehicles_offline : 0;
  const totalVehiclesCount = stats ? stats.total_vehicles : vehicles.length;

  const eventDistributionData = useMemo(() => {
    if (!eventsStats) return [];
    return [
      { name: "Critical Alerts", value: eventsStats.critical, color: "#ef4444" },
      { name: "Warning Alerts", value: eventsStats.warning, color: "#f59e0b" },
      { name: "Info Alerts", value: eventsStats.info, color: "#06b6d4" },
    ].filter((d) => d.value > 0);
  }, [eventsStats]);

  return (
    <div className="p-8 space-y-8 max-w-[1600px] mx-auto">
      {/* Refresh Bar */}
      <DashboardRefreshToolbar refreshing={refreshing} onRefresh={handleManualRefresh} />

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Stats Cards Grid */}
      <StatsGrid
        loading={loading}
        totalVehiclesCount={totalVehiclesCount}
        activeOnlineCount={activeOnlineCount}
        activeIdleCount={activeIdleCount}
        activeOfflineCount={activeOfflineCount}
      />

      {/* Main Charts & Alerts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Event Severity Badges */}
        <AlertsPriorityCounter eventsStats={eventsStats} />

        {/* Event Distribution Chart */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base">Event Distribution</CardTitle>
            <CardDescription>Alert severity proportions.</CardDescription>
          </CardHeader>
          <CardContent className="p-4 flex items-center justify-center">
            {eventDistributionData.length > 0 ? (
              <EventDistributionChart data={eventDistributionData} />
            ) : (
              <div className="text-slate-400 text-xs py-12">No event records found</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tables Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Vehicles Registry Summary */}
        <FleetOperationsSummary vehicles={vehicles} />

        {/* Recent Decoded Alerts */}
        <RecentEventsTable recentEvents={recentEvents} />
      </div>
    </div>
  );
}

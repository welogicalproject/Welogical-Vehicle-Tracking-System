"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { api } from "../lib/api";
import { Vehicle, SystemStats, Event, EventStats, VehicleTrackingSnapshot } from "../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { EventDistributionChart } from "../components/charts";
import { useFleet } from "../context/FleetContext";

// Dashboard Components
import { DashboardRefreshToolbar } from "../components/dashboard/DashboardRefreshToolbar";
import { StatsGrid } from "../components/dashboard/StatsGrid";
import { FleetOperationsSummary } from "../components/dashboard/FleetOperationsSummary";
import { SlidersHorizontal, Battery, Zap, Thermometer, ShieldAlert, Clock, AlertTriangle, Play, CheckCircle, Database } from "lucide-react";
import { cn } from "../lib/utils";
import { getPacketVal, getStatus } from "../utils/tracking";

// Recharts for Utilization & Fuel Trend placeholders
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar } from "recharts";

// Mock data for future analytics placeholders (utilization & fuel trends)
const UTILIZATION_MOCK_DATA = [
  { day: "Mon", driving: 12.5, idling: 2.1, parked: 9.4 },
  { day: "Tue", driving: 14.0, idling: 1.8, parked: 8.2 },
  { day: "Wed", driving: 11.2, idling: 2.5, parked: 10.3 },
  { day: "Thu", driving: 15.1, idling: 1.2, parked: 7.7 },
  { day: "Fri", driving: 13.8, idling: 2.0, parked: 8.2 },
  { day: "Sat", driving: 6.2, idling: 0.5, parked: 17.3 },
  { day: "Sun", driving: 4.1, idling: 0.2, parked: 19.7 },
];

const FUEL_MOCK_DATA = [
  { name: "Demo-007", burned: 42.1 },
  { name: "Demo-008", burned: 58.4 },
  { name: "Demo-009", burned: 31.2 },
  { name: "Demo-010", burned: 12.8 },
];

export default function OverviewPage() {
  const {
    stats,
    vehicles,
    eventsStats,
    recentEvents,
    snapshots: trackingSnapshots,
    loading,
    refreshing,
    error,
    loadData
  } = useFleet();

  const [fleetAnalytics, setFleetAnalytics] = useState<any>(null);

  useEffect(() => {
    api.getFleetAnalyticsToday().then(setFleetAnalytics).catch(console.error);
  }, [vehicles]);

  const handleManualRefresh = () => {
    loadData(true);
    api.getFleetAnalyticsToday().then(setFleetAnalytics).catch(console.error);
  };

  // 1. Compute dynamic Fleet Operational Status counts
  const totalVehiclesCount = stats ? stats.total_vehicles : vehicles.length;
  
  const statusCounts = useMemo(() => {
    let driving = 0;
    let idle = 0;
    let parked = 0;
    let offline = 0;
    let gpsLost = 0;

    vehicles.forEach(v => {
      const status = getStatus(v.last_seen, v.is_connected);
      const snapshot = trackingSnapshots.find(s => s.vehicle.id === v.id);

      if (status === "offline") {
        offline++;
      } else {
        const extra = snapshot?.latest_location?.extra_data;
        const ign = extra?.io?.ign;
        const speed = snapshot?.latest_location?.speed ?? 0;

        if (ign === 1) {
          if (speed > 0) driving++;
          else idle++;
        } else {
          parked++;
        }

        // GPS Lost check
        const gpsFix = extra?.gps?.fix ?? extra?.gps_details?.fix;
        const satCount = extra?.gps?.satellites ?? extra?.gps?.sat ?? extra?.gps_details?.sat;
        if (gpsFix === "V" || satCount === 0) {
          gpsLost++;
        }
      }
    });

    return { driving, idle, parked, offline, gpsLost };
  }, [vehicles, trackingSnapshots]);

  // 2. Identify and prioritizing Vehicles requiring immediate attention
  const needsAttentionList = useMemo(() => {
    const list: Array<{
      id: number;
      name: string;
      uid: string;
      reason: string;
      severity: "critical" | "warning" | "info";
      priority: number;
      icon: React.ReactNode;
    }> = [];

    trackingSnapshots.forEach(s => {
      const extra = s.latest_location?.extra_data;
      if (!extra) return;

      // Critical main power disconnect (Priority 3)
      const mainPower = extra.pwr?.main;
      if (mainPower === 0) {
        list.push({
          id: s.vehicle.id,
          name: s.vehicle.vehicle_name,
          uid: s.vehicle.device_uid,
          reason: "Main Power Cut (Running on backup battery)",
          severity: "critical",
          priority: 3,
          icon: <Zap className="h-4 w-4 text-rose-400" />,
        });
      }

      // Critical coolant temperature heating (Priority 3)
      const coolant = extra.engine?.coolant_temperature;
      if (typeof coolant === "number" && coolant > 98.0) {
        list.push({
          id: s.vehicle.id,
          name: s.vehicle.vehicle_name,
          uid: s.vehicle.device_uid,
          reason: `High Engine Coolant Temp (${coolant.toFixed(1)}°C)`,
          severity: "critical",
          priority: 3,
          icon: <Thermometer className="h-4 w-4 text-rose-400 font-bold" />,
        });
      }

      // Warning Low Fuel (< 10%) (Priority 2)
      const fuelPct = extra.fuel?.percentage ?? (typeof extra.io?.analog?.[2] === "number" ? extra.io.analog[2] / 100 : null);
      if (typeof fuelPct === "number" && fuelPct < 10.0) {
        list.push({
          id: s.vehicle.id,
          name: s.vehicle.vehicle_name,
          uid: s.vehicle.device_uid,
          reason: `Low Fuel Alert (${fuelPct.toFixed(1)}%)`,
          severity: "warning",
          priority: 2,
          icon: <SlidersHorizontal className="h-4 w-4 text-amber-400" />,
        });
      }

      // Warning Main Battery low (Priority 2)
      const mvolt = extra.power?.main_voltage ?? extra.pwr?.mvolt;
      if (typeof mvolt === "number" && mvolt < 11.5 && mvolt > 0.0) {
        list.push({
          id: s.vehicle.id,
          name: s.vehicle.vehicle_name,
          uid: s.vehicle.device_uid,
          reason: `Main Battery Low (${mvolt.toFixed(1)} V)`,
          severity: "warning",
          priority: 2,
          icon: <Battery className="h-4 w-4 text-amber-400" />,
        });
      }

      // Information GPS Lost (Priority 1)
      const gpsFix = extra?.gps?.fix ?? extra?.gps_details?.fix;
      const satCount = extra?.gps?.satellites ?? extra?.gps?.sat ?? extra?.gps_details?.sat;
      if (gpsFix === "V" || satCount === 0) {
        list.push({
          id: s.vehicle.id,
          name: s.vehicle.vehicle_name,
          uid: s.vehicle.device_uid,
          reason: "GPS Receiver Lost Fix",
          severity: "info",
          priority: 1,
          icon: <ShieldAlert className="h-4 w-4 text-cyan-400" />,
        });
      }
    });

    // Sort priority desc (3 -> 2 -> 1)
    list.sort((a, b) => b.priority - a.priority);
    return list;
  }, [trackingSnapshots]);

  // Chart severity statistics
  const eventDistributionData = useMemo(() => {
    if (!eventsStats) return [];
    return [
      { name: "Critical Alerts", value: eventsStats.critical, color: "#ef4444" },
      { name: "Warning Alerts", value: eventsStats.warning, color: "#f59e0b" },
      { name: "Info Alerts", value: eventsStats.info, color: "#06b6d4" },
    ].filter((d) => d.value > 0);
  }, [eventsStats]);

  // Unified empty-state template
  const RenderEmptyState = ({ title, description }: { title: string; description: string }) => (
    <div className="flex flex-col items-center justify-center h-full text-center p-6 border border-dashed border-[#1e294b]/60 rounded-lg bg-[#131a2d]/20">
      <Database className="h-8 w-8 text-slate-500 mb-2 animate-pulse" />
      <span className="text-xs font-bold text-slate-400 block">{title}</span>
      <span className="text-[10px] text-slate-500 block max-w-[200px] mt-1">{description}</span>
    </div>
  );

  // If initial load is in progress, display a premium layout skeleton
  if (loading && trackingSnapshots.length === 0) {
    return (
      <div className="p-4 sm:p-8 space-y-6 max-w-[1600px] mx-auto">
        <div className="h-10 bg-[#1e294b]/20 border border-[#1e294b]/10 rounded-lg animate-pulse w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-20 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="h-64 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
              <div className="h-64 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="h-64 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
              <div className="md:col-span-2 h-64 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
            </div>
          </div>
          <div className="space-y-6">
            <div className="h-72 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
            <div className="h-36 bg-[#131a2d]/40 border border-[#1e294b]/40 rounded-xl animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-8 space-y-6 max-w-[1600px] mx-auto">
      {/* Top refresh bar */}
      <DashboardRefreshToolbar refreshing={refreshing} onRefresh={handleManualRefresh} />

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* 1. Fleet KPIs Grid (8 cards) */}
      <StatsGrid
        loading={loading}
        totalVehiclesCount={totalVehiclesCount}
        drivingCount={statusCounts.driving}
        idleCount={statusCounts.idle}
        parkedCount={statusCounts.parked}
        offlineCount={statusCounts.offline}
        gpsLostCount={statusCounts.gpsLost}
        distanceToday={fleetAnalytics?.total_distance_km}
        fuelUsedToday={fleetAnalytics?.total_fuel_consumed_l}
      />

      {/* 2. Middle Grid: Analytics & Health Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left / Center Column (2/3 width) - Charts placeholders */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Fleet Utilization Stacked Chart Placeholder */}
            <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 text-left flex flex-col justify-between">
              <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white text-sm">Fleet Utilization</CardTitle>
                  <CardDescription className="text-[11px]">Cumulative driving, idle, and parking times</CardDescription>
                </div>
                {(!fleetAnalytics || (fleetAnalytics.total_engine_hours === 0 && fleetAnalytics.total_driving_hours === 0)) && (
                  <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase">Coming Soon</span>
                )}
              </CardHeader>
              <CardContent className="p-0 h-44 w-full flex flex-col justify-center">
                {fleetAnalytics && (fleetAnalytics.total_engine_hours > 0 || fleetAnalytics.total_driving_hours > 0) ? (
                  <div className="space-y-4 px-2">
                    <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                      <span className="text-slate-400">Total Engine Runtime</span>
                      <span className="text-white font-mono font-bold">{fleetAnalytics.total_engine_hours.toFixed(1)} hrs</span>
                    </div>
                    <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                      <span className="text-emerald-400">Driving Duration</span>
                      <span className="text-emerald-400 font-mono font-bold">{fleetAnalytics.total_driving_hours.toFixed(1)} hrs</span>
                    </div>
                    <div className="flex justify-between items-center text-xs pb-1">
                      <span className="text-amber-400">Idling Duration</span>
                      <span className="text-amber-400 font-mono font-bold">{fleetAnalytics.total_idle_hours.toFixed(1)} hrs</span>
                    </div>
                  </div>
                ) : (
                  <RenderEmptyState
                    title="No Utilization Data"
                    description="Awaiting daily summary pipeline processing. Chart updates at midnight."
                  />
                )}
              </CardContent>
            </Card>

            {/* Fuel Consumption Trend Placeholder */}
            <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 text-left flex flex-col justify-between">
              <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white text-sm">Fuel Consumption Trend</CardTitle>
                  <CardDescription className="text-[11px]">Dynamic liters burned per vehicle comparison</CardDescription>
                </div>
                {(!fleetAnalytics || fleetAnalytics.total_fuel_consumed_l === 0) && (
                  <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase">Coming Soon</span>
                )}
              </CardHeader>
              <CardContent className="p-0 h-44 w-full flex flex-col justify-center">
                {fleetAnalytics && fleetAnalytics.total_fuel_consumed_l > 0 ? (
                  <div className="space-y-4 px-2">
                    <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                      <span className="text-slate-400">Total Fuel Burned</span>
                      <span className="text-white font-mono font-bold">{fleetAnalytics.total_fuel_consumed_l.toFixed(1)} L</span>
                    </div>
                    <div className="flex justify-between items-center text-xs border-b border-slate-800 pb-2">
                      <span className="text-slate-400">Active Fleet Vehicles</span>
                      <span className="text-white font-mono font-bold">{fleetAnalytics.active_vehicles} active</span>
                    </div>
                    <div className="flex justify-between items-center text-xs pb-1">
                      <span className="text-slate-400">Fleet Max Speed</span>
                      <span className="text-white font-mono font-bold">{fleetAnalytics.fleet_max_speed.toFixed(1)} km/h</span>
                    </div>
                  </div>
                ) : (
                  <RenderEmptyState
                    title="No Consumption Records"
                    description="Required fuel spec indicators have not registered calculation cycles yet."
                  />
                )}
              </CardContent>
            </Card>

          </div>

          {/* Event severity proportion chart */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl md:col-span-1 text-left">
              <CardHeader className="pb-2">
                <CardTitle className="text-white text-sm">Alert Severity</CardTitle>
                <CardDescription className="text-[11px]">Ingested alert proportions.</CardDescription>
              </CardHeader>
              <CardContent className="p-4 flex items-center justify-center h-48">
                {eventDistributionData.length > 0 ? (
                  <EventDistributionChart data={eventDistributionData} />
                ) : (
                  <div className="text-slate-400 text-xs py-12">No event logs recorded</div>
                )}
              </CardContent>
            </Card>

            <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl md:col-span-2 p-5 text-left flex flex-col justify-between">
              <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white text-sm">Driver Eco-Scores Distribution</CardTitle>
                  <CardDescription className="text-[11px]">Safety behavior and speed rankings</CardDescription>
                </div>
                <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase">Coming Soon</span>
              </CardHeader>
              <CardContent className="p-0 h-44 flex items-center justify-center">
                <RenderEmptyState
                  title="Driver Scores Locked"
                  description="Eco scores will populate when overspeed and harsh brake triggers complete configuration."
                />
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right Column (1/3 width) - Needs Attention center */}
        <div className="space-y-6">
          
          {/* Needs Attention alert box */}
          <Card className="border-rose-955 bg-rose-955/5 rounded-xl border relative overflow-hidden text-left" style={{ borderColor: "rgba(244, 63, 94, 0.2)" }}>
            <CardHeader className="pb-3 border-b border-rose-955 bg-rose-950/10 p-4" style={{ borderBottomColor: "rgba(244, 63, 94, 0.15)" }}>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                <CardTitle className="text-rose-400 text-sm font-bold uppercase tracking-wider">Needs Attention</CardTitle>
              </div>
              <CardDescription className="text-slate-400 text-[10px] uppercase font-bold pt-1.5">Active diagnostic warnings ({needsAttentionList.length})</CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-3 max-h-[16.5rem] overflow-y-auto">
              {needsAttentionList.map((item, idx) => (
                <div
                  key={`${item.id}-${idx}`}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg border text-left",
                    item.severity === "critical"
                      ? "bg-rose-500/5 border-rose-500/20"
                      : item.severity === "warning"
                      ? "bg-amber-500/5 border-amber-500/10"
                      : "bg-cyan-500/5 border-cyan-500/10"
                  )}
                >
                  <div className="mt-0.5">{item.icon}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] font-bold text-white block truncate">{item.name}</span>
                      <span className={cn(
                        "text-[8px] font-extrabold uppercase px-1 rounded border",
                        item.severity === "critical"
                          ? "bg-rose-500/10 text-rose-400 border-rose-500/20 animate-pulse"
                          : item.severity === "warning"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                      )}>
                        {item.severity}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 block font-medium mt-0.5">{item.reason}</span>
                  </div>
                </div>
              ))}
              {needsAttentionList.length === 0 && (
                <div className="text-center py-12 text-slate-400 text-xs">
                  All vehicle assets operating healthy. No alerts triggered.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Maintenance alert panel placeholder */}
          <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl text-left flex flex-col justify-between">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-white text-sm">Maintenance Schedule</CardTitle>
                <CardDescription className="text-[11px]">Upcoming fleet services tracker</CardDescription>
              </div>
              <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase">Coming Soon</span>
            </CardHeader>
            <CardContent className="p-4 pt-1 flex items-center justify-center py-10">
              <span className="text-[11px] text-slate-500 font-semibold">Service scheduling card placeholder</span>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 3. Bottom Grid: Fleet Vehicles List & Live Activity Timeline */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Fleet Vehicles Registry Table (2/3 width) */}
        <div className="xl:col-span-2">
          <FleetOperationsSummary vehicles={vehicles} snapshots={trackingSnapshots} />
        </div>

        {/* Live Activity timeline feed (1/3 width) */}
        <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl text-left">
          <CardHeader className="border-b border-[#1e294b]/60 bg-[#0f172a]/20 p-4">
            <CardTitle className="text-white text-sm">Live Activity Feed</CardTitle>
            <CardDescription className="text-[11px]">Real-time logs stream mapping VTS transaction codes</CardDescription>
          </CardHeader>
          <CardContent className="p-4 max-h-[35rem] overflow-y-auto">
            <div className="relative border-l border-slate-800 ml-2.5 pl-5 space-y-5">
              {recentEvents.map((ev, idx) => {
                const date = new Date(ev.created_at);
                const timeStr = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
                
                // Color mapping per severity
                const isCritical = ev.severity === "Critical";
                const isWarning = ev.severity === "Warning";
                
                return (
                  <div key={ev.id} className="relative text-left">
                    {/* timeline node dot */}
                    <span className={cn(
                      "absolute -left-[26px] top-1 h-3 w-3 rounded-full border-2",
                      isCritical 
                        ? "bg-rose-500 border-rose-950 animate-pulse" 
                        : isWarning 
                          ? "bg-amber-500 border-amber-950" 
                          : "bg-cyan-500 border-cyan-950"
                    )} style={{ left: "-26px" }} />
                    <div className="space-y-0.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className={cn(
                          "text-[10px] font-bold uppercase",
                          isCritical ? "text-rose-400" : isWarning ? "text-amber-400" : "text-cyan-400"
                        )}>
                          {ev.event_type}
                        </span>
                        <span className="text-[9px] text-slate-500 font-bold font-mono">{timeStr}</span>
                      </div>
                      <span className="text-[11px] text-slate-300 block leading-relaxed">{ev.description}</span>
                    </div>
                  </div>
                );
              })}
              {recentEvents.length === 0 && (
                <div className="text-center py-12 text-slate-500 text-xs">
                  No activity logs reported
                </div>
              )}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}

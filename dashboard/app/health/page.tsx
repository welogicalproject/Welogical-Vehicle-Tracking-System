"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  RefreshCw,
  Heart,
  AlertTriangle,
  WifiOff,
  Battery,
  Zap,
  Globe,
  Database
} from "lucide-react";
import { api } from "../../lib/api";
import { Vehicle, Location } from "../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/date";

export default function HealthPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [latestLocations, setLatestLocations] = useState<Record<number, Location | null>>({});
  const [allLocations, setAllLocations] = useState<Location[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    try {
      // 1. Fetch vehicles
      const vehiclesRes = await api.getVehicles(0, 100).catch(() => []);
      setVehicles(vehiclesRes);

      // 2. Fetch all locations to compute aggregate packets count per vehicle
      const locationsRes = await api.getAllLocations(0, 1000).catch(() => []);
      setAllLocations(locationsRes);

      // 3. Fetch latest location for all vehicles in parallel
      const locMap: Record<number, Location | null> = {};
      await Promise.all(
        vehiclesRes.map(async (v) => {
          try {
            const loc = await api.getLatestLocation(v.id);
            locMap[v.id] = loc;
          } catch {
            locMap[v.id] = null;
          }
        })
      );
      setLatestLocations(locMap);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve device health parameters.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Compute location/packet count lookup per vehicle
  const packetCountsMap = new Map<number, number>();
  allLocations.forEach((loc) => {
    packetCountsMap.set(loc.vehicle_id, (packetCountsMap.get(loc.vehicle_id) || 0) + 1);
  });

  // Health Status evaluator
  const getHealthStatus = (lastSeen: string | null): { status: "Healthy" | "Warning" | "Offline"; color: string; bg: string } => {
    if (!lastSeen) return { status: "Offline", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" };
    
    const lastSeenStr = lastSeen.endsWith("Z") ? lastSeen : `${lastSeen}Z`;
    const lastSeenDate = new Date(lastSeenStr);
    const now = new Date();
    const diffMs = now.getTime() - lastSeenDate.getTime();
    const diffMin = diffMs / 60000;

    if (diffMin < 5) {
      return { status: "Healthy", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
    } else if (diffMin <= 30) {
      return { status: "Warning", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" };
    } else {
      return { status: "Offline", color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" };
    }
  };

  // Compile summary counts
  let healthyCount = 0;
  let warningCount = 0;
  let offlineCount = 0;

  vehicles.forEach((v) => {
    const health = getHealthStatus(v.last_seen);
    if (health.status === "Healthy") healthyCount++;
    else if (health.status === "Warning") warningCount++;
    else offlineCount++;
  });

  return (
    <div className="p-8 space-y-8 select-none">
      {/* Top Action bar */}
      <div className="flex items-center justify-between bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-semibold text-slate-400">
            Device hardware diagnostics logging active.
          </span>
        </div>
        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-200 font-semibold text-xs px-3.5 py-2 rounded-lg transition-all"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
          Refresh Registry
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-semibold">
          {error}
        </div>
      )}

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-5 flex items-center gap-4 text-left">
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Heart className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">Healthy Devices</div>
            <div className="text-xl font-extrabold text-white mt-1">{loading ? "..." : healthyCount} Active</div>
          </div>
        </div>

        <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-5 flex items-center gap-4 text-left">
          <div className="h-10 w-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">Delayed Warnings</div>
            <div className="text-xl font-extrabold text-white mt-1">{loading ? "..." : warningCount} Idle</div>
          </div>
        </div>

        <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-5 flex items-center gap-4 text-left">
          <div className="h-10 w-10 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <WifiOff className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">Offline Telemetry</div>
            <div className="text-xl font-extrabold text-white mt-1">{loading ? "..." : offlineCount} Inactive</div>
          </div>
        </div>
      </div>

      {/* Diagnostics Table */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Vehicle Node</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Device UID</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Diagnostic State</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Internal Battery</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Main Voltage</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs text-center">Packets Ingested</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Last Ping Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {vehicles.map((v) => {
                const health = getHealthStatus(v.last_seen);
                const loc = latestLocations[v.id];
                
                // Read diagnostic values from location extra_data
                const voltVal = loc?.extra_data?.pwr?.volt;
                const batteryVolt = typeof voltVal === "number" 
                  ? `${(voltVal / 1000).toFixed(2)} V` 
                  : (loc?.extra_data?.io?.analog?.[0] ? `${(loc.extra_data.io.analog[0] / 1000).toFixed(2)} V` : "—");
                
                const mvoltVal = loc?.extra_data?.pwr?.mvolt;
                const mainVolt = typeof mvoltVal === "number" ? `${mvoltVal.toFixed(1)} V` : "—";
                
                const packetsCount = packetCountsMap.get(v.id) || 0;

                return (
                  <TableRow key={v.id} className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors">
                    <TableCell className="font-bold text-white text-xs py-4">{v.vehicle_name}</TableCell>
                    <TableCell className="font-mono text-xs text-cyan-400 py-4">{v.device_uid}</TableCell>
                    <TableCell className="py-4">
                      <span className={cn(
                        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border",
                        health.bg,
                        health.color
                      )}>
                        <span className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          health.status === "Healthy" ? "bg-emerald-400" : health.status === "Warning" ? "bg-amber-400" : "bg-rose-400"
                        )} />
                        {health.status}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs text-slate-300 font-semibold py-4">
                      <div className="flex items-center gap-1.5">
                        <Battery className="h-3.5 w-3.5 text-slate-500" />
                        <span>{batteryVolt}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-slate-300 font-semibold py-4">
                      <div className="flex items-center gap-1.5">
                        <Zap className="h-3.5 w-3.5 text-slate-500" />
                        <span>{mainVolt}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-center text-white font-mono font-bold py-4">{packetsCount} pkts</TableCell>
                    <TableCell className="text-xs text-slate-400 py-4">
                      {formatDate(v.last_seen)}
                    </TableCell>
                  </TableRow>
                );
              })}
              {vehicles.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-12 text-slate-400 text-xs">
                    {loading ? "Loading diagnostics registers..." : "No hardware assets connected"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

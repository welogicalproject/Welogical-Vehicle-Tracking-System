"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  RefreshCw,
  Search
} from "lucide-react";
import { api } from "../../lib/api";
import { DeviceConfig, Vehicle } from "../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Input } from "../../components/ui/input";
import { cn } from "../../lib/utils";

export default function ConfigurationsPage() {
  const [configs, setConfigs] = useState<DeviceConfig[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search filter
  const [search, setSearch] = useState("");

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    try {
      const [configsRes, vehiclesRes] = await Promise.all([
        api.getConfigurations(0, 100).catch(() => []),
        api.getVehicles(0, 100).catch(() => [])
      ]);
      setConfigs(configsRes);
      setVehicles(vehiclesRes);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to retrieve device configuration settings.");
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

  // Create lookup dictionary for vehicle names
  const vehicleMap = new Map<number, { name: string, uid: string }>();
  vehicles.forEach((v) => {
    vehicleMap.set(v.id, { name: v.vehicle_name, uid: v.device_uid });
  });

  // Client-side filtering
  const filteredConfigs = configs.filter((c) => {
    const vMeta = vehicleMap.get(c.vehicle_id);
    const vName = vMeta ? vMeta.name : "";
    const vUid = vMeta ? vMeta.uid : "";
    
    return (
      vName.toLowerCase().includes(search.toLowerCase()) ||
      vUid.toLowerCase().includes(search.toLowerCase()) ||
      (c.apn && c.apn.toLowerCase().includes(search.toLowerCase())) ||
      (c.firmware_version && c.firmware_version.toLowerCase().includes(search.toLowerCase()))
    );
  });

  return (
    <div className="p-8 space-y-8 select-none">
      {/* Top Filter and Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
        <div className="flex-1 flex items-center gap-3">
          {/* Search box */}
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search by name, UID, APN..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-[#0b0f19] border-[#1e294b] text-xs h-9"
            />
          </div>

          <div className="hidden md:flex bg-[#0b0f19]/30 px-3 py-1.5 rounded-lg border border-[#1e294b]/40 text-xs font-semibold text-slate-400">
            <span>Total Profiles:</span>
            <span className="font-mono font-bold text-white ml-1.5">{configs.length}</span>
          </div>
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

      {/* Configurations Table Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Vehicle Node</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Device UID</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Server Endpoint</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Network APN</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs text-center">Interval</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs text-center">Speed Limit</TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">Firmware</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredConfigs.map((c) => {
                const vMeta = vehicleMap.get(c.vehicle_id);
                return (
                  <TableRow key={c.id} className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors">
                    <TableCell className="font-bold text-white text-xs py-4">
                      {vMeta ? vMeta.name : `Vehicle #${c.vehicle_id}`}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-cyan-400 py-4">
                      {vMeta ? vMeta.uid : "—"}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-slate-300 py-4">
                      {c.server_ip ? `${c.server_ip}:${c.server_port || ""}` : "—"}
                    </TableCell>
                    <TableCell className="text-xs text-slate-300 py-4">
                      {c.apn || "—"}
                    </TableCell>
                    <TableCell className="text-xs font-bold text-white font-mono text-center py-4">
                      {c.reporting_interval ? `${c.reporting_interval}s` : "—"}
                    </TableCell>
                    <TableCell className="text-xs font-bold text-white font-mono text-center py-4">
                      {c.speed_limit ? `${c.speed_limit} km/h` : "—"}
                    </TableCell>
                    <TableCell className="text-xs text-slate-400 py-4">
                      {c.firmware_version || "—"}
                    </TableCell>
                  </TableRow>
                );
              })}
              {filteredConfigs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-12 text-slate-400 text-xs">
                    {loading ? "Loading profiles registry..." : "No configuration profiles found"}
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

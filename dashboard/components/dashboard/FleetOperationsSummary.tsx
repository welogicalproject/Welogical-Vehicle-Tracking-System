import React from "react";
import Link from "next/link";
import { ArrowUpRight, ShieldAlert, CheckCircle, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { cn } from "../../lib/utils";
import { getStatus, getFuelLevel, getBatteryVolt, getMainVolt } from "../../utils/tracking";
import { Vehicle, VehicleTrackingSnapshot } from "../../types";

interface FleetOperationsSummaryProps {
  vehicles: Vehicle[];
  snapshots: VehicleTrackingSnapshot[];
}

export function FleetOperationsSummary({ vehicles, snapshots }: FleetOperationsSummaryProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="text-left">
          <CardTitle className="text-white text-base">Fleet Operations Summary</CardTitle>
          <CardDescription>Live health and diagnostics status of active assets.</CardDescription>
        </div>
        <Link
          href="/vehicles"
          className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
        >
          View Inventory <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                Vehicle Name
              </TableHead>
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                State
              </TableHead>
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                Fuel %
              </TableHead>
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                Battery
              </TableHead>
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                Health
              </TableHead>
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">
                Last Update
              </TableHead>
              <TableHead className="text-slate-400 text-[10px] font-bold uppercase tracking-wider text-right">
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {vehicles.slice(0, 10).map((v) => {
              const snapshot = snapshots.find((s) => s.vehicle.id === v.id);
              const status = getStatus(v.last_seen);
              
              // 1. Resolve State
              let opState = "Offline";
              if (status === "online") {
                const speed = snapshot?.latest_location?.speed ?? 0;
                const ign = snapshot?.latest_location?.extra_data?.io?.ign;
                if (ign === 1) {
                  opState = speed > 0 ? "Driving" : "Idle";
                } else {
                  opState = "Parked";
                }
              } else if (status === "idle") {
                opState = "Parked";
              }

              // 2. Resolve Fuel
              let fuelPctStr = "N/A";
              const extra = snapshot?.latest_location?.extra_data;
              const fuelPct = extra?.fuel?.percentage ?? (typeof extra?.io?.analog?.[2] === "number" ? extra.io.analog[2] / 100 : null);
              if (typeof fuelPct === "number") {
                fuelPctStr = `${fuelPct.toFixed(0)}%`;
              }

              // 3. Resolve Battery
              const mainVolt = extra?.power?.main_voltage ?? extra?.pwr?.mvolt;
              const batteryStr = typeof mainVolt === "number" ? `${mainVolt.toFixed(1)}V` : "N/A";

              // 4. Health determination
              let isHealthy = true;
              let healthReason = "Operational";
              
              if (extra) {
                if (typeof fuelPct === "number" && fuelPct < 10) {
                  isHealthy = false;
                  healthReason = "Low Fuel";
                } else if (typeof mainVolt === "number" && mainVolt < 11.5) {
                  isHealthy = false;
                  healthReason = "Low Battery";
                } else if (extra.pwr?.main === 0) {
                  isHealthy = false;
                  healthReason = "Power Lost";
                } else if (typeof extra.engine?.coolant_temperature === "number" && extra.engine.coolant_temperature > 98) {
                  isHealthy = false;
                  healthReason = "Overheating";
                }
              }

              // 5. Last update time format
              let lastUpdateStr = "N/A";
              if (v.last_seen) {
                const date = new Date(v.last_seen);
                lastUpdateStr = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
              }

              return (
                <TableRow
                  key={v.id}
                  className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
                >
                  <TableCell className="text-left py-3">
                    <span className="font-semibold text-slate-100 block">{v.vehicle_name}</span>
                    <span className="font-mono text-[9px] text-slate-500 block mt-0.5">{v.device_uid}</span>
                  </TableCell>
                  
                  <TableCell className="text-left py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wide border",
                        opState === "Driving"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : opState === "Idle"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : opState === "Parked"
                          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                      )}
                    >
                      {opState}
                    </span>
                  </TableCell>

                  <TableCell className={cn(
                    "text-left font-medium text-xs py-3",
                    typeof fuelPct === "number" && fuelPct < 15 ? "text-amber-400" : "text-slate-300"
                  )}>
                    {fuelPctStr}
                  </TableCell>

                  <TableCell className={cn(
                    "text-left font-medium text-xs py-3",
                    typeof mainVolt === "number" && mainVolt < 11.8 ? "text-rose-400 animate-pulse" : "text-slate-300"
                  )}>
                    {batteryStr}
                  </TableCell>

                  <TableCell className="text-left py-3">
                    <span className={cn(
                      "inline-flex items-center gap-1 text-[10px] font-semibold",
                      isHealthy ? "text-emerald-400" : "text-rose-400"
                    )}>
                      {isHealthy ? (
                        <CheckCircle className="h-3 w-3" />
                      ) : (
                        <AlertTriangle className="h-3 w-3 animate-bounce" />
                      )}
                      {healthReason}
                    </span>
                  </TableCell>

                  <TableCell className="text-left text-xs font-mono text-slate-400 py-3">
                    {lastUpdateStr}
                  </TableCell>

                  <TableCell className="text-right py-3">
                    <Link
                      href={`/vehicles/${v.id}`}
                      className="bg-[#131a2d] hover:bg-[#1e294b] text-[10px] text-cyan-400 font-extrabold uppercase border border-[#1e294b] px-2.5 py-1 rounded-lg transition-all"
                    >
                      Analyze
                    </Link>
                  </TableCell>
                </TableRow>
              );
            })}
            {vehicles.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-6 text-slate-400 text-xs">
                  No registered vehicles
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

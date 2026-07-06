"use client";

import Link from "next/link";
import { Battery, Car, Clock, Database, Gauge, Globe, MapPin, Navigation, Route, Satellite, Send, Sliders, SlidersHorizontal, Users, X, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { MetricRow } from "../shared/MetricRow";
import { TrackingDetailTab } from "../../hooks/useVehicleSelection";
import { VehicleTrackingSnapshot } from "../../types";
import { cn } from "../../lib/utils";
import { getBatteryVolt, getGPSFixText, getHeadingText, getLastUpdateText, getMainVolt, getNetworkStatus, getOdometerKm, getPacketVal } from "../../utils/tracking";

interface VehicleDetailsPanelProps {
  selectedVehicleId: number | "all";
  selectedSnapshot?: VehicleTrackingSnapshot;
  detailTab: TrackingDetailTab;
  onDetailTabChange: (tab: TrackingDetailTab) => void;
  onSelectVehicle: (id: number | "all") => void;
}

function IgnitionBadge({ snapshot }: { snapshot?: VehicleTrackingSnapshot }) {
  const ign = getPacketVal(snapshot, ["io", "ign"]);
  if (ign === 1) return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase">ON</span>;
  if (ign === 0) return <span className="bg-slate-500/10 text-slate-400 border border-slate-500/20 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase">OFF</span>;
  return <span className="text-slate-400 text-xs font-semibold">N/A</span>;
}

export function VehicleDetailsPanel({
  selectedVehicleId,
  selectedSnapshot,
  detailTab,
  onDetailTabChange,
  onSelectVehicle,
}: VehicleDetailsPanelProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
      <CardHeader className="border-b border-[#1e294b]/60 bg-[#0f172a]/20 p-4 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-white text-base">Vehicle Details</CardTitle>
        </div>
        {selectedVehicleId !== "all" && (
          <button
            onClick={() => onSelectVehicle("all")}
            className="p-1 hover:bg-[#1e294b] rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </CardHeader>
      <CardContent className="p-4 space-y-4">
        {!selectedSnapshot ? (
          <div className="text-center py-12 text-slate-400 text-xs bg-[#0b0f19]/30 border border-[#1e294b]/30 rounded-lg">
            Select a vehicle on the map or from the filters to inspect live telemetry.
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 p-3 bg-[#0b0f19]/50 border border-[#1e294b]/40 rounded-lg">
              <div className="h-10 w-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <Car className="h-6 w-6" />
              </div>
              <div className="min-w-0 text-left">
                <span className="text-xs font-bold text-white block truncate">{selectedSnapshot.vehicle.vehicle_name}</span>
                <span className="text-[10px] text-slate-500 font-mono block truncate">UID: {selectedSnapshot.vehicle.device_uid}</span>
              </div>
              <div className="ml-auto">
                {selectedSnapshot.movement_status === "Moving" ? (
                  <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase animate-pulse">Moving</span>
                ) : (
                  <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase">Stopped</span>
                )}
              </div>
            </div>

            <div className="flex border-b border-[#1e294b]/30">
              {(["live", "status", "history", "events"] as TrackingDetailTab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => onDetailTabChange(tab)}
                  className={cn(
                    "flex-1 py-1.5 text-[10px] font-bold tracking-wider uppercase border-b-2 text-center transition-all",
                    detailTab === tab
                      ? "border-cyan-400 text-cyan-400"
                      : "border-transparent text-slate-500 hover:text-slate-300"
                  )}
                >
                  {tab === "live" ? "Live Info" : tab}
                </button>
              ))}
            </div>

            <div className="space-y-2 pt-2 text-left">
              {detailTab === "live" && (
                <div className="space-y-2">
                  <MetricRow label="Location" val={selectedSnapshot.latest_location ? `${selectedSnapshot.latest_location.latitude.toFixed(4)}° N, ${selectedSnapshot.latest_location.longitude.toFixed(4)}° E` : "N/A"} icon={<MapPin className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Speed" val={selectedSnapshot.latest_location ? `${selectedSnapshot.latest_location.speed.toFixed(1)} km/h` : "N/A"} icon={<Gauge className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Heading" val={getHeadingText(selectedSnapshot)} icon={<Navigation className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Last Update" val={getLastUpdateText(selectedSnapshot)} icon={<Clock className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Ignition" val={<IgnitionBadge snapshot={selectedSnapshot} />} icon={<Zap className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="GPS Status" val={getGPSFixText(selectedSnapshot)} icon={<Satellite className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Battery Voltage" val={getBatteryVolt(selectedSnapshot)} icon={<Battery className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Main Voltage" val={getMainVolt(selectedSnapshot)} icon={<Zap className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Network" val={getNetworkStatus(selectedSnapshot)} icon={<Globe className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Odometer" val={getOdometerKm(selectedSnapshot)} icon={<Route className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Fuel Level" val="N/A" icon={<SlidersHorizontal className="h-3.5 w-3.5 text-cyan-400" />} />
                  <MetricRow label="Driver" val="N/A" icon={<Users className="h-3.5 w-3.5 text-cyan-400" />} />
                </div>
              )}

              {detailTab === "status" && (
                <div className="space-y-3 p-1">
                  <div>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Health Status</span>
                    <span className={cn(
                      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border mt-1.5",
                      selectedSnapshot.health_status === "Healthy"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : selectedSnapshot.health_status === "Warning"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    )}>
                      <span className={cn("h-1.5 w-1.5 rounded-full", selectedSnapshot.health_status === "Healthy" ? "bg-emerald-400" : selectedSnapshot.health_status === "Warning" ? "bg-amber-400" : "bg-rose-400")} />
                      {selectedSnapshot.health_status}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Movement Status</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border mt-1 border-[#1e294b]/60 text-slate-200">{selectedSnapshot.movement_status}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Packets Ingested</span>
                    <span className="text-sm font-bold text-white font-mono mt-1 block">{selectedSnapshot.packet_count} packets</span>
                  </div>
                  <div className="border-t border-[#1e294b]/30 pt-3 space-y-2">
                    <MetricRow label="Command" val={selectedSnapshot.latest_command ? `${selectedSnapshot.latest_command.command_name} (${selectedSnapshot.latest_command.status})` : "No pending command"} icon={<Send className="h-3.5 w-3.5 text-cyan-400" />} />
                    <MetricRow label="Reporting" val={selectedSnapshot.device_config?.reporting_interval ? `${selectedSnapshot.device_config.reporting_interval}s` : "N/A"} icon={<Sliders className="h-3.5 w-3.5 text-cyan-400" />} />
                    <MetricRow label="Speed Limit" val={selectedSnapshot.device_config?.speed_limit ? `${selectedSnapshot.device_config.speed_limit} km/h` : "N/A"} icon={<Gauge className="h-3.5 w-3.5 text-cyan-400" />} />
                    <MetricRow label="Firmware" val={selectedSnapshot.device_config?.firmware_version ?? "N/A"} icon={<Database className="h-3.5 w-3.5 text-cyan-400" />} />
                  </div>
                </div>
              )}

              {detailTab === "history" && (
                <div className="space-y-3 p-1 max-h-[250px] overflow-y-auto">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Last 5 Route History Nodes</span>
                  <div className="space-y-2 mt-2">
                    {selectedSnapshot.route_history.slice(-5).reverse().map((point, index) => (
                      <div key={index} className="border-b border-[#1e294b]/30 pb-2 flex justify-between items-center text-xs">
                        <div>
                          <span className="font-mono text-cyan-300 block">{point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}</span>
                          <span className="text-[10px] text-slate-500">{new Date(point.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <span className="font-bold text-slate-200 font-mono">{point.speed.toFixed(1)} km/h</span>
                      </div>
                    ))}
                    {selectedSnapshot.route_history.length === 0 && (
                      <div className="text-slate-400 text-xs py-4 text-center">No route history logs found</div>
                    )}
                  </div>
                </div>
              )}

              {detailTab === "events" && (
                <div className="space-y-2 max-h-[250px] overflow-y-auto">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Latest Vehicle Alert Logs</span>
                  <div className="space-y-2 mt-2">
                    {selectedSnapshot.latest_event ? (
                      <div className="border border-[#1e294b]/60 rounded-lg p-2.5 bg-[#0b0f19]/30 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-white">{selectedSnapshot.latest_event.event_type}</span>
                          <span className="text-[9px] text-slate-500 font-mono">{new Date(selectedSnapshot.latest_event.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-slate-400 mt-1 text-[11px] leading-relaxed">{selectedSnapshot.latest_event.description}</p>
                      </div>
                    ) : (
                      <div className="text-slate-400 text-xs py-4 text-center">No alerts logged for this asset</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <Link href={`/vehicles/${selectedSnapshot.vehicle.id}`} className="w-full bg-[#1b253b] hover:bg-[#253350] border border-[#1e294b] text-slate-200 font-bold text-xs py-2 rounded-lg flex items-center justify-center transition-all mt-4">
              View Node Profile Analyzer
            </Link>

            <Link href={`/vehicles/${selectedSnapshot.vehicle.id}?tab=route&playback=true`} className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs py-2 rounded-lg flex items-center justify-center transition-all mt-2">
              Replay Route History
            </Link>
          </>
        )}
      </CardContent>
    </Card>
  );
}

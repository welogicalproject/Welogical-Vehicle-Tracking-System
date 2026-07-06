"use client";

import { useState } from "react";
import { ChevronDown, Clock, RefreshCw } from "lucide-react";
import { RANGE_OPTIONS, RangeKey } from "../../constants/tracking";
import { VehicleTrackingSnapshot } from "../../types";
import { cn } from "../../lib/utils";
import { getVehicleColor } from "../../utils/tracking";

interface TrackingToolbarProps {
  snapshots: VehicleTrackingSnapshot[];
  vehicleOptions: VehicleTrackingSnapshot[];
  selectedSnapshot?: VehicleTrackingSnapshot;
  selectedVehicleId: number | "all";
  range: RangeKey;
  customStart: string;
  customEnd: string;
  refreshing: boolean;
  onSelectVehicle: (id: number | "all") => void;
  onRangeChange: (range: RangeKey) => void;
  onCustomStartChange: (value: string) => void;
  onCustomEndChange: (value: string) => void;
  onRefresh: () => void;
}

export function TrackingToolbar({
  snapshots,
  vehicleOptions,
  selectedSnapshot,
  selectedVehicleId,
  range,
  customStart,
  customEnd,
  refreshing,
  onSelectVehicle,
  onRangeChange,
  onCustomStartChange,
  onCustomEndChange,
  onRefresh,
}: TrackingToolbarProps) {
  const [vehicleDropdownOpen, setVehicleDropdownOpen] = useState(false);
  const [rangeDropdownOpen, setRangeDropdownOpen] = useState(false);

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="relative">
          <button
            onClick={() => { setVehicleDropdownOpen(!vehicleDropdownOpen); setRangeDropdownOpen(false); }}
            className="bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] rounded-lg px-4 py-2 text-xs font-semibold text-white flex items-center justify-between gap-3 w-56 transition-all"
          >
            {selectedVehicleId === "all" ? (
              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
                All Vehicles
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: getVehicleColor(snapshots.findIndex((snapshot) => snapshot.vehicle.id === selectedVehicleId)) }} />
                {selectedSnapshot?.vehicle.vehicle_name ?? "Selected Vehicle"}
              </span>
            )}
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {vehicleDropdownOpen && (
            <div className="absolute top-11 left-0 w-64 bg-[#0f172a] border border-[#1e294b] rounded-xl shadow-2xl z-[1000] p-1.5 space-y-0.5">
              <button
                onClick={() => { onSelectVehicle("all"); setVehicleDropdownOpen(false); }}
                className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold hover:bg-[#1d294d] text-slate-300 hover:text-white flex items-center gap-2"
              >
                <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
                All Vehicles
              </button>
              {vehicleOptions.map((snapshot, index) => (
                <button
                  key={snapshot.vehicle.id}
                  onClick={() => { onSelectVehicle(snapshot.vehicle.id); setVehicleDropdownOpen(false); }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-semibold hover:bg-[#1d294d] text-slate-300 hover:text-white flex items-center gap-2 justify-between"
                >
                  <span className="flex items-center gap-2 min-w-0">
                    <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ backgroundColor: getVehicleColor(index) }} />
                    <span className="truncate">{snapshot.vehicle.vehicle_name}</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono shrink-0">{snapshot.vehicle.device_uid}</span>
                </button>
              ))}
              {vehicleOptions.length === 0 && (
                <div className="px-3 py-2 text-xs font-semibold text-slate-500">
                  No vehicles with live coordinates
                </div>
              )}
            </div>
          )}
        </div>

        <div className="relative">
          <button
            onClick={() => { setRangeDropdownOpen(!rangeDropdownOpen); setVehicleDropdownOpen(false); }}
            className="bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] rounded-lg px-4 py-2 text-xs font-semibold text-white flex items-center justify-between gap-3 w-48 transition-all"
          >
            <span className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-cyan-400" />
              {RANGE_OPTIONS.find((item) => item.key === range)?.label}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {rangeDropdownOpen && (
            <div className="absolute top-11 left-0 w-48 bg-[#0f172a] border border-[#1e294b] rounded-xl shadow-2xl z-[1000] p-1.5 space-y-0.5">
              {RANGE_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  onClick={() => { onRangeChange(option.key); setRangeDropdownOpen(false); }}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-lg text-xs font-semibold hover:bg-[#1d294d] text-slate-300 hover:text-white",
                    range === option.key && "bg-[#132238] text-cyan-400"
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="flex items-center justify-center p-2 rounded-lg bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-300 disabled:opacity-50 transition-all"
          title="Refresh Feed"
        >
          <RefreshCw className={cn("h-4 w-4", refreshing ? "animate-spin" : "")} />
        </button>
      </div>

      <div className="flex items-center gap-4">
        {range === "custom" && (
          <div className="flex items-center gap-2">
            <input
              type="datetime-local"
              value={customStart}
              onChange={(event) => onCustomStartChange(event.target.value)}
              className="h-8 rounded-lg border border-[#1e294b] bg-[#0b0f19] px-2 text-[10px] text-white focus:outline-none"
            />
            <input
              type="datetime-local"
              value={customEnd}
              onChange={(event) => onCustomEndChange(event.target.value)}
              className="h-8 rounded-lg border border-[#1e294b] bg-[#0b0f19] px-2 text-[10px] text-white focus:outline-none"
            />
          </div>
        )}

        <div className="flex items-center gap-2 bg-[#10b981]/10 border border-[#10b981]/20 px-3 py-1.5 rounded-lg text-xs font-extrabold text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Live Telemetry Feed
        </div>
      </div>
    </div>
  );
}

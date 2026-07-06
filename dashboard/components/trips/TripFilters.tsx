import React from "react";
import { Vehicle } from "../../types";
import { SlidersHorizontal, RefreshCw } from "lucide-react";
import { Button } from "../ui/button";
import { DatePickerInput } from "../ui/date-picker";

interface TripFiltersProps {
  vehicleId: number | "all";
  setVehicleId: (id: number | "all") => void;
  status: string;
  setStatus: (status: string) => void;
  startTime: string;
  setStartTime: (time: string) => void;
  endTime: string;
  setEndTime: (time: string) => void;
  vehicles: Vehicle[];
  onRefresh: () => void;
  refreshing?: boolean;
  hideVehicleSelect?: boolean; // Used when embedded in single Vehicle details view
}

export function TripFilters({
  vehicleId,
  setVehicleId,
  status,
  setStatus,
  startTime,
  setStartTime,
  endTime,
  setEndTime,
  vehicles,
  onRefresh,
  refreshing = false,
  hideVehicleSelect = false,
}: TripFiltersProps) {
  return (
    <div className="glass-panel rounded-xl p-6 border border-[#1e294b]/60 flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-white">
          <SlidersHorizontal className="h-4.5 w-4.5 text-cyan-400" />
          <span className="text-sm font-bold tracking-wider uppercase">Filter Trips</span>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          className="flex items-center gap-2 text-slate-400 hover:text-white"
          disabled={refreshing}
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Vehicle Filter */}
        {!hideVehicleSelect && (
          <div className="flex flex-col gap-1 text-left">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              Vehicle Target
            </label>
            <select
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value === "all" ? "all" : Number(e.target.value))}
              className="bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 h-9"
            >
              <option value="all">All Vehicles</option>
              {vehicles.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.vehicle_name} ({v.device_uid})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Status Filter */}
        <div className="flex flex-col gap-1 text-left">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Trip Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400 h-9"
          >
            <option value="all">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
        </div>

        {/* Start Date */}
        <div className="flex flex-col gap-1 text-left">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            From Date
          </label>
          <DatePickerInput
            id="trip-filter-start-date"
            value={startTime}
            onChange={setStartTime}
            mode="start"
            placeholder="Pick start date"
          />
        </div>

        {/* End Date */}
        <div className="flex flex-col gap-1 text-left">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            To Date
          </label>
          <DatePickerInput
            id="trip-filter-end-date"
            value={endTime}
            onChange={setEndTime}
            mode="end"
            placeholder="Pick end date"
          />
        </div>
      </div>
    </div>
  );
}

import React from "react";
import { Trip } from "../../types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { formatDate } from "../../lib/date";
import { Clock, Eye, AlertTriangle } from "lucide-react";
import { cn } from "../../lib/utils";

interface TripTableProps {
  trips: Trip[];
  loading: boolean;
  onSelectTrip: (trip: Trip) => void;
  hideVehicleColumn?: boolean;
}

export function TripTable({ trips, loading, onSelectTrip, hideVehicleColumn = false }: TripTableProps) {
  // Helper to format duration seconds to human readable
  const formatDuration = (seconds: number): string => {
    if (seconds <= 0) return "0s";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    const parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (s > 0 || parts.length === 0) parts.push(`${s}s`);
    return parts.join(" ");
  };

  const getStatusBadge = (status: Trip["status"], isActive: boolean) => {
    if (isActive || status === "ACTIVE") {
      return (
        <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full w-fit">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          ACTIVE
        </span>
      );
    }
    if (status === "CANCELLED") {
      return (
        <span className="flex items-center gap-1 text-xs font-bold text-slate-400 bg-slate-500/10 border border-slate-500/20 px-2 py-0.5 rounded-full w-fit">
          <AlertTriangle className="h-3 w-3" />
          CANCELLED
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 text-xs font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full w-fit">
        COMPLETED
      </span>
    );
  };

  if (loading) {
    return (
      <div className="glass-panel border border-[#1e294b]/60 rounded-xl p-12 text-center text-slate-400 text-sm">
        <Clock className="h-6 w-6 animate-spin mx-auto mb-2 text-cyan-400" />
        Loading trip history...
      </div>
    );
  }

  if (trips.length === 0) {
    return (
      <div className="glass-panel border border-[#1e294b]/60 rounded-xl p-12 text-center text-slate-400 text-sm">
        No trips recorded for the selected filter criteria.
      </div>
    );
  }

  return (
    <div className="glass-panel border border-[#1e294b]/60 rounded-xl overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            {!hideVehicleColumn && <TableHead>Vehicle</TableHead>}
            <TableHead>Trip ID</TableHead>
            <TableHead>Start Time</TableHead>
            <TableHead>End Time</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Distance</TableHead>
            <TableHead>Avg Speed</TableHead>
            <TableHead>Max Speed</TableHead>
            <TableHead>Idle Time</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trips.map((trip) => (
            <TableRow
              key={trip.id}
              className="hover:bg-slate-900/40 cursor-pointer"
              onClick={() => onSelectTrip(trip)}
            >
              {!hideVehicleColumn && (
                <TableCell className="font-bold text-white">
                  <div className="flex flex-col text-left">
                    <span>{trip.vehicle_name || `Vehicle ${trip.vehicle_id}`}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{trip.device_uid}</span>
                  </div>
                </TableCell>
              )}
              <TableCell className="font-mono text-slate-400">#{trip.id}</TableCell>
              <TableCell className="text-xs">{formatDate(trip.start_time)}</TableCell>
              <TableCell className="text-xs">
                {trip.is_active ? "-" : formatDate(trip.end_time)}
              </TableCell>
              <TableCell className="font-semibold text-slate-200">
                {formatDuration(trip.duration)}
              </TableCell>
              <TableCell className="font-semibold text-cyan-400">
                {trip.distance.toFixed(2)} km
              </TableCell>
              <TableCell>{trip.average_speed.toFixed(1)} km/h</TableCell>
              <TableCell>{trip.maximum_speed.toFixed(1)} km/h</TableCell>
              <TableCell className="text-slate-400">
                {formatDuration(trip.idle_time)}
              </TableCell>
              <TableCell>{getStatusBadge(trip.status, trip.is_active)}</TableCell>
              <TableCell className="text-right">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectTrip(trip);
                  }}
                  className="p-2 hover:bg-[#1e294b] rounded-lg text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  <Eye className="h-4 w-4" />
                </button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

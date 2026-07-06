import React from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { formatDate } from "../../lib/date";
import { Vehicle, Location, RawPacket } from "../../types";

interface VehiclesTableProps {
  vehicles: Vehicle[];
  loading: boolean;
}

export function VehiclesTable({ vehicles, loading }: VehiclesTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            ID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Device UID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Vehicle Name
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Type
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Created At
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Last Seen
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((v) => (
          <TableRow
            key={v.id}
            className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
          >
            <TableCell className="font-mono text-[10px] text-slate-500 py-3 text-left">
              {v.id}
            </TableCell>
            <TableCell className="font-mono text-xs text-cyan-400 font-bold py-3 text-left">
              {v.device_uid}
            </TableCell>
            <TableCell className="font-bold text-white text-xs py-3 text-left">
              {v.vehicle_name}
            </TableCell>
            <TableCell className="text-xs text-slate-300 py-3 text-left">
              {v.vehicle_type}
            </TableCell>
            <TableCell className="text-[11px] text-slate-400 py-3 text-left">
              {formatDate(v.created_at)}
            </TableCell>
            <TableCell className="text-[11px] text-slate-400 py-3 text-left">
              {formatDate(v.last_seen)}
            </TableCell>
          </TableRow>
        ))}
        {vehicles.length === 0 && (
          <TableRow>
            <TableCell colSpan={6} className="text-center py-12 text-slate-400 text-xs">
              {loading ? "Querying PostgreSQL rows..." : "No asset records found"}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

interface LocationsTableProps {
  locations: Location[];
  loading: boolean;
}

export function LocationsTable({ locations, loading }: LocationsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            ID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Vehicle ID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Latitude
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Longitude
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Speed
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Altitude
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Timestamp
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {locations.map((l) => (
          <TableRow
            key={l.id}
            className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
          >
            <TableCell className="font-mono text-[10px] text-slate-500 py-3 text-left">
              {l.id}
            </TableCell>
            <TableCell className="font-mono text-xs text-slate-300 py-3 text-left">
              {l.vehicle_id}
            </TableCell>
            <TableCell className="font-mono text-xs text-cyan-400 py-3 text-left">
              {l.latitude.toFixed(6)}
            </TableCell>
            <TableCell className="font-mono text-xs text-cyan-400 py-3 text-left">
              {l.longitude.toFixed(6)}
            </TableCell>
            <TableCell className="font-bold text-white text-xs py-3 text-left">
              {l.speed.toFixed(1)} km/h
            </TableCell>
            <TableCell className="text-xs text-slate-300 py-3 text-left">
              {l.altitude.toFixed(1)} m
            </TableCell>
            <TableCell className="text-[11px] text-slate-400 py-3 text-left">
              {formatDate(l.timestamp)}
            </TableCell>
          </TableRow>
        ))}
        {locations.length === 0 && (
          <TableRow>
            <TableCell colSpan={7} className="text-center py-12 text-slate-400 text-xs">
              {loading ? "Querying PostgreSQL rows..." : "No location records found"}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

interface RawPacketsTableProps {
  packets: RawPacket[];
  loading: boolean;
}

export function RawPacketsTable({ packets, loading }: RawPacketsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            ID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Device UID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Message ID
          </TableHead>
          <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
            Created At
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {packets.map((p) => (
          <TableRow
            key={p.id}
            className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
          >
            <TableCell className="font-mono text-[10px] text-slate-500 py-3 text-left">
              {p.id}
            </TableCell>
            <TableCell className="font-mono text-xs text-cyan-400 font-bold py-3 text-left">
              {p.device_uid || "N/A"}
            </TableCell>
            <TableCell className="font-mono text-xs text-slate-300 py-3 text-left">
              {p.message_id !== null ? p.message_id : "N/A"}
            </TableCell>
            <TableCell className="text-[11px] text-slate-400 py-3 text-left">
              {formatDate(p.created_at)}
            </TableCell>
          </TableRow>
        ))}
        {packets.length === 0 && (
          <TableRow>
            <TableCell colSpan={4} className="text-center py-12 text-slate-400 text-xs">
              {loading ? "Querying PostgreSQL rows..." : "No packet records found"}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

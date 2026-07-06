import Link from "next/link";
import { AlertTriangle, Bell, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableRow } from "../ui/table";
import { Event } from "../../types";
import { cn } from "../../lib/utils";

interface RecentEventsCardProps {
  events: Event[];
  selectedVehicleId: number | "all";
  onSelectVehicle: (id: number | "all") => void;
}

export function RecentEventsCard({ events, selectedVehicleId, onSelectVehicle }: RecentEventsCardProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 relative overflow-hidden flex flex-col">
      <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-white text-sm">{selectedVehicleId === "all" ? "Recent Events" : "Vehicle Events"}</CardTitle>
        </div>
        <Link href="/events" className="text-[10px] text-cyan-400 hover:text-cyan-300 font-bold uppercase tracking-wider">
          View All
        </Link>
      </CardHeader>
      <CardContent className="p-0 overflow-y-auto max-h-[295px] flex-1">
        <Table>
          <TableBody>
            {events.map((event) => (
              <TableRow
                key={event.id}
                onClick={() => onSelectVehicle(event.vehicle_id)}
                className="border-[#1e294b]/20 hover:bg-[#131a2d]/30 transition-colors cursor-pointer"
              >
                <TableCell className="p-2.5">
                  <div className="flex items-center gap-2.5 text-left">
                    <div className={cn(
                      "h-7 w-7 rounded-lg border flex items-center justify-center shrink-0",
                      event.severity === "Critical"
                        ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
                        : event.severity === "Warning"
                          ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                          : "bg-cyan-500/10 border-cyan-500/20 text-cyan-400"
                    )}>
                      {event.severity === "Critical" ? <ShieldAlert className="h-4 w-4" /> : event.severity === "Warning" ? <AlertTriangle className="h-4 w-4" /> : <Bell className="h-4 w-4" />}
                    </div>
                    <div className="min-w-0">
                      <span className="text-[11px] font-bold text-slate-200 block truncate">{event.event_type}</span>
                      <span className="text-[10px] text-slate-500 truncate block">{event.vehicle_name || `Vehicle #${event.vehicle_id}`}</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="p-2.5 text-right font-mono text-[9px] text-slate-400">
                  {new Date(event.created_at.endsWith("Z") ? event.created_at : `${event.created_at}Z`).toLocaleTimeString()}
                </TableCell>
                <TableCell className="p-2.5 text-right">
                  <span className={cn(
                    "inline-flex items-center px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase border",
                    event.severity === "Critical"
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                      : event.severity === "Warning"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                  )}>
                    {event.severity === "Critical" ? "Critical" : event.severity === "Warning" ? "Warning" : "Info"}
                  </span>
                </TableCell>
              </TableRow>
            ))}
            {events.length === 0 && (
              <TableRow>
                <TableCell className="text-center py-12 text-slate-400 text-xs">
                  No events logged
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

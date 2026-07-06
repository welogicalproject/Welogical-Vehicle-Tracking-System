import React from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { cn } from "../../lib/utils";
import { Event } from "../../types";

interface RecentEventsTableProps {
  recentEvents: Event[];
}

export function RecentEventsTable({ recentEvents }: RecentEventsTableProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="text-left">
          <CardTitle className="text-white text-base">Recent Events Log</CardTitle>
          <CardDescription>Decoded telemetry violations.</CardDescription>
        </div>
        <Link
          href="/events"
          className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
        >
          View Events <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                Time
              </TableHead>
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                Vehicle
              </TableHead>
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                Event Type
              </TableHead>
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider text-right">
                Severity
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recentEvents.slice(0, 5).map((ev) => (
              <TableRow
                key={ev.id}
                className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
              >
                <TableCell className="text-xs font-mono text-slate-400 text-left">
                  {new Date(
                    ev.created_at.endsWith("Z") ? ev.created_at : `${ev.created_at}Z`
                  ).toLocaleTimeString()}
                </TableCell>
                <TableCell className="font-semibold text-slate-200 text-left">
                  {ev.vehicle_name || `Vehicle #${ev.vehicle_id}`}
                </TableCell>
                <TableCell className="text-xs font-semibold text-cyan-400 text-left">
                  {ev.event_type}
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border",
                      ev.severity === "Critical"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : ev.severity === "Warning"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                    )}
                  >
                    {ev.severity}
                  </span>
                </TableCell>
              </TableRow>
            ))}
            {recentEvents.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-6 text-slate-400 text-xs">
                  No telemetry anomalies logged
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

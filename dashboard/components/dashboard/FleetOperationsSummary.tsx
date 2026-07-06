import React from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { cn } from "../../lib/utils";
import { getStatus } from "../../utils/tracking";
import { Vehicle } from "../../types";

interface FleetOperationsSummaryProps {
  vehicles: Vehicle[];
}

export function FleetOperationsSummary({ vehicles }: FleetOperationsSummaryProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="text-left">
          <CardTitle className="text-white text-base">Fleet Operations Summary</CardTitle>
          <CardDescription>Current registered tracking nodes.</CardDescription>
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
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                Vehicle Name
              </TableHead>
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                Device UID
              </TableHead>
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider">
                Status
              </TableHead>
              <TableHead className="text-slate-400 text-xs font-bold uppercase tracking-wider text-right">
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {vehicles.slice(0, 5).map((v) => {
              const status = getStatus(v.last_seen);
              return (
                <TableRow
                  key={v.id}
                  className="border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors"
                >
                  <TableCell className="font-semibold text-slate-100 text-left">
                    {v.vehicle_name}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-cyan-400 text-left">
                    {v.device_uid}
                  </TableCell>
                  <TableCell className="text-left">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide border",
                        status === "online"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : status === "idle"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                      )}
                    >
                      {status}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <Link
                      href={`/vehicles/${v.id}`}
                      className="bg-[#131a2d] hover:bg-[#1e294b] text-xs text-cyan-400 font-semibold border border-[#1e294b] px-2.5 py-1 rounded-lg transition-all"
                    >
                      Analyze
                    </Link>
                  </TableCell>
                </TableRow>
              );
            })}
            {vehicles.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-6 text-slate-400 text-xs">
                  No vehicles registered
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

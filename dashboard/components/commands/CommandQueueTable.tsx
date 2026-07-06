import React, { useMemo } from "react";
import { Trash2 } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/date";
import { CommandStatusBadge } from "./CommandStatusBadge";
import { DeviceCommand } from "../../types";

interface CommandQueueTableProps {
  commands: DeviceCommand[];
  loading: boolean;
  selectedCommandId: number | null;
  onSelectCommand: (cmdId: number) => void;
  onDeleteCommand: (cmdId: number) => void;
}

export function CommandQueueTable({
  commands,
  loading,
  selectedCommandId,
  onSelectCommand,
  onDeleteCommand,
}: CommandQueueTableProps) {
  const commandGroups = useMemo(() => {
    return {
      PENDING: commands.filter((command) => command.status === "PENDING"),
      SENT: commands.filter((command) => command.status === "SENT"),
      EXECUTED: commands.filter((command) => command.status === "EXECUTED"),
      FAILED: commands.filter((command) => command.status === "FAILED"),
    };
  }, [commands]);

  return (
    <div className="space-y-6">
      {/* Command Status Counts Grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Object.entries(commandGroups).map(([status, rows]) => (
          <div
            key={status}
            className="rounded-xl border border-[#1e294b]/60 bg-[#131a2d]/40 p-4 text-left"
          >
            <div className="text-[10px] font-bold tracking-wider uppercase text-slate-500">
              {status}
            </div>
            <div className="mt-1 text-xl font-extrabold text-white">{rows.length}</div>
          </div>
        ))}
      </div>

      {/* Queue Table Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-[#1e294b]/40 hover:bg-transparent">
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                  Vehicle
                </TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                  Command
                </TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                  Lifecycle Status
                </TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs">
                  Dispatched Time
                </TableHead>
                <TableHead className="text-slate-400 font-bold uppercase tracking-wider text-xs text-right">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {commands.slice(0, 15).map((cmd) => (
                <TableRow
                  key={cmd.id}
                  onClick={() => onSelectCommand(cmd.id)}
                  className={cn(
                    "border-[#1e294b]/20 hover:bg-[#131a2d]/20 transition-colors cursor-pointer",
                    selectedCommandId === cmd.id &&
                      "bg-[#132238]/60 hover:bg-[#132238]/80 border-cyan-500/20"
                  )}
                >
                  <TableCell className="font-bold text-white text-xs py-3.5 text-left">
                    {cmd.vehicle_name || `Vehicle #${cmd.vehicle_id}`}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-cyan-400 py-3.5 text-left">
                    {cmd.command_name}
                    {cmd.command_value ? `=${cmd.command_value}` : ""}
                  </TableCell>
                  <TableCell className="py-3.5 text-left">
                    <CommandStatusBadge status={cmd.status} />
                  </TableCell>
                  <TableCell className="text-xs text-slate-400 py-3.5 text-left">
                    {formatDate(cmd.created_at)}
                  </TableCell>
                  <TableCell className="text-right py-3.5" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => onDeleteCommand(cmd.id)}
                      className="p-1.5 hover:bg-rose-500/10 rounded-lg text-slate-400 hover:text-rose-400 transition-colors"
                      title="Remove Command"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
              {commands.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12 text-slate-400 text-xs">
                    {loading ? "Loading command buffer..." : "Command queue buffer empty"}
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

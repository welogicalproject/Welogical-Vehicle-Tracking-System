import React from "react";
import { Info } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { formatDate } from "../../lib/date";
import { DeviceCommand, CommandLog } from "../../types";

interface CommandAuditLogProps {
  selectedCommandId: number | null;
  setSelectedCommandId: (id: number | null) => void;
  selectedCommand?: DeviceCommand;
  auditLogs: CommandLog[];
  loadingLogs: boolean;
}

export function CommandAuditLog({
  selectedCommandId,
  setSelectedCommandId,
  selectedCommand,
  auditLogs,
  loadingLogs,
}: CommandAuditLogProps) {
  if (!selectedCommandId) return null;

  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 text-left animate-fade-in">
      <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between border-b border-[#1e294b]/30">
        <div>
          <CardTitle className="text-white text-xs font-bold uppercase tracking-wider flex items-center gap-2">
            <Info className="h-4 w-4 text-cyan-400" />
            Audit Log Timeline &bull; Command #{selectedCommandId}
          </CardTitle>
          {selectedCommand && (
            <CardDescription className="text-slate-400 text-xs mt-1">
              {selectedCommand.command_name} payload enqueued for {selectedCommand.vehicle_name}
            </CardDescription>
          )}
        </div>
        <button
          onClick={() => setSelectedCommandId(null)}
          className="text-xs font-bold text-slate-400 hover:text-white"
        >
          Clear Selection
        </button>
      </CardHeader>
      <CardContent className="p-0 pt-4 space-y-3">
        {loadingLogs ? (
          <div className="text-center py-4 text-slate-400 text-xs">Loading transaction logs...</div>
        ) : auditLogs.length === 0 ? (
          <div className="text-slate-400 text-xs py-4 text-center">
            No transaction logs captured yet for this command.
          </div>
        ) : (
          <div className="space-y-3 relative pl-4 border-l border-[#1e294b]">
            {auditLogs.map((log) => (
              <div key={log.id} className="relative">
                <span className="absolute -left-[20px] top-1 h-2 w-2 rounded-full bg-cyan-400 border border-[#0b0f19]" />
                <div className="text-xs font-bold text-slate-200">
                  Status Transition to <span className="text-cyan-300 font-semibold">{log.status}</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {log.message || "Queue initialized state."}
                </p>
                <span className="text-[10px] text-slate-500 font-mono mt-1 block">
                  Timestamp: {formatDate(log.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

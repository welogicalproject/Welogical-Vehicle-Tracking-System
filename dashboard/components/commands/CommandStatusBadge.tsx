import React from "react";
import { cn } from "../../lib/utils";
import { DeviceCommand } from "../../types";

interface CommandStatusBadgeProps {
  status: DeviceCommand["status"];
}

const STATUS_STYLES: Record<string, string> = {
  // New lifecycle states
  Queued:       "bg-amber-500/10 text-amber-400 border-amber-500/20",
  Sending:      "bg-blue-400/10 text-blue-300 border-blue-400/20",
  Delivered:    "bg-sky-500/10 text-sky-400 border-sky-500/20",
  Acknowledged: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  Executing:    "bg-violet-500/10 text-violet-400 border-violet-500/20",
  Completed:    "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  Failed:       "bg-rose-500/10 text-rose-400 border-rose-500/20",
  "Timed Out":  "bg-orange-500/10 text-orange-400 border-orange-500/20",
  Cancelled:    "bg-slate-500/10 text-slate-400 border-slate-500/20",
  // Legacy aliases
  PENDING:      "bg-amber-500/10 text-amber-400 border-amber-500/20",
  SENT:         "bg-blue-500/10 text-blue-400 border-blue-500/20",
  EXECUTED:     "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  FAILED:       "bg-rose-500/10 text-rose-400 border-rose-500/20",
};

export function CommandStatusBadge({ status }: CommandStatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? "bg-slate-500/10 text-slate-400 border-slate-500/20";
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-[9px] font-extrabold uppercase border",
        style
      )}
    >
      {status}
    </span>
  );
}

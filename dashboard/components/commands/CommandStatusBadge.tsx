import React from "react";
import { cn } from "../../lib/utils";
import { DeviceCommand } from "../../types";

interface CommandStatusBadgeProps {
  status: DeviceCommand["status"];
}

export function CommandStatusBadge({ status }: CommandStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-[9px] font-extrabold uppercase border",
        status === "EXECUTED"
          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          : status === "SENT"
          ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
          : status === "FAILED"
          ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
      )}
    >
      {status}
    </span>
  );
}

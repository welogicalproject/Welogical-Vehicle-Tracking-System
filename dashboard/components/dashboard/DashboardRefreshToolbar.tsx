import React from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "../../lib/utils";

interface DashboardRefreshToolbarProps {
  refreshing: boolean;
  onRefresh: () => void;
}

export function DashboardRefreshToolbar({
  refreshing,
  onRefresh,
}: DashboardRefreshToolbarProps) {
  return (
    <div className="flex items-center justify-between bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        <span className="text-xs font-semibold text-slate-400">
          Telemetry Feed Connected (refreshing every 10s)
        </span>
      </div>
      <button
        onClick={onRefresh}
        disabled={refreshing}
        className="flex items-center gap-2 bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-200 font-semibold text-xs px-3.5 py-1.5 rounded-lg transition-all"
      >
        <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
        Refresh Feed
      </button>
    </div>
  );
}

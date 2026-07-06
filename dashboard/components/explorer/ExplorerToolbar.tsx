import React from "react";
import { Car, MapPin, Terminal, Search, RefreshCw } from "lucide-react";
import { Input } from "../ui/input";
import { cn } from "../../lib/utils";

interface ExplorerToolbarProps {
  activeTab: "vehicles" | "locations" | "packets";
  onTabChange: (tab: "vehicles" | "locations" | "packets") => void;
  search: string;
  onSearchChange: (val: string) => void;
  refreshing: boolean;
  onRefresh: () => void;
}

export function ExplorerToolbar({
  activeTab,
  onTabChange,
  search,
  onSearchChange,
  refreshing,
  onRefresh,
}: ExplorerToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#131a2d]/40 border border-[#1e294b]/60 rounded-xl px-4 py-3">
      <div className="flex-1 flex flex-col sm:flex-row items-center gap-3">
        {/* Tab buttons */}
        <div className="flex items-center gap-1 bg-[#0b0f19] p-1 rounded-lg border border-[#1e294b] shrink-0">
          <button
            onClick={() => onTabChange("vehicles")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
              activeTab === "vehicles"
                ? "bg-cyan-500 text-white shadow"
                : "text-slate-400 hover:text-white"
            )}
          >
            <Car size={13} />
            vehicles
          </button>

          <button
            onClick={() => onTabChange("locations")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
              activeTab === "locations"
                ? "bg-cyan-500 text-white shadow"
                : "text-slate-400 hover:text-white"
            )}
          >
            <MapPin size={13} />
            locations
          </button>

          <button
            onClick={() => onTabChange("packets")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
              activeTab === "packets"
                ? "bg-cyan-500 text-white shadow"
                : "text-slate-400 hover:text-white"
            )}
          >
            <Terminal size={13} />
            packets
          </button>
        </div>

        {/* Search box */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder={`Search ${activeTab}...`}
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 bg-[#0b0f19] border-[#1e294b] text-xs h-9"
          />
        </div>
      </div>

      <button
        onClick={onRefresh}
        disabled={refreshing}
        className="flex items-center gap-2 bg-[#131a2d] hover:bg-[#1e294b] border border-[#1e294b] text-slate-200 font-semibold text-xs px-3.5 py-2 rounded-lg transition-all shrink-0"
      >
        <RefreshCw className={cn("h-3.5 w-3.5", refreshing ? "animate-spin" : "")} />
        Refresh Explorer
      </button>
    </div>
  );
}

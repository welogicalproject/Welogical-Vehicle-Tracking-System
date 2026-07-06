import React from "react";
import { Car, TrendingUp, Clock, Radio } from "lucide-react";
import { Card, CardContent } from "../ui/card";

interface StatsGridProps {
  loading: boolean;
  totalVehiclesCount: number | string;
  activeOnlineCount: number | string;
  activeIdleCount: number | string;
  activeOfflineCount: number | string;
}

export function StatsGrid({
  loading,
  totalVehiclesCount,
  activeOnlineCount,
  activeIdleCount,
  activeOfflineCount,
}: StatsGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Total Vehicles Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-6 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">
              Total Assets
            </span>
            <div className="text-2xl font-extrabold text-white">
              {loading ? "..." : totalVehiclesCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Car className="h-5 w-5" />
          </div>
        </CardContent>
      </Card>

      {/* Moving Vehicles Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-6 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">
              Active / Moving
            </span>
            <div className="text-2xl font-extrabold text-emerald-400">
              {loading ? "..." : activeOnlineCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <TrendingUp className="h-5 w-5 animate-pulse" />
          </div>
        </CardContent>
      </Card>

      {/* Stopped Vehicles Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-6 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">
              Idle / Stopped
            </span>
            <div className="text-2xl font-extrabold text-amber-400">
              {loading ? "..." : activeIdleCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Clock className="h-5 w-5" />
          </div>
        </CardContent>
      </Card>

      {/* Offline Vehicles Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-6 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">
              Inactive / Offline
            </span>
            <div className="text-2xl font-extrabold text-slate-400">
              {loading ? "..." : activeOfflineCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-slate-500/10 border border-slate-500/20 flex items-center justify-center text-slate-400">
            <Radio className="h-5 w-5" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

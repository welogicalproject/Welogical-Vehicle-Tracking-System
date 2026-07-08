import React from "react";
import { Car, TrendingUp, Clock, Radio, ShieldAlert, Route, Fuel, Activity, Compass } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { cn } from "../../lib/utils";

interface StatsGridProps {
  loading: boolean;
  totalVehiclesCount: number;
  drivingCount: number;
  idleCount: number;
  parkedCount: number;
  offlineCount: number;
  gpsLostCount: number;
  
  // Optional daily summary rollup parameters
  distanceToday?: number;
  fuelUsedToday?: number;
}

export function StatsGrid({
  loading,
  totalVehiclesCount,
  drivingCount,
  idleCount,
  parkedCount,
  offlineCount,
  gpsLostCount,
  distanceToday,
  fuelUsedToday,
}: StatsGridProps) {
  const Skeleton = () => (
    <div className="h-6 bg-[#1e294b]/40 rounded animate-pulse w-14" />
  );

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8 gap-4">
      {/* Total Vehicles Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Total Assets
            </span>
            <div className="text-xl font-extrabold text-white">
              {loading ? <Skeleton /> : totalVehiclesCount}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Car className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Driving (Active) Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Driving
            </span>
            <div className="text-xl font-extrabold text-emerald-400">
              {loading ? <Skeleton /> : drivingCount}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <TrendingUp className="h-4 w-4 animate-pulse" />
          </div>
        </CardContent>
      </Card>

      {/* Idle Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Idle
            </span>
            <div className="text-xl font-extrabold text-amber-400">
              {loading ? <Skeleton /> : idleCount}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <Clock className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Parked Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Parked
            </span>
            <div className="text-xl font-extrabold text-blue-400">
              {loading ? <Skeleton /> : parkedCount}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Car className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Offline Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Offline
            </span>
            <div className="text-xl font-extrabold text-slate-400">
              {loading ? <Skeleton /> : offlineCount}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-slate-500/10 border border-slate-500/20 flex items-center justify-center text-slate-400">
            <Radio className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* GPS Lost Card */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl relative overflow-hidden">
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              GPS Lost
            </span>
            <div className="text-xl font-extrabold text-rose-400">
              {loading ? <Skeleton /> : gpsLostCount}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <Compass className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Distance Today */}
      <Card className={cn(
        "rounded-xl relative overflow-hidden",
        distanceToday !== undefined && distanceToday > 0
          ? "border-cyan-500/30 bg-[#131a2d]/40 border"
          : "border-[#1e294b]/40 bg-[#131a2d]/20"
      )}>
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Distance Today
            </span>
            <div className="text-base font-extrabold text-cyan-400">
              {loading ? <Skeleton /> : (distanceToday !== undefined && distanceToday > 0 ? `${distanceToday.toFixed(1)} km` : "0.0 km")}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Route className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>

      {/* Fuel Used Today */}
      <Card className={cn(
        "rounded-xl relative overflow-hidden",
        fuelUsedToday !== undefined && fuelUsedToday > 0
          ? "border-emerald-500/30 bg-[#131a2d]/40 border"
          : "border-[#1e294b]/40 bg-[#131a2d]/20"
      )}>
        <CardContent className="p-4 flex items-center justify-between h-full">
          <div className="space-y-1">
            <span className="text-[9px] font-bold text-slate-500 tracking-wider uppercase block">
              Fuel Used
            </span>
            <div className="text-base font-extrabold text-emerald-400">
              {loading ? <Skeleton /> : (fuelUsedToday !== undefined && fuelUsedToday > 0 ? `${fuelUsedToday.toFixed(1)} L` : "0.0 L")}
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Fuel className="h-4 w-4" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

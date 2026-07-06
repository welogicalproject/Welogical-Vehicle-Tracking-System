import React from "react";
import { Activity, ShieldAlert, Send, TrendingUp } from "lucide-react";
import { Card, CardContent } from "../ui/card";

interface AnalyticsSummaryCardsProps {
  loading: boolean;
  locationsCount: number;
  eventsCount: number;
  commandsCount: number;
  avgUtilizationPct: number;
}

export function AnalyticsSummaryCards({
  loading,
  locationsCount,
  eventsCount,
  commandsCount,
  avgUtilizationPct,
}: AnalyticsSummaryCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
        <CardContent className="p-5 flex items-center justify-between">
          <div className="space-y-1 text-left">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block">
              Telemetry Logs
            </span>
            <div className="text-2xl font-extrabold text-white">
              {loading ? "..." : locationsCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Activity size={18} />
          </div>
        </CardContent>
      </Card>

      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
        <CardContent className="p-5 flex items-center justify-between">
          <div className="space-y-1 text-left">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block">
              System Alerts
            </span>
            <div className="text-2xl font-extrabold text-white">
              {loading ? "..." : eventsCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <ShieldAlert size={18} />
          </div>
        </CardContent>
      </Card>

      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
        <CardContent className="p-5 flex items-center justify-between">
          <div className="space-y-1 text-left">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block">
              Queue Commands
            </span>
            <div className="text-2xl font-extrabold text-white">
              {loading ? "..." : commandsCount}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Send size={18} />
          </div>
        </CardContent>
      </Card>

      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
        <CardContent className="p-5 flex items-center justify-between">
          <div className="space-y-1 text-left">
            <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase block">
              Avg Utilization
            </span>
            <div className="text-2xl font-extrabold text-emerald-400">
              {loading ? "..." : `${avgUtilizationPct.toFixed(1)}%`}
            </div>
          </div>
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <TrendingUp size={18} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

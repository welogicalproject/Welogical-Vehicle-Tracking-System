import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

export function SystemAlertsCard({ offlineCount }: { offlineCount: number }) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 relative overflow-hidden flex flex-col justify-between">
      <CardHeader className="p-0 pb-4">
        <CardTitle className="text-white text-sm">System Alerts</CardTitle>
      </CardHeader>
      <CardContent className="p-0 space-y-3 flex-1 flex flex-col justify-center">
        {offlineCount > 0 ? (
          <div className="border border-rose-500/20 bg-rose-500/5 rounded-lg px-4 py-2.5 flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
            <span className="text-xs font-bold text-rose-400">{offlineCount} Vehicle Offline</span>
            <span className="text-[10px] text-slate-500 font-semibold ml-auto">Requires Attention</span>
          </div>
        ) : (
          <div className="border border-emerald-500/20 bg-emerald-500/5 rounded-lg px-4 py-2.5 flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-xs font-bold text-emerald-400">All Devices Active</span>
            <span className="text-[10px] text-slate-500 font-semibold ml-auto">0 Offline</span>
          </div>
        )}

        <div className="border border-amber-500/20 bg-amber-500/5 rounded-lg px-4 py-2.5 flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          <span className="text-xs font-bold text-amber-400">Warnings Active</span>
          <span className="text-[10px] text-slate-500 font-semibold ml-auto">Review Events Log</span>
        </div>

        <div className="border border-emerald-500/20 bg-emerald-500/5 rounded-lg px-4 py-2.5 flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-xs font-bold text-emerald-400">System Healthy</span>
          <span className="text-[10px] text-slate-500 font-semibold ml-auto">All Systems Operational</span>
        </div>
      </CardContent>
    </Card>
  );
}

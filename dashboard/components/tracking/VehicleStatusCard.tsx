import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface FleetCounts {
  total: number;
  moving: number;
  stopped: number;
  offline: number;
}

export function VehicleStatusCard({ counts, loading }: { counts: FleetCounts; loading: boolean }) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 relative overflow-hidden">
      <CardHeader className="p-0 pb-3">
        <CardTitle className="text-white text-sm">Live Status Summary</CardTitle>
      </CardHeader>
      <CardContent className="p-0 grid grid-cols-2 gap-4">
        <div className="bg-[#0b0f19]/30 border border-[#1e294b]/40 rounded-lg p-3">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Total Vehicles</span>
          <span className="text-xl font-extrabold text-white block mt-1">{loading ? "..." : counts.total}</span>
          <span className="text-[10px] text-emerald-400 font-bold mt-1 block">Online: {counts.total - counts.offline}</span>
        </div>
        <div className="bg-[#0b0f19]/30 border border-[#1e294b]/40 rounded-lg p-3">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Moving</span>
          <span className="text-xl font-extrabold text-emerald-400 block mt-1">{loading ? "..." : counts.moving}</span>
        </div>
        <div className="bg-[#0b0f19]/30 border border-[#1e294b]/40 rounded-lg p-3">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Stopped</span>
          <span className="text-xl font-extrabold text-amber-400 block mt-1">{loading ? "..." : counts.stopped}</span>
        </div>
        <div className="bg-[#0b0f19]/30 border border-[#1e294b]/40 rounded-lg p-3">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Offline</span>
          <span className="text-xl font-extrabold text-rose-500 block mt-1">{loading ? "..." : counts.offline}</span>
        </div>
      </CardContent>
    </Card>
  );
}

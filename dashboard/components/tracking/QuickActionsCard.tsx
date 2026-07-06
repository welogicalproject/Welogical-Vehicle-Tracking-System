import Link from "next/link";
import { FileText, Globe, Send } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { VehicleTrackingSnapshot } from "../../types";
import { exportSnapshotsCsv } from "../../utils/tracking";

export function QuickActionsCard({ snapshots }: { snapshots: VehicleTrackingSnapshot[] }) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 relative overflow-hidden">
      <CardHeader className="p-0 pb-4">
        <CardTitle className="text-white text-sm">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="p-0 grid grid-cols-2 gap-4">
        <Link href="/commands">
          <button className="w-full bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 font-bold text-xs py-3 rounded-lg border border-purple-500/20 flex items-center justify-center gap-2 transition-all">
            <Send className="h-4 w-4" /> Send Command
          </button>
        </Link>
        <Link href="/reports">
          <button className="w-full bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-bold text-xs py-3 rounded-lg border border-blue-500/20 flex items-center justify-center gap-2 transition-all">
            <FileText className="h-4 w-4" /> View Reports
          </button>
        </Link>
        <Link href="/geofences">
          <button className="w-full bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 font-bold text-xs py-3 rounded-lg border border-emerald-500/20 flex items-center justify-center gap-2 transition-all">
            <Globe className="h-4 w-4" /> Add Geofence
          </button>
        </Link>
        <button
          onClick={() => exportSnapshotsCsv(snapshots)}
          className="w-full bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 font-bold text-xs py-3 rounded-lg border border-amber-500/20 flex items-center justify-center gap-2 transition-all"
        >
          <FileText className="h-4 w-4" /> Export Data
        </button>
      </CardContent>
    </Card>
  );
}

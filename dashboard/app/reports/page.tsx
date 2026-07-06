"use client";

import { FileText, Download, Calendar } from "lucide-react";
import { Button } from "../../components/ui/button";

export default function ReportsPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-wide">Fleet Reports</h2>
          <p className="text-slate-400 text-sm mt-1">
            Export historical coordinates logs, diagnostic registers, and speed events.
          </p>
        </div>
        <Button variant="secondary" className="flex items-center gap-2">
          <Calendar className="h-4 w-4" /> Schedule Report
        </Button>
      </div>

      <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-12 text-center max-w-2xl mx-auto mt-12">
        <div className="h-12 w-12 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 mx-auto mb-4 border border-cyan-500/20">
          <FileText className="h-6 w-6" />
        </div>
        <h3 className="text-lg font-bold text-white">Reports Engine Loaded</h3>
        <p className="text-slate-400 text-sm mt-2 max-w-md mx-auto">
          No custom reports generated yet. Select a vehicle timeline to generate an excel/csv summary of telemetry parameters.
        </p>
        <div className="mt-6 flex justify-center">
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Download className="h-4 w-4" /> Export All Vehicles Log (CSV)
          </Button>
        </div>
      </div>
    </div>
  );
}

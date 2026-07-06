"use client";

import { Globe, Plus, ShieldAlert } from "lucide-react";
import { Button } from "../../components/ui/button";

export default function GeofencesPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-wide">Geofence Controls</h2>
          <p className="text-slate-400 text-sm mt-1">
            Draw and configure polygon geofences to track entry and exit events.
          </p>
        </div>
        <Button variant="secondary" className="flex items-center gap-2">
          <Plus className="h-4 w-4" /> Draw Geofence
        </Button>
      </div>

      <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-12 text-center max-w-2xl mx-auto mt-12">
        <div className="h-12 w-12 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 mx-auto mb-4 border border-cyan-500/20">
          <Globe className="h-6 w-6" />
        </div>
        <h3 className="text-lg font-bold text-white">Geofence Engine Active</h3>
        <p className="text-slate-400 text-sm mt-2 max-w-md mx-auto">
          Geofences are computed by the backend telemetry engine. Geofencing alert rules and map coordinates can be drawn here.
        </p>
        <div className="mt-6 flex items-center gap-2 justify-center text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-4 py-2 rounded-lg w-fit mx-auto">
          <ShieldAlert className="h-4 w-4" />
          <span>Note: Real-time boundary violations will log as Severity Warnings in the dashboard.</span>
        </div>
      </div>
    </div>
  );
}

"use client";

import { Sliders, Save, Database, Shield } from "lucide-react";
import { Button } from "../../components/ui/button";

export default function SettingsPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-wide">Global System Settings</h2>
          <p className="text-slate-400 text-sm mt-1">
            Configure system variables, polling intervals, and integrations.
          </p>
        </div>
        <Button variant="secondary" className="flex items-center gap-2">
          <Save className="h-4 w-4" /> Save Changes
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
        <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Sliders className="h-4.5 w-4.5 text-cyan-400" />
            General Configurations
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                Telemetry Polling Rate (Seconds)
              </label>
              <input 
                type="number" 
                defaultValue={10} 
                className="w-full bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400" 
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                Inactive Offline Threshold (Minutes)
              </label>
              <input 
                type="number" 
                defaultValue={5} 
                className="w-full bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400" 
              />
            </div>
          </div>
        </div>

        <div className="border border-[#1e294b]/60 rounded-xl bg-[#131a2d]/40 p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Database className="h-4.5 w-4.5 text-cyan-400" />
            Database Integrations
          </h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                PostgreSQL Host
              </label>
              <input 
                type="text" 
                defaultValue="localhost" 
                disabled 
                className="w-full bg-[#0b0f19]/60 border border-[#1e294b]/60 rounded-lg px-3 py-2 text-sm text-slate-400 cursor-not-allowed" 
              />
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-[#0b0f19]/30 p-3 rounded-lg border border-[#1e294b]/20">
              <Shield className="h-4 w-4 text-cyan-400 shrink-0" />
              <span>Configurations are managed through `.env` server settings and are locked in the console interface.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

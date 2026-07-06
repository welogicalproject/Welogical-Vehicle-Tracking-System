import React from "react";
import { Send } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Vehicle } from "../../types";

interface DispatchCommandFormProps {
  vehicles: Vehicle[];
  targetVehicle: string;
  setTargetVehicle: (val: string) => void;
  commandName: string;
  setCommandName: (val: string) => void;
  commandValue: string;
  setCommandValue: (val: string) => void;
  submitting: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

export function DispatchCommandForm({
  vehicles,
  targetVehicle,
  setTargetVehicle,
  commandName,
  setCommandName,
  commandValue,
  setCommandValue,
  submitting,
  onSubmit,
}: DispatchCommandFormProps) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 self-start">
      <CardHeader className="p-0 pb-4">
        <CardTitle className="text-white text-sm flex items-center gap-2">
          <Send className="h-4.5 w-4.5 text-purple-400" />
          Dispatch New Command
        </CardTitle>
        <CardDescription>Select target device and parameters.</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <form onSubmit={onSubmit} className="space-y-4 text-left">
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
              Target Vehicle
            </label>
            <select
              value={targetVehicle}
              onChange={(e) => setTargetVehicle(e.target.value)}
              className="w-full bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-2 text-xs text-white font-semibold focus:outline-none transition-all"
            >
              {vehicles.map((v) => (
                <option key={v.id} value={v.id.toString()}>
                  {v.vehicle_name} ({v.device_uid})
                </option>
              ))}
              {vehicles.length === 0 && <option value="">No vehicles registered</option>}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
              Command Code
            </label>
            <select
              value={commandName}
              onChange={(e) => setCommandName(e.target.value)}
              className="w-full bg-[#0b0f19] border border-[#1e294b] rounded-lg px-3 py-2 text-xs text-white font-semibold focus:outline-none transition-all"
            >
              <option value="STOPV">STOPV (Stop Engine / Immobilize)</option>
              <option value="RESUME">RESUME (Re-enable Engine)</option>
              <option value="SET_INT">SET_INT (Set Telemetry Interval)</option>
              <option value="PING">PING (Ping Status Log)</option>
              <option value="REBOOT">REBOOT (Reboot Hardware Board)</option>
              <option value="CONFIG">CONFIG (APN/Server Configurations)</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
              Parameters Value (Optional)
            </label>
            <Input
              placeholder="e.g. 30 or APN_name..."
              value={commandValue}
              onChange={(e) => setCommandValue(e.target.value)}
              className="bg-[#0b0f19] border-[#1e294b] text-xs"
            />
          </div>

          <Button
            type="submit"
            disabled={submitting || vehicles.length === 0}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs py-2.5 rounded-lg transition-all flex items-center justify-center gap-2"
          >
            <Send className="h-4 w-4" />
            {submitting ? "Enqueuing..." : "Enqueue Command"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

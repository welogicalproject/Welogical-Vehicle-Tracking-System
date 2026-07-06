"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { VehicleTrackingSnapshot } from "../../types";
import { getVehicleColor } from "../../utils/tracking";

export function SpeedChart({ data, snapshots }: { data: Record<string, any>[]; snapshots: VehicleTrackingSnapshot[] }) {
  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 relative overflow-hidden flex-1">
      <CardHeader className="p-0 pb-3">
        <CardTitle className="text-white text-sm">Speed Overview</CardTitle>
      </CardHeader>
      <CardContent className="p-0 h-44 w-full">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e294b/40" vertical={false} />
              <XAxis dataKey="time" stroke="#64748b" fontSize={9} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={9} tickLine={false} unit=" km/h" />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e294b", color: "#fff" }} />
              {snapshots.map((snapshot, index) => (
                <Line
                  key={snapshot.vehicle.id}
                  type="monotone"
                  dataKey={snapshot.vehicle.vehicle_name}
                  stroke={getVehicleColor(index)}
                  strokeWidth={1.8}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-400 text-xs">
            No speed data logged
          </div>
        )}
      </CardContent>
    </Card>
  );
}

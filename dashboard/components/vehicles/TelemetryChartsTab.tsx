import React, { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  AreaChart,
  Area,
} from "recharts";
import { VehicleTrackingSnapshot } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface TelemetryChartsTabProps {
  snapshot: VehicleTrackingSnapshot;
}

export function TelemetryChartsTab({ snapshot }: TelemetryChartsTabProps) {
  const chartsData = useMemo(() => {
    return snapshot.route_history.map((pt) => {
      const volt = pt.extra_data?.pwr?.volt;
      return {
        time: new Date(pt.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        speed: pt.speed,
        voltage: typeof volt === "number" ? volt / 1000 : null,
      };
    });
  }, [snapshot]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Historical Speed Chart */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5">
        <CardHeader className="p-0 pb-4">
          <CardTitle className="text-white text-sm">Speed Profile (Last 24 Hours)</CardTitle>
        </CardHeader>
        <CardContent className="p-0 h-64 w-full">
          {chartsData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartsData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e294b/30" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" fontSize={9} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={9} tickLine={false} unit=" km/h" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#1e294b",
                    color: "#fff",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="speed"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              No coordinates logged
            </div>
          )}
        </CardContent>
      </Card>

      {/* Battery Voltage Trends */}
      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5">
        <CardHeader className="p-0 pb-4">
          <CardTitle className="text-white text-sm">Internal Battery Load Trends</CardTitle>
        </CardHeader>
        <CardContent className="p-0 h-64 w-full">
          {chartsData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartsData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="voltageGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e294b/30" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" fontSize={9} tickLine={false} />
                <YAxis
                  stroke="#64748b"
                  fontSize={9}
                  tickLine={false}
                  unit=" V"
                  domain={["auto", "auto"]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#1e294b",
                    color: "#fff",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="voltage"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#voltageGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400 text-xs">
              No voltage data available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

import React from "react";
import {
  BarChart as BarIcon,
  TrendingUp,
  Send,
  PieChart as PieIcon,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import {
  VehicleActivityChart,
  EventDistributionChart,
  EventTrendChart,
  CommandAnalyticsChart,
} from "../charts";
import { Location, Event, DeviceCommand } from "../../types";

interface AnalyticsChartsSectionProps {
  locations: Location[];
  events: Event[];
  commands: DeviceCommand[];
  eventDistributionData: { name: string; value: number; color: string }[];
  eventTrendData: { time: string; count: number }[];
  vehicleActivityData: { vehicleName: string; count: number }[];
  utilizationStats: {
    chartData: { name: string; value: number; color: string }[];
    pct: number;
    movingMin: number;
    stoppedMin: number;
  };
  commandAnalyticsData: { name: string; count: number; color: string }[];
}

export function AnalyticsChartsSection({
  locations,
  events,
  commands,
  eventDistributionData,
  eventTrendData,
  vehicleActivityData,
  utilizationStats,
  commandAnalyticsData,
}: AnalyticsChartsSectionProps) {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      {/* A. Event Distribution */}
      <Card className="xl:col-span-1 border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5">
        <CardHeader className="p-0 pb-3 text-left">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <PieIcon className="h-4.5 w-4.5 text-rose-400" />
            Alerts Severity Distribution
          </CardTitle>
          <CardDescription>Visual split of Critical, Warning, and Info alerts.</CardDescription>
        </CardHeader>
        <CardContent className="p-0 flex items-center justify-center pt-2">
          {events.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">No alerts generated.</div>
          ) : (
            <EventDistributionChart data={eventDistributionData} />
          )}
        </CardContent>
      </Card>

      {/* B. Event Trend */}
      <Card className="xl:col-span-2 border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5">
        <CardHeader className="p-0 pb-3 text-left">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <TrendingUp className="h-4.5 w-4.5 text-cyan-400" />
            Alerts Chronological Trend
          </CardTitle>
          <CardDescription>Daily fleet alerts generation rate.</CardDescription>
        </CardHeader>
        <CardContent className="p-0 h-64 pt-2">
          {events.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">No events logged.</div>
          ) : (
            <EventTrendChart data={eventTrendData} />
          )}
        </CardContent>
      </Card>

      {/* C. Vehicle Ingestion Ranking */}
      <Card className="xl:col-span-2 border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5">
        <CardHeader className="p-0 pb-3 text-left">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <BarIcon className="h-4.5 w-4.5 text-cyan-400" />
            Vehicle Ingestion Density Ranking
          </CardTitle>
          <CardDescription>
            Ingested location telemetry packets count per vehicle.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 h-64 pt-2">
          {vehicleActivityData.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">No active data streams.</div>
          ) : (
            <VehicleActivityChart data={vehicleActivityData} />
          )}
        </CardContent>
      </Card>

      {/* D. Vehicle Utilization */}
      <Card className="xl:col-span-1 border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5 flex flex-col">
        <CardHeader className="p-0 pb-3 text-left">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <PieIcon className="h-4.5 w-4.5 text-emerald-400" />
            Motion Utilization Rate
          </CardTitle>
          <CardDescription>Aggregation of moving time vs stopped duration.</CardDescription>
        </CardHeader>
        <CardContent className="p-0 flex-1 flex flex-col justify-between pt-2">
          {locations.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">No coordinate logs.</div>
          ) : (
            <>
              <div className="flex items-center justify-center">
                <EventDistributionChart data={utilizationStats.chartData} />
              </div>
              <div className="grid grid-cols-2 gap-4 text-center text-xs border-t border-[#1e294b]/20 pt-3 mt-4">
                <div>
                  <span className="text-slate-500 font-bold uppercase tracking-wider block">
                    Moving Time
                  </span>
                  <strong className="text-emerald-400 text-sm">
                    {utilizationStats.movingMin} mins
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 font-bold uppercase tracking-wider block">
                    Stopped Time
                  </span>
                  <strong className="text-amber-500 text-sm">
                    {utilizationStats.stoppedMin} mins
                  </strong>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* E. Command Analytics */}
      <Card className="xl:col-span-3 border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl p-5">
        <CardHeader className="p-0 pb-3 text-left">
          <CardTitle className="text-white text-sm flex items-center gap-2">
            <Send className="h-4.5 w-4.5 text-blue-400" />
            Command Dispatch Success Rate
          </CardTitle>
          <CardDescription>Queued command states ratios.</CardDescription>
        </CardHeader>
        <CardContent className="p-0 h-64 pt-2">
          {commands.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">No commands dispatched.</div>
          ) : (
            <CommandAnalyticsChart data={commandAnalyticsData} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

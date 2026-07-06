import React from "react";
import { Trip } from "../../types";
import { Card, CardContent } from "../ui/card";
import { Navigation, Route, AlertTriangle, Compass, Award } from "lucide-react";

interface TripStatisticsProps {
  trips: Trip[];
  loading: boolean;
}

export function TripStatistics({ trips, loading }: TripStatisticsProps) {
  // Compute aggregate statistics
  const totalTrips = trips.length;
  const totalDistance = trips.reduce((acc, t) => acc + t.distance, 0);
  const totalDuration = trips.reduce((acc, t) => acc + t.duration, 0);
  
  const completedTrips = trips.filter(t => t.status === "COMPLETED");
  const cancelledTrips = trips.filter(t => t.status === "CANCELLED");
  const activeTrips = trips.filter(t => t.is_active || t.status === "ACTIVE");

  const averageDistance = totalTrips > 0 ? totalDistance / totalTrips : 0;
  
  // Format total duration into readable form
  const formatTotalTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  };

  const statCards = [
    {
      title: "Total Distance Logged",
      value: `${totalDistance.toFixed(1)} km`,
      desc: `Avg trip: ${averageDistance.toFixed(1)} km`,
      icon: Route,
      color: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    },
    {
      title: "Total Moving Duration",
      value: formatTotalTime(totalDuration),
      desc: `${totalTrips} recorded runs`,
      icon: Navigation,
      color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
    },
    {
      title: "Completed Trips",
      value: completedTrips.length.toString(),
      desc: `${activeTrips.length} active, ${cancelledTrips.length} cancelled`,
      icon: Compass,
      color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-panel h-24 rounded-xl border border-[#1e294b]/60 bg-[#131a2d]/40" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {statCards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <Card key={idx} className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl">
            <CardContent className="p-6 flex items-center justify-between">
              <div className="space-y-1 text-left">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  {card.title}
                </span>
                <h3 className="text-2xl font-black text-white font-mono tracking-tight leading-none pt-1">
                  {card.value}
                </h3>
                <span className="text-[11px] text-slate-400 font-semibold block pt-0.5">
                  {card.desc}
                </span>
              </div>
              <div className={`h-11 w-11 rounded-lg flex items-center justify-center border shrink-0 ${card.color}`}>
                <Icon className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

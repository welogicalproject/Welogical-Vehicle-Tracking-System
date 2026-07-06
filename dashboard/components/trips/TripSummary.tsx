import React from "react";
import { Trip, TripSummary as TripSummaryType } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatDate } from "../../lib/date";
import { Clock, Route, ShieldAlert, Award, AlertTriangle, Eye, ShieldCheck, MapPin } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

interface TripSummaryProps {
  trip: Trip;
  summary: TripSummaryType | null;
  loading: boolean;
}

export function TripSummary({ trip, summary, loading }: TripSummaryProps) {
  const formatDuration = (seconds: number): string => {
    if (seconds <= 0) return "0s";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    const parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (s > 0 || parts.length === 0) parts.push(`${s}s`);
    return parts.join(" ");
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return "text-emerald-400 border-emerald-500/20 bg-emerald-500/10";
    if (score >= 70) return "text-amber-400 border-amber-500/20 bg-amber-500/10";
    return "text-red-400 border-red-500/20 bg-red-500/10";
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <ShieldCheck className="h-6 w-6 text-emerald-400" />;
    if (score >= 70) return <Award className="h-6 w-6 text-amber-400" />;
    return <AlertTriangle className="h-6 w-6 text-red-400" />;
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        <Clock className="h-6 w-6 animate-spin mx-auto mb-2 text-cyan-400" />
        Calculating trip statistics...
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="p-8 text-center text-slate-400 text-sm">
        Failed to fetch summary data for this trip.
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left">
      {/* Overview Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Driving Score Card */}
        <div className={`border rounded-xl p-4 flex items-center gap-4 col-span-2 ${getScoreColor(summary.driving_score)}`}>
          <div className="h-12 w-12 rounded-full border border-current flex items-center justify-center shrink-0">
            {getScoreIcon(summary.driving_score)}
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider block opacity-75">
              Driving Behavior Score
            </span>
            <span className="text-3xl font-black font-mono leading-none tracking-tight">
              {summary.driving_score}/100
            </span>
          </div>
        </div>

        {/* Moving Time */}
        <div className="border border-[#1e294b]/60 bg-[#080d17]/40 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Moving Time
          </span>
          <span className="text-lg font-black text-white font-mono leading-none">
            {formatDuration(summary.moving_time)}
          </span>
          <span className="text-[10px] text-slate-400 block pt-1">
            Total Run: {formatDuration(summary.duration)}
          </span>
        </div>

        {/* Idle Time */}
        <div className="border border-[#1e294b]/60 bg-[#080d17]/40 rounded-xl p-4 flex flex-col gap-1">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Total Idle Time
          </span>
          <span className="text-lg font-black text-amber-400 font-mono leading-none">
            {formatDuration(summary.idle_time)}
          </span>
          <span className="text-[10px] text-slate-400 block pt-1">
            Stopped: {formatDuration(summary.duration - summary.moving_time)}
          </span>
        </div>
      </div>

      {/* Grid for Detailed metrics and event lists */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detailed Stats Column */}
        <div className="glass-panel border border-[#1e294b]/60 rounded-xl p-6 space-y-4 h-fit">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-[#1e294b]/40 pb-2">
            Trip Parameters
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Total Distance</span>
              <span className="text-white font-bold">{summary.distance.toFixed(2)} km</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Average Speed</span>
              <span className="text-white font-bold">{summary.average_speed.toFixed(1)} km/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Average Moving Speed</span>
              <span className="text-cyan-400 font-bold">{summary.average_moving_speed.toFixed(1)} km/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Maximum Speed</span>
              <span className="text-white font-bold">{summary.maximum_speed.toFixed(1)} km/h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">GPS Packet Count</span>
              <span className="text-white font-bold">{summary.packet_count} packets</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Average Packet Interval</span>
              <span className="text-white font-bold">{summary.average_packet_interval.toFixed(1)}s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Stop Events Detected</span>
              <span className="text-white font-bold">{summary.stop_count} stops</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Overspeeds Registered</span>
              <span className="text-red-400 font-bold">{summary.overspeed_count} alerts</span>
            </div>
          </div>
        </div>

        {/* Detected Stops Column */}
        <div className="glass-panel border border-[#1e294b]/60 rounded-xl p-6 lg:col-span-2 space-y-4 max-h-[300px] overflow-y-auto">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-[#1e294b]/40 pb-2 flex items-center gap-1.5">
            <MapPin className="h-4.5 w-4.5 text-cyan-400" />
            Detected Stop Events ({summary.stop_count})
          </h3>
          {summary.stops.length === 0 ? (
            <div className="text-slate-400 text-xs text-center py-12">
              No stop events detected (Speed remained stable or stop duration &lt; 120s)
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs py-2">Stop Time</TableHead>
                  <TableHead className="text-xs py-2">Duration</TableHead>
                  <TableHead className="text-xs py-2">Position</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summary.stops.map((stop, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="text-xs py-2">{formatDate(stop.start_time)}</TableCell>
                    <TableCell className="text-xs py-2 font-mono font-bold text-slate-200">
                      {formatDuration(stop.duration)}
                    </TableCell>
                    <TableCell className="text-xs py-2 font-mono text-[10px]">
                      {stop.latitude.toFixed(4)}, {stop.longitude.toFixed(4)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </div>

      {/* Overspeeds Logs */}
      {summary.overspeeds.length > 0 && (
        <div className="glass-panel border border-[#1e294b]/60 rounded-xl p-6 space-y-4 max-h-[300px] overflow-y-auto">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-[#1e294b]/40 pb-2 flex items-center gap-1.5">
            <ShieldAlert className="h-4.5 w-4.5 text-red-400" />
            Overspeed Alerts History ({summary.overspeed_count})
          </h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs py-2">Alert Time</TableHead>
                <TableHead className="text-xs py-2">Recorded Speed</TableHead>
                <TableHead className="text-xs py-2">Position</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {summary.overspeeds.map((ov, idx) => (
                <TableRow key={idx}>
                  <TableCell className="text-xs py-2">{formatDate(ov.timestamp)}</TableCell>
                  <TableCell className="text-xs py-2 font-mono font-bold text-red-400">
                    {ov.speed.toFixed(1)} km/h
                  </TableCell>
                  <TableCell className="text-xs py-2 font-mono text-[10px]">
                    {ov.latitude.toFixed(4)}, {ov.longitude.toFixed(4)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

import React from "react";
import { Route, Gauge, Zap, Pause, Play, RotateCcw } from "lucide-react";
import { VehicleTrackingSnapshot } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Metric } from "./VehicleBadges";
import { FleetTrackingMap } from "../fleet-tracking-map";
import { RouteStats } from "../../hooks/useVehicleDetailsPlayback";

interface RoutePlaybackTabProps {
  snapshot: VehicleTrackingSnapshot;
  activeSnapshot: VehicleTrackingSnapshot | null;
  playbackActive: boolean;
  setPlaybackActive: (active: boolean) => void;
  playbackIndex: number;
  setPlaybackIndex: (index: number) => void;
  routeStats: RouteStats;
}

export function RoutePlaybackTab({
  snapshot,
  activeSnapshot,
  playbackActive,
  setPlaybackActive,
  playbackIndex,
  setPlaybackIndex,
  routeStats,
}: RoutePlaybackTabProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Metric
          label="Distance Logged"
          value={`${routeStats.distance.toFixed(2)} km`}
          icon={<Route className="h-4 w-4 text-cyan-400" />}
        />
        <Metric
          label="Average Speed"
          value={`${routeStats.avgSpeed.toFixed(1)} km/h`}
          icon={<Gauge className="h-4 w-4 text-cyan-400" />}
        />
        <Metric
          label="Max Speed Captured"
          value={`${routeStats.maxSpeed.toFixed(1)} km/h`}
          icon={<Zap className="h-4 w-4 text-cyan-400" />}
        />
      </div>

      <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden p-5">
        <CardHeader className="p-0 pb-4 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white text-sm">Playback Map Controller</CardTitle>
          </div>
          {/* Playback Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPlaybackActive(!playbackActive)}
              className="bg-[#1b253b] hover:bg-[#253350] border border-[#1e294b]/60 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-200 flex items-center gap-1.5 transition-all"
            >
              {playbackActive ? (
                <Pause className="h-3.5 w-3.5 text-amber-400" />
              ) : (
                <Play className="h-3.5 w-3.5 text-emerald-400" />
              )}
              {playbackActive ? "Pause" : "Play"}
            </button>
            <button
              onClick={() => {
                setPlaybackActive(false);
                setPlaybackIndex(0);
              }}
              className="bg-[#1b253b] hover:bg-[#253350] border border-[#1e294b]/60 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-200 flex items-center gap-1.5 transition-all"
            >
              <RotateCcw className="h-3.5 w-3.5 text-cyan-400" />
              Reset
            </button>
          </div>
        </CardHeader>
        <CardContent className="p-0 space-y-4">
          {/* Scrub Slider */}
          {snapshot.route_history.length > 0 && (
            <div className="flex items-center gap-3 bg-[#0b0f19]/30 border border-[#1e294b]/20 p-3 rounded-lg">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider w-16 text-left shrink-0">
                Progress
              </span>
              <input
                type="range"
                min="0"
                max={snapshot.route_history.length - 1}
                value={playbackIndex}
                onChange={(e) => {
                  setPlaybackActive(false);
                  setPlaybackIndex(parseInt(e.target.value));
                }}
                className="flex-1 accent-cyan-400 cursor-pointer h-1.5 rounded-lg bg-[#1e294b]"
              />
              <span className="text-[10px] text-cyan-400 font-bold font-mono w-16 text-right shrink-0">
                {playbackIndex + 1} / {snapshot.route_history.length}
              </span>
            </div>
          )}

          {activeSnapshot && (
            <FleetTrackingMap
              snapshots={[activeSnapshot]}
              selectedVehicleId={snapshot.vehicle.id}
              visibleVehicleIds={[snapshot.vehicle.id]}
              heightClass="h-[480px]"
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

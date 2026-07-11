import { Crosshair, Expand, Layers, LocateFixed, Minimize, Eye, EyeOff, Navigation, RefreshCw, Radio } from "lucide-react";
import { Button } from "../ui/button";

interface MapControlsProps {
  layer: "street" | "satellite";
  fullscreen: boolean;
  selectedVehicleId: number | "all";
  onToggleLayer: () => void;
  onFitFleet: () => void;
  onZoomSelected: () => void;
  onToggleFullscreen: () => void;

  showPlannedRoute: boolean;
  onTogglePlannedRoute: () => void;
  showActualRoute: boolean;
  onToggleActualRoute: () => void;
  showTraffic: boolean;
  onToggleTraffic: () => void;
  followVehicle: boolean;
  onToggleFollow: () => void;
  onFitPlannedRoute: () => void;
  onResetView: () => void;
}

export function MapControls({
  layer,
  fullscreen,
  selectedVehicleId,
  onToggleLayer,
  onFitFleet,
  onZoomSelected,
  onToggleFullscreen,
  showPlannedRoute,
  onTogglePlannedRoute,
  showActualRoute,
  onToggleActualRoute,
  showTraffic,
  onToggleTraffic,
  followVehicle,
  onToggleFollow,
  onFitPlannedRoute,
  onResetView,
}: MapControlsProps) {
  return (
    <div className="absolute left-3 top-3 z-[500] flex flex-wrap gap-1.5 max-w-[95%] pointer-events-auto">
      {/* Map Type */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleLayer}
        className="bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60 text-[11px]"
        title="Toggle Map Layer"
      >
        <Layers className="mr-1 h-3.5 w-3.5 text-cyan-400" />
        {layer === "street" ? "Street" : "Satellite"}
      </Button>

      {/* Locate/Zoom Selected Vehicle */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onZoomSelected}
        disabled={selectedVehicleId === "all"}
        className="bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60 text-[11px] disabled:opacity-40"
        title="Locate Selected Vehicle"
      >
        <LocateFixed className="mr-1 h-3.5 w-3.5 text-cyan-400" />
        Locate
      </Button>

      {/* Fit Fleet */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onFitFleet}
        className="bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60 text-[11px]"
        title="Fit Fleet bounds"
      >
        <Crosshair className="mr-1 h-3.5 w-3.5 text-cyan-400" />
        Fit Fleet
      </Button>

      {/* Fit Planned Route */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onFitPlannedRoute}
        className="bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60 text-[11px]"
        title="Fit Planned Route bounds"
      >
        <Navigation className="mr-1 h-3.5 w-3.5 text-cyan-400 rotate-45" />
        Fit Route
      </Button>

      {/* Follow Vehicle Toggle */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleFollow}
        disabled={selectedVehicleId === "all"}
        className={`border text-[11px] disabled:opacity-40 transition-all ${
          followVehicle && selectedVehicleId !== "all"
            ? "bg-cyan-600 hover:bg-cyan-500 text-white border-cyan-500"
            : "bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border-[#1e294b]/60"
        }`}
        title="Follow Vehicle mode"
      >
        <Radio className={`mr-1 h-3.5 w-3.5 ${followVehicle && selectedVehicleId !== "all" ? "text-white animate-pulse" : "text-cyan-400"}`} />
        {followVehicle && selectedVehicleId !== "all" ? "Following" : "Follow"}
      </Button>

      {/* Reset View */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onResetView}
        className="bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60 text-[11px]"
        title="Reset Map View"
      >
        <RefreshCw className="mr-1 h-3.5 w-3.5 text-cyan-400" />
        Reset View
      </Button>

      {/* Toggle Planned Route */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onTogglePlannedRoute}
        className={`border text-[11px] ${
          showPlannedRoute
            ? "bg-[#1e294b]/60 text-white border-cyan-500/40"
            : "bg-[#131a2d]/40 text-slate-400 border-transparent"
        }`}
        title="Toggle Planned Route Polyline"
      >
        {showPlannedRoute ? <Eye className="mr-1 h-3.5 w-3.5 text-cyan-400" /> : <EyeOff className="mr-1 h-3.5 w-3.5 text-slate-500" />}
        Planned Route
      </Button>

      {/* Toggle Actual Route */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleActualRoute}
        className={`border text-[11px] ${
          showActualRoute
            ? "bg-[#1e294b]/60 text-white border-cyan-500/40"
            : "bg-[#131a2d]/40 text-slate-400 border-transparent"
        }`}
        title="Toggle Actual Driven Path Polyline"
      >
        {showActualRoute ? <Eye className="mr-1 h-3.5 w-3.5 text-emerald-400" /> : <EyeOff className="mr-1 h-3.5 w-3.5 text-slate-500" />}
        Actual Path
      </Button>

      {/* Traffic Toggle */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleTraffic}
        className={`border text-[11px] ${
          showTraffic
            ? "bg-[#1e294b]/60 text-white border-rose-500/40"
            : "bg-[#131a2d]/40 text-slate-400 border-transparent"
        }`}
        title="Toggle Real-time Traffic (Future Ready)"
      >
        <Layers className={`mr-1 h-3.5 w-3.5 ${showTraffic ? "text-rose-400" : "text-slate-500"}`} />
        Traffic
      </Button>

      {/* Fullscreen */}
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleFullscreen}
        className="bg-[#131a2d]/90 hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60"
        title="Toggle Fullscreen"
      >
        {fullscreen ? <Minimize className="h-3.5 w-3.5 text-cyan-400" /> : <Expand className="h-3.5 w-3.5 text-cyan-400" />}
      </Button>
    </div>
  );
}

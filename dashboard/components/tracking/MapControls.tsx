import { Crosshair, Expand, Layers, LocateFixed, Minimize } from "lucide-react";
import { Button } from "../ui/button";

interface MapControlsProps {
  layer: "street" | "satellite";
  fullscreen: boolean;
  selectedVehicleId: number | "all";
  onToggleLayer: () => void;
  onFitFleet: () => void;
  onZoomSelected: () => void;
  onToggleFullscreen: () => void;
}

export function MapControls({
  layer,
  fullscreen,
  selectedVehicleId,
  onToggleLayer,
  onFitFleet,
  onZoomSelected,
  onToggleFullscreen,
}: MapControlsProps) {
  return (
    <div className="absolute left-3 top-3 z-[500] flex flex-wrap gap-2 pointer-events-auto">
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleLayer}
        className="bg-[#131a2d] hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60"
        title="Toggle Map Layer"
      >
        <Layers className="mr-1.5 h-3.5 w-3.5 text-cyan-400" />
        {layer === "street" ? "Street" : "Satellite"}
      </Button>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onFitFleet}
        className="bg-[#131a2d] hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60"
        title="Fit Fleet bounds"
      >
        <Crosshair className="mr-1.5 h-3.5 w-3.5 text-cyan-400" />
        Fit Fleet
      </Button>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onZoomSelected}
        disabled={selectedVehicleId === "all"}
        className="bg-[#131a2d] hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60 disabled:opacity-50"
        title="Zoom to Selected"
      >
        <LocateFixed className="mr-1.5 h-3.5 w-3.5 text-cyan-400" />
        Zoom
      </Button>
      <Button
        type="button"
        size="sm"
        variant="secondary"
        onClick={onToggleFullscreen}
        className="bg-[#131a2d] hover:bg-[#1e294b] text-slate-200 border border-[#1e294b]/60"
        title="Toggle Fullscreen"
      >
        {fullscreen ? <Minimize className="h-3.5 w-3.5 text-cyan-400" /> : <Expand className="h-3.5 w-3.5 text-cyan-400" />}
      </Button>
    </div>
  );
}

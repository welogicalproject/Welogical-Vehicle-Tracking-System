import { FleetTrackingMap } from "../fleet-tracking-map";
import { VehicleTrackingSnapshot } from "../../types";

interface FleetMapProps {
  snapshots: VehicleTrackingSnapshot[];
  selectedVehicleId: number | "all";
  visibleVehicleIds: number[];
  onSelectVehicle: (id: number | "all") => void;
  plannedRoute?: {lat: number, lng: number}[];
  onMapClick?: (lat: number, lng: number) => void;
}

export function FleetMap({
  snapshots,
  selectedVehicleId,
  visibleVehicleIds,
  onSelectVehicle,
  plannedRoute,
  onMapClick,
}: FleetMapProps) {
  return (
    <FleetTrackingMap
      snapshots={snapshots}
      selectedVehicleId={selectedVehicleId}
      visibleVehicleIds={visibleVehicleIds}
      onSelectVehicle={onSelectVehicle}
      plannedRoute={plannedRoute}
      onMapClick={onMapClick}
    />
  );
}

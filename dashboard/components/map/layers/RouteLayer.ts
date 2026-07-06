"use client";

import { IMapLayer } from "../engine/types";
import { getVehicleColor } from "../../../utils/trackingMap";

export class RouteLayer implements IMapLayer {
  id = "RouteLayer";
  private map: any = null;
  private adapter: any = null;
  private polylines: Map<number, any> = new Map(); // vehicle_id -> google.maps.Polyline

  constructor(adapter: any) {
    this.adapter = adapter;
    this.map = adapter.getRawMap();
  }

  show(): void {
    if (!this.map) return;
    this.polylines.forEach((p) => p.setMap(this.map));
  }

  hide(): void {
    this.polylines.forEach((p) => p.setMap(null));
  }

  refresh(payload?: { snapshots: any[]; visibleIds: number[]; selectedId: number | "all"; colorOverride?: string }): void {
    if (!this.map || typeof window === "undefined" || !payload) return;
    if (typeof google === "undefined" || !google.maps) return;

    const { snapshots, visibleIds, selectedId, colorOverride } = payload;
    const visibleSet = new Set(visibleIds);

    const currentSnapshotIds = new Set(snapshots.map((s) => s.vehicle.id));

    // 1. Clean up unused polylines
    this.polylines.forEach((polyline, id) => {
      if (!currentSnapshotIds.has(id)) {
        polyline.setMap(null);
        google.maps.event.clearInstanceListeners(polyline);
        this.polylines.delete(id);
      }
    });

    // 2. Add or update polylines in place
    snapshots.forEach((snapshot, index) => {
      const vehicleId = snapshot.vehicle.id;
      const history = snapshot.route_history || [];
      const isVisible = visibleSet.has(vehicleId) && (selectedId === "all" || selectedId === vehicleId);
      const isFocused = selectedId === "all" || selectedId === vehicleId;
      const color = colorOverride || getVehicleColor(index);

      let polyline = this.polylines.get(vehicleId);
      if (!polyline) {
        polyline = new google.maps.Polyline({
          strokeOpacity: 0.8,
          map: isVisible ? this.map : null
        });
        this.polylines.set(vehicleId, polyline);
      }

      // Convert coordinates list
      const path = history.map((pt: any) => ({ lat: pt.latitude, lng: pt.longitude }));

      polyline.setPath(path);
      polyline.setOptions({
        strokeColor: color,
        strokeWeight: isFocused ? 4 : 2,
        strokeOpacity: isFocused ? 0.85 : 0.25,
        map: isVisible ? this.map : null
      });
    });
  }

  destroy(): void {
    this.hide();
    if (typeof google !== "undefined" && google.maps && google.maps.event) {
      this.polylines.forEach((p) => {
        google.maps.event.clearInstanceListeners(p);
      });
    }
    this.polylines.clear();
    this.map = null;
    this.adapter = null;
  }
}

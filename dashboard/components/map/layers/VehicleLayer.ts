"use client";

import { IMapLayer } from "../engine/types";
import { getVehicleColor } from "../../../utils/trackingMap";

export class VehicleLayer implements IMapLayer {
  id = "VehicleLayer";
  private map: any = null;
  private adapter: any = null;
  private markers: Map<number, any> = new Map(); // vehicle_id -> google.maps.Marker
  private headingMarkers: Map<number, any> = new Map(); // vehicle_id -> google.maps.Marker for heading arrow
  private snapshotMap: Map<number, any> = new Map(); // vehicle_id -> latest snapshot reference
  private snapshots: any[] = [];
  private visibleIds: Set<number> = new Set();
  private selectedId: number | "all" = "all";

  constructor(adapter: any) {
    this.adapter = adapter;
    this.map = adapter.getRawMap();
  }

  show(): void {
    if (!this.map) return;
    this.markers.forEach((m) => m.setMap(this.map));
    this.headingMarkers.forEach((m) => m.setMap(this.map));
  }

  hide(): void {
    this.markers.forEach((m) => m.setMap(null));
    this.headingMarkers.forEach((m) => m.setMap(null));
  }

  refresh(payload?: { snapshots: any[]; visibleIds: number[]; selectedId: number | "all" }): void {
    if (!this.map || typeof window === "undefined" || !payload) return;
    const google = (window as any).google;
    if (!google || !google.maps) return;

    const { snapshots, visibleIds, selectedId } = payload;
    this.snapshots = snapshots;
    this.visibleIds = new Set(visibleIds);
    this.selectedId = selectedId;

    const currentSnapshotIds = new Set(snapshots.map((s) => s.vehicle.id));

    // 1. Clean up markers for vehicles no longer present
    this.markers.forEach((marker, id) => {
      if (!currentSnapshotIds.has(id)) {
        marker.setMap(null);
        google.maps.event.clearInstanceListeners(marker);
        this.markers.delete(id);
        this.snapshotMap.delete(id);
      }
    });
    this.headingMarkers.forEach((marker, id) => {
      if (!currentSnapshotIds.has(id)) {
        marker.setMap(null);
        google.maps.event.clearInstanceListeners(marker);
        this.headingMarkers.delete(id);
      }
    });

    // 2. Add or update markers in place
    snapshots.forEach((snapshot, index) => {
      const vehicleId = snapshot.vehicle.id;
      const latest = snapshot.latest_location;
      
      if (!latest) return;

      // Keep snapshot map reference updated for event listeners to avoid stale closure references
      this.snapshotMap.set(vehicleId, snapshot);

      const position = { lat: latest.latitude, lng: latest.longitude };
      const isVisible = this.visibleIds.has(vehicleId) && (selectedId === "all" || selectedId === vehicleId);
      const isFocused = selectedId === "all" || selectedId === vehicleId;
      const color = getVehicleColor(index);

      // Re-use or create base marker
      let marker = this.markers.get(vehicleId);
      if (!marker) {
        marker = new google.maps.Marker({
          map: isVisible ? this.map : null,
          title: snapshot.vehicle.vehicle_name,
          zIndex: 100
        });

        // Event dispatching looks up current snapshot dynamically to avoid stale closures
        marker.addListener("click", () => {
          const currentSnapshot = this.snapshotMap.get(vehicleId);
          if (currentSnapshot) {
            this.adapter.getEventBus().emit("MarkerClicked", currentSnapshot);
          }
        });

        this.markers.set(vehicleId, marker);
      }

      // Re-use or create heading arrow marker
      let headingMarker = this.headingMarkers.get(vehicleId);
      if (!headingMarker) {
        headingMarker = new google.maps.Marker({
          map: isVisible ? this.map : null,
          clickable: false,
          zIndex: 101
        });
        this.headingMarkers.set(vehicleId, headingMarker);
      }

      // Setup icons
      // Base circle
      const baseIcon = {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 7,
        fillColor: color,
        fillOpacity: isFocused ? 1.0 : 0.35,
        strokeColor: "#ffffff",
        strokeWeight: 1.5
      };

      // Triangle heading arrow
      const heading = this.getHeading(snapshot);
      const headingIcon = {
        path: "M 0,-6 L 4,3 L -4,3 Z",
        scale: 1,
        fillColor: color,
        fillOpacity: isFocused ? 1.0 : 0.35,
        strokeColor: "#ffffff",
        strokeWeight: 0.75,
        rotation: heading
      };

      // Set positions and visibility
      marker.setPosition(position);
      marker.setIcon(baseIcon);
      marker.setMap(isVisible ? this.map : null);

      headingMarker.setPosition(position);
      headingMarker.setIcon(headingIcon);
      headingMarker.setMap(isVisible ? this.map : null);
    });
  }

  private getHeading(snapshot: any): number {
    const latest = snapshot.latest_location;
    if (!latest) return 0;
    const fromGps = latest.extra_data?.gps?.dir ?? latest.extra_data?.gps_details?.dir;
    if (typeof fromGps === "number") return fromGps;

    const trail = snapshot.route_history || [];
    if (trail.length < 2) return 0;
    const a = trail[trail.length - 2];
    const b = trail[trail.length - 1];
    return (Math.atan2(b.longitude - a.longitude, b.latitude - a.latitude) * 180) / Math.PI;
  }

  destroy(): void {
    this.hide();
    
    // Clear Google Maps event listeners to prevent memory leaks
    this.markers.forEach((marker) => {
      google.maps.event.clearInstanceListeners(marker);
    });
    this.markers.clear();

    this.headingMarkers.forEach((marker) => {
      google.maps.event.clearInstanceListeners(marker);
    });
    this.headingMarkers.clear();

    this.snapshotMap.clear();
    this.map = null;
    this.adapter = null;
  }
}

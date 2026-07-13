"use client";

import { IMapLayer } from "../engine/types";

export class PlannedRouteLayer implements IMapLayer {
  id = "PlannedRouteLayer";
  private map: any = null;
  private adapter: any = null;
  private polyline: any = null;

  constructor(adapter: any) {
    this.adapter = adapter;
    this.map = adapter.getRawMap();
  }

  show(): void {
    if (this.polyline) {
      this.polyline.setMap(this.map);
    }
  }

  hide(): void {
    if (this.polyline) {
      this.polyline.setMap(null);
    }
  }

  refresh(payload?: { coordinates: {lat: number, lng: number}[]; visible: boolean }): void {
    if (!this.map || typeof window === "undefined" || !payload) return;
    if (typeof google === "undefined" || !google.maps) return;

    const { coordinates, visible } = payload;

    if (!this.polyline) {
      this.polyline = new google.maps.Polyline({
        strokeColor: "#3b82f6", // Blue
        strokeOpacity: 0.85,
        strokeWeight: 4,
        zIndex: 50, // Make it appear below markers but clearly visible
      } as any);
    }

    if (visible && coordinates && coordinates.length > 0) {
      this.polyline.setPath(coordinates);
      this.polyline.setMap(this.map);
    } else {
      this.polyline.setMap(null);
    }
  }

  destroy(): void {
    if (this.polyline) {
      this.polyline.setMap(null);
      if (typeof google !== "undefined" && google.maps && google.maps.event) {
        google.maps.event.clearInstanceListeners(this.polyline);
      }
      this.polyline = null;
    }
    this.map = null;
    this.adapter = null;
  }
}

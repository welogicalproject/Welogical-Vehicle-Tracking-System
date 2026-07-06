"use client";

import { IMapLayer } from "../engine/types";

export class GoogleRouteLayer implements IMapLayer {
  id = "GoogleRouteLayer";
  private map: any = null;
  private adapter: any = null;
  private polyline: any = null; // google.maps.Polyline reference

  constructor(adapter: any) {
    this.adapter = adapter;
    this.map = adapter.getRawMap();
  }

  show(): void {
    if (this.polyline && this.map) {
      this.polyline.setMap(this.map);
    }
  }

  hide(): void {
    if (this.polyline) {
      this.polyline.setMap(null);
    }
  }

  refresh(payload?: { encodedPolyline?: string; visible?: boolean }): void {
    if (!this.map || typeof window === "undefined" || !payload) return;
    if (typeof google === "undefined" || !google.maps || !google.maps.geometry || !google.maps.geometry.encoding) {
      console.warn("Google Maps geometry library not loaded when rendering GoogleRouteLayer");
      return;
    }

    const { encodedPolyline, visible = true } = payload;

    // Remove existing polyline from map
    if (this.polyline) {
      this.polyline.setMap(null);
      google.maps.event.clearInstanceListeners(this.polyline);
      this.polyline = null;
    }

    if (!encodedPolyline) return;

    try {
      const decodedPath = google.maps.geometry.encoding.decodePath(encodedPolyline);
      
      // Render solid green snapped polyline on Google Maps
      this.polyline = new google.maps.Polyline({
        path: decodedPath,
        strokeColor: "#10b981", // Green (#10b981)
        strokeWeight: 4,
        strokeOpacity: 0.8,
        map: visible ? this.map : null
      });
    } catch (e) {
      console.error("Failed to decode and draw Google snapped polyline:", e);
    }
  }

  destroy(): void {
    this.hide();
    if (this.polyline) {
      if (typeof google !== "undefined" && google.maps && google.maps.event) {
        google.maps.event.clearInstanceListeners(this.polyline);
      }
      this.polyline = null;
    }
    this.map = null;
    this.adapter = null;
  }
}

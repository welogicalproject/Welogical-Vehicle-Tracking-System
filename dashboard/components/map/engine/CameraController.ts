"use client";

import { ICameraController, CameraMode, MapLatLng } from "./types";

export class CameraController implements ICameraController {
  private map: any = null; // google.maps.Map instance
  private mode: CameraMode = "Manual";

  constructor(mapInstance?: any) {
    if (mapInstance) {
      this.map = mapInstance;
    }
  }

  setMapInstance(mapInstance: any) {
    this.map = mapInstance;
  }

  setMode(mode: CameraMode): void {
    this.mode = mode;
  }

  getMode(): CameraMode {
    return this.mode;
  }

  fitBounds(bounds: MapLatLng[]): void {
    if (!this.map || typeof window === "undefined" || !bounds || bounds.length === 0) return;
    const google = (window as any).google;
    if (!google || !google.maps) return;

    const gBounds = new google.maps.LatLngBounds();
    bounds.forEach((coord) => {
      gBounds.extend(coord);
    });
    
    this.map.fitBounds(gBounds);
  }

  panTo(coord: MapLatLng): void {
    if (!this.map) return;
    this.map.panTo(coord);
  }

  setZoom(zoom: number): void {
    if (!this.map) return;
    this.map.setZoom(zoom);
  }

  getZoom(): number {
    return this.map ? this.map.getZoom() || 0 : 0;
  }

  destroy(): void {
    this.map = null;
  }
}

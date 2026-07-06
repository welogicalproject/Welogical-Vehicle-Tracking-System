"use client";

import { IMapLayer, MapLatLng } from "../engine/types";

export class SelectionLayer implements IMapLayer {
  id = "SelectionLayer";
  private map: any = null;
  private adapter: any = null;
  private ring: any = null;

  constructor(adapter: any) {
    this.adapter = adapter;
    this.map = adapter.getRawMap();
  }

  show(): void {
    if (this.ring && this.map) this.ring.setMap(this.map);
  }

  hide(): void {
    if (this.ring) this.ring.setMap(null);
  }

  refresh(payload?: { selectedCoord: MapLatLng | null }): void {
    if (!this.map || typeof window === "undefined" || !payload) return;
    const google = (window as any).google;
    if (!google || !google.maps) return;

    const { selectedCoord } = payload;

    if (!selectedCoord) {
      if (this.ring) this.ring.setMap(null);
      return;
    }

    if (!this.ring) {
      this.ring = new google.maps.Marker({
        map: this.map,
        clickable: false
      });
    }

    this.ring.setPosition(selectedCoord);
    this.ring.setIcon({
      path: google.maps.SymbolPath.CIRCLE,
      scale: 16,
      fillColor: "#22d3ee",
      fillOpacity: 0.15,
      strokeColor: "#22d3ee",
      strokeWeight: 2,
      strokeOpacity: 0.8
    });
    this.ring.setMap(this.map);
  }

  destroy(): void {
    this.hide();
    if (this.ring) {
      google.maps.event.clearInstanceListeners(this.ring);
      this.ring.setMap(null);
    }
    this.ring = null;
    this.map = null;
    this.adapter = null;
  }
}

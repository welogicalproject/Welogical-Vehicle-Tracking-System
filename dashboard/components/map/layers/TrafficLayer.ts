"use client";

import { IMapLayer } from "../engine/types";

export class TrafficLayer implements IMapLayer {
  id = "TrafficLayer";
  private map: any = null;
  private adapter: any = null;
  private gTrafficLayer: any = null;
  private visible = false;

  constructor(adapter: any) {
    this.adapter = adapter;
    this.map = adapter.getRawMap();
  }

  show(): void {
    if (!this.map || typeof window === "undefined") return;
    const google = (window as any).google;
    if (!google || !google.maps) return;

    if (!this.gTrafficLayer) {
      this.gTrafficLayer = new google.maps.TrafficLayer();
    }
    this.gTrafficLayer.setMap(this.map);
    this.visible = true;
  }

  hide(): void {
    if (this.gTrafficLayer) {
      this.gTrafficLayer.setMap(null);
    }
    this.visible = false;
  }

  refresh(payload?: any): void {
    if (this.visible) {
      this.show();
    } else {
      this.hide();
    }
  }

  destroy(): void {
    this.hide();
    if (this.gTrafficLayer) {
      google.maps.event.clearInstanceListeners(this.gTrafficLayer);
    }
    this.gTrafficLayer = null;
    this.map = null;
    this.adapter = null;
  }
}

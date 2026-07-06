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
      // Create a dashed purple line to look distinct
      const lineSymbol = {
        path: "M 0,-1 0,1",
        strokeOpacity: 1,
        scale: 4,
      };

      this.polyline = new google.maps.Polyline({
        strokeColor: "#9333ea", // Purple
        strokeOpacity: 0,
        icons: [
          {
            icon: lineSymbol,
            offset: "0",
            repeat: "20px",
          },
        ],
        zIndex: 100, // Make it appear above other routes
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
      google.maps.event.clearInstanceListeners(this.polyline);
      this.polyline = null;
    }
  }
}

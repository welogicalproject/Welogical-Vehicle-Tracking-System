"use client";

import { IOverlayManager, MapLatLng } from "./types";

export class OverlayManager implements IOverlayManager {
  private map: any = null; // google.maps.Map instance
  private activeInfoWindow: any = null; // google.maps.InfoWindow instance

  constructor(mapInstance?: any) {
    if (mapInstance) {
      this.map = mapInstance;
    }
  }

  setMapInstance(mapInstance: any) {
    this.map = mapInstance;
    this.destroyInfoWindow();
  }

  private destroyInfoWindow() {
    if (this.activeInfoWindow) {
      try {
        if (typeof window !== "undefined") {
          const google = (window as any).google;
          if (google && google.maps && google.maps.event) {
            google.maps.event.clearInstanceListeners(this.activeInfoWindow);
          }
        }
        this.activeInfoWindow.close();
      } catch (e) {
        // Ignored
      }
      this.activeInfoWindow = null;
    }
  }

  showPopup(anchorCoord: MapLatLng, contentHtml: string | HTMLElement, onClose?: () => void): void {
    if (!this.map || typeof window === "undefined") return;
    const google = (window as any).google;
    if (!google || !google.maps) return;

    this.destroyInfoWindow();

    // Configure info window parameters
    this.activeInfoWindow = new google.maps.InfoWindow({
      content: contentHtml,
      position: anchorCoord,
      // Lift window above markers
      pixelOffset: new google.maps.Size(0, -10)
    });

    if (onClose) {
      this.activeInfoWindow.addListener("closeclick", () => {
        onClose();
      });
    }

    this.activeInfoWindow.open({
      map: this.map,
      shouldFocus: false
    });
  }

  hidePopup(): void {
    this.destroyInfoWindow();
  }

  destroy(): void {
    this.destroyInfoWindow();
    this.map = null;
  }
}

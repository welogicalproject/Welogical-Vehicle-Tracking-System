"use client";

import { IMapEngine, IEventBus, ILayerManager, ICameraController, IOverlayManager } from "../types";
import { EventBus } from "../EventBus";
import { LayerManager } from "../LayerManager";
import { CameraController } from "../CameraController";
import { OverlayManager } from "../OverlayManager";
import { GOOGLE_MAPS_DARK_THEME } from "../../styles/darkTheme";

export class GoogleMapsAdapter implements IMapEngine {
  private map: any = null; // google.maps.Map instance
  private eventBus: IEventBus;
  private layerManager: ILayerManager;
  private cameraController: CameraController;
  private overlayManager: OverlayManager;
  private mapListeners: any[] = [];
  private ready = false;

  constructor() {
    this.eventBus = new EventBus();
    this.layerManager = new LayerManager();
    this.cameraController = new CameraController();
    this.overlayManager = new OverlayManager();
  }

  initialize(container: HTMLDivElement, options?: any): void {
    if (typeof window === "undefined") return;
    const google = (window as any).google;
    if (!google || !google.maps) {
      console.error("Google Maps SDK not loaded when initializing GoogleMapsAdapter");
      return;
    }

    const mapOptions: any = {
      zoom: options?.zoom || 7,
      center: options?.center || { lat: 22.3072, lng: 73.1812 },
      disableDefaultUI: options?.isMiniMap ? true : false,
      zoomControl: options?.isMiniMap ? false : true,
      zoomControlOptions: {
        position: google.maps.ControlPosition.RIGHT_BOTTOM
      },
      styles: GOOGLE_MAPS_DARK_THEME,
      mapTypeId: options?.mapTypeId || google.maps.MapTypeId.ROADMAP,
      ...options
    };

    this.map = new google.maps.Map(container, mapOptions);
    this.ready = true;

    // Inject active map instance to sub-managers
    this.cameraController.setMapInstance(this.map);
    this.overlayManager.setMapInstance(this.map);

    // Bind basic map events to event bus and track them for cleanup
    this.mapListeners.push(
      this.map.addListener("click", () => {
        this.overlayManager.hidePopup();
        this.eventBus.emit("CameraChanged");
      })
    );
    this.mapListeners.push(
      this.map.addListener("bounds_changed", () => {
        this.eventBus.emit("CameraChanged");
      })
    );
  }

  setMapType(type: "street" | "satellite"): void {
    if (!this.map || typeof window === "undefined") return;
    const google = (window as any).google;
    const mapType = type === "satellite" ? google.maps.MapTypeId.SATELLITE : google.maps.MapTypeId.ROADMAP;
    this.map.setOptions({
      mapTypeId: mapType,
      styles: type === "street" ? GOOGLE_MAPS_DARK_THEME : []
    });
  }

  getEventBus(): IEventBus {
    return this.eventBus;
  }

  getLayerManager(): ILayerManager {
    return this.layerManager;
  }

  getCameraController(): ICameraController {
    return this.cameraController;
  }

  getOverlayManager(): IOverlayManager {
    return this.overlayManager;
  }

  isReady(): boolean {
    return this.ready && this.map !== null;
  }

  // Helper to fetch raw map object within adapters layer
  getRawMap(): any {
    return this.map;
  }

  onMapClick(callback: (lat: number, lng: number) => void): void {
    if (!this.map) return;
    const listener = this.map.addListener("click", (e: any) => {
      if (e.latLng) {
        callback(e.latLng.lat(), e.latLng.lng());
      }
    });
    this.mapListeners.push(listener);
  }

  destroy(): void {
    // Unsubscribe map event listeners to prevent memory leaks
    this.mapListeners.forEach((listener) => {
      if (listener && typeof listener.remove === "function") {
        listener.remove();
      }
    });
    this.mapListeners = [];

    if (this.map && typeof window !== "undefined") {
      const google = (window as any).google;
      if (google && google.maps && google.maps.event) {
        google.maps.event.clearInstanceListeners(this.map);
      }
    }

    this.eventBus.destroy();
    this.layerManager.destroy();
    this.cameraController.destroy();
    this.overlayManager.destroy();
    this.map = null;
    this.ready = false;
  }
}

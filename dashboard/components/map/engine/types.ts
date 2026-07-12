"use client";

// General coordinate model
export interface MapLatLng {
  lat: number;
  lng: number;
}

// System events fired inside the internal EventBus
export type MapEventType =
  | "MarkerClicked"
  | "CameraChanged";

export type MapEventCallback = (payload?: any) => void;

export interface IEventBus {
  on(event: MapEventType, callback: MapEventCallback): void;
  off(event: MapEventType, callback: MapEventCallback): void;
  emit(event: MapEventType, payload?: any): void;
  destroy(): void;
}

// Layer control interfaces
export interface IMapLayer {
  id: string;
  show(): void;
  hide(): void;
  refresh(payload?: any): void;
  destroy(): void;
}

export interface ILayerManager {
  registerLayer(layer: IMapLayer): void;
  showLayer(layerId: string): void;
  hideLayer(layerId: string): void;
  refreshLayer(layerId: string, payload?: any): void;
  destroy(): void;
}

// Camera Modes and controllers
export type CameraMode = "FitFleet" | "FollowVehicle" | "FollowReplay" | "FitBounds" | "Manual" | "Reset";

export interface ICameraController {
  setMode(mode: CameraMode): void;
  getMode(): CameraMode;
  fitBounds(bounds: MapLatLng[]): void;
  panTo(coord: MapLatLng): void;
  setZoom(zoom: number): void;
  getZoom(): number;
  destroy(): void;
}

// Overlay (Popup, InfoWindow) manager interfaces
export interface IOverlayManager {
  showPopup(anchorCoord: MapLatLng, contentHtml: string | HTMLElement, onClose?: () => void): void;
  hidePopup(): void;
  destroy(): void;
}

// Core Map Engine interfaces
export interface IMapEngine {
  initialize(container: HTMLDivElement, options?: any): void;
  setMapType(type: "street" | "satellite"): void;
  getEventBus(): IEventBus;
  getLayerManager(): ILayerManager;
  getCameraController(): ICameraController;
  getOverlayManager(): IOverlayManager;
  isReady(): boolean;
  getRawMap(): any;
  destroy(): void;
}

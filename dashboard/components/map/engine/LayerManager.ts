"use client";

import { ILayerManager, IMapLayer } from "./types";

export class LayerManager implements ILayerManager {
  private layers: Map<string, IMapLayer> = new Map();
  private activeLayers: Set<string> = new Set();

  registerLayer(layer: IMapLayer): void {
    if (this.layers.has(layer.id)) {
      console.warn(`Layer with ID ${layer.id} is already registered. Overwriting.`);
      // Clean up previous layer if any
      this.layers.get(layer.id)!.destroy();
    }
    this.layers.set(layer.id, layer);
  }

  showLayer(layerId: string): void {
    const layer = this.layers.get(layerId);
    if (layer) {
      layer.show();
      this.activeLayers.add(layerId);
    } else {
      console.warn(`Layer with ID ${layerId} not found.`);
    }
  }

  hideLayer(layerId: string): void {
    const layer = this.layers.get(layerId);
    if (layer) {
      layer.hide();
      this.activeLayers.delete(layerId);
    }
  }

  refreshLayer(layerId: string, payload?: any): void {
    const layer = this.layers.get(layerId);
    if (layer) {
      layer.refresh(payload);
    }
  }

  destroy(): void {
    this.layers.forEach((layer) => {
      try {
        layer.destroy();
      } catch (e) {
        console.error(`Error destroying layer ${layer.id}:`, e);
      }
    });
    this.layers.clear();
    this.activeLayers.clear();
  }
}

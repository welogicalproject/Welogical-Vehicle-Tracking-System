"use client";

import { IEventBus, MapEventType, MapEventCallback } from "./types";

export class EventBus implements IEventBus {
  private listeners: Map<MapEventType, Set<MapEventCallback>> = new Map();

  on(event: MapEventType, callback: MapEventCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: MapEventType, callback: MapEventCallback): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.listeners.delete(event);
      }
    }
  }

  emit(event: MapEventType, payload?: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      // Run on next tick to prevent synchronous recursion blocks
      callbacks.forEach((cb) => {
        try {
          cb(payload);
        } catch (e) {
          console.error(`Error in event callback for event ${event}:`, e);
        }
      });
    }
  }

  destroy(): void {
    this.listeners.clear();
  }
}

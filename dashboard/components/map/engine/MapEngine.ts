"use client";

import { IMapEngine } from "./types";
import { GoogleMapsAdapter } from "./adapters/GoogleMapsAdapter";

export class MapEngine {
  static createEngine(vendor: "google" = "google"): IMapEngine {
    if (vendor === "google") {
      return new GoogleMapsAdapter();
    }
    throw new Error(`Unsupported map vendor: ${vendor}`);
  }
}

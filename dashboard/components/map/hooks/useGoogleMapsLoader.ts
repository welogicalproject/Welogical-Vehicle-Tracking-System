"use client";

import { useEffect, useState } from "react";

let globalLoadPromise: Promise<void> | null = null;

export function useGoogleMapsLoader() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Check if namespace already exists
    if ((window as any).google && (window as any).google.maps) {
      setIsLoaded(true);
      return;
    }

    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";
    console.log("Google Maps API Key:", apiKey);
    if (!apiKey) {
      setError("Google Maps API Key is missing. Please define NEXT_PUBLIC_GOOGLE_MAPS_API_KEY.");
      return;
    }

    // Reuse load promise across mounts
    if (!globalLoadPromise) {
      globalLoadPromise = new Promise<void>((resolve, reject) => {
        const scriptId = "google-maps-api-script";
        const existingScript = document.getElementById(scriptId);
        if (existingScript) {
          resolve();
          return;
        }

        const script = document.createElement("script");
        script.id = scriptId;
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry,marker,places`;
        script.async = true;
        script.defer = true;

        script.onload = () => {
          if ((window as any).google && (window as any).google.maps) {
            resolve();
          } else {
            reject(new Error("google.maps namespace is not defined after script load"));
          }
        };

        script.onerror = () => {
          reject(new Error("Failed to load Google Maps SDK script"));
        };

        document.head.appendChild(script);
      });
    }

    globalLoadPromise
      .then(() => {
        setIsLoaded(true);
      })
      .catch((err) => {
        console.error("Google Maps loader failed:", err);
        setError(err.message || "Failed to load Google Maps script");
        // Reset promise on failure so that retries can happen
        globalLoadPromise = null;
      });
  }, []);

  return { isLoaded, error };
}

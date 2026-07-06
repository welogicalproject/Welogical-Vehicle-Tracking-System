import { useEffect, useMemo, useRef, useState } from "react";
import { VehicleTrackingSnapshot } from "../types";
import { haversineKm } from "../utils/geo";

export interface RouteStats {
  distance: number;
  avgSpeed: number;
  maxSpeed: number;
}

export function useVehicleDetailsPlayback(snapshot: VehicleTrackingSnapshot | null) {
  const [playbackActive, setPlaybackActive] = useState(false);
  const [playbackIndex, setPlaybackIndex] = useState(0);

  // Hold the current route length in a ref so the interval callback
  // does NOT capture `snapshot` as a dependency.
  // Without this, any 10-second data refresh creates a new `snapshot`
  // object reference, which restarts the interval every 10 seconds —
  // causing the visible jerk/freeze during playback.
  const routeLengthRef = useRef(0);

  useEffect(() => {
    routeLengthRef.current = snapshot?.route_history?.length ?? 0;
  }, [snapshot]);

  // Handle playback ticker
  useEffect(() => {
    if (!playbackActive) return;

    const timer = setInterval(() => {
      setPlaybackIndex((prev) => {
        // Read length from ref, NOT from snapshot closure
        const totalPoints = routeLengthRef.current;
        if (totalPoints === 0 || prev >= totalPoints - 1) {
          setPlaybackActive(false);
          return prev;
        }
        return prev + 1;
      });
    }, 350);

    return () => {
      clearInterval(timer);
    };
    // Only depends on playbackActive — snapshot changes do NOT restart the timer
  }, [playbackActive]);

  // Playback snapshot mapper
  const activeSnapshot = useMemo(() => {
    if (!snapshot) return null;

    const history = snapshot.route_history;

    // Always use playbackIndex when user has interacted with the slider
    // or playback is running. Only fall back to raw snapshot when we're
    // at position 0 AND playback has never been started.
    if (playbackIndex === 0 && !playbackActive) return snapshot;

    const currentPoint = history[playbackIndex] ?? snapshot.latest_location;

    return {
      ...snapshot,
      latest_location: currentPoint,
      route_history: history.slice(0, playbackIndex + 1),
    };
  }, [snapshot, playbackActive, playbackIndex]);

  const routeStats = useMemo<RouteStats>(() => {
    const route = snapshot?.route_history || [];
    const distance = route
      .slice(1)
      .reduce((sum, point, index) => sum + haversineKm(route[index], point), 0);
    const avgSpeed = route.length
      ? route.reduce((sum, point) => sum + point.speed, 0) / route.length
      : 0;
    const maxSpeed = route.length
      ? Math.max(...route.map((point) => point.speed))
      : 0;
    return { distance, avgSpeed, maxSpeed };
  }, [snapshot]);

  return {
    playbackActive,
    setPlaybackActive,
    playbackIndex,
    setPlaybackIndex,
    activeSnapshot,
    routeStats,
  };
}

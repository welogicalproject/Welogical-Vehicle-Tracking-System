import { useState, useEffect, useRef, useMemo } from "react";
import { ReplayPoint } from "../types";

export function useTripReplay(points: ReplayPoint[]) {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1); // 1x, 2x, 5x, 10x
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Stop playback when points change
  useEffect(() => {
    setIsPlaying(false);
    setCurrentIndex(0);
  }, [points]);

  // Handle play loop timer
  useEffect(() => {
    if (isPlaying) {
      // Calculate delay based on speed multiplier.
      // Basic delay is 500ms per step, speed speeds it up.
      const delay = Math.max(50, 400 / playbackSpeed);
      
      timerRef.current = setInterval(() => {
        setCurrentIndex((prevIndex) => {
          if (prevIndex >= points.length - 1) {
            setIsPlaying(false);
            if (timerRef.current) clearInterval(timerRef.current);
            return prevIndex;
          }
          return prevIndex + 1;
        });
      }, delay);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, points.length]);

  const play = () => {
    if (points.length === 0) return;
    if (currentIndex >= points.length - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying(true);
  };

  const pause = () => {
    setIsPlaying(false);
  };

  const reset = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
  };

  const currentPoint = useMemo(() => {
    return points[currentIndex] || null;
  }, [points, currentIndex]);

  // Build route polyline path up to the current playback step
  const currentPath = useMemo(() => {
    return points.slice(0, currentIndex + 1);
  }, [points, currentIndex]);

  return {
    isPlaying,
    currentIndex,
    setCurrentIndex,
    playbackSpeed,
    setPlaybackSpeed,
    play,
    pause,
    reset,
    currentPoint,
    currentPath,
    totalPoints: points.length,
  };
}

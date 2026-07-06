"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Card } from "../ui/card";
import { VehicleTrackingSnapshot } from "../../types";
import { useGoogleMapsLoader } from "../map/hooks/useGoogleMapsLoader";
import { GOOGLE_MAPS_DARK_THEME } from "../map/styles/darkTheme";
import { getVehicleColor } from "../../utils/tracking";

interface MiniRouteHistoryMapProps {
  selectedSnapshot?: VehicleTrackingSnapshot;
  selectedVehicleId: number | "all";
  snapshots: VehicleTrackingSnapshot[];
}

export function MiniRouteHistoryMap({ selectedSnapshot, selectedVehicleId, snapshots }: MiniRouteHistoryMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [marker, setMarker] = useState<any>(null);
  const [polyline, setPolyline] = useState<any>(null);
  const { isLoaded } = useGoogleMapsLoader();

  useEffect(() => {
    if (!isLoaded || !containerRef.current || map) return;

    const google = (window as any).google;
    if (!google || !google.maps) return;

    // Initialize compact Google Map with default controls disabled
    const mapInstance = new google.maps.Map(containerRef.current, {
      zoom: 14,
      center: { lat: 22.3072, lng: 73.1812 },
      disableDefaultUI: true,
      zoomControl: false,
      scrollWheelZoom: false,
      dragging: false,
      styles: GOOGLE_MAPS_DARK_THEME
    });

    const markerInstance = new google.maps.Marker({
      map: mapInstance
    });

    const polylineInstance = new google.maps.Polyline({
      map: mapInstance,
      strokeOpacity: 0.8,
      strokeWeight: 2
    });

    setMap(mapInstance);
    setMarker(markerInstance);
    setPolyline(polylineInstance);

    return () => {
      markerInstance.setMap(null);
      polylineInstance.setMap(null);
      setMap(null);
      setMarker(null);
      setPolyline(null);
    };
  }, [isLoaded]);

  useEffect(() => {
    if (!map || !marker || !polyline || !selectedSnapshot?.latest_location) return;

    const google = (window as any).google;
    if (!google || !google.maps) return;

    const lat = selectedSnapshot.latest_location.latitude;
    const lon = selectedSnapshot.latest_location.longitude;
    const index = snapshots.findIndex((snapshot) => snapshot.vehicle.id === selectedSnapshot.vehicle.id);
    const color = getVehicleColor(index >= 0 ? index : 0);

    const position = { lat, lng: lon };
    map.setCenter(position);

    marker.setPosition(position);
    marker.setIcon({
      path: google.maps.SymbolPath.CIRCLE,
      scale: 5,
      fillColor: color,
      fillOpacity: 1.0,
      strokeColor: "#ffffff",
      strokeWeight: 1
    });

    const points = selectedSnapshot.route_history.map((pt) => ({
      lat: pt.latitude,
      lng: pt.longitude
    }));

    polyline.setPath(points);
    polyline.setOptions({ strokeColor: color });

    if (points.length > 1) {
      const bounds = new google.maps.LatLngBounds();
      points.forEach((pt) => bounds.extend(pt));
      map.fitBounds(bounds, { top: 10, bottom: 10, left: 10, right: 10 });
    }
  }, [selectedSnapshot, snapshots, map, marker, polyline]);

  if (selectedVehicleId === "all" || !selectedSnapshot) return null;

  return (
    <Card className="border-[#1e294b]/60 bg-[#131a2d]/40 rounded-xl overflow-hidden p-4 space-y-3">
      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block text-left">Last 10 Locations</span>
      <div
        ref={containerRef}
        className="w-full h-32 rounded-lg border border-[#1e294b]/60 overflow-hidden bg-[#07111f] z-10"
      />
      <Link
        href={`/vehicles/${selectedSnapshot.vehicle.id}?tab=route`}
        className="text-[10px] text-cyan-400 hover:text-cyan-300 font-bold uppercase tracking-wider block text-center pt-1"
      >
        View Full Route History &rarr;
      </Link>
    </Card>
  );
}

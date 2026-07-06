"use client";

import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { VehicleTrackingSnapshot } from "../types";
import { useGoogleMapsLoader } from "./map/hooks/useGoogleMapsLoader";
import { MapEngine } from "./map/engine/MapEngine";
import { VehicleLayer } from "./map/layers/VehicleLayer";
import { RouteLayer } from "./map/layers/RouteLayer";
import { SelectionLayer } from "./map/layers/SelectionLayer";
import { TrafficLayer } from "./map/layers/TrafficLayer";
import { GoogleRouteLayer } from "./map/layers/GoogleRouteLayer";
import { PlannedRouteLayer } from "./map/layers/PlannedRouteLayer";
import { MapControls } from "./tracking/MapControls";
import { voltage, escapeHtml } from "../utils/trackingMap";

type MapLayerType = "street" | "satellite";

interface FleetTrackingMapProps {
  snapshots: VehicleTrackingSnapshot[];
  selectedVehicleId: number | "all";
  visibleVehicleIds: number[];
  onSelectVehicle?: (id: number | "all") => void;
  heightClass?: string;
  isMiniMap?: boolean;
  googleRoutePolyline?: string | null;
  showGoogleRoute?: boolean;
  showGPSRoute?: boolean;
  routeColor?: string;
  plannedRoute?: {lat: number, lng: number}[];
}

export function FleetTrackingMap({
  snapshots,
  selectedVehicleId,
  visibleVehicleIds,
  onSelectVehicle,
  heightClass = "h-[560px]",
  isMiniMap = false,
  googleRoutePolyline = null,
  showGoogleRoute = false,
  showGPSRoute = true,
  routeColor,
  plannedRoute
}: FleetTrackingMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [engine, setEngine] = useState<any>(null);
  const [layer, setLayer] = useState<MapLayerType>("street");
  // Track the last coordinate we panned to so we don't fire panTo on every
  // playback tick (every 350ms). Only re-pan when the target has moved more
  // than a threshold distance from the last panned position.
  const lastPannedRef = useRef<{ lat: number; lng: number } | null>(null);
  const hasInitialFitRef = useRef(false);
  const prevSelectedVehicleIdRef = useRef<number | "all">(selectedVehicleId);
  const prevRoutePolylineRef = useRef<string | null>(googleRoutePolyline);
  
  const [fullscreen, setFullscreen] = useState(false);
  const { isLoaded, error: loadError } = useGoogleMapsLoader();

  // Reset the initial fit flag when the selected vehicle or the route changes
  useEffect(() => {
    if (
      prevSelectedVehicleIdRef.current !== selectedVehicleId ||
      prevRoutePolylineRef.current !== googleRoutePolyline
    ) {
      hasInitialFitRef.current = false;
      lastPannedRef.current = null;
      prevSelectedVehicleIdRef.current = selectedVehicleId;
      prevRoutePolylineRef.current = googleRoutePolyline;
    }
  }, [selectedVehicleId, googleRoutePolyline]);

  // 1. Initialize MapEngine adapter
  useEffect(() => {
    if (!isLoaded || !containerRef.current || engine) return;

    const mapEngine = MapEngine.createEngine("google");
    const initialCenter = { lat: 22.3072, lng: 73.1812 };
    
    mapEngine.initialize(containerRef.current, {
      zoom: isMiniMap ? 14 : 7,
      center: initialCenter,
      isMiniMap
    });

    // Create & Register active layers
    const vehicleLayer = new VehicleLayer(mapEngine);
    const routeLayer = new RouteLayer(mapEngine);
    const selectionLayer = new SelectionLayer(mapEngine);
    const trafficLayer = new TrafficLayer(mapEngine);
    const googleRouteLayer = new GoogleRouteLayer(mapEngine);
    const plannedRouteLayer = new PlannedRouteLayer(mapEngine);

    const layerManager = mapEngine.getLayerManager();
    layerManager.registerLayer(vehicleLayer);
    layerManager.registerLayer(routeLayer);
    layerManager.registerLayer(selectionLayer);
    layerManager.registerLayer(trafficLayer);
    layerManager.registerLayer(googleRouteLayer);
    layerManager.registerLayer(plannedRouteLayer);

    layerManager.showLayer("VehicleLayer");
    layerManager.showLayer("RouteLayer");
    layerManager.showLayer("SelectionLayer");
    layerManager.showLayer("GoogleRouteLayer");
    layerManager.showLayer("PlannedRouteLayer");

    // Listen to EventBus clicked markers
    mapEngine.getEventBus().on("MarkerClicked", (snapshot: any) => {
      if (onSelectVehicle) {
        onSelectVehicle(snapshot.vehicle.id);
      }

      // Render InfoWindow popup contents
      const latest = snapshot.latest_location;
      if (!latest) return;

      const ignitionState = latest.extra_data?.io?.ign === 1 ? "ON" : "OFF";
      const gpsFix = latest.extra_data?.gps_details?.fix ?? latest.extra_data?.gps?.fix ?? "A";
      const batteryVolt = voltage(snapshot, "battery");
      const mainVolt = voltage(snapshot, "main");
      const lastSeenStr = new Date(latest.timestamp).toLocaleTimeString();

      const popupHtml = `
        <div class="vts-popup">
          <strong style="color: #22d3ee; font-size: 13px; font-weight: 800; display: block;">${escapeHtml(snapshot.vehicle.vehicle_name)}</strong>
          <code style="color: #94a3b8; font-size: 10px; display: block; margin-bottom: 6px;">UID: ${escapeHtml(snapshot.vehicle.device_uid)}</code>
          <dl style="display: grid; grid-template-columns: 80px 1fr; gap: 3px 6px; margin: 0; border-top: 1px solid rgba(30,41,75,0.5); padding-top: 6px; font-size: 11px;">
            <dt style="color: #64748b; font-weight: 600;">Status</dt><dd style="margin:0; color:#cbd5e1;">${snapshot.movement_status} / ${snapshot.health_status}</dd>
            <dt style="color: #64748b; font-weight: 600;">Speed</dt><dd style="margin:0; color:#cbd5e1;">${latest.speed.toFixed(1)} km/h</dd>
            <dt style="color: #64748b; font-weight: 600;">Ignition</dt><dd style="margin:0; color:#cbd5e1;">${ignitionState}</dd>
            <dt style="color: #64748b; font-weight: 600;">GPS Fix</dt><dd style="margin:0; color:#cbd5e1;">${gpsFix === "A" ? "Valid Fix" : "No Fix"}</dd>
            <dt style="color: #64748b; font-weight: 600;">Battery</dt><dd style="margin:0; color:#cbd5e1;">${batteryVolt}</dd>
            <dt style="color: #64748b; font-weight: 600;">Main V</dt><dd style="margin:0; color:#cbd5e1;">${mainVolt}</dd>
            <dt style="color: #64748b; font-weight: 600;">Last Seen</dt><dd style="margin:0; color:#cbd5e1;">${lastSeenStr}</dd>
          </dl>
          <a href="/vehicles/${snapshot.vehicle.id}" style="display: block; margin-top: 8px; border: 1px solid rgba(6,182,212,0.6); background: rgba(6,182,212,0.1); border-radius: 6px; padding: 4px 6px; color: #22d3ee; text-align: center; font-weight: 700; text-decoration: none;">Open Vehicle Profile</a>
        </div>
      `;

      mapEngine.getOverlayManager().showPopup(
        { lat: latest.latitude, lng: latest.longitude },
        popupHtml
      );
    });

    setEngine(mapEngine);

    return () => {
      mapEngine.destroy();
      setEngine(null);
    };
  }, [isLoaded, isMiniMap, onSelectVehicle]);

  // Reset lastPannedRef whenever the user selects a different vehicle so that
  // the initial pan-to-vehicle fires correctly for the newly selected one.
  const prevSelectedVehicleRef = useRef<number | "all">(selectedVehicleId);
  useEffect(() => {
    if (prevSelectedVehicleRef.current !== selectedVehicleId) {
      lastPannedRef.current = null;
      prevSelectedVehicleRef.current = selectedVehicleId;
    }
  }, [selectedVehicleId]);

  // 2. Sync layers state and center viewport updates
  useEffect(() => {
    if (!engine || !engine.isReady()) return;

    const layerManager = engine.getLayerManager();
    
    // Refresh layers
    layerManager.refreshLayer("VehicleLayer", {
      snapshots,
      visibleIds: visibleVehicleIds,
      selectedId: selectedVehicleId
    });

    layerManager.refreshLayer("RouteLayer", {
      snapshots,
      visibleIds: showGPSRoute ? visibleVehicleIds : [],
      selectedId: selectedVehicleId,
      colorOverride: routeColor
    });

    layerManager.refreshLayer("GoogleRouteLayer", {
      encodedPolyline: googleRoutePolyline,
      visible: showGoogleRoute
    });

    layerManager.refreshLayer("PlannedRouteLayer", {
      coordinates: plannedRoute || [],
      visible: !!plannedRoute && plannedRoute.length > 0
    });

    // Refresh Selection Layer
    let selectedCoord = null;
    if (selectedVehicleId !== "all") {
      const activeSnap = snapshots.find((s) => s.vehicle.id === selectedVehicleId);
      if (activeSnap?.latest_location) {
        selectedCoord = {
          lat: activeSnap.latest_location.latitude,
          lng: activeSnap.latest_location.longitude
        };
      }
    }
    layerManager.refreshLayer("SelectionLayer", { selectedCoord });

    // Focus Viewport bounds
    const camera = engine.getCameraController();
    const boundsPoints: any[] = [];

    const targets = isMiniMap ? snapshots.slice(0, 1) : snapshots;

    targets.forEach((snapshot) => {
      const latest = snapshot.latest_location;
      const isVisible = visibleVehicleIds.includes(snapshot.vehicle.id) && (selectedVehicleId === "all" || selectedVehicleId === snapshot.vehicle.id);
      
      if (latest && isVisible) {
        boundsPoints.push({ lat: latest.latitude, lng: latest.longitude });
      }
    });

    if (boundsPoints.length > 0) {
      if (!hasInitialFitRef.current) {
        if (boundsPoints.length === 1) {
          camera.panTo(boundsPoints[0]);
          camera.setZoom(isMiniMap ? 14 : 16);
        } else {
          camera.fitBounds(boundsPoints);
        }
        hasInitialFitRef.current = true;
        
        if (boundsPoints.length === 1 && selectedVehicleId !== "all") {
          lastPannedRef.current = boundsPoints[0];
        } else {
          lastPannedRef.current = null;
        }
      } else {
        // After initial load:
        // During replay or live tracking, if a single vehicle is selected, auto-follow it.
        // Otherwise, never move the camera.
        if (boundsPoints.length === 1 && selectedVehicleId !== "all") {
          const target = boundsPoints[0];
          const last = lastPannedRef.current;
          // Only pan when the vehicle has moved more than ~0.005 deg (~500m)
          // from the last panned position to prevent constant micro-adjustments
          const hasMoved =
            !last ||
            Math.abs(target.lat - last.lat) > 0.005 ||
            Math.abs(target.lng - last.lng) > 0.005;

          if (hasMoved) {
            camera.panTo(target);
            lastPannedRef.current = target;
            // Notice we do NOT change zoom here. We keep the current zoom level.
          }
        }
      }
    }
  }, [engine, snapshots, selectedVehicleId, visibleVehicleIds, isMiniMap]);

  // 3. Set satellite/street layer mode
  useEffect(() => {
    if (engine) {
      engine.setMapType(layer);
    }
  }, [engine, layer]);

  const fitFleet = () => {
    if (!engine) return;
    const boundsPoints: any[] = [];
    snapshots.forEach((s) => {
      if (s.latest_location) {
        boundsPoints.push({ lat: s.latest_location.latitude, lng: s.latest_location.longitude });
      }
    });
    if (boundsPoints.length > 0) {
      if (boundsPoints.length === 1) {
        engine.getCameraController().panTo(boundsPoints[0]);
        engine.getCameraController().setZoom(16);
      } else {
        engine.getCameraController().fitBounds(boundsPoints);
      }
      hasInitialFitRef.current = true;
    }
  };

  const zoomSelected = () => {
    if (!engine || selectedVehicleId === "all") return;
    const activeSnap = snapshots.find((s) => s.vehicle.id === selectedVehicleId);
    if (activeSnap?.latest_location) {
      const coord = {
        lat: activeSnap.latest_location.latitude,
        lng: activeSnap.latest_location.longitude
      };
      engine.getCameraController().panTo(coord);
      engine.getCameraController().setZoom(17);
      hasInitialFitRef.current = true;
      lastPannedRef.current = coord;
    }
  };

  const toggleFullscreen = async () => {
    const element = containerRef.current?.parentElement;
    if (!element) return;
    if (!document.fullscreenElement) {
      await element.requestFullscreen?.();
      setFullscreen(true);
    } else {
      await document.exitFullscreen?.();
      setFullscreen(false);
    }
  };

  return (
    <div className={`relative w-full ${heightClass} overflow-hidden rounded-xl border border-[#1e294b]/60 bg-[#07111f]`}>
      {(!isLoaded || loadError) && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#07111f] text-xs font-semibold text-slate-400">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin text-cyan-400" />
          {loadError ? `Error loading map: ${loadError}` : "Loading Google Maps engine..."}
        </div>
      )}

      {/* Floating control toolbar */}
      {!isMiniMap && isLoaded && (
        <MapControls
          layer={layer}
          fullscreen={fullscreen}
          selectedVehicleId={selectedVehicleId}
          onToggleLayer={() => setLayer(layer === "street" ? "satellite" : "street")}
          onFitFleet={fitFleet}
          onZoomSelected={zoomSelected}
          onToggleFullscreen={toggleFullscreen}
        />
      )}

      {snapshots.length === 0 && isLoaded && !isMiniMap && (
        <div className="pointer-events-none absolute inset-x-0 bottom-5 z-20 mx-auto w-fit rounded-lg border border-[#1e294b]/60 bg-[#0f172a]/95 px-4 py-2 text-xs font-semibold text-slate-400">
          No vehicles in view range
        </div>
      )}

      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}

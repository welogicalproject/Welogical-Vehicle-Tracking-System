declare namespace google {
  namespace maps {
    class Map {
      constructor(mapDiv: HTMLElement, opts?: any);
    }
    class Polyline {
      constructor(opts?: PolylineOptions);
      setMap(map: Map | null): void;
      setPath(path: LatLng[] | LatLngLiteral[]): void;
      setOptions(options: PolylineOptions): void;
    }
    interface PolylineOptions {
      path?: LatLng[] | LatLngLiteral[];
      strokeColor?: string;
      strokeWeight?: number;
      strokeOpacity?: number;
      map?: Map | null;
      icons?: IconSequence[];
    }
    interface IconSequence {
      icon?: any;
      offset?: string;
      repeat?: string;
    }
    class LatLng {
      constructor(lat: number, lng: number);
      lat(): number;
      lng(): number;
    }
    interface LatLngLiteral {
      lat: number;
      lng: number;
    }
    namespace event {
      function clearInstanceListeners(instance: any): void;
    }
    namespace geometry {
      namespace encoding {
        function decodePath(encodedPath: string): LatLng[];
      }
    }
  }
}

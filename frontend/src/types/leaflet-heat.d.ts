import * as L from "leaflet";

declare module "leaflet" {
  export interface HeatMapOptions {
    minOpacity?: number;
    maxZoom?: number;
    max?: number;
    radius?: number;
    blur?: number;
    gradient?: { [key: number]: string };
  }

  export interface HeatLayer extends L.Layer {
    setLatLngs(
      latlngs: Array<[number, number, number]> | Array<{ lat: number; lng: number; alt?: number }>,
    ): this;
    addLatLng(
      latlng: [number, number, number] | { lat: number; lng: number; alt?: number },
    ): this;
    setOptions(options: HeatMapOptions): this;
    redraw(): this;
  }

  export function heatLayer(
    latlngs: Array<[number, number, number]>,
    options?: HeatMapOptions,
  ): HeatLayer;
}

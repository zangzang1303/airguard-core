export interface GeographicExtent {
  latMin: number;
  latMax: number;
  lonMin: number;
  lonMax: number;
}

// Bounding Box Coordinates matching Ocean Park 1 boundary polygon
export const OCEAN_PARK_1_EXTENT: GeographicExtent = {
  latMin: 20.9840,
  latMax: 21.0050,
  lonMin: 105.9330,
  lonMax: 105.9630,
};

// Exact Ocean Park 1 Boundary Polygon
export const OCEAN_PARK_1_BOUNDARY: [number, number][] = [
  [21.0047847, 105.9477604],
  [20.9933962, 105.9628773],
  [20.9890436, 105.9600712],
  [20.9852230, 105.9518985],
  [20.9840728, 105.9509930],
  [20.9851752, 105.9432602],
  [20.9921545, 105.9371584],
  [20.9968500, 105.9334673],
  [20.9980664, 105.9352872],
  [21.0017814, 105.9420739],
];

/**
 * Ray-casting point-in-polygon check for geographic coordinates.
 * Pure function: independent of camera, zoom, or screen pixels.
 */
export function isPointInBoundaryPolygon(
  lat: number,
  lon: number,
  polygon: [number, number][] = OCEAN_PARK_1_BOUNDARY
): boolean {
  let inside = false;
  const n = polygon.length;
  let p1 = polygon[0];
  for (let i = 1; i <= n; i++) {
    const p2 = polygon[i % n];
    if (lat > Math.min(p1[0], p2[0]) && lat <= Math.max(p1[0], p2[0])) {
      if (lon <= Math.max(p1[1], p2[1])) {
        let x_inters = p1[1];
        if (p1[0] !== p2[0]) {
          x_inters = ((lat - p1[0]) * (p2[1] - p1[1])) / (p2[0] - p1[0]) + p1[1];
        }
        if (p1[1] === p2[1] || lon <= x_inters) {
          inside = !inside;
        }
      }
    }
    p1 = p2;
  }
  return inside;
}

import { getMetricColor } from "../constants/metrics";

/**
 * Fixed metric color scale lookup for all environmental metrics.
 * Delegate strictly to single source of truth in constants/metrics.ts.
 */
export function getMetricColorHex(metric: string, val: number): string {
  return getMetricColor(metric, val);
}

/**
 * Helper to convert Hex color string to RGB object.
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  let c = hex.replace("#", "");
  if (c.length === 3) {
    c = c.split("").map((x) => x + x).join("");
  }
  const num = parseInt(c, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  };
}

/**
 * Generates an offscreen geographic 2D raster canvas covering OCEAN_PARK_1_EXTENT.
 * Each pixel corresponds to a fixed geographic (lat, lon) inside Ocean Park 1.
 * Pure rendering step — zero dependency on zoom or Leaflet camera.
 */
export function createDispersionOffscreenCanvas(
  gridPoints: Array<{ lat: number; lon: number; value: number }>,
  metric: string,
  width = 120,
  height = 120,
  extent = OCEAN_PARK_1_EXTENT,
  boundaryPolygon = OCEAN_PARK_1_BOUNDARY
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;

  const latStep = (extent.latMax - extent.latMin) / height;
  const lonStep = (extent.lonMax - extent.lonMin) / width;
  const sampleGridValue = createGridSampler(gridPoints);

  for (let y = 0; y < height; y++) {
    const lat = extent.latMax - (y + 0.5) * latStep;
    for (let x = 0; x < width; x++) {
      const lon = extent.lonMin + (x + 0.5) * lonStep;
      const idx = (y * width + x) * 4;

      if (gridPoints.length === 0) continue;
      const val = sampleGridValue(lat, lon);

      const hexColor = getMetricColorHex(metric, val);
      const rgb = hexToRgb(hexColor);

      data[idx] = rgb.r;
      data[idx + 1] = rgb.g;
      data[idx + 2] = rgb.b;
      // The raster remains translucent so geographic context stays visible.
      // The legend uses the same composited preview treatment.
      data[idx + 3] = 195;
    }
  }

  ctx.putImageData(imgData, 0, 0);

  // Apply clean vector polygon clipping via destination-in to avoid dark anti-alias fringe
  if (boundaryPolygon && boundaryPolygon.length > 0) {
    ctx.save();
    ctx.globalCompositeOperation = "destination-in";
    ctx.beginPath();
    boundaryPolygon.forEach(([lat, lon], i) => {
      const px = ((lon - extent.lonMin) / (extent.lonMax - extent.lonMin)) * width;
      const py = ((extent.latMax - lat) / (extent.latMax - extent.latMin)) * height;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  return canvas;
}

/**
 * Samples the regular grid produced by the spatial API. The API has already
 * performed the IDW calculation, so applying IDW again here creates artificial
 * local hotspots. Bilinear interpolation keeps the supplied field continuous
 * without changing its model or inventing a second spatial weighting.
 */
function createGridSampler(
  gridPoints: Array<{ lat: number; lon: number; value: number }>,
): (lat: number, lon: number) => number {
  const latitudes = [...new Set(gridPoints.map((point) => point.lat))].sort((a, b) => a - b);
  const longitudes = [...new Set(gridPoints.map((point) => point.lon))].sort((a, b) => a - b);
  const values = new Map(
    gridPoints.map((point) => [gridKey(point.lat, point.lon), point.value]),
  );

  return (lat: number, lon: number) => {
    const [latLower, latUpper] = getAxisBounds(latitudes, lat);
    const [lonLower, lonUpper] = getAxisBounds(longitudes, lon);
    const latRatio = latUpper === latLower ? 0 : (lat - latLower) / (latUpper - latLower);
    const lonRatio = lonUpper === lonLower ? 0 : (lon - lonLower) / (lonUpper - lonLower);

    const weightedCorners = [
      { value: values.get(gridKey(latLower, lonLower)), weight: (1 - latRatio) * (1 - lonRatio) },
      { value: values.get(gridKey(latLower, lonUpper)), weight: (1 - latRatio) * lonRatio },
      { value: values.get(gridKey(latUpper, lonLower)), weight: latRatio * (1 - lonRatio) },
      { value: values.get(gridKey(latUpper, lonUpper)), weight: latRatio * lonRatio },
    ];
    const usableCorners = weightedCorners.filter(
      (corner): corner is { value: number; weight: number } => typeof corner.value === "number",
    );
    const totalWeight = usableCorners.reduce((sum, corner) => sum + corner.weight, 0);

    if (totalWeight > 0) {
      return usableCorners.reduce((sum, corner) => sum + corner.value * corner.weight, 0) / totalWeight;
    }

    return gridPoints.reduce((closest, point) => {
      const closestDistance = Math.hypot(lat - closest.lat, lon - closest.lon);
      const pointDistance = Math.hypot(lat - point.lat, lon - point.lon);
      return pointDistance < closestDistance ? point : closest;
    }).value;
  };
}

function getAxisBounds(axis: number[], target: number): [number, number] {
  const first = axis[0];
  const last = axis[axis.length - 1];
  if (target <= first) return [first, first];
  if (target >= last) return [last, last];

  const upperIndex = axis.findIndex((value) => value >= target);
  return [axis[upperIndex - 1], axis[upperIndex]];
}

function gridKey(lat: number, lon: number): string {
  return `${lat.toFixed(5)}:${lon.toFixed(5)}`;
}

import { getAqiColorHex } from "../constants/aqi";

export interface StationPoint {
  lat: number;
  lon: number;
  val: number;
}

export interface WindContext {
  speedMs: number;
  directionDeg: number;
}

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

/**
 * Pure geographic Inverse Distance Weighting (IDW) field evaluation.
 * Formula: valueAt(lat, lon, stations, windConfig)
 * ABSOLUTELY NO camera zoom, viewport size, or pixel coordinates in calculation.
 */
export function calculateIdwValueAt(
  lat: number,
  lon: number,
  stations: StationPoint[],
  wind?: WindContext,
  power = 2.0,
  epsilon = 0.0001
): number {
  if (!stations || stations.length === 0) return 50.0;

  let sumWeights = 0.0;
  let sumWeightedVals = 0.0;

  const windSpeed = wind ? wind.speedMs : 0.0;
  const windRad = wind ? (wind.directionDeg * Math.PI) / 180.0 : 0.0;
  const windVecX = Math.sin(windRad);
  const windVecY = Math.cos(windRad);

  for (const st of stations) {
    const dLat = (lat - st.lat) * 111.0; // Approx km
    const dLon = (lon - st.lon) * 103.0; // Approx km
    const dist = Math.hypot(dLat, dLon);

    let effectiveDist = dist;
    if (dist > 0.001 && windSpeed > 0) {
      const normDx = dLon / dist;
      const normDy = dLat / dist;
      const cosTheta = normDx * windVecX + normDy * windVecY;
      const dispersionFactor = 1.0 - cosTheta * Math.min(0.6, windSpeed * 0.08);
      effectiveDist = Math.max(dist * Math.max(0.2, dispersionFactor), epsilon);
    } else {
      effectiveDist = Math.max(dist, epsilon);
    }

    const weight = 1.0 / Math.pow(effectiveDist, power);
    sumWeights += weight;
    sumWeightedVals += weight * st.val;
  }

  const result = sumWeights > 0 ? sumWeightedVals / sumWeights : 50.0;
  return Math.round(result * 10) / 10;
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
  gridPoints: Array<{ lat: number; lon: number; value: number }> | null,
  stations: StationPoint[],
  metric: string,
  wind?: WindContext,
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

  for (let y = 0; y < height; y++) {
    const lat = extent.latMax - (y + 0.5) * latStep;
    for (let x = 0; x < width; x++) {
      const lon = extent.lonMin + (x + 0.5) * lonStep;
      const idx = (y * width + x) * 4;

      // Strict clipping to Ocean Park 1 polygon
      if (!isPointInBoundaryPolygon(lat, lon, boundaryPolygon)) {
        data[idx] = 0;
        data[idx + 1] = 0;
        data[idx + 2] = 0;
        data[idx + 3] = 0;
        continue;
      }

      let val: number;
      if (gridPoints && gridPoints.length > 0) {
        // Interpolate value from grid points or IDW
        val = interpolateValueFromGridOrIdw(lat, lon, gridPoints, stations, wind);
      } else {
        val = calculateIdwValueAt(lat, lon, stations, wind);
      }

      const hexColor = getMetricColorHex(metric, val);
      const rgb = hexToRgb(hexColor);

      data[idx] = rgb.r;
      data[idx + 1] = rgb.g;
      data[idx + 2] = rgb.b;
      data[idx + 3] = 195; // ~0.76 opacity for clear street basemap visibility
    }
  }

  ctx.putImageData(imgData, 0, 0);
  return canvas;
}

function interpolateValueFromGridOrIdw(
  lat: number,
  lon: number,
  gridPoints: Array<{ lat: number; lon: number; value: number }>,
  stations: StationPoint[],
  wind?: WindContext
): number {
  let closestDist = Infinity;
  let closestVal = 50.0;

  for (const pt of gridPoints) {
    const dLat = (lat - pt.lat) * 111.0;
    const dLon = (lon - pt.lon) * 103.0;
    const d = Math.hypot(dLat, dLon);
    if (d < closestDist) {
      closestDist = d;
      closestVal = pt.value;
    }
  }

  if (closestDist < 0.15) {
    return closestVal;
  }

  return calculateIdwValueAt(lat, lon, stations, wind);
}

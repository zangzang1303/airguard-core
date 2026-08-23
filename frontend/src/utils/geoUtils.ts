import { Station } from "../types";

/**
 * Calculates distance in meters between two lat/lng coordinates using the Haversine formula.
 */
export function calculateDistanceMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371e3; // Earth radius in meters
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return Math.round(R * c);
}

/**
 * Formats distance into a human-readable Vietnamese string.
 */
export function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${meters}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
}

export interface NearestStationResult {
  station: Station;
  distanceMeters: number;
  formattedDistance: string;
}

/**
 * Finds the nearest active sensor station to the given coordinates.
 */
export function findNearestStation(
  coords: [number, number],
  stations: Station[]
): NearestStationResult | null {
  if (!stations || stations.length === 0) return null;

  const [lat, lon] = coords;
  let nearestStation: Station | null = null;
  let minDistance = Infinity;

  for (const st of stations) {
    if (typeof st.latitude !== "number" || typeof st.longitude !== "number") continue;
    const d = calculateDistanceMeters(lat, lon, st.latitude, st.longitude);
    if (d < minDistance) {
      minDistance = d;
      nearestStation = st;
    }
  }

  if (!nearestStation) return null;

  return {
    station: nearestStation,
    distanceMeters: minDistance,
    formattedDistance: formatDistance(minDistance),
  };
}

/**
 * Tries to parse a coordinate string like "20.993, 105.946" or "20.9935 105.9520".
 */
export function parseCoordinateString(input: string): [number, number] | null {
  const cleaned = input.trim();
  // Match patterns like "20.993, 105.946", "20.993,105.946", "20.993 105.946"
  const match = cleaned.match(/^([+-]?\d+(?:\.\d+)?)[,\s]+([+-]?\d+(?:\.\d+)?)$/);
  if (!match) return null;

  const lat = parseFloat(match[1]);
  const lng = parseFloat(match[2]);

  if (isNaN(lat) || isNaN(lng)) return null;
  // Basic sanity check for latitude & longitude bounds
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;

  return [lat, lng];
}

import { Station, Alert, HistoryPoint, ForecastData, Proposal } from "./index";

export type ActiveDrawerType =
  | null
  | "station-poi"
  | "analysis"
  | "ai-chat"
  | "near-me"
  | "today"
  | "forecast-bar"
  | "alerts"
  | "health-profile"
  | "community-report"
  | "manager-approval"
  | "directions";

export type EnvironmentalLayerType =
  | "aqi"
  | "pm25"
  | "co2"
  | "temperature"
  | "noise_db"
  | "humidity";

export interface MapLayerConfig {
  activeEnvironmentalLayer: EnvironmentalLayerType;
  showBoundary: boolean;
  showPlaces: boolean;
  showSensors: boolean;
  showHeatmap: boolean;
  showWindVectors: boolean;
  showCommunityReports: boolean;
}

export interface PlacePOI {
  id: string;
  name: string;
  category: "lake" | "park" | "university" | "residential" | "mall" | "landmark" | "gate";
  subdivision?: string;
  latitude: number;
  longitude: number;
  description: string;
  estimatedAqi?: number;
  sensorIdRef?: string;
  bestTimeToVisit?: string;
  iconName?: string;
}

export interface AiMapHighlightArea {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  radius: number;
  color: string;
  label: string;
  type: "recommended" | "avoid" | "moderate";
}

export interface RouteOption {
  id: string;
  name: string;
  durationMinutes: number;
  distanceKm: number;
  pollutionExposurePercent: number; // e.g. -24%
  isRecommended: boolean;
  waypoints: [number, number][];
  summary: string;
}

export interface HealthProfile {
  sensitivityGroup: "normal" | "sensitive" | "respiratory" | "elderly" | "child" | "outdoor_sport";
  fullName: string;
  interests: string[];
  alertPushEnabled: boolean;
  dailyDigestEnabled: boolean;
}

export interface CommunityReport {
  id: string;
  category: "smoke" | "dust" | "bad_smell" | "noise" | "waste" | "other";
  description: string;
  latitude: number;
  longitude: number;
  address: string;
  createdAt: string;
  status: "pending" | "investigating" | "resolved";
}

export interface ForecastTimeStep {
  label: string;
  hourOffset: number;
  timeString: string;
  heatMultiplier: number;
  aqiMap: Record<string, number>;
}

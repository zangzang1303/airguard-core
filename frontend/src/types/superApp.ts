export type ActiveDrawerType =
  | null
  | "station-poi"
  | "forecast"
  | "analysis"
  | "ai-chat"
  | "near-me"
  | "today"
  | "alerts"
  | "health-profile"
  | "community-report"
  | "manager-approval"
  | "directions"
  | "audit";

export type EnvironmentalLayerType =
  | "aqi"
  | "pm25"
  | "co2"
  | "temperature"
  | "noise_db"
  | "humidity";

export type MapViewMode = "markers" | "heatmap";

export type MapLayerVisibilityKey =
  | "showBoundary"
  | "showPlaces"
  | "showSensors"
  | "showHeatmap"
  | "showWindVectors"
  | "showCommunityReports"
  | "showConnectionStatus"
  | "showStationOverview"
  | "showDemoControl"
  | "showForecastTimeline"
  | "showAirQualityNow"
  | "showMapLegend";

export interface MapLayerConfig {
  activeEnvironmentalLayer: EnvironmentalLayerType;
  viewMode: MapViewMode;
  showBoundary: boolean;
  showPlaces: boolean;
  showSensors: boolean;
  showHeatmap: boolean;
  showWindVectors: boolean;
  showCommunityReports: boolean;
  showConnectionStatus: boolean;
  showStationOverview: boolean;
  showDemoControl?: boolean;
  showForecastTimeline?: boolean;
  showAirQualityNow?: boolean;
  showMapLegend?: boolean;
}

export interface PlacePOI {
  id: string;
  name: string;
  category:
    | "lake"
    | "park"
    | "university"
    | "residential"
    | "mall"
    | "landmark"
    | "gate"
    | "gym"
    | "bus"
    | "bike"
    | "pool"
    | "indoor_fitness";
  subdivision?: string;
  latitude: number;
  longitude: number;
  description: string;
  sensorIdRef?: string;
  iconName?: string;
}

export interface HealthProfile {
  /** Recommendation policy selector; this is not a medical diagnosis. */
  sensitivityGroup: "normal" | "sensitive" | "outdoor_sport";
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

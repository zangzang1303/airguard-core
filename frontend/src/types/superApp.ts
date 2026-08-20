export type ActiveDrawerType =
  | null
  | "station-poi"
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
  sensorIdRef?: string;
  iconName?: string;
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


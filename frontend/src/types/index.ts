export type UserRole = 'resident' | 'manager' | 'admin';
export type UserGroup = 'normal' | 'sensitive' | 'outdoor_sport';

export type StationStatus = 'online' | 'offline' | 'stale' | 'invalid';

export interface Station {
  station_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  pm25: number | null;
  status: StationStatus;
  is_stale: boolean;
  updated_at: string;
  location_type?: string;
}

export interface WeatherContext {
  temperature: number;
  humidity: number;
  wind_speed: number;
  source: string;
}

export interface StationDetailData extends Station {
  weather?: WeatherContext;
  source: string;
}

export interface HistoryPoint {
  timestamp: string;
  pm25: number;
  temperature?: number;
  humidity?: number;
}

export interface ForecastHorizon {
  horizon: string;
  pm25_predicted: number;
  range: [number, number];
}

export interface ForecastData {
  station_id: string;
  horizon_hours: number;
  source: string;
  confidence: string;
  forecasts: ForecastHorizon[];
}

export interface Alert {
  alert_id: string;
  station_id: string;
  severity: 'warning' | 'moderate' | 'critical' | 'good';
  message: string;
  observed_value: number;
  threshold: number;
  status: 'active' | 'resolved';
  created_at: string;
}

export interface Evidence {
  pm25: number;
  humidity?: number;
  wind_speed?: number;
  observed_at?: string;
}

export interface Proposal {
  proposal_id: string;
  station_id: string;
  severity: string;
  target: string;
  action: string;
  rationale: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  evidence: Evidence;
  reviewed_by?: string;
  reviewed_at?: string;
  review_note?: string;
  dispatch_status?: 'not_configured' | 'pending' | 'succeeded' | 'failed';
}

export interface AuditLogEntry {
  id: string;
  time: string;
  actor: string;
  action: string;
  target: string;
  outcome: string;
  correlation_id: string;
}

export interface AgentResponse {
  reply: string;
  used_tools: string[];
  evidence: Record<string, any>;
  proposal_created?: Proposal | null;
}

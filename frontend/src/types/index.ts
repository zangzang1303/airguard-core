export type UserRole = "resident" | "manager" | "admin";
export type UserGroup = "normal" | "sensitive" | "outdoor_sport";
export type AdminUserStatus = "active" | "disabled" | "invitation_pending";

export interface AdminUser {
  user_id: string;
  full_name: string;
  email: string;
  role: UserRole;
  user_group: UserGroup;
  organization: string;
  region: string;
  status: AdminUserStatus;
  last_active_at: string | null;
  created_at: string;
  avatar_initials: string;
}

export interface AdminAuditEntry {
  id: string;
  time: string;
  actor: string;
  action: string;
  target: string;
  outcome: string;
  correlation_id: string;
  detail?: string;
}

export interface UserMutationResult {
  success: boolean;
  message?: string;
  user?: AdminUser;
  audit_entry: AdminAuditEntry;
}

export type StationStatus = "online" | "offline" | "stale" | "invalid";

export type StationLifecycle = "active" | "retired";

export interface AdminRegion {
  region_id: string;
  region_name: string;
  description: string;
}

/** Station catalog record cho module Admin · Khu vực & Trạm (P2). */
export interface AdminStation {
  station_id: string;
  station_name: string;
  region_id: string;
  region_name: string;
  location_type: string;
  lifecycle: StationLifecycle;
  owner: string;
  status: StationStatus;
  is_stale: boolean;
  /** null khi backend không có measurement hợp lệ — không thay bằng 0. */
  pm25: number | null;
  measured_at: string | null;
  received_at: string | null;
  source: string;
  /** null khi catalog thiếu toạ độ; UI không được đặt marker giả. */
  latitude: number | null;
  longitude: number | null;
  /** Vị trí trên sơ đồ schematic, phần trăm; null nếu thiếu toạ độ. */
  map_x: number | null;
  map_y: number | null;
  /** Lý do stale/offline/invalid hoặc thiếu toạ độ, do backend trả về. */
  status_reason: string | null;
  provisioned_at: string;
}

export interface StationCatalogResponse {
  regions: AdminRegion[];
  stations: AdminStation[];
  /** Thông báo partial error từ backend, ví dụ map data không đầy đủ. */
  partial_error: string | null;
}

export interface StationChangeEntry {
  id: string;
  time: string;
  actor: string;
  action: string;
  detail: string;
  outcome: string;
  correlation_id: string;
}

/* ===== Admin · Thiết bị IoT (P2) ===== */

export type DeviceConnectivity = "online" | "stale" | "offline" | "invalid";

/** Vòng đời registry; deactivate thay vì hard-delete. */
export type DeviceLifecycle = "active" | "maintenance" | "deactivated";

export type FirmwareState = "up_to_date" | "update_available" | "unknown";

export type ConfigState = "in_sync" | "drift" | "pending" | "unknown";

/** Outcome hợp lệ của mutation/command; UI không tự tuyên bố thành công. */
export type DeviceMutationOutcome =
  | "not_configured"
  | "pending"
  | "succeeded"
  | "failed";

export interface DeviceDataQuality {
  /** Khoảng thời gian backend tổng hợp, ví dụ "24 giờ gần nhất". */
  window_label: string;
  invalid_count: number;
  duplicate_count: number;
  rejected_count: number;
  /** Reason code gần nhất do backend trả về, không suy diễn ở client. */
  last_reason_code: string | null;
  last_event_at: string | null;
}

export interface DeviceEvent {
  id: string;
  time: string;
  /** reconnect, publish_failure, invalid_payload, config_applied, maintenance... */
  type: string;
  detail: string;
  outcome: string;
  correlation_id: string;
}

/** Device registry record cho module Admin · Thiết bị IoT (P2). */
export interface AdminDevice {
  /** Immutable sau provision. */
  device_id: string;
  device_name: string;
  device_type: string;
  /** Serial đã mask theo policy; không hiển thị giá trị đầy đủ. */
  serial_masked: string;
  /** null khi thiết bị chưa gán trạm — không fallback thành online. */
  station_id: string | null;
  station_name: string | null;
  region_id: string | null;
  region_name: string | null;
  connectivity: DeviceConnectivity;
  /** Lý do stale/offline/invalid do backend trả về. */
  connectivity_reason: string | null;
  last_heartbeat_at: string | null;
  heartbeat_interval_seconds: number | null;
  /** null khi backend không cung cấp; không suy diễn từ client timer. */
  uptime_ratio_24h: number | null;
  latency_ms: number | null;
  firmware_version: string;
  firmware_recommended: string | null;
  firmware_state: FirmwareState;
  config_profile: string;
  config_version: string;
  /** Checksum đã redacted; không chứa secret, MQTT URL hay token. */
  config_checksum: string;
  config_state: ConfigState;
  config_applied_at: string | null;
  calibration_note: string | null;
  lifecycle: DeviceLifecycle;
  is_simulator: boolean;
  source: string;
  provisioned_at: string;
  owner: string;
  data_quality: DeviceDataQuality;
  last_event: DeviceEvent | null;
}

export interface DeviceRegistryResponse {
  devices: AdminDevice[];
  /** Partial error từ backend, ví dụ telemetry service không khả dụng. */
  partial_error: string | null;
}

export interface DeviceMutationResult {
  outcome: DeviceMutationOutcome;
  message: string;
  audit_entry: AdminAuditEntry | null;
}

export interface Station {
  station_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  pm25: number | null;
  aqi?: number | null;
  aqi_category?: string | null;
  co2?: number | null;
  noise_db?: number | null;
  temperature?: number | null;
  status: StationStatus;
  is_stale: boolean;
  updated_at: string;
  location_type?: string;
  source?: string | null;
  freshness?: string;
  humidity?: number | null;
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
  aqi?: number | null;
  co2?: number | null;
  noise_db?: number | null;
  temperature?: number | null;
  humidity?: number | null;
  source?: string | null;
  quality_flag?: string;
  message_id?: string;
}

export interface ForecastHorizon {
  horizon: string;
  pm25_predicted: number | null;
  range: [number | null, number | null];
  value?: number | null;
  value_min?: number | null;
  value_max?: number | null;
  confidence?: number;
}

export interface ForecastData {
  station_id: string;
  horizon_hours: number;
  metric: "pm25" | "aqi" | "co2" | "noise_db" | "temperature";
  source: string;
  confidence: string;
  model_name?: string;
  limitations?: string[];
  forecasts: ForecastHorizon[];
}

export interface Alert {
  alert_id: string;
  station_id: string;
  alert_type: string;
  severity: "warning" | "moderate" | "critical" | "good";
  title: string;
  message: string;
  observed_value: number;
  threshold: number;
  unit?: string;
  recommendation?: string;
  status: "active" | "resolved";
  created_at: string;
}

export interface Evidence {
  aqi?: number;
  aqi_category?: string;
  pm25?: number;
  co2?: number;
  noise_db?: number;
  temperature?: number;
  observed_at?: string;
}

export interface Proposal {
  proposal_id: string;
  station_id: string;
  request_type?: string;
  device_id?: string | null;
  proposed_action?: "notify_station_area_users" | "ventilation_boost" | "air_purifier_on" | "eco_mode";
  duration_minutes?: number | null;
  severity: string;
  target: string;
  action: string;
  rationale: string;
  status: "pending" | "approved" | "rejected" | "expired";
  created_at: string;
  created_by?: string;
  evidence: Evidence;
  version: number;
  reviewed_by?: string;
  reviewed_at?: string;
  review_note?: string;
  dispatch_status?: "unknown" | "not_configured" | "queued" | "pending" | "succeeded" | "failed";
}

export type ReportType = "daily" | "weekly";
export type ReportStatus = "generating" | "completed" | "failed";
export type ReportGenerationMode = "live_llm" | "deterministic_grounded";
export type ReportTrendDirection = "improving" | "worsening" | "stable" | "insufficient_data";
export type VentilationEffectivenessOutcome = "improved" | "worsened" | "mixed" | "insufficient_data";
export type ReportExportFormat = "markdown" | "html" | "pdf";

export interface ReportStationStatistics {
  station_id: string;
  sample_count: number;
  avg_aqi: number | null;
  max_aqi: number | null;
  avg_pm25: number | null;
  max_pm25: number | null;
  avg_co2: number | null;
  max_co2: number | null;
  avg_noise_db: number | null;
  max_noise_db: number | null;
  avg_temperature: number | null;
  max_temperature: number | null;
}

export interface ReportMeasurementStatistics {
  valid_sample_count: number;
  excluded_sample_count: number;
  station_count: number;
  overall_avg_aqi: number | null;
  overall_max_aqi: number | null;
  worst_station_id: string | null;
  stations: ReportStationStatistics[];
}

export interface ReportDailyTrendPoint {
  date: string;
  valid_sample_count: number;
  avg_aqi: number | null;
  avg_pm25: number | null;
}

export interface ReportTrendStatistics {
  direction: ReportTrendDirection;
  daily_series: ReportDailyTrendPoint[];
  weekday_avg_aqi: number | null;
  weekend_avg_aqi: number | null;
  weekend_minus_weekday_aqi: number | null;
}

export interface ReportCountBreakdown {
  total_count: number;
  threshold_exceedance_count: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
}

export interface ReportProposalStatistics {
  total_count: number;
  by_status: Record<string, number>;
  by_action: Record<string, number>;
}

export interface VentilationEffectivenessStatistics {
  evaluated_cycle_count: number;
  insufficient_cycle_count: number;
  mean_pm25_change: number | null;
  mean_pm25_change_percent: number | null;
  mean_co2_change: number | null;
  mean_co2_change_percent: number | null;
  outcome: VentilationEffectivenessOutcome;
}

export interface ReportVentilationStatistics {
  activation_count: number;
  total_duration_minutes: number;
  by_action: Record<string, number>;
  effectiveness: VentilationEffectivenessStatistics;
}

export interface ReportDataQualityStatistics {
  source_labels: string[];
  disclaimer: string;
}

export interface ReportStatistics {
  measurements: ReportMeasurementStatistics;
  trends: ReportTrendStatistics;
  alerts: ReportCountBreakdown;
  proposals: ReportProposalStatistics;
  ventilation: ReportVentilationStatistics;
  data_quality: ReportDataQualityStatistics;
}

export interface Report {
  report_id: string;
  report_type: ReportType;
  period_start: string;
  period_end: string;
  timezone: string;
  status: ReportStatus;
  statistics: ReportStatistics;
  evidence_summary: Record<string, unknown>;
  narrative: string;
  generation_mode: ReportGenerationMode;
  model_source: string;
  generated_by: string | null;
  failure_code: string | null;
  created_at: string;
  completed_at: string | null;
  reused?: boolean;
}

export interface ReportGenerateRequest {
  type: ReportType;
  period_start?: string;
  period_end?: string;
  timezone: string;
}

export interface ReportExport {
  blob: Blob;
  filename: string;
  media_type: string;
}

export interface AuditLogEntry {
  id: string;
  time: string;
  actor: string;
  action: string;
  target: string;
  outcome: string;
}

export interface AuditLogEntry {
  id: string;
  time: string;
  actor: string;
  action: string;
  target: string;
  outcome: string;
  correlation_id: string;
  detail?: string;
}


export interface AgentResponseAnswer {
  summary: string;
  details: string;
}

export interface AgentResponse {
  reply: string;
  answer?: AgentResponseAnswer | string;
  intent?: string;
  time_context?: {
    type: "live" | "forecast";
    is_forecast?: boolean;
    label?: string;
    start?: string;
    end?: string;
    forecast_hour?: number;
  };
  data_mode?: "live" | "forecast";
  evidence: Record<string, any> | Array<Record<string, any>>;
  map_actions?: Array<Record<string, any>>;
  used_tools?: string[];
  proposal_created?: Proposal | null;
  proposal_id?: string | null;
  request_id?: string;
}

export interface SpatialHeatmapPoint {
  lat: number;
  lon: number;
  value: number;
  intensity: number;
  level: "good" | "moderate" | "unhealthy_sensitive" | "unhealthy" | "very_unhealthy" | "hazardous";
}

export interface SpatialModel {
  name: string;
  version: string;
  grid_rows: number;
  grid_columns: number;
  power: number;
  minimum_stations: number;
}

export interface SpatialExtent {
  south: number;
  west: number;
  north: number;
  east: number;
}

export interface SpatialWeather {
  wind_speed_ms: number;
  wind_direction_deg: number;
  source: string;
  observed_at: string;
  is_fallback: boolean;
  is_stale: false;
  assumptions: string[];
}

export interface SpatialDataQuality {
  status: "valid";
  stations_required: number;
  stations_used: string[];
  stations_excluded: string[];
  exclusion_reasons: Record<string, string[]>;
  station_sources: string[];
  forecast_sources: string[];
}

export interface SpatialStationInput {
  station_id: string;
  lat: number;
  lon: number;
  value: number;
  source: string;
  observed_at: string;
  forecast_source: string | null;
}

export interface SpatialHeatmapResponse {
  metric: "aqi" | "pm25" | "co2" | "noise_db" | "temperature";
  unit: string;
  forecast_hour: number;
  generated_at: string;
  timestamp: string;
  wind_speed_ms: number;
  wind_direction_deg: number;
  model_version: string;
  model: SpatialModel;
  extent: SpatialExtent;
  weather: SpatialWeather;
  data_quality: SpatialDataQuality;
  station_inputs: SpatialStationInput[];
  source: "spatial_idw_dispersion_model";
  grid_points: SpatialHeatmapPoint[];
  disclaimer: string;
}

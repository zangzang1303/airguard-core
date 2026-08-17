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
  humidity?: number;
}

export interface ForecastHorizon {
  horizon: string;
  pm25_predicted: number;
  range: [number, number];
  value?: number;
  value_min?: number;
  value_max?: number;
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
  severity: string;
  target: string;
  action: string;
  rationale: string;
  status: "pending" | "approved" | "rejected" | "expired";
  created_at: string;
  evidence: Evidence;
  version: number;
  reviewed_by?: string;
  reviewed_at?: string;
  review_note?: string;
  dispatch_status?: "not_configured" | "queued" | "pending" | "succeeded" | "failed";
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
  proposal_id?: string | null;
}

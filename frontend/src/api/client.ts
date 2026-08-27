import {
  Station,
  StationDetailData,
  HistoryPoint,
  ForecastData,
  Alert,
  Proposal,
  AuditLogEntry,
  AgentResponse,
  AdminUser,
  AdminAuditEntry,
  UserMutationResult,
  Report,
  ReportExport,
  ReportExportFormat,
  ReportGenerateRequest,
  ReportType,
  SpatialHeatmapResponse,
  SpatialHeatmapPoint,
  EmailDeliveryStatus,
} from "../types";
import { resolveApiBaseUrl } from "./apiBaseUrl";
import { extractAgentReply } from "./agentResponseHelper.js";

export interface DemoApiActor {
  userId: string;
  role: "manager";
}

const isBrowser = typeof window !== "undefined";
const API_BASE_URL = resolveApiBaseUrl({
  hostname: isBrowser ? window.location.hostname : "",
  configuredBaseUrl: import.meta.env.VITE_API_BASE_URL,
});

const API_TIMEOUT_MS = 10_000;

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  const upstreamSignal = init.signal;
  const forwardAbort = () => controller.abort(upstreamSignal?.reason);

  if (upstreamSignal) {
    if (upstreamSignal.aborted) {
      forwardAbort();
    } else {
      upstreamSignal.addEventListener("abort", forwardAbort, { once: true });
    }
  }

  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    globalThis.clearTimeout(timeoutId);
    upstreamSignal?.removeEventListener("abort", forwardAbort);
  }
}

const demoNow = new Date();
const hoursAgo = (h: number) =>
  new Date(demoNow.getTime() - h * 3600 * 1000).toISOString();
const daysAgo = (d: number) =>
  new Date(demoNow.getTime() - d * 24 * 3600 * 1000).toISOString();

// Demo data cho module Quản lý người dùng (P2).
// Chỉ tồn tại trên client cho mục đích demo MVP; KHÔNG phải dữ liệu production.
// Khi backend chốt API contract, thay thế bằng response thật từ /api/v1/users.
export const DEMO_ADMIN_USERS: AdminUser[] = [
  {
    user_id: "USR-001",
    full_name: "Lê Thị D",
    email: "admin@vinuni.edu.vn",
    role: "admin",
    user_group: "normal",
    organization: "AirGuard Operations",
    region: "Toàn hệ thống",
    status: "active",
    last_active_at: hoursAgo(0.5),
    created_at: daysAgo(120),
    avatar_initials: "LD",
  },
  {
    user_id: "USR-002",
    full_name: "Nguyễn Văn A",
    email: "manager@vinuni.edu.vn",
    role: "manager",
    user_group: "sensitive",
    organization: "VinUniversity",
    region: "VinUni Campus",
    status: "active",
    last_active_at: hoursAgo(2),
    created_at: daysAgo(95),
    avatar_initials: "NA",
  },
  {
    user_id: "USR-003",
    full_name: "Trần Minh Anh",
    email: "resident@vinuni.edu.vn",
    role: "resident",
    user_group: "normal",
    organization: "Vinhomes Ocean Park",
    region: "Vinhomes Ocean Park",
    status: "active",
    last_active_at: hoursAgo(5),
    created_at: daysAgo(80),
    avatar_initials: "TA",
  },
  {
    user_id: "USR-004",
    full_name: "Phạm Quốc Bảo",
    email: "bao.pq@vinuni.edu.vn",
    role: "manager",
    user_group: "outdoor_sport",
    organization: "VinUniversity",
    region: "VinUni Campus",
    status: "active",
    last_active_at: hoursAgo(9),
    created_at: daysAgo(60),
    avatar_initials: "PB",
  },
  {
    user_id: "USR-005",
    full_name: "Hoàng Thu Hà",
    email: "ha.ht@vinuni.edu.vn",
    role: "resident",
    user_group: "sensitive",
    organization: "Vinhomes Ocean Park",
    region: "Vinhomes Ocean Park",
    status: "active",
    last_active_at: daysAgo(1),
    created_at: daysAgo(45),
    avatar_initials: "HH",
  },
  {
    user_id: "USR-006",
    full_name: "Vũ Đức Long",
    email: "long.vd@vinuni.edu.vn",
    role: "resident",
    user_group: "outdoor_sport",
    organization: "Vinhomes Ocean Park",
    region: "Vinhomes Ocean Park",
    status: "disabled",
    last_active_at: daysAgo(12),
    created_at: daysAgo(40),
    avatar_initials: "VL",
  },
  {
    user_id: "USR-007",
    full_name: "Đỗ Mai Linh",
    email: "linh.dm@vinuni.edu.vn",
    role: "manager",
    user_group: "normal",
    organization: "VinUniversity",
    region: "VinUni Campus",
    status: "invitation_pending",
    last_active_at: null,
    created_at: daysAgo(3),
    avatar_initials: "DL",
  },
  {
    user_id: "USR-008",
    full_name: "Ngô Thị Hồng",
    email: "hong.nt@vinuni.edu.vn",
    role: "resident",
    user_group: "sensitive",
    organization: "Vinhomes Ocean Park",
    region: "Vinhomes Ocean Park",
    status: "active",
    last_active_at: hoursAgo(30),
    created_at: daysAgo(20),
    avatar_initials: "NH",
  },
  {
    user_id: "USR-009",
    full_name: "Trịnh Minh Khôi",
    email: "khoi.tm@vinuni.edu.vn",
    role: "resident",
    user_group: "normal",
    organization: "Vinhomes Ocean Park",
    region: "Vinhomes Ocean Park",
    status: "disabled",
    last_active_at: daysAgo(45),
    created_at: daysAgo(90),
    avatar_initials: "TK",
  },
];

export const DEMO_USER_AUDIT: AdminAuditEntry[] = [
  {
    id: "AUD-U01",
    time: hoursAgo(0.5),
    actor: "Lê Thị D (admin)",
    action: "USER_UPDATE_ROLE",
    target: "USR-004 · Phạm Quốc Bảo",
    outcome: "SUCCESS",
    correlation_id: "req-u-9001",
    detail: "Cập nhật vai trò sang manager",
  },
  {
    id: "AUD-U02",
    time: daysAgo(2),
    actor: "Lê Thị D (admin)",
    action: "USER_DISABLE",
    target: "USR-006 · Vũ Đức Long",
    outcome: "SUCCESS",
    correlation_id: "req-u-8831",
    detail: "Tài khoản bị vô hiệu hóa theo yêu cầu",
  },
  {
    id: "AUD-U03",
    time: daysAgo(3),
    actor: "Lê Thị D (admin)",
    action: "USER_INVITE",
    target: "USR-007 · Đỗ Mai Linh",
    outcome: "SUCCESS",
    correlation_id: "req-u-8722",
    detail: "Gửi lời mời vai trò manager",
  },
  {
    id: "AUD-U04",
    time: daysAgo(45),
    actor: "Hệ thống",
    action: "USER_DISABLE",
    target: "USR-009 · Trịnh Minh Khôi",
    outcome: "SUCCESS",
    correlation_id: "req-u-8105",
    detail: "Tự động vô hiệu hóa sau nhiều lần đăng nhập sai",
  },
];

let cachedCsrfToken: string | null = null;

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(^|;\\s*)(${name})=([^;]*)`));
  return match ? decodeURIComponent(match[3]) : null;
}

export async function fetchCsrfToken(): Promise<string> {
  const fromCookie = getCookie("airguard_csrf");
  if (fromCookie) {
    cachedCsrfToken = fromCookie;
    return fromCookie;
  }
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/auth/csrf`, {
      credentials: "include",
    });
    if (res.ok) {
      const data = await res.json();
      if (data.csrf_token) {
        cachedCsrfToken = data.csrf_token;
        return data.csrf_token;
      }
    }
  } catch (e) {
    console.warn("Failed to fetch CSRF token:", e);
  }
  return cachedCsrfToken || "";
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const method = (options.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCookie("airguard_csrf") || cachedCsrfToken || (await fetchCsrfToken());
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }
  }

  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`, {
      ...options,
      credentials: "include",
      headers,
    });

    if (!res.ok) {
      let errBody: any = null;
      try {
        errBody = await res.json();
      } catch {
        // Not JSON
      }
      const message = errBody?.message || `API Error ${res.status}: ${res.statusText}`;
      const err: any = new Error(message);
      err.status = res.status;
      err.code = errBody?.code;
      err.details = errBody?.details;
      err.request_id = errBody?.request_id || res.headers.get("x-request-id") || null;
      throw err;
    }
    return await res.json();
  } catch (err: any) {
    console.warn(`Fetch to ${endpoint} failed:`, err?.message);
    throw err;
  }
}

function mapProposal(request: Record<string, any>): Proposal {
  const rawEvidence = request.evidence ?? {};
  const rawControl =
    rawEvidence.control && typeof rawEvidence.control === "object" ? rawEvidence.control : {};
  const evidenceItems = Array.isArray(rawEvidence.items) ? rawEvidence.items : [];
  const currentEvidence = evidenceItems.find((item: Record<string, any>) => item.source_tool === "get_current_pm25") ?? {};
  const alertEvidence = evidenceItems.find((item: Record<string, any>) => item.source_tool === "get_active_alerts") ?? {};
  const evidence = {
    ...rawEvidence,
    aqi: rawEvidence.aqi ?? currentEvidence.aqi,
    aqi_category: rawEvidence.aqi_category ?? currentEvidence.aqi_category,
    pm25: rawEvidence.pm25 ?? currentEvidence.observed_value,
    co2: rawEvidence.co2 ?? currentEvidence.co2,
    noise_db: rawEvidence.noise_db ?? currentEvidence.noise_db,
    observed_at: rawEvidence.observed_at ?? currentEvidence.measured_at,
    severity: rawEvidence.severity ?? alertEvidence.severity,
    threshold: rawEvidence.threshold ?? alertEvidence.threshold_value,
  };
  const actionLabels: Record<string, string> = {
    notify_station_area_users: "Gửi cảnh báo đến người dân trong khu vực",
    ventilation_boost: "Tăng cường thông gió",
    air_purifier_on: "Bật hệ thống lọc không khí",
    eco_mode: "Đưa thiết bị về chế độ tiết kiệm",
  };
  const deviceId = request.device_id ?? rawControl.device_id ?? null;
  const proposedAction = request.proposed_action ?? rawControl.action;
  const rawDispatchStatus = request.dispatch_status ?? request.command_intent?.status;
  const dispatchStatus: Proposal["dispatch_status"] =
    rawDispatchStatus === "queued"
      ? "queued"
      : rawDispatchStatus === "pending" || rawDispatchStatus === "published"
        ? "pending"
        : rawDispatchStatus === "succeeded" || rawDispatchStatus === "acknowledged"
          ? "succeeded"
          : rawDispatchStatus === "failed" || rawDispatchStatus === "rejected"
            ? "failed"
            : rawDispatchStatus === "not_configured"
              ? "not_configured"
              : "unknown";
  return {
    proposal_id: request.request_id,
    station_id: request.station_id,
    request_type: request.request_type,
    device_id: deviceId,
    proposed_action: proposedAction,
    duration_minutes:
      request.duration_minutes ?? request.command_intent?.duration_minutes ?? rawControl.duration_minutes ?? null,
    severity: evidence.severity ?? "unknown",
    target: deviceId ?? request.station_id ?? "Không xác định",
    action: actionLabels[proposedAction] ?? proposedAction,
    rationale: request.reason ?? "Backend không cung cấp lý do.",
    status: request.status,
    created_at: request.created_at,
    created_by: request.created_by,
    evidence,
    version: request.version ?? 1,
    reviewed_by: request.reviewed_by,
    reviewed_at: request.reviewed_at,
    review_note: request.review_note,
    dispatch_status: dispatchStatus,
  };
}

async function downloadApiFile(endpoint: string): Promise<ReportExport> {
  const response = await fetchWithTimeout(`${API_BASE_URL}${endpoint}`, { credentials: "include" });
  if (!response.ok) {
    let errorBody: Record<string, any> | null = null;
    try {
      errorBody = await response.json();
    } catch {
      // The shared API error envelope may be unavailable for proxy-level failures.
    }
    const error: any = new Error(errorBody?.message || `API Error ${response.status}: ${response.statusText}`);
    error.status = response.status;
    error.code = errorBody?.code;
    error.details = errorBody?.details;
    throw error;
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const encodedFilename = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  const quotedFilename = disposition.match(/filename="?([^";]+)"?/i)?.[1];
  const filename = encodedFilename
    ? decodeURIComponent(encodedFilename)
    : quotedFilename || "airguard-report";
  return {
    blob: await response.blob(),
    filename,
    media_type: response.headers.get("Content-Type") ?? "application/octet-stream",
  };
}

export function normalizeSpatialHeatmapResponse(raw: any): SpatialHeatmapResponse {
  const contractError = (message: string): never => {
    throw new Error(`Spatial Heatmap API response contract failure: ${message}`);
  };
  const requireObject = (value: any, field: string): Record<string, any> => {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      contractError(`'${field}' must be an object.`);
    }
    return value;
  };
  const requireString = (value: any, field: string): string => {
    if (typeof value !== "string" || !value.trim()) {
      contractError(`'${field}' must be a non-empty string.`);
    }
    return value.trim();
  };
  const requireFinite = (value: any, field: string): number => {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      contractError(`'${field}' must be a finite number.`);
    }
    return value;
  };
  const requireInteger = (value: any, field: string): number => {
    const parsed = requireFinite(value, field);
    if (!Number.isInteger(parsed)) {
      contractError(`'${field}' must be an integer.`);
    }
    return parsed;
  };
  const requireTimestamp = (value: any, field: string): string => {
    const timestamp = requireString(value, field);
    if (!/(?:Z|[+-]\d{2}:\d{2})$/i.test(timestamp) || Number.isNaN(Date.parse(timestamp))) {
      contractError(`'${field}' must be a timezone-aware ISO-8601 timestamp.`);
    }
    return timestamp;
  };
  const requireStringArray = (value: any, field: string): string[] => {
    if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || !item.trim())) {
      contractError(`'${field}' must be an array of non-empty strings.`);
    }
    return value.map((item) => item.trim());
  };

  if (!raw || typeof raw !== "object") {
    contractError("response object is missing.");
  }

  const allowedMetrics = new Set(["aqi", "pm25", "co2", "noise_db", "temperature"]);
  if (typeof raw.metric !== "string" || !allowedMetrics.has(raw.metric)) {
    contractError("'metric' is unsupported.");
  }
  const unit = requireString(raw.unit, "unit");
  const forecastHour = requireInteger(raw.forecast_hour, "forecast_hour");
  if (forecastHour < 0 || forecastHour > 24) {
    contractError("'forecast_hour' must be between 0 and 24.");
  }

  if (raw.source !== "spatial_idw_dispersion_model") {
    contractError("'source' must be 'spatial_idw_dispersion_model'.");
  }
  const modelVersion = requireString(raw.model_version, "model_version");
  const generatedAt = requireTimestamp(raw.generated_at, "generated_at");
  const timestamp = requireTimestamp(raw.timestamp, "timestamp");
  const disclaimer = requireString(raw.disclaimer, "disclaimer");

  const windSpeed = requireFinite(raw.wind_speed_ms, "wind_speed_ms");
  const windDirection = requireInteger(raw.wind_direction_deg, "wind_direction_deg");
  if (windSpeed < 0 || windSpeed > 60) {
    contractError("'wind_speed_ms' must be between 0 and 60.");
  }
  if (windDirection < 0 || windDirection >= 360) {
    contractError("'wind_direction_deg' must be between 0 and 359.");
  }

  const rawModel = requireObject(raw.model, "model");
  const model = {
    name: requireString(rawModel.name, "model.name"),
    version: requireString(rawModel.version, "model.version"),
    grid_rows: requireInteger(rawModel.grid_rows, "model.grid_rows"),
    grid_columns: requireInteger(rawModel.grid_columns, "model.grid_columns"),
    power: requireFinite(rawModel.power, "model.power"),
    minimum_stations: requireInteger(rawModel.minimum_stations, "model.minimum_stations"),
  };
  if (
    model.version !== modelVersion ||
    model.grid_rows < 1 ||
    model.grid_columns < 1 ||
    model.power <= 0 ||
    model.minimum_stations < 3
  ) {
    contractError("'model' metadata is inconsistent or outside supported bounds.");
  }

  const rawExtent = requireObject(raw.extent, "extent");
  const extent = {
    south: requireFinite(rawExtent.south, "extent.south"),
    west: requireFinite(rawExtent.west, "extent.west"),
    north: requireFinite(rawExtent.north, "extent.north"),
    east: requireFinite(rawExtent.east, "extent.east"),
  };
  if (
    extent.south < -90 ||
    extent.north > 90 ||
    extent.west < -180 ||
    extent.east > 180 ||
    extent.south >= extent.north ||
    extent.west >= extent.east
  ) {
    contractError("'extent' bounds are invalid or unordered.");
  }

  const rawWeather = requireObject(raw.weather, "weather");
  const weather = {
    wind_speed_ms: requireFinite(rawWeather.wind_speed_ms, "weather.wind_speed_ms"),
    wind_direction_deg: requireInteger(rawWeather.wind_direction_deg, "weather.wind_direction_deg"),
    source: requireString(rawWeather.source, "weather.source"),
    observed_at: requireTimestamp(rawWeather.observed_at, "weather.observed_at"),
    is_fallback: rawWeather.is_fallback,
    is_stale: rawWeather.is_stale,
    assumptions: requireStringArray(rawWeather.assumptions, "weather.assumptions"),
  };
  if (
    typeof weather.is_fallback !== "boolean" ||
    weather.is_stale !== false ||
    weather.wind_speed_ms !== windSpeed ||
    weather.wind_direction_deg !== windDirection
  ) {
    contractError("'weather' must be fresh and consistent with top-level wind fields.");
  }

  const rawQuality = requireObject(raw.data_quality, "data_quality");
  const stationsRequired = requireInteger(rawQuality.stations_required, "data_quality.stations_required");
  const stationsUsed = requireStringArray(rawQuality.stations_used, "data_quality.stations_used");
  const exclusionReasonsRaw = requireObject(rawQuality.exclusion_reasons, "data_quality.exclusion_reasons");
  const exclusionReasons: Record<string, string[]> = {};
  for (const [stationId, reasons] of Object.entries(exclusionReasonsRaw)) {
    exclusionReasons[stationId] = requireStringArray(reasons, `data_quality.exclusion_reasons.${stationId}`);
  }
  const dataQuality = {
    status: rawQuality.status,
    stations_required: stationsRequired,
    stations_used: stationsUsed,
    stations_excluded: requireStringArray(rawQuality.stations_excluded, "data_quality.stations_excluded"),
    exclusion_reasons: exclusionReasons,
    station_sources: requireStringArray(rawQuality.station_sources, "data_quality.station_sources"),
    forecast_sources: requireStringArray(rawQuality.forecast_sources, "data_quality.forecast_sources"),
  };
  if (dataQuality.status !== "valid" || stationsRequired < 3 || stationsUsed.length < stationsRequired) {
    contractError("'data_quality' does not prove sufficient valid station coverage.");
  }

  if (!Array.isArray(raw.station_inputs) || raw.station_inputs.length < stationsRequired) {
    contractError("'station_inputs' must include every station required for interpolation.");
  }
  const stationInputs = raw.station_inputs.map((item: any, index: number) => {
    const station = requireObject(item, `station_inputs.${index}`);
    const forecastSource = station.forecast_source;
    if (forecastSource !== null && (typeof forecastSource !== "string" || !forecastSource.trim())) {
      contractError(`'station_inputs.${index}.forecast_source' must be null or a non-empty string.`);
    }
    return {
      station_id: requireString(station.station_id, `station_inputs.${index}.station_id`),
      lat: requireFinite(station.lat, `station_inputs.${index}.lat`),
      lon: requireFinite(station.lon, `station_inputs.${index}.lon`),
      value: requireFinite(station.value, `station_inputs.${index}.value`),
      source: requireString(station.source, `station_inputs.${index}.source`),
      observed_at: requireTimestamp(station.observed_at, `station_inputs.${index}.observed_at`),
      forecast_source: forecastSource === null ? null : forecastSource.trim(),
    };
  });

  if (!Array.isArray(raw.grid_points) || raw.grid_points.length < 1) {
    contractError("'grid_points' must be a non-empty array.");
  }
  const allowedLevels = new Set([
    "good",
    "moderate",
    "unhealthy_sensitive",
    "unhealthy",
    "very_unhealthy",
    "hazardous",
  ]);
  const gridPoints: SpatialHeatmapPoint[] = raw.grid_points.map((item: any, index: number) => {
    const point = requireObject(item, `grid_points.${index}`);
    const lat = requireFinite(point.lat, `grid_points.${index}.lat`);
    const lon = requireFinite(point.lon, `grid_points.${index}.lon`);
    const value = requireFinite(point.value, `grid_points.${index}.value`);
    const intensity = requireFinite(point.intensity, `grid_points.${index}.intensity`);
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180 || intensity < 0 || intensity > 1) {
      contractError(`'grid_points.${index}' coordinates or intensity are outside supported bounds.`);
    }
    if (typeof point.level !== "string" || !allowedLevels.has(point.level)) {
      contractError(`'grid_points.${index}.level' is unsupported.`);
    }
    return { lat, lon, value, intensity, level: point.level } as SpatialHeatmapPoint;
  });

  return {
    metric: raw.metric,
    unit,
    forecast_hour: forecastHour,
    generated_at: generatedAt,
    timestamp,
    source: raw.source,
    wind_speed_ms: windSpeed,
    wind_direction_deg: windDirection,
    model_version: modelVersion,
    model,
    extent,
    weather,
    data_quality: dataQuality,
    station_inputs: stationInputs,
    disclaimer,
    grid_points: gridPoints,
  };
}

export const api = {
  getStations: async (): Promise<Station[]> => {
    const data = await apiFetch<{ items: Station[] }>("/api/v1/stations");
    return data.items;
  },

  getStationCurrent: async (stationId: string): Promise<StationDetailData> => {
    return apiFetch<StationDetailData>(`/api/v1/stations/${stationId}/current`);
  },

  getStationHistory: async (
    stationId: string,
    hours = 24,
  ): Promise<HistoryPoint[]> => {
    const data = await apiFetch<{ items: Array<HistoryPoint & { measured_at?: string }> }>(
      `/api/v1/stations/${stationId}/history?hours=${hours}`,
    );
    return data.items.map((point) => ({ ...point, timestamp: point.measured_at ?? point.timestamp }));
  },

  getStationForecast: async (
    stationId: string,
    metric: ForecastData["metric"] = "pm25",
    hours = 3,
    model: "baseline" = "baseline",
  ): Promise<ForecastData> => {
    try {
      const data = await apiFetch<any>(
        `/api/v1/stations/${stationId}/forecast?metric=${metric}&hours=${hours}&model=${model}`,
      );
      if (!data.source || !data.model_name) {
        throw new Error("Forecast response is missing provenance");
      }
      const items = data.horizons ?? data.items ?? [];
      return {
        station_id: data.station_id,
        horizon_hours: items.length,
        metric: data.metric ?? metric,
        source: data.source,
        confidence: typeof data.confidence === "number" ? `${Math.round(data.confidence * 100)}%` : data.confidence,
        model_name: data.model_name,
        limitations: data.limitations ?? data.trend_summary,
        forecasts: items.map((item: any) => {
          const predicted = item.predicted_value ?? item.value ?? item.pm25 ?? null;
          const minVal = item.lower_bound ?? item.value_min ?? item.pm25_min ?? predicted;
          const maxVal = item.upper_bound ?? item.value_max ?? item.pm25_max ?? predicted;
          const h = item.hours_ahead ?? item.hour_offset ?? 1;
          return {
            horizon: `${h} hour`,
            pm25_predicted: predicted,
            range: [minVal, maxVal] as [number | null, number | null],
            value: predicted,
            value_min: minVal,
            value_max: maxVal,
            confidence: item.confidence,
          };
        }),
      };
    } catch {
      throw new Error("Forecast API unavailable");
    }
  },

  getAlerts: async (): Promise<Alert[]> => {
    const data = await apiFetch<{ items: Array<Record<string, any>> }>("/api/v1/alerts");
    return data.items.map((alert) => ({
      alert_id: alert.alert_id,
      station_id: alert.station_id,
      alert_type: alert.alert_type,
      severity: alert.severity,
      title: alert.title,
      message: alert.description ?? alert.title,
      observed_value: alert.observed_value,
      threshold: alert.threshold_value,
      recommendation: alert.recommendation,
      unit: alert.unit,
      status: alert.status,
      created_at: alert.created_at,
    }));
  },

  sendAgentMessage: async (
    message: string,
    contextStationId: string | null = null,
    userId: string = "demo-user",
    mapContext?: Record<string, any>,
    conversationId?: string | null,
  ): Promise<AgentResponse> => {
    // The public Demo Day map is intentionally usable without authentication.
    // AuthContext represents that state with an empty string, so normalize it to
    // the grounded demo profile required by the backend AgentChatRequest contract.
    const effectiveUserId = userId.trim() || "demo-user";
    const response = await apiFetch<any>("/api/v1/agent/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        station_id: contextStationId,
        user_id: effectiveUserId,
        map_context: mapContext,
        conversation_id: conversationId || undefined,
      }),
    });

    const { reply: textReply, summary: summaryStr, details: detailsStr } = extractAgentReply(response);

    return {
      reply: textReply,
      answer: { summary: summaryStr, details: detailsStr },
      intent: response.intent,
      map_intent: response.map_intent,
      time_context: response.time_context,
      data_mode: response.data_mode,
      evidence: response.evidence || response.sources || {},
      map_actions: response.map_actions || [],
      used_tools: response.used_tools || [],
      proposal_created: null,
      proposal_id: response.proposal_id ?? null,
      request_id: response.request_id,
      conversation_id: response.conversation_id,
      quality: response.quality ?? null,
      failure_reason: response.failure_reason ?? null,
      clarification: response.clarification ?? null,
      pending: response.pending ?? false,
    };
  },

  getProposals: async (_actor?: DemoApiActor): Promise<Proposal[]> => {
    const data = await apiFetch<{ items: Array<Record<string, any>> }>("/api/v1/approvals");
    return data.items.map(mapProposal);
  },

  approveProposal: async (proposalId: string, version: number, note: string, _actor?: DemoApiActor): Promise<Proposal> => {
    const data = await apiFetch<Record<string, any>>(`/api/v1/approvals/${proposalId}/approve`, {
      method: "POST",
      body: JSON.stringify({ version, note }),
    });
    return mapProposal(data);
  },

  quickApproveProposal: async (
    proposalId: string,
    version: number,
    note: string,
    idempotencyKey: string,
    _actor?: DemoApiActor,
  ): Promise<Proposal> => {
    const data = await apiFetch<Record<string, any>>(`/api/v1/approvals/${proposalId}/quick-approve`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ version, note }),
    });
    return mapProposal(data);
  },

  rejectProposal: async (proposalId: string, version: number, note: string, _actor?: DemoApiActor): Promise<Proposal> => {
    const data = await apiFetch<Record<string, any>>(`/api/v1/approvals/${proposalId}/reject`, {
      method: "POST",
      body: JSON.stringify({ version, note }),
    });
    return mapProposal(data);
  },

  getReports: async (type: ReportType): Promise<Report[]> => {
    const data = await apiFetch<{ items: Report[] }>(`/api/v1/reports?type=${encodeURIComponent(type)}`);
    return data.items;
  },

  getReport: async (reportId: string): Promise<Report> => {
    return apiFetch<Report>(`/api/v1/reports/${encodeURIComponent(reportId)}`);
  },

  generateReport: async (input: ReportGenerateRequest): Promise<Report> => {
    return apiFetch<Report>("/api/v1/reports/generate", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  exportReport: async (reportId: string, format: ReportExportFormat): Promise<ReportExport> => {
    return downloadApiFile(
      `/api/v1/reports/${encodeURIComponent(reportId)}/export?format=${encodeURIComponent(format)}`,
    );
  },

  getAuditLogs: async (_actor?: DemoApiActor): Promise<AuditLogEntry[]> => {
    const data = await apiFetch<{ items: Array<Record<string, any>> }>("/api/v1/audit-logs");
    return data.items.map((entry) => ({
      id: String(entry.audit_id),
      time: entry.created_at,
      actor: entry.actor_id ?? entry.actor_type,
      action: entry.action,
      target: [entry.entity_type, entry.entity_id].filter(Boolean).join(":"),
      outcome: entry.outcome,
      correlation_id: entry.correlation_id ?? "—",
    }));
  },

  // ---- Authentication Endpoints ----
  register: async (input: {
    email: string;
    password: string;
    full_name?: string;
    sensitivity_group?: string;
  }): Promise<{
    user_id: string;
    email: string;
    role: string;
    full_name: string;
    message: string;
    email_delivery_status?: EmailDeliveryStatus;
  }> => {
    return await apiFetch("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  login: async (input: {
    email: string;
    password: string;
  }): Promise<{ user: any; csrf_token: string; message: string }> => {
    const res = await apiFetch<{ user: any; csrf_token: string; message: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    });
    if (res.csrf_token) {
      cachedCsrfToken = res.csrf_token;
    }
    return res;
  },

  getMe: async (): Promise<{ user: any }> => {
    return await apiFetch<{ user: any }>("/api/v1/auth/me");
  },

  updateProfile: async (input: {
    full_name?: string;
    sensitivity_group?: "normal" | "sensitive" | "outdoor_sport";
  }): Promise<{ user: any }> => {
    return await apiFetch<{ user: any }>("/api/v1/auth/profile", {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  },

  logout: async (): Promise<{ success: boolean; message: string }> => {
    const res = await apiFetch<{ success: boolean; message: string }>("/api/v1/auth/logout", {
      method: "POST",
    });
    cachedCsrfToken = null;
    return res;
  },

  verifyEmail: async (token: string): Promise<{ success: boolean; message: string }> => {
    return await apiFetch<{ success: boolean; message: string }>("/api/v1/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  },

  resendVerification: async (email: string): Promise<{
    success: boolean;
    message: string;
    email_delivery_status?: EmailDeliveryStatus;
  }> => {
    return await apiFetch<{
      success: boolean;
      message: string;
      email_delivery_status?: EmailDeliveryStatus;
    }>("/api/v1/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  forgotPassword: async (email: string): Promise<{
    success: boolean;
    message: string;
    email_delivery_status?: EmailDeliveryStatus;
  }> => {
    return await apiFetch<{
      success: boolean;
      message: string;
      email_delivery_status?: EmailDeliveryStatus;
    }>("/api/v1/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  resetPassword: async (token: string, newPassword: string): Promise<{ success: boolean; message: string }> => {
    return await apiFetch<{ success: boolean; message: string }>("/api/v1/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  },

  getAuthConfig: async (): Promise<{ demo_mode: boolean; google_auth_enabled: boolean }> => {
    return await apiFetch<{ demo_mode: boolean; google_auth_enabled: boolean }>("/api/v1/auth/config");
  },

  getDemoStationOverrides: async (): Promise<{ demo_mode: boolean; overrides: Record<string, unknown> }> =>
    apiFetch("/api/v1/demo/station-overrides"),

  setDemoStationOverride: async (stationId: string, values: { pm25: number; co2: number; noise_db: number; temperature: number }): Promise<any> =>
    apiFetch(`/api/v1/demo/stations/${stationId}/override`, { method: "PUT", body: JSON.stringify(values) }),

  clearDemoStationOverride: async (stationId: string): Promise<any> =>
    apiFetch(`/api/v1/demo/stations/${stationId}/override`, { method: "DELETE" }),

  demoLogin: async (persona: "resident" | "sensitive" | "outdoor_sport" | "manager" | "admin"): Promise<{ user: any; csrf_token: string; message: string }> => {
    const res = await apiFetch<{ user: any; csrf_token: string; message: string }>("/api/v1/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ persona }),
    });
    if (res.csrf_token) {
      cachedCsrfToken = res.csrf_token;
    }
    return res;
  },

  getGoogleAuthStartUrl: (): string => {
    return `${API_BASE_URL}/api/v1/auth/google/start`;
  },

  // ---- Spatial Heatmap Endpoint ----
  getSpatialHeatmap: async (
    metric: string = "aqi",
    forecastHour: number = 0,
    signal?: AbortSignal,
  ): Promise<SpatialHeatmapResponse> => {
    const params = new URLSearchParams({
      metric: encodeURIComponent(metric),
      forecast_hour: String(forecastHour),
    });
    const data = await apiFetch<any>(
      `/api/v1/spatial/heatmap?${params.toString()}`,
      { signal },
    );
    return normalizeSpatialHeatmapResponse(data);
  },

  // ---- Quản lý người dùng ----
  getAdminUsers: async (): Promise<AdminUser[]> => {
    const data = await apiFetch<any>("/api/v1/users");
    return data.items || data;
  },
};

export const fetchStations = api.getStations;
export const fetchAlerts = api.getAlerts;
export const fetchStationHistory = api.getStationHistory;
export const fetchStationForecast = api.getStationForecast;
export const fetchProposals = async (_status?: string): Promise<{ items: Proposal[] }> => {
  const items = await api.getProposals();
  return { items };
};
export const approveProposal = (proposalId: string, version: number, note = "Approved by manager") =>
  api.approveProposal(proposalId, version, note);
export const rejectProposal = (proposalId: string, version: number, note = "Rejected by manager") =>
  api.rejectProposal(proposalId, version, note);
export const sendAgentChat = async (message: string, userId = "USR-002"): Promise<{ response: string; message?: string }> => {
  const res = await api.sendAgentMessage(message, null, userId);
  return { response: res.reply };
};


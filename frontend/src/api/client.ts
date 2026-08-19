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
} from "../types";

export interface DemoApiActor {
  userId: string;
  role: "manager";
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Fallback seed data if backend is offline during initial demo
export const FALLBACK_STATIONS: Station[] = [
  {
    station_id: "S01",
    station_name: "Trục Đa Tốn phía Tây Bắc",
    latitude: 21.0008,
    longitude: 105.9428,
    pm25: 42.5,
    aqi: 118, co2: 650, noise_db: 57, temperature: 31.1,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S02",
    station_name: "Khu căn hộ Sapphire",
    latitude: 20.9975,
    longitude: 105.943,
    pm25: 55.2,
    aqi: 149, co2: 720, noise_db: 65, temperature: 31.8,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S03",
    station_name: "Ven Hồ Ngọc Trai",
    latitude: 20.9953,
    longitude: 105.95,
    pm25: 66.1,
    aqi: 158, co2: 780, noise_db: 71, temperature: 32.4,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S04",
    station_name: "Khuôn viên VinUni",
    latitude: 20.9898,
    longitude: 105.9467,
    pm25: 28.4,
    aqi: 78, co2: 540, noise_db: 49, temperature: 30.2,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S05",
    station_name: "Khu Hải Âu phía Đông Nam",
    latitude: 20.991,
    longitude: 105.956,
    pm25: 35.9,
    aqi: 99, co2: 590, noise_db: 54, temperature: 30.8,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
];

export const FALLBACK_ALERTS: Alert[] = [
  {
    alert_id: "ALT-001",
    station_id: "S03",
    alert_type: "pm25_threshold",
    severity: "warning",
    title: "PM2.5 vượt ngưỡng",
    message: "PM2.5 vượt ngưỡng khuyến nghị (66.1 µg/m³)",
    observed_value: 66.1,
    threshold: 50.0,
    unit: "µg/m³",
    recommendation: "Theo dõi lần đo tiếp theo và hạn chế nguồn bụi gần khu vực.",
    status: "active",
    created_at: new Date(Date.now() - 15 * 60000).toISOString(),
  },
  {
    alert_id: "ALT-002",
    station_id: "S02",
    alert_type: "aqi_threshold",
    severity: "moderate",
    title: "AQI cần theo dõi",
    message: "PM2.5 tăng nhẹ khu vực Bãi đỗ xe",
    observed_value: 55.2,
    threshold: 50.0,
    unit: "",
    recommendation: "Theo dõi cập nhật AQI trước khi lên kế hoạch hoạt động ngoài trời kéo dài.",
    status: "active",
    created_at: new Date(Date.now() - 45 * 60000).toISOString(),
  },
];

export const FALLBACK_PROPOSALS: Proposal[] = [
  {
    proposal_id: "PROP-101",
    station_id: "S03",
    severity: "warning",
    target: "Khu vực Trục đường chính Ocean Park",
    action: "Khuyến nghị hạn chế hoạt động thể thao ngoài trời & phát cảnh báo",
    rationale: "PM2.5 đạt 66.1 µg/m³ duy trì trên 30 phút cùng độ ẩm cao.",
    status: "pending",
    version: 1,
    created_at: new Date(Date.now() - 20 * 60000).toISOString(),
    evidence: { aqi: 158, pm25: 66.1, co2: 780, noise_db: 71, temperature: 32.4 },
  },
];

export const FALLBACK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: "AUD-01",
    time: new Date(Date.now() - 120 * 60000).toISOString(),
    actor: "AI Agent",
    action: "CREATE_PROPOSAL",
    target: "PROP-101",
    outcome: "SUCCESS",
    correlation_id: "req-9912",
  },
  {
    id: "AUD-02",
    time: new Date(Date.now() - 300 * 60000).toISOString(),
    actor: "Manager (Demo)",
    action: "APPROVE_PROPOSAL",
    target: "PROP-099",
    outcome: "SUCCESS",
    correlation_id: "req-8810",
  },
];

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

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err: any) {
    console.warn(`Fetch to ${endpoint} failed:`, err?.message);
    throw err;
  }
}

function mapProposal(request: Record<string, any>): Proposal {
  const rawEvidence = request.evidence ?? {};
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
    temperature: rawEvidence.temperature ?? currentEvidence.temperature,
    observed_at: rawEvidence.observed_at ?? currentEvidence.measured_at,
    severity: rawEvidence.severity ?? alertEvidence.severity,
    threshold: rawEvidence.threshold ?? alertEvidence.threshold_value,
  };
  const legacyReason = "Fresh simulator PM2.5 data and an active backend alert require manager review.";
  const actionLabels: Record<string, string> = {
    notify_station_area_users: "Gửi cảnh báo đến người dân trong khu vực",
  };
  return {
    proposal_id: request.request_id,
    station_id: request.station_id,
    severity: evidence.severity ?? "warning",
    target: request.device_id ?? request.station_id,
    action: actionLabels[request.proposed_action] ?? request.proposed_action,
    rationale: request.reason === legacyReason
      ? "Dữ liệu simulator còn mới và đang có cảnh báo active từ backend; đề xuất cần Manager xem xét."
      : request.reason,
    status: request.status,
    created_at: request.created_at,
    evidence,
    version: request.version,
    reviewed_by: request.reviewed_by,
    reviewed_at: request.reviewed_at,
    review_note: request.review_note,
    dispatch_status: request.command_intent?.status ?? "not_configured",
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

  getStationForecast: async (stationId: string, metric: ForecastData["metric"] = "pm25"): Promise<ForecastData> => {
    try {
      const data = await apiFetch<any>(
        `/api/v1/stations/${stationId}/forecast?metric=${metric}`,
      );
      return {
        station_id: data.station_id,
        horizon_hours: data.items.length,
        metric: data.metric ?? metric,
        source: data.source,
        confidence: typeof data.confidence === "number" ? `${Math.round(data.confidence * 100)}%` : data.confidence,
        model_name: data.model_name,
        limitations: data.limitations,
        forecasts: data.items.map((item: { hour_offset: number; pm25?: number; pm25_min?: number; pm25_max?: number; value?: number; value_min?: number; value_max?: number; confidence?: number }) => ({
          horizon: `${item.hour_offset} hour`,
          pm25_predicted: item.pm25 ?? item.value ?? 0,
          range: [item.pm25_min ?? item.value_min ?? item.pm25 ?? item.value ?? 0, item.pm25_max ?? item.value_max ?? item.pm25 ?? item.value ?? 0] as [number, number],
          value: item.value ?? item.pm25,
          value_min: item.value_min ?? item.pm25_min,
          value_max: item.value_max ?? item.pm25_max,
          confidence: item.confidence,
        })),
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
    contextStationId: string | null,
    userId: string,
  ): Promise<AgentResponse> => {
    const response = await apiFetch<{
      answer: string;
      used_tools: string[];
      sources: Array<Record<string, unknown>>;
      request_id: string;
      trace: Record<string, unknown>;
      proposal_id?: string | null;
    }>("/api/v1/agent/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        station_id: contextStationId,
        user_id: userId,
      }),
    });
    return {
      reply: response.answer,
      used_tools: response.used_tools,
      evidence: {
        sources: response.sources,
        request_id: response.request_id,
        trace: response.trace,
      },
      proposal_created: null,
      proposal_id: response.proposal_id ?? null,
    };
  },

  getProposals: async (actor: DemoApiActor): Promise<Proposal[]> => {
    const data = await apiFetch<{ items: Array<Record<string, any>> }>("/api/v1/approvals", {
      headers: { "X-User-ID": actor.userId, "X-User-Role": actor.role },
    });
    return data.items.map(mapProposal);
  },

  approveProposal: async (proposalId: string, version: number, note: string, actor: DemoApiActor): Promise<Proposal> => {
    const data = await apiFetch<Record<string, any>>(`/api/v1/approvals/${proposalId}/approve`, {
      method: "POST",
      headers: { "X-User-ID": actor.userId, "X-User-Role": actor.role },
      body: JSON.stringify({ version, note }),
    });
    return mapProposal(data);
  },

  rejectProposal: async (proposalId: string, version: number, note: string, actor: DemoApiActor): Promise<Proposal> => {
    const data = await apiFetch<Record<string, any>>(`/api/v1/approvals/${proposalId}/reject`, {
      method: "POST",
      headers: { "X-User-ID": actor.userId, "X-User-Role": actor.role },
      body: JSON.stringify({ version, note }),
    });
    return mapProposal(data);
  },

  getAuditLogs: async (actor: DemoApiActor): Promise<AuditLogEntry[]> => {
    const data = await apiFetch<{ items: Array<Record<string, any>> }>("/api/v1/audit-logs", {
      headers: { "X-User-ID": actor.userId, "X-User-Role": actor.role },
    });
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

  // ---- P2 · Quản lý người dùng (demo client-side, contract pending) ----
  getAdminUsers: async (): Promise<AdminUser[]> => {
    try {
      const data = await apiFetch<any>("/api/v1/users");
      return data.items || data;
    } catch {
      return DEMO_ADMIN_USERS;
    }
  },
};

export const fetchStations = api.getStations;
export const fetchAlerts = api.getAlerts;
export const fetchStationHistory = api.getStationHistory;
export const fetchStationForecast = api.getStationForecast;
export const fetchProposals = async (_status?: string): Promise<{ items: Proposal[] }> => {
  try {
    const items = await api.getProposals({ userId: "USR-002", role: "manager" });
    return { items };
  } catch {
    return { items: FALLBACK_PROPOSALS };
  }
};
export const approveProposal = (proposalId: string, version: number, note = "Approved by manager") =>
  api.approveProposal(proposalId, version, note, { userId: "USR-002", role: "manager" });
export const rejectProposal = (proposalId: string, version: number, note = "Rejected by manager") =>
  api.rejectProposal(proposalId, version, note, { userId: "USR-002", role: "manager" });
export const sendAgentChat = async (message: string, userId = "USR-002"): Promise<{ response: string; message?: string }> => {
  const res = await api.sendAgentMessage(message, null, userId);
  return { response: res.reply };
};


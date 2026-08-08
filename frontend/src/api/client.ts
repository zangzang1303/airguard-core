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

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Fallback seed data if backend is offline during initial demo
export const FALLBACK_STATIONS: Station[] = [
  {
    station_id: "S01",
    station_name: "Cổng chính VinUni",
    latitude: 20.9441,
    longitude: 105.9439,
    pm25: 42.5,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S02",
    station_name: "Bãi đỗ xe trung tâm",
    latitude: 20.945,
    longitude: 105.9435,
    pm25: 55.2,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S03",
    station_name: "Trục đường chính Ocean Park",
    latitude: 20.9445,
    longitude: 105.9452,
    pm25: 66.1,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S04",
    station_name: "Công viên trung tâm",
    latitude: 20.9455,
    longitude: 105.9458,
    pm25: 28.4,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
  {
    station_id: "S05",
    station_name: "Khu thể thao ngoài trời",
    latitude: 20.9437,
    longitude: 105.9448,
    pm25: 35.9,
    status: "online",
    is_stale: false,
    updated_at: new Date().toISOString(),
  },
];

export const FALLBACK_ALERTS: Alert[] = [
  {
    alert_id: "ALT-001",
    station_id: "S03",
    severity: "warning",
    message: "PM2.5 vượt ngưỡng khuyến nghị (66.1 µg/m³)",
    observed_value: 66.1,
    threshold: 50.0,
    status: "active",
    created_at: new Date(Date.now() - 15 * 60000).toISOString(),
  },
  {
    alert_id: "ALT-002",
    station_id: "S02",
    severity: "moderate",
    message: "PM2.5 tăng nhẹ khu vực Bãi đỗ xe",
    observed_value: 55.2,
    threshold: 50.0,
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
    created_at: new Date(Date.now() - 20 * 60000).toISOString(),
    evidence: { pm25: 66.1, humidity: 78, wind_speed: 1.2 },
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
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API Error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err: any) {
    console.warn(`Fetch to ${endpoint} failed, fallback used:`, err?.message);
    throw err;
  }
}

export const api = {
  getStations: async (): Promise<Station[]> => {
    try {
      const data = await apiFetch<any>("/api/v1/stations");
      return data.items || data;
    } catch {
      return FALLBACK_STATIONS;
    }
  },

  getStationCurrent: async (stationId: string): Promise<StationDetailData> => {
    try {
      return await apiFetch<StationDetailData>(
        `/api/v1/stations/${stationId}/current`,
      );
    } catch {
      const st =
        FALLBACK_STATIONS.find((s) => s.station_id === stationId) ||
        FALLBACK_STATIONS[0];
      return {
        ...st,
        weather: {
          temperature: 29.5,
          humidity: 75,
          wind_speed: 2.1,
          source: "OpenWeatherMap/Simulator",
        },
        source: "simulator",
      };
    }
  },

  getStationHistory: async (
    stationId: string,
    hours = 24,
  ): Promise<HistoryPoint[]> => {
    try {
      return await apiFetch<HistoryPoint[]>(
        `/api/v1/stations/${stationId}/history?hours=${hours}`,
      );
    } catch {
      const now = Date.now();
      return Array.from({ length: 12 }, (_, i) => ({
        timestamp: new Date(
          now - (11 - i) * 2 * 3600 * 1000,
        ).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
        pm25: Math.round(25 + Math.random() * 45),
        temperature: 28 + Math.round(Math.random() * 4),
        humidity: 70 + Math.round(Math.random() * 15),
      }));
    }
  },

  getStationForecast: async (stationId: string): Promise<ForecastData> => {
    try {
      return await apiFetch<ForecastData>(
        `/api/v1/stations/${stationId}/forecast`,
      );
    } catch {
      const base = 40;
      return {
        station_id: stationId,
        horizon_hours: 3,
        source: "AirGuard AI Linear-Trend Model",
        confidence: "Cao (0.88)",
        forecasts: [
          {
            horizon: "1 giờ",
            pm25_predicted: base + 4,
            range: [base, base + 8],
          },
          {
            horizon: "2 giờ",
            pm25_predicted: base + 7,
            range: [base + 2, base + 12],
          },
          {
            horizon: "3 giờ",
            pm25_predicted: base + 2,
            range: [base - 5, base + 8],
          },
        ],
      };
    }
  },

  getAlerts: async (): Promise<Alert[]> => {
    try {
      const data = await apiFetch<any>("/api/v1/alerts");
      return data.items || data;
    } catch {
      return FALLBACK_ALERTS;
    }
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
    };
  },

  getProposals: async (): Promise<Proposal[]> => {
    try {
      const data = await apiFetch<any>("/api/v1/approvals");
      return data.items || data;
    } catch {
      return FALLBACK_PROPOSALS;
    }
  },

  approveProposal: async (proposalId: string, note = ""): Promise<any> => {
    try {
      return await apiFetch(`/api/v1/approvals/${proposalId}/approve`, {
        method: "POST",
        body: JSON.stringify({ note }),
      });
    } catch {
      return {
        status: "approved",
        proposal_id: proposalId,
        note,
        approved_at: new Date().toISOString(),
      };
    }
  },

  rejectProposal: async (proposalId: string, note: string): Promise<any> => {
    try {
      return await apiFetch(`/api/v1/approvals/${proposalId}/reject`, {
        method: "POST",
        body: JSON.stringify({ note }),
      });
    } catch {
      return {
        status: "rejected",
        proposal_id: proposalId,
        note,
        rejected_at: new Date().toISOString(),
      };
    }
  },

  getAuditLogs: async (): Promise<AuditLogEntry[]> => {
    try {
      const data = await apiFetch<any>("/api/v1/audit");
      return data.items || data;
    } catch {
      return FALLBACK_AUDIT_LOGS;
    }
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

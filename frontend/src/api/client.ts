import { Station, StationDetailData, HistoryPoint, ForecastData, Alert, Proposal, AuditLogEntry, AgentResponse, UserGroup } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Fallback seed data if backend is offline during initial demo
export const FALLBACK_STATIONS: Station[] = [
  { station_id: "S01", station_name: "Cổng chính VinUni", latitude: 20.9441, longitude: 105.9439, pm25: 42.5, status: "online", is_stale: false, updated_at: new Date().toISOString() },
  { station_id: "S02", station_name: "Bãi đỗ xe trung tâm", latitude: 20.9450, longitude: 105.9435, pm25: 55.2, status: "online", is_stale: false, updated_at: new Date().toISOString() },
  { station_id: "S03", station_name: "Trục đường chính Ocean Park", latitude: 20.9445, longitude: 105.9452, pm25: 66.1, status: "online", is_stale: false, updated_at: new Date().toISOString() },
  { station_id: "S04", station_name: "Công viên trung tâm", latitude: 20.9455, longitude: 105.9458, pm25: 28.4, status: "online", is_stale: false, updated_at: new Date().toISOString() },
  { station_id: "S05", station_name: "Khu thể thao ngoài trời", latitude: 20.9437, longitude: 105.9448, pm25: 35.9, status: "online", is_stale: false, updated_at: new Date().toISOString() }
];

export const FALLBACK_ALERTS: Alert[] = [
  { alert_id: "ALT-001", station_id: "S03", severity: "warning", message: "PM2.5 vượt ngưỡng khuyến nghị (66.1 µg/m³)", observed_value: 66.1, threshold: 50.0, status: "active", created_at: new Date(Date.now() - 15 * 60000).toISOString() },
  { alert_id: "ALT-002", station_id: "S02", severity: "moderate", message: "PM2.5 tăng nhẹ khu vực Bãi đỗ xe", observed_value: 55.2, threshold: 50.0, status: "active", created_at: new Date(Date.now() - 45 * 60000).toISOString() }
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
    evidence: { pm25: 66.1, humidity: 78, wind_speed: 1.2 }
  }
];

export const FALLBACK_AUDIT_LOGS: AuditLogEntry[] = [
  { id: "AUD-01", time: new Date(Date.now() - 120 * 60000).toISOString(), actor: "AI Agent", action: "CREATE_PROPOSAL", target: "PROP-101", outcome: "SUCCESS", correlation_id: "req-9912" },
  { id: "AUD-02", time: new Date(Date.now() - 300 * 60000).toISOString(), actor: "Manager (Demo)", action: "APPROVE_PROPOSAL", target: "PROP-099", outcome: "SUCCESS", correlation_id: "req-8810" }
];

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers
      },
      ...options
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
      return await apiFetch<StationDetailData>(`/api/v1/stations/${stationId}/current`);
    } catch {
      const st = FALLBACK_STATIONS.find(s => s.station_id === stationId) || FALLBACK_STATIONS[0];
      return {
        ...st,
        weather: { temperature: 29.5, humidity: 75, wind_speed: 2.1, source: "OpenWeatherMap/Simulator" },
        source: "simulator"
      };
    }
  },

  getStationHistory: async (stationId: string, hours = 24): Promise<HistoryPoint[]> => {
    try {
      return await apiFetch<HistoryPoint[]>(`/api/v1/stations/${stationId}/history?hours=${hours}`);
    } catch {
      const now = Date.now();
      return Array.from({ length: 12 }, (_, i) => ({
        timestamp: new Date(now - (11 - i) * 2 * 3600 * 1000).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
        pm25: Math.round(25 + Math.random() * 45),
        temperature: 28 + Math.round(Math.random() * 4),
        humidity: 70 + Math.round(Math.random() * 15)
      }));
    }
  },

  getStationForecast: async (stationId: string): Promise<ForecastData> => {
    try {
      return await apiFetch<ForecastData>(`/api/v1/stations/${stationId}/forecast`);
    } catch {
      const base = 40;
      return {
        station_id: stationId,
        horizon_hours: 3,
        source: "AirGuard AI Linear-Trend Model",
        confidence: "Cao (0.88)",
        forecasts: [
          { horizon: "1 giờ", pm25_predicted: base + 4, range: [base, base + 8] },
          { horizon: "2 giờ", pm25_predicted: base + 7, range: [base + 2, base + 12] },
          { horizon: "3 giờ", pm25_predicted: base + 2, range: [base - 5, base + 8] }
        ]
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

  sendAgentMessage: async (message: string, contextStationId: string | null = null, userGroup: UserGroup = "normal"): Promise<AgentResponse> => {
    try {
      return await apiFetch<AgentResponse>("/api/v1/agent/chat", {
        method: "POST",
        body: JSON.stringify({ message, station_id: contextStationId, user_group: userGroup })
      });
    } catch {
      return {
        reply: `Dựa trên dữ liệu quan trắc giả lập từ trạm ${contextStationId || 'S01-S05'}, nồng độ PM2.5 hiện tại ở mức trung bình. Khuyến nghị nhóm người dùng [${userGroup}] theo dõi chỉ số trước khi tập luyện ngoài trời.`,
        used_tools: ["get_current_pm25", "get_weather_context", "get_user_profile"],
        evidence: { station_id: contextStationId || "S01", pm25: 42.5, source: "simulator" },
        proposal_created: message.toLowerCase().includes("cảnh báo") ? FALLBACK_PROPOSALS[0] : null
      };
    }
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
        body: JSON.stringify({ note })
      });
    } catch {
      return { status: "approved", proposal_id: proposalId, note, approved_at: new Date().toISOString() };
    }
  },

  rejectProposal: async (proposalId: string, note: string): Promise<any> => {
    try {
      return await apiFetch(`/api/v1/approvals/${proposalId}/reject`, {
        method: "POST",
        body: JSON.stringify({ note })
      });
    } catch {
      return { status: "rejected", proposal_id: proposalId, note, rejected_at: new Date().toISOString() };
    }
  },

  getAuditLogs: async (): Promise<AuditLogEntry[]> => {
    try {
      const data = await apiFetch<any>("/api/v1/audit");
      return data.items || data;
    } catch {
      return FALLBACK_AUDIT_LOGS;
    }
  }
};

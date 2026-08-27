import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Check,
  ChevronRight,
  CircleDot,
  Clock3,
  Cpu,
  MapPin,
  RefreshCw,
  ShieldAlert,
  Wifi,
  X,
} from "lucide-react";
import {
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../../api/client";
import { getPm25Severity } from "../../components/common/DataQualityBadge";
import { useAuth } from "../../context/AuthContext";
import { Alert, HistoryPoint, Proposal, Station } from "../../types";
import { ReportViewer } from "./ReportViewer";
import "./AdminDashboard.css";

const MAP_POSITIONS = [
  { left: "23%", top: "62%" },
  { left: "51%", top: "39%" },
  { left: "74%", top: "65%" },
  { left: "34%", top: "31%" },
  { left: "82%", top: "27%" },
];

const CHART_COLORS = ["#3b82f6", "#f97316", "#a855f7"];

const formatClock = (value?: string) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
};

const severityText: Record<Alert["severity"], string> = {
  good: "Tốt",
  moderate: "Trung bình",
  warning: "Ô nhiễm",
  critical: "Nghiêm trọng",
};

interface ChartRow {
  time: string;
  [stationId: string]: number | string;
}

const mergeHistory = (series: Array<{ stationId: string; points: HistoryPoint[] }>): ChartRow[] => {
  const maxLength = Math.max(0, ...series.map((item) => item.points.length));
  return Array.from({ length: maxLength }, (_, index) => {
    const row: ChartRow = { time: series[0]?.points[index]?.timestamp ?? `${index + 1}` };
    series.forEach(({ stationId, points }) => {
      const point = points[index];
      if (point) row[stationId] = point.pm25;
    });
    return row;
  });
};

export const AdminDashboard: React.FC = () => {
  const { navigateTo, setPendingApprovalsCount } = useAuth();
  const [stations, setStations] = useState<Station[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [chartData, setChartData] = useState<ChartRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stationData, alertData, proposalData] = await Promise.all([
        api.getStations(),
        api.getAlerts(),
        Promise.resolve([] as Proposal[]),
      ]);
      const mainStations = stationData.slice(0, 3);
      const histories = await Promise.all(mainStations.map(async (station) => ({
        stationId: station.station_id,
        points: await api.getStationHistory(station.station_id, 24),
      })));
      setStations(stationData);
      setAlerts(alertData);
      setProposals(proposalData);
      setChartData(mergeHistory(histories));
      setPendingApprovalsCount(proposalData.filter((proposal) => proposal.status === "pending").length);
      setLastUpdated(new Date());
    } catch {
      setError("Không thể tải đầy đủ dữ liệu quản trị. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const validStations = useMemo(
    () => stations.filter((station) => station.pm25 !== null && station.status === "online" && !station.is_stale),
    [stations],
  );
  const averagePm25 = validStations.length
    ? Math.round(validStations.reduce((sum, station) => sum + Number(station.pm25), 0) / validStations.length)
    : null;
  const onlineCount = stations.filter((station) => station.status === "online" && !station.is_stale).length;
  const staleCount = stations.filter((station) => station.is_stale).length;
  const offlineCount = stations.filter((station) => station.status === "offline").length;
  const pendingProposals = proposals.filter((proposal) => proposal.status === "pending");
  const currentProposal = pendingProposals[0] ?? null;
  const deviceData = [
    { name: "Trực tuyến", value: onlineCount, color: "#10b981" },
    { name: "Gián đoạn", value: staleCount, color: "#f59e0b" },
    { name: "Ngoại tuyến", value: offlineCount, color: "#64748b" },
  ];

  return (
    <div className="admin-dashboard">
      <header className="admin-dashboard__header">
        <div>
          <h1>Tổng quan hệ thống</h1>
          <p>Cập nhật lần cuối: {lastUpdated ? formatClock(lastUpdated.toISOString()) : "—"} · VinUni / Vinhomes Ocean Park</p>
        </div>
        <button type="button" className="admin-primary-button" onClick={loadDashboard} disabled={loading}>
          <RefreshCw size={16} className={loading ? "is-spinning" : ""} />
          {loading ? "Đang làm mới" : "Làm mới"}
        </button>
      </header>

      <div className="admin-simulator-note" role="note">
        <CircleDot size={15} />
        <span><strong>SIMULATOR</strong> · Dữ liệu giả lập cho MVP, không phải quan trắc chính thức và không dùng cho quyết định y tế hoặc pháp lý.</span>
      </div>

      {error && (
        <div className="admin-error" role="alert">
          <AlertTriangle size={17} /><span>{error}</span>
          <button type="button" onClick={loadDashboard}>Thử lại</button>
        </div>
      )}

      <section className="admin-kpis" aria-label="Chỉ số tổng quan">
        <article className="admin-kpi admin-kpi--success">
          <div className="admin-kpi__top"><span>Cảm biến đang hoạt động</span><i><Activity size={19} /></i></div>
          <strong>{loading ? "—" : `${onlineCount} / ${stations.length}`}</strong>
          <small>{onlineCount === stations.length && stations.length > 0 ? "Tất cả trạm đang kết nối" : `${stations.length - onlineCount} trạm cần kiểm tra`}</small>
        </article>
        <article className="admin-kpi admin-kpi--info">
          <div className="admin-kpi__top"><span>Trạng thái kết nối</span><i><Wifi size={19} /></i></div>
          <strong>{onlineCount > 0 ? "Trực tuyến" : "Gián đoạn"}</strong>
          <small>{onlineCount} Online · {staleCount} Gián đoạn · {offlineCount} Ngoại tuyến</small>
        </article>
        <article className="admin-kpi admin-kpi--warning">
          <div className="admin-kpi__top"><span>PM2.5 trung bình</span><i><Cpu size={19} /></i></div>
          <strong>{averagePm25 ?? "—"}<em>{averagePm25 !== null ? " µg/m³" : ""}</em></strong>
          <small>{validStations.length} trạm có dữ liệu hợp lệ</small>
        </article>
        <article className="admin-kpi admin-kpi--danger">
          <div className="admin-kpi__top"><span>Đề xuất HITL chờ duyệt</span><i><ShieldAlert size={19} /></i></div>
          <strong>{loading ? "—" : `${pendingProposals.length} đề xuất`}</strong>
          <small>{pendingProposals.length ? "Cần kiểm tra evidence" : "Hàng chờ đang trống"}</small>
        </article>
      </section>

      <section className="admin-overview-grid">
        <article className="admin-card admin-map-panel">
          <header className="admin-card__header">
            <div><MapPin size={17} /><h2>Bản đồ trạm quan trắc</h2></div>
            <span>{stations.length} trạm · DEMO</span>
          </header>
          <div className="admin-map-canvas">
            <div className="admin-map-canvas__grid" />
            <span className="admin-map-place admin-map-place--school">Trường học</span>
            <span className="admin-map-place admin-map-place--park">Công viên</span>
            <span className="admin-map-place admin-map-place--mall">Trung tâm TM</span>
            <strong className="admin-map-label">VINUNI / VINHOMES OCEAN PARK · SƠ ĐỒ KHU VỰC [SIMULATOR]</strong>
            {stations.map((station, index) => {
              const severity = getPm25Severity(station.pm25);
              const color = station.status === "offline" ? "#64748b" : station.is_stale ? "#f59e0b" : severity.color;
              const position = MAP_POSITIONS[index % MAP_POSITIONS.length];
              return (
                <button
                  key={station.station_id}
                  type="button"
                  className="admin-map-marker"
                  style={{ ...position, "--marker-color": color } as React.CSSProperties}
                  aria-label={`${station.station_id} ${station.station_name}, PM2.5 ${station.pm25 ?? "không khả dụng"}`}
                  onClick={() => navigateTo("station-detail", { stationId: station.station_id })}
                >
                  <span>{station.station_id}</span>
                  <small>{station.pm25 ?? "—"}</small>
                </button>
              );
            })}
          </div>
          <div className="admin-map-legend">
            <strong>Chú giải trạng thái</strong>
            <span><i style={{ background: "#10b981" }} />Tốt/Online</span>
            <span><i style={{ background: "#f59e0b" }} />Gián đoạn</span>
            <span><i style={{ background: "#f97316" }} />Ô nhiễm</span>
            <span><i style={{ background: "#64748b" }} />Ngoại tuyến</span>
          </div>
        </article>

        <article className="admin-card admin-hitl-panel">
          <header className="admin-card__header">
            <div><ShieldAlert size={17} /><h2>Đề xuất HITL đang chờ</h2></div>
            <span>{pendingProposals.length}</span>
          </header>
          {loading ? (
            <div className="admin-panel-state"><RefreshCw className="is-spinning" size={20} />Đang tải đề xuất…</div>
          ) : currentProposal ? (
            <div className="admin-hitl-content">
              <div className="admin-hitl-meta"><code>{currentProposal.proposal_id}</code><span>Đề xuất từ AI Agent</span></div>
              <blockquote>“{currentProposal.action}”</blockquote>
              <dl>
                <div><dt>PM2.5 evidence</dt><dd>{currentProposal.evidence?.pm25 ?? "—"} µg/m³</dd></div>
                <div><dt>Khu vực</dt><dd>{currentProposal.station_id}</dd></div>
                <div><dt>Mức độ</dt><dd>{currentProposal.severity}</dd></div>
                <div><dt>Thời gian tạo</dt><dd>{formatClock(currentProposal.created_at)}</dd></div>
              </dl>
              <p>{currentProposal.rationale}</p>
              <div className="admin-hitl-actions">
                <button type="button" className="admin-approve" onClick={() => navigateTo("approvals")}><Check size={16} />Phê duyệt</button>
                <button type="button" className="admin-reject" onClick={() => navigateTo("approvals")}><X size={16} />Từ chối</button>
              </div>
            </div>
          ) : (
            <div className="admin-panel-state"><Check size={20} />Không có đề xuất đang chờ.</div>
          )}
        </article>
      </section>

      <section className="admin-analytics-grid">
        <article className="admin-card admin-chart-card">
          <header className="admin-card__header">
            <div><Activity size={17} /><h2>Xu hướng PM2.5 theo giờ</h2></div>
            <span>24 giờ · 3 trạm chính</span>
          </header>
          <div className="admin-line-chart" aria-label="Biểu đồ xu hướng PM2.5">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 12, right: 18, left: -18, bottom: 4 }}>
                  <CartesianGrid stroke="rgba(148,163,184,.12)" vertical={false} />
                  <XAxis dataKey="time" stroke="#718096" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} minTickGap={30} />
                  <YAxis stroke="#718096" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} unit=" µg" />
                  <Tooltip contentStyle={{ background: "#111d2f", border: "1px solid rgba(148,163,184,.18)", borderRadius: 10, fontSize: 11 }} />
                  {stations.slice(0, 3).map((station, index) => (
                    <Line key={station.station_id} type="monotone" dataKey={station.station_id} stroke={CHART_COLORS[index]} strokeWidth={2.4} dot={false} activeDot={{ r: 4 }} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            ) : <div className="admin-panel-state">Chưa có dữ liệu lịch sử.</div>}
          </div>
          <div className="admin-chart-legend">
            {stations.slice(0, 3).map((station, index) => <span key={station.station_id}><i style={{ background: CHART_COLORS[index] }} />{station.station_id} {station.station_name}</span>)}
          </div>
        </article>

        <article className="admin-card admin-device-card">
          <header className="admin-card__header">
            <div><Cpu size={17} /><h2>Trạng thái thiết bị</h2></div>
            <span>{stations.length} cảm biến</span>
          </header>
          <div className="admin-device-chart">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={deviceData} dataKey="value" innerRadius={62} outerRadius={82} paddingAngle={4} stroke="none">
                  {deviceData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#111d2f", border: "1px solid rgba(148,163,184,.18)", borderRadius: 10, fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="admin-device-chart__center"><strong>{stations.length}</strong><span>Tổng trạm</span></div>
          </div>
          <div className="admin-device-legend">
            {deviceData.map((entry) => <div key={entry.name}><span><i style={{ background: entry.color }} />{entry.name}</span><strong>{entry.value}</strong></div>)}
          </div>
        </article>
      </section>

      <section className="admin-card admin-alert-log">
        <header className="admin-card__header">
          <div><Clock3 size={17} /><h2>Nhật ký cảnh báo</h2></div>
          <button type="button" onClick={() => navigateTo("alerts")}>Xem tất cả <ChevronRight size={15} /></button>
        </header>
        <div className="admin-table-wrap">
          <table>
            <thead><tr><th>Thời gian</th><th>Mã trạm</th><th>PM2.5</th><th>Mức độ</th><th>Trạng thái</th></tr></thead>
            <tbody>
              {alerts.slice(0, 6).map((alert) => (
                <tr key={alert.alert_id}>
                  <td>{formatClock(alert.created_at)}</td>
                  <td><strong>{alert.station_id}</strong></td>
                  <td>{alert.observed_value ?? "—"} µg/m³</td>
                  <td><span className={`admin-severity admin-severity--${alert.severity}`}>{severityText[alert.severity]}</span></td>
                  <td><span className={`admin-alert-status admin-alert-status--${alert.status}`}>{alert.status === "active" ? "Đang xử lý" : "Đã giải quyết"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && alerts.length === 0 && <div className="admin-panel-state">Không có cảnh báo phù hợp.</div>}
        </div>
      </section>

      {/* Periodic Environment Report Viewer Section */}
      <section style={{ marginTop: "24px" }}>
        <ReportViewer />
      </section>
    </div>
  );
};


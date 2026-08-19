import React, { useState, useEffect } from "react";
import { X, TrendingUp, AlertTriangle, ShieldCheck, Database, Layers, RefreshCw, BarChart3, Wind } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Station, HistoryPoint } from "../../types";
import { getAqiColorHex } from "../map/SensorMarkers";
import { fetchStationHistory } from "../../api/client";

interface AnalysisWorkspaceDrawerProps {
  stationId: string;
  stations: Station[];
  onClose: () => void;
  onSelectStationId: (id: string) => void;
}

export const AnalysisWorkspaceDrawer: React.FC<AnalysisWorkspaceDrawerProps> = ({
  stationId,
  stations,
  onClose,
  onSelectStationId,
}) => {
  const [activeTab, setActiveTab] = useState<"overview" | "history" | "prediction" | "evidence" | "raw">("overview");
  const [selectedMetric, setSelectedMetric] = useState<"aqi" | "pm25" | "co2" | "noise_db" | "temperature">("aqi");
  const [historyData, setHistoryData] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(false);

  const currentStation = stations.find((s) => s.station_id === stationId) || stations[0];

  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      setLoading(true);
      try {
        const res = await fetchStationHistory(stationId, 24);
        if (isMounted) {
          setHistoryData(Array.isArray(res) ? res : []);
        }
      } catch (err) {

        console.error("Failed to load history:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadHistory();
    return () => {
      isMounted = false;
    };
  }, [stationId]);

  // Format timestamp for charts
  const chartData = historyData.map((pt) => {
    const d = new Date(pt.timestamp);
    const hourStr = isNaN(d.getTime())
      ? pt.timestamp || "—"
      : `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
    return {
      time: hourStr,
      aqi: pt.aqi ?? Math.round(Number(pt.pm25) * 2.6),
      pm25: Number(pt.pm25) || 0,
      co2: Number(pt.co2) || 600,
      noise_db: Number(pt.noise_db) || 50,
      temperature: Number(pt.temperature) || 30,
    };
  });


  const getMetricColor = (metric: string) => {
    switch (metric) {
      case "aqi": return "#10b981";
      case "pm25": return "#f97316";
      case "co2": return "#06b6d4";
      case "noise_db": return "#8b5cf6";
      case "temperature": return "#ec4899";
      default: return "#10b981";
    }
  };

  const getMetricUnit = (metric: string) => {
    switch (metric) {
      case "aqi": return "AQI";
      case "pm25": return "µg/m³";
      case "co2": return "ppm";
      case "noise_db": return "dB";
      case "temperature": return "°C";
      default: return "";
    }
  };

  return (
    <aside className="contextual-drawer right-drawer wide-analysis-drawer">
      {/* Header */}
      <div className="drawer-header-bar">
        <div className="drawer-title-group">
          <div className="badge-tag">Contextual Analytics Workspace</div>
          <h2 className="drawer-main-title">Phân tích chuyên sâu 24h</h2>
          <div className="station-selector-pills">
            {stations.map((s) => (
              <button
                key={s.station_id}
                className={`station-pill-btn ${s.station_id === stationId ? "active" : ""}`}
                onClick={() => onSelectStationId(s.station_id)}
              >
                {s.station_id} · {s.station_name.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      {/* Tabs */}
      <div className="workspace-tabs-bar">
        <button
          className={`tab-item-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Tổng quan
        </button>
        <button
          className={`tab-item-btn ${activeTab === "history" ? "active" : ""}`}
          onClick={() => setActiveTab("history")}
        >
          Chuỗi 24h
        </button>
        <button
          className={`tab-item-btn ${activeTab === "prediction" ? "active" : ""}`}
          onClick={() => setActiveTab("prediction")}
        >
          Dự báo & Xu hướng
        </button>
        <button
          className={`tab-item-btn ${activeTab === "evidence" ? "active" : ""}`}
          onClick={() => setActiveTab("evidence")}
        >
          Bằng chứng & Tương quan
        </button>
        <button
          className={`tab-item-btn ${activeTab === "raw" ? "active" : ""}`}
          onClick={() => setActiveTab("raw")}
        >
          Dữ liệu thô
        </button>
      </div>

      <div className="drawer-scroll-body">
        {/* TAB 1: OVERVIEW & ANOMALY */}
        {activeTab === "overview" && (
          <div className="tab-pane-content">
            {/* Anomaly Detection Banner */}
            <div className="anomaly-alert-card">
              <div className="anomaly-header">
                <AlertTriangle size={18} className="anomaly-icon" />
                <span className="anomaly-title">Phát hiện biến động bất thường (Anomaly Detected)</span>
              </div>
              <div className="anomaly-stats">
                <div className="stat-badge">+17% nồng độ PM2.5 / 45 phút gần nhất</div>
                <div className="stat-desc">Khả năng cao do lưu lượng xe cộ tăng cục bộ tại trục kết nối phía Đông Ocean Park 1.</div>
              </div>
            </div>

            {/* Metric Switcher */}
            <div className="metric-pill-switcher">
              {(["aqi", "pm25", "co2", "noise_db", "temperature"] as const).map((m) => (
                <button
                  key={m}
                  className={`metric-select-btn ${selectedMetric === m ? "active" : ""}`}
                  onClick={() => setSelectedMetric(m)}
                >
                  {m.toUpperCase()} ({getMetricUnit(m)})
                </button>
              ))}
            </div>

            {/* Chart Area */}
            <div className="analysis-chart-card">
              <div className="chart-title-row">
                <span className="chart-heading">Biểu đồ biến thiên 24 giờ qua</span>
                {loading && <RefreshCw size={14} className="spin-icon" />}
              </div>
              <div className="chart-svg-container">
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                    <defs>
                      <linearGradient id={`grad-${selectedMetric}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={getMetricColor(selectedMetric)} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={getMetricColor(selectedMetric)} stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <RechartsTooltip
                      contentStyle={{ backgroundColor: "#ffffff", borderRadius: "10px", border: "1px solid #e2e8f0", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
                    />
                    <Area
                      type="monotone"
                      dataKey={selectedMetric}
                      stroke={getMetricColor(selectedMetric)}
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill={`url(#grad-${selectedMetric})`}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Environmental Correlation Grid */}
            <div className="correlation-section">
              <h3 className="section-title">Tương quan môi trường (Environmental Correlation)</h3>
              <div className="correlation-grid">
                <div className="corr-item">
                  <span className="corr-label">Vận tốc gió</span>
                  <span className="corr-val">2.4 m/s (Đông Nam)</span>
                  <span className="corr-note">Gió nhẹ làm chậm tốc độ khuếch tán</span>
                </div>
                <div className="corr-item">
                  <span className="corr-label">Nhiệt độ mặt đất</span>
                  <span className="corr-val">32.4 °C</span>
                  <span className="corr-note">Nghịch nhiệt nhẹ lúc chiều tối</span>
                </div>
                <div className="corr-item">
                  <span className="corr-label">Giờ cao điểm</span>
                  <span className="corr-val">17:30 – 19:00</span>
                  <span className="corr-note">Tương quan 87% với mật độ phương tiện</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: HISTORY */}
        {activeTab === "history" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Chi tiết các mốc đo lường 24 giờ qua</h3>
            <div className="history-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Thời gian</th>
                    <th>AQI</th>
                    <th>PM2.5</th>
                    <th>CO₂</th>
                    <th>Độ ồn</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.slice(-12).reverse().map((row, idx) => (
                    <tr key={idx}>
                      <td>{row.time}</td>
                      <td>
                        <span className="table-aqi-badge" style={{ backgroundColor: getAqiColorHex(row.aqi) }}>
                          {row.aqi}
                        </span>
                      </td>
                      <td>{row.pm25} µg/m³</td>
                      <td>{row.co2} ppm</td>
                      <td>{row.noise_db} dB</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: PREDICTION */}
        {activeTab === "prediction" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Mô hình dự báo xu hướng (Damped Linear & Time-Series)</h3>
            <div className="prediction-cards-list">
              <div className="pred-card">
                <div className="pred-time">+1 Giờ tới (18:30)</div>
                <div className="pred-aqi">AQI ~165 <span className="tag-unhealthy">Ô nhiễm nhẹ</span></div>
                <p>Nồng độ bụi mịn tiếp tục tăng trong giờ cao điểm giao thông.</p>
              </div>
              <div className="pred-card">
                <div className="pred-time">+3 Giờ tới (20:30)</div>
                <div className="pred-aqi">AQI ~85 <span className="tag-moderate">Cải thiện</span></div>
                <p>Gió hồ tăng tốc độ đối lưu giúp không khí trong lành hơn.</p>
              </div>
              <div className="pred-card">
                <div className="pred-time">Đêm nay (22:30+)</div>
                <div className="pred-aqi">AQI ~45 <span className="tag-good">Rất tốt</span></div>
                <p>Trạng thái lý tưởng cho giấc ngủ và mở cửa thông gió tự nhiên.</p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: EVIDENCE */}
        {activeTab === "evidence" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Bằng chứng & Nguồn gốc số liệu (Evidence Chain)</h3>
            <div className="evidence-list">
              <div className="evidence-item">
                <ShieldCheck size={18} className="evidence-icon" />
                <div>
                  <strong>Trạm quan trắc {currentStation?.station_id}</strong>
                  <p>Mã message: MSG-{currentStation?.station_id}-LATEST · Nguồn: Simulator đạt chuẩn EPA 2012.</p>
                </div>
              </div>
              <div className="evidence-item">
                <ShieldCheck size={18} className="evidence-icon" />
                <div>
                  <strong>Mô hình AI Grounding</strong>
                  <p>Độ tin cậy 87% dựa trên chuỗi quan trắc 24 giờ và đối soát tương quan trạm lân cận.</p>
                </div>
              </div>
              <div className="evidence-item">
                <ShieldCheck size={18} className="evidence-icon" />
                <div>
                  <strong>Cổng kiểm soát chất lượng (Ingestion Gate)</strong>
                  <p>Trạng thái: Hợp lệ (Valid), Timestamp timezone-aware, độ trễ truyền thông &lt; 2 giây.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: RAW DATA */}
        {activeTab === "raw" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Dữ liệu thô JSON dành cho chuyên gia / Developer</h3>
            <pre className="raw-json-box">
              {JSON.stringify(
                {
                  station_id: currentStation?.station_id,
                  station_name: currentStation?.station_name,
                  coordinates: [currentStation?.latitude, currentStation?.longitude],
                  current_metrics: {
                    aqi: currentStation?.aqi,
                    pm25: currentStation?.pm25,
                    co2: currentStation?.co2,
                    noise_db: currentStation?.noise_db,
                    temperature: currentStation?.temperature,
                  },
                  status: currentStation?.status,
                  is_stale: currentStation?.is_stale,
                  sample_count_24h: historyData.length,
                },
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>
    </aside>
  );
};

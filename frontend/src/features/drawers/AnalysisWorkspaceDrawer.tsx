import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Database, RefreshCw, X } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis, YAxis } from "recharts";

import { fetchStationHistory } from "../../api/client";
import { HistoryPoint, Station } from "../../types";
import { formatVnDateTime } from "../../utils/datetime";
import { getAqiColorHex } from "../map/SensorMarkers";
import { useDraggableFloatingPanel } from "../floating";

interface AnalysisWorkspaceDrawerProps {
  stationId: string;
  stations: Station[];
  onClose: () => void;
  onSelectStationId: (id: string) => void;
}

type AnalysisTab = "overview" | "history" | "evidence" | "raw";
type HistoryMetric = "aqi" | "pm25" | "co2" | "noise_db" | "temperature" | "humidity";

const METRICS: Record<HistoryMetric, { label: string; unit: string; color: string }> = {
  aqi: { label: "AQI", unit: "", color: "#ef4444" },
  pm25: { label: "PM2.5", unit: "µg/m³", color: "#f97316" },
  co2: { label: "CO₂", unit: "ppm", color: "#06b6d4" },
  noise_db: { label: "Tiếng ồn", unit: "dB", color: "#8b5cf6" },
  temperature: { label: "Nhiệt độ", unit: "°C", color: "#ec4899" },
  humidity: { label: "Độ ẩm", unit: "%", color: "#0284c7" },
};

const finiteOrNull = (value: unknown): number | null =>
  typeof value === "number" && Number.isFinite(value) ? value : null;

export const AnalysisWorkspaceDrawer: React.FC<AnalysisWorkspaceDrawerProps> = ({
  stationId,
  stations,
  onClose,
  onSelectStationId,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "analysis",
    group: "drawer",
  });

  const [activeTab, setActiveTab] = useState<AnalysisTab>("overview");
  const [selectedMetric, setSelectedMetric] = useState<HistoryMetric>("aqi");
  const [historyData, setHistoryData] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const currentStation = stations.find((station) => station.station_id === stationId) ?? null;

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchStationHistory(stationId, 24)
      .then((items) => {
        if (active) setHistoryData(Array.isArray(items) ? items : []);
      })
      .catch((requestError) => {
        if (!active) return;
        setHistoryData([]);
        setError(requestError instanceof Error ? requestError.message : "Không thể tải lịch sử 24 giờ.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [reloadToken, stationId]);

  const chartData = useMemo(() => historyData.map((point) => {
    const measuredAt = new Date(point.timestamp);
    return {
      time: Number.isNaN(measuredAt.getTime())
        ? point.timestamp || "—"
        : measuredAt.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      timestamp: point.timestamp,
      aqi: finiteOrNull(point.aqi),
      pm25: finiteOrNull(point.pm25),
      co2: finiteOrNull(point.co2),
      noise_db: finiteOrNull(point.noise_db),
      temperature: finiteOrNull(point.temperature),
      humidity: finiteOrNull(point.humidity),
      source: point.source ?? null,
      quality_flag: point.quality_flag ?? null,
      message_id: point.message_id ?? null,
    };
  }), [historyData]);

  const latestPoint = chartData.length > 0 ? chartData[chartData.length - 1] : null;
  const metric = METRICS[selectedMetric];

  const renderValue = (value: number | null, unit: string) => value == null ? "—" : `${value}${unit ? ` ${unit}` : ""}`;

  return (
    <aside {...containerProps} className="contextual-drawer right-drawer wide-analysis-drawer">
      <div className="drawer-header-bar">
        <div className="drawer-title-group" {...handleProps}>
          <div className="badge-tag">Dữ liệu lịch sử từ backend</div>
          <h2 className="drawer-main-title">Phân tích 24 giờ</h2>
          <div className="station-selector-pills no-drag" data-no-drag="true" aria-label="Chọn trạm phân tích">
            {stations.map((station) => (
              <button
                type="button"
                key={station.station_id}
                className={`station-pill-btn ${station.station_id === stationId ? "active" : ""}`}
                onClick={() => onSelectStationId(station.station_id)}
              >
                {station.station_id} · {station.station_name}
              </button>
            ))}
          </div>
        </div>
        <button className="no-drag drawer-close-btn" data-no-drag="true" onClick={onClose} aria-label="Đóng bảng phân tích">
          <X size={18} />
        </button>
      </div>

      <div className="workspace-tabs-bar" role="tablist" aria-label="Nội dung phân tích">
        {([
          ["overview", "Biểu đồ"],
          ["history", "Chuỗi đo"],
          ["evidence", "Nguồn dữ liệu"],
          ["raw", "JSON"],
        ] as const).map(([tab, label]) => (
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-item-btn ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
            key={tab}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="drawer-scroll-body">
        {error && (
          <div className="analysis-data-state is-error" role="alert">
            <AlertTriangle size={20} aria-hidden="true" />
            <div><strong>Không thể tải lịch sử trạm</strong><p>{error}</p></div>
            <button type="button" onClick={() => setReloadToken((value) => value + 1)}>Thử lại</button>
          </div>
        )}

        {loading && (
          <div className="analysis-data-state" role="status">
            <RefreshCw size={20} className="spin-icon" aria-hidden="true" />
            <span>Đang tải chuỗi đo 24 giờ từ backend…</span>
          </div>
        )}

        {!loading && !error && historyData.length === 0 && (
          <div className="analysis-data-state">
            <Database size={20} aria-hidden="true" />
            <div><strong>Chưa có dữ liệu lịch sử</strong><p>Backend không trả về phép đo hợp lệ trong 24 giờ qua.</p></div>
          </div>
        )}

        {!error && historyData.length > 0 && activeTab === "overview" && (
          <div className="tab-pane-content">
            <div className="analysis-source-summary">
              <span><strong>{currentStation?.station_name ?? stationId}</strong></span>
              <span>{historyData.length} phép đo hợp lệ</span>
              <span>Nguồn: {latestPoint?.source ?? "Không khả dụng"}</span>
              <span>Mới nhất: {latestPoint?.timestamp ? formatVnDateTime(latestPoint.timestamp) : "—"}</span>
            </div>

            <div className="metric-pill-switcher" role="group" aria-label="Chọn chỉ số lịch sử">
              {(Object.keys(METRICS) as HistoryMetric[]).map((metricKey) => (
                <button
                  type="button"
                  key={metricKey}
                  className={`metric-select-btn ${selectedMetric === metricKey ? "active" : ""}`}
                  aria-pressed={selectedMetric === metricKey}
                  onClick={() => setSelectedMetric(metricKey)}
                >
                  {METRICS[metricKey].label}
                </button>
              ))}
            </div>

            <div className="analysis-chart-card" role="img" aria-label={`Biểu đồ ${metric.label} trong 24 giờ từ dữ liệu backend`}>
              <div className="chart-title-row">
                <span className="chart-heading">Biến thiên {metric.label} trong 24 giờ</span>
                <span>{metric.unit}</span>
              </div>
              <div className="chart-svg-container">
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                    <defs>
                      <linearGradient id={`grad-${selectedMetric}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={metric.color} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={metric.color} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                    <RechartsTooltip formatter={(value: number) => [renderValue(value, metric.unit), metric.label]} />
                    <Area
                      type="monotone"
                      dataKey={selectedMetric}
                      stroke={metric.color}
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill={`url(#grad-${selectedMetric})`}
                      connectNulls={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {!error && historyData.length > 0 && activeTab === "history" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Các phép đo gần nhất</h3>
            <div className="history-table-wrapper" tabIndex={0} role="region" aria-label="Bảng lịch sử đo, có thể cuộn ngang">
              <table className="data-table">
                <thead><tr><th>Thời gian</th><th>AQI</th><th>PM2.5</th><th>CO₂</th><th>Tiếng ồn</th><th>Nhiệt độ</th><th>Độ ẩm</th></tr></thead>
                <tbody>
                  {chartData.slice(-12).reverse().map((row) => (
                    <tr key={`${row.timestamp}-${row.message_id ?? "measurement"}`}>
                      <td>{formatVnDateTime(row.timestamp)}</td>
                      <td><span className="table-aqi-badge" style={{ backgroundColor: getAqiColorHex(row.aqi) }}>{renderValue(row.aqi, "")}</span></td>
                      <td>{renderValue(row.pm25, "µg/m³")}</td>
                      <td>{renderValue(row.co2, "ppm")}</td>
                      <td>{renderValue(row.noise_db, "dB")}</td>
                      <td>{renderValue(row.temperature, "°C")}</td>
                      <td>{renderValue(row.humidity, "%")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!error && historyData.length > 0 && activeTab === "evidence" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Nguồn gốc dữ liệu mới nhất</h3>
            <dl className="analysis-evidence-grid">
              <div><dt>Trạm</dt><dd>{stationId}</dd></div>
              <div><dt>Thời gian đo</dt><dd>{latestPoint?.timestamp ? formatVnDateTime(latestPoint.timestamp) : "—"}</dd></div>
              <div><dt>Nguồn</dt><dd>{latestPoint?.source ?? "Không khả dụng"}</dd></div>
              <div><dt>Chất lượng</dt><dd>{latestPoint?.quality_flag ?? "Không khả dụng"}</dd></div>
              <div><dt>Message ID</dt><dd>{latestPoint?.message_id ?? "Không khả dụng"}</dd></div>
              <div><dt>Số mẫu</dt><dd>{historyData.length}</dd></div>
            </dl>
            <p className="today-simulator-note">Không có phân tích nguyên nhân hoặc độ tin cậy nào được tự suy diễn ở frontend.</p>
          </div>
        )}

        {!error && historyData.length > 0 && activeTab === "raw" && (
          <div className="tab-pane-content">
            <h3 className="section-title">Dữ liệu API đã nhận</h3>
            <pre className="raw-json-box">{JSON.stringify({ station: currentStation, history: historyData }, null, 2)}</pre>
          </div>
        )}
      </div>
    </aside>
  );
};

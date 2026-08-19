import React, { useEffect, useState } from "react";
import { Activity, ArrowLeft, Bot, ChartNoAxesCombined, Database, Sparkles, Thermometer, TriangleAlert, Volume2, Wind } from "lucide-react";

import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { DataQualityBadge, getAqiSeverity, getPm25Severity } from "../../components/common/DataQualityBadge";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { ForecastData, HistoryPoint, StationDetailData } from "../../types";
import { VN_TZ, formatVnDateTime } from "../../utils/datetime";

type MetricKey = ForecastData["metric"];
const METRICS: Record<MetricKey, { label: string; unit: string }> = {
  aqi: { label: "AQI", unit: "" }, pm25: { label: "PM2.5", unit: "µg/m³" },
  co2: { label: "CO₂", unit: "ppm" }, noise_db: { label: "Tiếng ồn", unit: "dB" }, temperature: { label: "Nhiệt độ", unit: "°C" },
};

const MetricSelector: React.FC<{ value: MetricKey; onChange: (metric: MetricKey) => void; label: string }> = ({ value, onChange, label }) => (
  <div className="metric-selector" role="group" aria-label={label}>
    {(Object.keys(METRICS) as MetricKey[]).map((metric) => <button type="button" key={metric} className={`preset-btn ${value === metric ? "active" : ""}`} aria-pressed={value === metric} onClick={() => onChange(metric)}>{METRICS[metric].label}</button>)}
  </div>
);

export const StationDetail: React.FC = () => {
  const { selectedStationId, navigateTo } = useAuth();
  const [station, setStation] = useState<StationDetailData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [rangeHours, setRangeHours] = useState(24);
  const [chartMetric, setChartMetric] = useState<MetricKey>("pm25");
  const [forecastMetric, setForecastMetric] = useState<MetricKey>("pm25");
  const [chartType, setChartType] = useState<"area" | "line">("area");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const load = async () => {
      setLoading(true); setError(null);
      try {
        const [current, points] = await Promise.all([
          api.getStationCurrent(selectedStationId), api.getStationHistory(selectedStationId, rangeHours),
        ]);
        setStation(current); setHistory(points);
        try { setForecast(await api.getStationForecast(selectedStationId, forecastMetric)); }
        catch { setForecast(null); }
      } catch { setError("Không thể tải dữ liệu trạm. Vui lòng thử lại."); }
      finally { setLoading(false); }
    };
    load();
  }, [selectedStationId, rangeHours, forecastMetric, reloadToken]);

  if (loading) return <div className="detail-container"><PageHeader title="Chi tiết trạm" description="Đang tải dữ liệu hiện tại, lịch sử và dự báo ngắn hạn." /><div className="skeleton-card skeleton-card--sm" /><div className="skeleton-card skeleton-card--lg" /></div>;
  if (error || !station) return <div className="detail-container"><PageHeader title="Chi tiết trạm" description="Không thể hiển thị dữ liệu trạm ở thời điểm này." leading={<Button variant="ghost" size="sm" onClick={() => navigateTo("dashboard")}><ArrowLeft size={16} /> Quay lại bản đồ</Button>} /><div className="alert-box alert-error" role="alert"><TriangleAlert size={17} /><span>{error ?? `Không tìm thấy dữ liệu cho trạm ${selectedStationId}.`}</span><Button variant="outline" size="sm" onClick={() => setReloadToken((value) => value + 1)}>Thử lại</Button></div></div>;

  const aqiSeverity = getAqiSeverity(station.aqi); const pm25Severity = getPm25Severity(station.pm25);
  const chartColor = chartMetric === "aqi" ? aqiSeverity.color : pm25Severity.color;
  const Chart = chartType === "area" ? AreaChart : LineChart;

  return <div className="detail-container">
    <PageHeader title={`${station.station_name} (${station.station_id})`} description={`Vị trí: Lat ${station.latitude}, Lon ${station.longitude}`} leading={<Button variant="ghost" size="sm" onClick={() => navigateTo("dashboard")}><ArrowLeft size={16} /> Quay lại bản đồ</Button>} actions={<Button variant="primary" onClick={() => navigateTo("agent", { stationId: selectedStationId })}><Bot size={17} /> Hỏi AI</Button>} />

    <div className="metrics-grid">
      <MetricCard label="AQI hiện tại" value={station.aqi} unit="" icon={<Activity size={25} />} color={aqiSeverity.color} support="Chỉ số tổng quan, tính từ PM2.5 trong dữ liệu mô phỏng." /><MetricCard label="PM2.5" value={station.pm25} unit="µg/m³" icon={<Wind size={24} />} color={pm25Severity.color} support="Thành phần dùng để tính AQI." /><MetricCard label="CO₂" value={station.co2} unit="ppm" icon={<Database size={24} />} support="Nồng độ carbon dioxide tại trạm." /><MetricCard label="Tiếng ồn" value={station.noise_db} unit="dB" icon={<Volume2 size={24} />} support="Mức âm thanh môi trường." /><MetricCard label="Nhiệt độ" value={station.temperature} unit="°C" icon={<Thermometer size={24} />} support="Nhiệt độ không khí tại trạm." />
      <div className="metric-card metric-card--meta"><div className="metric-label">Độ mới dữ liệu</div><DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} aqi={station.aqi} /><div className="meta-info"><div>Nguồn: <span className="source-tag">{station.source ?? "Không khả dụng"}</span></div><div>Cập nhật: {formatVnDateTime(station.updated_at)}</div><div>Múi giờ: {VN_TZ}</div></div></div>
    </div>
    <section className="forecast-section"><div className="history-header"><h2><Sparkles size={18} /> Dự báo {METRICS[forecastMetric].label} ngắn hạn (1 - 3 giờ)</h2><MetricSelector value={forecastMetric} onChange={setForecastMetric} label="Chỉ số dự báo" /></div>{forecast ? <><p className="forecast-meta">Mô hình: {forecast.model_name ?? forecast.source} | Độ tin cậy: {forecast.confidence}</p><div className="forecast-grid">{forecast.forecasts.map((fc, index) => <div key={index} className="forecast-card"><div className="forecast-time">Dự báo sau {fc.horizon}</div><div className="forecast-pm25">{fc.value ?? fc.pm25_predicted ?? "—"} {METRICS[forecastMetric].unit}</div><div className="forecast-range">Khoảng: {fc.value_min ?? fc.range[0] ?? "—"} - {fc.value_max ?? fc.range[1] ?? "—"} {METRICS[forecastMetric].unit}</div>{fc.confidence != null && <div className="forecast-range">Độ tin cậy: {Math.round(fc.confidence * 100)}%</div>}</div>)}</div>{forecast.limitations?.map((item) => <p className="forecast-meta" key={item}>{item}</p>)}</> : <p className="forecast-meta">Không có dự báo cho chỉ số đã chọn.</p>}</section>
    <section className="history-section"><div className="history-header"><h2><ChartNoAxesCombined size={18} /> Lịch sử {METRICS[chartMetric].label} theo thời gian</h2><MetricSelector value={chartMetric} onChange={setChartMetric} label="Chỉ số biểu đồ" /><div className="range-presets" role="group" aria-label="Khoảng thời gian lịch sử">{[1, 6, 24, 72].map((hours) => <button type="button" key={hours} className={`preset-btn ${rangeHours === hours ? "active" : ""}`} aria-pressed={rangeHours === hours} onClick={() => setRangeHours(hours)}>{hours}h</button>)}</div><div className="chart-type-toggle" role="group" aria-label="Kiểu biểu đồ"><button type="button" className={`preset-btn ${chartType === "area" ? "active" : ""}`} onClick={() => setChartType("area")}>Vùng</button><button type="button" className={`preset-btn ${chartType === "line" ? "active" : ""}`} onClick={() => setChartType("line")}>Đường</button></div></div><div className="chart-wrapper"><ResponsiveContainer width="100%" height={320}><Chart data={history}><defs><linearGradient id="metricGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={chartColor} stopOpacity={0.8} /><stop offset="95%" stopColor={chartColor} stopOpacity={0.05} /></linearGradient></defs><CartesianGrid strokeDasharray="3 3" stroke="#334155" /><XAxis dataKey="timestamp" stroke="#94a3b8" /><YAxis stroke="#94a3b8" domain={[0, "dataMax + 10"]} /><Tooltip contentStyle={{ backgroundColor: "#1e293b", borderColor: "#475569", color: "#f8fafc" }} formatter={(value: number) => [`${value} ${METRICS[chartMetric].unit}`, METRICS[chartMetric].label]} />{chartType === "area" ? <Area type="monotone" dataKey={chartMetric} stroke={chartColor} fill="url(#metricGradient)" connectNulls /> : <Line type="monotone" dataKey={chartMetric} stroke={chartColor} strokeWidth={2} dot={false} connectNulls />}</Chart></ResponsiveContainer></div></section>
  </div>;
};

const MetricCard: React.FC<{ label: string; value: number | null | undefined; unit: string; icon: React.ReactNode; support: string; color?: string }> = ({ label, value, unit, icon, support, color }) => <div className="metric-card"><div className="metric-label">{label}</div><div className="metric-value metric-value--with-icon" style={color ? { color } : undefined}>{icon} {value ?? "—"} <small>{value != null ? unit : ""}</small></div><p className="metric-support-text">{support}</p></div>;

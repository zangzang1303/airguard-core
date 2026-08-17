import React, { useEffect, useState } from "react";
import { Activity, ArrowLeft, Bot, ChartNoAxesCombined, Database, GitCompareArrows, Sparkles, Thermometer, TriangleAlert, Volume2, Wind } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { DataQualityBadge, getAqiSeverity, getPm25Severity } from "../../components/common/DataQualityBadge";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { ForecastData, HistoryPoint, StationDetailData } from "../../types";
import { VN_TZ, formatVnDateTime } from "../../utils/datetime";

export const StationDetail: React.FC = () => {
  const { selectedStationId, navigateTo, setCompareStationIds } = useAuth();
  const [station, setStation] = useState<StationDetailData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [rangeHours, setRangeHours] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const fetchDetailData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [currentData, historyData, forecastData] = await Promise.all([
          api.getStationCurrent(selectedStationId),
          api.getStationHistory(selectedStationId, rangeHours),
          api.getStationForecast(selectedStationId)
        ]);
        setStation(currentData);
        setHistory(historyData);
        setForecast(forecastData);
      } catch (err) {
        console.error("Error fetching station detail:", err);
        setError("Không thể tải dữ liệu trạm. Vui lòng thử lại.");
      } finally {
        setLoading(false);
      }
    };

    fetchDetailData();
  }, [selectedStationId, rangeHours, reloadToken]);

  const handleAskAI = () => {
    navigateTo("agent", { stationId: selectedStationId });
  };

  const handleCompare = () => {
    const otherId = selectedStationId === "S01" ? "S02" : "S01";
    setCompareStationIds([selectedStationId, otherId]);
    navigateTo("compare");
  };

  if (loading) {
    return (
      <div className="detail-container">
        <PageHeader title="Chi tiết trạm" description="Đang tải dữ liệu hiện tại, lịch sử và dự báo ngắn hạn." />
        <div className="skeleton-card skeleton-card--sm" role="status" aria-label="Đang tải dữ liệu trạm" />
        <div className="skeleton-card skeleton-card--lg" />
      </div>
    );
  }

  // Khi API lỗi hoặc không trả về trạm, phải báo lỗi kèm hành động thử lại thay vì skeleton quay mãi.
  if (error || !station) {
    return (
      <div className="detail-container">
        <PageHeader
          title="Chi tiết trạm"
          description="Không thể hiển thị dữ liệu trạm ở thời điểm này."
          leading={(
            <Button variant="ghost" size="sm" onClick={() => navigateTo("dashboard")}>
              <ArrowLeft size={16} aria-hidden="true" /> Quay lại bản đồ
            </Button>
          )}
        />
        <div className="alert-box alert-error" role="alert">
          <TriangleAlert size={17} aria-hidden="true" />
          <span>{error ?? `Không tìm thấy dữ liệu cho trạm ${selectedStationId}.`}</span>
          <Button variant="outline" size="sm" onClick={() => setReloadToken((token) => token + 1)}>
            Thử lại
          </Button>
        </div>
      </div>
    );
  }

  const aqiSeverity = getAqiSeverity(station.aqi);
  const pm25Severity = getPm25Severity(station.pm25);

  return (
    <div className="detail-container">
      <PageHeader
        title={`${station.station_name} (${station.station_id})`}
        description={`Vị trí: Lat ${station.latitude}, Lon ${station.longitude}`}
        leading={(
          <Button variant="ghost" size="sm" onClick={() => navigateTo("dashboard")}>
            <ArrowLeft size={16} aria-hidden="true" /> Quay lại bản đồ
          </Button>
        )}
        actions={(
          <>
            <Button variant="outline" onClick={handleCompare}>
              <GitCompareArrows size={17} aria-hidden="true" /> So sánh
            </Button>
            <Button variant="primary" onClick={handleAskAI}>
              <Bot size={17} aria-hidden="true" /> Hỏi AI
            </Button>
          </>
        )}
      />

      {/* AQI is the primary station summary; the four underlying environmental readings follow. */}
      <div className="metrics-grid">
        <div className="metric-card metric-primary">
          <div className="metric-label">AQI hiện tại</div>
          <div className="metric-value metric-value--with-icon" style={{ color: aqiSeverity.color }}>
            <Activity size={25} aria-hidden="true" /> {station.aqi ?? "—"}
          </div>
          <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} aqi={station.aqi} />
          <p className="metric-support-text">Chỉ số tổng quan, tính từ PM2.5 trong dữ liệu mô phỏng.</p>
        </div>

        <div className="metric-card">
          <div className="metric-label">PM2.5</div>
          <div className="metric-value metric-value--with-icon" style={{ color: pm25Severity.color }}>
            <Wind size={24} aria-hidden="true" /> {station.pm25 ?? "—"} <small>{station.pm25 != null ? "µg/m³" : ""}</small>
          </div>
          <p className="metric-support-text">Thành phần dùng để tính AQI.</p>
        </div>

        <div className="metric-card">
          <div className="metric-label">CO₂</div>
          <div className="metric-value metric-value--with-icon"><Database size={24} aria-hidden="true" /> {station.co2 ?? "—"} <small>{station.co2 != null ? "ppm" : ""}</small></div>
          <p className="metric-support-text">Nồng độ carbon dioxide tại điểm trạm.</p>
        </div>

        <div className="metric-card">
          <div className="metric-label">Tiếng ồn</div>
          <div className="metric-value metric-value--with-icon"><Volume2 size={24} aria-hidden="true" /> {station.noise_db ?? "—"} <small>{station.noise_db != null ? "dB" : ""}</small></div>
          <p className="metric-support-text">Mức âm thanh môi trường ghi nhận tại trạm.</p>
        </div>

        <div className="metric-card">
          <div className="metric-label">Nhiệt độ</div>
          <div className="metric-value metric-value--with-icon"><Thermometer size={24} aria-hidden="true" /> {station.temperature ?? "—"} <small>{station.temperature != null ? "°C" : ""}</small></div>
          <p className="metric-support-text">Nhiệt độ không khí tại vị trí trạm.</p>
        </div>

        <div className="metric-card metric-card--meta">
          <div className="metric-label">Độ mới dữ liệu</div>
          <div className="meta-info">
            <div>Nguồn: <span className="source-tag">{station.source ?? "Không khả dụng"}</span></div>
            <div>Cập nhật: {formatVnDateTime(station.updated_at)}</div>
            <div>Múi giờ: {VN_TZ}</div>
          </div>
        </div>
      </div>

      {/* Forecast 1-3h Panel */}
      {forecast && (
        <section className="forecast-section">
          <h2><Sparkles size={18} aria-hidden="true" /> Dự báo PM2.5 ngắn hạn (1 - 3 giờ)</h2>
          <p className="forecast-meta">Mô hình: {forecast.model_name ?? forecast.source} | Độ tin cậy: {forecast.confidence}</p>
          <div className="forecast-grid">
            {forecast.forecasts.map((fc, idx) => (
              <div key={idx} className="forecast-card">
                <div className="forecast-time">Dự báo sau {fc.horizon}</div>
                <div className="forecast-pm25">{fc.pm25_predicted} µg/m³</div>
                <div className="forecast-range">Khoảng: {fc.range[0]} - {fc.range[1]} µg/m³</div>
                {fc.confidence != null && <div className="forecast-range">Độ tin cậy: {Math.round(fc.confidence * 100)}%</div>}
              </div>
            ))}
          </div>
          {forecast.limitations?.map((limitation) => <p className="forecast-meta" key={limitation}>{limitation}</p>)}
        </section>
      )}

      {/* History Recharts Graph */}
      <section className="history-section">
        <div className="history-header">
          <h2><ChartNoAxesCombined size={18} aria-hidden="true" /> Lịch sử PM2.5 theo thời gian</h2>
          <div className="range-presets" role="group" aria-label="Khoảng thời gian lịch sử">
            {[1, 6, 24, 72].map((h) => (
              <button
                type="button"
                key={h}
                className={`preset-btn ${rangeHours === h ? "active" : ""}`}
                aria-pressed={rangeHours === h}
                onClick={() => setRangeHours(h)}
              >
                {h}h
              </button>
            ))}
          </div>
        </div>

        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={history}>
              <defs>
                <linearGradient id="pm25Gradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={pm25Severity.color} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={pm25Severity.color} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="timestamp" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={[0, 'dataMax + 10']} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", borderColor: "#475569", color: "#f8fafc" }}
                formatter={(val: any) => [`${val} µg/m³`, "PM2.5"]}
              />
              <Area type="monotone" dataKey="pm25" stroke={pm25Severity.color} fillOpacity={1} fill="url(#pm25Gradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
};

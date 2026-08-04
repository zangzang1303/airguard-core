import React, { useEffect, useState } from "react";
import { ArrowLeft, Bot, ChartNoAxesCombined, Droplets, GitCompareArrows, Sparkles, Thermometer, Wind } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { DataQualityBadge, getPm25Severity } from "../../components/common/DataQualityBadge";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { ForecastData, HistoryPoint, StationDetailData } from "../../types";

export const StationDetail: React.FC = () => {
  const { selectedStationId, navigateTo, setCompareStationIds } = useAuth();
  const [station, setStation] = useState<StationDetailData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [rangeHours, setRangeHours] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchDetailData = async () => {
      setLoading(true);
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
      } finally {
        setLoading(false);
      }
    };

    fetchDetailData();
  }, [selectedStationId, rangeHours]);

  const handleAskAI = () => {
    navigateTo("agent", { stationId: selectedStationId });
  };

  const handleCompare = () => {
    const otherId = selectedStationId === "S01" ? "S02" : "S01";
    setCompareStationIds([selectedStationId, otherId]);
    navigateTo("compare");
  };

  if (loading || !station) {
    return (
      <div className="detail-container">
        <PageHeader title="Chi tiết trạm" description="Đang tải dữ liệu hiện tại, lịch sử và dự báo ngắn hạn." />
        <div className="skeleton-card" style={{ height: 200 }}></div>
        <div className="skeleton-card" style={{ height: 350 }}></div>
      </div>
    );
  }

  const severity = getPm25Severity(station.pm25);

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

      {/* Current Real-time Metrics Card */}
      <div className="metrics-grid">
        <div className="metric-card metric-primary">
          <div className="metric-label">PM2.5 Hiện tại</div>
          <div className="metric-value" style={{ color: severity.color }}>
            {station.pm25 ?? "N/A"} <small>µg/m³</small>
          </div>
          <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} />
        </div>

        <div className="metric-card">
          <div className="metric-label">Thời tiết Ngữ cảnh</div>
          <div className="weather-info">
            <div><Thermometer size={16} aria-hidden="true" /> Nhiệt độ: <strong>{station.weather?.temperature ?? "Không khả dụng"}{station.weather ? " °C" : ""}</strong></div>
            <div><Droplets size={16} aria-hidden="true" /> Độ ẩm: <strong>{station.weather?.humidity ?? "Không khả dụng"}{station.weather ? " %" : ""}</strong></div>
            <div><Wind size={16} aria-hidden="true" /> Tốc độ gió: <strong>{station.weather?.wind_speed ?? "Không khả dụng"}{station.weather ? " m/s" : ""}</strong></div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Thông tin Nguồn & Độ mới</div>
          <div className="meta-info">
            <div>Nguồn: <span className="source-tag">{station.source}</span></div>
            <div>Cập nhật: {new Date(station.updated_at).toLocaleString("vi-VN")}</div>
            <div>Múi giờ: Asia/Ho_Chi_Minh</div>
          </div>
        </div>
      </div>

      {/* Forecast 1-3h Panel */}
      {forecast && (
        <section className="forecast-section">
          <h3><Sparkles size={18} aria-hidden="true" /> Dự báo PM2.5 ngắn hạn (1 - 3 giờ)</h3>
          <p className="forecast-meta">Mô hình: {forecast.source} | Độ tin cậy: {forecast.confidence}</p>
          <div className="forecast-grid">
            {forecast.forecasts.map((fc, idx) => (
              <div key={idx} className="forecast-card">
                <div className="forecast-time">Dự báo sau {fc.horizon}</div>
                <div className="forecast-pm25">{fc.pm25_predicted} µg/m³</div>
                <div className="forecast-range">Khoảng: {fc.range[0]} - {fc.range[1]} µg/m³</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* History Recharts Graph */}
      <section className="history-section">
        <div className="history-header">
          <h3><ChartNoAxesCombined size={18} aria-hidden="true" /> Lịch sử PM2.5 theo thời gian</h3>
          <div className="range-presets">
            {[1, 6, 24, 72].map((h) => (
              <button
                key={h}
                className={`preset-btn ${rangeHours === h ? "active" : ""}`}
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
                  <stop offset="5%" stopColor={severity.color} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={severity.color} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="timestamp" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={[0, 'dataMax + 10']} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", borderColor: "#475569", color: "#f8fafc" }}
                formatter={(val: any) => [`${val} µg/m³`, "PM2.5"]}
              />
              <Area type="monotone" dataKey="pm25" stroke={severity.color} fillOpacity={1} fill="url(#pm25Gradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
};

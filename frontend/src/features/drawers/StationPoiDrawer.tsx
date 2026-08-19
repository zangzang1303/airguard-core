import React, { useEffect, useState } from "react";
import { X, Activity, Wind, Droplets, Volume2, Thermometer, Sparkles, BarChart2, Clock, MapPin, Database } from "lucide-react";
import { api } from "../../api/client";
import { HistoryPoint, Station } from "../../types";
import { PlacePOI } from "../../types/superApp";
import { getAqiColorHex, getAqiCategoryLabel } from "../map/SensorMarkers";
import { DataQualityBadge } from "../../components/common/DataQualityBadge";
import { formatVnDateTime } from "../../utils/datetime";

interface StationPoiDrawerProps {
  station: Station | null;
  poi: PlacePOI | null;
  onClose: () => void;
  onOpenAnalysis: (stationId: string) => void;
  onOpenForecast: (stationId: string) => void;
  onAskAiAboutStation: (stationName: string, aqi: number | null) => void;
}

export const StationPoiDrawer: React.FC<StationPoiDrawerProps> = ({
  station,
  poi,
  onClose,
  onOpenAnalysis,
  onOpenForecast,
  onAskAiAboutStation,
}) => {
  const [latestHistoryPoint, setLatestHistoryPoint] = useState<HistoryPoint | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    let active = true;
    if (!station?.station_id) {
      setLatestHistoryPoint(null);
      return () => { active = false; };
    }

    setHistoryLoading(true);
    api.getStationHistory(station.station_id, 1)
      .then((items) => {
        if (active) setLatestHistoryPoint(items.length > 0 ? items[items.length - 1] : null);
      })
      .catch(() => {
        if (active) setLatestHistoryPoint(null);
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });

    return () => { active = false; };
  }, [station?.station_id]);

  if (!station && !poi) return null;

  const title = station ? station.station_name : poi?.name || "Chi tiết vị trí";
  const subtitle = station ? `Cảm biến ${station.station_id} · Ocean Park 1` : poi?.subdivision || "Vinhomes Ocean Park 1";
  const hasUsableCurrentData = station?.status === "online" && !station.is_stale;
  const aqiVal = hasUsableCurrentData ? station.aqi : null;
  const pm25Val = hasUsableCurrentData ? station.pm25 : null;
  const co2Val = hasUsableCurrentData ? station.co2 : null;
  const noiseVal = hasUsableCurrentData ? station.noise_db : null;
  const tempVal = hasUsableCurrentData ? station.temperature : null;
  const humidityVal = hasUsableCurrentData ? latestHistoryPoint?.humidity ?? station.humidity ?? null : null;
  const observedAt = station?.updated_at;
  const sourceLabel = latestHistoryPoint?.source ?? station?.source ?? "Không khả dụng";
  const { label: categoryLabel } = getAqiCategoryLabel(aqiVal);
  const colorHex = getAqiColorHex(aqiVal);

  return (
    <aside className="contextual-drawer right-drawer station-poi-drawer">
      {/* Header */}
      <div className="drawer-header-bar">
        <div className="drawer-title-group">
          <h2 className="drawer-main-title">{title}</h2>
          <div className="drawer-sub-meta">
            <MapPin size={13} />
            <span>{subtitle}</span>
          </div>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng chi tiết trạm">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body">
        {/* Main AQI Hero Score Card */}
        <div className="station-aqi-hero-card" style={{ "--hero-color": colorHex } as React.CSSProperties}>
          <div className="hero-score-column">
            <span className="hero-label">Chất lượng không khí (AQI)</span>
            <div className="hero-number-wrap">
              <span className="hero-number">{aqiVal ?? "—"}</span>
              <span className="hero-unit">AQI</span>
            </div>
            <span className="hero-category-pill" style={{ backgroundColor: colorHex }}>
              {categoryLabel}
            </span>
          </div>
          <div className="hero-status-indicator">
            <Activity size={32} className="indicator-icon" />
          </div>
        </div>

        {/* Data Quality & Source Metadata Bar */}
        {station && (
          <div className="station-data-meta-box" style={{ padding: "10px 14px", background: "var(--bg-secondary, #f8fafc)", borderRadius: "8px", margin: "12px 0", fontSize: "0.82rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <span>Trạng thái trạm:</span>
              <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} aqi={station.aqi} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted, #64748b)", fontSize: "0.78rem" }}>
              <span>Thời gian cập nhật:</span>
              <strong>{observedAt ? formatVnDateTime(observedAt) : "Không khả dụng"}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted, #64748b)", fontSize: "0.78rem", marginTop: "2px" }}>
              <span>Nguồn dữ liệu:</span>
              <strong style={{ color: "#4f46e5" }}><Database size={12} style={{ verticalAlign: "middle", marginRight: "3px" }} />{sourceLabel}</strong>
            </div>
          </div>
        )}

        {/* 4 Environmental KPI Metric Grid */}
        <div className="env-metrics-grid">
          <div className="env-metric-item">
            <div className="metric-icon-wrap pm25">
              <Wind size={16} />
            </div>
            <div className="metric-info">
              <span className="metric-name">PM2.5</span>
              <span className="metric-val">{pm25Val ?? "—"} <small>µg/m³</small></span>
            </div>
          </div>

          <div className="env-metric-item">
            <div className="metric-icon-wrap humidity">
              <Droplets size={16} />
            </div>
            <div className="metric-info">
              <span className="metric-name">Độ ẩm</span>
              <span className="metric-val">
                {historyLoading ? "Đang tải" : humidityVal ?? "—"} <small>{humidityVal != null ? "%" : ""}</small>
              </span>
            </div>
          </div>

          <div className="env-metric-item">
            <div className="metric-icon-wrap co2">
              <Droplets size={16} />
            </div>
            <div className="metric-info">
              <span className="metric-name">Khí CO₂</span>
              <span className="metric-val">{co2Val ?? "—"} <small>ppm</small></span>
            </div>
          </div>

          <div className="env-metric-item">
            <div className="metric-icon-wrap noise">
              <Volume2 size={16} />
            </div>
            <div className="metric-info">
              <span className="metric-name">Độ ồn</span>
              <span className="metric-val">{noiseVal ?? "—"} <small>dB</small></span>
            </div>
          </div>

          <div className="env-metric-item">
            <div className="metric-icon-wrap temp">
              <Thermometer size={16} />
            </div>
            <div className="metric-info">
              <span className="metric-name">Nhiệt độ</span>
              <span className="metric-val">{tempVal ?? "—"} <small>°C</small></span>
            </div>
          </div>
        </div>

        {/* AirGuard Grounded Information Notice */}
        <div className="airguard-insight-box">
          <div className="insight-header">
            <Sparkles size={16} className="insight-star" />
            <span className="insight-title">AirGuard AI Grounded Status</span>
          </div>
          <div className="insight-content">
            <strong>Dữ liệu giả lập cho MVP — không phải quan trắc chính thức</strong>
            <p style={{ marginTop: "4px", fontSize: "0.85rem" }}>
              Để nhận phân tích chuyên sâu và khuyến nghị phù hợp với nhóm nhạy cảm theo đúng dữ liệu realtime, hãy nhấn nút <strong>Hỏi AI về vị trí</strong> bên dưới.
            </p>
          </div>
        </div>

      </div>

      {/* Action Footer Buttons */}
      <div className="drawer-footer-actions">
        {station && (
          <>
            <button
              className="action-pill-btn secondary"
              onClick={() => onOpenAnalysis(station.station_id)}
            >
              <BarChart2 size={15} />
              <span>Phân tích 24h</span>
            </button>

            <button
              className="action-pill-btn secondary"
              onClick={() => onOpenForecast(station.station_id)}
            >
              <Clock size={15} />
              <span>Xem dự báo</span>
            </button>
          </>
        )}

        <button
          className="action-pill-btn primary"
          onClick={() => onAskAiAboutStation(title, aqiVal)}
        >
          <Sparkles size={15} />
          <span>Hỏi AI về vị trí</span>
        </button>
      </div>
    </aside>
  );
};


import React from "react";
import { X, Activity, Wind, Droplets, Volume2, Thermometer, Sparkles, BarChart2, Clock, MapPin, AlertCircle } from "lucide-react";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";
import { getAqiColorHex, getAqiCategoryLabel } from "../map/SensorMarkers";

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
  if (!station && !poi) return null;

  const title = station ? station.station_name : poi?.name || "Chi tiết vị trí";
  const subtitle = station ? `Cảm biến ${station.station_id} · Ocean Park 1` : poi?.subdivision || "Vinhomes Ocean Park 1";
  const aqiVal = station ? station.aqi : poi?.estimatedAqi ?? null;
  const pm25Val = station ? station.pm25 : 32.4;
  const co2Val = station ? station.co2 : 620;
  const noiseVal = station ? station.noise_db : 54;
  const tempVal = station ? station.temperature : 30.5;
  const { label: categoryLabel } = getAqiCategoryLabel(aqiVal);
  const colorHex = getAqiColorHex(aqiVal);

  const getInsightText = () => {
    if (aqiVal && aqiVal > 150) {
      return {
        title: "Cảnh báo ô nhiễm cục bộ",
        desc: "Chỉ số PM2.5 tăng nhanh trong 45 phút qua, khả năng cao do lưu lượng giao thông tăng tại trục đường lân cận. Khuyến nghị nhóm nhạy cảm hạn chế tập thể dục ngoài trời.",
        prediction: "Dự kiến chỉ số sẽ hạ nhiệt dần sau 20:00 tối nay.",
      };
    }
    if (aqiVal && aqiVal > 100) {
      return {
        title: "Chất lượng không khí ở mức nhạy cảm",
        desc: "Chỉ số dao động mức trung bình cao. Cư dân có vấn đề hô hấp nên cân nhắc đeo khẩu trang khi đi bộ lâu.",
        prediction: "Khung giờ không khí tốt nhất: 06:00 – 08:30 sáng mai.",
      };
    }
    return {
      title: "Không khí trong lành & thoáng đãng",
      desc: "Nồng độ bụi mịn và CO₂ ở mức lý tưởng. Khu vực đón gió hồ thông thoáng, rất thích hợp cho các hoạt động thể thao, dạo bộ ngoài trời.",
      prediction: "Duy trì chất lượng tốt trong 3 giờ tới.",
    };
  };

  const insight = getInsightText();

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
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body">
        {/* Main AQI Hero Score Card */}
        <div className="station-aqi-hero-card" style={{ "--hero-color": colorHex } as React.CSSProperties}>
          <div className="hero-score-column">
            <span className="hero-label">Chất lượng không khí</span>
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

        {/* AirGuard Natural Language Insight Box */}
        <div className="airguard-insight-box">
          <div className="insight-header">
            <Sparkles size={16} className="insight-star" />
            <span className="insight-title">AirGuard AI Insight</span>
          </div>
          <div className="insight-content">
            <strong>{insight.title}</strong>
            <p>{insight.desc}</p>
            <div className="insight-pred">
              <Clock size={13} />
              <span>{insight.prediction}</span>
            </div>
          </div>
        </div>

        {/* Best time to visit POI if available */}
        {poi?.bestTimeToVisit && (
          <div className="poi-best-time-box">
            <div className="box-title">Khung giờ lý tưởng tham quan</div>
            <div className="box-val">{poi.bestTimeToVisit}</div>
          </div>
        )}
      </div>

      {/* Action Footer Buttons */}
      <div className="drawer-footer-actions">
        <button
          className="action-pill-btn secondary"
          onClick={() => onOpenAnalysis(station?.station_id || "S03")}
        >
          <BarChart2 size={15} />
          <span>Phân tích 24h</span>
        </button>

        <button
          className="action-pill-btn secondary"
          onClick={() => onOpenForecast(station?.station_id || "S03")}
        >
          <Clock size={15} />
          <span>Xem dự báo</span>
        </button>

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

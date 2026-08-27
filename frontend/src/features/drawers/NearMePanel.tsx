import React, { useMemo } from "react";
import { MapPin, Sparkles, X, LocateFixed, Crosshair, Navigation, ArrowRight, ShieldAlert, CheckCircle2 } from "lucide-react";
import { Station } from "../../types";
import { findNearestStation } from "../../utils/geoUtils";

interface NearMePanelProps {
  userLocation: [number, number];
  userLocationName?: string;
  userLocationSource?: "gps" | "search" | "manual_click" | "default";
  userLocationAccuracy?: number | null;
  stations: Station[];
  isLocating?: boolean;
  onClose: () => void;
  onOpenAiChat: () => void;
  onLocateGps?: () => void;
  onStartPickOnMap?: () => void;
  onSelectStation?: (stationId: string) => void;
}

export const NearMePanel: React.FC<NearMePanelProps> = ({
  userLocation,
  userLocationName = "Vị trí của bạn",
  userLocationSource = "default",
  userLocationAccuracy,
  stations,
  isLocating = false,
  onClose,
  onOpenAiChat,
  onLocateGps,
  onStartPickOnMap,
  onSelectStation,
}) => {
  const nearestResult = useMemo(
    () => findNearestStation(userLocation, stations),
    [userLocation, stations]
  );

  const sourceLabel = useMemo(() => {
    switch (userLocationSource) {
      case "gps":
        return "Định vị GPS vệ tinh";
      case "search":
        return "Nhập / Tìm kiếm";
      case "manual_click":
        return "Tự chọn trên bản đồ";
      default:
        return "Mặc định Ocean Park 1";
    }
  }, [userLocationSource]);

  const nearestSt = nearestResult?.station;

  const getAqiColor = (aqi: number | null | undefined) => {
    if (aqi === null || aqi === undefined) return "#64748b";
    if (aqi <= 50) return "#10b981";
    if (aqi <= 100) return "#eab308";
    if (aqi <= 150) return "#f97316";
    if (aqi <= 200) return "#ef4444";
    if (aqi <= 300) return "#8b5cf6";
    return "#7f1d1d";
  };

  const getAqiLevelText = (aqi: number | null | undefined) => {
    if (aqi === null || aqi === undefined) return "Chưa có dữ liệu";
    if (aqi <= 50) return "Tốt - Không khí trong lành";
    if (aqi <= 100) return "Trung bình - Chấp nhận được";
    if (aqi <= 150) return "Kém - Nhạy cảm cần lưu ý";
    if (aqi <= 200) return "Xấu - Hạn chế ra ngoài";
    return "Rất nguy hại";
  };

  return (
    <div className="floating-bottom-sheet near-me-sheet">
      {/* Header */}
      <div className="sheet-header-row">
        <div className="sheet-title-group">
          <MapPin size={18} className="sheet-pin-icon text-primary" aria-hidden="true" />
          <div>
            <h3 className="sheet-title">Thông tin môi trường gần bạn</h3>
            <span className="sheet-sub">
              {sourceLabel} • Toạ độ: {userLocation[0].toFixed(4)}, {userLocation[1].toFixed(4)}
              {userLocationAccuracy ? ` (±${Math.round(userLocationAccuracy)}m)` : ""}
            </span>
          </div>
        </div>
        <button
          type="button"
          className="sheet-close-btn"
          onClick={onClose}
          aria-label="Đóng thông tin gần bạn"
        >
          <X size={18} />
        </button>
      </div>

      {/* Location Switcher Quick Bar */}
      <div className="near-me-location-switchers">
        <span className="switchers-label">Thay đổi vị trí:</span>
        <div className="switchers-buttons-group">
          {onLocateGps && (
            <button
              type="button"
              className={`near-me-switch-btn ${userLocationSource === "gps" ? "active" : ""}`}
              onClick={onLocateGps}
              disabled={isLocating}
            >
              <LocateFixed size={13} />
              <span>{isLocating ? "Đang tìm GPS..." : "Bắt GPS"}</span>
            </button>
          )}
          {onStartPickOnMap && (
            <button
              type="button"
              className={`near-me-switch-btn ${userLocationSource === "manual_click" ? "active" : ""}`}
              onClick={() => {
                onStartPickOnMap();
                onClose();
              }}
            >
              <Crosshair size={13} />
              <span>Chọn trên Map</span>
            </button>
          )}
        </div>
      </div>

      {/* Current User Location Card */}
      <div className="near-me-current-loc-badge">
        <div className="loc-badge-icon">📍</div>
        <div className="loc-badge-info">
          <strong className="loc-badge-name">{userLocationName}</strong>
          <span className="loc-badge-coords">
            Kinh độ: {userLocation[1].toFixed(5)}, Vĩ độ: {userLocation[0].toFixed(5)}
          </span>
        </div>
      </div>

      {/* Nearest Station Card */}
      {nearestSt ? (
        <div className="nearest-station-card">
          <div className="nearest-station-header">
            <div className="nearest-tag">
              <Navigation size={13} />
              <span>Trạm quan trắc gần nhất ({nearestResult.formattedDistance})</span>
            </div>
            <span className={`station-live-status-pill ${nearestSt.status}`}>
              {nearestSt.status === "online" ? (
                <>
                  <CheckCircle2 size={11} /> Online
                </>
              ) : (
                <>
                  <ShieldAlert size={11} /> {nearestSt.status}
                </>
              )}
            </span>
          </div>

          <div className="nearest-station-body">
            <div className="nearest-station-title-row">
              <h4>{nearestSt.station_name}</h4>
              <span className="nearest-station-code">{nearestSt.station_id}</span>
            </div>

            <div className="nearest-metric-highlight">
              <div
                className="nearest-aqi-chip"
                style={{ backgroundColor: getAqiColor(nearestSt.aqi) }}
              >
                <span className="aqi-label">AQI</span>
                <span className="aqi-value">{nearestSt.aqi ?? "—"}</span>
              </div>
              <div className="nearest-aqi-text">
                <strong>{getAqiLevelText(nearestSt.aqi)}</strong>
                <span>PM2.5: {nearestSt.pm25 ?? "—"} µg/m³ • CO2: {nearestSt.co2 ?? "—"} ppm</span>
              </div>
            </div>

            {onSelectStation && (
              <button
                type="button"
                className="nearest-view-details-btn"
                onClick={() => {
                  onSelectStation(nearestSt.station_id);
                }}
              >
                <span>Xem phân tích chi tiết trạm này</span>
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="near-me-unavailable-state">
          <MapPin size={24} aria-hidden="true" />
          <div>
            <strong>Chưa có dữ liệu trạm quan trắc xung quanh</strong>
            <p>Hãy kiểm tra lại kết nối simulator hoặc thử chọn lại vị trí khác.</p>
          </div>
        </div>
      )}

      <p className="today-simulator-note">
        Dữ liệu đo đạc trực tiếp từ trạm sensor lân cận, không nội suy giả định.
      </p>

      {/* Footer Ask AI Action */}
      <div className="near-me-footer-actions">
        <button
          type="button"
          className="sheet-btn primary"
          onClick={onOpenAiChat}
        >
          <Sparkles size={15} aria-hidden="true" />
          <span>Hỏi AirGuard AI về chất lượng không khí tại đây</span>
        </button>
      </div>
    </div>
  );
};

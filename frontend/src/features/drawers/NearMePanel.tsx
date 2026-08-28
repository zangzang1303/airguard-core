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
  isPickingOnMap?: boolean;
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
  isPickingOnMap = false,
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
    <div className={`floating-bottom-sheet near-me-sheet ${isPickingOnMap ? "is-picking-map" : ""}`}>
      <div className="sheet-header-row">
        <div className="sheet-title-group">
          <span className="near-me-header-icon" aria-hidden="true">
            <MapPin size={19} />
          </span>
          <div className="near-me-heading-copy">
            <span className="near-me-eyebrow">Không khí quanh bạn</span>
            <h3 className="sheet-title">Thông tin môi trường gần bạn</h3>
            <span className="sheet-sub">
              {sourceLabel} · {userLocation[0].toFixed(4)}, {userLocation[1].toFixed(4)}
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

      <section className="near-me-location-switchers" aria-labelledby="near-me-location-title">
        <div className="near-me-section-heading">
          <div>
            <strong id="near-me-location-title">Chọn vị trí tham chiếu</strong>
            <span>Dùng GPS hoặc chạm trực tiếp lên bản đồ</span>
          </div>
        </div>
        <div className="switchers-buttons-group">
          {onLocateGps && (
            <button
              type="button"
              className={`near-me-switch-btn ${userLocationSource === "gps" ? "active" : ""}`}
              onClick={onLocateGps}
              disabled={isLocating}
              aria-pressed={userLocationSource === "gps"}
            >
              <span className="near-me-switch-icon" aria-hidden="true">
                <LocateFixed size={17} />
              </span>
              <span className="near-me-switch-copy">
                <strong>{isLocating ? "Đang định vị..." : "Vị trí hiện tại"}</strong>
                <small>GPS của thiết bị</small>
              </span>
            </button>
          )}
          {onStartPickOnMap && (
            <button
              type="button"
              className={`near-me-switch-btn ${isPickingOnMap || userLocationSource === "manual_click" ? "active" : ""}`}
              onClick={onStartPickOnMap}
              aria-pressed={isPickingOnMap || userLocationSource === "manual_click"}
            >
              <span className="near-me-switch-icon" aria-hidden="true">
                <Crosshair size={17} />
              </span>
              <span className="near-me-switch-copy">
                <strong>{isPickingOnMap ? "Đang chờ bạn chọn" : "Chọn trên bản đồ"}</strong>
                <small>Chạm một điểm bất kỳ</small>
              </span>
            </button>
          )}
        </div>
        {isPickingOnMap && (
          <p className="near-me-picking-hint" role="status">
            <Crosshair size={14} aria-hidden="true" />
            Panel vẫn mở — hãy chạm một điểm trên phần bản đồ còn hiển thị.
          </p>
        )}
      </section>

      <div className="near-me-current-loc-badge">
        <span className="loc-badge-icon" aria-hidden="true"><MapPin size={18} /></span>
        <div className="loc-badge-info">
          <span className="loc-badge-label">Điểm đang xem</span>
          <strong className="loc-badge-name">{userLocationName}</strong>
          <span className="loc-badge-coords">
            {userLocation[0].toFixed(5)}, {userLocation[1].toFixed(5)}
          </span>
        </div>
      </div>

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
                style={{
                  backgroundColor: getAqiColor(nearestSt.aqi),
                  color: nearestSt.aqi !== null && nearestSt.aqi !== undefined && nearestSt.aqi <= 100
                    ? "#172033"
                    : "#ffffff",
                }}
              >
                <span className="aqi-label">AQI</span>
                <span className="aqi-value">{nearestSt.aqi ?? "—"}</span>
              </div>
              <div className="nearest-aqi-text">
                <strong>{getAqiLevelText(nearestSt.aqi)}</strong>
                <span>Chỉ số tổng quan tại trạm gần nhất</span>
              </div>
            </div>

            <div className="nearest-secondary-metrics" aria-label="Chỉ số thành phần">
              <div>
                <span>PM2.5</span>
                <strong>{nearestSt.pm25 ?? "—"} <small>µg/m³</small></strong>
              </div>
              <div>
                <span>CO₂</span>
                <strong>{nearestSt.co2 ?? "—"} <small>ppm</small></strong>
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
        Dữ liệu từ trạm mô phỏng gần nhất; không nội suy cho thẻ này và không phải quan trắc chính thức.
      </p>

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

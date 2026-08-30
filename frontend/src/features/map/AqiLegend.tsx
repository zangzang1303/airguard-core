import React, { useState } from "react";
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock,
  Compass,
  Cpu,
  Info,
  Layers,
  RefreshCw,
  Wind,
  X,
} from "lucide-react";
import { getMetricScale } from "../../constants/metrics";
import { STATION_STATUS_CONFIG } from "../../constants/stationStatus";
import { SpatialHeatmapResponse, StationStatus } from "../../types";
import {
  formatVnDateTimeWithSeconds,
  formatVnTimeWithSeconds,
} from "../../utils/datetime";

// The heatmap raster uses alpha 195 and its Leaflet overlay uses opacity 0.60.
// Preview the resulting colour over the warm OSM land tone used by this map,
// so the legend communicates the colour users actually see on the map.
const HEATMAP_COMPOSITED_ALPHA = (195 / 255) * 0.60;
const HEATMAP_BASEMAP_COLOR = "#e8c59b";

export type MapLegendVariant = "stations" | "dispersion";

export function getFriendlyModelName(modelRaw: string | undefined): string {
  if (!modelRaw) return "IDW · Gió v1.0";
  if (modelRaw.includes("idw")) return "IDW · Gió v1.0";
  return modelRaw;
}

export function getFriendlyBadgeLabel(modelRaw: string | undefined, forecastHour: number): string {
  if (forecastHour > 0) {
    return `DỰ BÁO +${forecastHour}h`;
  }
  return "IDW · GIÓ";
}

/**
 * Unified Metric Color Scale Component (<MetricColorScale metric={selectedMetric} />)
 * Dynamically renders description, continuous proportional segmented color bar,
 * value ticks, unit, provisional disclaimer, and level labels for ANY metric.
 */
export const MetricColorScale: React.FC<{
  metric?: string;
  className?: string;
  style?: React.CSSProperties;
  heatmapPreview?: boolean;
}> = ({ metric = "aqi", className = "", style, heatmapPreview = false }) => {
  const scale = getMetricScale(metric);
  const minVal = scale.min;
  const maxVal = scale.max;
  const rangeTotal = maxVal - minVal;

  return (
    <div className={`aqi-bar-section metric-color-scale-wrapper ${className}`} style={style} aria-label={`Chú giải ${scale.label}`}>
      <div className="aqi-bar-guidance">
        <span>{scale.description}</span>
        {scale.provisional && (
          <span
            className="provisional-tag"
            style={{
              marginLeft: "6px",
              color: "#92400e",
              background: "#fef3c7",
              border: "1px solid #fde68a",
              padding: "1px 5px",
              borderRadius: "4px",
              fontSize: "0.65rem",
              fontWeight: 600,
              display: "inline-block",
            }}
          >
            * Ngưỡng tham khảo cho MVP
          </span>
        )}
      </div>

      {/* Proportional Segmented Color Bar */}
      <div
        className="aqi-color-bar-container"
        role="img"
        aria-label={`Thanh màu ${scale.label} từ ${scale.min} đến ${scale.max} ${scale.unit}`}
      >
        {scale.levels.map((level) => {
          const levelRange = level.max - level.min;
          const widthPercent = (levelRange / rangeTotal) * 100;
          return (
            <div
              key={level.classTag}
              className="aqi-color-segment"
              style={{
                width: `${widthPercent}%`,
                backgroundColor: heatmapPreview
                  ? blendHexColors(level.color, HEATMAP_BASEMAP_COLOR, HEATMAP_COMPOSITED_ALPHA)
                  : level.color,
              }}
              title={`${level.label}: ${level.min}–${level.max} ${scale.unit}`}
              aria-label={`${level.label}: ${level.min}–${level.max} ${scale.unit}`}
            />
          );
        })}
      </div>

      {/* Ticks Row Below Color Bar */}
      <div className="aqi-ticks-container">
        {scale.ticks.map((tick) => {
          const leftPercent = ((tick - minVal) / rangeTotal) * 100;
          let transform = "translateX(-50%)";
          let alignClass = "tick-center";

          if (tick === minVal) {
            transform = "translateX(0)";
            alignClass = "tick-left";
          } else if (tick === maxVal) {
            transform = "translateX(-100%)";
            alignClass = "tick-right";
          }

          return (
            <div
              key={tick}
              className={`aqi-tick-item ${alignClass}`}
              style={{ left: `${leftPercent}%`, transform }}
            >
              <span className="aqi-tick-mark" />
              <span className="aqi-tick-label">{tick}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

function blendHexColors(foreground: string, background: string, alpha: number): string {
  const toRgb = (hex: string) => {
    const value = Number.parseInt(hex.slice(1), 16);
    return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
  };
  const [fgRed, fgGreen, fgBlue] = toRgb(foreground);
  const [bgRed, bgGreen, bgBlue] = toRgb(background);
  const blendChannel = (fg: number, bg: number) => Math.round(fg * alpha + bg * (1 - alpha));
  return `rgb(${blendChannel(fgRed, bgRed)}, ${blendChannel(fgGreen, bgGreen)}, ${blendChannel(fgBlue, bgBlue)})`;
}

/**
 * Legacy Alias for AQI Color Scale
 */
export const AqiColorScale: React.FC<{ className?: string; style?: React.CSSProperties }> = (props) => (
  <MetricColorScale metric="aqi" {...props} />
);

// Sub-component 2: StationStatusLegend (Trạng thái trạm 4 nhóm đồng bộ)
export const StationStatusLegend: React.FC<{ className?: string }> = ({ className = "" }) => {
  const statusKeys: StationStatus[] = ["online", "stale", "offline", "invalid"];

  return (
    <div className={`aqi-status-indicators ${className}`} aria-label="Chú giải trạng thái cảm biến">
      {statusKeys.map((key) => {
        const config = STATION_STATUS_CONFIG[key];
        return (
          <span
            key={config.status}
            className="status-item"
            title={config.tooltipText}
          >
            <span
              className={`status-indicator-badge status-${config.status}`}
              aria-hidden="true"
            >
              <span className="status-symbol">{config.symbol}</span>
            </span>
            <span className="status-label-text">{config.label}</span>
          </span>
        );
      })}
    </div>
  );
};

// Sub-component 3: DispersionMetadata (Thông tin mô hình IDW, thời điểm tạo & gió)
export const DispersionMetadata: React.FC<{
  data: SpatialHeatmapResponse | null;
  forecastHour?: number;
}> = ({ data, forecastHour = 0 }) => {
  const [showDetail, setShowDetail] = useState(false);

  const modelCreatedTime = data?.generated_at ? formatVnDateTimeWithSeconds(data.generated_at) : "Đang cập nhật...";
  const forecastValidTime = data?.timestamp ? formatVnDateTimeWithSeconds(data.timestamp) : "Đang tính toán...";
  const modelName = getFriendlyModelName(data?.model_version || data?.source);
  const windSpeed = data?.wind_speed_ms != null ? `${data.wind_speed_ms.toFixed(1)} m/s` : "3.2 m/s";
  const windDeg = data?.wind_direction_deg != null ? `${data.wind_direction_deg}°` : "135°";

  return (
    <div className="dispersion-metadata-block">
      <div className="dispersion-grid">
        <div className="dispersion-grid-item" title="Thời điểm backend tạo mô hình IDW">
          <Clock size={13} className="dispersion-icon" />
          <span>Mô hình tạo lúc: <strong>{modelCreatedTime}</strong></span>
        </div>

        {forecastHour > 0 && (
          <div className="dispersion-grid-item" title="Thời điểm dự báo có hiệu lực">
            <Clock size={13} className="dispersion-icon" style={{ color: "#d97706" }} />
            <span>Hiệu lực lúc: <strong>{forecastValidTime}</strong></span>
          </div>
        )}

        <div className="dispersion-grid-item" title="Tên mô hình nội suy không gian">
          <Cpu size={13} className="dispersion-icon" />
          <span>Mô hình: <strong>{modelName}</strong></span>
        </div>

        <div className="dispersion-grid-item" title="Tốc độ gió giả lập">
          <Wind size={13} className="dispersion-icon" />
          <span>Gió: <strong>{windSpeed}</strong></span>
        </div>

        <div className="dispersion-grid-item" title="Hướng gió">
          <Compass
            size={13}
            className="dispersion-icon"
            style={{ transform: `rotate(${data?.wind_direction_deg || 135}deg)`, transition: "transform 0.3s ease" }}
          />
          <span>Hướng: <strong>{windDeg}</strong></span>
        </div>
      </div>

      <div className="dispersion-detail-trigger">
        <button
          type="button"
          className="dispersion-toggle-btn no-drag"
          data-no-drag="true"
          onClick={() => setShowDetail(!showDetail)}
          aria-expanded={showDetail}
        >
          <Info size={12} />
          <span>{showDetail ? "Ẩn chi tiết phương pháp IDW" : "Xem chi tiết phương pháp IDW"}</span>
        </button>

        {showDetail && (
          <div className="dispersion-detail-box">
            <div><strong>Mã mô hình:</strong> <code>{data?.source || "spatial_idw_dispersion_model"}</code></div>
            <div><strong>Phiên bản:</strong> <code>{data?.model_version || "idw-dispersion-v1.0"}</code></div>
            {data?.generated_at && (
              <div><strong>Thời điểm tạo mô hình:</strong> <code>{formatVnDateTimeWithSeconds(data.generated_at)}</code></div>
            )}
            {data?.timestamp && (
              <div><strong>Mốc thời gian hiệu lực:</strong> <code>{formatVnDateTimeWithSeconds(data.timestamp)}</code></div>
            )}
            {data?.weather?.observed_at && (
              <div><strong>Thời điểm dữ liệu gió:</strong> <code>{formatVnDateTimeWithSeconds(data.weather.observed_at)}</code></div>
            )}
            {data?.station_inputs && data.station_inputs.length > 0 && (
              <div>
                <strong>Thời điểm trạm đầu vào:</strong>{" "}
                <code>
                  {data.station_inputs
                    .map((s) => `${s.station_id}: ${formatVnTimeWithSeconds(s.observed_at)}`)
                    .join(", ")}
                </code>
              </div>
            )}
            <div style={{ marginTop: "4px", lineHeight: "1.3" }}>
              Nội suy trọng số khoảng cách ngược (IDW) với power $p=2.0$, kết hợp vector phát tán khí tượng trong ranh giới Ocean Park 1.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Sub-component 4: SimulationDisclaimer
export const SimulationDisclaimer: React.FC<{ text?: string }> = ({
  text = "* Dữ liệu mô phỏng cho MVP · Không phải quan trắc chính thức.",
}) => <div className="aqi-disclaimer-text">{text}</div>;

export interface UnifiedMapLegendProps {
  variant?: MapLegendVariant;
  showStationStatus?: boolean;
  metric?: string;
  forecastHour?: number;
  dispersionData?: SpatialHeatmapResponse | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  headerProps?: any;
  onClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

/**
 * Unified Context-Aware Map Legend Component
 * Seamlessly adapts between "stations" mode and "dispersion" (heatmap) mode.
 * Always renders exactly ONE MetricColorScale, avoiding duplicates.
 */
export const AqiLegend: React.FC<UnifiedMapLegendProps> = ({
  variant = "stations",
  showStationStatus = true,
  metric = "aqi",
  forecastHour = 0,
  dispersionData = null,
  loading = false,
  error = null,
  onRetry,
  headerProps,
  onClose,
  isCollapsed: controlledCollapsed,
  onToggleCollapse,
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;
  const handleToggleCollapse = onToggleCollapse || (() => setInternalCollapsed((prev) => !prev));

  const scale = getMetricScale(metric);
  const isDispersion = variant === "dispersion";

  const headerTitle = isDispersion
    ? `Bản đồ lan truyền ${scale.label}`
    : showStationStatus
    ? `Chú giải ${scale.label} & Trạng thái trạm`
    : `Chú giải ${scale.label}`;

  return (
    <div className={`aqi-legend-card unified-map-legend ${isDispersion ? "dispersion-variant" : "stations-variant"}`}>
      {/* 1. Header Bar with Drag Handle, Badge, Collapse and Close */}
      <div className="aqi-legend-header unified-legend-header">
        <div className="legend-title-drag-area" {...headerProps}>
          {isDispersion ? (
            <Layers size={15} className="legend-header-icon dispersion-icon-tint" />
          ) : (
            <Activity size={15} className="legend-header-icon station-icon-tint" />
          )}
          <span className="aqi-legend-title-text">{headerTitle}</span>
        </div>

        <div className="legend-header-controls">
          {isDispersion && (
            <span className={`header-badge ${forecastHour > 0 ? "badge-forecast" : ""}`}>
              {getFriendlyBadgeLabel(dispersionData?.model_version || dispersionData?.source, forecastHour)}
            </span>
          )}

          <button
            type="button"
            className="no-drag panel-collapse-btn"
            data-no-drag="true"
            onClick={handleToggleCollapse}
            title={isCollapsed ? "Mở rộng chú giải" : "Thu gọn chú giải"}
            aria-label={isCollapsed ? "Mở rộng chú giải" : "Thu gọn chú giải"}
          >
            {isCollapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          </button>

          {onClose && (
            <button
              type="button"
              className="no-drag legend-close-btn"
              data-no-drag="true"
              onClick={onClose}
              aria-label="Ẩn chú giải"
              title="Ẩn chú giải"
            >
              <X size={15} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      {/* 2. Expanded Body Content */}
      {!isCollapsed && (
        <div className="aqi-legend-body">
          {isDispersion && loading && (
            <div className="unified-loading-state">
              <RefreshCw size={14} className="spin-icon" />
              <span>Đang cập nhật mô hình {scale.label}...</span>
            </div>
          )}

          {isDispersion && error && (
            <div className="unified-error-state" role="alert">
              <div className="error-title-row">
                <AlertTriangle size={14} />
                <strong>Không thể tải mô hình</strong>
              </div>
              <p className="error-message-text">{error}</p>
              {onRetry && (
                <button type="button" onClick={onRetry} className="error-retry-btn">
                  <RefreshCw size={12} /> Thử lại
                </button>
              )}
            </div>
          )}

          {(!isDispersion || (!loading && !error)) && (
            <>
              {/* MetricColorScale is rendered strictly ONCE */}
              <MetricColorScale metric={metric} heatmapPreview={isDispersion} />

              {/* Context-aware secondary information */}
              {isDispersion ? (
                <DispersionMetadata data={dispersionData} forecastHour={forecastHour} />
              ) : (
                showStationStatus && <StationStatusLegend />
              )}

              <SimulationDisclaimer />
            </>
          )}
        </div>
      )}
    </div>
  );
};

export const UnifiedMapLegend = AqiLegend;

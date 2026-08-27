import React, { useState } from "react";
import { Clock, Compass, Cpu, Info, Wind } from "lucide-react";
import { getMetricScale, getMetricTicks, METRIC_SCALES } from "../../constants/metrics";
import { STATION_STATUS_CONFIG } from "../../constants/stationStatus";
import { SpatialHeatmapResponse, StationStatus } from "../../types";
import { formatVnDateTime, formatVnDateTimeWithSeconds, formatVnTimeWithSeconds } from "../../utils/datetime";

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
}> = ({ metric = "aqi", className = "", style }) => {
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
                backgroundColor: level.color,
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
          className="dispersion-toggle-btn"
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

export const AqiLegend: React.FC<{
  showStationStatus?: boolean;
  metric?: string;
  headerProps?: any;
}> = ({ showStationStatus = false, metric = "aqi", headerProps }) => {
  const scale = getMetricScale(metric);
  const headerTitle = showStationStatus
    ? `Chú giải ${scale.label} & Trạng thái trạm`
    : `Chú giải ${scale.label}`;

  return (
    <div className="aqi-legend-card">
      <div className="aqi-legend-header" {...headerProps}>{headerTitle}</div>
      <MetricColorScale metric={metric} />
      {showStationStatus && <StationStatusLegend />}
      <SimulationDisclaimer />
    </div>
  );
};

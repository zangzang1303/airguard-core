import React from "react";
import { Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { Station } from "../../types";
import { EnvironmentalLayerType } from "../../types/superApp";
import { getAqiLevel } from "../../constants/aqi";
import { getMetricLevel } from "../../constants/metrics";
import {
  getStationStatusConfig,
  resolveStationStatus,
} from "../../constants/stationStatus";
import { formatVnDateTime } from "../../utils/datetime";

export function getAqiColorHex(aqi: number | null | undefined): string {
  if (aqi == null) return "#64748b";
  return getAqiLevel(aqi).color;
}

interface SensorMarkersProps {
  stations: Station[];
  selectedStationId: string | null;
  criticalStationIds?: ReadonlySet<string> | string[];
  onSelectStation: (stationId: string) => void;
  showSensors?: boolean;
  activeMetric?: EnvironmentalLayerType;
}

/**
 * Standardized Sensor Station Icon for S01–S05
 * Features:
 * - Station Code Pill (e.g. S01, S02, S03, S04, S05)
 * - Metric value or status symbol inside core badge
 * - 4 distinct visual border styles and symbols for status (Online, Stale, Offline, Invalid)
 * - Distinct Pin Tail
 * - Selected highlight and critical indicator
 */
function createSensorStationIcon(
  stationId: string,
  metricValue: number | null | undefined,
  badgeColor: string,
  isSelected: boolean,
  isCritical: boolean,
  status: "online" | "stale" | "offline" | "invalid"
): L.DivIcon {
  const statusConfig = getStationStatusConfig(status);
  const selectedClass = isSelected ? "sensor-pin-selected" : "";
  const criticalClass = isCritical ? "sensor-pin-critical" : "";
  const statusClass = `status-${status}`;

  // Formatted display value: if offline or invalid -> show status symbol or "—"
  let displayValue = "—";
  let symbolHtml = "";
  if (status === "online" || status === "stale") {
    if (metricValue != null && !Number.isNaN(metricValue)) {
      displayValue = Math.round(metricValue).toString();
    }
  } else if (status === "offline") {
    symbolHtml = `<span class="status-marker-symbol" aria-hidden="true">✖</span>`;
  } else if (status === "invalid") {
    symbolHtml = `<span class="status-marker-symbol" aria-hidden="true">?</span>`;
  }

  return L.divIcon({
    className: "custom-sensor-station-icon",
    html: `
      <div
        class="sensor-station-pin ${selectedClass} ${criticalClass} ${statusClass}"
        style="--badge-color: ${badgeColor}; --border-style: ${statusConfig.borderStyle};"
        role="button"
        aria-label="Trạm ${stationId} - Trạng thái: ${statusConfig.label}"
      >
        <span class="station-code-pill">${stationId}</span>
        <div class="sensor-value-core">
          ${symbolHtml}
          <span class="metric-num">${displayValue}</span>
          ${isCritical ? '<div class="badge-ring" aria-hidden="true"></div>' : ""}
        </div>
        <div class="marker-pin-tail" aria-hidden="true"></div>
      </div>
    `,
    iconSize: [40, 48],
    iconAnchor: [20, 46],
  });
}

function getMetricDisplay(station: Station, metric: EnvironmentalLayerType = "aqi") {
  switch (metric) {
    case "pm25":
      return {
        val: station.pm25,
        unit: "µg/m³",
        label: "PM2.5",
        level: getMetricLevel("pm25", station.pm25 ?? 0),
      };
    case "co2":
      return {
        val: station.co2,
        unit: "ppm",
        label: "CO2",
        level: getMetricLevel("co2", station.co2 ?? 0),
      };
    case "noise_db":
      return {
        val: station.noise_db,
        unit: "dB",
        label: "Tiếng ồn",
        level: getMetricLevel("noise_db", station.noise_db ?? 0),
      };
    case "temperature":
      return {
        val: station.temperature,
        unit: "°C",
        label: "Nhiệt độ",
        level: getMetricLevel("temperature", station.temperature ?? 0),
      };
    case "humidity":
      return {
        val: station.humidity,
        unit: "%",
        label: "Độ ẩm",
        level: getMetricLevel("humidity", station.humidity ?? 0),
      };
    case "aqi":
    default: {
      const aqiVal = station.aqi ?? (station.pm25 != null ? Math.round(station.pm25 * 2) : 0);
      return {
        val: aqiVal,
        unit: "AQI",
        label: "AQI",
        level: getAqiLevel(aqiVal),
      };
    }
  }
}

export const SensorMarkers: React.FC<SensorMarkersProps> = ({
  stations,
  selectedStationId,
  criticalStationIds,
  onSelectStation,
  showSensors = true,
  activeMetric = "aqi",
}) => {
  if (!showSensors) return null;

  const isStationCritical = (stationId: string) => {
    if (!criticalStationIds) return false;
    if (criticalStationIds instanceof Set) {
      return criticalStationIds.has(stationId);
    }
    if (Array.isArray(criticalStationIds)) {
      return criticalStationIds.includes(stationId);
    }
    return false;
  };

  return (
    <>
      {stations.map((station) => {
        const isSelected = selectedStationId === station.station_id;
        const isCritical = isStationCritical(station.station_id);
        const resolvedStatus = resolveStationStatus(station);
        const statusConfig = getStationStatusConfig(resolvedStatus);

        const metricData = getMetricDisplay(station, activeMetric);
        const color = resolvedStatus === "invalid"
          ? "#64748b"
          : resolvedStatus === "offline"
          ? "#ef4444"
          : resolvedStatus === "stale"
          ? "#f59e0b"
          : metricData.level.color;

        const icon = createSensorStationIcon(
          station.station_id,
          metricData.val,
          color,
          isSelected,
          isCritical,
          resolvedStatus
        );

        return (
          <Marker
            key={station.station_id}
            position={[station.latitude, station.longitude]}
            icon={icon}
            eventHandlers={{
              click: () => onSelectStation(station.station_id),
            }}
          >
            <Tooltip direction="top" offset={[0, -42]} opacity={0.96} permanent={false}>
              <div className="sensor-map-tooltip">
                <div className="tooltip-title">
                  <span className="tooltip-station-tag">{station.station_id}</span>
                  <span>{station.station_name || `Trạm ${station.station_id}`}</span>
                </div>

                {resolvedStatus === "invalid" && (
                  <div className="tooltip-aqi-row">
                    <span className="tooltip-aqi-pill" style={{ backgroundColor: "#64748b" }}>
                      <span className="tooltip-status-icon">?</span> Trạng thái: Invalid
                    </span>
                    <span className="tooltip-category">Dữ liệu không hợp lệ</span>
                  </div>
                )}

                {resolvedStatus === "offline" && (
                  <div className="tooltip-aqi-row">
                    <span className="tooltip-aqi-pill" style={{ backgroundColor: "#ef4444" }}>
                      <span className="tooltip-status-icon">✖</span> Trạng thái: Offline
                    </span>
                    <span className="tooltip-category">Mất kết nối</span>
                  </div>
                )}

                {resolvedStatus === "stale" && (
                  <>
                    <div className="tooltip-aqi-row">
                      <span className="tooltip-aqi-pill" style={{ backgroundColor: "#f59e0b" }}>
                        <span className="tooltip-status-icon">▲</span> {metricData.val ?? "—"} {metricData.unit}
                      </span>
                      <span className="tooltip-category">Cảnh báo: Dữ liệu cũ (Stale)</span>
                    </div>
                  </>
                )}

                {resolvedStatus === "online" && (
                  <div className="tooltip-aqi-row">
                    <span className="tooltip-aqi-pill" style={{ backgroundColor: color }}>
                      <span className="tooltip-status-icon">●</span> {metricData.val ?? "—"} {metricData.unit}
                    </span>
                    <span className="tooltip-category">{metricData.level.label}</span>
                  </div>
                )}

                <div className="tooltip-meta">
                  <span>Trạng thái: <strong>{statusConfig.label}</strong></span>
                  <span>Cập nhật: {station.updated_at ? formatVnDateTime(station.updated_at) : "Chưa có"}</span>
                </div>
              </div>
            </Tooltip>
          </Marker>
        );
      })}
    </>
  );
};

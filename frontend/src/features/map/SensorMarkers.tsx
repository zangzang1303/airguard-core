import React from "react";
import { Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { Station } from "../../types";
import { EnvironmentalLayerType } from "../../types/superApp";
import { getAqiColorHex, getAqiCategoryLabel } from "../../constants/aqi";
import { getMetricPresentation, formatMetricValue } from "../../utils/metricPresentation";

export { getAqiColorHex, getAqiCategoryLabel };

export interface SensorMarkersProps {
  stations: Station[];
  selectedStationId: string | null;
  criticalStationIds: ReadonlySet<string>;
  onSelectStation: (stationId: string) => void;
  showSensors: boolean;
  activeMetric?: EnvironmentalLayerType;
}

export function createMetricBadgeIcon(
  displayVal: string,
  color: string,
  isSelected: boolean,
  isCritical: boolean
) {
  const selectedClass = isSelected ? "sensor-badge-selected" : "";
  const criticalClass = isCritical ? "sensor-badge-critical" : "";

  return L.divIcon({
    className: "custom-sensor-div-icon",
    html: `
      <div class="sensor-aqi-badge ${selectedClass} ${criticalClass}" style="--badge-color: ${color}">
        ${isCritical ? '<div class="badge-ring" aria-hidden="true"></div>' : ""}
        <span class="badge-number">${displayVal}</span>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

export const createAqiBadgeIcon = (
  aqi: number | null | undefined,
  isSelected: boolean,
  dataState: "fresh" | "stale" | "unavailable",
  isCritical: boolean
) => {
  const color =
    dataState === "stale"
      ? "#f59e0b"
      : dataState === "unavailable"
      ? "#94a3b8"
      : getAqiColorHex(aqi);
  const displayVal = aqi !== null && aqi !== undefined ? Math.round(aqi).toString() : "—";
  return createMetricBadgeIcon(displayVal, color, isSelected, isCritical);
};

export const SensorMarkers: React.FC<SensorMarkersProps> = ({
  stations,
  selectedStationId,
  criticalStationIds,
  onSelectStation,
  showSensors,
  activeMetric = "aqi",
}) => {
  if (!showSensors) return null;

  const presentation = getMetricPresentation(activeMetric);

  return (
    <>
      {stations.map((station) => {
        const isSelected = selectedStationId === station.station_id;
        const hasUsableCurrentData = station.status === "online" && !station.is_stale;
        const rawVal = hasUsableCurrentData ? presentation.extractValue(station) : null;
        const displayVal =
          hasUsableCurrentData && rawVal !== null
            ? presentation.formatValue(rawVal)
            : "—";

        const dataState = hasUsableCurrentData
          ? "fresh"
          : station.is_stale || station.status === "stale"
          ? "stale"
          : "unavailable";

        const color =
          dataState === "stale"
            ? "#f59e0b"
            : dataState === "unavailable"
            ? "#94a3b8"
            : rawVal !== null
            ? presentation.getColor(rawVal)
            : "#94a3b8";

        const isCritical = hasUsableCurrentData && criticalStationIds.has(station.station_id);
        const icon = createMetricBadgeIcon(displayVal, color, isSelected, isCritical);

        const level = rawVal !== null ? presentation.getLevel(rawVal) : null;
        const levelLabel =
          level?.label ||
          (dataState === "stale"
            ? "Dữ liệu cũ"
            : dataState === "unavailable"
            ? "Không khả dụng"
            : "Chưa có dữ liệu");

        return (
          <Marker
            key={station.station_id}
            position={[station.latitude, station.longitude]}
            icon={icon}
            eventHandlers={{
              click: () => onSelectStation(station.station_id),
            }}
          >
            <Tooltip direction="top" offset={[0, -18]} opacity={1}>
              <div className="sensor-map-tooltip">
                <div className="tooltip-title">
                  {station.station_name}
                </div>
                <div className="tooltip-aqi-row">
                  <span
                    className="tooltip-aqi-pill"
                    style={{ backgroundColor: color }}
                  >
                    {presentation.shortLabel} {displayVal} {rawVal !== null && presentation.unit && displayVal !== "—" ? presentation.unit : ""}
                  </span>
                  <span className="tooltip-category">{levelLabel}</span>
                </div>
                <div className="tooltip-meta">
                  <span className="meta-tag">Cảm biến {station.station_id}</span>
                  {hasUsableCurrentData && activeMetric !== "pm25" && station.pm25 !== null && station.pm25 !== undefined && (
                    <span className="meta-val">PM2.5: {formatMetricValue("pm25", station.pm25)} µg/m³</span>
                  )}
                  {hasUsableCurrentData && activeMetric !== "aqi" && station.aqi !== null && station.aqi !== undefined && (
                    <span className="meta-val">AQI: {formatMetricValue("aqi", station.aqi)}</span>
                  )}
                  {!hasUsableCurrentData && (
                    <span
                      className="meta-val"
                      style={{ color: dataState === "stale" ? "#d97706" : "#ef4444" }}
                    >
                      {dataState === "stale" ? "Cảnh báo: Dữ liệu cũ" : "Trạng thái: Offline"}
                    </span>
                  )}
                </div>
              </div>
            </Tooltip>
          </Marker>
        );
      })}
    </>
  );
};

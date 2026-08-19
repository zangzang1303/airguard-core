import React from "react";
import { Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { Station } from "../../types";

interface SensorMarkersProps {
  stations: Station[];
  selectedStationId: string | null;
  onSelectStation: (stationId: string) => void;
  showSensors: boolean;
}

export function getAqiColorHex(aqi: number | null | undefined): string {
  if (aqi === null || aqi === undefined) return "#94a3b8"; // slate-400
  if (aqi <= 50) return "#10b981"; // Emerald/Green (Good)
  if (aqi <= 100) return "#eab308"; // Yellow (Moderate)
  if (aqi <= 150) return "#f97316"; // Orange (Unhealthy for sensitive)
  if (aqi <= 200) return "#ef4444"; // Red (Unhealthy)
  if (aqi <= 300) return "#8b5cf6"; // Purple (Very Unhealthy)
  return "#831843"; // Maroon (Hazardous)
}

export function getAqiCategoryLabel(aqi: number | null | undefined): { label: string; classTag: string } {
  if (aqi === null || aqi === undefined) return { label: "Không khả dụng", classTag: "na" };
  if (aqi <= 50) return { label: "Tốt (Good)", classTag: "good" };
  if (aqi <= 100) return { label: "Trung bình (Moderate)", classTag: "moderate" };
  if (aqi <= 150) return { label: "Kém (Sensitive)", classTag: "sensitive" };
  if (aqi <= 200) return { label: "Xấu (Unhealthy)", classTag: "unhealthy" };
  if (aqi <= 300) return { label: "Rất xấu (Very Unhealthy)", classTag: "very-unhealthy" };
  return { label: "Nguy hại (Hazardous)", classTag: "hazardous" };
}

// Function to generate customized Leaflet DivIcon for AQI badge
function createAqiBadgeIcon(aqi: number | null | undefined, isSelected: boolean, isStale: boolean) {
  const color = isStale ? "#f59e0b" : getAqiColorHex(aqi);
  const displayVal = aqi !== null && aqi !== undefined ? Math.round(aqi) : "—";
  const selectedClass = isSelected ? "sensor-badge-selected" : "";

  return L.divIcon({
    className: "custom-sensor-div-icon",
    html: `
      <div class="sensor-aqi-badge ${selectedClass}" style="--badge-color: ${color}">
        <div class="badge-ring"></div>
        <span class="badge-number">${displayVal}</span>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

export const SensorMarkers: React.FC<SensorMarkersProps> = ({
  stations,
  selectedStationId,
  onSelectStation,
  showSensors,
}) => {
  if (!showSensors) return null;

  return (
    <>
      {stations.map((station) => {
        const isSelected = selectedStationId === station.station_id;
        const icon = createAqiBadgeIcon(station.aqi, isSelected, station.is_stale);
        const { label: categoryLabel } = getAqiCategoryLabel(station.aqi);

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
                <div className="tooltip-title">{station.station_name}</div>
                <div className="tooltip-aqi-row">
                  <span
                    className="tooltip-aqi-pill"
                    style={{ backgroundColor: getAqiColorHex(station.aqi) }}
                  >
                    AQI {station.aqi ?? "—"}
                  </span>
                  <span className="tooltip-category">{categoryLabel}</span>
                </div>
                <div className="tooltip-meta">
                  <span className="meta-tag">Cảm biến {station.station_id}</span>
                  {station.pm25 !== null && station.pm25 !== undefined && (
                    <span className="meta-val">PM2.5: {station.pm25} µg/m³</span>
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

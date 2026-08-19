import React from "react";
import { Circle } from "react-leaflet";
import { Station } from "../../types";
import { EnvironmentalLayerType } from "../../types/superApp";
import { getAqiColorHex } from "./SensorMarkers";

interface EnvironmentalHeatmapLayerProps {
  stations: Station[];
  activeLayer: EnvironmentalLayerType;
  showHeatmap: boolean;
}

function getLayerValue(station: Station, layer: EnvironmentalLayerType): number | null {
  if (station.status === "offline" || station.is_stale) return null;
  switch (layer) {
    case "aqi":
      return station.aqi ?? station.pm25 ?? null;
    case "pm25":
      return station.pm25 ?? null;
    case "co2":
      return station.co2 ?? null;
    case "temperature":
      return station.temperature ?? null;
    case "noise_db":
      return station.noise_db ?? null;
    case "humidity":
      return station.humidity ?? null;
    default:
      return station.aqi ?? null;
  }
}

function getLayerColor(value: number | null, layer: EnvironmentalLayerType): string {
  if (value === null) return "transparent";
  switch (layer) {
    case "aqi":
    case "pm25":
      return getAqiColorHex(value);
    case "co2":
      if (value <= 600) return "#10b981";
      if (value <= 1000) return "#eab308";
      if (value <= 1500) return "#f97316";
      return "#ef4444";
    case "temperature":
      if (value < 26) return "#38bdf8";
      if (value <= 32) return "#10b981";
      if (value <= 36) return "#f97316";
      return "#ef4444";
    case "noise_db":
      if (value <= 55) return "#10b981";
      if (value <= 70) return "#eab308";
      if (value <= 85) return "#f97316";
      return "#ef4444";
    case "humidity":
      if (value <= 50) return "#38bdf8";
      if (value <= 75) return "#0284c7";
      return "#1d4ed8";
    default:
      return getAqiColorHex(value);
  }
}

export const EnvironmentalHeatmapLayer: React.FC<EnvironmentalHeatmapLayerProps> = ({
  stations,
  activeLayer,
  showHeatmap,
}) => {
  if (!showHeatmap) return null;

  return (
    <>
      {stations
        .filter((station) => station.status === "online" && !station.is_stale)
        .map((station) => {
          const rawVal = getLayerValue(station, activeLayer);
          if (rawVal === null) return null;
          const color = getLayerColor(rawVal, activeLayer);

          // Render a multi-tier subtle soft radial halo for smooth blending
          return (
            <React.Fragment key={`heat-${station.station_id}-${activeLayer}`}>
              {/* Outer soft dispersion ring */}
              <Circle
                center={[station.latitude, station.longitude]}
                radius={420}
                pathOptions={{
                  color: "transparent",
                  fillColor: color,
                  fillOpacity: 0.08,
                  interactive: false,
                }}
              />
              {/* Middle dispersion ring */}
              <Circle
                center={[station.latitude, station.longitude]}
                radius={260}
                pathOptions={{
                  color: "transparent",
                  fillColor: color,
                  fillOpacity: 0.14,
                  interactive: false,
                }}
              />
              {/* Core concentration zone */}
              <Circle
                center={[station.latitude, station.longitude]}
                radius={140}
                pathOptions={{
                  color: "transparent",
                  fillColor: color,
                  fillOpacity: 0.22,
                  interactive: false,
                }}
              />
            </React.Fragment>
          );
        })}
    </>
  );
};

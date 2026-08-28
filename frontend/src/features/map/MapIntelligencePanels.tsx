import React, { useMemo } from "react";
import { Activity, ChevronRight, Cloud, ShieldAlert, Thermometer, Volume2, Wind } from "lucide-react";
import { Alert, Station } from "../../types";
import { useDraggableFloatingPanel } from "../floating";

interface MapIntelligencePanelsProps {
  stations: Station[];
  alerts: Alert[];
  onOpenAlerts: () => void;
}

const aqiLabel = (value: number | null | undefined) => {
  if (value == null) return "Data unavailable";
  if (value <= 50) return "Good";
  if (value <= 100) return "Moderate";
  if (value <= 150) return "Sensitive groups";
  if (value <= 200) return "Unhealthy";
  return "Very unhealthy";
};

export const MapIntelligencePanels: React.FC<MapIntelligencePanelsProps> = ({
  stations,
  alerts,
  onOpenAlerts,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "air-quality-now",
    group: "widget",
  });

  const freshStations = useMemo(
    () => stations.filter((station) => station.status === "online" && !station.is_stale && station.aqi != null),
    [stations],
  );
  const focusStation = useMemo(
    () => [...freshStations].sort((a, b) => Number(b.aqi) - Number(a.aqi))[0] ?? null,
    [freshStations],
  );
  const activeAlert = useMemo(
    () => alerts.find((alert) => alert.status === "active" && alert.station_id === focusStation?.station_id)
      ?? alerts.find((alert) => alert.status === "active")
      ?? null,
    [alerts, focusStation],
  );
  const averageAqi = freshStations.length
    ? Math.round(freshStations.reduce((sum, station) => sum + Number(station.aqi), 0) / freshStations.length)
    : null;

  return (
    <aside {...containerProps} className="map-intelligence-stack" aria-label="Tổng quan chất lượng không khí">
      <section className="map-intelligence-summary" aria-label="Air quality now">
        <div className="map-panel-kicker" {...handleProps}>
          <Activity size={14} /> AIR QUALITY NOW
        </div>
        <div className="map-summary-main">
          <strong>{averageAqi ?? "—"}</strong>
          <div><span className={`map-aqi-badge map-aqi-badge--${averageAqi == null ? "neutral" : averageAqi <= 50 ? "good" : averageAqi <= 100 ? "moderate" : "warning"}`}>{aqiLabel(averageAqi)}</span><small>AQI · {freshStations.length}/{stations.length} fresh stations</small></div>
        </div>
        {focusStation ? (
          <div className="map-summary-metrics" aria-label={`Current readings at ${focusStation.station_id}`}>
            <span><Wind size={14} /> {focusStation.pm25 ?? "—"} µg/m³</span>
            <span><Cloud size={14} /> {focusStation.co2 ?? "—"} ppm</span>
            <span><Volume2 size={14} /> {focusStation.noise_db ?? "—"} dB</span>
            <span><Thermometer size={14} /> {focusStation.temperature ?? "—"} °C</span>
          </div>
        ) : <p className="map-panel-empty">Waiting for fresh validated station data.</p>}
        <div className="map-panel-source">SIMULATED DATA · backend-sourced</div>
      </section>

      {activeAlert && (
        <button type="button" className="map-alert-peek no-drag" data-no-drag="true" onClick={onOpenAlerts}>
          <ShieldAlert size={17} />
          <span><strong>{activeAlert.title}</strong><small>{activeAlert.station_id} · {activeAlert.severity}</small></span>
          <ChevronRight size={16} />
        </button>
      )}
    </aside>
  );
};

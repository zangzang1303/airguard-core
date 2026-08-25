import React, { useMemo } from "react";
import { Activity, Bot, ChevronRight, Cloud, ShieldAlert, Thermometer, Volume2, Wind } from "lucide-react";
import { Alert, Station } from "../../types";

interface MapIntelligencePanelsProps {
  stations: Station[];
  alerts: Alert[];
  onAskAi: (query: string) => void;
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
  onAskAi,
  onOpenAlerts,
}) => {
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
    <>
      <section className="map-intelligence-summary" aria-label="Air quality now">
        <div className="map-panel-kicker"><Activity size={14} /> Air quality now</div>
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

      <section className="map-ai-insight" aria-label="AirGuard AI insight">
        <div className="map-ai-insight__head"><span><Bot size={17} /> AirGuard AI Insight</span>{activeAlert && <button type="button" onClick={onOpenAlerts}>{alerts.filter((alert) => alert.status === "active").length} alerts</button>}</div>
        {focusStation ? (
          <>
            <h2>{focusStation.station_id} has the highest current AQI</h2>
            <p>AQI at {focusStation.station_id} is {focusStation.aqi}. This insight is based on the latest fresh station readings.</p>
            <div className="map-ai-recommendation"><span>Recommended next step</span><p>{activeAlert?.recommendation ?? "Review this station on the map and monitor the next validated update."}</p></div>
            <button type="button" className="map-ai-cta" onClick={() => onAskAi(`Phân tích dữ liệu mới nhất của trạm ${focusStation.station_id} và khuyến nghị phù hợp dựa trên bằng chứng hiện có.`)}>Ask AirGuard AI <ChevronRight size={16} /></button>
          </>
        ) : (
          <><h2>Insight pending data</h2><p>AirGuard AI will wait for valid, fresh measurements before making a recommendation.</p></>
        )}
      </section>

      {activeAlert && (
        <button type="button" className="map-alert-peek" onClick={onOpenAlerts}>
          <ShieldAlert size={17} />
          <span><strong>{activeAlert.title}</strong><small>{activeAlert.station_id} · {activeAlert.severity}</small></span>
          <ChevronRight size={16} />
        </button>
      )}
    </>
  );
};

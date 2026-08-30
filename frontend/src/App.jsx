import React, { useEffect, useMemo, useState } from "react";
import { Circle, CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function format(value, unit, digits = 1) {
  return value == null ? "—" : `${Number(value).toFixed(digits)} ${unit}`;
}

function getMarkerColor(pm25) {
  if (pm25 <= 25) return "#2f9e44";
  if (pm25 <= 50) return "#f59f00";
  if (pm25 <= 100) return "#e03131";
  return "#862e9c";
}

function getAqiColor(aqi, pm25) {
  if (Number.isFinite(aqi)) {
    if (aqi <= 50) return "#2f9e44";
    if (aqi <= 100) return "#f59f00";
    if (aqi <= 150) return "#f97316";
    if (aqi <= 200) return "#e03131";
    return "#862e9c";
  }
  return getMarkerColor(pm25);
}

export default function App() {
  const [stations, setStations] = useState([]);
  const [apiStatus, setApiStatus] = useState("Loading API data");
  const [showHeatmap, setShowHeatmap] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/stations`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("API request failed");
        }
        return response.json();
      })
      .then((data) => {
        setStations(data.items);
        setApiStatus("Simulator data from backend");
      })
      .catch(() => {
        setStations([]);
        setApiStatus("Backend unavailable");
      });
  }, []);

  const averagePm25 = useMemo(() => {
    if (!stations.length) return null;
    const total = stations.reduce((sum, station) => sum + Number(station.pm25 || 0), 0);
    return Math.round((total / stations.length) * 10) / 10;
  }, [stations]);
  const averageAqi = useMemo(() => {
    const values = stations.map((station) => station.aqi).filter(Number.isFinite);
    return values.length ? Math.round(values.reduce((sum, item) => sum + item, 0) / values.length) : null;
  }, [stations]);

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">AirGuard AI</p>
          <h1>Campus environmental monitoring</h1>
        </div>
        <div className="summary-panel">
          <span>Stations: {stations.length}</span>
          <span>Average AQI: {averageAqi ?? "—"}</span>
          <span>Average PM2.5: {averagePm25 ?? "—"} ug/m3</span>
          <span>{apiStatus}</span>
        </div>
      </section>

      <section className="map-layout">
        <div className="map-wrapper">
          <div className="map-toolbar">
            <div><strong>Bản đồ nhiệt AQI</strong><small>Trực quan hóa từ dữ liệu 5 trạm</small></div>
            <button className={`heatmap-toggle ${showHeatmap ? "is-active" : ""}`} onClick={() => setShowHeatmap((visible) => !visible)}>
              {showHeatmap ? "Ẩn vùng nhiệt" : "Hiện vùng nhiệt"}
            </button>
          </div>
        <MapContainer center={[20.9446, 105.9447]} zoom={16} scrollWheelZoom className="map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
          />
          {showHeatmap && stations.filter((station) => station.status === "online" && station.aqi != null).map((station) => {
            const color = getAqiColor(station.aqi, station.pm25);
            const radius = 95 + Math.min(Number(station.aqi) || 0, 250) * 1.1;
            return <Circle
              key={`heat-${station.station_id}`}
              center={[station.latitude, station.longitude]}
              radius={radius}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.17, weight: 0 }}
            />;
          })}
          {stations.map((station) => (
            <CircleMarker
              key={station.station_id}
              center={[station.latitude, station.longitude]}
              radius={12}
              pathOptions={{
                color: "#111827",
                weight: 2,
                fillColor: getAqiColor(station.aqi, station.pm25),
                fillOpacity: 0.9
              }}
            >
              <Popup>
                <strong>{station.station_name}</strong>
                <br />
                Station: {station.station_id}
                <br />
                AQI: {station.aqi ?? "—"} ({station.aqi_category || "unavailable"})
                <br />
                PM2.5: {format(station.pm25, "ug/m3")}
                <br />
                CO₂: {format(station.co2, "ppm", 0)}
                <br />
                Noise: {format(station.noise_db, "dB")}
                <br />
                Temperature: {format(station.temperature, "°C")}
                <br />
                Status: {station.status}
                <br />
                Updated: {station.updated_at}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
        <div className="heatmap-legend" aria-label="AQI heatmap legend">
          <span><i className="aqi-good" />Tốt 0–50</span><span><i className="aqi-moderate" />Trung bình 51–100</span><span><i className="aqi-sensitive" />Nhạy cảm 101–150</span><span><i className="aqi-unhealthy" />Không lành mạnh 151+</span>
        </div>
        <p className="heatmap-disclaimer">Vùng màu là ước tính trực quan quanh các trạm simulator theo AQI; không phải mô hình lan truyền, nội suy khoa học hoặc dữ liệu quan trắc chính thức.</p>
        </div>

        <aside className="station-list">
          {stations.map((station) => (
            <article key={station.station_id} className="station-card">
              <div>
                <h2>{station.station_name}</h2>
                <p>{station.station_id} - {station.status}</p>
              </div>
              <div className="pm25-value" style={{ color: getMarkerColor(station.pm25) }}>
                {station.aqi ?? "—"}
                <span>AQI</span>
              </div>
              <div className="station-metrics">CO₂ {format(station.co2, "ppm", 0)} · Noise {format(station.noise_db, "dB")} · {format(station.temperature, "°C")}</div>
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}

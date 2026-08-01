import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const fallbackStations = [
  { station_id: "S01", station_name: "Cong chinh", latitude: 20.9441, longitude: 105.9439, pm25: 42.5, status: "online", updated_at: "mock" },
  { station_id: "S02", station_name: "Bai do xe", latitude: 20.945, longitude: 105.9435, pm25: 55.2, status: "online", updated_at: "mock" },
  { station_id: "S03", station_name: "Truc duong chinh", latitude: 20.9445, longitude: 105.9452, pm25: 66.1, status: "online", updated_at: "mock" },
  { station_id: "S04", station_name: "Cong vien", latitude: 20.9455, longitude: 105.9458, pm25: 28.4, status: "online", updated_at: "mock" },
  { station_id: "S05", station_name: "Khu the thao ngoai troi", latitude: 20.9437, longitude: 105.9448, pm25: 35.9, status: "online", updated_at: "mock" }
];

function getPm25Level(pm25) {
  if (pm25 <= 25) return "Good";
  if (pm25 <= 50) return "Moderate";
  if (pm25 <= 100) return "Unhealthy";
  return "Very unhealthy";
}

function getMarkerColor(pm25) {
  if (pm25 <= 25) return "#2f9e44";
  if (pm25 <= 50) return "#f59f00";
  if (pm25 <= 100) return "#e03131";
  return "#862e9c";
}

export default function App() {
  const [stations, setStations] = useState(fallbackStations);
  const [apiStatus, setApiStatus] = useState("Loading API data");

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
        setApiStatus("Live mock API data");
      })
      .catch(() => {
        setStations(fallbackStations);
        setApiStatus("Local fallback data");
      });
  }, []);

  const averagePm25 = useMemo(() => {
    const total = stations.reduce((sum, station) => sum + Number(station.pm25 || 0), 0);
    return Math.round((total / stations.length) * 10) / 10;
  }, [stations]);

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">AirGuard AI</p>
          <h1>PM2.5 campus monitoring</h1>
        </div>
        <div className="summary-panel">
          <span>Stations: {stations.length}</span>
          <span>Average PM2.5: {averagePm25} ug/m3</span>
          <span>{apiStatus}</span>
        </div>
      </section>

      <section className="map-layout">
        <MapContainer center={[20.9446, 105.9447]} zoom={16} scrollWheelZoom className="map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {stations.map((station) => (
            <CircleMarker
              key={station.station_id}
              center={[station.latitude, station.longitude]}
              radius={12}
              pathOptions={{
                color: "#111827",
                weight: 2,
                fillColor: getMarkerColor(station.pm25),
                fillOpacity: 0.9
              }}
            >
              <Popup>
                <strong>{station.station_name}</strong>
                <br />
                Station: {station.station_id}
                <br />
                PM2.5: {station.pm25} ug/m3
                <br />
                Level: {getPm25Level(station.pm25)}
                <br />
                Status: {station.status}
                <br />
                Updated: {station.updated_at}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        <aside className="station-list">
          {stations.map((station) => (
            <article key={station.station_id} className="station-card">
              <div>
                <h2>{station.station_name}</h2>
                <p>{station.station_id} - {station.status}</p>
              </div>
              <div className="pm25-value" style={{ color: getMarkerColor(station.pm25) }}>
                {station.pm25}
                <span>ug/m3</span>
              </div>
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}

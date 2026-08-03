import React, { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { api } from "../../api/client";
import { DataQualityBadge, getPm25Severity } from "../../components/common/DataQualityBadge";
import { useAuth } from "../../context/AuthContext";
import { Station } from "../../types";

export const Dashboard: React.FC = () => {
  const { navigateTo, setSelectedStationId } = useAuth();
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchStations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStations();
      setStations(data);
    } catch (err: any) {
      setError("Không thể tải danh sách trạm từ máy chủ. Đang sử dụng dữ liệu mặc định.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStations();
  }, []);

  const filteredStations = useMemo(() => {
    return stations.filter(s =>
      s.station_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.station_id.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [stations, searchQuery]);

  const averagePm25 = useMemo(() => {
    const validStations = stations.filter(s => s.pm25 !== null && s.status === "online");
    if (validStations.length === 0) return 0;
    const total = validStations.reduce((sum, s) => sum + Number(s.pm25), 0);
    return Math.round((total / validStations.length) * 10) / 10;
  }, [stations]);

  const handleSelectStation = (stationId: string) => {
    setSelectedStationId(stationId);
    navigateTo("station-detail", { stationId });
  };

  return (
    <div className="dashboard-container">
      {/* Overview Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">📍</span>
          <div>
            <div className="stat-value">{stations.length}</div>
            <div className="stat-label">Trạm quan trắc (S01 - S05)</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">💨</span>
          <div>
            <div className="stat-value">{averagePm25} <small>µg/m³</small></div>
            <div className="stat-label">Nồng độ PM2.5 trung bình</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🟢</span>
          <div>
            <div className="stat-value">
              {stations.filter(s => s.status === "online" && !s.is_stale).length} / {stations.length}
            </div>
            <div className="stat-label">Trạm Online thời gian thực</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🔄</span>
          <div>
            <button className="btn-refresh" onClick={fetchStations} disabled={loading}>
              {loading ? "Đang tải..." : "Làm mới dữ liệu"}
            </button>
            <div className="stat-label">Cập nhật tự động</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert-box alert-warning">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Main Map & Station Side Panel Layout */}
      <div className="map-layout">
        <div className="map-wrapper">
          <MapContainer center={[20.9446, 105.9447]} zoom={16} scrollWheelZoom className="map">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filteredStations.map((station) => {
              const severity = getPm25Severity(station.pm25);
              return (
                <CircleMarker
                  key={station.station_id}
                  center={[station.latitude, station.longitude]}
                  radius={14}
                  pathOptions={{
                    color: "#0f172a",
                    weight: 3,
                    fillColor: severity.color,
                    fillOpacity: 0.95
                  }}
                  eventHandlers={{
                    click: () => handleSelectStation(station.station_id)
                  }}
                >
                  <Popup>
                    <div className="popup-content">
                      <h3>{station.station_name} ({station.station_id})</h3>
                      <div className="popup-pm25">
                        PM2.5: <strong>{station.pm25 ?? "N/A"} µg/m³</strong>
                      </div>
                      <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} />
                      <br /><br />
                      <button
                        className="btn-primary-sm"
                        onClick={() => handleSelectStation(station.station_id)}
                      >
                        Xem chi tiết trạm & Dự báo →
                      </button>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </div>

        {/* Side Panel Station List */}
        <aside className="station-sidebar">
          <div className="sidebar-header">
            <h2>Danh sách Trạm ({filteredStations.length})</h2>
            <input
              type="text"
              placeholder="Tìm kiếm trạm..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          {loading ? (
            <div className="skeleton-list">
              <div className="skeleton-card"></div>
              <div className="skeleton-card"></div>
              <div className="skeleton-card"></div>
            </div>
          ) : (
            <div className="station-cards-list">
              {filteredStations.map((station) => {
                const severity = getPm25Severity(station.pm25);
                return (
                  <article
                    key={station.station_id}
                    className="station-card"
                    onClick={() => handleSelectStation(station.station_id)}
                  >
                    <div className="station-card-info">
                      <span className="station-id-tag">{station.station_id}</span>
                      <h3>{station.station_name}</h3>
                      <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} />
                    </div>
                    <div className="station-card-value" style={{ color: severity.color }}>
                      {station.pm25 ?? "--"}
                      <span>µg/m³</span>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

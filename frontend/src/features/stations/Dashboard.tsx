import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  Bell,
  Clock3,
  Database,
  LocateFixed,
  MapPin,
  Radio,
  RefreshCw,
  Search,
  Sparkles,
  TriangleAlert,
  Thermometer,
  Volume2,
  Wifi,
  WifiOff,
  Wind,
} from "lucide-react";
import { Circle, CircleMarker, MapContainer, Polygon, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { DataQualityBadge } from "../../components/common/DataQualityBadge";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { Alert, Station } from "../../types";
import { formatVnDateTime } from "../../utils/datetime";

const severityLabel: Record<Alert["severity"], string> = {
  good: "Thấp",
  moderate: "Trung bình",
  warning: "Cao",
  critical: "Nghiêm trọng",
};

const getAqiColor = (aqi: number | null | undefined) => {
  if (aqi == null) return "var(--pm25-offline)";
  if (aqi <= 50) return "#22a06b";
  if (aqi <= 100) return "#e6a700";
  if (aqi <= 150) return "#f97316";
  if (aqi <= 200) return "#e5484d";
  return "#7c3aed";
};

// Simplified from OpenStreetMap way 761986888 (Vinhomes Ocean Park residential area),
// retrieved 2026-08-13. Dashboard scope only; it is not an administrative/legal boundary.
const OCEAN_PARK_1_BOUNDARY: [number, number][] = [
  [21.0047847, 105.9477604],
  [20.9933962, 105.9628773],
  [20.9890436, 105.9600712],
  [20.9852230, 105.9518985],
  [20.9840728, 105.9509930],
  [20.9851752, 105.9432602],
  [20.9921545, 105.9371584],
  [20.9968500, 105.9334673],
  [20.9980664, 105.9352872],
  [21.0017814, 105.9420739],
];

const MAP_OUTER_MASK: [number, number][] = [
  [85, -180],
  [85, 180],
  [-85, 180],
  [-85, -180],
];

const MAP_MAX_BOUNDS: [[number, number], [number, number]] = [
  [20.978, 105.925],
  [21.012, 105.971],
];

const MapFocus: React.FC = () => {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(OCEAN_PARK_1_BOUNDARY, { padding: [34, 34], maxZoom: 15 });
  }, [map]);
  return null;
};

export const Dashboard: React.FC = () => {
  const { navigateTo, setSelectedStationId } = useAuth();
  const [stations, setStations] = useState<Station[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeStationId, setActiveStationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showHeatmap, setShowHeatmap] = useState(true);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [stationData, alertData] = await Promise.all([api.getStations(), api.getAlerts()]);
      setStations(stationData);
      setAlerts(alertData);
      setActiveStationId((current) => {
        if (current && stationData.some((station) => station.station_id === current)) return current;
        return null;
      });
    } catch {
      setError("Không thể tải đầy đủ dữ liệu Dashboard. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") fetchDashboard();
    }, 30_000);
    const onVisible = () => {
      if (document.visibilityState === "visible") fetchDashboard();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [fetchDashboard]);

  const filteredStations = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase("vi");
    if (!query) return stations;
    return stations.filter((station) =>
      station.station_name.toLocaleLowerCase("vi").includes(query)
      || station.station_id.toLocaleLowerCase("vi").includes(query));
  }, [stations, searchQuery]);

  const selectedStation = useMemo(
    () => stations.find((station) => station.station_id === activeStationId) ?? null,
    [activeStationId, stations],
  );

  const validStations = useMemo(
    () => stations.filter((station) => station.pm25 !== null && station.status === "online" && !station.is_stale),
    [stations],
  );
  const averageAqi = validStations.length
    ? Math.round(validStations.reduce((sum, station) => sum + Number(station.aqi ?? 0), 0) / validStations.length)
    : null;
  const onlineCount = stations.filter((station) => station.status === "online").length;
  const freshOnlineCount = stations.filter((station) => station.status === "online" && !station.is_stale).length;
  const offlineCount = stations.filter((station) => station.status === "offline").length;
  const staleCount = stations.filter((station) => station.is_stale).length;
  const activeAlerts = alerts.filter((alert) => alert.status === "active");
  const heatColor = (station: Station) => getAqiColor(station.aqi);

  const selectStation = (stationId: string) => setActiveStationId(stationId);

  const openStationDetail = (stationId: string) => {
    setSelectedStationId(stationId);
    navigateTo("station-detail", { stationId });
  };

  const askAiAboutStation = (stationId: string) => {
    setSelectedStationId(stationId);
    navigateTo("agent");
  };

  return (
    <div className="dashboard-container dashboard-modern">
      <PageHeader
        title="Tổng quan chất lượng không khí"
        description="AQI là chỉ số tổng quan; mở một trạm để xem các thành phần PM2.5, CO₂, tiếng ồn và nhiệt độ."
        actions={(
          <Button variant="outline" size="sm" onClick={fetchDashboard} disabled={loading}>
            <RefreshCw className={loading ? "is-spinning" : ""} size={16} aria-hidden="true" />
            {loading ? "Đang làm mới" : "Làm mới"}
          </Button>
        )}
      />

      <section className="dashboard-kpis" aria-label="Tổng quan hệ thống">
        <article className="dashboard-kpi dashboard-kpi--primary dashboard-kpi--aqi-primary">
          <span className="dashboard-kpi__icon"><Activity size={20} aria-hidden="true" /></span>
          <div className="dashboard-kpi__copy">
            <span>AQI trung bình</span>
            <strong>{averageAqi ?? "—"}</strong>
            <small>Chỉ số chất lượng không khí tổng quan</small>
          </div>
          <Activity size={46} className="dashboard-kpi__watermark" aria-hidden="true" />
        </article>
        <article className="dashboard-kpi dashboard-kpi--info">
          <span className="dashboard-kpi__icon"><MapPin size={20} aria-hidden="true" /></span>
          <div className="dashboard-kpi__copy">
            <span>Trạm quan trắc</span>
            <strong>{loading ? "—" : stations.length}</strong>
            <small>{validStations.length} trạm có dữ liệu hợp lệ</small>
          </div>
          <MapPin size={46} className="dashboard-kpi__watermark" aria-hidden="true" />
        </article>
        <article className="dashboard-kpi dashboard-kpi--success">
          <span className="dashboard-kpi__icon"><Radio size={20} aria-hidden="true" /></span>
          <div className="dashboard-kpi__copy">
            <span>Kết nối hệ thống</span>
            <strong>{loading ? "—" : `${freshOnlineCount}/${stations.length}`}</strong>
            <small>Online và dữ liệu còn mới</small>
          </div>
          <Wifi size={46} className="dashboard-kpi__watermark" aria-hidden="true" />
        </article>
        <article className="dashboard-kpi dashboard-kpi--danger">
          <span className="dashboard-kpi__icon"><Bell size={20} aria-hidden="true" /></span>
          <div className="dashboard-kpi__copy">
            <span>Cảnh báo đang mở</span>
            <strong>{loading ? "—" : activeAlerts.length}</strong>
            <small>{activeAlerts.length ? "Cần theo dõi và xử lý" : "Chưa có cảnh báo active"}</small>
          </div>
          <Bell size={46} className="dashboard-kpi__watermark" aria-hidden="true" />
        </article>
      </section>

      {selectedStation && (
        <section className="dashboard-environment-metrics" aria-label="Chỉ số môi trường của trạm đang chọn">
          <div className="dashboard-environment-heading"><span>Chỉ số tại trạm</span><strong>{selectedStation.station_id} · {selectedStation.station_name}</strong><small>Cập nhật {formatVnDateTime(selectedStation.updated_at)}</small></div>
          <article className="environment-metric environment-metric--aqi"><Activity size={19} /><div><span>AQI</span><strong>{selectedStation.aqi ?? "—"}</strong><small>{selectedStation.aqi_category ?? "PM2.5 sub-index"}</small></div></article>
          <article className="environment-metric environment-metric--pm25"><Wind size={19} /><div><span>PM2.5</span><strong>{selectedStation.pm25 ?? "—"}<em>{selectedStation.pm25 != null ? " µg/m³" : ""}</em></strong><small>Thành phần tạo AQI</small></div></article>
          <article className="environment-metric environment-metric--co2"><Database size={19} /><div><span>CO₂</span><strong>{selectedStation.co2 ?? "—"}<em>{selectedStation.co2 != null ? " ppm" : ""}</em></strong><small>Carbon dioxide</small></div></article>
          <article className="environment-metric environment-metric--noise"><Volume2 size={19} /><div><span>Tiếng ồn</span><strong>{selectedStation.noise_db ?? "—"}<em>{selectedStation.noise_db != null ? " dB" : ""}</em></strong><small>Sound pressure</small></div></article>
          <article className="environment-metric environment-metric--temp"><Thermometer size={19} /><div><span>Nhiệt độ</span><strong>{selectedStation.temperature ?? "—"}<em>{selectedStation.temperature != null ? " °C" : ""}</em></strong><small>Không khí xung quanh</small></div></article>
        </section>
      )}

      {error && (
        <div className="alert-box alert-warning" role="alert">
          <TriangleAlert size={17} aria-hidden="true" />
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchDashboard}>Thử lại</Button>
        </div>
      )}

      <div className="dashboard-workspace">
        <section className="dashboard-map-card" aria-labelledby="dashboard-map-title">
          <header className="dashboard-panel-header">
            <div>
              <span className="dashboard-eyebrow"><LocateFixed size={14} aria-hidden="true" /> Bản đồ khu vực</span>
              <h2 id="dashboard-map-title">Vinhomes Ocean Park 1</h2>
            </div>
            <div className="dashboard-map-legend" aria-label="Chú thích trạng thái">
              <span><i className="legend-dot legend-dot--online" />Online</span>
              <span><i className="legend-dot legend-dot--stale" />Dữ liệu cũ</span>
              <span><i className="legend-dot legend-dot--offline" />Offline</span>
              <span><i className="legend-boundary" />Khu kiểm soát</span>
              <button type="button" className={`dashboard-heat-toggle${showHeatmap ? " is-active" : ""}`} onClick={() => setShowHeatmap((value) => !value)}>{showHeatmap ? "Ẩn vùng nhiệt" : "Hiện vùng nhiệt"}</button>
            </div>
          </header>

          <div className="dashboard-map-frame">
            {loading && stations.length === 0 ? (
              <div className="dashboard-map-loading" role="status">
                <RefreshCw className="is-spinning" size={22} aria-hidden="true" />
                Đang tải dữ liệu bản đồ…
              </div>
            ) : (
              <MapContainer
                center={[20.9945, 105.9482]}
                zoom={15}
                minZoom={13}
                scrollWheelZoom={false}
                maxBounds={MAP_MAX_BOUNDS}
                maxBoundsViscosity={1}
                className="dashboard-map"
              >
                <MapFocus />
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {showHeatmap && stations.filter((station) => station.status === "online" && !station.is_stale && station.pm25 !== null).map((station) => (
                  <Circle
                    key={`heat-${station.station_id}`}
                    center={[station.latitude, station.longitude]}
                    radius={105 + Math.min(Number(station.aqi ?? station.pm25) || 0, 250) * 1.1}
                    pathOptions={{ color: heatColor(station), fillColor: heatColor(station), fillOpacity: 0.18, weight: 0 }}
                  />
                ))}
                <Polygon
                  positions={[MAP_OUTER_MASK, [...OCEAN_PARK_1_BOUNDARY].reverse()]}
                  pathOptions={{
                    color: "transparent",
                    fillColor: "#334155",
                    fillOpacity: 0.78,
                    fillRule: "evenodd",
                    interactive: false,
                  }}
                />
                <Polygon
                  positions={OCEAN_PARK_1_BOUNDARY}
                  pathOptions={{
                    color: "#6366f1",
                    weight: 5,
                    dashArray: "12 7",
                    fill: false,
                    interactive: false,
                  }}
                />
                {stations.map((station) => {
                  const isSelected = selectedStation?.station_id === station.station_id;
                  const fillColor = station.status === "offline"
                    ? "var(--pm25-offline)"
                    : station.is_stale ? "var(--color-warning-500)" : getAqiColor(station.aqi);
                  return (
                    <CircleMarker
                      key={station.station_id}
                      center={[station.latitude, station.longitude]}
                      radius={isSelected ? 16 : 12}
                      pathOptions={{
                        color: isSelected ? "#4f46e5" : "#ffffff",
                        weight: isSelected ? 5 : 3,
                        fillColor,
                        fillOpacity: 0.96,
                      }}
                      eventHandlers={{ click: () => selectStation(station.station_id) }}
                    >
                      <Tooltip direction="top" offset={[0, -12]} opacity={1}>
                        <strong>{station.station_id} · {station.station_name}</strong><br />
                        AQI: {station.aqi ?? "Không khả dụng"}
                      </Tooltip>
                      <Popup>
                        <div className="popup-content">
                          <h3>{station.station_name} ({station.station_id})</h3>
                          <div className="popup-pm25">AQI: <strong>{station.aqi ?? "—"}</strong></div>
                          <p className="popup-environment">PM2.5: <strong>{station.pm25 ?? "—"} µg/m³</strong><br />CO₂: <strong>{station.co2 ?? "—"} ppm</strong><br />Tiếng ồn: <strong>{station.noise_db ?? "—"} dB</strong><br />Nhiệt độ: <strong>{station.temperature ?? "—"} °C</strong></p>
                          <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} aqi={station.aqi} />
                          <Button variant="primary" size="sm" onClick={() => openStationDetail(station.station_id)}>Xem chi tiết</Button>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            )}
          </div>
          <div className="dashboard-map-footnote">
            <span className="dashboard-map-footnote__scope"><i /> Phạm vi giám sát Ocean Park 1</span>
            <span>Vùng màu là cường độ AQI từ API, không phải mô hình lan truyền.</span>
          </div>

          {selectedStation && (
            <article className="dashboard-selected-station">
              <div className="dashboard-selected-station__identity">
                <span className="dashboard-station-code">{selectedStation.station_id}</span>
                <div>
                  <span className="dashboard-eyebrow">Trạm đang chọn</span>
                  <h3>{selectedStation.station_name}</h3>
                  <p><Clock3 size={14} aria-hidden="true" /> Cập nhật {formatVnDateTime(selectedStation.updated_at)}</p>
                </div>
              </div>
              <div className="dashboard-selected-station__reading">
                <span>AQI hiện tại</span>
                <strong style={{ color: getAqiColor(selectedStation.aqi) }}>
                  {selectedStation.aqi ?? "—"}
                </strong>
                <DataQualityBadge status={selectedStation.status} isStale={selectedStation.is_stale} pm25={selectedStation.pm25} aqi={selectedStation.aqi} />
              </div>
              <div className="dashboard-selected-station__actions">
                <Button variant="outline" size="sm" onClick={() => askAiAboutStation(selectedStation.station_id)}>
                  <Sparkles size={16} aria-hidden="true" /> Hỏi AI
                </Button>
                <Button variant="primary" size="sm" onClick={() => openStationDetail(selectedStation.station_id)}>
                  Xem chi tiết <ArrowRight size={16} aria-hidden="true" />
                </Button>
              </div>
            </article>
          )}
        </section>

        <aside className="dashboard-rail" aria-label="Thông tin nhanh">
          <section className="dashboard-rail-card">
            <header className="dashboard-rail-card__header">
              <div><span className="dashboard-eyebrow">Tổng quan hệ thống</span><h2>Trạng thái cảm biến</h2></div>
              <Database size={19} aria-hidden="true" />
            </header>
            <div className="dashboard-health-grid">
              <div><span className="health-icon health-icon--online"><Wifi size={17} /></span><strong>{onlineCount}</strong><small>Online</small></div>
              <div><span className="health-icon health-icon--offline"><WifiOff size={17} /></span><strong>{offlineCount}</strong><small>Offline</small></div>
              <div><span className="health-icon health-icon--stale"><Clock3 size={17} /></span><strong>{staleCount}</strong><small>Dữ liệu cũ</small></div>
            </div>
          </section>

          <section className="dashboard-rail-card">
            <header className="dashboard-rail-card__header dashboard-rail-card__header--action">
              <div><span className="dashboard-eyebrow">Theo dõi ưu tiên</span><h2>Cảnh báo gần nhất</h2></div>
              <Button variant="ghost" size="sm" onClick={() => navigateTo("alerts")}>Xem tất cả</Button>
            </header>
            <div className="dashboard-alert-list">
              {loading && alerts.length === 0 ? (
                <div className="dashboard-empty-state" role="status">
                  <RefreshCw className="is-spinning" size={20} aria-hidden="true" />
                  <span>Đang tải cảnh báo…</span>
                </div>
              ) : activeAlerts.length === 0 ? (
                <div className="dashboard-empty-state"><Bell size={20} /><span>Không có cảnh báo đang kích hoạt.</span></div>
              ) : activeAlerts.slice(0, 3).map((alert) => {
                const station = stations.find((item) => item.station_id === alert.station_id);
                return (
                  <button
                    type="button"
                    className={`dashboard-alert-item dashboard-alert-item--${alert.severity}`}
                    key={alert.alert_id}
                    onClick={() => openStationDetail(alert.station_id)}
                  >
                    <span className="dashboard-alert-item__icon"><TriangleAlert size={17} /></span>
                    <span className="dashboard-alert-item__copy">
                      <strong>{station?.station_name ?? alert.station_id}</strong>
                      <small>{alert.message}</small>
                      <time>{formatVnDateTime(alert.created_at)}</time>
                    </span>
                    <span className="dashboard-alert-item__meta">
                      <b>{severityLabel[alert.severity]}</b>
                      <StatusBadge status={alert.status} />
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="dashboard-rail-card dashboard-stations-panel">
            <header className="dashboard-rail-card__header">
              <div><span className="dashboard-eyebrow">Danh mục cảm biến</span><h2>Các trạm ({filteredStations.length})</h2></div>
            </header>
            <label className="dashboard-search">
              <Search size={16} aria-hidden="true" />
              <span className="sr-only">Tìm kiếm trạm</span>
              <input
                type="search"
                placeholder="Tìm theo tên hoặc mã trạm"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
            </label>
            <div className="dashboard-station-list">
              {filteredStations.map((station) => {
                const isSelected = selectedStation?.station_id === station.station_id;
                return (
                  <button
                    type="button"
                    key={station.station_id}
                    className={`dashboard-station-row${isSelected ? " is-selected" : ""}`}
                    aria-pressed={isSelected}
                    onClick={() => selectStation(station.station_id)}
                  >
                    <span className="dashboard-station-row__status" style={{ background: station.status === "offline" ? "var(--pm25-offline)" : getAqiColor(station.aqi) }} />
                    <span className="dashboard-station-row__identity"><b>{station.station_id}</b><span>{station.station_name}</span></span>
                    <span className="dashboard-station-row__value" style={{ color: getAqiColor(station.aqi) }}>
                      <strong>{station.aqi ?? "—"}</strong><small>{station.aqi != null ? "AQI" : "Offline"}</small>
                    </span>
                  </button>
                );
              })}
              {!loading && filteredStations.length === 0 && (
                <div className="dashboard-empty-state"><Search size={20} /><span>Không tìm thấy trạm phù hợp.</span></div>
              )}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
};

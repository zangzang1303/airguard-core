import React, { useEffect, useMemo, useState } from "react";
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
  Wifi,
  WifiOff,
  Wind,
} from "lucide-react";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { DataQualityBadge, getPm25Severity } from "../../components/common/DataQualityBadge";
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

export const Dashboard: React.FC = () => {
  const { navigateTo, setSelectedStationId } = useAuth();
  const [stations, setStations] = useState<Station[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeStationId, setActiveStationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stationData, alertData] = await Promise.all([api.getStations(), api.getAlerts()]);
      setStations(stationData);
      setAlerts(alertData);
      setActiveStationId((current) => {
        if (current && stationData.some((station) => station.station_id === current)) return current;
        return stationData[0]?.station_id ?? null;
      });
    } catch {
      setError("Không thể tải đầy đủ dữ liệu Dashboard. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const filteredStations = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase("vi");
    if (!query) return stations;
    return stations.filter((station) =>
      station.station_name.toLocaleLowerCase("vi").includes(query)
      || station.station_id.toLocaleLowerCase("vi").includes(query));
  }, [stations, searchQuery]);

  const selectedStation = useMemo(
    () => stations.find((station) => station.station_id === activeStationId) ?? stations[0] ?? null,
    [activeStationId, stations],
  );

  const validStations = useMemo(
    () => stations.filter((station) => station.pm25 !== null && station.status === "online" && !station.is_stale),
    [stations],
  );
  const averagePm25 = validStations.length
    ? Math.round((validStations.reduce((sum, station) => sum + Number(station.pm25), 0) / validStations.length) * 10) / 10
    : null;
  const onlineCount = stations.filter((station) => station.status === "online").length;
  const freshOnlineCount = stations.filter((station) => station.status === "online" && !station.is_stale).length;
  const offlineCount = stations.filter((station) => station.status === "offline").length;
  const staleCount = stations.filter((station) => station.is_stale).length;
  const activeAlerts = alerts.filter((alert) => alert.status === "active");

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
        description="Theo dõi PM2.5, độ mới dữ liệu và cảnh báo tại các trạm quanh VinUni và Vinhomes Ocean Park."
        actions={(
          <Button variant="outline" size="sm" onClick={fetchDashboard} disabled={loading}>
            <RefreshCw className={loading ? "is-spinning" : ""} size={16} aria-hidden="true" />
            {loading ? "Đang làm mới" : "Làm mới"}
          </Button>
        )}
      />

      <section className="dashboard-kpis" aria-label="Tổng quan hệ thống">
        <article className="dashboard-kpi dashboard-kpi--primary">
          <span className="dashboard-kpi__icon"><MapPin size={20} aria-hidden="true" /></span>
          <div className="dashboard-kpi__copy">
            <span>Trạm quan trắc</span>
            <strong>{loading ? "—" : stations.length}</strong>
            <small>Danh mục S01–S05</small>
          </div>
          <Activity size={46} className="dashboard-kpi__watermark" aria-hidden="true" />
        </article>
        <article className="dashboard-kpi dashboard-kpi--info">
          <span className="dashboard-kpi__icon"><Wind size={20} aria-hidden="true" /></span>
          <div className="dashboard-kpi__copy">
            <span>PM2.5 trung bình</span>
            <strong>{averagePm25 ?? "—"}<em>{averagePm25 !== null ? " µg/m³" : ""}</em></strong>
            <small>{validStations.length} trạm có dữ liệu hợp lệ</small>
          </div>
          <Wind size={46} className="dashboard-kpi__watermark" aria-hidden="true" />
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
              <h2 id="dashboard-map-title">VinUni · Vinhomes Ocean Park</h2>
            </div>
            <div className="dashboard-map-legend" aria-label="Chú thích trạng thái">
              <span><i className="legend-dot legend-dot--online" />Online</span>
              <span><i className="legend-dot legend-dot--stale" />Dữ liệu cũ</span>
              <span><i className="legend-dot legend-dot--offline" />Offline</span>
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
                center={[20.9446, 105.9447]}
                zoom={16}
                scrollWheelZoom={false}
                className="dashboard-map"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {stations.map((station) => {
                  const severity = getPm25Severity(station.pm25);
                  const isSelected = selectedStation?.station_id === station.station_id;
                  const fillColor = station.status === "offline"
                    ? "var(--pm25-offline)"
                    : station.is_stale ? "var(--color-warning-500)" : severity.color;
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
                        PM2.5: {station.pm25 ?? "Không khả dụng"}{station.pm25 !== null ? " µg/m³" : ""}
                      </Tooltip>
                      <Popup>
                        <div className="popup-content">
                          <h3>{station.station_name} ({station.station_id})</h3>
                          <div className="popup-pm25">PM2.5: <strong>{station.pm25 ?? "N/A"} µg/m³</strong></div>
                          <DataQualityBadge status={station.status} isStale={station.is_stale} pm25={station.pm25} />
                          <Button variant="primary" size="sm" onClick={() => openStationDetail(station.station_id)}>Xem chi tiết</Button>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            )}
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
                <span>PM2.5 hiện tại</span>
                <strong style={{ color: getPm25Severity(selectedStation.pm25).color }}>
                  {selectedStation.pm25 ?? "—"}<em>{selectedStation.pm25 !== null ? " µg/m³" : ""}</em>
                </strong>
                <DataQualityBadge status={selectedStation.status} isStale={selectedStation.is_stale} pm25={selectedStation.pm25} />
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
                const severity = getPm25Severity(station.pm25);
                const isSelected = selectedStation?.station_id === station.station_id;
                return (
                  <button
                    type="button"
                    key={station.station_id}
                    className={`dashboard-station-row${isSelected ? " is-selected" : ""}`}
                    aria-pressed={isSelected}
                    onClick={() => selectStation(station.station_id)}
                  >
                    <span className="dashboard-station-row__status" style={{ background: station.status === "offline" ? "var(--pm25-offline)" : severity.color }} />
                    <span className="dashboard-station-row__identity"><b>{station.station_id}</b><span>{station.station_name}</span></span>
                    <span className="dashboard-station-row__value" style={{ color: severity.color }}>
                      <strong>{station.pm25 ?? "—"}</strong><small>{station.pm25 !== null ? "µg/m³" : "Offline"}</small>
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

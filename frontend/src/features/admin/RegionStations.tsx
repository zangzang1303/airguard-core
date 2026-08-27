import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Ban,
  Building2,
  CheckCircle2,
  ChevronDown,
  CircleOff,
  Clock3,
  ExternalLink,
  MapPin,
  Plus,
  RadioTower,
  RefreshCw,
  Search,
  ShieldAlert,
  X,
} from "lucide-react";
import { stationCatalogApi } from "../../api/stationCatalog";
import { useAuth } from "../../context/AuthContext";
import {
  AdminRegion,
  AdminStation,
  StationChangeEntry,
  StationStatus,
} from "../../types";
import "./RegionStations.css";

type DisplayState = {
  key: StationStatus;
  label: string;
  color: string;
  icon: React.ElementType;
};

/**
 * Display mapper dùng chung cho marker, list và drawer.
 * Precedence theo thiết kế: invalid > offline > stale > severity.
 */
const getDisplayState = (station: AdminStation): DisplayState => {
  if (station.status === "invalid") {
    return {
      key: "invalid",
      label: "Không hợp lệ",
      color: "#f43f5e",
      icon: AlertTriangle,
    };
  }
  if (station.status === "offline") {
    return {
      key: "offline",
      label: "Ngoại tuyến",
      color: "#64748b",
      icon: CircleOff,
    };
  }
  if (station.status === "stale" || station.is_stale) {
    return {
      key: "stale",
      label: "Dữ liệu cũ",
      color: "#f59e0b",
      icon: Clock3,
    };
  }
  return {
    key: "online",
    label: "Trực tuyến",
    color: "#10b981",
    icon: CheckCircle2,
  };
};

const LEGEND: Array<{ label: string; color: string; icon: React.ElementType }> =
  [
    { label: "Online", color: "#10b981", icon: CheckCircle2 },
    { label: "Dữ liệu cũ", color: "#f59e0b", icon: Clock3 },
    { label: "Offline", color: "#64748b", icon: CircleOff },
    { label: "Invalid", color: "#f43f5e", icon: AlertTriangle },
  ];

const formatTime = (value: string | null) => {
  if (!value) return "Không khả dụng";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
};

const formatPm25 = (pm25: number | null) =>
  pm25 === null ? "Không khả dụng" : `${pm25} µg/m³`;

const formatCoordinates = (station: AdminStation) =>
  station.latitude === null || station.longitude === null
    ? "Chưa có toạ độ hợp lệ"
    : `${station.latitude.toFixed(4)}, ${station.longitude.toFixed(4)}`;

export const RegionStations: React.FC = () => {
  const { navigateTo } = useAuth();
  const [regions, setRegions] = useState<AdminRegion[]>([]);
  const [stations, setStations] = useState<AdminStation[]>([]);
  const [partialError, setPartialError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [regionFilter, setRegionFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [changes, setChanges] = useState<StationChangeEntry[]>([]);

  const loadCatalog = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await stationCatalogApi.getCatalog();
      setRegions(data.regions);
      setStations(data.stations);
      setPartialError(data.partial_error);
    } catch {
      setError(
        "Không thể tải catalog khu vực và trạm. Vui lòng thử lại hoặc kiểm tra kết nối backend.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    stationCatalogApi
      .getStationChanges(selectedId)
      .then(setChanges)
      .catch(() => setChanges([]));
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedId(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedId]);

  const filteredStations = useMemo(() => {
    const q = query.trim().toLowerCase();
    return stations.filter((station) => {
      if (regionFilter !== "all" && station.region_id !== regionFilter) {
        return false;
      }
      if (!q) return true;
      return `${station.station_id} ${station.station_name} ${station.location_type}`
        .toLowerCase()
        .includes(q);
    });
  }, [stations, regionFilter, query]);

  const mappableStations = filteredStations.filter(
    (station) => station.map_x !== null && station.map_y !== null,
  );
  const unmappedStations = filteredStations.filter(
    (station) => station.map_x === null || station.map_y === null,
  );

  const onlineCount = stations.filter(
    (station) => getDisplayState(station).key === "online",
  ).length;
  const attentionCount = stations.length - onlineCount;

  const selectedStation =
    stations.find((station) => station.station_id === selectedId) ?? null;

  const filtersActive = regionFilter !== "all" || query.trim() !== "";

  const resetFilters = () => {
    setRegionFilter("all");
    setQuery("");
  };

  const renderStatusChip = (station: AdminStation) => {
    const state = getDisplayState(station);
    const Icon = state.icon;
    return (
      <span className={`admin-station-status is-${state.key}`}>
        <Icon size={13} aria-hidden="true" />
        {state.label}
      </span>
    );
  };

  const renderStationRow = (station: AdminStation) => {
    const state = getDisplayState(station);
    const active = station.station_id === selectedId;
    return (
      <li key={station.station_id}>
        <button
          type="button"
          className={`admin-station-row${active ? " is-active" : ""}`}
          aria-pressed={active}
          onClick={() => setSelectedId(station.station_id)}
        >
          <span
            className="admin-station-row__mark"
            style={{ "--state-color": state.color } as React.CSSProperties}
            aria-hidden="true"
          >
            {station.station_id}
          </span>
          <span className="admin-station-row__body">
            <strong>{station.station_name}</strong>
            <small>
              {station.region_name} · {station.location_type}
            </small>
            <span className="admin-station-row__meta">
              {renderStatusChip(station)}
              <b>{formatPm25(station.pm25)}</b>
            </span>
            <small className="admin-station-row__time">
              Đo lúc {formatTime(station.measured_at)} · Nguồn {station.source}
            </small>
            {station.status_reason && (
              <small className="admin-station-row__reason">
                {station.status_reason}
              </small>
            )}
          </span>
        </button>
      </li>
    );
  };

  return (
    <div className="admin-dashboard admin-regions-page">
      <header className="admin-dashboard__header">
        <div>
          <h1>Khu vực & Trạm</h1>
          <p>
            Catalog vận hành khu vực và trạm S01-S05 · Metadata, vị trí,
            ownership và chất lượng dữ liệu
          </p>
        </div>
        <button
          type="button"
          className="admin-primary-button"
          disabled
          title="Cần API provisioning, policy station-id và quyền Admin từ backend"
        >
          <Plus size={16} />
          Thêm trạm
        </button>
      </header>

      <div className="admin-simulator-note" role="note">
        <RadioTower size={15} />
        <span>
          <strong>SIMULATOR</strong> · Mọi giá trị PM2.5, trạng thái và thời
          điểm đo bên dưới đến từ Simulator của MVP, không phải quan trắc chính
          thức. Module P2 — hành động provisioning chờ API contract.
        </span>
      </div>

      {error && (
        <div className="admin-error" role="alert">
          <AlertTriangle size={17} />
          <span>{error}</span>
          <button type="button" onClick={loadCatalog}>
            Thử lại
          </button>
        </div>
      )}

      <section className="admin-kpis" aria-label="Chỉ số catalog trạm">
        <article className="admin-kpi admin-kpi--info">
          <div className="admin-kpi__top">
            <span>Tổng khu vực</span>
            <i>
              <Building2 size={19} />
            </i>
          </div>
          <strong>{loading ? "—" : regions.length}</strong>
          <small>
            {loading
              ? "Đang tải catalog…"
              : regions.map((region) => region.region_name).join(" · ")}
          </small>
        </article>
        <article className="admin-kpi admin-kpi--info">
          <div className="admin-kpi__top">
            <span>Tổng trạm</span>
            <i>
              <RadioTower size={19} />
            </i>
          </div>
          <strong>{loading ? "—" : stations.length}</strong>
          <small>
            {loading ? "Đang tải catalog…" : "Station ID immutable sau provision"}
          </small>
        </article>
        <article className="admin-kpi admin-kpi--success">
          <div className="admin-kpi__top">
            <span>Trạm online / fresh</span>
            <i>
              <CheckCircle2 size={19} />
            </i>
          </div>
          <strong>{loading ? "—" : `${onlineCount} / ${stations.length}`}</strong>
          <small>Có measurement hợp lệ trong ngưỡng freshness</small>
        </article>
        <article className="admin-kpi admin-kpi--warning">
          <div className="admin-kpi__top">
            <span>Trạm cần chú ý</span>
            <i>
              <ShieldAlert size={19} />
            </i>
          </div>
          <strong>{loading ? "—" : attentionCount}</strong>
          <small>Stale, offline hoặc dữ liệu không hợp lệ</small>
        </article>
      </section>

      <section className="admin-regions-toolbar" aria-label="Bộ lọc trạm">
        <label className="admin-users-select">
          <span className="sr-only">Chọn khu vực</span>
          <select
            value={regionFilter}
            onChange={(event) => setRegionFilter(event.target.value)}
          >
            <option value="all">Tất cả khu vực</option>
            {regions.map((region) => (
              <option key={region.region_id} value={region.region_id}>
                {region.region_name}
              </option>
            ))}
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Tìm kiếm trạm</span>
          <input
            type="search"
            placeholder="Tìm theo mã trạm, tên trạm hoặc loại vị trí..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <button
          type="button"
          className="admin-users-reset"
          onClick={resetFilters}
          disabled={!filtersActive}
        >
          Đặt lại
        </button>
      </section>

      {partialError && !loading && (
        <div className="admin-partial-note" role="status">
          <MapPin size={15} />
          <span>{partialError}</span>
        </div>
      )}

      <section className="admin-regions-workspace">
        <article className="admin-card admin-region-map">
          <header className="admin-card__header">
            <div>
              <MapPin size={17} />
              <h2>Bản đồ vùng quan sát</h2>
            </div>
            <span>
              {loading
                ? "Đang tải"
                : `${mappableStations.length} / ${filteredStations.length} trạm có toạ độ`}
            </span>
          </header>

          {loading ? (
            <div className="admin-skeleton admin-skeleton--map" aria-hidden="true" />
          ) : (
            <div className="admin-map-canvas">
              <div className="admin-map-canvas__grid" />
              <strong className="admin-map-label">
                SƠ ĐỒ KHU VỰC · S01-S05 [SIMULATOR]
              </strong>
              {mappableStations.map((station) => {
                const state = getDisplayState(station);
                const active = station.station_id === selectedId;
                return (
                  <button
                    key={station.station_id}
                    type="button"
                    className={`admin-map-marker${active ? " is-active" : ""}`}
                    style={
                      {
                        left: `${station.map_x}%`,
                        top: `${station.map_y}%`,
                        "--marker-color": state.color,
                      } as React.CSSProperties
                    }
                    aria-label={`${station.station_id} ${station.station_name}, ${state.label}, PM2.5 ${formatPm25(station.pm25)}`}
                    onClick={() => setSelectedId(station.station_id)}
                  >
                    <span>{station.station_id}</span>
                    <small>{station.pm25 ?? "—"}</small>
                  </button>
                );
              })}
              {mappableStations.length === 0 && (
                <div className="admin-map-empty">
                  Không có trạm nào có toạ độ hợp lệ trong bộ lọc hiện tại.
                </div>
              )}
            </div>
          )}

          <div className="admin-map-legend">
            <strong>Chú giải trạng thái</strong>
            {LEGEND.map((item) => {
              const Icon = item.icon;
              return (
                <span key={item.label}>
                  <i style={{ background: item.color }} />
                  <Icon size={12} aria-hidden="true" />
                  {item.label}
                </span>
              );
            })}
          </div>
        </article>

        <article className="admin-card admin-region-list">
          <header className="admin-card__header">
            <div>
              <RadioTower size={17} />
              <h2>Danh sách trạm</h2>
            </div>
            <span>
              {loading
                ? "Đang tải…"
                : `${filteredStations.length} / ${stations.length} trạm`}
            </span>
          </header>

          {loading ? (
            <div className="admin-station-skeletons">
              {[0, 1, 2, 3].map((index) => (
                <div
                  key={index}
                  className="admin-skeleton admin-skeleton--row"
                  aria-hidden="true"
                />
              ))}
            </div>
          ) : filteredStations.length === 0 ? (
            <div className="admin-panel-state">
              <RadioTower size={20} />
              {stations.length === 0
                ? "Catalog chưa có trạm nào."
                : "Không có trạm phù hợp với khu vực hoặc từ khóa đã chọn."}
              {filtersActive && (
                <button
                  type="button"
                  className="admin-users-reset"
                  onClick={resetFilters}
                >
                  Đặt lại bộ lọc
                </button>
              )}
            </div>
          ) : (
            <ul className="admin-station-rows">
              {filteredStations.map(renderStationRow)}
            </ul>
          )}

          {!loading && unmappedStations.length > 0 && (
            <p className="admin-region-list__note">
              {unmappedStations.length} trạm không có marker trên bản đồ do
              thiếu toạ độ hợp lệ; không đặt marker giả.
            </p>
          )}
        </article>
      </section>

      {selectedStation && (
        <div
          className="admin-drawer-scrim"
          role="presentation"
          onClick={() => setSelectedId(null)}
        />
      )}
      {selectedStation && (
        <aside
          className="admin-station-drawer"
          role="dialog"
          aria-modal="true"
          aria-label={`Chi tiết trạm ${selectedStation.station_id}`}
        >
          <header className="admin-station-drawer__header">
            <div>
              <code>{selectedStation.station_id}</code>
              <strong>{selectedStation.station_name}</strong>
              <small>
                {selectedStation.region_name} · {selectedStation.location_type}
              </small>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label="Đóng chi tiết trạm"
              onClick={() => setSelectedId(null)}
            >
              <X size={20} />
            </button>
          </header>

          <div className="admin-station-drawer__body">
            <section className="admin-drawer-section">
              <h3>Identity</h3>
              <dl className="admin-user-info">
                <div>
                  <dt>Mã trạm</dt>
                  <dd>
                    <code>{selectedStation.station_id}</code>
                    <small className="admin-user-role-hint">
                      Immutable sau provision; ID đã retire không được tái sử
                      dụng.
                    </small>
                  </dd>
                </div>
                <div>
                  <dt>Tên trạm</dt>
                  <dd>{selectedStation.station_name}</dd>
                </div>
                <div>
                  <dt>Khu vực / Loại vị trí</dt>
                  <dd>
                    {selectedStation.region_name} ·{" "}
                    {selectedStation.location_type}
                  </dd>
                </div>
                <div>
                  <dt>Trạng thái vòng đời</dt>
                  <dd>
                    {selectedStation.lifecycle === "active"
                      ? "Active"
                      : "Retired"}
                  </dd>
                </div>
                <div>
                  <dt>Owner vận hành</dt>
                  <dd>{selectedStation.owner}</dd>
                </div>
              </dl>
            </section>

            <section className="admin-drawer-section">
              <h3>Vị trí</h3>
              <dl className="admin-user-info">
                <div>
                  <dt>Toạ độ</dt>
                  <dd>{formatCoordinates(selectedStation)}</dd>
                </div>
              </dl>
              {selectedStation.map_x !== null &&
              selectedStation.map_y !== null ? (
                <div className="admin-drawer-map" aria-hidden="true">
                  <div className="admin-map-canvas__grid" />
                  <span
                    className="admin-drawer-map__pin"
                    style={
                      {
                        left: `${selectedStation.map_x}%`,
                        top: `${selectedStation.map_y}%`,
                        "--marker-color": getDisplayState(selectedStation).color,
                      } as React.CSSProperties
                    }
                  >
                    {selectedStation.station_id}
                  </span>
                </div>
              ) : (
                <div className="admin-drawer-warning" role="note">
                  <MapPin size={15} />
                  <span>
                    Trạm chưa có toạ độ hợp lệ nên không hiển thị trên bản đồ.
                    UI không đặt marker giả; cập nhật toạ độ cần API provisioning
                    và validation phía backend.
                  </span>
                </div>
              )}
            </section>

            <section className="admin-drawer-section">
              <h3>Dữ liệu gần nhất</h3>
              <dl className="admin-user-info">
                <div>
                  <dt>Trạng thái</dt>
                  <dd>{renderStatusChip(selectedStation)}</dd>
                </div>
                <div>
                  <dt>PM2.5</dt>
                  <dd>{formatPm25(selectedStation.pm25)}</dd>
                </div>
                <div>
                  <dt>Đo lúc (measured_at)</dt>
                  <dd>{formatTime(selectedStation.measured_at)}</dd>
                </div>
                <div>
                  <dt>Nhận lúc (received_at)</dt>
                  <dd>{formatTime(selectedStation.received_at)}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>{selectedStation.source}</dd>
                </div>
              </dl>
              {selectedStation.status_reason && (
                <div className="admin-drawer-warning" role="note">
                  <AlertTriangle size={15} />
                  <span>{selectedStation.status_reason}</span>
                </div>
              )}
              {getDisplayState(selectedStation).key !== "online" && (
                <p className="admin-user-actions__note">
                  Dữ liệu stale/offline/invalid không được dùng cho forecast,
                  alert hay HITL proposal.
                </p>
              )}
            </section>

            <section className="admin-drawer-section">
              <h3>Audit & maintenance</h3>
              {changes.length === 0 ? (
                <div className="admin-panel-state admin-panel-state--compact">
                  Chưa có thay đổi metadata hoặc sự kiện nào được ghi nhận.
                </div>
              ) : (
                <ul className="admin-user-audit-list">
                  {changes.map((entry) => (
                    <li key={entry.id}>
                      <time>{formatTime(entry.time)}</time>
                      <div>
                        <strong>{entry.action}</strong>
                        <span>{entry.actor}</span>
                        <p>{entry.detail}</p>
                        <code>
                          {entry.outcome} · {entry.correlation_id}
                        </code>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <p className="admin-user-actions__note">
                Audit chỉ đọc. Retire/deactivate là hành động destructive, yêu
                cầu lý do và bảo toàn history; không hard-delete trạm qua UI.
              </p>
            </section>
          </div>

          <footer className="admin-station-drawer__footer">
            <button
              type="button"
              className="admin-primary-button"
              onClick={() => {
                navigateTo("station-detail", {
                  stationId: selectedStation.station_id,
                });
                setSelectedId(null);
              }}
            >
              <ExternalLink size={15} />
              Xem dữ liệu trạm
            </button>
            <div className="admin-station-drawer__secondary">
              <button
                type="button"
                disabled
                title="Cần endpoint cập nhật metadata và policy quyền chỉnh sửa"
              >
                Chỉnh sửa metadata
              </button>
              <button
                type="button"
                className="admin-station-drawer__danger"
                disabled
                title="Cần endpoint retire kèm lý do và audit"
              >
                <Ban size={14} />
                Retire trạm
              </button>
            </div>
          </footer>
        </aside>
      )}
    </div>
  );
};

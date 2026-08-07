import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  ChevronDown,
  CircleOff,
  Clock3,
  Cpu,
  ExternalLink,
  Filter,
  Info,
  MoreVertical,
  Plus,
  RadioTower,
  RefreshCw,
  Search,
  Settings2,
  Wrench,
  X,
} from "lucide-react";
import { deviceRegistryApi } from "../../api/deviceRegistry";
import { useAuth } from "../../context/AuthContext";
import {
  AdminDevice,
  ConfigState,
  DeviceConnectivity,
  DeviceEvent,
  DeviceLifecycle,
  DeviceMutationOutcome,
  FirmwareState,
} from "../../types";
import "./IotDevices.css";

type DetailTab = "overview" | "connectivity" | "firmware" | "events" | "audit";

type DeviceAction =
  | "assign_station"
  | "update_config"
  | "set_maintenance"
  | "reactivate"
  | "deactivate";

type PendingAction = { kind: DeviceAction; device: AdminDevice } | null;

type ConnectivityDisplay = {
  key: DeviceConnectivity;
  label: string;
  color: string;
  icon: React.ElementType;
};

/**
 * Display mapper dùng chung cho bảng, cards và drawer.
 * Trạng thái luôn đến từ backend; client không suy diễn từ timer.
 */
const getConnectivity = (device: AdminDevice): ConnectivityDisplay => {
  switch (device.connectivity) {
    case "invalid":
      return {
        key: "invalid",
        label: "Không hợp lệ",
        color: "#f43f5e",
        icon: AlertTriangle,
      };
    case "offline":
      return {
        key: "offline",
        label: "Ngoại tuyến",
        color: "#64748b",
        icon: CircleOff,
      };
    case "stale":
      return {
        key: "stale",
        label: "Gián đoạn",
        color: "#f59e0b",
        icon: Clock3,
      };
    default:
      return {
        key: "online",
        label: "Trực tuyến",
        color: "#10b981",
        icon: CheckCircle2,
      };
  }
};

const firmwareLabel: Record<FirmwareState, string> = {
  up_to_date: "Mới nhất",
  update_available: "Có bản mới",
  unknown: "Chưa xác định",
};

const configLabel: Record<ConfigState, string> = {
  in_sync: "Đồng bộ",
  drift: "Lệch cấu hình",
  pending: "Chờ áp dụng",
  unknown: "Chưa áp dụng",
};

const lifecycleLabel: Record<DeviceLifecycle, string> = {
  active: "Active",
  maintenance: "Bảo trì",
  deactivated: "Deactivated",
};

const actionLabel: Record<DeviceAction, string> = {
  assign_station: "Gán trạm",
  update_config: "Cập nhật cấu hình",
  set_maintenance: "Đặt bảo trì",
  reactivate: "Kích hoạt lại",
  deactivate: "Deactivate",
};

const actionImpact: Record<DeviceAction, string> = {
  assign_station:
    "Liên kết thiết bị - trạm sẽ thay đổi. Measurement mới được gán về trạm đích, dữ liệu lịch sử giữ nguyên liên kết cũ.",
  update_config:
    "Dispatcher server-side sẽ đẩy config profile mới sau khi được backend phê duyệt. Cấu hình chỉ có hiệu lực khi thiết bị xác nhận áp dụng.",
  set_maintenance:
    "Thiết bị chuyển sang chế độ bảo trì. Telemetry vẫn được lưu nhưng không dùng cho alert hay HITL proposal.",
  reactivate:
    "Thiết bị trở lại vận hành bình thường và telemetry hợp lệ được dùng lại cho alert.",
  deactivate:
    "Thiết bị ngừng vận hành nhưng không bị xóa cứng. Measurement, event và audit được giữ theo retention policy.",
};

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

const formatUptime = (value: number | null) =>
  value === null ? "Không khả dụng" : `${(value * 100).toFixed(1)}%`;

const formatLatency = (value: number | null) =>
  value === null ? "Không khả dụng" : `${value} ms`;

const formatInterval = (value: number | null) =>
  value === null ? "Không khả dụng" : `${value} giây`;

const LEGEND: Array<{ label: string; color: string; icon: React.ElementType }> = [
  { label: "Trực tuyến", color: "#10b981", icon: CheckCircle2 },
  { label: "Gián đoạn", color: "#f59e0b", icon: Clock3 },
  { label: "Ngoại tuyến", color: "#64748b", icon: CircleOff },
  { label: "Không hợp lệ", color: "#f43f5e", icon: AlertTriangle },
];

type Filters = {
  query: string;
  region: string;
  deviceType: string;
  connectivity: DeviceConnectivity | "all";
  config: "all" | "firmware_attention" | "config_attention";
  lifecycle: DeviceLifecycle | "all";
};

const emptyFilters: Filters = {
  query: "",
  region: "all",
  deviceType: "all",
  connectivity: "all",
  config: "all",
  lifecycle: "all",
};

export const IotDevices: React.FC = () => {
  const { navigateTo } = useAuth();
  const [devices, setDevices] = useState<AdminDevice[]>([]);
  const [partialError, setPartialError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("overview");
  const [events, setEvents] = useState<DeviceEvent[]>([]);
  const [menuFor, setMenuFor] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [mutationResult, setMutationResult] = useState<{
    outcome: DeviceMutationOutcome;
    message: string;
  } | null>(null);

  const loadDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await deviceRegistryApi.getDevices();
      setDevices(data.devices);
      setPartialError(data.partial_error);
    } catch {
      setError(
        "Không thể tải registry thiết bị. Vui lòng thử lại hoặc kiểm tra kết nối backend.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setDetailTab("overview");
    deviceRegistryApi
      .getDeviceEvents(selectedId)
      .then(setEvents)
      .catch(() => setEvents([]));
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId && !pendingAction) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (pendingAction) setPendingAction(null);
      else setSelectedId(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [selectedId, pendingAction]);

  const regionOptions = useMemo(
    () =>
      Array.from(
        new Map(
          devices
            .filter((device) => device.region_id && device.region_name)
            .map((device) => [device.region_id!, device.region_name!]),
        ).entries(),
      ),
    [devices],
  );

  const typeOptions = useMemo(
    () => Array.from(new Set(devices.map((device) => device.device_type))),
    [devices],
  );

  const needsFirmwareAttention = (device: AdminDevice) =>
    device.firmware_state === "update_available" ||
    device.firmware_state === "unknown";

  const needsConfigAttention = (device: AdminDevice) =>
    device.config_state === "drift" ||
    device.config_state === "pending" ||
    device.config_state === "unknown";

  const filteredDevices = useMemo(() => {
    const q = filters.query.trim().toLowerCase();
    return devices.filter((device) => {
      if (
        q &&
        !`${device.device_id} ${device.device_name} ${device.station_id ?? ""}`
          .toLowerCase()
          .includes(q)
      ) {
        return false;
      }
      if (filters.region !== "all" && device.region_id !== filters.region) {
        return false;
      }
      if (
        filters.deviceType !== "all" &&
        device.device_type !== filters.deviceType
      ) {
        return false;
      }
      if (
        filters.connectivity !== "all" &&
        device.connectivity !== filters.connectivity
      ) {
        return false;
      }
      if (
        filters.config === "firmware_attention" &&
        !needsFirmwareAttention(device)
      ) {
        return false;
      }
      if (
        filters.config === "config_attention" &&
        !needsConfigAttention(device)
      ) {
        return false;
      }
      if (
        filters.lifecycle !== "all" &&
        device.lifecycle !== filters.lifecycle
      ) {
        return false;
      }
      return true;
    });
  }, [devices, filters]);

  const selectedDevice =
    devices.find((device) => device.device_id === selectedId) ?? null;

  const filtersActive = useMemo(
    () =>
      filters.query.trim() !== "" ||
      filters.region !== "all" ||
      filters.deviceType !== "all" ||
      filters.connectivity !== "all" ||
      filters.config !== "all" ||
      filters.lifecycle !== "all",
    [filters],
  );

  const openDevice = (device: AdminDevice) => {
    setSelectedId(device.device_id);
    setMenuFor(null);
    setMutationResult(null);
  };

  const requestAction = (kind: DeviceAction, device: AdminDevice) => {
    setMenuFor(null);
    setReason("");
    setMutationResult(null);
    setPendingAction({ kind, device });
  };

  const submitAction = async () => {
    if (!pendingAction || !reason.trim()) return;
    setSubmitting(true);
    try {
      const result = await deviceRegistryApi.requestAction(
        pendingAction.device.device_id,
        pendingAction.kind,
        reason.trim(),
      );
      // Chỉ phản ánh outcome backend trả về; không tự coi là succeeded.
      setMutationResult({ outcome: result.outcome, message: result.message });
      setPendingAction(null);
      setReason("");
    } catch {
      setMutationResult({
        outcome: "failed",
        message:
          "Yêu cầu thất bại. Không có thay đổi nào được áp dụng cho thiết bị.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const renderConnectivityChip = (device: AdminDevice) => {
    const state = getConnectivity(device);
    const Icon = state.icon;
    return (
      <span className={`admin-device-status is-${state.key}`}>
        <Icon size={13} aria-hidden="true" />
        {state.label}
      </span>
    );
  };

  const renderActionMenu = (device: AdminDevice) => (
    <>
      <button type="button" onClick={() => openDevice(device)}>
        <Info size={14} />
        Xem chi tiết
      </button>
      <button
        type="button"
        onClick={() => requestAction("assign_station", device)}
      >
        <RadioTower size={14} />
        {device.station_id ? "Đổi trạm liên kết" : "Gán trạm"}
      </button>
      <button
        type="button"
        onClick={() => requestAction("update_config", device)}
      >
        <Settings2 size={14} />
        Cập nhật cấu hình
      </button>
      {device.lifecycle === "maintenance" ? (
        <button
          type="button"
          onClick={() => requestAction("reactivate", device)}
        >
          <CheckCircle2 size={14} />
          Kích hoạt lại
        </button>
      ) : (
        <button
          type="button"
          onClick={() => requestAction("set_maintenance", device)}
        >
          <Wrench size={14} />
          Đặt bảo trì
        </button>
      )}
      {device.lifecycle === "deactivated" ? (
        <button
          type="button"
          onClick={() => requestAction("reactivate", device)}
        >
          <CheckCircle2 size={14} />
          Kích hoạt lại
        </button>
      ) : (
        <button
          type="button"
          className="admin-users-action--danger"
          onClick={() => requestAction("deactivate", device)}
        >
          <Ban size={14} />
          Deactivate
        </button>
      )}
    </>
  );

  const renderStationCell = (device: AdminDevice) =>
    device.station_id ? (
      <div className="admin-device-cell">
        <strong>{device.station_id}</strong>
        <small>{device.station_name}</small>
      </div>
    ) : (
      <span className="admin-device-unassigned">Chưa gán</span>
    );

  const renderTable = () => (
    <div className="admin-users-table-wrap">
      <table className="admin-users-table admin-devices-table">
        <thead>
          <tr>
            <th>Thiết bị</th>
            <th>Trạm liên kết</th>
            <th>Kết nối</th>
            <th>Heartbeat cuối</th>
            <th>Firmware</th>
            <th>Cấu hình</th>
            <th>Sự kiện gần nhất</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          {filteredDevices.map((device) => (
            <tr
              key={device.device_id}
              role="button"
              tabIndex={0}
              onClick={() => openDevice(device)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openDevice(device);
                }
              }}
            >
              <td>
                <div className="admin-device-identity">
                  <span className="admin-device-icon" aria-hidden="true">
                    <Cpu size={16} />
                  </span>
                  <div>
                    <strong>{device.device_id}</strong>
                    <small>
                      {device.device_name} · {device.device_type}
                    </small>
                    <small className="admin-device-serial">
                      Serial {device.serial_masked}
                    </small>
                  </div>
                </div>
              </td>
              <td>{renderStationCell(device)}</td>
              <td>
                <div className="admin-device-cell">
                  {renderConnectivityChip(device)}
                  {device.connectivity_reason && (
                    <small className="admin-device-reason">
                      {device.connectivity_reason}
                    </small>
                  )}
                </div>
              </td>
              <td className="admin-device-mono">
                {formatTime(device.last_heartbeat_at)}
              </td>
              <td>
                <div className="admin-device-cell">
                  <strong>{device.firmware_version}</strong>
                  <small
                    className={
                      needsFirmwareAttention(device)
                        ? "admin-device-attention"
                        : undefined
                    }
                  >
                    {firmwareLabel[device.firmware_state]}
                    {device.firmware_recommended &&
                    device.firmware_recommended !== device.firmware_version
                      ? ` · khuyến nghị ${device.firmware_recommended}`
                      : ""}
                  </small>
                </div>
              </td>
              <td>
                <div className="admin-device-cell">
                  <strong>
                    {device.config_profile} · {device.config_version}
                  </strong>
                  <small
                    className={
                      needsConfigAttention(device)
                        ? "admin-device-attention"
                        : undefined
                    }
                  >
                    {configLabel[device.config_state]}
                  </small>
                </div>
              </td>
              <td>
                {device.last_event ? (
                  <div className="admin-device-cell">
                    <strong>{device.last_event.type}</strong>
                    <small>{formatTime(device.last_event.time)}</small>
                  </div>
                ) : (
                  <span className="admin-device-unassigned">Chưa có</span>
                )}
              </td>
              <td onClick={(event) => event.stopPropagation()}>
                <div className="admin-users-menu-wrap">
                  <button
                    type="button"
                    className="admin-icon-button"
                    aria-label={`Menu hành động cho ${device.device_id}`}
                    onClick={() =>
                      setMenuFor(
                        menuFor === device.device_id ? null : device.device_id,
                      )
                    }
                  >
                    <MoreVertical size={17} />
                  </button>
                  {menuFor === device.device_id && (
                    <div className="admin-users-menu">
                      {renderActionMenu(device)}
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderCards = () => (
    <div className="admin-users-cards">
      {filteredDevices.map((device) => (
        <article key={device.device_id} className="admin-user-card">
          <header>
            <span className="admin-device-icon" aria-hidden="true">
              <Cpu size={16} />
            </span>
            <div>
              <strong>{device.device_id}</strong>
              <small>{device.device_name}</small>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label={`Hành động cho ${device.device_id}`}
              onClick={() =>
                setMenuFor(
                  menuFor === device.device_id ? null : device.device_id,
                )
              }
            >
              <MoreVertical size={18} />
            </button>
          </header>
          {menuFor === device.device_id && (
            <div className="admin-user-card__menu">
              {renderActionMenu(device)}
            </div>
          )}
          <dl className="admin-device-card__grid">
            <div>
              <dt>Trạm</dt>
              <dd>{device.station_id ?? "Chưa gán"}</dd>
            </div>
            <div>
              <dt>Heartbeat</dt>
              <dd>{formatTime(device.last_heartbeat_at)}</dd>
            </div>
            <div>
              <dt>Firmware</dt>
              <dd>{device.firmware_version}</dd>
            </div>
            <div>
              <dt>Cấu hình</dt>
              <dd>{device.config_version}</dd>
            </div>
          </dl>
          {device.connectivity_reason && (
            <p className="admin-device-reason">{device.connectivity_reason}</p>
          )}
          <footer>
            {renderConnectivityChip(device)}
            <button
              type="button"
              className="admin-device-card__link"
              onClick={() => openDevice(device)}
            >
              Xem chi tiết
            </button>
          </footer>
        </article>
      ))}
    </div>
  );

  return (
    <div className="admin-dashboard admin-devices-page">
      <header className="admin-dashboard__header">
        <div>
          <h1>Thiết bị IoT</h1>
          <p>
            Registry và telemetry thiết bị · Kết nối, heartbeat, firmware, cấu
            hình và data quality
          </p>
        </div>
        <button
          type="button"
          className="admin-primary-button"
          disabled
          title="Cần device registry API, policy cấp phát và Admin RBAC"
        >
          <Plus size={16} />
          Provision thiết bị
        </button>
      </header>

      <div className="admin-simulator-note" role="note">
        <RadioTower size={15} />
        <span>
          <strong>SIMULATOR</strong> · Trạng thái kết nối, heartbeat và data
          quality bên dưới đến từ Simulator của MVP. Module P2 — frontend không
          publish MQTT, không truy cập broker credential; command chỉ do
          dispatcher server-side thực hiện sau phê duyệt.
        </span>
      </div>

      {error && (
        <div className="admin-error" role="alert">
          <AlertTriangle size={17} />
          <span>{error}</span>
          <button type="button" onClick={loadDevices}>
            Thử lại
          </button>
        </div>
      )}

      {mutationResult && (
        <div
          className={`admin-mutation-banner admin-mutation-banner--${
            mutationResult.outcome === "succeeded" ? "success" : "error"
          }`}
          role="status"
        >
          {mutationResult.outcome === "succeeded" ? (
            <CheckCircle2 size={16} />
          ) : (
            <AlertTriangle size={16} />
          )}
          <span>
            <b className="admin-device-outcome">{mutationResult.outcome}</b>
            {mutationResult.message}
          </span>
          <button
            type="button"
            aria-label="Đóng thông báo"
            onClick={() => setMutationResult(null)}
          >
            <X size={15} />
          </button>
        </div>
      )}

      <section className="admin-devices-toolbar" aria-label="Bộ lọc thiết bị">
        <label className="admin-users-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Tìm kiếm thiết bị</span>
          <input
            type="search"
            placeholder="Tìm theo device ID hoặc station ID..."
            value={filters.query}
            onChange={(event) =>
              setFilters({ ...filters, query: event.target.value })
            }
          />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc khu vực</span>
          <select
            value={filters.region}
            onChange={(event) =>
              setFilters({ ...filters, region: event.target.value })
            }
          >
            <option value="all">Tất cả khu vực</option>
            {regionOptions.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc loại thiết bị</span>
          <select
            value={filters.deviceType}
            onChange={(event) =>
              setFilters({ ...filters, deviceType: event.target.value })
            }
          >
            <option value="all">Tất cả loại thiết bị</option>
            {typeOptions.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc trạng thái kết nối</span>
          <select
            value={filters.connectivity}
            onChange={(event) =>
              setFilters({
                ...filters,
                connectivity: event.target.value as DeviceConnectivity | "all",
              })
            }
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="online">Trực tuyến</option>
            <option value="stale">Gián đoạn</option>
            <option value="offline">Ngoại tuyến</option>
            <option value="invalid">Không hợp lệ</option>
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc firmware và cấu hình</span>
          <select
            value={filters.config}
            onChange={(event) =>
              setFilters({
                ...filters,
                config: event.target.value as Filters["config"],
              })
            }
          >
            <option value="all">Firmware / cấu hình: tất cả</option>
            <option value="firmware_attention">Firmware cần chú ý</option>
            <option value="config_attention">Cấu hình cần chú ý</option>
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc trạng thái bảo trì</span>
          <select
            value={filters.lifecycle}
            onChange={(event) =>
              setFilters({
                ...filters,
                lifecycle: event.target.value as DeviceLifecycle | "all",
              })
            }
          >
            <option value="all">Tất cả vòng đời</option>
            <option value="active">Active</option>
            <option value="maintenance">Bảo trì</option>
            <option value="deactivated">Deactivated</option>
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <button
          type="button"
          className="admin-users-reset"
          onClick={() => setFilters(emptyFilters)}
          disabled={!filtersActive}
        >
          <Filter size={14} />
          Đặt lại
        </button>
      </section>

      {partialError && !loading && (
        <div className="admin-partial-note" role="status">
          <Info size={15} />
          <span>{partialError}</span>
        </div>
      )}

      <section className="admin-card admin-users-panel">
        <header className="admin-card__header">
          <div>
            <Cpu size={17} />
            <h2>Danh sách thiết bị</h2>
          </div>
          <span>
            {loading
              ? "Đang tải…"
              : `${filteredDevices.length} / ${devices.length} thiết bị`}
          </span>
        </header>

        {loading ? (
          <div className="admin-device-skeletons">
            {[0, 1, 2, 3].map((index) => (
              <div
                key={index}
                className="admin-skeleton admin-skeleton--row"
                aria-hidden="true"
              />
            ))}
          </div>
        ) : filteredDevices.length === 0 ? (
          <div className="admin-panel-state">
            <Cpu size={20} />
            {devices.length === 0
              ? "Registry chưa có thiết bị nào."
              : "Không có thiết bị phù hợp với bộ lọc hiện tại."}
            {filtersActive && (
              <button
                type="button"
                className="admin-users-reset"
                onClick={() => setFilters(emptyFilters)}
              >
                Đặt lại bộ lọc
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="admin-users-desktop">{renderTable()}</div>
            <div className="admin-users-mobile">{renderCards()}</div>
          </>
        )}

        <div className="admin-map-legend admin-devices-legend">
          <strong>Chú giải kết nối</strong>
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
      </section>

      {selectedDevice && (
        <div
          className="admin-drawer-scrim"
          role="presentation"
          onClick={() => setSelectedId(null)}
        />
      )}
      {selectedDevice && (
        <aside
          className="admin-station-drawer admin-device-drawer"
          role="dialog"
          aria-modal="true"
          aria-label={`Chi tiết thiết bị ${selectedDevice.device_id}`}
        >
          <header className="admin-station-drawer__header">
            <div>
              <code>{selectedDevice.device_id}</code>
              <strong>{selectedDevice.device_name}</strong>
              <small>
                {selectedDevice.device_type} ·{" "}
                {lifecycleLabel[selectedDevice.lifecycle]}
              </small>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label="Đóng chi tiết thiết bị"
              onClick={() => setSelectedId(null)}
            >
              <X size={20} />
            </button>
          </header>

          <nav
            className="admin-user-drawer__tabs"
            aria-label="Các mục chi tiết thiết bị"
          >
            {(
              [
                ["overview", "Tổng quan"],
                ["connectivity", "Kết nối"],
                ["firmware", "Firmware & cấu hình"],
                ["events", "Sự kiện"],
                ["audit", "Audit"],
              ] as Array<[DetailTab, string]>
            ).map(([tab, label]) => (
              <button
                key={tab}
                type="button"
                className={detailTab === tab ? "is-active" : ""}
                onClick={() => setDetailTab(tab)}
              >
                {label}
              </button>
            ))}
          </nav>

          <div className="admin-station-drawer__body">
            {detailTab === "overview" && (
              <section className="admin-drawer-section">
                <h3>Tổng quan</h3>
                <dl className="admin-user-info">
                  <div>
                    <dt>Device ID</dt>
                    <dd>
                      <code>{selectedDevice.device_id}</code>
                      <small className="admin-user-role-hint">
                        Immutable sau provision; không tái sử dụng ID đã
                        deactivate.
                      </small>
                    </dd>
                  </div>
                  <div>
                    <dt>Loại thiết bị</dt>
                    <dd>{selectedDevice.device_type}</dd>
                  </div>
                  <div>
                    <dt>Trạm liên kết</dt>
                    <dd>
                      {selectedDevice.station_id
                        ? `${selectedDevice.station_id} · ${selectedDevice.station_name}`
                        : "Chưa gán"}
                    </dd>
                  </div>
                  <div>
                    <dt>Serial</dt>
                    <dd>
                      <code>{selectedDevice.serial_masked}</code>
                      <small className="admin-user-role-hint">
                        Đã mask theo policy.
                      </small>
                    </dd>
                  </div>
                  <div>
                    <dt>Nguồn</dt>
                    <dd>
                      {selectedDevice.source}
                      {selectedDevice.is_simulator ? " (simulator)" : ""}
                    </dd>
                  </div>
                  <div>
                    <dt>Ngày provision</dt>
                    <dd>{formatTime(selectedDevice.provisioned_at)}</dd>
                  </div>
                  <div>
                    <dt>Owner vận hành</dt>
                    <dd>{selectedDevice.owner}</dd>
                  </div>
                  <div>
                    <dt>Vòng đời</dt>
                    <dd>{lifecycleLabel[selectedDevice.lifecycle]}</dd>
                  </div>
                </dl>
              </section>
            )}

            {detailTab === "connectivity" && (
              <section className="admin-drawer-section">
                <h3>Kết nối</h3>
                <dl className="admin-user-info">
                  <div>
                    <dt>Trạng thái</dt>
                    <dd>{renderConnectivityChip(selectedDevice)}</dd>
                  </div>
                  <div>
                    <dt>Heartbeat cuối</dt>
                    <dd>{formatTime(selectedDevice.last_heartbeat_at)}</dd>
                  </div>
                  <div>
                    <dt>Heartbeat interval</dt>
                    <dd>
                      {formatInterval(
                        selectedDevice.heartbeat_interval_seconds,
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Uptime 24h</dt>
                    <dd>{formatUptime(selectedDevice.uptime_ratio_24h)}</dd>
                  </div>
                  <div>
                    <dt>Latency</dt>
                    <dd>{formatLatency(selectedDevice.latency_ms)}</dd>
                  </div>
                </dl>
                {selectedDevice.connectivity_reason && (
                  <div className="admin-drawer-warning" role="note">
                    <AlertTriangle size={15} />
                    <span>{selectedDevice.connectivity_reason}</span>
                  </div>
                )}
                <p className="admin-user-actions__note">
                  Trạng thái kết nối đến từ backend, không suy diễn từ client
                  timer. Thiếu heartbeat không được hiển thị thành online.
                </p>
              </section>
            )}

            {detailTab === "firmware" && (
              <>
                <section className="admin-drawer-section">
                  <h3>Firmware & cấu hình</h3>
                  <dl className="admin-user-info">
                    <div>
                      <dt>Firmware hiện tại</dt>
                      <dd>{selectedDevice.firmware_version}</dd>
                    </div>
                    <div>
                      <dt>Firmware khuyến nghị</dt>
                      <dd>
                        {selectedDevice.firmware_recommended ??
                          "Không khả dụng"}
                        <small className="admin-user-role-hint">
                          {firmwareLabel[selectedDevice.firmware_state]}
                        </small>
                      </dd>
                    </div>
                    <div>
                      <dt>Config profile / version</dt>
                      <dd>
                        {selectedDevice.config_profile} ·{" "}
                        {selectedDevice.config_version}
                      </dd>
                    </div>
                    <div>
                      <dt>Checksum</dt>
                      <dd>
                        <code>{selectedDevice.config_checksum}</code>
                        <small className="admin-user-role-hint">
                          Đã redacted — không hiển thị secret, MQTT URL hay
                          token.
                        </small>
                      </dd>
                    </div>
                    <div>
                      <dt>Trạng thái cấu hình</dt>
                      <dd>{configLabel[selectedDevice.config_state]}</dd>
                    </div>
                    <div>
                      <dt>Áp dụng lúc</dt>
                      <dd>{formatTime(selectedDevice.config_applied_at)}</dd>
                    </div>
                    <div>
                      <dt>Calibration</dt>
                      <dd>
                        {selectedDevice.calibration_note ?? "Không khả dụng"}
                      </dd>
                    </div>
                  </dl>
                </section>

                <section className="admin-drawer-section">
                  <h3>Data quality</h3>
                  <dl className="admin-user-info">
                    <div>
                      <dt>Khoảng tổng hợp</dt>
                      <dd>{selectedDevice.data_quality.window_label}</dd>
                    </div>
                    <div>
                      <dt>Invalid</dt>
                      <dd>{selectedDevice.data_quality.invalid_count}</dd>
                    </div>
                    <div>
                      <dt>Duplicate</dt>
                      <dd>{selectedDevice.data_quality.duplicate_count}</dd>
                    </div>
                    <div>
                      <dt>Rejected</dt>
                      <dd>{selectedDevice.data_quality.rejected_count}</dd>
                    </div>
                    <div>
                      <dt>Reason code gần nhất</dt>
                      <dd>
                        {selectedDevice.data_quality.last_reason_code ? (
                          <code>
                            {selectedDevice.data_quality.last_reason_code}
                          </code>
                        ) : (
                          "Không có"
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>Sự kiện gần nhất</dt>
                      <dd>
                        {formatTime(selectedDevice.data_quality.last_event_at)}
                      </dd>
                    </div>
                  </dl>
                  <p className="admin-user-actions__note">
                    Giá trị thiếu không được thay bằng 0; measurement invalid
                    không được coi là telemetry hợp lệ.
                  </p>
                </section>
              </>
            )}

            {detailTab === "events" && (
              <section className="admin-drawer-section">
                <h3>Sự kiện</h3>
                {events.length === 0 ? (
                  <div className="admin-panel-state admin-panel-state--compact">
                    Chưa có sự kiện nào được ghi nhận cho thiết bị này.
                  </div>
                ) : (
                  <ul className="admin-user-audit-list">
                    {events.map((event) => (
                      <li key={event.id}>
                        <time>{formatTime(event.time)}</time>
                        <div>
                          <strong>{event.type}</strong>
                          <p>{event.detail}</p>
                          <code>
                            {event.outcome} · {event.correlation_id}
                          </code>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {detailTab === "audit" && (
              <section className="admin-drawer-section">
                <h3>Audit</h3>
                {events.length === 0 ? (
                  <div className="admin-panel-state admin-panel-state--compact">
                    Chưa có bản ghi audit cho thiết bị này.
                  </div>
                ) : (
                  <ul className="admin-user-audit-list">
                    {events.map((event) => (
                      <li key={`audit-${event.id}`}>
                        <time>{formatTime(event.time)}</time>
                        <div>
                          <strong>{event.type}</strong>
                          <span>
                            {selectedDevice.owner} · {selectedDevice.device_id}
                          </span>
                          <code>
                            {event.outcome} · {event.correlation_id}
                          </code>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                <p className="admin-user-actions__note">
                  Audit chỉ đọc gồm actor, action, target, outcome và
                  correlation id. Deactivate thay vì hard-delete; measurement,
                  event và audit được giữ theo retention policy.
                </p>
              </section>
            )}
          </div>

          <footer className="admin-station-drawer__footer">
            {selectedDevice.station_id ? (
              <button
                type="button"
                className="admin-primary-button"
                onClick={() => {
                  navigateTo("station-detail", {
                    stationId: selectedDevice.station_id!,
                  });
                  setSelectedId(null);
                }}
              >
                <ExternalLink size={15} />
                Xem dữ liệu trạm liên kết
              </button>
            ) : (
              <button
                type="button"
                className="admin-primary-button"
                disabled
                title="Thiết bị chưa gán trạm nên không có dữ liệu để mở"
              >
                <ExternalLink size={15} />
                Chưa gán trạm
              </button>
            )}
            <div className="admin-station-drawer__secondary">
              <button
                type="button"
                onClick={() =>
                  requestAction("update_config", selectedDevice)
                }
              >
                <Settings2 size={14} />
                Cập nhật cấu hình
              </button>
              <button
                type="button"
                className="admin-station-drawer__danger"
                onClick={() =>
                  requestAction(
                    selectedDevice.lifecycle === "deactivated"
                      ? "reactivate"
                      : "deactivate",
                    selectedDevice,
                  )
                }
              >
                <Ban size={14} />
                {selectedDevice.lifecycle === "deactivated"
                  ? "Kích hoạt lại"
                  : "Deactivate"}
              </button>
            </div>
            <p className="admin-device-drawer__note">
              Không có điều khiển thiết bị trực tiếp hay publish MQTT từ
              browser. Mọi command do dispatcher server-side thực hiện sau
              server-side approval.
            </p>
          </footer>
        </aside>
      )}

      {pendingAction && (
        <div
          className="admin-confirm-scrim"
          role="presentation"
          onClick={() => setPendingAction(null)}
        />
      )}
      {pendingAction && (
        <div
          className="admin-confirm-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="device-confirm-title"
        >
          <header>
            <span className="admin-confirm-modal__icon">
              {pendingAction.kind === "deactivate" ? (
                <Ban size={20} />
              ) : (
                <Settings2 size={20} />
              )}
            </span>
            <div>
              <h2 id="device-confirm-title">
                {actionLabel[pendingAction.kind]}
              </h2>
              <p>
                {pendingAction.device.device_id} ·{" "}
                {pendingAction.device.device_name}
              </p>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label="Đóng"
              onClick={() => setPendingAction(null)}
            >
              <X size={18} />
            </button>
          </header>

          <div className="admin-confirm-modal__body">
            <div className="admin-confirm-impact">
              <strong>Tác động:</strong>
              <span>{actionImpact[pendingAction.kind]}</span>
            </div>
            <label className="admin-confirm-reason">
              <span>
                Lý do thay đổi <b aria-hidden="true">*</b>
              </span>
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Bắt buộc nhập lý do để ghi vào audit..."
                rows={3}
              />
            </label>
            <p className="admin-user-actions__note">
              UI chỉ hiển thị outcome do backend trả về:{" "}
              <code>not_configured</code>, <code>pending</code>,{" "}
              <code>succeeded</code> hoặc <code>failed</code>.
            </p>
          </div>

          <footer>
            <button
              type="button"
              className="admin-confirm-cancel"
              onClick={() => setPendingAction(null)}
              disabled={submitting}
            >
              Hủy
            </button>
            <button
              type="button"
              className={`admin-confirm-submit admin-confirm-submit--${
                pendingAction.kind === "deactivate" ? "danger" : "primary"
              }`}
              onClick={submitAction}
              disabled={submitting || !reason.trim()}
            >
              {submitting && <RefreshCw className="is-spinning" size={15} />}
              {submitting
                ? "Đang gửi..."
                : `Xác nhận ${actionLabel[pendingAction.kind].toLowerCase()}`}
            </button>
          </footer>
        </div>
      )}
    </div>
  );
};

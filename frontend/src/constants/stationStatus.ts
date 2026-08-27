import { Station, StationStatus } from "../types";

export interface StationStatusConfig {
  status: StationStatus;
  label: string;
  symbol: string;
  color: string;
  bgColor: string;
  borderStyle: "solid" | "dashed" | "double" | "dotted";
  iconClass: string;
  description: string;
  tooltipText: string;
}

/**
 * Canonical 4-State Station Configuration
 * Single Source of Truth shared between AqiLegend, SensorMarkers, and Map components.
 */
export const STATION_STATUS_CONFIG: Record<StationStatus, StationStatusConfig> = {
  online: {
    status: "online",
    label: "Online",
    symbol: "●",
    color: "#10b981",
    bgColor: "rgba(16, 185, 129, 0.15)",
    borderStyle: "solid",
    iconClass: "status-online",
    description: "Trực tuyến · Dữ liệu mới cập nhật",
    tooltipText: "Trạm đang hoạt động và truyền dữ liệu bình thường",
  },
  stale: {
    status: "stale",
    label: "Stale (Dữ liệu cũ)",
    symbol: "▲",
    color: "#f59e0b",
    bgColor: "rgba(245, 158, 11, 0.15)",
    borderStyle: "dashed",
    iconClass: "status-stale",
    description: "Dữ liệu cũ · Chưa có bản tin mới trong ngưỡng tươi",
    tooltipText: "Dữ liệu quá hạn (stale) - Cần kiểm tra kết nối trạm",
  },
  offline: {
    status: "offline",
    label: "Offline",
    symbol: "✖",
    color: "#ef4444",
    bgColor: "rgba(239, 68, 68, 0.15)",
    borderStyle: "double",
    iconClass: "status-offline",
    description: "Mất kết nối · Không nhận được tín hiệu",
    tooltipText: "Trạm đã ngắt kết nối hoặc mất nguồn",
  },
  invalid: {
    status: "invalid",
    label: "Invalid",
    symbol: "?",
    color: "#64748b",
    bgColor: "rgba(100, 116, 139, 0.15)",
    borderStyle: "dotted",
    iconClass: "status-invalid",
    description: "Lỗi dữ liệu · Cảm biến hỏng hoặc giá trị ngoài dải",
    tooltipText: "Dữ liệu không hợp lệ hoặc cảm biến gặp sự cố",
  },
};

/**
 * Resolves station data quality status with clear precedence:
 * invalid > offline > stale > online
 */
export function resolveStationStatus(
  station: Partial<Station> | null | undefined
): StationStatus {
  if (!station) return "offline";

  if (station.status === "invalid") {
    return "invalid";
  }

  if (station.status === "offline") {
    return "offline";
  }

  if (station.status === "stale" || station.is_stale === true) {
    return "stale";
  }

  if (station.status === "online") {
    return "online";
  }

  return "offline";
}

export function getStationStatusConfig(status: StationStatus): StationStatusConfig {
  return STATION_STATUS_CONFIG[status] || STATION_STATUS_CONFIG.offline;
}

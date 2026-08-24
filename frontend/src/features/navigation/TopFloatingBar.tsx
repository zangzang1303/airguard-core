import React from "react";
import { Wind, Bell, User, ShieldCheck, FileClock, Wifi, WifiOff, RefreshCw, EyeOff } from "lucide-react";
import { PlaceSearchOmnibox } from "./PlaceSearchOmnibox";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";
import { formatVnTimeWithSeconds } from "../../utils/datetime";

/**
 * Format alert count badge:
 * - count <= 0: null (badge hidden)
 * - 1 <= count <= 99: exact count as string
 * - count > 99: "99+"
 */
export const formatAlertBadge = (count: number): string | null => {
  if (count <= 0) return null;
  if (count > 99) return "99+";
  return count.toString();
};

interface TopFloatingBarProps {
  stations: Station[];
  activeAlertCount: number;
  isAlertsOpen?: boolean;
  isManager: boolean;
  connectionStatus: "connected" | "updating" | "disconnected";
  lastStationSyncAt?: Date | null;
  lastUpdated?: Date | null;
  refreshData: () => Promise<void>;
  showConnectionStatus: boolean;
  hasAIOverlay?: boolean;
  onClearAIOverlay?: () => void;
  onSelectCoordinates: (coords: [number, number], title: string) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onOpenAlerts: () => void;
  onOpenProfile: () => void;
  onOpenManagerDrawer: () => void;
  onOpenAudit?: () => void;
  onAskAiWithQuery: (query: string) => void;
  onSetUserLocation?: (
    coords: [number, number],
    name: string,
    source: "search" | "manual_click" | "gps"
  ) => void;
  onLocateGps?: () => void;
  onStartPickOnMap?: () => void;
}

export const TopFloatingBar: React.FC<TopFloatingBarProps> = ({
  stations,
  activeAlertCount,
  isAlertsOpen = false,
  isManager,
  connectionStatus,
  lastStationSyncAt,
  lastUpdated,
  refreshData,
  showConnectionStatus,
  hasAIOverlay = false,
  onClearAIOverlay,
  onSelectCoordinates,
  onSelectStation,
  onSelectPoi,
  onOpenAlerts,
  onOpenProfile,
  onOpenManagerDrawer,
  onOpenAudit,
  onAskAiWithQuery,
  onSetUserLocation,
  onLocateGps,
  onStartPickOnMap,
}) => {
  const syncTime = lastStationSyncAt ?? lastUpdated ?? null;
  const formattedAlertBadge = formatAlertBadge(activeAlertCount);
  const alertAriaLabel =
    activeAlertCount > 0
      ? `Cảnh báo môi trường, có ${activeAlertCount > 99 ? "hơn 99" : activeAlertCount} cảnh báo đang hoạt động`
      : "Cảnh báo môi trường, không có cảnh báo nào";

  const formattedSyncTime = syncTime ? formatVnTimeWithSeconds(syncTime) : "Chưa đồng bộ";

  return (
    <header className="top-floating-bar-header">
      {/* Top Left Controls Group: Brand Badge & Connection Status (Structured normal flow) */}
      <div className="top-left-controls-group">
        {/* Brand & Location Identifier (Always rendered) */}
        <div
          className="top-brand-badge"
          onClick={() => onSelectCoordinates([20.9942, 105.9485], "Ocean Park 1")}
          role="button"
          tabIndex={0}
          aria-label="Về vị trí trung tâm Vinhomes Ocean Park 1"
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onSelectCoordinates([20.9942, 105.9485], "Ocean Park 1");
            }
          }}
        >
          <div className="brand-logo-circle" aria-hidden="true">
            <Wind size={18} className="brand-icon" />
          </div>
          <div className="brand-text-block">
            <span className="brand-name">AirGuard</span>
            <span className="brand-location">Ocean Park 1</span>
          </div>
        </div>

        {/* Connection Status Badge Bar (Controlled by showConnectionStatus) */}
        {showConnectionStatus && (
          <div
            className="connection-status-badge-bar"
            role="status"
            aria-live="polite"
            aria-label={`Trạng thái kết nối: ${
              connectionStatus === "connected"
                ? "Đã kết nối trực tiếp"
                : connectionStatus === "updating"
                ? "Đang cập nhật dữ liệu"
                : "Mất kết nối - Đang thử lại"
            }. ${syncTime ? `Đồng bộ trạm lúc ${formattedSyncTime}` : "Chưa đồng bộ"}`}
          >
          <span className="status-indicator">
            {connectionStatus === "connected" && (
              <>
                <Wifi size={13} className="status-icon status-connected-icon" aria-hidden="true" />
                <strong className="status-label status-connected-text">
                  <span className="status-text-full">Live Connected</span>
                  <span className="status-text-short">Đã kết nối</span>
                </strong>
              </>
            )}
            {connectionStatus === "updating" && (
              <>
                <RefreshCw size={13} className="status-icon spin-icon status-updating-icon" aria-hidden="true" />
                <strong className="status-label status-updating-text">
                  <span className="status-text-full">Đang cập nhật...</span>
                  <span className="status-text-short">Cập nhật...</span>
                </strong>
              </>
            )}
            {connectionStatus === "disconnected" && (
              <>
                <WifiOff size={13} className="status-icon status-disconnected-icon" aria-hidden="true" />
                <strong className="status-label status-disconnected-text">
                  <span className="status-text-full">Mất kết nối - Đang thử lại</span>
                  <span className="status-text-short">Mất kết nối</span>
                </strong>
              </>
            )}
          </span>
          <span className="status-divider" aria-hidden="true">
            |
          </span>
          <span className="status-time">
            {syncTime ? (
              <>
                <span className="time-prefix">Đồng bộ trạm lúc </span>
                <span className="time-val">{formattedSyncTime}</span>
              </>
            ) : (
              "Chưa đồng bộ"
            )}
          </span>
          <button
            type="button"
            onClick={refreshData}
            disabled={connectionStatus === "updating"}
            className="status-refresh-btn"
            title="Làm mới dữ liệu thủ công"
            aria-label="Làm mới dữ liệu thủ công"
          >
            <RefreshCw size={12} className={connectionStatus === "updating" ? "spin-icon" : ""} aria-hidden="true" />
          </button>
        </div>
        )}

        {/* Proactive AI Overlay Clear Button in normal stack flow */}
        {hasAIOverlay && onClearAIOverlay && (
          <button
            type="button"
            className="ai-overlay-clear-floating-btn"
            onClick={onClearAIOverlay}
            aria-label="Xóa các lớp hiển thị do AI tạo trên bản đồ"
            title="Xóa hiển thị AI trên bản đồ"
          >
            <EyeOff size={13} aria-hidden="true" />
            <span>Xóa hiển thị AI</span>
          </button>
        )}
      </div>

      {/* Center Search Omnibox */}
      <PlaceSearchOmnibox
        stations={stations}
        onSelectCoordinates={onSelectCoordinates}
        onSelectStation={onSelectStation}
        onSelectPoi={onSelectPoi}
        onAskAiWithQuery={onAskAiWithQuery}
        onSetUserLocation={onSetUserLocation}
        onLocateGps={onLocateGps}
        onStartPickOnMap={onStartPickOnMap}
      />

      {/* Right Quick Action Utility Icons */}
      <div className="top-actions-right">
        {/* Active Alerts Bell: Single entry point for environmental alerts */}
        <button
          type="button"
          className={`top-icon-btn ${activeAlertCount > 0 ? "has-alerts" : ""} ${isAlertsOpen ? "active" : ""}`}
          onClick={onOpenAlerts}
          title={alertAriaLabel}
          aria-label={alertAriaLabel}
          aria-expanded={isAlertsOpen}
        >
          <Bell size={18} aria-hidden="true" />
          {formattedAlertBadge && (
            <span className="badge-count" aria-hidden="true">
              {formattedAlertBadge}
            </span>
          )}
        </button>

        {/* Manager Mode Access Button */}
        {isManager && (
          <>
            <button
              type="button"
              className="top-manager-btn"
              onClick={onOpenManagerDrawer}
              title="Bảng phê duyệt Ban Quản Lý"
              aria-label="Mở Bảng phê duyệt Ban Quản Lý"
            >
              <ShieldCheck size={16} aria-hidden="true" />
              <span className="btn-text">Duyệt BQL</span>
            </button>
            {onOpenAudit && (
              <button
                type="button"
                className="top-icon-btn"
                onClick={onOpenAudit}
                title="Nhật ký Audit Log"
                aria-label="Mở Nhật ký Audit Log"
              >
                <FileClock size={18} aria-hidden="true" />
              </button>
            )}
          </>
        )}

        {/* User Health Profile */}
        <button
          type="button"
          className="top-icon-btn profile-btn"
          onClick={onOpenProfile}
          title="Hồ sơ người dùng & Đăng xuất"
          aria-label="Hồ sơ người dùng & Đăng xuất"
        >
          <User size={18} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
};




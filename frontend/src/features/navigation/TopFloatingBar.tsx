import React from "react";
import { Wind, Bell, Sparkles, User, ShieldCheck, FileClock, Wifi, WifiOff, RefreshCw, EyeOff } from "lucide-react";
import { PlaceSearchOmnibox } from "./PlaceSearchOmnibox";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";

interface TopFloatingBarProps {
  stations: Station[];
  activeAlertCount: number;
  isManager: boolean;
  connectionStatus: "connected" | "updating" | "disconnected";
  lastUpdated: Date | null;
  refreshData: () => Promise<void>;
  showConnectionStatus: boolean;
  hasAIOverlay?: boolean;
  onClearAIOverlay?: () => void;
  onSelectCoordinates: (coords: [number, number], title: string) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onOpenAiChat: () => void;
  onOpenAlerts: () => void;
  onOpenProfile: () => void;
  onOpenManagerDrawer: () => void;
  onOpenAudit?: () => void;
  onAskAiWithQuery: (query: string) => void;
}

export const TopFloatingBar: React.FC<TopFloatingBarProps> = ({
  stations,
  activeAlertCount,
  isManager,
  connectionStatus,
  lastUpdated,
  refreshData,
  showConnectionStatus,
  hasAIOverlay = false,
  onClearAIOverlay,
  onSelectCoordinates,
  onSelectStation,
  onSelectPoi,
  onOpenAiChat,
  onOpenAlerts,
  onOpenProfile,
  onOpenManagerDrawer,
  onOpenAudit,
  onAskAiWithQuery,
}) => {
  return (
    <header className="top-floating-bar-header">
      {/* Top Left Controls Group: Brand Badge & Connection Status (Structured normal flow) */}
      <div className="top-left-controls-group">
        {/* Brand & Location Identifier */}
        {showConnectionStatus && <div
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
        </div>}

        {/* Connection Status Badge Bar */}
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
          }. ${lastUpdated ? `Dữ liệu cập nhật lúc ${lastUpdated.toLocaleTimeString("vi-VN")}` : "Chưa đồng bộ"}`}
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
          <span className="status-divider" aria-hidden="true">|</span>
          <span className="status-time">
            {lastUpdated ? (
              <>
                <span className="time-prefix">Vừa cập nhật </span>
                <span className="time-val">{lastUpdated.toLocaleTimeString("vi-VN")}</span>
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
            title="Làm mới thủ công"
            aria-label="Làm mới dữ liệu thủ công"
          >
            <RefreshCw size={12} className={connectionStatus === "updating" ? "spin-icon" : ""} aria-hidden="true" />
          </button>
        </div>

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
      />

      {/* Right Quick Action Utility Icons */}
      <div className="top-actions-right">
        {/* Active Alerts Bell */}
        <button
          className={`top-icon-btn ${activeAlertCount > 0 ? "has-alerts" : ""}`}
          onClick={onOpenAlerts}
          title="Cảnh báo môi trường"
        >
          <Bell size={18} />
          {activeAlertCount > 0 && <span className="badge-count">{activeAlertCount}</span>}
        </button>

        {/* Ask AirGuard AI Button */}
        <button
          className="top-ai-btn"
          onClick={onOpenAiChat}
          title="Trò chuyện với AirGuard AI"
        >
          <Sparkles size={16} />
          <span className="btn-text">Hỏi AI</span>
        </button>

        {/* Manager Mode Access Button */}
        {isManager && (
          <>
            <button
              className="top-manager-btn"
              onClick={onOpenManagerDrawer}
              title="Bảng phê duyệt Ban Quản Lý"
            >
              <ShieldCheck size={16} />
              <span className="btn-text">Duyệt BQL</span>
            </button>
            {onOpenAudit && (
              <button
                className="top-icon-btn"
                onClick={onOpenAudit}
                title="Nhật ký Audit Log"
              >
                <FileClock size={18} />
              </button>
            )}
          </>
        )}

        {/* User Health Profile */}
        <button
          className="top-icon-btn profile-btn"
          onClick={onOpenProfile}
          title="Hồ sơ người dùng & Đăng xuất"
        >
          <User size={18} />
        </button>
      </div>
    </header>
  );
};



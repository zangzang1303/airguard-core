import React from "react";
import { Wind, Bell, Sparkles, User, ShieldCheck, FileClock, Wifi, WifiOff, RefreshCw } from "lucide-react";
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
      {/* Top Left Controls Group: Brand Badge & Connection Status */}
      <div className="top-left-controls-group">
        {/* Brand & Location Identifier */}
        <div className="top-brand-badge" onClick={() => onSelectCoordinates([20.9942, 105.9485], "Ocean Park 1")}>
          <div className="brand-logo-circle">
            <Wind size={18} className="brand-icon" />
          </div>
          <div className="brand-text-block">
            <span className="brand-name">AirGuard</span>
            <span className="brand-location">Ocean Park 1</span>
          </div>
        </div>

        {/* Connection Status Badge Bar */}
        <div className="connection-status-badge-bar">
          <span className="status-indicator">
            {connectionStatus === "connected" && (
              <>
                <Wifi size={13} style={{ color: "#10b981" }} />
                <strong style={{ color: "#10b981" }}>Live Connected</strong>
              </>
            )}
            {connectionStatus === "updating" && (
              <>
                <RefreshCw size={13} className="spin-icon" style={{ color: "#3b82f6" }} />
                <strong style={{ color: "#3b82f6" }}>Đang cập nhật...</strong>
              </>
            )}
            {connectionStatus === "disconnected" && (
              <>
                <WifiOff size={13} style={{ color: "#ef4444" }} />
                <strong style={{ color: "#ef4444" }}>Mất kết nối - Đang thử lại</strong>
              </>
            )}
          </span>
          <span className="status-divider">|</span>
          <span className="status-time">
            {lastUpdated ? `Vừa cập nhật ${lastUpdated.toLocaleTimeString("vi-VN")}` : "Chưa đồng bộ"}
          </span>
          <button
            type="button"
            onClick={refreshData}
            disabled={connectionStatus === "updating"}
            className="status-refresh-btn"
            title="Làm mới thủ công"
          >
            <RefreshCw size={12} className={connectionStatus === "updating" ? "spin-icon" : ""} />
          </button>
        </div>
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



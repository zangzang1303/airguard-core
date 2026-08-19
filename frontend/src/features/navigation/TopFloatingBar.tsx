import React from "react";
import { Wind, Bell, Sparkles, User, ShieldCheck } from "lucide-react";
import { PlaceSearchOmnibox } from "./PlaceSearchOmnibox";
import { Station } from "../../types";
import { PlacePOI } from "../../types/superApp";

interface TopFloatingBarProps {
  stations: Station[];
  activeAlertCount: number;
  isManager: boolean;
  onSelectCoordinates: (coords: [number, number], title: string) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onOpenAiChat: () => void;
  onOpenAlerts: () => void;
  onOpenProfile: () => void;
  onOpenManagerDrawer: () => void;
  onAskAiWithQuery: (query: string) => void;
}

export const TopFloatingBar: React.FC<TopFloatingBarProps> = ({
  stations,
  activeAlertCount,
  isManager,
  onSelectCoordinates,
  onSelectStation,
  onSelectPoi,
  onOpenAiChat,
  onOpenAlerts,
  onOpenProfile,
  onOpenManagerDrawer,
  onAskAiWithQuery,
}) => {
  return (
    <header className="top-floating-bar-header">
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
          <button
            className="top-manager-btn"
            onClick={onOpenManagerDrawer}
            title="Bảng phê duyệt Ban Quản Lý"
          >
            <ShieldCheck size={16} />
            <span className="btn-text">Duyệt BQL</span>
          </button>
        )}

        {/* User Health Profile */}
        <button
          className="top-icon-btn profile-btn"
          onClick={onOpenProfile}
          title="Hồ sơ sức khỏe & Cài đặt"
        >
          <User size={18} />
        </button>
      </div>
    </header>
  );
};

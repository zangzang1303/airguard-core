import React from "react";
import { Layers, MapPin, Calendar, Clock, Bell, AlertTriangle, Sparkles, MessageSquarePlus } from "lucide-react";
import { ActiveDrawerType } from "../../types/superApp";

interface BottomActionDockProps {
  activeDrawer: ActiveDrawerType;
  isLayersOpen: boolean;
  activeAlertCount: number;
  onToggleLayers: () => void;
  onOpenDrawer: (drawer: ActiveDrawerType) => void;
}

export const BottomActionDock: React.FC<BottomActionDockProps> = ({
  activeDrawer,
  isLayersOpen,
  activeAlertCount,
  onToggleLayers,
  onOpenDrawer,
}) => {
  return (
    <nav className="bottom-action-dock-bar">
      {/* 1. Layers Toggle */}
      <button
        className={`dock-action-btn ${isLayersOpen ? "active" : ""}`}
        onClick={onToggleLayers}
        title="Lớp hiển thị bản đồ"
      >
        <Layers size={18} />
        <span className="dock-label">Lớp bản đồ</span>
      </button>

      {/* 2. Near Me */}
      <button
        className={`dock-action-btn ${activeDrawer === "near-me" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "near-me" ? null : "near-me")}
        title="Chất lượng không khí gần bạn"
      >
        <MapPin size={18} />
        <span className="dock-label">Gần tôi</span>
      </button>

      {/* 3. Today Summary */}
      <button
        className={`dock-action-btn ${activeDrawer === "today" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "today" ? null : "today")}
        title="Tổng hợp thời tiết & môi trường hôm nay"
      >
        <Calendar size={18} />
        <span className="dock-label">Hôm nay</span>
      </button>

      {/* 4. Forecast Timeline Slider */}
      <button
        className={`dock-action-btn ${activeDrawer === "forecast-bar" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "forecast-bar" ? null : "forecast-bar")}
        title="Dự báo chất lượng không khí theo dòng thời gian"
      >
        <Clock size={18} />
        <span className="dock-label">Dự báo</span>
      </button>

      {/* 5. Alerts */}
      <button
        className={`dock-action-btn ${activeDrawer === "alerts" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "alerts" ? null : "alerts")}
        title="Cảnh báo môi trường"
      >
        <div className="dock-icon-wrap">
          <Bell size={18} />
          {activeAlertCount > 0 && <span className="dock-badge">{activeAlertCount}</span>}
        </div>
        <span className="dock-label">Cảnh báo</span>
      </button>

      {/* 6. Community Report */}
      <button
        className={`dock-action-btn ${activeDrawer === "community-report" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "community-report" ? null : "community-report")}
        title="Báo cáo ô nhiễm cộng đồng"
      >
        <MessageSquarePlus size={18} />
        <span className="dock-label">Phản ánh</span>
      </button>

      {/* 7. Ask AirGuard AI */}
      <button
        className={`dock-action-btn ai-highlight-btn ${activeDrawer === "ai-chat" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "ai-chat" ? null : "ai-chat")}
        title="Trò chuyện với trợ lý môi trường AI"
      >
        <Sparkles size={18} />
        <span className="dock-label">Hỏi AI</span>
      </button>
    </nav>
  );
};

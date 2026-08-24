import React from "react";
import { Layers, MapPin, Calendar, Sparkles, MessageSquarePlus } from "lucide-react";
import { ActiveDrawerType } from "../../types/superApp";

interface BottomActionDockProps {
  activeDrawer: ActiveDrawerType;
  isLayersOpen: boolean;
  onToggleLayers: () => void;
  onOpenDrawer: (drawer: ActiveDrawerType) => void;
}

export const BottomActionDock: React.FC<BottomActionDockProps> = ({
  activeDrawer,
  isLayersOpen,
  onToggleLayers,
  onOpenDrawer,
}) => {
  return (
    <nav className="bottom-action-dock-bar" aria-label="Điều hướng chính ứng dụng">
      {/* 1. Layers Toggle */}
      <button
        type="button"
        className={`dock-action-btn ${isLayersOpen ? "active" : ""}`}
        onClick={onToggleLayers}
        title="Lớp hiển thị bản đồ"
        aria-label="Lớp hiển thị bản đồ"
        aria-pressed={isLayersOpen}
      >
        <div className="dock-icon-wrap">
          <Layers size={18} aria-hidden="true" />
          {isLayersOpen && <span className="dock-active-dot" aria-hidden="true" />}
        </div>
        <span className="dock-label">Lớp bản đồ</span>
      </button>

      {/* 2. Near Me */}
      <button
        type="button"
        className={`dock-action-btn ${activeDrawer === "near-me" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "near-me" ? null : "near-me")}
        title="Chất lượng không khí gần bạn"
        aria-label="Chất lượng không khí gần bạn"
        aria-expanded={activeDrawer === "near-me"}
      >
        <div className="dock-icon-wrap">
          <MapPin size={18} aria-hidden="true" />
          {activeDrawer === "near-me" && <span className="dock-active-dot" aria-hidden="true" />}
        </div>
        <span className="dock-label">Gần tôi</span>
      </button>

      {/* 3. Today Summary */}
      <button
        type="button"
        className={`dock-action-btn ${activeDrawer === "today" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "today" ? null : "today")}
        title="Tổng hợp thời tiết & môi trường hôm nay"
        aria-label="Tổng hợp thời tiết & môi trường hôm nay"
        aria-expanded={activeDrawer === "today"}
      >
        <div className="dock-icon-wrap">
          <Calendar size={18} aria-hidden="true" />
          {activeDrawer === "today" && <span className="dock-active-dot" aria-hidden="true" />}
        </div>
        <span className="dock-label">Hôm nay</span>
      </button>

      {/* 4. Community Report */}
      <button
        type="button"
        className={`dock-action-btn ${activeDrawer === "community-report" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "community-report" ? null : "community-report")}
        title="Báo cáo ô nhiễm cộng đồng"
        aria-label="Báo cáo ô nhiễm cộng đồng"
        aria-expanded={activeDrawer === "community-report"}
      >
        <div className="dock-icon-wrap">
          <MessageSquarePlus size={18} aria-hidden="true" />
          {activeDrawer === "community-report" && <span className="dock-active-dot" aria-hidden="true" />}
        </div>
        <span className="dock-label">Phản ánh</span>
      </button>

      {/* 5. Ask AirGuard AI - Single entry point for AI Chat */}
      <button
        type="button"
        className={`dock-action-btn ai-highlight-btn ${activeDrawer === "ai-chat" ? "active" : ""}`}
        onClick={() => onOpenDrawer(activeDrawer === "ai-chat" ? null : "ai-chat")}
        title="Trò chuyện với trợ lý môi trường AI"
        aria-label="Hỏi Trợ lý AirGuard AI"
        aria-expanded={activeDrawer === "ai-chat"}
      >
        <div className="dock-icon-wrap">
          <Sparkles size={18} aria-hidden="true" />
          {activeDrawer === "ai-chat" && <span className="dock-active-dot ai-dot" aria-hidden="true" />}
        </div>
        <span className="dock-label">Hỏi AI</span>
      </button>
    </nav>
  );
};



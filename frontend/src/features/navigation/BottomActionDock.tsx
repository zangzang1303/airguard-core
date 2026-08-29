import React from "react";
import { Calendar, Layers, MapPin, MessageSquarePlus, Sparkles } from "lucide-react";
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
  const toggleDrawer = (drawer: ActiveDrawerType) => {
    onOpenDrawer(activeDrawer === drawer ? null : drawer);
  };

  return (
    <nav className="bottom-action-dock-bar" aria-label="Điều hướng chính ứng dụng">
      <button
        type="button"
        className={`dock-action-btn ${isLayersOpen ? "active" : ""}`}
        onClick={() => {
          onToggleLayers();
        }}
        title="Lớp hiển thị bản đồ"
        aria-label="Lớp hiển thị bản đồ"
        aria-pressed={isLayersOpen}
      >
        <div className="dock-icon-wrap">
          <Layers size={18} aria-hidden="true" />
        </div>
        <span className="dock-label">Lớp bản đồ</span>
      </button>

      <button
        type="button"
        className={`dock-action-btn ${activeDrawer === "near-me" ? "active" : ""}`}
        onClick={() => toggleDrawer("near-me")}
        title="Chất lượng không khí quanh bạn"
        aria-label="Mở Gần tôi"
        aria-pressed={activeDrawer === "near-me"}
      >
        <div className="dock-icon-wrap">
          <MapPin size={18} aria-hidden="true" />
        </div>
        <span className="dock-label">Gần tôi</span>
      </button>

      <button
        type="button"
        className={`dock-action-btn ${activeDrawer === "today" ? "active" : ""}`}
        onClick={() => toggleDrawer("today")}
        title="Tóm tắt môi trường trong ngày"
        aria-label="Mở Hôm nay"
        aria-pressed={activeDrawer === "today"}
      >
        <div className="dock-icon-wrap">
          <Calendar size={18} aria-hidden="true" />
        </div>
        <span className="dock-label">Hôm nay</span>
      </button>

      <button
        type="button"
        className={`dock-action-btn ${activeDrawer === "community-report" ? "active" : ""}`}
        onClick={() => toggleDrawer("community-report")}
        title="Gửi phản ánh cộng đồng"
        aria-label="Mở Phản ánh"
        aria-pressed={activeDrawer === "community-report"}
      >
        <div className="dock-icon-wrap">
          <MessageSquarePlus size={18} aria-hidden="true" />
        </div>
        <span className="dock-label">Phản ánh</span>
      </button>

      <button
        type="button"
        className={`dock-action-btn ai-highlight-btn ${activeDrawer === "ai-chat" ? "active" : ""}`}
        onClick={() => {
          toggleDrawer("ai-chat");
        }}
        title="Trò chuyện với trợ lý môi trường AI"
        aria-label="Hỏi Trợ lý AirGuard AI"
        aria-expanded={activeDrawer === "ai-chat"}
      >
        <div className="dock-icon-wrap">
          <Sparkles size={18} aria-hidden="true" />
        </div>
        <span className="dock-label">Hỏi AI</span>
      </button>

    </nav>
  );
};

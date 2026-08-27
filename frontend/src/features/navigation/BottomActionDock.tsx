import React, { useState } from "react";
import { Calendar, Layers, MapPin, Menu, MessageSquarePlus, Sparkles } from "lucide-react";
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
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const hasUtilityDrawerOpen = ["near-me", "today", "community-report"].includes(activeDrawer ?? "");

  const openUtilityDrawer = (drawer: ActiveDrawerType) => {
    setIsMoreOpen(false);
    onOpenDrawer(activeDrawer === drawer ? null : drawer);
  };

  return (
    <nav className="bottom-action-dock-bar" aria-label="Điều hướng chính ứng dụng">
      <button
        type="button"
        className={`dock-action-btn ${isLayersOpen ? "active" : ""}`}
        onClick={() => {
          setIsMoreOpen(false);
          onToggleLayers();
        }}
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

      <button
        type="button"
        className={`dock-action-btn ${hasUtilityDrawerOpen || isMoreOpen ? "active" : ""}`}
        onClick={() => setIsMoreOpen((open) => !open)}
        title="Mở thêm công cụ bản đồ"
        aria-label="Mở thêm công cụ bản đồ"
        aria-expanded={isMoreOpen}
        aria-controls="dock-more-menu"
      >
        <div className="dock-icon-wrap">
          <Menu size={18} aria-hidden="true" />
          {hasUtilityDrawerOpen && <span className="dock-active-dot" aria-hidden="true" />}
        </div>
        <span className="dock-label">Khám phá</span>
      </button>

      <button
        type="button"
        className={`dock-action-btn ai-highlight-btn ${activeDrawer === "ai-chat" ? "active" : ""}`}
        onClick={() => {
          setIsMoreOpen(false);
          onOpenDrawer(activeDrawer === "ai-chat" ? null : "ai-chat");
        }}
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

      {isMoreOpen && (
        <div id="dock-more-menu" className="dock-more-menu" role="menu" aria-label="Công cụ bổ sung">
          <button type="button" role="menuitem" onClick={() => openUtilityDrawer("near-me")}>
            <MapPin size={17} aria-hidden="true" />
            <span><strong>Gần tôi</strong><small>Chất lượng không khí quanh bạn</small></span>
          </button>
          <button type="button" role="menuitem" onClick={() => openUtilityDrawer("today")}>
            <Calendar size={17} aria-hidden="true" />
            <span><strong>Hôm nay</strong><small>Tóm tắt môi trường trong ngày</small></span>
          </button>
          <button type="button" role="menuitem" onClick={() => openUtilityDrawer("community-report")}>
            <MessageSquarePlus size={17} aria-hidden="true" />
            <span><strong>Phản ánh</strong><small>Gửi phản ánh cộng đồng</small></span>
          </button>
        </div>
      )}
    </nav>
  );
};

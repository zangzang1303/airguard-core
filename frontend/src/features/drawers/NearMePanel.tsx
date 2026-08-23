import React from "react";
import { MapPin, Sparkles, X } from "lucide-react";
import { useDraggableFloatingPanel } from "../floating";

interface NearMePanelProps {
  onClose: () => void;
  onOpenAiChat: () => void;
}

export const NearMePanel: React.FC<NearMePanelProps> = ({ onClose, onOpenAiChat }) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "near-me",
    group: "sheet",
  });

  return (
    <div {...containerProps} className="floating-bottom-sheet near-me-sheet">
      <div className="sheet-header-row">
        <div className="sheet-title-group" {...handleProps}>
          <MapPin size={18} className="sheet-pin-icon" aria-hidden="true" />
          <div style={{ minWidth: 0 }}>
            <h3 className="sheet-title">Thông tin môi trường gần bạn</h3>
            <span className="sheet-sub">Dữ liệu chỉ có tại các trạm simulator trên bản đồ</span>
          </div>
        </div>
        <button className="no-drag sheet-close-btn" data-no-drag="true" onClick={onClose} aria-label="Đóng thông tin gần bạn">
          <X size={18} />
        </button>
      </div>

      <div className="near-me-unavailable-state no-drag" data-no-drag="true">
        <MapPin size={24} aria-hidden="true" />
        <div>
          <strong>Không có phép đo trực tiếp tại vị trí người dùng</strong>
          <p>Hãy chọn một marker trạm để xem số liệu backend, hoặc hỏi Agent để nhận câu trả lời có nguồn và thời gian đo.</p>
        </div>
      </div>

      <p className="today-simulator-note no-drag" data-no-drag="true">Frontend không nội suy AQI hoặc khuyến nghị từ vị trí người dùng.</p>

      <div className="near-me-footer-actions no-drag" data-no-drag="true">
        <button className="sheet-btn primary" onClick={onOpenAiChat}>
          <Sparkles size={15} aria-hidden="true" />
          <span>Hỏi AirGuard AI</span>
        </button>
      </div>
    </div>
  );
};

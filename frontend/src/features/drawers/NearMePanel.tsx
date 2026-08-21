import React from "react";
import { MapPin, Sparkles, X } from "lucide-react";

interface NearMePanelProps {
  onClose: () => void;
  onOpenAiChat: () => void;
}

export const NearMePanel: React.FC<NearMePanelProps> = ({ onClose, onOpenAiChat }) => (
  <div className="floating-bottom-sheet near-me-sheet">
    <div className="sheet-header-row">
      <div className="sheet-title-group">
        <MapPin size={18} className="sheet-pin-icon" aria-hidden="true" />
        <div>
          <h3 className="sheet-title">Thông tin môi trường gần bạn</h3>
          <span className="sheet-sub">Dữ liệu chỉ có tại các trạm simulator trên bản đồ</span>
        </div>
      </div>
      <button className="sheet-close-btn" onClick={onClose} aria-label="Đóng thông tin gần bạn">
        <X size={18} />
      </button>
    </div>

    <div className="near-me-unavailable-state">
      <MapPin size={24} aria-hidden="true" />
      <div>
        <strong>Không có phép đo trực tiếp tại vị trí người dùng</strong>
        <p>Hãy chọn một marker trạm để xem số liệu backend, hoặc hỏi Agent để nhận câu trả lời có nguồn và thời gian đo.</p>
      </div>
    </div>

    <p className="today-simulator-note">Frontend không nội suy AQI hoặc khuyến nghị từ vị trí người dùng.</p>

    <div className="near-me-footer-actions">
      <button className="sheet-btn primary" onClick={onOpenAiChat}>
        <Sparkles size={15} aria-hidden="true" />
        <span>Hỏi AirGuard AI</span>
      </button>
    </div>
  </div>
);

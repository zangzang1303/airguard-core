import React from "react";
import { X, MapPin, CheckCircle2, AlertCircle, Clock, Sparkles, Wind, Volume2, Thermometer } from "lucide-react";

interface NearMePanelProps {
  onClose: () => void;
  onOpenForecast: () => void;
  onOpenAiChat: () => void;
}

export const NearMePanel: React.FC<NearMePanelProps> = ({
  onClose,
  onOpenForecast,
  onOpenAiChat,
}) => {
  return (
    <div className="floating-bottom-sheet near-me-sheet">
      <div className="sheet-header-row">
        <div className="sheet-title-group">
          <MapPin size={18} className="sheet-pin-icon" />
          <div>
            <h3 className="sheet-title">Chất lượng không khí tại vị trí của bạn</h3>
            <span className="sheet-sub">Cập nhật thời gian thực · Vinhomes Ocean Park 1</span>
          </div>
        </div>
        <button className="sheet-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      <div className="near-me-body-grid">
        {/* Main AQI Badge Card */}
        <div className="near-me-score-card">
          <div className="score-top-line">
            <span className="score-status-text good">Tốt (Good)</span>
            <span className="score-aqi-number">AQI 44</span>
          </div>
          <p className="score-recommendation">
            Thời điểm rất tuyệt vời cho các hoạt động thể thao, chạy bộ và dạo chơi ngoài trời.
          </p>

          <div className="mini-metrics-row">
            <div className="mini-item">
              <Wind size={14} />
              <span>PM2.5: <strong>16 µg/m³</strong></span>
            </div>
            <div className="mini-item">
              <Volume2 size={14} />
              <span>Độ ồn: <strong>51 dB</strong></span>
            </div>
            <div className="mini-item">
              <Thermometer size={14} />
              <span>Nhiệt độ: <strong>29°C</strong></span>
            </div>
          </div>
        </div>

        {/* Time recommendations */}
        <div className="near-me-timeline-advice">
          <div className="advice-block good">
            <div className="advice-label">
              <Clock size={15} />
              <span>Khung giờ vàng ngoài trời:</span>
            </div>
            <div className="advice-time">Hiện tại – 16:30</div>
          </div>

          <div className="advice-block warning">
            <div className="advice-label">
              <AlertCircle size={15} />
              <span>Nếu bạn thuộc nhóm nhạy cảm:</span>
            </div>
            <div className="advice-time">Nên hạn chế ra ngoài từ 17:30 – 19:00 (giờ tan tầm)</div>
          </div>
        </div>
      </div>

      <div className="near-me-footer-actions">
        <button className="sheet-btn secondary" onClick={onOpenForecast}>
          <Clock size={15} />
          <span>Xem dự báo chi tiết</span>
        </button>
        <button className="sheet-btn primary" onClick={onOpenAiChat}>
          <Sparkles size={15} />
          <span>Hỏi AirGuard AI</span>
        </button>
      </div>
    </div>
  );
};

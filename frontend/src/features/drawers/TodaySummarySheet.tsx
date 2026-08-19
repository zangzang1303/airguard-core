import React from "react";
import { X, Calendar, Sun, Wind, Volume2, AlertTriangle, Clock, ArrowRight } from "lucide-react";

interface TodaySummarySheetProps {
  onClose: () => void;
  onOpenForecast: () => void;
}

export const TodaySummarySheet: React.FC<TodaySummarySheetProps> = ({
  onClose,
  onOpenForecast,
}) => {
  return (
    <div className="floating-bottom-sheet today-summary-sheet">
      <div className="sheet-header-row">
        <div className="sheet-title-group">
          <Calendar size={18} className="sheet-pin-icon" />
          <div>
            <h3 className="sheet-title">Tổng quan môi trường hôm nay tại Ocean Park 1</h3>
            <span className="sheet-sub">Bản tin tổng hợp tự động · Cập nhật lúc 07:00 sáng</span>
          </div>
        </div>
        <button className="sheet-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      <div className="today-summary-grid">
        <div className="today-bullet-item">
          <span className="bullet-emoji">🌿</span>
          <div className="bullet-text">
            <strong>Chất lượng không khí nhìn chung ở mức Tốt</strong>
            <p>AQI trung bình ngày dao động từ 38 – 65 trên toàn khu đô thị.</p>
          </div>
        </div>

        <div className="today-bullet-item">
          <span className="bullet-emoji">🌡️</span>
          <div className="bullet-text">
            <strong>Nhiệt độ 29°C – 32°C</strong>
            <p>Trời nắng nhẹ, gió hồ thổi đều 2.4 m/s hướng Đông Nam, độ ẩm 68%.</p>
          </div>
        </div>

        <div className="today-bullet-item">
          <span className="bullet-emoji">🔊</span>
          <div className="bullet-text">
            <strong>Độ ồn bình thường (51 dB)</strong>
            <p>Không ghi nhận công trình thi công gây ồn đột biến quanh khu dân cư.</p>
          </div>
        </div>

        <div className="today-bullet-item warning">
          <span className="bullet-emoji">⚠️</span>
          <div className="bullet-text">
            <strong>Lưu ý: Ô nhiễm tăng nhẹ lúc 18:00</strong>
            <p>Khu vực ven đường Đa Tốn và Hồ Ngọc Trai có thể tăng PM2.5 do mật độ xe cộ giờ tan tầm.</p>
          </div>
        </div>
      </div>

      <div className="today-best-period-box">
        <div className="period-label">
          <Clock size={16} />
          <span>Khoảng thời gian lý tưởng nhất cho thể thao ngoài trời:</span>
        </div>
        <div className="period-val">06:00 – 09:00 & 20:00 – 22:30</div>
      </div>

      <div className="today-footer-row">
        <button className="sheet-btn primary full-width" onClick={onOpenForecast}>
          <span>Xem dự báo chi tiết theo từng giờ</span>
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
};

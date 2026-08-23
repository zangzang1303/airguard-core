import React, { useEffect, useRef } from "react";
import { useAuth } from "../../context/AuthContext";
import { Sparkles, KeyRound, ArrowLeft, Cpu, Users, Settings } from "lucide-react";
import "./auth.css";

export const AdminComingSoon: React.FC = () => {
  const { setCurrentScreen } = useAuth();
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    headingRef.current?.focus();
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, []);

  const handleBack = () => {
    setCurrentScreen("login");
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  };

  return (
    <main
      className="auth-layout"
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          handleBack();
        }
      }}
    >
      <div className="admin-coming-soon-container" role="region" aria-labelledby="admin-coming-soon-title">
        {/* Top Action Bar: Small Back Button & Admin Badge */}
        <div className="admin-coming-soon-top-bar">
          <button
            type="button"
            className="admin-back-top-btn"
            onClick={handleBack}
            aria-label="Quay lại màn hình chọn vai trò"
          >
            <ArrowLeft size={16} aria-hidden="true" />
            <span>Quay lại</span>
          </button>

          <div className="admin-coming-soon-badge">
            <Sparkles size={13} aria-hidden="true" />
            <span>ADMIN · SẮP RA MẮT</span>
          </div>
        </div>

        {/* Hero Icon */}
        <div className="admin-coming-soon-icon-wrap" aria-hidden="true">
          <KeyRound size={28} />
        </div>

        {/* Main Heading */}
        <h1
          id="admin-coming-soon-title"
          className="admin-coming-soon-title"
          ref={headingRef}
          tabIndex={-1}
        >
          Tính năng Quản trị viên sắp được phát triển
        </h1>

        {/* Main Description */}
        <p className="admin-coming-soon-desc">
          Chúng tôi đang hoàn thiện khu vực quản trị hệ thống, giám sát vận hành và quản lý phân quyền. Tính năng này sẽ được cung cấp trong một phiên bản tiếp theo.
        </p>

        {/* Feature Pillars Preview */}
        <div className="admin-coming-soon-pillars" aria-label="Các nhóm tính năng dự kiến">
          <div className="admin-pillar-item">
            <Cpu size={16} className="admin-pillar-item__icon" aria-hidden="true" />
            <div className="admin-pillar-item__text">
              <strong>Giám sát vận hành & Mạng trạm</strong>
              <span>Theo dõi trạng thái IoT, gateway và chu kỳ dữ liệu toàn khu đô thị.</span>
            </div>
          </div>
          <div className="admin-pillar-item">
            <Users size={16} className="admin-pillar-item__icon" aria-hidden="true" />
            <div className="admin-pillar-item__text">
              <strong>Quản lý người dùng & Phân quyền</strong>
              <span>Thiết lập quyền truy cập cho cư dân, ban quản lý và quản trị viên.</span>
            </div>
          </div>
          <div className="admin-pillar-item">
            <Settings size={16} className="admin-pillar-item__icon" aria-hidden="true" />
            <div className="admin-pillar-item__text">
              <strong>Cấu hình ngưỡng & Điều phối thiết bị</strong>
              <span>Tùy biến bộ quy tắc cảnh báo AQI và kịch bản can thiệp thông minh.</span>
            </div>
          </div>
        </div>

        {/* Supplemental Guidance Notice */}
        <div className="admin-coming-soon-notice">
          Trong thời gian chờ đợi, bạn vẫn có thể trải nghiệm vai trò <strong>Cư dân</strong> hoặc <strong>Quản lý</strong>.
        </div>

        {/* Primary Action Button */}
        <button
          type="button"
          className="admin-coming-soon-btn"
          onClick={handleBack}
          aria-label="Quay lại màn hình chọn vai trò"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          <span>Quay lại chọn vai trò</span>
        </button>
      </div>
    </main>
  );
};

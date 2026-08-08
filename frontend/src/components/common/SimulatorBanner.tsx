import React from "react";

export const SimulatorBanner: React.FC = () => {
  return (
    <div className="simulator-banner" role="banner">
      <span className="banner-pulse" aria-hidden="true"></span>
      <p>
        <strong>Dữ liệu mô phỏng:</strong> Đây là dữ liệu simulator cho MVP, không phải quan trắc chính thức và không dùng cho quyết định y tế hoặc pháp lý.
      </p>
    </div>
  );
};

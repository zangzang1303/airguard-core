import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { UserGroup } from "../../types";

export const Profile: React.FC = () => {
  const { userName, setUserName, role, setRole, userGroup, setUserGroup } = useAuth();
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h2>👤 Hồ sơ Nối mạng Người dùng (User Profile & Group Policy)</h2>
        <p className="profile-subtitle">Thiết lập nhóm đối tượng sức khỏe để Agent cá nhân hóa thông điệp cảnh báo PM2.5</p>
      </div>

      <div className="profile-card">
        {savedSuccess && (
          <div className="alert-box alert-success">
            ✅ Đã lưu cấu hình Hồ sơ người dùng thành công! Các truy vấn Agent tiếp theo sẽ áp dụng chính sách ưu tiên này.
          </div>
        )}

        <form onSubmit={handleSave} className="profile-form">
          <div className="form-group">
            <label>Họ và Tên:</label>
            <input
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              className="chat-input"
              required
            />
          </div>

          <div className="form-group">
            <label>Vai trò Hiện tại trong Hệ thống (Role):</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as any)}
              className="role-select"
            >
              <option value="resident">Resident (Cư dân)</option>
              <option value="manager">Manager (Quản lý)</option>
              <option value="admin">Admin (Hệ thống)</option>
            </select>
            <small className="form-hint">Trong hệ thống thực tế, Vai trò Manager/Admin do quản trị viên cấp quyền server-side.</small>
          </div>

          <div className="form-group">
            <label>Nhóm Đối tượng Sức khỏe / Rủi ro PM2.5 (User Group):</label>
            <div className="group-options">
              <label className={`radio-card ${userGroup === "normal" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="userGroup"
                  value="normal"
                  checked={userGroup === "normal"}
                  onChange={() => setUserGroup("normal")}
                />
                <div>
                  <strong>🟢 Normal (Thông thường)</strong>
                  <p>Cơ thể khỏe mạnh, ít nhạy cảm với sự thay đổi của nồng độ chất lượng không khí.</p>
                </div>
              </label>

              <label className={`radio-card ${userGroup === "sensitive" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="userGroup"
                  value="sensitive"
                  checked={userGroup === "sensitive"}
                  onChange={() => setUserGroup("sensitive")}
                />
                <div>
                  <strong>🟡 Sensitive (Nhạy cảm sức khỏe)</strong>
                  <p>Trẻ em, người cao tuổi, người có tiền sử hô hấp/tim mạch. Ưu tiên phát cảnh báo sớm khi PM2.5 vượt 35 µg/m³.</p>
                </div>
              </label>

              <label className={`radio-card ${userGroup === "outdoor_sport" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="userGroup"
                  value="outdoor_sport"
                  checked={userGroup === "outdoor_sport"}
                  onChange={() => setUserGroup("outdoor_sport")}
                />
                <div>
                  <strong>🏃 Outdoor Sport (Tập luyện ngoài trời)</strong>
                  <p>Thường xuyên chạy bộ, đá bóng, đạp xe ngoài trời. Khuyên thời điểm tập luyện an toàn nhất trong ngày.</p>
                </div>
              </label>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary">
              💾 Lưu Cấu hình Hồ sơ
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

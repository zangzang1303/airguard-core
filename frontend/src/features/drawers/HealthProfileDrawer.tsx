import React, { useState } from "react";
import { X, Check, LogOut, Mail, Building, ShieldCheck } from "lucide-react";
import { HealthProfile } from "../../types/superApp";
import { useAuth } from "../../context/AuthContext";

interface HealthProfileDrawerProps {
  profile: HealthProfile;
  onUpdateProfile: (updated: HealthProfile) => void;
  onClose: () => void;
}

export const HealthProfileDrawer: React.FC<HealthProfileDrawerProps> = ({
  profile,
  onUpdateProfile,
  onClose,
}) => {
  const { userName, userEmail, role, organization, logout } = useAuth();
  const [formData, setFormData] = useState<HealthProfile>(profile);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const SENSITIVITY_GROUPS: { id: HealthProfile["sensitivityGroup"]; label: string; desc: string; emoji: string }[] = [
    { id: "normal", label: "Cư dân thông thường (Normal)", desc: "Sức khỏe ổn định, không có tiền sử dị ứng thời tiết", emoji: "🏃" },
    { id: "sensitive", label: "Nhóm nhạy cảm (Sensitive)", desc: "Ưu tiên nhận cảnh báo và giải thích thận trọng hơn", emoji: "🌿" },
    { id: "respiratory", label: "Bệnh lý hô hấp (Respiratory)", desc: "Viêm xoang, hen suyễn, cần tránh ô nhiễm đột ngột", emoji: "🫁" },
    { id: "outdoor_sport", label: "Vận động viên ngoài trời (Athlete)", desc: "Thường xuyên chạy bộ, đạp xe, bơi lội trong khu", emoji: "🚴" },
    { id: "elderly", label: "Người cao tuổi (Elderly)", desc: "Cần khung giờ đi dạo dưỡng sinh an toàn, mát mẻ", emoji: "👴" },
    { id: "child", label: "Gia đình có trẻ nhỏ (Children)", desc: "Ưu tiên cảnh báo an toàn cho bé chơi công viên", emoji: "👶" },
  ];

  const ACTIVITIES = [
    { id: "running", label: "Chạy bộ (Running)" },
    { id: "walking", label: "Đi dạo ven hồ (Walking)" },
    { id: "cycling", label: "Đạp xe (Cycling)" },
    { id: "kids_park", label: "Khu vui chơi trẻ em (Kids Park)" },
    { id: "bbq", label: "Nướng BBQ dã ngoại" },
  ];

  const toggleInterest = (actId: string) => {
    const exists = formData.interests.includes(actId);
    const newInterests = exists
      ? formData.interests.filter((i) => i !== actId)
      : [...formData.interests, actId];
    setFormData({ ...formData, interests: newInterests });
  };

  const handleSave = () => {
    onUpdateProfile(formData);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 800);
  };

  const roleLabel = role === "resident" ? "Cư dân" : role === "manager" ? "Manager BQL" : "Admin";

  return (
    <aside className="contextual-drawer right-drawer health-profile-drawer">
      <div className="drawer-header-bar">
        <div className="drawer-title-group">
          <div className="badge-tag">Tài khoản & Cá nhân hóa</div>
          <h2 className="drawer-main-title">Hồ sơ người dùng</h2>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng hồ sơ">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body">
        {/* User Account Card */}
        <div className="user-account-card" style={{ padding: "14px 16px", background: "linear-gradient(135deg, #1e293b, #0f172a)", color: "#fff", borderRadius: "12px", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "42px", height: "42px", borderRadius: "50%", background: "#4f46e5", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "1.1rem" }}>
              {userName ? userName.charAt(0) : "U"}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: "1rem" }}>{userName || "Người dùng AirGuard"}</div>
              <div style={{ fontSize: "0.8rem", color: "#94a3b8", display: "flex", alignItems: "center", gap: "4px" }}>
                <Mail size={12} /> {userEmail}
              </div>
            </div>
            <span style={{ padding: "3px 8px", borderRadius: "12px", background: role === "resident" ? "#10b981" : role === "manager" ? "#f59e0b" : "#6366f1", fontSize: "0.72rem", fontWeight: 700 }}>
              {roleLabel}
            </span>
          </div>
          <div style={{ marginTop: "10px", paddingTop: "8px", borderTop: "1px solid rgba(255,255,255,0.1)", fontSize: "0.78rem", color: "#cbd5e1", display: "flex", alignItems: "center", gap: "6px" }}>
            <Building size={13} /> Organization: {organization || "Vinhomes Ocean Park 1"}
          </div>
        </div>

        {/* Grounding notice: the frontend does not calculate personal exposure. */}
        <div className="exposure-summary-card">
          <div className="exposure-header">
            <ShieldCheck size={18} className="heart-icon" />
            <span>Cá nhân hóa có kiểm chứng</span>
          </div>
          <p className="exposure-note">
            Hồ sơ này chỉ được dùng làm ngữ cảnh. Mức phơi nhiễm và khuyến nghị chỉ hiển thị khi Agent có dữ liệu môi trường cùng bằng chứng backend; giao diện không tự tính điểm an toàn.
          </p>
        </div>

        {/* Sensitivity Group Selection */}
        <div className="form-section-group">
          <label className="section-form-label">Nhóm sức khỏe của bạn:</label>
          <div className="sensitivity-options-list">
            {SENSITIVITY_GROUPS.map((grp) => (
              <div
                key={grp.id}
                className={`sensitivity-item-card ${formData.sensitivityGroup === grp.id ? "selected" : ""}`}
                onClick={() => setFormData({ ...formData, sensitivityGroup: grp.id })}
              >
                <span className="grp-emoji">{grp.emoji}</span>
                <div className="grp-text">
                  <div className="grp-title">{grp.label}</div>
                  <div className="grp-desc">{grp.desc}</div>
                </div>
                {formData.sensitivityGroup === grp.id && <Check size={16} className="grp-check" />}
              </div>
            ))}
          </div>
        </div>

        {/* Interests & Activities */}
        <div className="form-section-group">
          <label className="section-form-label">Hoạt động ngoài trời bạn quan tâm:</label>
          <div className="interests-pills-wrap">
            {ACTIVITIES.map((act) => {
              const isSelected = formData.interests.includes(act.id);
              return (
                <button
                  key={act.id}
                  type="button"
                  className={`interest-chip-btn ${isSelected ? "selected" : ""}`}
                  onClick={() => toggleInterest(act.id)}
                >
                  {act.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="form-section-group">
          <label className="section-form-label">Cài đặt thông báo môi trường:</label>
          <div className="settings-toggle-list">
            <label className="setting-toggle-row">
              <span>Nhận cảnh báo khẩn do backend phát hành</span>
              <input
                type="checkbox"
                checked={formData.alertPushEnabled}
                onChange={(e) => setFormData({ ...formData, alertPushEnabled: e.target.checked })}
              />
            </label>
            <label className="setting-toggle-row">
              <span>Bản tin tổng hợp thời tiết sáng (07:00)</span>
              <input
                type="checkbox"
                checked={formData.dailyDigestEnabled}
                onChange={(e) => setFormData({ ...formData, dailyDigestEnabled: e.target.checked })}
              />
            </label>
          </div>
        </div>
      </div>

      <div className="drawer-footer-actions" style={{ display: "flex", gap: "8px", justifyContent: "space-between" }}>
        <button
          className="action-pill-btn danger"
          onClick={() => {
            onClose();
            logout();
          }}
          style={{ background: "#ef4444", color: "#fff" }}
        >
          <LogOut size={15} />
          <span>Đăng xuất</span>
        </button>
        <div style={{ display: "flex", gap: "8px" }}>
          <button className="action-pill-btn secondary" onClick={onClose}>
            Hủy
          </button>
          <button className="action-pill-btn primary" onClick={handleSave}>
            {savedSuccess ? "Đã lưu!" : "Lưu hồ sơ"}
          </button>
        </div>
      </div>
    </aside>
  );
};


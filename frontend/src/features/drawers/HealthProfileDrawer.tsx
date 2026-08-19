import React, { useState } from "react";
import { X, User, Heart, Shield, Check, Activity, Bell, Compass } from "lucide-react";
import { HealthProfile } from "../../types/superApp";

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
  const [formData, setFormData] = useState<HealthProfile>(profile);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const SENSITIVITY_GROUPS: { id: HealthProfile["sensitivityGroup"]; label: string; desc: string; emoji: string }[] = [
    { id: "normal", label: "Cư dân thông thường (Normal)", desc: "Sức khỏe ổn định, không có tiền sử dị ứng thời tiết", emoji: "🏃" },
    { id: "sensitive", label: "Nhóm nhạy cảm (Sensitive)", desc: "Dễ bị kích ứng đường thở khi bụi mịn vượt ngưỡng 100", emoji: "🌿" },
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

  return (
    <aside className="contextual-drawer right-drawer health-profile-drawer">
      <div className="drawer-header-bar">
        <div className="drawer-title-group">
          <div className="badge-tag">Cá nhân hóa trải nghiệm</div>
          <h2 className="drawer-main-title">Hồ sơ sức khỏe & Thói quen</h2>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body">
        {/* Personal Exposure Status Card */}
        <div className="exposure-summary-card">
          <div className="exposure-header">
            <Heart size={18} className="heart-icon" />
            <span>Mức độ phơi nhiễm cá nhân hôm nay:</span>
          </div>
          <div className="exposure-val-row">
            <span className="exposure-tag-pill low">THẤP (LOW EXPOSURE)</span>
            <span className="exposure-score">An toàn 96%</span>
          </div>
          <p className="exposure-note">
            AI tự động điều chỉnh lời khuyên theo hồ sơ <strong>{SENSITIVITY_GROUPS.find((g) => g.id === formData.sensitivityGroup)?.label}</strong>.
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
              <span>Nhận cảnh báo khẩn khi AQI &gt; 150</span>
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

      <div className="drawer-footer-actions">
        <button className="action-pill-btn secondary" onClick={onClose}>
          Hủy
        </button>
        <button className="action-pill-btn primary" onClick={handleSave}>
          {savedSuccess ? "Đã lưu thành công!" : "Lưu hồ sơ sức khỏe"}
        </button>
      </div>
    </aside>
  );
};

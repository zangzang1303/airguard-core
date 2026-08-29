import React, { useEffect, useState } from "react";
import { Activity, Bell, CheckCircle2, HeartPulse, Mail, Save, UserRound } from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { NotificationPreferences, UserGroup } from "../../types";

const groupOptions: Array<{ value: UserGroup; title: string; description: string; icon: typeof UserRound }> = [
  { value: "normal", title: "Bình thường", description: "Không có nhu cầu cảnh báo ưu tiên.", icon: UserRound },
  { value: "sensitive", title: "Nhạy cảm", description: "Ưu tiên cách trình bày thận trọng hơn.", icon: HeartPulse },
  { value: "outdoor_sport", title: "Hoạt động ngoài trời", description: "Quan tâm thời điểm vận động phù hợp.", icon: Activity },
];

export const Profile: React.FC = () => {
  const { userName, userEmail, organization, role, userGroup, updateProfile } = useAuth();
  const [formName, setFormName] = useState(userName);
  const [formGroup, setFormGroup] = useState<UserGroup>(userGroup);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [notificationPreferences, setNotificationPreferences] = useState<NotificationPreferences>({
    environmental_email_enabled: false,
    predictive_email_enabled: false,
  });
  const [notificationLoading, setNotificationLoading] = useState(true);
  const [notificationSaving, setNotificationSaving] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState<string | null>(null);
  const [notificationError, setNotificationError] = useState<string | null>(null);

  useEffect(() => {
    setFormName(userName);
    setFormGroup(userGroup);
  }, [userGroup, userName]);

  useEffect(() => {
    let active = true;
    api.getNotificationPreferences()
      .then((preferences) => {
        if (active) setNotificationPreferences(preferences);
      })
      .catch(() => {
        if (active) setNotificationError("Không thể tải tùy chọn email.");
      })
      .finally(() => {
        if (active) setNotificationLoading(false);
      });
    return () => { active = false; };
  }, []);

  const saveNotificationPreferences = async () => {
    setNotificationSaving(true);
    setNotificationError(null);
    setNotificationMessage(null);
    try {
      const savedPreferences = await api.updateNotificationPreferences(notificationPreferences);
      setNotificationPreferences(savedPreferences);
      setNotificationMessage("Đã lưu lựa chọn email. Hai loại email được bật/tắt độc lập.");
    } catch {
      setNotificationError("Không thể lưu tùy chọn email. Vui lòng thử lại.");
    } finally {
      setNotificationSaving(false);
    }
  };

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaveError(null);
    setSaving(true);
    const result = await updateProfile({ fullName: formName.trim(), userGroup: formGroup });
    setSaving(false);
    if (!result.success) {
      setSaveError(result.message || "Không thể lưu hồ sơ.");
      return;
    }
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  };

  const resetForm = () => {
    setFormName(userName);
    setFormGroup(userGroup);
  };

  const roleLabel = role === "resident" ? "Cư dân" : role === "manager" ? "Manager" : "Admin";

  return (
    <div className="profile-container">
      <PageHeader
        title="Hồ sơ người dùng"
        description="Quản lý thông tin hiển thị và nhóm người dùng áp dụng cho trải nghiệm AirGuard AI."
      />

      {saved && (
        <div className="alert-box alert-success" role="status">
          <CheckCircle2 size={18} aria-hidden="true" />
          Đã lưu thay đổi hồ sơ.
        </div>
      )}
      {saveError && <div className="alert-box alert-error" role="alert">{saveError}</div>}

      <form className="profile-layout" onSubmit={handleSave}>
        <section className="profile-card profile-account-card">
          <div className="profile-section-heading">
            <div className="profile-avatar" aria-hidden="true">
              {formName.trim().charAt(0).toUpperCase() || "U"}
            </div>
            <div>
              <span className="dashboard-eyebrow">Thông tin tài khoản</span>
              <h2>{formName || "Người dùng AirGuard"}</h2>
              <p>Identity và vai trò được cấp bởi hệ thống.</p>
            </div>
          </div>

          <div className="profile-form">
            <label className="form-group">
              <span>Họ và tên</span>
              <input value={formName} onChange={(event) => setFormName(event.target.value)} required />
            </label>

            {/* Ba ô dưới đây chỉ hiển thị, không có control — dùng <div> + aria-labelledby thay cho <label>. */}
            <div className="profile-identity-grid">
              <div className="form-group">
                <span id="profile-email-label">Email</span>
                <p className="readonly-field" aria-labelledby="profile-email-label">{userEmail}</p>
              </div>
              <div className="form-group">
                <span id="profile-role-label">Vai trò</span>
                <p
                  className={`readonly-field role-readonly role-readonly--${role}`}
                  aria-labelledby="profile-role-label"
                >
                  {roleLabel}
                </p>
              </div>
              <div className="form-group">
                <span id="profile-org-label">Đơn vị</span>
                <p className="readonly-field" aria-labelledby="profile-org-label">{organization}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="profile-card">
          <div className="profile-section-heading profile-section-heading--compact">
            <div>
              <span className="dashboard-eyebrow">Cá nhân hóa</span>
              <h2>Nhóm người dùng</h2>
              <p>Chỉ dùng để lựa chọn policy và cách trình bày; không thu thập chẩn đoán chi tiết.</p>
            </div>
          </div>

          <fieldset className="group-options">
            <legend className="sr-only">Nhóm người dùng</legend>
            {groupOptions.map((option) => {
              const Icon = option.icon;
              return (
                <label key={option.value} className={`radio-card ${formGroup === option.value ? "active" : ""}`}>
                  <input
                    type="radio"
                    name="userGroup"
                    checked={formGroup === option.value}
                    onChange={() => setFormGroup(option.value)}
                  />
                  <div>
                    <strong><Icon size={17} aria-hidden="true" />{option.title}</strong>
                    <p>{option.description}</p>
                  </div>
                </label>
              );
            })}
          </fieldset>
        </section>

        <section className="profile-card profile-notification-card">
          <div className="profile-section-heading profile-section-heading--compact">
            <Bell size={22} aria-hidden="true" />
            <div>
              <span className="dashboard-eyebrow">Tùy chọn email</span>
              <h2>Thông báo môi trường</h2>
              <p>Mặc định tắt. Bạn phải chủ động bật từng loại email và có thể tắt lại bất cứ lúc nào.</p>
            </div>
          </div>

          <div className="profile-disabled-options">
            <label>
              <span><Mail size={16} aria-hidden="true" /> Email cảnh báo đang xảy ra</span>
              <input
                type="checkbox"
                checked={notificationPreferences.environmental_email_enabled}
                disabled={notificationLoading || notificationSaving}
                onChange={(event) => setNotificationPreferences((current) => ({
                  ...current,
                  environmental_email_enabled: event.target.checked,
                }))}
              />
            </label>
            <label>
              <span><Mail size={16} aria-hidden="true" /> Email cảnh báo dự báo 1–2 giờ</span>
              <input
                type="checkbox"
                checked={notificationPreferences.predictive_email_enabled}
                disabled={notificationLoading || notificationSaving}
                onChange={(event) => setNotificationPreferences((current) => ({
                  ...current,
                  predictive_email_enabled: event.target.checked,
                }))}
              />
            </label>
          </div>
          {notificationError && <div className="alert-box alert-error" role="alert">{notificationError}</div>}
          {notificationMessage && <div className="alert-box alert-success" role="status">{notificationMessage}</div>}
          <Button
            type="button"
            variant="outline"
            onClick={saveNotificationPreferences}
            disabled={notificationLoading || notificationSaving}
          >
            {notificationSaving ? "Đang lưu" : "Lưu tùy chọn email"}
          </Button>
        </section>

        <div className="profile-actions">
          <Button type="button" variant="outline" onClick={resetForm}>Hủy thay đổi</Button>
          <Button type="submit" variant="primary" disabled={!formName.trim() || saving}>
            <Save size={17} aria-hidden="true" />
            Lưu thay đổi
          </Button>
        </div>
      </form>
    </div>
  );
};

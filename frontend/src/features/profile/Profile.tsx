import React, { useEffect, useState } from "react";
import { Activity, BellOff, CheckCircle2, HeartPulse, Save, UserRound } from "lucide-react";
import { Button } from "../../components/common/Button";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { UserGroup } from "../../types";

const groupOptions: Array<{ value: UserGroup; title: string; description: string; icon: typeof UserRound }> = [
  { value: "normal", title: "Bình thường", description: "Không có nhu cầu cảnh báo ưu tiên.", icon: UserRound },
  { value: "sensitive", title: "Nhạy cảm", description: "Ưu tiên cách trình bày thận trọng hơn.", icon: HeartPulse },
  { value: "outdoor_sport", title: "Hoạt động ngoài trời", description: "Quan tâm thời điểm vận động phù hợp.", icon: Activity },
];

export const Profile: React.FC = () => {
  const { userName, setUserName, userEmail, organization, role, userGroup, setUserGroup } = useAuth();
  const [formName, setFormName] = useState(userName);
  const [formGroup, setFormGroup] = useState<UserGroup>(userGroup);
  const [saved, setSaved] = useState(false);
  useEffect(() => { setFormName(userName); setFormGroup(userGroup); }, [userGroup, userName]);

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();
    setUserName(formName.trim());
    setUserGroup(formGroup);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  };
  const resetForm = () => { setFormName(userName); setFormGroup(userGroup); };
  const roleLabel = role === "resident" ? "Cư dân" : role === "manager" ? "Manager" : "Admin";

  return <div className="profile-container">
    <PageHeader title="Hồ sơ người dùng" description="Quản lý thông tin hiển thị và nhóm người dùng áp dụng cho trải nghiệm AirGuard AI." />
    {saved && <div className="alert-box alert-success" role="status"><CheckCircle2 size={18} />Đã lưu thay đổi hồ sơ.</div>}
    <form className="profile-layout" onSubmit={handleSave}>
      <section className="profile-card profile-account-card">
        <div className="profile-section-heading"><div className="profile-avatar">{formName.trim().charAt(0).toUpperCase() || "U"}</div><div><span className="dashboard-eyebrow">Thông tin tài khoản</span><h2>{formName || "Người dùng AirGuard"}</h2><p>Identity và vai trò được cấp bởi hệ thống.</p></div></div>
        <div className="profile-form">
          <label className="form-group"><span>Họ và tên</span><input value={formName} onChange={(event) => setFormName(event.target.value)} required /></label>
          <div className="profile-identity-grid"><label className="form-group"><span>Email</span><div className="readonly-field" aria-readonly="true">{userEmail}</div></label><label className="form-group"><span>Vai trò</span><div className={`readonly-field role-readonly role-readonly--${role}`} aria-readonly="true">{roleLabel}</div></label><label className="form-group"><span>Đơn vị</span><div className="readonly-field" aria-readonly="true">{organization}</div></label></div>
        </div>
      </section>

      <section className="profile-card">
        <div className="profile-section-heading profile-section-heading--compact"><div><span className="dashboard-eyebrow">Cá nhân hóa</span><h2>Nhóm người dùng</h2><p>Chỉ dùng để lựa chọn policy và cách trình bày; không thu thập chẩn đoán chi tiết.</p></div></div>
        <fieldset className="group-options"><legend className="sr-only">Nhóm người dùng</legend>{groupOptions.map((option) => { const Icon = option.icon; return <label key={option.value} className={`radio-card ${formGroup === option.value ? "active" : ""}`}><input type="radio" name="userGroup" checked={formGroup === option.value} onChange={() => setFormGroup(option.value)} /><div><strong><Icon size={17} />{option.title}</strong><p>{option.description}</p></div></label>; })}</fieldset>
      </section>

      <section className="profile-card profile-notification-card"><div className="profile-section-heading profile-section-heading--compact"><BellOff size={22} /><div><span className="dashboard-eyebrow">Tùy chọn thông báo · P2</span><h2>Chưa cấu hình trong MVP</h2><p>Push Notification và email hàng ngày sẽ được bật sau khi có contract phía backend.</p></div></div><div className="profile-disabled-options"><label><span>Push Notification</span><input type="checkbox" disabled /></label><label><span>Email hàng ngày</span><input type="checkbox" disabled /></label></div></section>

      <div className="profile-actions"><Button type="button" variant="outline" onClick={resetForm}>Hủy thay đổi</Button><Button type="submit" variant="primary" disabled={!formName.trim()}><Save size={17} />Lưu thay đổi</Button></div>
    </form>
  </div>;
};

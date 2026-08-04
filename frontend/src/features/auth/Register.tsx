import React, { useState } from "react";
import { Activity, ArrowLeft, ArrowRight, Check, Eye, EyeOff, HeartPulse, KeyRound, LockKeyhole, Mail, UserRound } from "lucide-react";
import { Button } from "../../components/common/Button";
import { RegisterResidentInput, useAuth } from "../../context/AuthContext";
import { UserGroup } from "../../types";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

const groups: Array<{ value: UserGroup; label: string; description: string; icon: typeof UserRound }> = [
  { value: "normal", label: "Bình thường", description: "Không có nhu cầu cảnh báo ưu tiên.", icon: UserRound },
  { value: "sensitive", label: "Nhạy cảm", description: "Ưu tiên thông tin thận trọng hơn.", icon: HeartPulse },
  { value: "outdoor_sport", label: "Hoạt động ngoài trời", description: "Quan tâm thời điểm vận động phù hợp.", icon: Activity },
];

export const Register: React.FC = () => {
  const { navigateTo, registerResident } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [userGroup, setUserGroup] = useState<UserGroup>("normal");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!name.trim() || !email.trim() || !password || !confirmPassword) {
      setError("Vui lòng hoàn thành tất cả trường bắt buộc.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setError("Email chưa đúng định dạng.");
      return;
    }
    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(password)) {
      setError("Mật khẩu cần ít nhất 8 ký tự, gồm chữ hoa, chữ thường và số.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận chưa khớp.");
      return;
    }
    if (!termsAccepted) {
      setError("Bạn cần đồng ý với Điều khoản sử dụng và Chính sách dữ liệu.");
      return;
    }

    const input: RegisterResidentInput = { name, email, password, userGroup };
    const result = registerResident(input);
    if (!result.success) setError(result.message ?? "Không thể tạo tài khoản.");
  };

  return (
    <AuthLayout
      title="Tham gia mạng lưới quan sát không khí cộng đồng."
      description="Tạo hồ sơ Cư dân để nhận trải nghiệm phù hợp với nhu cầu sử dụng, không thu thập chẩn đoán y tế chi tiết."
    >
      <div className="auth-card auth-card--register">
        <Button variant="ghost" size="sm" className="auth-back" onClick={() => navigateTo("login")}>
          <ArrowLeft size={16} aria-hidden="true" /> Quay lại đăng nhập
        </Button>
        <div className="auth-card__heading">
          <span className="auth-card__kicker">Resident Registration · Demo</span>
          <h2>Đăng ký tài khoản Cư dân</h2>
          <p>Tài khoản mới luôn được cấp vai trò Cư dân. Manager/Admin do quản trị viên cấp.</p>
        </div>

        <div className="resident-role-lock"><LockKeyhole size={18} aria-hidden="true" /><span><strong>Vai trò: Cư dân</strong><small>Cố định và không thể tự nâng quyền</small></span></div>
        {error && <div className="auth-notice auth-notice--error" role="alert">{error}</div>}

        <form className="auth-form auth-form--register" onSubmit={handleSubmit} noValidate>
          <div className="auth-form-grid">
            <div className="auth-field">
              <label htmlFor="register-name">Họ và tên</label>
              <div className="auth-input-wrap"><UserRound size={18} aria-hidden="true" /><input id="register-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Nguyễn Văn A" autoComplete="name" /></div>
            </div>
            <div className="auth-field">
              <label htmlFor="register-email">Email</label>
              <div className="auth-input-wrap"><Mail size={18} aria-hidden="true" /><input id="register-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@vinuni.edu.vn" autoComplete="email" /></div>
            </div>
            <div className="auth-field">
              <label htmlFor="register-password">Mật khẩu</label>
              <div className="auth-input-wrap"><KeyRound size={18} aria-hidden="true" /><input id="register-password" type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Tối thiểu 8 ký tự" autoComplete="new-password" /><button type="button" className="auth-password-toggle" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>
            </div>
            <div className="auth-field">
              <label htmlFor="register-confirm">Xác nhận mật khẩu</label>
              <div className="auth-input-wrap"><Check size={18} aria-hidden="true" /><input id="register-confirm" type={showPassword ? "text" : "password"} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Nhập lại mật khẩu" autoComplete="new-password" /></div>
            </div>
          </div>

          <fieldset className="auth-groups">
            <legend>Nhóm người dùng</legend>
            <p>Thông tin này chỉ phục vụ lựa chọn policy và cách trình bày khuyến nghị.</p>
            <div className="auth-group-grid">
              {groups.map((group) => {
                const Icon = group.icon;
                return (
                  <label key={group.value} className={`auth-group-option ${userGroup === group.value ? "is-selected" : ""}`}>
                    <input type="radio" name="user-group" value={group.value} checked={userGroup === group.value} onChange={() => setUserGroup(group.value)} />
                    <Icon size={19} aria-hidden="true" />
                    <span><strong>{group.label}</strong><small>{group.description}</small></span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <label className="auth-terms">
            <input type="checkbox" checked={termsAccepted} onChange={(event) => setTermsAccepted(event.target.checked)} />
            <span>Tôi đồng ý với <button type="button">Điều khoản sử dụng</button> và <button type="button">Chính sách dữ liệu</button> của AirGuard AI.</span>
          </label>

          <Button type="submit" variant="primary" className="auth-submit">Tạo tài khoản Cư dân <ArrowRight size={17} aria-hidden="true" /></Button>
        </form>
        <p className="auth-switch">Đã có tài khoản? <button type="button" onClick={() => navigateTo("login")}>Đăng nhập</button></p>
        <p className="auth-contract-note">Auth provider production đang chờ xác nhận. Tài khoản tạo tại đây chỉ tồn tại trong phiên demo hiện tại.</p>
      </div>
    </AuthLayout>
  );
};


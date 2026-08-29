import React, { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  KeyRound,
  Mail,
  ShieldCheck,
  UserRound,
  HeartPulse,
} from "lucide-react";
import { Button } from "../../components/common/Button";
import { RegisterResidentInput, useAuth } from "../../context/AuthContext";
import { UserGroup } from "../../types";
import { AuthShell } from "./AuthShell";
import "./auth.css";

export const Register: React.FC = () => {
  const { navigateTo, registerResident } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [userGroup, setUserGroup] = useState<UserGroup>("normal");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = termsAccepted && !submitting;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!termsAccepted) {
      setError("Bạn cần đồng ý với Điều khoản sử dụng.");
      return;
    }
    if (!name.trim() || !email.trim() || !password || !confirmPassword) {
      setError("Vui lòng hoàn thành tất cả các trường bắt buộc.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setError("Email chưa đúng định dạng.");
      return;
    }
    if (password.length < 8) {
      setError("Mật khẩu cần có ít nhất 8 ký tự.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Mật khẩu xác nhận chưa khớp.");
      return;
    }

    setSubmitting(true);
    try {
      const input: RegisterResidentInput = {
        name: name.trim(),
        email: email.trim(),
        password,
        userGroup,
      };
      const result = await registerResident(input);
      if (!result.success) {
        setError(result.message ?? "Không thể tạo tài khoản.");
      } else {
        // Navigate directly to verify-email so the user sees the confirmation/verification step
        navigateTo("verify-email");
      }
    } catch (err: any) {
      setError(err?.message ?? "Lỗi kết nối máy chủ.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell className="auth-unified-container--register">
      <section className="auth-column-main auth-column-main--register">
        <div className="auth-registration-content">
          <Button
            variant="ghost"
            size="sm"
            className="auth-link-btn auth-back-btn"
            onClick={() => navigateTo("login")}
            disabled={submitting}
          >
            <ArrowLeft size={16} aria-hidden="true" /> Quay lại
          </Button>

          <div className="auth-brand-compact">
            <div className="auth-brand-icon">
              <ShieldCheck size={22} strokeWidth={2.2} />
            </div>
            <div className="auth-brand-text">
              <h2>Đăng ký tài khoản</h2>
              <p>Tạo tài khoản cư dân để theo dõi chất lượng không khí.</p>
            </div>
          </div>

          {error && <div className="auth-notice auth-notice--error" role="alert" aria-live="assertive">{error}</div>}

          <form className="auth-form auth-form--register" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="register-name">Họ và tên</label>
            <div className="auth-input-wrap">
              <UserRound size={18} aria-hidden="true" />
              <input
                id="register-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Nguyễn Văn A"
                autoComplete="name"
                disabled={submitting}
                required
              />
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="register-email">Địa chỉ Email</label>
            <div className="auth-input-wrap">
              <Mail size={18} aria-hidden="true" />
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="email@vinuni.edu.vn"
                autoComplete="email"
                disabled={submitting}
                required
              />
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="register-group">Nhóm nhạy cảm / Sức khỏe</label>
            <div className="auth-input-wrap">
              <HeartPulse size={18} aria-hidden="true" />
              <select
                id="register-group"
                className="auth-select"
                value={userGroup}
                onChange={(e) => setUserGroup(e.target.value as UserGroup)}
                disabled={submitting}
              >
                <option value="normal">Bình thường (Cư dân chung)</option>
                <option value="sensitive">Nhạy cảm (Người già, trẻ nhỏ, hô hấp)</option>
                <option value="outdoor_sport">Thể thao ngoài trời thường xuyên</option>
              </select>
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="register-password">Mật khẩu</label>
            <div className="auth-input-wrap">
              <KeyRound size={18} aria-hidden="true" />
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Tối thiểu 8 ký tự"
                autoComplete="new-password"
                disabled={submitting}
                required
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                disabled={submitting}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="register-confirm">Xác nhận mật khẩu</label>
            <div className="auth-input-wrap">
              <Check size={18} aria-hidden="true" />
              <input
                id="register-confirm"
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Nhập lại mật khẩu"
                autoComplete="new-password"
                disabled={submitting}
                required
              />
            </div>
          </div>

          <label className="auth-terms" htmlFor="register-terms">
            <input
              id="register-terms"
              type="checkbox"
              checked={termsAccepted}
              onChange={(event) => setTermsAccepted(event.target.checked)}
              disabled={submitting}
            />
            <span>Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật dữ liệu.</span>
          </label>

          <Button
            type="submit"
            variant="primary"
            className="auth-submit"
            disabled={!canSubmit}
            aria-busy={submitting}
          >
            {submitting ? "Đang tạo tài khoản..." : "Tạo tài khoản"}
            {!submitting && <ArrowRight size={17} aria-hidden="true" />}
          </Button>
        </form>

          <p className="auth-switch">
            Đã có tài khoản?{" "}
            <button type="button" onClick={() => navigateTo("login")} disabled={submitting}>
              Đăng nhập
            </button>
          </p>
        </div>
      </section>

    </AuthShell>
  );
};


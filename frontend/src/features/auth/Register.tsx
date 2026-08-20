import React, { useState } from "react";
import { ArrowLeft, ArrowRight, Check, Eye, EyeOff, KeyRound, Mail, ShieldCheck, UserRound } from "lucide-react";
import { Button } from "../../components/common/Button";
import { RegisterResidentInput, useAuth } from "../../context/AuthContext";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

export const Register: React.FC = () => {
  const { navigateTo, registerResident } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
      setError("Bạn cần đồng ý với Điều khoản sử dụng.");
      return;
    }

    const input: RegisterResidentInput = { name, email, password, userGroup: "normal" };
    const result = registerResident(input);
    if (!result.success) setError(result.message ?? "Không thể tạo tài khoản.");
  };

  return (
    <AuthLayout>
      <div className="auth-card auth-card--register-main">
        {/* HEADER TOOLBAR: BACK BUTTON ON LEFT, LOGO ON RIGHT */}
        <div className="register-header-toolbar">
          <Button variant="ghost" size="sm" className="auth-back" onClick={() => navigateTo("login")}>
            <ArrowLeft size={16} aria-hidden="true" /> Quay lại
          </Button>

          <div className="auth-card__brand">
            <div className="auth-brand-logo">
              <ShieldCheck size={22} strokeWidth={2.2} />
            </div>
            <h1 className="auth-brand-title">AirGuard AI</h1>
          </div>
        </div>


        <div className="auth-card__heading">
          <h2>Đăng ký</h2>
        </div>


        {error && <div className="auth-notice auth-notice--error" role="alert">{error}</div>}

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
              />
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="register-email">Email</label>
            <div className="auth-input-wrap">
              <Mail size={18} aria-hidden="true" />
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="email@vinuni.edu.vn"
                autoComplete="email"
              />
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
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
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
              />
            </div>
          </div>

          <label className="auth-terms">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(event) => setTermsAccepted(event.target.checked)}
            />
            <span>Tôi đồng ý với <button type="button">Điều khoản sử dụng</button></span>
          </label>

          <Button type="submit" variant="primary" className="auth-submit">
            Tạo tài khoản <ArrowRight size={17} aria-hidden="true" />
          </Button>
        </form>

        <p className="auth-switch">
          Đã có tài khoản?{" "}
          <button type="button" onClick={() => navigateTo("login")}>
            Đăng nhập
          </button>
        </p>
      </div>
    </AuthLayout>
  );
};




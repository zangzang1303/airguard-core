import React, { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Eye, EyeOff, KeyRound, LockKeyhole, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { useAuth } from "../../context/AuthContext";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

export const ResetPassword: React.FC = () => {
  const { navigateTo, resetPassword, setAuthMessage } = useAuth();
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const urlToken = urlParams.get("token");
      if (urlToken) {
        setToken(urlToken);
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!token.trim()) {
      setError("Vui lòng cung cấp mã xác nhận đặt lại mật khẩu.");
      return;
    }
    if (!newPassword || newPassword.length < 8) {
      setError("Mật khẩu mới phải có ít nhất 8 ký tự.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Mật khẩu xác nhận chưa trùng khớp.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await resetPassword(token.trim(), newPassword);
      if (res.success) {
        setSuccessMsg(res.message || "Đặt lại mật khẩu thành công!");
        setAuthMessage("Mật khẩu đã được thay đổi. Vui lòng đăng nhập bằng mật khẩu mới.");
        setTimeout(() => {
          navigateTo("login");
        }, 2000);
      } else {
        setError(res.message || "Không thể đặt lại mật khẩu.");
      }
    } catch (err: any) {
      setError(err?.message || "Lỗi đặt lại mật khẩu.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <div className="auth-card auth-card--login-main" style={{ maxWidth: "480px" }}>
        <div className="register-header-toolbar">
          <Button variant="ghost" size="sm" className="auth-back" onClick={() => navigateTo("login")}>
            <ArrowLeft size={16} aria-hidden="true" /> Đăng nhập
          </Button>

          <div className="auth-card__brand">
            <div className="auth-brand-logo">
              <ShieldCheck size={22} strokeWidth={2.2} />
            </div>
            <h1 className="auth-brand-title">AirGuard AI</h1>
          </div>
        </div>

        <div className="auth-card__heading">
          <h2>Đặt lại mật khẩu</h2>
          <p className="auth-card__subtitle">
            Thiết lập mật khẩu mới an toàn cho tài khoản của bạn
          </p>
        </div>

        {successMsg && (
          <div className="auth-notice auth-notice--success" role="status">
            <CheckCircle2 size={18} style={{ marginRight: "6px", verticalAlign: "middle" }} />
            {successMsg}
          </div>
        )}
        {error && (
          <div className="auth-notice auth-notice--error" role="alert">
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="reset-token">Mã đặt lại mật khẩu (Token)</label>
            <div className="auth-input-wrap">
              <LockKeyhole size={18} aria-hidden="true" />
              <input
                id="reset-token"
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Dán mã bảo mật từ email"
                required
              />
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="new-password">Mật khẩu mới</label>
            <div className="auth-input-wrap">
              <KeyRound size={18} aria-hidden="true" />
              <input
                id="new-password"
                type={showPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Tối thiểu 8 ký tự"
                required
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="auth-field">
            <label htmlFor="confirm-new-password">Xác nhận mật khẩu mới</label>
            <div className="auth-input-wrap">
              <KeyRound size={18} aria-hidden="true" />
              <input
                id="confirm-new-password"
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Nhập lại mật khẩu mới"
                required
              />
            </div>
          </div>

          <Button type="submit" variant="primary" className="auth-submit" disabled={submitting}>
            {submitting ? "Đang lưu mật khẩu..." : "Cập nhật mật khẩu"}
          </Button>
        </form>
      </div>
    </AuthLayout>
  );
};

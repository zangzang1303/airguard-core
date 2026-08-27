import React, { useState } from "react";
import { AlertTriangle, ArrowLeft, CheckCircle2, Mail, Send, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { useAuth } from "../../context/AuthContext";
import { EmailDeliveryStatus } from "../../types";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

export const ForgotPassword: React.FC = () => {
  const { navigateTo, forgotPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [emailDeliveryStatus, setEmailDeliveryStatus] = useState<EmailDeliveryStatus | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setEmailDeliveryStatus(null);
    if (!email.trim() || !/^\S+@\S+\.\S+$/.test(email.trim())) {
      setError("Vui lòng nhập địa chỉ email hợp lệ.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await forgotPassword(email.trim());
      setSuccessMsg(
        res.message ||
          "Nếu địa chỉ email tồn tại, yêu cầu đặt lại mật khẩu đã được tiếp nhận."
      );
      setEmailDeliveryStatus(res.emailDeliveryStatus ?? "unknown");
    } catch (err: any) {
      setError(err?.message || "Không thể thực hiện yêu cầu.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <div className="auth-card auth-card--login-main" style={{ maxWidth: "480px" }}>
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
          <h2>Quên mật khẩu</h2>
          <p className="auth-card__subtitle">
            Nhập email tài khoản để nhận liên kết thiết lập lại mật khẩu
          </p>
        </div>

        {successMsg && (
          <div className="auth-notice auth-notice--success" role="status">
            <CheckCircle2 size={18} style={{ marginRight: "6px", verticalAlign: "middle" }} />
            {successMsg}
          </div>
        )}
        {emailDeliveryStatus && emailDeliveryStatus !== "accepted" && (
          <div className="auth-notice auth-notice--warning" role="alert">
            <AlertTriangle size={15} style={{ marginRight: "6px", verticalAlign: "middle", flexShrink: 0 }} />
            {emailDeliveryStatus === "not_configured"
              ? "Dịch vụ email hiện chưa được cấu hình. Vui lòng liên hệ quản trị viên."
              : "Chưa thể gửi email. Vui lòng thử lại sau vài phút."}
          </div>
        )}
        {error && (
          <div className="auth-notice auth-notice--error" role="alert">
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="forgot-email">Địa chỉ Email</label>
            <div className="auth-input-wrap">
              <Mail size={18} aria-hidden="true" />
              <input
                id="forgot-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="resident@vinuni.edu.vn"
                required
              />
            </div>
          </div>

          <Button type="submit" variant="primary" className="auth-submit" disabled={submitting}>
            <Send size={16} style={{ marginRight: "6px" }} />
            {submitting ? "Đang gửi yêu cầu..." : "Gửi liên kết đặt lại mật khẩu"}
          </Button>
        </form>

        <p className="auth-switch" style={{ marginTop: "1.5rem" }}>
          Nhớ mật khẩu?{" "}
          <button type="button" onClick={() => navigateTo("login")}>
            Đăng nhập ngay
          </button>
        </p>
      </div>
    </AuthLayout>
  );
};

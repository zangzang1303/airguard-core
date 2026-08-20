import React, { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Mail, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "../../components/common/Button";
import { useAuth } from "../../context/AuthContext";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

export const VerifyEmail: React.FC = () => {
  const { navigateTo, verifyEmail, resendVerification, setAuthMessage } = useAuth();
  const [token, setToken] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Auto-verify if token is in URL query parameters
  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const urlToken = urlParams.get("token");
      if (urlToken && urlToken.length >= 16) {
        setToken(urlToken);
        handleVerify(urlToken);
      }
    }
  }, []);

  const handleVerify = async (tokenToUse: string) => {
    setError(null);
    setSuccessMsg(null);
    if (!tokenToUse.trim()) {
      setError("Vui lòng nhập mã xác minh.");
      return;
    }
    setVerifying(true);
    try {
      const res = await verifyEmail(tokenToUse.trim());
      if (res.success) {
        setSuccessMsg(res.message || "Xác minh email thành công!");
        setAuthMessage("Tài khoản của bạn đã được kích hoạt thành công. Vui lòng đăng nhập.");
        setTimeout(() => {
          navigateTo("login");
        }, 2000);
      } else {
        setError(res.message || "Mã xác minh không hợp lệ hoặc đã hết hạn.");
      }
    } catch (err: any) {
      setError(err?.message || "Lỗi xác minh email.");
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    if (!resendEmail.trim() || !/^\S+@\S+\.\S+$/.test(resendEmail.trim())) {
      setError("Vui lòng nhập địa chỉ email hợp lệ.");
      return;
    }
    setResending(true);
    try {
      const res = await resendVerification(resendEmail.trim());
      setSuccessMsg(res.message || "Liên kết xác minh mới đã được gửi nếu email tồn tại.");
    } catch (err: any) {
      setError(err?.message || "Không thể gửi lại mã xác minh.");
    } finally {
      setResending(false);
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
          <h2>Xác minh địa chỉ Email</h2>
          <p className="auth-card__subtitle">
            Kích hoạt tài khoản để truy cập hệ thống cảnh báo và quan sát môi trường
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

        <form
          className="auth-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleVerify(token);
          }}
          noValidate
        >
          <div className="auth-field">
            <label htmlFor="verify-token">Mã xác minh (Token)</label>
            <div className="auth-input-wrap">
              <input
                id="verify-token"
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Dán mã kích hoạt từ email vào đây"
                required
              />
            </div>
          </div>

          <Button type="submit" variant="primary" className="auth-submit" disabled={verifying}>
            {verifying ? "Đang xác minh..." : "Xác minh ngay"}
          </Button>
        </form>

        <hr style={{ border: "none", borderTop: "1px solid #e2e8f0", margin: "1.75rem 0" }} />

        <div>
          <h3 style={{ fontSize: "0.95rem", color: "#0f172a", marginBottom: "0.5rem" }}>
            Chưa nhận được email hoặc mã đã hết hạn?
          </h3>
          <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "0.75rem" }}>
            Nhập email của bạn để hệ thống gửi lại liên kết kích hoạt mới.
          </p>
          <form className="auth-form" onSubmit={handleResend} noValidate>
            <div className="auth-field">
              <div className="auth-input-wrap">
                <Mail size={18} aria-hidden="true" />
                <input
                  type="email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="resident@vinuni.edu.vn"
                  required
                />
              </div>
            </div>
            <Button type="submit" variant="outline" size="sm" disabled={resending} style={{ width: "100%" }}>
              <RefreshCw size={15} style={{ marginRight: "6px" }} />
              {resending ? "Đang gửi..." : "Gửi lại liên kết xác minh"}
            </Button>
          </form>
        </div>
      </div>
    </AuthLayout>
  );
};

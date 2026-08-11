import React, { useState } from "react";
import {
  ArrowRight,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
  Mail,
  Shield,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { Button } from "../../components/common/Button";
import {
  DEMO_ACCOUNTS,
  DEMO_PASSWORD,
  useAuth,
} from "../../context/AuthContext";
import { UserRole } from "../../types";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

const roleMeta: Record<
  UserRole,
  { label: string; description: string; icon: typeof UserRound }
> = {
  resident: {
    label: "Cư dân",
    description: "Dashboard · AI Agent · Cảnh báo",
    icon: UserRound,
  },
  manager: {
    label: "Manager",
    description: "Thêm Phê duyệt · Audit Log",
    icon: Shield,
  },
  admin: {
    label: "Admin",
    description: "Toàn quyền quản trị MVP",
    icon: LockKeyhole,
  },
};

export const Login: React.FC = () => {
  const { authMessage, login, loginAsDemo, navigateTo } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password) {
      setError("Vui lòng nhập đầy đủ email và mật khẩu.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setError("Email chưa đúng định dạng.");
      return;
    }

    setSubmitting(true);
    window.setTimeout(() => {
      const result = login(email, password);
      if (!result.success) setError(result.message ?? "Không thể đăng nhập.");
      setSubmitting(false);
    }, 450);
  };

  return (
    <AuthLayout
      title="Không khí sạch hơn bắt đầu từ dữ liệu đáng tin cậy."
      description="Theo dõi PM2.5, cảnh báo và đề xuất có kiểm soát trong một không gian làm việc thống nhất."
    >
      <div className="auth-card auth-card--login">
        {/* LOGO THƯƠNG HIỆU PHỤ TRÊN MOBILE - TỰ ĐỘNG HIỆN KHI TRÊN ĐIỆN THOẠI */}
        <div className="auth-card__mobile-logo" aria-hidden="true">
          <span
            style={{
              display: "grid",
              width: "40px",
              height: "40px",
              placeItems: "center",
              border: "1px solid var(--color-border-strong)",
              borderRadius: "10px",
              background: "var(--color-primary-50)",
              color: "var(--color-primary-600)",
            }}
          >
            <ShieldCheck size={24} strokeWidth={2.2} />
          </span>
          <strong>AirGuard AI</strong>
        </div>

        <div className="auth-card__heading">
          <span className="auth-card__kicker">Demo Access</span>
          <h2>Đăng nhập AirGuard AI</h2>
          <p>
            Sử dụng tài khoản mẫu theo vai trò hoặc tài khoản Cư dân vừa đăng
            ký.
          </p>
        </div>

        {authMessage && (
          <div className="auth-notice auth-notice--success" role="status">
            {authMessage}
          </div>
        )}
        {error && (
          <div className="auth-notice auth-notice--error" role="alert">
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="login-email">Email</label>
            <div className="auth-input-wrap">
              <Mail size={18} aria-hidden="true" />
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="email@vinuni.edu.vn"
                autoComplete="email"
              />
            </div>
          </div>
          <div className="auth-field">
            <div className="auth-field__label-row">
              <label htmlFor="login-password">Mật khẩu</label>
              <span>Phiên demo nội bộ</span>
            </div>
            <div className="auth-input-wrap">
              <KeyRound size={18} aria-hidden="true" />
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Nhập mật khẩu"
                autoComplete="current-password"
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              >
                {showPassword ? (
                  <EyeOff size={18} aria-hidden="true" />
                ) : (
                  <Eye size={18} aria-hidden="true" />
                )}
              </button>
            </div>
          </div>
          <Button
            type="submit"
            variant="primary"
            className="auth-submit"
            disabled={submitting}
          >
            {submitting ? "Đang xác thực..." : "Đăng nhập"}
            {!submitting && <ArrowRight size={17} aria-hidden="true" />}
          </Button>
        </form>

        <div className="auth-divider">
          <span>Hoặc đăng nhập nhanh theo vai trò</span>
        </div>

        <div className="demo-account-list">
          {DEMO_ACCOUNTS.map((account) => {
            const meta = roleMeta[account.role];
            const Icon = meta.icon;
            return (
              <button
                key={account.role}
                type="button"
                className={`demo-account demo-account--${account.role}`}
                onClick={() => loginAsDemo(account.role)}
              >
                <span className="demo-account__icon">
                  <Icon size={19} aria-hidden="true" />
                </span>
                <span className="demo-account__copy">
                  <strong>{meta.label}</strong>
                  <small>{account.email}</small>
                  <em>{meta.description}</em>
                </span>
                <ArrowRight size={17} aria-hidden="true" />
              </button>
            );
          })}
        </div>

        <div className="demo-credential-note">
          <LockKeyhole size={16} aria-hidden="true" />
          <span>
            Mật khẩu chung cho tài khoản demo: <code>{DEMO_PASSWORD}</code>
          </span>
        </div>

        <p className="auth-switch">
          Chưa có tài khoản Cư dân?{" "}
          <button type="button" onClick={() => navigateTo("register")}>
            Đăng ký ngay
          </button>
        </p>
      </div>
    </AuthLayout>
  );
};

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
  Sparkles,
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
  { label: string; badgeColor: string; icon: typeof UserRound }
> = {
  resident: {
    label: "Cư dân",
    badgeColor: "#10b981",
    icon: UserRound,
  },
  manager: {
    label: "Quản lý",
    badgeColor: "#f59e0b",
    icon: Shield,
  },
  admin: {
    label: "Admin",
    badgeColor: "#6366f1",
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
    <AuthLayout>
      <div className="auth-wrapper-flex">
        {/* LEFT CARD: MAIN LOGIN FORM */}
        <div className="auth-card auth-card--login-main">
          <div className="auth-card__brand">
            <div className="auth-brand-logo">
              <ShieldCheck size={24} strokeWidth={2.2} />
            </div>
            <h1 className="auth-brand-title">AirGuard AI</h1>
          </div>

          <div className="auth-card__heading">
            <h2>Đăng nhập</h2>
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
                  placeholder="resident@vinuni.edu.vn"
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="login-password">Mật khẩu</label>
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

          <p className="auth-switch">
            Chưa có tài khoản?{" "}
            <button type="button" onClick={() => navigateTo("register")}>
              Đăng ký
            </button>
          </p>
        </div>

        {/* RIGHT CARD: DEMO ACCOUNT SELECTOR */}
        <div className="auth-card auth-card--demo-selector">
          <div className="demo-selector-header">
            <div className="demo-title-row">
              <Sparkles size={18} style={{ color: "#10b981" }} />
              <h3>Truy cập nhanh</h3>
            </div>
          </div>

          <div className="demo-role-cards-stack">
            {DEMO_ACCOUNTS.map((account) => {
              const meta = roleMeta[account.role];
              const Icon = meta.icon;
              return (
                <button
                  key={account.role}
                  type="button"
                  className={`demo-role-btn demo-role-btn--${account.role}`}
                  onClick={() => loginAsDemo(account.role)}
                >
                  <div className="demo-role-btn__icon" style={{ background: `${meta.badgeColor}18`, color: meta.badgeColor }}>
                    <Icon size={20} />
                  </div>
                  <div className="demo-role-btn__info">
                    <div className="demo-role-btn__top">
                      <strong className="role-name">{meta.label}</strong>
                    </div>
                    <span className="account-email">{account.email}</span>
                  </div>
                  <ArrowRight size={16} className="btn-arrow-icon" />
                </button>
              );
            })}
          </div>

          <div className="demo-credential-note">
            <LockKeyhole size={15} aria-hidden="true" />
            <span>
              Mật khẩu demo: <code>{DEMO_PASSWORD}</code>
            </span>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
};



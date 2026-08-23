import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../api/client";
import { formatAuthError, isEmailNotVerifiedError } from "../../utils/authErrors";
import "./auth.css";

// Icons
const ShieldIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const MailIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2" />
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
  </svg>
);

const LockIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const EyeIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const EyeOffIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
    <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
    <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61" />
    <line x1="2" y1="2" x2="22" y2="22" />
  </svg>
);

const UserIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

const ShieldCheckIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const KeyIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="7.5" cy="15.5" r="5.5" />
    <path d="m21 2-9.6 9.6" />
    <path d="m15.5 7.5 3 3L22 7l-3-3" />
  </svg>
);

const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
    />
  </svg>
);

const SparklesIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
    <path d="M5 3v4" />
    <path d="M19 17v4" />
    <path d="M3 5h4" />
    <path d="M17 19h4" />
  </svg>
);

const ChevronDownIcon = ({ open }: { open: boolean }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ transform: open ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}
  >
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

export const Login: React.FC = () => {
  const {
    login,
    demoLogin,
    setCurrentScreen,
    navigateTo,
    authMessage,
    clearAuthMessage,
    demoMode,
    googleAuthEnabled,
    setPendingEmailVerification,
  } = useAuth();


  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [demoSubmitting, setDemoSubmitting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUnverified, setIsUnverified] = useState(false);
  const [showMobileAccordion, setShowMobileAccordion] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsUnverified(false);
    clearAuthMessage();

    if (!email.trim() || !password) {
      setError("Vui lòng nhập đầy đủ email và mật khẩu.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setError("Email chưa đúng định dạng.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await login(email.trim(), password);
      if (!result.success) {
        setError(formatAuthError(result.message));
        if (isEmailNotVerifiedError(result.message)) {
          setIsUnverified(true);
        }
      }
    } catch (err: any) {
      setError(formatAuthError(err));
      if (isEmailNotVerifiedError(err)) {
        setIsUnverified(true);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoToVerifyEmail = () => {
    setPendingEmailVerification({
      email: email.trim(),
      deliveryStatus: "unknown",
    });
    navigateTo("verify-email");
  };

  const handleGoogleLogin = () => {
    setError(null);
    clearAuthMessage();

    // If Google OAuth is disabled on server, inform user gracefully
    if (!googleAuthEnabled) {
      setError("Đăng nhập Google hiện chưa khả dụng.");
      return;
    }

    setGoogleLoading(true);
    try {
      // Top-level navigation to backend OAuth endpoint
      const targetUrl = api.getGoogleAuthStartUrl();
      window.location.assign(targetUrl);
    } catch (err: any) {
      setGoogleLoading(false);
      setError("Đăng nhập Google hiện chưa khả dụng.");
    }
  };

  const handleDemoRole = async (persona: "resident" | "sensitive" | "outdoor_sport" | "manager") => {
    setError(null);
    clearAuthMessage();
    setDemoSubmitting(persona);

    try {
      const result = await demoLogin(persona);
      if (!result.success) {
        setError(formatAuthError(result.message));
      }
    } catch (err: any) {
      setError(formatAuthError(err));
    } finally {
      setDemoSubmitting(null);
    }
  };

  const handleAdminComingSoon = () => {
    setError(null);
    clearAuthMessage();
    setCurrentScreen("admin-coming-soon");
  };

  const isAnySubmitting = submitting || googleLoading || demoSubmitting !== null;

  return (
    <div className="auth-layout">
      <div className="auth-unified-container">
        {/* LEFT COLUMN: Main Login Form */}
        <div className="auth-column-main">
          {/* Brand Header */}
          <div className="auth-brand-compact">
            <div className="auth-brand-icon">
              <ShieldIcon />
            </div>
            <div className="auth-brand-text">
              <h2>Chào mừng trở lại</h2>
              <p>Đăng nhập để theo dõi chất lượng không khí.</p>
            </div>
          </div>

          {/* Feedback Alerts */}
          {authMessage && (
            <div className="auth-notice auth-notice--success" role="status" aria-live="polite">
              <span>{authMessage}</span>
            </div>
          )}

          {error && (
            <div
              className="auth-notice auth-notice--error"
              role="alert"
              aria-live="assertive"
              style={isUnverified ? { flexDirection: "column", alignItems: "flex-start", gap: "6px" } : undefined}
            >
              <span>{error}</span>
              {isUnverified && (
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={handleGoToVerifyEmail}
                  style={{ color: "#0284c7", fontWeight: 700, textDecoration: "underline", marginTop: "2px" }}
                >
                  Gửi lại email xác minh →
                </button>
              )}
            </div>
          )}

          {/* Google OAuth Button */}
          <button
            type="button"
            className="auth-google-btn"
            onClick={handleGoogleLogin}
            disabled={isAnySubmitting}
            aria-label="Tiếp tục với Google"
          >
            <GoogleIcon />
            <span>{googleLoading ? "Đang chuyển hướng..." : "Tiếp tục với Google"}</span>
          </button>

          {/* Divider */}
          <div className="auth-divider" aria-hidden="true">
            <span>hoặc đăng nhập bằng email</span>
          </div>

          {/* Form */}
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-field">
              <label htmlFor="login-email">Email</label>
              <div className="auth-input-wrap">
                <MailIcon />
                <input
                  id="login-email"
                  type="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isAnySubmitting}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="auth-field">
              <div className="auth-field-header">
                <label htmlFor="login-password">Mật khẩu</label>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={() => setCurrentScreen("forgot-password")}
                  disabled={isAnySubmitting}
                >
                  Quên mật khẩu?
                </button>
              </div>
              <div className="auth-input-wrap">
                <LockIcon />
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isAnySubmitting}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn--primary auth-submit"
              disabled={isAnySubmitting}
            >
              {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>

          {/* Bottom links */}
          <div className="auth-bottom-links">
            <div className="auth-switch">
              <span>Chưa có tài khoản?</span>{" "}
              <button
                type="button"
                onClick={() => setCurrentScreen("register")}
                disabled={isAnySubmitting}
              >
                Đăng ký
              </button>
            </div>
            {error && error.includes("xác minh") && (
              <button
                type="button"
                className="auth-link-secondary"
                onClick={() => setCurrentScreen("verify-email")}
                disabled={isAnySubmitting}
              >
                Xác minh lại email
              </button>
            )}
          </div>

          {/* MOBILE ACCORDION FOR DEMO ROLES */}
          {demoMode && (
            <div className="demo-mobile-section">
              <button
                type="button"
                className="demo-accordion-toggle"
                onClick={() => setShowMobileAccordion(!showMobileAccordion)}
                aria-expanded={showMobileAccordion}
              >
                <div className="demo-accordion-toggle__left">
                  <SparklesIcon />
                  <span>Dùng tài khoản trải nghiệm</span>
                </div>
                <ChevronDownIcon open={showMobileAccordion} />
              </button>

              {showMobileAccordion && (
                <div className="demo-mobile-cards">
                  <div className="demo-persona-card">
                    <div className="demo-persona-card__icon demo-persona-card__icon--resident">
                      <UserIcon />
                    </div>
                    <div className="demo-persona-card__content">
                      <div className="demo-persona-card__header">
                        <span className="demo-persona-card__name">Cư dân</span>
                        <span className="demo-persona-badge demo-persona-badge--resident">Resident</span>
                      </div>
                      <p className="demo-persona-card__desc">Theo dõi AQI, cảnh báo và khuyến nghị cá nhân.</p>
                    </div>
                    <button
                      type="button"
                      className="demo-try-action-btn"
                      onClick={() => handleDemoRole("resident")}
                      disabled={isAnySubmitting}
                    >
                      {demoSubmitting === "resident" ? "..." : "Dùng thử"}
                    </button>
                  </div>

                  <div className="demo-persona-card">
                    <div className="demo-persona-card__icon demo-persona-card__icon--resident">
                      <UserIcon />
                    </div>
                    <div className="demo-persona-card__content">
                      <div className="demo-persona-card__header">
                        <span className="demo-persona-card__name">Nhóm nhạy cảm</span>
                        <span className="demo-persona-badge demo-persona-badge--resident">Sensitive</span>
                      </div>
                      <p className="demo-persona-card__desc">Kiểm thử cảnh báo sớm và khuyến nghị thận trọng.</p>
                    </div>
                    <button type="button" className="demo-try-action-btn" onClick={() => handleDemoRole("sensitive")} disabled={isAnySubmitting}>
                      {demoSubmitting === "sensitive" ? "..." : "Dùng thử"}
                    </button>
                  </div>

                  <div className="demo-persona-card">
                    <div className="demo-persona-card__icon demo-persona-card__icon--resident">
                      <UserIcon />
                    </div>
                    <div className="demo-persona-card__content">
                      <div className="demo-persona-card__header">
                        <span className="demo-persona-card__name">Hoạt động ngoài trời</span>
                        <span className="demo-persona-badge demo-persona-badge--resident">Outdoor</span>
                      </div>
                      <p className="demo-persona-card__desc">Kiểm thử thời điểm và khu vực vận động phù hợp.</p>
                    </div>
                    <button type="button" className="demo-try-action-btn" onClick={() => handleDemoRole("outdoor_sport")} disabled={isAnySubmitting}>
                      {demoSubmitting === "outdoor_sport" ? "..." : "Dùng thử"}
                    </button>
                  </div>

                  <div className="demo-persona-card">
                    <div className="demo-persona-card__icon demo-persona-card__icon--manager">
                      <ShieldCheckIcon />
                    </div>
                    <div className="demo-persona-card__content">
                      <div className="demo-persona-card__header">
                        <span className="demo-persona-card__name">Quản lý</span>
                        <span className="demo-persona-badge demo-persona-badge--manager">Manager</span>
                      </div>
                      <p className="demo-persona-card__desc">Xử lý cảnh báo và phê duyệt đề xuất.</p>
                    </div>
                    <button
                      type="button"
                      className="demo-try-action-btn"
                      onClick={() => handleDemoRole("manager")}
                      disabled={isAnySubmitting}
                    >
                      {demoSubmitting === "manager" ? "..." : "Dùng thử"}
                    </button>
                  </div>

                  <div className="demo-persona-card">
                    <div className="demo-persona-card__icon demo-persona-card__icon--admin">
                      <KeyIcon />
                    </div>
                    <div className="demo-persona-card__content">
                      <div className="demo-persona-card__header">
                        <span className="demo-persona-card__name">Quản trị viên</span>
                        <span className="demo-persona-badge demo-persona-badge--admin">Admin</span>
                      </div>
                      <p className="demo-persona-card__desc">Khu vực quản trị đang được phát triển.</p>
                    </div>
                    <button
                      type="button"
                      className="demo-try-action-btn"
                      onClick={handleAdminComingSoon}
                      disabled={isAnySubmitting}
                      aria-label="Xem thông tin tính năng Quản trị viên sắp ra mắt"
                    >
                      Xem thông tin
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Desktop Quick Demo Roles or System Highlights */}
        <div className="auth-column-demo">
          {demoMode ? (
            <div className="demo-panel-inner">
              <div className="demo-selector-header">
                <div className="demo-title-row">
                  <SparklesIcon />
                  <h3>Trải nghiệm theo vai trò</h3>
                </div>
                <p>Chọn vai trò để khám phá các tính năng của AirGuard AI.</p>
              </div>

              <div className="demo-role-cards-stack">
                {/* 1. Resident Card */}
                <div className="demo-persona-card">
                  <div className="demo-persona-card__icon demo-persona-card__icon--resident">
                    <UserIcon />
                  </div>
                  <div className="demo-persona-card__content">
                    <div className="demo-persona-card__header">
                      <span className="demo-persona-card__name">Cư dân</span>
                      <span className="demo-persona-badge demo-persona-badge--resident">Resident</span>
                    </div>
                    <p className="demo-persona-card__desc">Theo dõi AQI, cảnh báo và khuyến nghị cá nhân.</p>
                  </div>
                  <button
                    type="button"
                    className="demo-try-action-btn"
                    onClick={() => handleDemoRole("resident")}
                    disabled={isAnySubmitting}
                    aria-label="Dùng thử vai trò Cư dân"
                  >
                    {demoSubmitting === "resident" ? "Đang vào..." : "Dùng thử"}
                  </button>
                </div>

                <div className="demo-persona-card">
                  <div className="demo-persona-card__icon demo-persona-card__icon--resident">
                    <UserIcon />
                  </div>
                  <div className="demo-persona-card__content">
                    <div className="demo-persona-card__header">
                      <span className="demo-persona-card__name">Nhóm nhạy cảm</span>
                      <span className="demo-persona-badge demo-persona-badge--resident">Sensitive</span>
                    </div>
                    <p className="demo-persona-card__desc">Kiểm thử cảnh báo sớm và khuyến nghị thận trọng.</p>
                  </div>
                  <button type="button" className="demo-try-action-btn" onClick={() => handleDemoRole("sensitive")} disabled={isAnySubmitting}>
                    {demoSubmitting === "sensitive" ? "Đang vào..." : "Dùng thử"}
                  </button>
                </div>

                <div className="demo-persona-card">
                  <div className="demo-persona-card__icon demo-persona-card__icon--resident">
                    <UserIcon />
                  </div>
                  <div className="demo-persona-card__content">
                    <div className="demo-persona-card__header">
                      <span className="demo-persona-card__name">Hoạt động ngoài trời</span>
                      <span className="demo-persona-badge demo-persona-badge--resident">Outdoor</span>
                    </div>
                    <p className="demo-persona-card__desc">Kiểm thử thời điểm và khu vực vận động phù hợp.</p>
                  </div>
                  <button type="button" className="demo-try-action-btn" onClick={() => handleDemoRole("outdoor_sport")} disabled={isAnySubmitting}>
                    {demoSubmitting === "outdoor_sport" ? "Đang vào..." : "Dùng thử"}
                  </button>
                </div>

                {/* 4. Manager Card */}
                <div className="demo-persona-card">
                  <div className="demo-persona-card__icon demo-persona-card__icon--manager">
                    <ShieldCheckIcon />
                  </div>
                  <div className="demo-persona-card__content">
                    <div className="demo-persona-card__header">
                      <span className="demo-persona-card__name">Quản lý</span>
                      <span className="demo-persona-badge demo-persona-badge--manager">Manager</span>
                    </div>
                    <p className="demo-persona-card__desc">Xử lý cảnh báo và phê duyệt đề xuất.</p>
                  </div>
                  <button
                    type="button"
                    className="demo-try-action-btn"
                    onClick={() => handleDemoRole("manager")}
                    disabled={isAnySubmitting}
                    aria-label="Dùng thử vai trò Quản lý"
                  >
                    {demoSubmitting === "manager" ? "Đang vào..." : "Dùng thử"}
                  </button>
                </div>

                {/* 3. Admin Card */}
                <div className="demo-persona-card">
                  <div className="demo-persona-card__icon demo-persona-card__icon--admin">
                    <KeyIcon />
                  </div>
                  <div className="demo-persona-card__content">
                    <div className="demo-persona-card__header">
                      <span className="demo-persona-card__name">Quản trị viên</span>
                      <span className="demo-persona-badge demo-persona-badge--admin">Admin</span>
                    </div>
                    <p className="demo-persona-card__desc">Khu vực quản trị đang được phát triển.</p>
                  </div>
                  <button
                    type="button"
                    className="demo-try-action-btn"
                    onClick={handleAdminComingSoon}
                    disabled={isAnySubmitting}
                    aria-label="Xem thông tin tính năng Quản trị viên sắp ra mắt"
                  >
                    Xem thông tin
                  </button>
                </div>
              </div>

              <div className="demo-env-badge">
                <span>Chế độ trải nghiệm thử nghiệm (Demo Mode)</span>
              </div>
            </div>
          ) : (
            <div className="demo-panel-inner">
              <div className="demo-selector-header">
                <h3>Hệ thống AirGuard AI</h3>
                <p>Nền tảng quan trắc và cảnh báo chất lượng môi trường không khí.</p>
              </div>

              <div className="prod-benefits-stack">
                <div className="prod-benefit-item">
                  <strong>Dữ liệu đa chỉ số tức thời</strong>
                  <p>Cập nhật liên tục AQI, PM2.5, CO₂, nhiệt độ và độ ồn từ mạng lưới trạm quan trắc.</p>
                </div>
                <div className="prod-benefit-item">
                  <strong>Bản đồ lan truyền không gian</strong>
                  <p>Trực quan hóa vùng nồng độ môi trường kết hợp hướng và vận tốc gió thực tế.</p>
                </div>
                <div className="prod-benefit-item">
                  <strong>Trợ lý AI & Khuyến nghị cá nhân</strong>
                  <p>Phân tích xu hướng và đề xuất lộ trình hoạt động ngoài trời an toàn theo nhóm thể trạng.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

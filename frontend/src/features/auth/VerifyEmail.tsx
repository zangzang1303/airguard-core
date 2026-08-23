import React, { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  MailCheck,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Button } from "../../components/common/Button";
import { useAuth } from "../../context/AuthContext";
import { AuthLayout } from "./AuthLayout";
import "./auth.css";

const OTP_LENGTH = 6;

function maskEmail(email: string): string {
  if (!email || !email.includes("@")) return "";
  const [local, domain] = email.split("@");
  if (local.length <= 2) {
    return `${local}***@${domain}`;
  }
  return `${local.slice(0, 2)}***@${domain}`;
}

export const VerifyEmail: React.FC = () => {
  const {
    navigateTo,
    verifyEmail,
    resendVerification,
    setAuthMessage,
    pendingEmailVerification,
    clearPendingEmailVerification,
  } = useAuth();

  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number>(60);
  const [manualEmail, setManualEmail] = useState("");

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // 60s countdown timer effect
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  // Focus the first input on load
  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  const hasPendingEmail = Boolean(pendingEmailVerification?.email?.trim());
  const targetEmail = pendingEmailVerification?.email?.trim() || manualEmail.trim();
  const hasValidEmail = /^\S+@\S+\.\S+$/.test(targetEmail);
  const displayedMaskedEmail = maskEmail(targetEmail);

  const handleOtpChange = (index: number, value: string) => {
    const cleaned = value.replace(/\D/g, "");
    if (!cleaned) {
      const newOtp = [...otp];
      newOtp[index] = "";
      setOtp(newOtp);
      return;
    }

    const digit = cleaned.slice(-1);
    const newOtp = [...otp];
    newOtp[index] = digit;
    setOtp(newOtp);
    setError(null);

    // Auto-advance focus to next box
    if (index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (!otp[index] && index > 0) {
        inputRefs.current[index - 1]?.focus();
        const newOtp = [...otp];
        newOtp[index - 1] = "";
        setOtp(newOtp);
      }
    } else if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "");
    if (!pasted) return;

    const digits = pasted.slice(0, OTP_LENGTH).split("");
    const newOtp = [...otp];
    digits.forEach((d, i) => {
      newOtp[i] = d;
    });
    setOtp(newOtp);
    setError(null);

    const nextIndex = Math.min(digits.length, OTP_LENGTH) - 1;
    if (nextIndex >= 0 && nextIndex < OTP_LENGTH) {
      inputRefs.current[nextIndex]?.focus();
    }
  };

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const fullCode = otp.join("").trim();
    if (fullCode.length !== OTP_LENGTH) {
      setError("Vui lòng nhập đủ 6 chữ số mã xác minh.");
      return;
    }

    setError(null);
    setSuccessMsg(null);
    setVerifying(true);

    try {
      const res = await verifyEmail(fullCode);
      if (res.success) {
        clearPendingEmailVerification();
        setSuccessMsg(res.message || "Xác minh email thành công!");
        setAuthMessage("Tài khoản của bạn đã được kích hoạt thành công. Vui lòng đăng nhập.");
        setTimeout(() => {
          navigateTo("login");
        }, 1800);
      } else {
        setError(res.message || "Mã xác minh không chính xác hoặc đã hết hạn.");
      }
    } catch (err: any) {
      setError(err?.message || "Mã xác minh không hợp lệ hoặc đã hết hạn. Vui lòng thử lại.");
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async () => {
    if (!hasValidEmail) {
      setError("Vui lòng nhập địa chỉ email hợp lệ để nhận mã xác minh.");
      return;
    }
    if ((hasPendingEmail && countdown > 0) || resending) return;
    setError(null);
    setSuccessMsg(null);
    setResending(true);

    try {
      const res = await resendVerification(targetEmail);
      if (res.success) {
        setCountdown(60);
        setOtp(Array(OTP_LENGTH).fill(""));
        inputRefs.current[0]?.focus();
        setSuccessMsg("Mã xác minh mới đã được gửi đến email của bạn.");
      } else {
        setError(res.message || "Không thể gửi lại mã xác minh. Vui lòng thử lại sau.");
      }
    } catch (err: any) {
      setError(err?.message || "Không thể gửi lại mã xác minh. Vui lòng thử lại sau.");
    } finally {
      setResending(false);
    }
  };

  const isOtpComplete = otp.every((d) => d.trim() !== "");

  return (
    <AuthLayout>
      <div className="auth-card auth-card--standalone" style={{ maxWidth: "480px" }}>
        {/* Header Toolbar */}
        <div className="register-header-toolbar">
          <Button
            variant="ghost"
            size="sm"
            className="auth-back"
            onClick={() => {
              clearPendingEmailVerification();
              navigateTo("login");
            }}
          >
            <ArrowLeft size={16} aria-hidden="true" /> Quay lại đăng nhập
          </Button>

          <div className="auth-card__brand">
            <div className="auth-brand-logo">
              <ShieldCheck size={22} strokeWidth={2.2} />
            </div>
            <h1 className="auth-brand-title">AirGuard AI</h1>
          </div>
        </div>

        {/* Dynamic Heading */}
        <div className="auth-card__heading" style={{ textAlign: "center", marginBottom: "18px" }}>
          <h2 style={{ fontSize: "1.32rem", fontWeight: 800, color: "#0f172a", margin: "0 0 6px" }}>
            Xác nhận địa chỉ email
          </h2>
          <p className="auth-card__subtitle" style={{ fontSize: "0.86rem", color: "#475569", margin: 0, lineHeight: 1.5 }}>
            {hasPendingEmail ? (
              <>Chúng tôi đã gửi mã xác minh gồm 6 chữ số đến <strong>{displayedMaskedEmail}</strong>.</>
            ) : (
              <>Nhập email để nhận mã xác minh gồm 6 chữ số.</>
            )}
          </p>
        </div>

        {!hasPendingEmail && (
          <div className="auth-field" style={{ marginBottom: "16px" }}>
            <label htmlFor="verification-email">Email nhận mã xác minh</label>
            <div className="auth-input-wrap">
              <input
                id="verification-email"
                type="email"
                value={manualEmail}
                onChange={(event) => setManualEmail(event.target.value)}
                placeholder="name@example.com"
                autoComplete="email"
                disabled={resending}
              />
            </div>
          </div>
        )}

        {/* Notices */}
        {successMsg && (
          <div className="auth-notice auth-notice--success" role="status">
            <CheckCircle2 size={18} style={{ marginRight: "6px", verticalAlign: "middle", flexShrink: 0 }} />
            {successMsg}
          </div>
        )}
        {error && (
          <div className="auth-notice auth-notice--error" role="alert">
            <ShieldAlert size={18} style={{ marginRight: "6px", verticalAlign: "middle", flexShrink: 0 }} />
            {error}
          </div>
        )}

        {/* Instructions Block */}
        <div className="verify-instruction-box">
          <div className="verify-instruction-icon">
            <MailCheck size={24} strokeWidth={2.2} />
          </div>
          <h3 className="verify-instruction-title">Kiểm tra email của bạn</h3>
          <p className="verify-instruction-desc">
            Nhập mã xác minh để kích hoạt tài khoản.
          </p>
        </div>

        {/* 6-Digit OTP Form */}
        <form onSubmit={handleVerify} noValidate>
          <div className="otp-container">
            <label className="auth-field__label" style={{ fontWeight: 700, fontSize: "0.88rem", color: "#1e293b", marginBottom: "4px" }}>
              Mã xác minh
            </label>

            <div className="otp-inputs-row" role="group" aria-label="Mã xác minh 6 chữ số">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => {
                    inputRefs.current[index] = el;
                  }}
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={1}
                  autoComplete="one-time-code"
                  value={digit}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={handlePaste}
                  aria-label={`Chữ số thứ ${index + 1}`}
                  className={`otp-digit-input ${digit ? "otp-digit-input--filled" : ""} ${
                    error ? "otp-digit-input--error" : ""
                  }`}
                  disabled={verifying || !hasPendingEmail}
                />
              ))}
            </div>

            <p className="otp-hint-text">Mã có hiệu lực trong 10 phút.</p>
          </div>

          {/* Action Buttons */}
          <div className="verify-actions">
            <Button
              type="submit"
              variant="primary"
              className="auth-submit"
              disabled={!hasPendingEmail || !isOtpComplete || verifying}
              style={{ width: "100%", height: "46px", fontSize: "0.95rem", fontWeight: 700 }}
            >
              {verifying ? (
                <>
                  <RefreshCw className="auth-spinner" size={16} aria-hidden="true" />
                  Đang xác minh...
                </>
              ) : (
                "Xác minh ngay"
              )}
            </Button>

            <Button
              type="button"
              variant="ghost"
              className="verify-resend-btn"
              onClick={handleResend}
              disabled={!hasValidEmail || (hasPendingEmail && countdown > 0) || resending}
            >
              {resending ? (
                <>
                  <RefreshCw className="auth-spinner" size={15} aria-hidden="true" />
                  Đang gửi mã mới...
                </>
              ) : hasPendingEmail && countdown > 0 ? (
                `Gửi lại mã xác minh (${countdown}s)`
              ) : hasPendingEmail ? (
                "Gửi lại mã xác minh"
              ) : (
                "Gửi mã xác minh"
              )}
            </Button>
          </div>
        </form>

        {/* Footer Navigation */}
        <div style={{ textAlign: "center", marginTop: "16px" }}>
          <button
            type="button"
            className="verify-back-link"
            onClick={() => {
              clearPendingEmailVerification();
              navigateTo("login");
            }}
          >
            Quay lại đăng nhập
          </button>
        </div>
      </div>
    </AuthLayout>
  );
};

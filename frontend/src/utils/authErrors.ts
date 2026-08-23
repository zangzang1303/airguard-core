/**
 * Utility for mapping backend error responses and exceptions to friendly Vietnamese user messages.
 * Prevents showing raw technical status codes (e.g. "API Error 404: Not Found") or internal exception strings.
 */

export interface AppError {
  code?: string;
  status?: number;
  message?: string;
  details?: Record<string, any>;
}

export function formatAuthError(err: any): string {
  if (!err) {
    return "Đã có lỗi xảy ra. Vui lòng thử lại.";
  }

  // If already a friendly string without technical prefixes
  if (typeof err === "string") {
    if (err.includes("API Error") || err.includes("404") || err.includes("500") || err.includes("Failed to fetch")) {
      return mapErrorByPatterns(err);
    }
    return err;
  }

  const code = (err.code || "").toLowerCase();
  const status = Number(err.status) || 0;
  const msg = (err.message || "").toLowerCase();

  // 1. Google OAuth errors
  if (
    code === "oauth_not_configured" ||
    code === "not_configured" ||
    msg.includes("oauth_not_configured") ||
    msg.includes("google") ||
    msg.includes("oauth")
  ) {
    return "Đăng nhập Google hiện chưa khả dụng.";
  }

  // 2. Demo mode / persona errors
  if (
    code === "demo_mode_disabled" ||
    code === "demo_disabled" ||
    (status === 404 && msg.includes("demo")) ||
    msg.includes("demo-login") ||
    msg.includes("persona")
  ) {
    return "Tài khoản trải nghiệm hiện chưa được bật.";
  }

  // 3. Credentials & Auth errors
  if (
    code === "invalid_credentials" ||
    status === 401 ||
    msg.includes("credentials") ||
    msg.includes("mật khẩu") ||
    msg.includes("sai email")
  ) {
    return "Email hoặc mật khẩu không đúng.";
  }

  // 4. Verification errors
  if (
    code === "email_not_verified" ||
    code === "unverified" ||
    msg.includes("chưa xác minh") ||
    msg.includes("unverified")
  ) {
    return "Vui lòng xác minh email trước khi đăng nhập.";
  }

  // 5. Account state errors
  if (
    code === "account_locked" ||
    code === "locked" ||
    msg.includes("khóa") ||
    msg.includes("locked")
  ) {
    return "Tài khoản đang bị khóa. Vui lòng liên hệ quản trị viên.";
  }

  if (
    code === "account_disabled" ||
    code === "account_inactive" ||
    msg.includes("vô hiệu hóa")
  ) {
    return "Tài khoản đang bị vô hiệu hóa. Vui lòng liên hệ quản trị viên.";
  }

  // 6. Generic 404
  if (status === 404 || msg.includes("404") || msg.includes("not found")) {
    return "Dịch vụ yêu cầu hiện chưa sẵn sàng hoặc không tồn tại.";
  }

  // 7. Network / Server connection errors
  if (
    status === 502 ||
    status === 503 ||
    status === 504 ||
    msg.includes("failed to fetch") ||
    msg.includes("network") ||
    msg.includes("kết nối") ||
    msg.includes("cors")
  ) {
    return "Không thể kết nối máy chủ. Vui lòng thử lại.";
  }

  // Return sanitized message if readable, otherwise fallback
  if (err.message && !err.message.includes("API Error") && !err.message.includes("statusText")) {
    return err.message;
  }

  return "Không thể kết nối máy chủ. Vui lòng thử lại.";
}

function mapErrorByPatterns(raw: string): string {
  const lower = raw.toLowerCase();
  if (lower.includes("google") || lower.includes("oauth")) {
    return "Đăng nhập Google hiện chưa khả dụng.";
  }
  if (lower.includes("demo") || (lower.includes("404") && lower.includes("demo"))) {
    return "Tài khoản trải nghiệm hiện chưa được bật.";
  }
  if (lower.includes("failed to fetch") || lower.includes("network") || lower.includes("kết nối")) {
    return "Không thể kết nối máy chủ. Vui lòng thử lại.";
  }
  return "Đã có lỗi xảy ra. Vui lòng thử lại.";
}

export function isEmailNotVerifiedError(err: any): boolean {
  if (!err) return false;
  if (typeof err === "string") {
    const lower = err.toLowerCase();
    return lower.includes("email_not_verified") || lower.includes("chưa xác minh") || lower.includes("unverified");
  }
  const code = (err.code || "").toLowerCase();
  const msg = (err.message || "").toLowerCase();
  return (
    code === "email_not_verified" ||
    code === "unverified" ||
    msg.includes("email_not_verified") ||
    msg.includes("chưa xác minh") ||
    msg.includes("unverified")
  );
}


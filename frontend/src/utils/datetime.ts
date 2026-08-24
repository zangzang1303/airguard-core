export const VN_TZ = "Asia/Ho_Chi_Minh";

export const SEVERITY_LABEL: Record<string, string> = {
  good: "Tốt",
  moderate: "Trung bình",
  warning: "Cảnh báo",
  critical: "Nghiêm trọng",
};

/**
 * Helper to safely parse a Date or ISO string
 */
function parseDate(value?: string | Date | null): Date | null {
  if (!value) return null;
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return null;
  return date;
}

/**
 * Format time with seconds in Asia/Ho_Chi_Minh (HH:mm:ss)
 * Example: 23:07:02
 */
export function formatVnTimeWithSeconds(value?: string | Date | null): string {
  const date = parseDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: VN_TZ,
  }).format(date);
}

/**
 * Format date time with seconds in Asia/Ho_Chi_Minh (HH:mm:ss DD/MM/YYYY)
 * Example: 23:07:03 24/08/2026
 */
export function formatVnDateTimeWithSeconds(value?: string | Date | null): string {
  const date = parseDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour12: false,
    timeZone: VN_TZ,
  }).format(date);
}

/**
 * Format date time in Asia/Ho_Chi_Minh (HH:mm DD/MM/YYYY)
 */
export function formatVnDateTime(value?: string | Date | null): string {
  const date = parseDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour12: false,
    timeZone: VN_TZ,
  }).format(date);
}

/**
 * Format time only in Asia/Ho_Chi_Minh (HH:mm)
 */
export function formatVnTime(value?: string | Date | null): string {
  const date = parseDate(value);
  if (!date) return "—";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: VN_TZ,
  }).format(date);
}

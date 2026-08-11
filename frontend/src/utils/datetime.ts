export const VN_TZ = "Asia/Ho_Chi_Minh";

export const SEVERITY_LABEL: Record<string, string> = {
  good: "Tốt",
  moderate: "Trung bình",
  warning: "Cảnh báo",
  critical: "Nghiêm trọng",
};

export function formatVnDateTime(value?: string): string {
  if (!value) return "Chưa có dữ liệu";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Không xác định";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
    timeZone: VN_TZ,
  }).format(date);
}

export function formatVnTime(value?: string): string {
  if (!value) return "Chưa có dữ liệu";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Không xác định";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: VN_TZ,
  }).format(date);
}

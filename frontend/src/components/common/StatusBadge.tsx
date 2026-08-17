import React from "react";
import { AlertCircle, CheckCircle2, CircleDashed, CircleX, Clock3 } from "lucide-react";

type Status = "active" | "resolved" | "pending" | "approved" | "rejected" | "success" | "succeeded" | "failed" | "error" | string;

interface StatusBadgeProps {
  status: Status;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const normalized = status.toLowerCase();
  const Icon = normalized === "active"
    ? AlertCircle
    : normalized === "resolved" || normalized === "approved" || normalized === "success" || normalized === "succeeded"
      ? CheckCircle2
      : normalized === "pending"
        ? Clock3
        : normalized === "rejected" || normalized === "expired" || normalized === "failed" || normalized === "error"
          ? CircleX
          : CircleDashed;

  const defaultLabel: Record<string, string> = {
    active: "Đang kích hoạt",
    resolved: "Đã xử lý",
    pending: "Đang chờ",
    approved: "Đã phê duyệt",
    rejected: "Đã từ chối",
    expired: "Đã quá hạn",
    success: "Thành công",
    succeeded: "Thành công",
    failed: "Thất bại",
    error: "Lỗi",
  };

  return (
    <span className={`status-badge status-badge--${normalized}`}>
      <Icon size={14} aria-hidden="true" />
      {label ?? defaultLabel[normalized] ?? status}
    </span>
  );
};


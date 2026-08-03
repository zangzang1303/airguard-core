import React from "react";
import { StationStatus } from "../../types";

export interface Pm25SeverityInfo {
  label: string;
  class: string;
  color: string;
}

export function getPm25Severity(pm25: number | null | undefined): Pm25SeverityInfo {
  if (pm25 === null || pm25 === undefined) return { label: "Không khả dụng", class: "status-null", color: "#9ca3af" };
  if (pm25 <= 25) return { label: "Tốt (Good)", class: "level-good", color: "#10b981" };
  if (pm25 <= 50) return { label: "Trung bình (Moderate)", class: "level-moderate", color: "#f59e0b" };
  if (pm25 <= 100) return { label: "Kém (Unhealthy)", class: "level-unhealthy", color: "#ef4444" };
  return { label: "Rất nguy hại (Hazardous)", class: "level-hazardous", color: "#8b5cf6" };
}

interface DataQualityBadgeProps {
  status?: StationStatus;
  isStale?: boolean;
  pm25?: number | null;
}

export const DataQualityBadge: React.FC<DataQualityBadgeProps> = ({
  status = "online",
  isStale = false,
  pm25 = null
}) => {
  // Data quality precedence: invalid > offline > stale > PM2.5 severity
  if (status === "invalid") {
    return <span className="badge badge-invalid" title="Dữ liệu bị lỗi kiểm định">⚠️ Invalid Data</span>;
  }
  if (status === "offline") {
    return <span className="badge badge-offline" title="Trạm quan trắc đang mất kết nối">🔴 Station Offline</span>;
  }
  if (isStale) {
    return <span className="badge badge-stale" title="Dữ liệu trễ so với thời gian thực">⏳ Stale Data</span>;
  }

  const severity = getPm25Severity(pm25);
  return (
    <span className={`badge ${severity.class}`} style={{ borderLeft: `4px solid ${severity.color}` }}>
      🟢 {severity.label}
    </span>
  );
};

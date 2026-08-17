import React from "react";
import { AlertTriangle, CheckCircle2, CircleOff, Clock3 } from "lucide-react";
import { StationStatus } from "../../types";

export interface Pm25SeverityInfo {
  label: string;
  class: string;
  color: string;
}

export function getPm25Severity(pm25: number | null | undefined): Pm25SeverityInfo {
  if (pm25 === null || pm25 === undefined) return { label: "Không khả dụng", class: "status-null", color: "var(--pm25-null)" };
  if (pm25 <= 25) return { label: "Tốt (Good)", class: "level-good", color: "var(--pm25-good)" };
  if (pm25 <= 50) return { label: "Trung bình (Moderate)", class: "level-moderate", color: "var(--pm25-moderate)" };
  if (pm25 <= 100) return { label: "Kém (Unhealthy)", class: "level-unhealthy", color: "var(--pm25-unhealthy)" };
  return { label: "Rất nguy hại (Hazardous)", class: "level-hazardous", color: "var(--pm25-hazardous)" };
}

export function getAqiSeverity(aqi: number | null | undefined): Pm25SeverityInfo {
  if (aqi === null || aqi === undefined) return { label: "AQI không khả dụng", class: "status-null", color: "var(--pm25-null)" };
  if (aqi <= 50) return { label: "AQI tốt", class: "level-good", color: "var(--pm25-good)" };
  if (aqi <= 100) return { label: "AQI trung bình", class: "level-moderate", color: "var(--pm25-moderate)" };
  if (aqi <= 150) return { label: "AQI kém cho nhóm nhạy cảm", class: "level-unhealthy", color: "var(--pm25-unhealthy)" };
  return { label: "AQI không tốt", class: "level-hazardous", color: "var(--pm25-hazardous)" };
}

interface DataQualityBadgeProps {
  status?: StationStatus;
  isStale?: boolean;
  pm25?: number | null;
  aqi?: number | null;
}

export const DataQualityBadge: React.FC<DataQualityBadgeProps> = ({
  status = "online",
  isStale = false,
  pm25 = null,
  aqi = null,
}) => {
  // Data quality precedence: invalid > offline > stale > PM2.5 severity
  if (status === "invalid") {
    return <span className="badge badge-invalid" title="Dữ liệu bị lỗi kiểm định"><AlertTriangle size={14} aria-hidden="true" /> Dữ liệu không hợp lệ</span>;
  }
  if (status === "offline") {
    return <span className="badge badge-offline" title="Trạm đang mất kết nối"><CircleOff size={14} aria-hidden="true" /> Trạm offline</span>;
  }
  if (isStale) {
    return <span className="badge badge-stale" title="Dữ liệu đã quá độ mới cho phép"><Clock3 size={14} aria-hidden="true" /> Dữ liệu cũ</span>;
  }

  const severity = aqi !== null && aqi !== undefined ? getAqiSeverity(aqi) : getPm25Severity(pm25);
  return (
    <span className={`badge ${severity.class}`}>
      <CheckCircle2 size={14} aria-hidden="true" /> {severity.label}
    </span>
  );
};

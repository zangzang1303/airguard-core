import React, { useMemo } from "react";
import { AlertTriangle, Bot, Calendar, CheckCircle2, Clock3, Database, RefreshCw, Wifi, WifiOff, X } from "lucide-react";

import { Alert, Station } from "../../types";
import { formatVnDateTime } from "../../utils/datetime";

interface TodaySummarySheetProps {
  stations: Station[];
  alerts: Alert[];
  loading: boolean;
  loadError: string | null;
  onClose: () => void;
  onOpenAiChat: () => void;
  onRetry: () => Promise<void>;
}

export const TodaySummarySheet: React.FC<TodaySummarySheetProps> = ({
  stations,
  alerts,
  loading,
  loadError,
  onClose,
  onOpenAiChat,
  onRetry,
}) => {
  const summary = useMemo(() => {
    const fresh = stations.filter((station) => station.status === "online" && !station.is_stale);
    const stale = stations.filter((station) => station.status === "stale" || station.is_stale);
    const offline = stations.filter((station) => station.status === "offline");
    const activeAlerts = alerts.filter((alert) => alert.status === "active");
    const recommendations = Array.from(
      new Map(
        activeAlerts
          .filter((alert) => Boolean(alert.recommendation))
          .map((alert) => [alert.alert_id, alert]),
      ).values(),
    );
    const latestUpdatedAt = fresh
      .map((station) => station.updated_at)
      .filter(Boolean)
      .sort((left, right) => new Date(right).getTime() - new Date(left).getTime())[0];

    return { fresh, stale, offline, activeAlerts, recommendations, latestUpdatedAt };
  }, [alerts, stations]);

  return (
    <div className="floating-bottom-sheet today-summary-sheet">
      <div className="sheet-header-row">
        <div className="sheet-title-group">
          <Calendar size={18} className="sheet-pin-icon" aria-hidden="true" />
          <div>
            <h3 className="sheet-title">Tổng quan môi trường hiện tại</h3>
            <span className="sheet-sub">
              {summary.latestUpdatedAt
                ? `Dữ liệu mới nhất ${formatVnDateTime(summary.latestUpdatedAt)}`
                : "Chưa có thời điểm đo hợp lệ"}
            </span>
          </div>
        </div>
        <button className="sheet-close-btn" onClick={onClose} aria-label="Đóng tổng quan môi trường">
          <X size={18} />
        </button>
      </div>

      {loadError && (
        <div className="today-state-message is-error" role="alert">
          <AlertTriangle size={17} aria-hidden="true" />
          <span>{loadError}</span>
          <button type="button" onClick={onRetry} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin-icon" : ""} aria-hidden="true" /> Thử lại
          </button>
        </div>
      )}

      <div className="today-status-grid" aria-label="Trạng thái dữ liệu trạm">
        <div><Wifi size={17} aria-hidden="true" /><strong>{summary.fresh.length}</strong><span>Online và fresh</span></div>
        <div><Clock3 size={17} aria-hidden="true" /><strong>{summary.stale.length}</strong><span>Dữ liệu cũ</span></div>
        <div><WifiOff size={17} aria-hidden="true" /><strong>{summary.offline.length}</strong><span>Offline</span></div>
        <div><AlertTriangle size={17} aria-hidden="true" /><strong>{summary.activeAlerts.length}</strong><span>Cảnh báo active</span></div>
      </div>

      <section className="today-grounded-section" aria-labelledby="today-recommendations-title">
        <div className="today-section-heading">
          <Database size={16} aria-hidden="true" />
          <h4 id="today-recommendations-title">Khuyến nghị cần lưu ý</h4>
        </div>
        {summary.recommendations.length === 0 ? (
          <div className="today-no-recommendation">
            <CheckCircle2 size={18} aria-hidden="true" />
            <span>Backend chưa trả về khuyến nghị active. Giao diện không tự suy diễn kết luận an toàn.</span>
          </div>
        ) : (
          <ul className="today-recommendation-list">
            {summary.recommendations.map((alert) => (
              <li key={alert.alert_id}>
                <strong>{alert.station_id} · {alert.title}</strong>
                <span>{alert.recommendation}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="today-simulator-note">
        Dữ liệu giả lập cho MVP — không phải quan trắc chính thức và không dùng cho quyết định y tế hoặc pháp lý.
      </p>

      <div className="today-footer-row">
        <button className="sheet-btn primary" onClick={onOpenAiChat}>
          <Bot size={15} aria-hidden="true" /> Hỏi AI về sinh hoạt
        </button>
      </div>
    </div>
  );
};

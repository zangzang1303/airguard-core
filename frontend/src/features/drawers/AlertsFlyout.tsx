import React, { useMemo, useState } from "react";
import { AlertTriangle, Bell, CheckCircle, MapPin, RefreshCw, X } from "lucide-react";

import { Alert, Station } from "../../types";
import { useDraggableFloatingPanel } from "../floating";

interface AlertsFlyoutProps {
  alerts: Alert[];
  stations: Station[];
  loading: boolean;
  loadError: string | null;
  onRetry: () => Promise<void>;
  onClose: () => void;
  onShowAlertOnMap: (stationId: string) => void;
}

const SEVERITY_LABEL: Record<Alert["severity"], string> = {
  good: "Tốt",
  moderate: "Theo dõi",
  warning: "Cảnh báo",
  critical: "Nghiêm trọng",
};

type SeverityFilter = "all" | Alert["severity"];

export const AlertsFlyout: React.FC<AlertsFlyoutProps> = ({
  alerts,
  stations,
  loading,
  loadError,
  onRetry,
  onClose,
  onShowAlertOnMap,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "alerts",
    group: "drawer",
  });

  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const activeAlerts = useMemo(
    () => alerts
      .filter((alert) => alert.status === "active")
      .filter((alert) => severityFilter === "all" || alert.severity === severityFilter)
      .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime()),
    [alerts, severityFilter],
  );

  return (
    <div {...containerProps} className="floating-flyout-card alerts-flyout">
      <div className="flyout-header-row">
        <div className="flyout-title-group" {...handleProps}>
          <Bell size={18} className="flyout-bell-icon" aria-hidden="true" />
          <h3 className="flyout-title">Cảnh báo môi trường</h3>
        </div>
        <button className="no-drag flyout-close-btn" data-no-drag="true" onClick={onClose} aria-label="Đóng danh sách cảnh báo">
          <X size={16} />
        </button>
      </div>

      <div className="alerts-filter-row no-drag" data-no-drag="true">
        <label htmlFor="map-alert-severity">Mức độ</label>
        <select
          id="map-alert-severity"
          value={severityFilter}
          onChange={(event) => setSeverityFilter(event.target.value as SeverityFilter)}
        >
          <option value="all">Tất cả</option>
          <option value="moderate">Theo dõi</option>
          <option value="warning">Cảnh báo</option>
          <option value="critical">Nghiêm trọng</option>
        </select>
        <button type="button" onClick={onRetry} disabled={loading} aria-label="Làm mới cảnh báo">
          <RefreshCw size={14} className={loading ? "spin-icon" : ""} aria-hidden="true" />
          <span>{loading ? "Đang tải" : "Làm mới"}</span>
        </button>
      </div>

      {loadError && (
        <div className="alerts-inline-error" role="alert">
          <AlertTriangle size={16} aria-hidden="true" />
          <span>Không thể đồng bộ cảnh báo mới. Danh sách hiện tại có thể đã cũ.</span>
        </div>
      )}

      <div className="alerts-list-scroll">
        {loading && alerts.length === 0 ? (
          <div className="alerts-loading-state" role="status">
            <RefreshCw size={24} className="spin-icon" aria-hidden="true" />
            <span>Đang tải cảnh báo từ backend…</span>
          </div>
        ) : activeAlerts.length === 0 ? (
          <div className="alerts-empty-state">
            <CheckCircle size={28} className="empty-check-icon" aria-hidden="true" />
            <div className="empty-title">Không có cảnh báo phù hợp</div>
            <p>
              {severityFilter === "all"
                ? "Backend chưa trả về cảnh báo active. Giao diện không tự kết luận khu vực an toàn."
                : "Hãy chọn mức độ khác hoặc đặt lại bộ lọc."}
            </p>
            {severityFilter !== "all" && (
              <button type="button" className="alert-map-btn" onClick={() => setSeverityFilter("all")}>Đặt lại bộ lọc</button>
            )}
          </div>
        ) : (
          activeAlerts.map((alert) => {
            const station = stations.find((item) => item.station_id === alert.station_id);

            return (
              <article key={alert.alert_id} className={`alert-card-item ${alert.severity}`}>
                <div className="alert-card-header">
                  <div className="alert-badge-wrap">
                    <AlertTriangle size={15} aria-hidden="true" />
                    <span className="alert-severity-text">{SEVERITY_LABEL[alert.severity]}</span>
                  </div>
                  <span className="alert-station-tag">{station?.station_name || alert.station_id}</span>
                </div>

                <div className="alert-card-body">
                  <h4 className="alert-title">{alert.title}</h4>
                  <p className="alert-desc">{alert.message}</p>
                  <div className="alert-meta-row">
                    Giá trị đo: <strong>{alert.observed_value ?? "—"} {alert.unit}</strong>
                    {alert.threshold != null && <> · Ngưỡng backend: {alert.threshold} {alert.unit}</>}
                  </div>
                  {alert.recommendation && <p className="alert-rule-recommendation">{alert.recommendation}</p>}
                </div>

                <div className="alert-card-footer">
                  <button
                    className="alert-map-btn"
                    onClick={() => onShowAlertOnMap(alert.station_id)}
                  >
                    <MapPin size={14} aria-hidden="true" />
                    <span>Xem trên bản đồ</span>
                  </button>
                </div>
              </article>
            );
          })
        )}
      </div>
    </div>
  );
};

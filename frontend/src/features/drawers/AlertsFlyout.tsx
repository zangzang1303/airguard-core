import React from "react";
import { X, Bell, AlertTriangle, MapPin, CheckCircle, Clock } from "lucide-react";
import { Alert, Station } from "../../types";

interface AlertsFlyoutProps {
  alerts: Alert[];
  stations: Station[];
  onClose: () => void;
  onShowAlertOnMap: (stationId: string) => void;
}

export const AlertsFlyout: React.FC<AlertsFlyoutProps> = ({
  alerts,
  stations,
  onClose,
  onShowAlertOnMap,
}) => {
  return (
    <div className="floating-flyout-card alerts-flyout">
      <div className="flyout-header-row">
        <div className="flyout-title-group">
          <Bell size={18} className="flyout-bell-icon" />
          <h3 className="flyout-title">Cảnh báo Môi trường Thời gian thực</h3>
        </div>
        <button className="flyout-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={16} />
        </button>
      </div>

      <div className="alerts-list-scroll">
        {alerts.length === 0 ? (
          <div className="alerts-empty-state">
            <CheckCircle size={28} className="empty-check-icon" />
            <div className="empty-title">Không có cảnh báo nguy hại</div>
            <p>Toàn bộ 5 trạm quan trắc quanh Vinhomes Ocean Park 1 đang hoạt động trong ngưỡng an toàn.</p>
          </div>
        ) : (
          alerts.map((alert) => {
            const station = stations.find((s) => s.station_id === alert.station_id);
            const isCritical = alert.severity === "critical";

            return (
              <div key={alert.alert_id} className={`alert-card-item ${alert.severity}`}>
                <div className="alert-card-header">
                  <div className="alert-badge-wrap">
                    <AlertTriangle size={15} />
                    <span className="alert-severity-text">
                      {isCritical ? "Cảnh báo Khẩn (Critical)" : "Cảnh báo Nhắc nhở (Warning)"}
                    </span>
                  </div>
                  <span className="alert-station-tag">{station?.station_name || alert.station_id}</span>
                </div>

                <div className="alert-card-body">
                  <h4 className="alert-title">{alert.title}</h4>
                  <p className="alert-desc">{alert.message || alert.recommendation}</p>

                  <div className="alert-meta-row">
                    <div className="meta-observed">
                      Giá trị đo: <strong>{alert.observed_value ?? "—"} {alert.unit}</strong> (Ngưỡng: {alert.threshold})
                    </div>
                  </div>
                </div>

                <div className="alert-card-footer">
                  <button
                    className="alert-map-btn"
                    onClick={() => {
                      if (alert.station_id) onShowAlertOnMap(alert.station_id);
                    }}
                  >
                    <MapPin size={14} />
                    <span>Xem vị trí trên bản đồ</span>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

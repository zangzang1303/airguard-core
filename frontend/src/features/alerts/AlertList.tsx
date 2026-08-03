import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Alert } from "../../types";

export const AlertList: React.FC = () => {
  const { navigateTo } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("active");

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        const data = await api.getAlerts();
        setAlerts(data);
      } catch (err) {
        console.error("Error fetching alerts:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAlerts();
  }, []);

  const filteredAlerts = alerts.filter(a => {
    if (filterSeverity !== "all" && a.severity !== filterSeverity) return false;
    if (filterStatus !== "all" && a.status !== filterStatus) return false;
    return true;
  });

  const handleFocusStation = (stationId: string) => {
    navigateTo("station-detail", { stationId });
  };

  return (
    <div className="alerts-container">
      <div className="alerts-header">
        <div>
          <h2>🔔 Danh sách Cảnh báo Môi trường (Alerts)</h2>
          <p className="alerts-subtitle">Theo dõi trạng thái vượt ngưỡng PM2.5 tại các trạm quan trắc</p>
        </div>
        <button className="btn-refresh" onClick={() => api.getAlerts().then(setAlerts)}>
          🔄 Làm mới
        </button>
      </div>

      {/* Filters */}
      <div className="alerts-filters">
        <div className="filter-group">
          <label>Trạng thái:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="role-select">
            <option value="all">Tất cả trạng thái</option>
            <option value="active">Đang kích hoạt (Active)</option>
            <option value="resolved">Đã giải quyết (Resolved)</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Mức độ nghiêm trọng:</label>
          <select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)} className="role-select">
            <option value="all">Tất cả mức độ</option>
            <option value="warning">Cảnh báo (Warning)</option>
            <option value="moderate">Trung bình (Moderate)</option>
            <option value="critical">Rất nghiêm trọng (Critical)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="skeleton-card" style={{ height: 250 }}></div>
      ) : filteredAlerts.length === 0 ? (
        <div className="empty-state">
          <span>✅ Không có cảnh báo nào phù hợp với bộ lọc.</span>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mã Alert</th>
                <th>Trạm ID</th>
                <th>Mức độ</th>
                <th>Nội dung thông báo</th>
                <th>Thực đo / Ngưỡng</th>
                <th>Thời gian kích hoạt</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((a) => (
                <tr key={a.alert_id}>
                  <td><strong>{a.alert_id}</strong></td>
                  <td>
                    <button className="btn-link" onClick={() => handleFocusStation(a.station_id)}>
                      📍 {a.station_id}
                    </button>
                  </td>
                  <td>
                    <span className={`badge level-${a.severity}`}>
                      {a.severity.toUpperCase()}
                    </span>
                  </td>
                  <td>{a.message}</td>
                  <td><strong>{a.observed_value}</strong> / {a.threshold} µg/m³</td>
                  <td>{new Date(a.created_at).toLocaleTimeString("vi-VN")}</td>
                  <td>
                    <span className={`status-pill ${a.status}`}>
                      {a.status === "active" ? "🔴 Active" : "🟢 Resolved"}
                    </span>
                  </td>
                  <td>
                    <button className="btn-secondary-sm" onClick={() => handleFocusStation(a.station_id)}>
                      Xem trạm
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

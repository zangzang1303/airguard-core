import React, { useEffect, useMemo, useState } from "react";
import { MapPin, RefreshCw, TriangleAlert } from "lucide-react";
import { api } from "../../api/client";
import { AlertFilters } from "../../components/common/AlertFilters";
import { Button } from "../../components/common/Button";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { Alert, Station } from "../../types";

export const AlertList: React.FC = () => {
  const { navigateTo } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterStatus, setFilterStatus] = useState("active");

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const [alertData, stationData] = await Promise.all([api.getAlerts(), api.getStations()]);
      setAlerts(alertData);
      setStations(stationData);
    } catch {
      setError("Không thể tải danh sách cảnh báo. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const stationNames = useMemo(
    () => new Map(stations.map((station) => [station.station_id, station.station_name])),
    [stations],
  );

  const filteredAlerts = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("vi");
    return alerts.filter((alert) => {
      const stationName = stationNames.get(alert.station_id) ?? "";
      const matchesSearch = !query
        || alert.station_id.toLocaleLowerCase("vi").includes(query)
        || stationName.toLocaleLowerCase("vi").includes(query);
      const matchesSeverity = filterSeverity === "all" || alert.severity === filterSeverity;
      const matchesStatus = filterStatus === "all" || alert.status === filterStatus;
      return matchesSearch && matchesSeverity && matchesStatus;
    });
  }, [alerts, filterSeverity, filterStatus, search, stationNames]);

  const handleFocusStation = (stationId: string) => {
    navigateTo("station-detail", { stationId });
  };

  return (
    <div className="alerts-container">
      <PageHeader
        title="Cảnh báo"
        description="Theo dõi cảnh báo PM2.5 đang kích hoạt và lịch sử xử lý tại các trạm."
        actions={(
          <Button variant="outline" size="sm" onClick={fetchAlerts} disabled={loading}>
            <RefreshCw className={loading ? "is-spinning" : ""} size={16} aria-hidden="true" />
            {loading ? "Đang làm mới" : "Làm mới"}
          </Button>
        )}
      />

      <AlertFilters
        search={search}
        status={filterStatus}
        severity={filterSeverity}
        onSearchChange={setSearch}
        onStatusChange={setFilterStatus}
        onSeverityChange={setFilterSeverity}
        onReset={() => {
          setSearch("");
          setFilterStatus("active");
          setFilterSeverity("all");
        }}
      />

      {error && (
        <div className="alert-box alert-error">
          <TriangleAlert size={17} aria-hidden="true" />
          {error}
        </div>
      )}

      {loading && alerts.length === 0 ? (
        <div className="skeleton-card" style={{ height: 250 }} />
      ) : filteredAlerts.length === 0 ? (
        <div className="empty-state">Không có cảnh báo phù hợp với bộ lọc.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mã cảnh báo</th>
                <th>Trạm</th>
                <th>Mức độ</th>
                <th>Nội dung</th>
                <th>Thực đo / Ngưỡng</th>
                <th>Thời gian</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert) => (
                <tr key={alert.alert_id}>
                  <td><strong>{alert.alert_id}</strong></td>
                  <td>
                    <button className="btn-link table-station-link" onClick={() => handleFocusStation(alert.station_id)}>
                      <MapPin size={15} aria-hidden="true" />
                      <span>{stationNames.get(alert.station_id) ?? alert.station_id}</span>
                    </button>
                  </td>
                  <td><span className={`badge level-${alert.severity}`}>{alert.severity.toUpperCase()}</span></td>
                  <td>{alert.message}</td>
                  <td><strong>{alert.observed_value}</strong> / {alert.threshold} µg/m³</td>
                  <td>{new Date(alert.created_at).toLocaleString("vi-VN")}</td>
                  <td><StatusBadge status={alert.status} /></td>
                  <td>
                    <Button variant="outline" size="sm" onClick={() => handleFocusStation(alert.station_id)}>
                      Xem trạm
                    </Button>
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

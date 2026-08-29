import React, { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Lightbulb, MapPin, RefreshCw, TriangleAlert } from "lucide-react";
import { api } from "../../api/client";
import { AlertFilters } from "../../components/common/AlertFilters";
import { Button } from "../../components/common/Button";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { Alert, PredictiveWarningDetail, Station } from "../../types";
import { SEVERITY_LABEL, formatVnDateTime } from "../../utils/datetime";

const CHECKLIST_LABELS: Record<string, string> = {
  close_windows: "Đóng cửa sổ và cửa ban công",
  bring_laundry_inside: "Đưa quần áo đang phơi vào trong",
  reduce_outdoor_activity: "Cân nhắc giảm hoạt động ngoài trời",
  check_air_purifier: "Kiểm tra máy lọc không khí",
};

export const PredictiveWarningCard: React.FC<{
  episodeId: string;
  onFocusStation?: (stationId: string) => void;
}> = ({ episodeId, onFocusStation }) => {
  const { role } = useAuth();
  const [detail, setDetail] = useState<PredictiveWarningDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingItem, setSavingItem] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.getPredictiveWarning(episodeId)
      .then((response) => { if (active) setDetail(response); })
      .catch(() => { if (active) setError("Không thể tải chi tiết cảnh báo dự báo."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [episodeId]);

  const updateChecklist = async (itemKey: string, completed: boolean) => {
    if (!detail || role !== "resident") return;
    setSavingItem(itemKey);
    setError(null);
    try {
      const response = await api.updatePredictiveWarningChecklist(episodeId, itemKey, completed);
      setDetail({
        ...detail,
        checklist: detail.checklist.map((item) => item.item_key === itemKey ? response.item : item),
      });
    } catch {
      setError("Không thể lưu checklist. Hãy kiểm tra phiên đăng nhập và thử lại.");
    } finally {
      setSavingItem(null);
    }
  };

  if (loading) return <div className="skeleton-card skeleton-card--md" role="status" aria-label="Đang tải cảnh báo dự báo" />;
  if (error && !detail) return <div className="alert-box alert-error" role="alert">{error}</div>;
  if (!detail) return <div className="empty-state">Không có dữ liệu cảnh báo dự báo.</div>;

  const episode = detail.episode;
  return (
    <section className={`profile-card predictive-warning-detail level-${episode.severity}`}>
      <div className="profile-section-heading profile-section-heading--compact">
        <TriangleAlert size={22} aria-hidden="true" />
        <div>
          <span className="dashboard-eyebrow">Cảnh báo dự báo · {episode.status}</span>
          <h2>{episode.station_id} · PM2.5 {episode.predicted_value} µg/m³</h2>
          <p>
            Khoảng {episode.predicted_min}–{episode.predicted_max} µg/m³ · độ tin cậy {Math.round(episode.confidence * 100)}%
          </p>
        </div>
      </div>
      <p>Nguồn: {episode.source} · Model: {episode.model_version} · Policy: {episode.policy_version}</p>
      <p>{detail.disclaimer}</p>
      {onFocusStation && (
        <Button type="button" variant="outline" size="sm" onClick={() => onFocusStation(episode.station_id)}>
          <MapPin size={15} aria-hidden="true" /> Xem trạm trên bản đồ
        </Button>
      )}
      <fieldset className="predictive-checklist">
        <legend>Checklist hành động cá nhân</legend>
        {detail.checklist.map((item) => (
          <label key={item.item_key}>
            <input
              type="checkbox"
              checked={item.completed}
              disabled={role !== "resident" || savingItem === item.item_key}
              onChange={(event) => updateChecklist(item.item_key, event.target.checked)}
            />
            <span>{CHECKLIST_LABELS[item.item_key] ?? item.item_key}</span>
            {item.completed && <CheckCircle2 size={15} aria-label="Đã hoàn thành" />}
          </label>
        ))}
      </fieldset>
      {role !== "resident" && <p className="text-muted">Manager chỉ có quyền xem checklist.</p>}
      {error && <div className="alert-box alert-error" role="alert">{error}</div>}
    </section>
  );
};

export const AlertList: React.FC = () => {
  const { navigateTo } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterStatus, setFilterStatus] = useState("active");
  const predictiveWarningId = typeof window === "undefined"
    ? null
    : new URLSearchParams(window.location.search).get("predictive_warning_id");

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

  const [sortBy, setSortBy] = useState<"newest" | "severity">("newest");

  const stationNames = useMemo(
    () => new Map(stations.map((station) => [station.station_id, station.station_name])),
    [stations],
  );

  const severityRank: Record<string, number> = {
    critical: 4,
    warning: 3,
    moderate: 2,
    good: 1,
  };

  const filteredAlerts = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("vi");
    const result = alerts.filter((alert) => {
      const stationName = stationNames.get(alert.station_id) ?? "";
      const matchesSearch = !query
        || alert.station_id.toLocaleLowerCase("vi").includes(query)
        || stationName.toLocaleLowerCase("vi").includes(query);
      const matchesSeverity = filterSeverity === "all" || alert.severity === filterSeverity;
      const matchesStatus = filterStatus === "all" || alert.status === filterStatus;
      return matchesSearch && matchesSeverity && matchesStatus;
    });

    return result.sort((a, b) => {
      if (sortBy === "severity") {
        const rankDiff = (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0);
        if (rankDiff !== 0) return rankDiff;
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [alerts, filterSeverity, filterStatus, search, sortBy, stationNames]);


  const handleFocusStation = (stationId: string) => {
    navigateTo("station-detail", { stationId });
  };

  const measurementLabel = (alert: Alert) => {
    const unit = alert.unit ? ` ${alert.unit}` : "";
    if (alert.observed_value == null || alert.threshold == null) return "Không có số đo";
    return `${alert.observed_value}${unit} / ${alert.threshold}${unit}`;
  };

  return (
    <div className="alerts-container">
      <PageHeader
        title="Cảnh báo"
        description="Theo dõi cảnh báo AQI và các chỉ số môi trường; mỗi cảnh báo có khuyến nghị vận hành từ Rule Engine."
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
        sortBy={sortBy}
        onSearchChange={setSearch}
        onStatusChange={setFilterStatus}
        onSeverityChange={setFilterSeverity}
        onSortByChange={setSortBy}
        onReset={() => {
          setSearch("");
          setFilterStatus("active");
          setFilterSeverity("all");
          setSortBy("newest");
        }}
      />

      {predictiveWarningId && (
        <PredictiveWarningCard episodeId={predictiveWarningId} onFocusStation={handleFocusStation} />
      )}


      {error && (
        <div className="alert-box alert-error">
          <TriangleAlert size={17} aria-hidden="true" />
          {error}
        </div>
      )}

      {loading && alerts.length === 0 ? (
        <div className="skeleton-card skeleton-card--md" role="status" aria-label="Đang tải danh sách cảnh báo" />
      ) : filteredAlerts.length === 0 ? (
        <div className="empty-state">Không có cảnh báo phù hợp với bộ lọc.</div>
      ) : (
        <div
          className="table-wrapper"
          tabIndex={0}
          role="region"
          aria-label="Bảng danh sách cảnh báo, có thể cuộn ngang"
        >
          <table className="data-table data-table--cards">
            <thead>
              <tr>
                <th>Mã cảnh báo</th>
                <th>Trạm</th>
                <th>Mức độ</th>
                <th>Chỉ số / nội dung</th>
                <th>Thực đo / Ngưỡng</th>
                <th>Khuyến nghị</th>
                <th>Thời gian</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert) => (
                <tr key={alert.alert_id}>
                  <td data-label="Mã cảnh báo"><strong>{alert.alert_id}</strong></td>
                  <td data-label="Trạm">
                    <button
                      type="button"
                      className="btn-link table-station-link"
                      onClick={() => handleFocusStation(alert.station_id)}
                    >
                      <MapPin size={15} aria-hidden="true" />
                      <span>{stationNames.get(alert.station_id) ?? alert.station_id}</span>
                    </button>
                  </td>
                  <td data-label="Mức độ">
                    <span className={`badge level-${alert.severity}`}>
                      {SEVERITY_LABEL[alert.severity] ?? alert.severity}
                    </span>
                  </td>
                  <td data-label="Chỉ số / nội dung"><strong>{alert.title}</strong><br /><small>{alert.message}</small></td>
                  <td data-label="Thực đo / Ngưỡng"><strong>{measurementLabel(alert)}</strong></td>
                  <td data-label="Khuyến nghị">
                    {alert.recommendation ? <span className="alert-recommendation"><Lightbulb size={15} aria-hidden="true" />{alert.recommendation}</span> : "—"}
                  </td>
                  <td data-label="Thời gian">{formatVnDateTime(alert.created_at)}</td>
                  <td data-label="Trạng thái"><StatusBadge status={alert.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Calendar,
  CheckCircle2,
  Download,
  FileText,
  Info,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { api } from "../../api/client";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import {
  Report,
  ReportExportFormat,
  ReportStatus,
  ReportType,
  VentilationEffectivenessOutcome,
} from "../../types";

const REPORT_TIMEZONE = "Asia/Ho_Chi_Minh";

const statusLabels: Record<ReportStatus, string> = {
  generating: "ĐANG TẠO",
  completed: "HOÀN TẤT",
  failed: "THẤT BẠI",
};

const trendLabels: Record<Report["statistics"]["trends"]["direction"], string> = {
  improving: "Cải thiện",
  worsening: "Xấu đi",
  stable: "Ổn định",
  insufficient_data: "Chưa đủ dữ liệu",
};

const effectivenessLabels: Record<VentilationEffectivenessOutcome, string> = {
  improved: "Cải thiện",
  worsened: "Xấu đi",
  mixed: "Kết quả hỗn hợp",
  insufficient_data: "Chưa đủ dữ liệu đánh giá",
};

function formatNumber(value: number | null | undefined, fractionDigits = 1): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("vi-VN", {
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function formatPeriod(report: Report): string {
  return `${formatTimestamp(report.period_start)} – ${formatTimestamp(report.period_end)}`;
}

function formatBreakdown(values: Record<string, number>): string {
  const entries = Object.entries(values);
  if (!entries.length) return "—";
  return entries.map(([key, value]) => `${key}: ${value}`).join(" · ");
}

function errorText(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  return "Không thể tải dữ liệu báo cáo từ server.";
}

export const ReportViewer: React.FC = () => {
  const { role } = useAuth();
  const isManagerOrAdmin = role === "manager" || role === "admin";

  const [activeTab, setActiveTab] = useState<ReportType>("daily");
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [report, setReport] = useState<Report | null>(null);
  const [exportFormat, setExportFormat] = useState<ReportExportFormat>("pdf");
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isManagerOrAdmin) return undefined;

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      setReports([]);
      setSelectedReportId("");
      setReport(null);

      try {
        const items = await api.getReports(activeTab);
        if (cancelled) return;
        setReports(items);

        const first = items[0];
        if (!first) return;

        setSelectedReportId(first.report_id);
        setDetailLoading(true);
        const detail = await api.getReport(first.report_id);
        if (!cancelled) setReport(detail);
      } catch (loadError) {
        if (!cancelled) setError(errorText(loadError));
      } finally {
        if (!cancelled) {
          setLoading(false);
          setDetailLoading(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [activeTab, isManagerOrAdmin]);

  const refreshReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await api.getReports(activeTab);
      setReports(items);
      const selected =
        items.find((item) => item.report_id === selectedReportId) ?? items[0] ?? null;
      setSelectedReportId(selected?.report_id ?? "");
      if (!selected) {
        setReport(null);
        return;
      }
      setDetailLoading(true);
      setReport(await api.getReport(selected.report_id));
    } catch (refreshError) {
      setError(errorText(refreshError));
    } finally {
      setLoading(false);
      setDetailLoading(false);
    }
  };

  const selectReport = async (reportId: string) => {
    setSelectedReportId(reportId);
    setDetailLoading(true);
    setError(null);
    try {
      setReport(await api.getReport(reportId));
    } catch (detailError) {
      setReport(null);
      setError(errorText(detailError));
    } finally {
      setDetailLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    setError(null);
    try {
      const generated = await api.generateReport({
        type: activeTab,
        timezone: REPORT_TIMEZONE,
      });
      setReport(generated);
      setSelectedReportId(generated.report_id);
      setReports((current) => [
        generated,
        ...current.filter((item) => item.report_id !== generated.report_id),
      ]);
    } catch (generationError) {
      setError(errorText(generationError));
    } finally {
      setGenerating(false);
    }
  };

  const downloadReport = async () => {
    if (!report || report.status !== "completed") return;
    setDownloading(true);
    setError(null);
    try {
      const exported = await api.exportReport(report.report_id, exportFormat);
      const url = URL.createObjectURL(exported.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = exported.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (downloadError) {
      setError(errorText(downloadError));
    } finally {
      setDownloading(false);
    }
  };

  if (!isManagerOrAdmin) {
    return (
      <div className="report-viewer-container">
        <PageHeader
          title="Báo cáo Môi trường Định kỳ"
          description="Báo cáo tổng hợp chất lượng môi trường cho Ban Quản lý."
        />
        <div className="alert-box alert-warning" role="alert">
          <ShieldAlert size={18} />
          <span>Màn hình này chỉ dành cho tài khoản Manager hoặc Admin.</span>
        </div>
      </div>
    );
  }

  const measurements = report?.statistics.measurements;
  const trends = report?.statistics.trends;
  const alerts = report?.statistics.alerts;
  const proposals = report?.statistics.proposals;
  const ventilation = report?.statistics.ventilation;
  const dataQuality = report?.statistics.data_quality;

  return (
    <div className="report-viewer-container">
      <PageHeader
        title="Báo cáo Môi trường Định kỳ"
        description="Dữ liệu báo cáo Daily/Weekly do backend tổng hợp từ bằng chứng đã lưu."
        actions={
          <div className="report-header-actions">
            <button
              type="button"
              className="btn btn-outline report-action-btn"
              onClick={generateReport}
              disabled={generating}
            >
              {generating ? <RefreshCw size={15} className="spin-icon" /> : <FileText size={15} />}
              <span>{generating ? "Đang tạo..." : "Tạo báo cáo"}</span>
            </button>

            <select
              className="report-export-select"
              aria-label="Định dạng xuất báo cáo"
              value={exportFormat}
              onChange={(event) => setExportFormat(event.target.value as ReportExportFormat)}
              disabled={!report || report.status !== "completed" || downloading}
            >
              <option value="pdf">PDF</option>
              <option value="html">HTML</option>
              <option value="markdown">Markdown</option>
            </select>
            <button
              type="button"
              className="btn btn-outline report-action-btn"
              onClick={downloadReport}
              disabled={!report || report.status !== "completed" || downloading}
            >
              {downloading ? <RefreshCw size={15} className="spin-icon" /> : <Download size={15} />}
              <span>{downloading ? "Đang tải..." : "Tải báo cáo"}</span>
            </button>
          </div>
        }
      />

      <div className="alert-box alert-info report-simulator-banner" role="status">
        <Info size={18} />
        <span>
          Dữ liệu MVP có nguồn từ simulator, không phải quan trắc chính thức và không dùng cho
          chẩn đoán y tế hay quyết định pháp lý.
        </span>
      </div>

      <div className="report-controls-bar">
        <div className="report-tabs" role="tablist" aria-label="Loại báo cáo">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "daily"}
            className={`report-tab-btn ${activeTab === "daily" ? "is-active" : ""}`}
            onClick={() => setActiveTab("daily")}
          >
            <Calendar size={15} />
            <span>Hàng ngày</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "weekly"}
            className={`report-tab-btn ${activeTab === "weekly" ? "is-active" : ""}`}
            onClick={() => setActiveTab("weekly")}
          >
            <BarChart3 size={15} />
            <span>Hàng tuần</span>
          </button>
        </div>

        <div className="report-filter-group">
          <label htmlFor="report-period-select" className="sr-only">
            Chọn kỳ báo cáo
          </label>
          <select
            id="report-period-select"
            className="report-period-select"
            value={selectedReportId}
            onChange={(event) => void selectReport(event.target.value)}
            disabled={loading || reports.length === 0}
          >
            {reports.length === 0 ? (
              <option value="">Chưa có báo cáo</option>
            ) : (
              reports.map((item) => (
                <option key={item.report_id} value={item.report_id}>
                  {formatPeriod(item)} · {statusLabels[item.status]}
                </option>
              ))
            )}
          </select>
          <button
            type="button"
            className="btn btn-outline report-refresh-btn"
            onClick={() => void refreshReports()}
            disabled={loading || detailLoading}
            aria-label="Làm mới danh sách báo cáo"
          >
            <RefreshCw size={15} className={loading ? "spin-icon" : ""} />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="report-error-state" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="report-content-card">
        {loading || detailLoading ? (
          <div className="report-loading-state" role="status">
            <RefreshCw size={24} className="spin-icon" />
            <span>Đang tải dữ liệu báo cáo từ server...</span>
          </div>
        ) : !report ? (
          <div className="report-empty-state">
            <FileText size={28} />
            <strong>Chưa có báo cáo {activeTab === "daily" ? "hàng ngày" : "hàng tuần"}.</strong>
            <span>Chọn “Tạo báo cáo” để backend tổng hợp dữ liệu cho kỳ gần nhất.</span>
          </div>
        ) : (
          <>
            <div className="report-card-header">
              <div className="report-meta-tag">
                <FileText size={16} />
                <span>{report.report_type === "daily" ? "BÁO CÁO HÀNG NGÀY" : "BÁO CÁO HÀNG TUẦN"}</span>
              </div>
              <span className={`report-status-badge report-status-${report.status}`}>
                {statusLabels[report.status]}
              </span>
            </div>

            <div className="report-card-body">
              <div className="report-document-header">
                <h3>Báo cáo tổng hợp chất lượng môi trường</h3>
                <div className="document-sub-meta">
                  <span>Kỳ: {formatPeriod(report)}</span>
                  <span>•</span>
                  <span>Múi giờ: {report.timezone}</span>
                  <span>•</span>
                  <span>Tạo lúc: {formatTimestamp(report.created_at)}</span>
                </div>
                <div className="document-sub-meta">
                  <span>Chế độ: {report.generation_mode}</span>
                  <span>•</span>
                  <span>Nguồn mô hình: {report.model_source || "—"}</span>
                  {report.reused && (
                    <>
                      <span>•</span>
                      <span>Dùng lại báo cáo đã lưu</span>
                    </>
                  )}
                </div>
              </div>

              {report.status === "generating" && (
                <div className="alert-box alert-info" role="status">
                  <RefreshCw size={16} className="spin-icon" />
                  <span>Backend đang tạo báo cáo. Dùng “Làm mới” để kiểm tra trạng thái mới nhất.</span>
                </div>
              )}

              {report.status === "failed" && (
                <div className="alert-box alert-error" role="alert">
                  <AlertTriangle size={16} />
                  <span>
                    Tạo báo cáo thất bại
                    {report.failure_code ? ` (mã: ${report.failure_code})` : ""}.
                  </span>
                </div>
              )}

              <section className="report-section-block">
                <h4>1. Tổng quan dữ liệu</h4>
                <div className="report-kpi-grid">
                  <div>
                    <span>Mẫu hợp lệ</span>
                    <strong>{measurements?.valid_sample_count ?? 0}</strong>
                  </div>
                  <div>
                    <span>Mẫu bị loại</span>
                    <strong>{measurements?.excluded_sample_count ?? 0}</strong>
                  </div>
                  <div>
                    <span>AQI trung bình</span>
                    <strong>{formatNumber(measurements?.overall_avg_aqi)}</strong>
                  </div>
                  <div>
                    <span>AQI cao nhất</span>
                    <strong>{formatNumber(measurements?.overall_max_aqi)}</strong>
                  </div>
                </div>
                <p>
                  Số trạm có dữ liệu: <strong>{measurements?.station_count ?? 0}</strong>
                  {" · "}Trạm có AQI cao nhất: <strong>{measurements?.worst_station_id || "—"}</strong>
                  {" · "}Xu hướng: <strong>{trends ? trendLabels[trends.direction] : "—"}</strong>
                </p>
              </section>

              <section className="report-section-block">
                <h4>2. Thống kê theo trạm</h4>
                {measurements?.stations.length ? (
                  <div className="report-summary-table-wrapper">
                    <table className="report-summary-table" aria-label="Thống kê môi trường theo trạm">
                      <thead>
                        <tr>
                          <th>Trạm</th>
                          <th>Số mẫu</th>
                          <th>AQI TB / Max</th>
                          <th>PM2.5 TB / Max</th>
                          <th>CO₂ TB / Max</th>
                          <th>Tiếng ồn TB / Max</th>
                          <th>Nhiệt độ TB / Max</th>
                        </tr>
                      </thead>
                      <tbody>
                        {measurements.stations.map((station) => (
                          <tr key={station.station_id}>
                            <td>{station.station_id}</td>
                            <td>{station.sample_count}</td>
                            <td>{formatNumber(station.avg_aqi)} / {formatNumber(station.max_aqi)}</td>
                            <td>{formatNumber(station.avg_pm25)} / {formatNumber(station.max_pm25)}</td>
                            <td>{formatNumber(station.avg_co2)} / {formatNumber(station.max_co2)}</td>
                            <td>{formatNumber(station.avg_noise_db)} / {formatNumber(station.max_noise_db)}</td>
                            <td>{formatNumber(station.avg_temperature)} / {formatNumber(station.max_temperature)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>Không có mẫu hợp lệ theo trạm trong kỳ báo cáo này.</p>
                )}
              </section>

              <section className="report-section-block">
                <h4>3. Cảnh báo, đề xuất và thông gió</h4>
                <p>
                  Cảnh báo: <strong>{alerts?.total_count ?? 0}</strong>
                  {" · "}Theo loại: {alerts ? formatBreakdown(alerts.by_type) : "—"}
                  {" · "}Theo mức độ: {alerts ? formatBreakdown(alerts.by_severity) : "—"}
                </p>
                <p>
                  Đề xuất: <strong>{proposals?.total_count ?? 0}</strong>
                  {" · "}Theo trạng thái: {proposals ? formatBreakdown(proposals.by_status) : "—"}
                  {" · "}Theo hành động: {proposals ? formatBreakdown(proposals.by_action) : "—"}
                </p>
                <p>
                  Lượt kích hoạt thông gió: <strong>{ventilation?.activation_count ?? 0}</strong>
                  {" · "}Tổng thời lượng: <strong>{formatNumber(ventilation?.total_duration_minutes, 0)} phút</strong>
                  {" · "}Theo hành động: {ventilation ? formatBreakdown(ventilation.by_action) : "—"}
                </p>
                {ventilation && (
                  <div className="report-effectiveness-note">
                    <CheckCircle2 size={16} />
                    <span>
                      Hiệu quả: <strong>{effectivenessLabels[ventilation.effectiveness.outcome]}</strong>
                      {" · "}Chu kỳ đủ dữ liệu: {ventilation.effectiveness.evaluated_cycle_count}
                      {" · "}Thay đổi PM2.5 trung bình: {formatNumber(ventilation.effectiveness.mean_pm25_change)} µg/m³
                      {" · "}Thay đổi CO₂ trung bình: {formatNumber(ventilation.effectiveness.mean_co2_change)} ppm
                    </span>
                  </div>
                )}
              </section>

              <section className="report-section-block">
                <h4>4. Nhận định có căn cứ</h4>
                <div className="report-narrative">
                  {report.narrative || "Backend chưa cung cấp phần nhận định cho báo cáo này."}
                </div>
              </section>

              <div className="report-disclaimer-footer">
                <small>
                  Nguồn dữ liệu: {dataQuality?.source_labels?.join(", ") || "không được backend cung cấp"}.
                  {" "}{dataQuality?.disclaimer || "Dữ liệu simulator cho MVP, không phải quan trắc chính thức."}
                </small>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

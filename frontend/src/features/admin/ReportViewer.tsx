import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Calendar,
  CheckCircle2,
  Database,
  Download,
  FileCheck2,
  FileText,
  Info,
  Leaf,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { api } from "../../api/client";
import { PageHeader } from "../../components/common/PageHeader";
import { useAuth } from "../../context/AuthContext";
import { WeeklyMatrixChart } from "./WeeklyMatrixChart";
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

const estimateStatusLabels: Record<"complete" | "insufficient_data", string> = {
  complete: "Đã có dữ liệu ước tính",
  insufficient_data: "Chưa đủ dữ liệu để ước tính",
};

const estimateReasonLabels: Record<string, string> = {
  no_acknowledged_boost_cycles: "Chưa có chu kỳ tăng cường thông gió được xác nhận.",
  no_acknowledged_eco_intervals: "Chưa có khoảng thời gian tiết kiệm năng lượng được xác nhận.",
  insufficient_acknowledged_duration: "Thời lượng vận hành được xác nhận chưa đủ để ước tính.",
};

const qcvnStatusLabels: Record<"not_comparable" | "insufficient_data", string> = {
  not_comparable: "Không đối chiếu trực tiếp",
  insufficient_data: "Chưa đủ dữ liệu",
};

const whoStatusLabels: Record<"below_reference" | "above_reference" | "insufficient_data", string> = {
  below_reference: "Dưới mức tham chiếu",
  above_reference: "Trên mức tham chiếu",
  insufficient_data: "Chưa đủ dữ liệu",
};

function formatEstimateReason(reasonCode: string | null): string | null {
  if (!reasonCode) return null;
  return estimateReasonLabels[reasonCode] ?? "Chưa có đủ dữ liệu đầu vào để thực hiện ước tính.";
}

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

function buildReaderSummary(report: Report): Array<{ label: string; value: string; detail: string; tone: string }> {
  const { measurements, alerts, ventilation, trends } = report.statistics;
  const trend = trendLabels[trends.direction] ?? "Chưa đủ dữ liệu";
  return [
    {
      label: "Dữ liệu đủ điều kiện",
      value: `${formatNumber(measurements.valid_sample_count, 0)} mẫu hợp lệ`,
      detail: `${formatNumber(measurements.excluded_sample_count, 0)} mẫu bị loại khỏi tổng hợp.`,
      tone: "data",
    },
    {
      label: "Chất lượng không khí",
      value: `AQI trung bình ${formatNumber(measurements.overall_avg_aqi)}`,
      detail: `Trạm có AQI cao nhất: ${measurements.worst_station_id || "chưa xác định"}.`,
      tone: "air",
    },
    {
      label: "Cảnh báo và vận hành",
      value: `${formatNumber(alerts.total_count, 0)} cảnh báo`,
      detail: `${formatNumber(ventilation.activation_count, 0)} lượt thông gió đã được xác nhận.`,
      tone: "operations",
    },
    {
      label: "Xu hướng quan sát",
      value: trend,
      detail: "Chỉ mô tả mẫu trong dữ liệu đã lưu; không kết luận nguyên nhân.",
      tone: "trend",
    },
  ];
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

  const downloadReport = async (format = exportFormat) => {
    if (!report || report.status !== "completed") return;
    setDownloading(true);
    setError(null);
    try {
      const exported = await api.exportReport(report.report_id, format);
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
  const esgMetrics = report?.statistics.esg_metrics;
  const referenceComparison = report?.statistics.reference_comparison;
  const weeklyMatrix = report?.statistics.weekly_matrix;
  const isLegacyReport = Boolean(report && report.schema_version !== "b7-esg-reports-v1");
  const readerSummary = report ? buildReaderSummary(report) : [];
  const hasMultipleReports = reports.length > 1;

  return (
    <div className="report-viewer-container">
      <header className="report-hero">
        <div className="report-hero-copy">
          <div className="report-eyebrow">
            <Sparkles size={15} aria-hidden="true" />
            <span>AirGuard Intelligence · ESG Reporting</span>
          </div>
          <h1>Báo cáo Môi trường Định kỳ</h1>
          <p>
            Không gian tổng hợp Daily/Weekly dành cho Ban Quản lý, được dựng từ bằng chứng đã lưu
            và giữ nguyên dấu vết xuất bản.
          </p>
          <div className="report-trust-row" aria-label="Thuộc tính tin cậy của báo cáo">
            <span><Database size={14} /> Bằng chứng từ backend</span>
            <span><ShieldCheck size={14} /> Kiểm tra toàn vẹn SHA-256</span>
            <span><FileCheck2 size={14} /> Sẵn sàng xuất bản</span>
          </div>
        </div>

        <div className="report-hero-panel">
          <span className="report-hero-panel-label">Trung tâm xuất bản</span>
          <div className="report-header-actions">
            <button
              type="button"
              className="btn report-action-btn report-action-primary"
              onClick={generateReport}
              disabled={generating}
            >
              {generating ? <RefreshCw size={15} className="spin-icon" /> : <FileText size={15} />}
              <span>{generating ? "Đang tạo..." : "Tạo báo cáo"}</span>
            </button>

          </div>
          <small>Tải PDF ở thanh công cụ bên dưới sau khi chọn kỳ báo cáo.</small>
        </div>
      </header>

      <div className="alert-box alert-info report-simulator-banner" role="status">
        <span className="report-banner-icon"><Info size={18} /></span>
        <div>
          <strong>Phạm vi sử dụng dữ liệu</strong>
          <span>
            Dữ liệu MVP có nguồn từ simulator, không phải quan trắc chính thức và không dùng cho
            chẩn đoán y tế hay quyết định pháp lý.
          </span>
        </div>
      </div>

      <section className="report-download-toolbar" aria-label="Tải báo cáo đã chọn">
        <div className="report-download-toolbar-copy">
          <span className="report-download-toolbar-icon"><FileText size={18} /></span>
          <div><strong>Tải báo cáo</strong><span>Chọn định dạng tệp trước khi tải xuống.</span></div>
        </div>
        <div className="report-download-toolbar-actions">
          <label htmlFor="report-export-format" className="sr-only">Định dạng tải</label>
          <select id="report-export-format" className="report-export-select" value={exportFormat} onChange={(event) => setExportFormat(event.target.value as ReportExportFormat)} disabled={!report || report.status !== "completed" || downloading}>
            <option value="pdf">PDF</option><option value="html">Trang HTML</option><option value="markdown">Markdown</option>
          </select>
          <button type="button" className="btn report-download-btn" onClick={() => void downloadReport()} disabled={!report || report.status !== "completed" || downloading}>
            {downloading ? <RefreshCw size={16} className="spin-icon" /> : <Download size={16} />}
            <span>{downloading ? "Đang tải tệp..." : "Tải tệp"}</span>
          </button>
        </div>
      </section>

      <div className="report-controls-bar">
        <div className="report-control-cluster">
          <span className="report-control-label">Chu kỳ báo cáo</span>
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
        </div>

        <div className="report-control-cluster report-period-cluster">
          <span className="report-control-label">
            {hasMultipleReports ? "Chọn kỳ báo cáo" : "Báo cáo đang xem"}
          </span>
          <div className="report-filter-group">
            {hasMultipleReports ? (
              <>
                <label htmlFor="report-period-select" className="sr-only">
                  Chọn kỳ báo cáo
                </label>
                <select
                  id="report-period-select"
                  className="report-period-select"
                  value={selectedReportId}
                  onChange={(event) => void selectReport(event.target.value)}
                  disabled={loading}
                >
                  {reports.map((item) => (
                    <option key={item.report_id} value={item.report_id}>
                      {formatPeriod(item)} · {statusLabels[item.status]}
                    </option>
                  ))}
                </select>
              </>
            ) : (
              <span className="report-current-period" aria-live="polite">
                {report ? `Đang xem báo cáo: ${formatPeriod(report)}` : "Chưa có báo cáo đã lưu"}
              </span>
            )}
            <button
              type="button"
              className="btn report-refresh-btn"
              onClick={() => void refreshReports()}
              disabled={loading || detailLoading}
              aria-label="Làm mới danh sách báo cáo"
            >
              <RefreshCw size={15} className={loading ? "spin-icon" : ""} />
              <span>Làm mới</span>
            </button>
          </div>
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
                <span className="report-meta-icon"><FileText size={18} /></span>
                <div>
                  <span className="report-meta-eyebrow">Bản ghi đã xuất bản</span>
                  <strong>{report.report_type === "daily" ? "Báo cáo hàng ngày" : "Báo cáo hàng tuần"}</strong>
                </div>
              </div>
              <span className={`report-status-badge report-status-${report.status}`}>
                {statusLabels[report.status]}
              </span>
            </div>

            <div className="report-card-body">
              <div className="report-document-header">
                <div className="report-document-heading">
                  <span className="report-document-mark"><Leaf size={21} /></span>
                  <div>
                    <span className="report-document-kicker">Tóm tắt từ dữ liệu đã lưu</span>
                    <h3>Báo cáo tổng hợp chất lượng môi trường</h3>
                  </div>
                </div>
                <div className="report-document-meta-grid">
                  <div><span>Kỳ báo cáo</span><strong>{formatPeriod(report)}</strong></div>
                  <div><span>Tạo lúc</span><strong>{formatTimestamp(report.created_at)}</strong></div>
                </div>
              </div>

              <details className="report-technical-details">
                <summary><ShieldCheck size={15} /> Thông tin kỹ thuật và kiểm tra toàn vẹn</summary>
                <div>
                  <span>Schema: <strong>{report.schema_version || "periodic-report-v1"}</strong></span>
                  <span>SHA-256: <code>{report.content_checksum_sha256 || "Không có (legacy)"}</code></span>
                  <span>Múi giờ: <strong>{report.timezone}</strong></span>
                  {report.reused && <span className="report-reused-pill">Dùng lại bản ghi đã lưu</span>}
                </div>
              </details>

              {isLegacyReport && (
                <div className="alert-box alert-info" role="status">
                  <Info size={16} />
                  <span>Báo cáo legacy vẫn có thể xem và xuất; các khối ESG, đối chiếu và ma trận có thể chưa có.</span>
                </div>
              )}

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

              <section className="report-reader-summary" aria-labelledby="report-reader-summary-title">
                <div className="report-reader-summary-heading">
                  <div>
                    <span>Tóm tắt cho Ban Quản lý</span>
                    <h4 id="report-reader-summary-title">Bốn điểm cần nắm trong kỳ này</h4>
                  </div>
                  <p>Được diễn giải từ cùng bản ghi báo cáo, không tính lại dữ liệu.</p>
                </div>
                <div className="report-reader-summary-grid">
                  {readerSummary.map((item) => (
                    <article key={item.label} className={`report-reader-card report-reader-card--${item.tone}`}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                      <small>{item.detail}</small>
                    </article>
                  ))}
                </div>
              </section>

              <section className="report-section-block">
                <h4>1. Tổng quan dữ liệu</h4>
                <div className="report-kpi-grid">
                  <div className="report-kpi-card report-kpi-card--valid">
                    <div className="report-kpi-label"><Database size={15} /><span>Mẫu hợp lệ</span></div>
                    <strong>{measurements?.valid_sample_count ?? 0}</strong>
                    <small>Được đưa vào tổng hợp</small>
                  </div>
                  <div className="report-kpi-card report-kpi-card--excluded">
                    <div className="report-kpi-label"><ShieldAlert size={15} /><span>Mẫu bị loại</span></div>
                    <strong>{measurements?.excluded_sample_count ?? 0}</strong>
                    <small>Không qua quality gate</small>
                  </div>
                  <div className="report-kpi-card report-kpi-card--average">
                    <div className="report-kpi-label"><Activity size={15} /><span>AQI trung bình</span></div>
                    <strong>{formatNumber(measurements?.overall_avg_aqi)}</strong>
                    <small>Toàn bộ trạm đủ điều kiện</small>
                  </div>
                  <div className="report-kpi-card report-kpi-card--peak">
                    <div className="report-kpi-label"><BarChart3 size={15} /><span>AQI cao nhất</span></div>
                    <strong>{formatNumber(measurements?.overall_max_aqi)}</strong>
                    <small>Đỉnh quan sát trong kỳ</small>
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
                <h4>4. Chỉ số ESG ước tính</h4>
                {esgMetrics ? (
                  <div className="report-esg-grid">
                    <article>
                      <span>PM2.5 ước tính</span>
                      <strong>
                        {esgMetrics.estimated_pm25_removed_kg.value == null
                          ? "Không đủ dữ liệu"
                          : `${formatNumber(esgMetrics.estimated_pm25_removed_kg.value, 9)} kg`}
                      </strong>
                      <small>
                        {estimateStatusLabels[esgMetrics.estimated_pm25_removed_kg.status]}
                        {formatEstimateReason(esgMetrics.estimated_pm25_removed_kg.reason_code)
                          ? ` · ${formatEstimateReason(esgMetrics.estimated_pm25_removed_kg.reason_code)}`
                          : ""}
                      </small>
                    </article>
                    <article>
                      <span>Điện năng ước tính</span>
                      <strong>
                        {esgMetrics.estimated_energy_saved_kwh.value == null
                          ? "Không đủ dữ liệu"
                          : `${formatNumber(esgMetrics.estimated_energy_saved_kwh.value, 6)} kWh`}
                      </strong>
                      <small>
                        {estimateStatusLabels[esgMetrics.estimated_energy_saved_kwh.status]}
                        {formatEstimateReason(esgMetrics.estimated_energy_saved_kwh.reason_code)
                          ? ` · ${formatEstimateReason(esgMetrics.estimated_energy_saved_kwh.reason_code)}`
                          : ""}
                      </small>
                    </article>
                  </div>
                ) : (
                  <p>Khối ESG không có trong báo cáo legacy.</p>
                )}
                <p className="report-reference-disclaimer">
                  Đây là estimate từ ACK/profile simulator, không phải lượng bụi thực đo, bằng chứng nhân quả
                  hoặc điện năng đo từ công tơ.
                </p>
              </section>

              <section className="report-section-block">
                <h4>5. Đối chiếu tham chiếu và KPI nội bộ</h4>
                {referenceComparison?.station_days?.length ? (
                  <div className="report-summary-table-wrapper">
                    <table className="report-summary-table" aria-label="Đối chiếu QCVN WHO và KPI giờ tốt">
                      <thead>
                        <tr>
                          <th>Trạm / ngày</th>
                          <th>PM2.5 TB</th>
                          <th>Độ phủ</th>
                          <th>QCVN</th>
                          <th>WHO</th>
                          <th>KPI giờ tốt</th>
                        </tr>
                      </thead>
                      <tbody>
                        {referenceComparison.station_days.map((item) => (
                          <tr key={`${item.station_id}-${item.local_date}`}>
                            <td>{item.station_id} · {item.local_date}</td>
                            <td>{formatNumber(item.avg_pm25_ug_m3)} µg/m³</td>
                            <td>{formatNumber(item.coverage_ratio * 100)}%</td>
                            <td>{qcvnStatusLabels[item.qcvn.status]}</td>
                            <td>{whoStatusLabels[item.who.status]}</td>
                            <td>
                              {item.good_hour_kpi.good_hour_rate == null
                                ? "N/A"
                                : `${formatNumber(item.good_hour_kpi.good_hour_rate * 100)}% (${item.good_hour_kpi.good_hour_count}/${item.good_hour_kpi.eligible_hour_count})`}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>Không có station-day đủ điều kiện hoặc report legacy chưa lưu block này.</p>
                )}
                <p className="report-reference-disclaimer">
                  QCVN dùng µg/Nm³ nên không thể đối chiếu trực tiếp với dữ liệu mô phỏng µg/m³. WHO là hướng dẫn,
                  không phải quy chuẩn pháp lý. KPI mục tiêu 85% là KPI demo độc lập; không đánh giá tuân thủ trung bình năm.
                </p>
              </section>

              <section className="report-section-block">
                <h4>6. Ma trận 7 ngày × 24 giờ</h4>
                <WeeklyMatrixChart matrix={weeklyMatrix} />
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

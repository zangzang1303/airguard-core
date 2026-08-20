import React, { useState } from "react";
import {
  FileText,
  Download,
  Mail,
  ShieldAlert,
  AlertTriangle,
  Clock,
  Calendar,
  Filter,
  BarChart3,
  Info,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { PageHeader } from "../../components/common/PageHeader";

export type ReportType = "daily" | "weekly";

export const ReportViewer: React.FC = () => {
  const { role } = useAuth();
  const isManagerOrAdmin = role === "manager" || role === "admin";

  const [activeTab, setActiveTab] = useState<ReportType>("daily");
  const [selectedPeriod, setSelectedPeriod] = useState<string>("today");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Access Restriction Gate
  if (!isManagerOrAdmin) {
    return (
      <div className="report-viewer-container">
        <PageHeader
          title="Báo cáo Môi trường Định kỳ"
          description="Báo cáo tổng hợp chất lượng không khí cho Ban Quản Lý."
        />
        <div className="alert-box alert-warning" role="alert">
          <ShieldAlert size={18} />
          <span>Màn hình Báo cáo Định kỳ chỉ dành cho tài khoản Manager hoặc Admin.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="report-viewer-container">
      <PageHeader
        title="Báo cáo Môi trường Định kỳ"
        description="Xem trực tiếp nội dung phân tích chất lượng môi trường khu đô thị Vinhomes Ocean Park 1."
        actions={
          <div className="report-header-actions">
            <button
              type="button"
              className="btn btn-outline btn-disabled"
              disabled
              title="Contract pending: Backend chưa có endpoint tải file PDF"
            >
              <Download size={15} />
              <span>Tải báo cáo PDF</span>
              <span className="pending-badge">Contract pending</span>
            </button>

            <button
              type="button"
              className="btn btn-outline btn-disabled"
              disabled
              title="Contract pending: Backend chưa có endpoint gửi email tự động"
            >
              <Mail size={15} />
              <span>Gửi Email cho BQL</span>
              <span className="pending-badge">Contract pending</span>
            </button>
          </div>
        }
      />

      {/* Contract Pending & Specification Notice Banner */}
      <div className="alert-box alert-info contract-pending-banner" role="status">
        <Info size={18} className="banner-icon" />
        <div className="banner-content">
          <strong>Thông báo trạng thái API (Contract Pending):</strong>
          <p>
            Backend hiện tại chưa cung cấp API endpoint chính thức cho Báo cáo Daily/Weekly, xuất file PDF
            hoặc dịch vụ gửi mail tự động. Hệ thống tuyệt đối không hiển thị dữ liệu giả lập không có thực.
          </p>
        </div>
      </div>

      {/* Tab Controls & Period Filters */}
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
            <span>Báo cáo Hàng ngày (Daily)</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "weekly"}
            className={`report-tab-btn ${activeTab === "weekly" ? "is-active" : ""}`}
            onClick={() => setActiveTab("weekly")}
          >
            <BarChart3 size={15} />
            <span>Báo cáo Hàng tuần (Weekly)</span>
          </button>
        </div>

        <div className="report-filter-group">
          <Filter size={14} className="filter-icon" />
          <label htmlFor="period-select" className="sr-only">
            Chọn kỳ báo cáo
          </label>
          <select
            id="period-select"
            className="report-period-select"
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
          >
            {activeTab === "daily" ? (
              <>
                <option value="today">Hôm nay (20/08/2026)</option>
                <option value="yesterday">Hôm qua (19/08/2026)</option>
                <option value="2026-08-18">18/08/2026</option>
              </>
            ) : (
              <>
                <option value="current-week">Tuần hiện tại (Tuần 34/2026)</option>
                <option value="last-week">Tuần trước (Tuần 33/2026)</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Report Content Card Container */}
      <div className="report-content-card">
        <div className="report-card-header">
          <div className="report-meta-tag">
            <FileText size={16} />
            <span>BÁO CÁO MÔI TRƯỜNG DÀNH CHO BAN QUẢN LÝ</span>
          </div>
          <span className="report-status-badge">CONTRACT PENDING</span>
        </div>

        <div className="report-card-body">
          {loading ? (
            <div className="report-loading-state">
              <RefreshCw size={24} className="spin-icon" />
              <span>Đang tải thông tin báo cáo...</span>
            </div>
          ) : error ? (
            <div className="report-error-state" role="alert">
              <AlertTriangle size={24} />
              <span>{error}</span>
            </div>
          ) : (
            <div className="report-placeholder-view">
              <div className="report-document-header">
                <h3>
                  {activeTab === "daily"
                    ? "Báo cáo Tổng quan Môi trường Hàng ngày"
                    : "Báo cáo Tổng quan Môi trường Hàng tuần"}
                </h3>
                <div className="document-sub-meta">
                  <span>Khu vực: Vinhomes Ocean Park 1</span>
                  <span>•</span>
                  <span>Múi giờ: Asia/Ho_Chi_Minh</span>
                  <span>•</span>
                  <span>Phát hành: Ban Quản Lý (System)</span>
                </div>
              </div>

              <div className="report-section-block">
                <h4>1. Tóm tắt tình trạng quan trắc</h4>
                <p>
                  Hệ thống ghi nhận dữ liệu từ 5 trạm quan trắc mô phỏng (S01–S05). Chỉ số AQI và PM2.5 được
                  tính toán theo tiêu chuẩn US EPA PM2.5 24H (2012).
                </p>
                <div className="report-summary-table-wrapper">
                  <table className="report-summary-table" aria-label="Bảng tóm tắt chỉ số quan trắc">
                    <thead>
                      <tr>
                        <th>Trạm</th>
                        <th>AQI Trung bình</th>
                        <th>PM2.5 Max (µg/m³)</th>
                        <th>CO₂ Max (ppm)</th>
                        <th>Tiếng ồn Max (dB)</th>
                        <th>Nhiệt độ (°C)</th>
                        <th>Trạng thái API</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>S01 · VinUni Campus</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td><span className="pending-text">Pending endpoint</span></td>
                      </tr>
                      <tr>
                        <td>S02 · Hồ San Hô</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td><span className="pending-text">Pending endpoint</span></td>
                      </tr>
                      <tr>
                        <td>S03 · Biển Hồ Nước Mặn</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td><span className="pending-text">Pending endpoint</span></td>
                      </tr>
                      <tr>
                        <td>S04 · Park River</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td><span className="pending-text">Pending endpoint</span></td>
                      </tr>
                      <tr>
                        <td>S05 · Phân khu Sapphire</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td>—</td>
                        <td><span className="pending-text">Pending endpoint</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="report-section-block">
                <h4>2. Phân tích từ AI Agent & Đề xuất điều tiết</h4>
                <div className="report-ai-notice">
                  <Clock size={16} />
                  <span>
                    Chức năng tổng hợp báo cáo văn bản tự động sẽ kích hoạt sau khi backend hoàn thiện
                    endpoint `/api/v1/reports`.
                  </span>
                </div>
              </div>

              <div className="report-disclaimer-footer">
                <small>
                  Tuyên bố miễn trừ: Dữ liệu giả lập cho MVP — không phải quan trắc chính thức. Không dùng để
                  chẩn đoán y tế hoặc đưa ra quyết định pháp lý.
                </small>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Clock,
  Eye,
  FileCheck2,
  FileSearch,
  Filter,
  LockKeyhole,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  XCircle,
  X,
  FileText
} from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { IconButton } from "../../components/common/IconButton";
import { useAuth } from "../../context/AuthContext";
import { AuditLogEntry, Station } from "../../types";
import "./AuditLog.css";

// Formatter cho thời gian Việt Nam
const formatVnDateTime = (isoString: string): { primary: string; relative: string } => {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return { primary: isoString, relative: "" };

    const primary = date.toLocaleString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

    const diffMinutes = Math.floor((Date.now() - date.getTime()) / 60000);
    let relative = "";
    if (diffMinutes < 1) relative = "vừa xong";
    else if (diffMinutes < 60) relative = `${diffMinutes} phút trước`;
    else if (diffMinutes < 1440) relative = `${Math.floor(diffMinutes / 60)} giờ trước`;
    else relative = `${Math.floor(diffMinutes / 1440)} ngày trước`;

    return { primary, relative };
  } catch {
    return { primary: isoString, relative: "" };
  }
};

// Formatter cho mã hành động
const formatActionLabel = (action: string): string => {
  const map: Record<string, string> = {
    CREATE_PROPOSAL: "Tạo đề xuất",
    APPROVE_PROPOSAL: "Phê duyệt đề xuất",
    REJECT_PROPOSAL: "Từ chối đề xuất",
    DISPATCH_DEVICE_COMMAND: "Gửi lệnh thiết bị",
    UPDATE_USER_ROLE: "Cập nhật quyền",
    CREATE_USER: "Tạo người dùng mới",
    DISABLE_USER: "Vô hiệu tài khoản",
  };
  return map[action] ?? action;
};

// Avatar viết tắt cho Actor
const getActorInitials = (actor: string): string => {
  if (actor.toLowerCase().includes("ai")) return "AI";
  if (actor.toLowerCase().includes("manager")) return "MGR";
  if (actor.toLowerCase().includes("admin")) return "ADM";
  const parts = actor.split("@")[0].split(/[._\s-]/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return actor.substring(0, 2).toUpperCase();
};

interface AuditLogProps {
  onClose?: () => void;
  stations?: Station[];
}

export const AuditLog: React.FC<AuditLogProps> = ({ onClose, stations = [] }) => {
  const { role, userId } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  // Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [actorFilter, setActorFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("all");
  const [stationFilter, setStationFilter] = useState("all");
  const [outcomeFilter, setOutcomeFilter] = useState("all");
  const [timeRangeFilter, setTimeRangeFilter] = useState("all");

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLogs({ userId, role: "manager" });
      setLogs(data);
    } catch (err: any) {
      setError(err?.message ?? "Không thể tải nhật ký kiểm toán. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (role === "manager" || role === "admin") {
      fetchLogs();
    } else {
      setLoading(false);
    }
  }, [role]);

  // Dynamic filter options
  const actors = useMemo(() => Array.from(new Set(logs.map((log) => log.actor))), [logs]);
  const actions = useMemo(() => Array.from(new Set(logs.map((log) => log.action))), [logs]);

  // Check if any filter is active
  const hasActiveFilters = useMemo(() => {
    return (
      searchTerm.trim() !== "" ||
      actorFilter !== "all" ||
      actionFilter !== "all" ||
      stationFilter !== "all" ||
      outcomeFilter !== "all" ||
      timeRangeFilter !== "all"
    );
  }, [searchTerm, actorFilter, actionFilter, stationFilter, outcomeFilter, timeRangeFilter]);

  const resetFilters = () => {
    setSearchTerm("");
    setActorFilter("all");
    setActionFilter("all");
    setStationFilter("all");
    setOutcomeFilter("all");
    setTimeRangeFilter("all");
  };

  // Filtered Logs
  const filteredLogs = useMemo(() => {
    const now = Date.now();
    const query = searchTerm.toLowerCase().trim();

    return logs.filter((log) => {
      // 1. Text Search Query
      if (query !== "") {
        const matchesQuery =
          log.actor.toLowerCase().includes(query) ||
          log.action.toLowerCase().includes(query) ||
          log.target.toLowerCase().includes(query) ||
          log.correlation_id.toLowerCase().includes(query) ||
          log.id.toLowerCase().includes(query) ||
          (log.detail && log.detail.toLowerCase().includes(query));
        if (!matchesQuery) return false;
      }

      // 2. Actor Filter
      if (actorFilter !== "all" && log.actor !== actorFilter) return false;

      // 3. Action Filter
      if (actionFilter !== "all" && log.action !== actionFilter) return false;

      // 4. Station Filter
      if (stationFilter !== "all") {
        const matchesStation =
          (log.target && log.target.includes(stationFilter)) ||
          (log.detail && log.detail.includes(stationFilter));
        if (!matchesStation) return false;
      }

      // 5. Outcome Filter
      if (outcomeFilter !== "all") {
        const outcomeLower = log.outcome.toLowerCase();
        if (outcomeFilter === "success" && !["success", "approved", "succeeded"].includes(outcomeLower)) {
          return false;
        }
        if (outcomeFilter === "failure" && !["failure", "failed", "rejected"].includes(outcomeLower)) {
          return false;
        }
        if (outcomeFilter === "pending" && !["pending", "queued"].includes(outcomeLower)) {
          return false;
        }
      }

      // 6. Time Range Filter
      if (timeRangeFilter !== "all") {
        const logTime = new Date(log.time).getTime();
        const diffHours = (now - logTime) / (1000 * 3600);
        if (timeRangeFilter === "today") {
          const todayStart = new Date();
          todayStart.setHours(0, 0, 0, 0);
          if (logTime < todayStart.getTime()) return false;
        } else if (timeRangeFilter === "24h") {
          if (diffHours > 24) return false;
        } else if (timeRangeFilter === "7d") {
          if (diffHours > 168) return false;
        }
      }

      return true;
    });
  }, [logs, searchTerm, actorFilter, actionFilter, stationFilter, outcomeFilter, timeRangeFilter]);

  // Access Control Guard
  if (role !== "manager" && role !== "admin") {
    return (
      <div className="audit-explorer-container">
        <div className="alert-box alert-warning" style={{ marginTop: 24 }}>
          <LockKeyhole size={20} />
          <div>
            <strong>Truy cập bị giới hạn</strong>
            <p style={{ margin: 0, fontSize: "0.85rem" }}>
              Nhật ký kiểm toán hệ thống (Audit Log Explorer) chỉ dành riêng cho tài khoản vai trò Manager hoặc Admin.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="audit-explorer-container">
      {/* HEADER SECTION */}
      <div className="audit-explorer-header">
        <div className="audit-explorer-title-group">
          <div className="audit-explorer-title-row">
            <div className="audit-explorer-title-icon">
              <FileCheck2 size={20} />
            </div>
            <h2 className="audit-explorer-title">Audit Log Explorer</h2>
          </div>
          <p className="audit-explorer-subtitle">
            Nhật ký kiểm toán hệ thống append-only · Giám sát và truy vết quy trình phê duyệt BQL
          </p>
          <div className="audit-header-badges">
            <span className="audit-pill-badge audit-pill-badge--count">
              <FileText size={13} /> {filteredLogs.length} / {logs.length} bản ghi
            </span>
            <span className="audit-pill-badge audit-pill-badge--verified">
              <ShieldCheck size={13} /> Append-Only Read-Only Verified
            </span>
          </div>
        </div>

        <div className="audit-header-actions">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchLogs}
            disabled={loading}
            style={{ borderRadius: 10, padding: "8px 14px" }}
          >
            <RefreshCw className={loading ? "is-spinning" : ""} size={15} />
            <span>{loading ? "Đang cập nhật" : "Làm mới"}</span>
          </Button>

          {onClose && (
            <IconButton
              label="Đóng"
              onClick={onClose}
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: "#f1f5f9",
                color: "#475569",
                border: "1px solid #cbd5e1",
              }}
            >
              <X size={18} />
            </IconButton>
          )}
        </div>
      </div>

      {/* FILTER TOOLBAR */}
      <section className="audit-filter-card" aria-label="Bộ lọc Audit Log">
        <div className="audit-filter-top-row">
          <div className="audit-search-input-wrap">
            <Search className="audit-search-icon" size={16} />
            <input
              type="text"
              className="audit-search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Tìm theo Người thực hiện, Hành động, ID..."
            />
          </div>
        </div>

        <div className="audit-filter-grid">
          <div className="audit-filter-field">
            <span className="audit-field-label">Trạm quan trắc</span>
            <select
              className="audit-select-control"
              value={stationFilter}
              onChange={(e) => setStationFilter(e.target.value)}
            >
              <option value="all">Tất cả trạm</option>
              {stations.map((station) => (
                <option key={station.station_id} value={station.station_id}>
                  {station.station_id} · {station.station_name}
                </option>
              ))}
            </select>
          </div>

          <div className="audit-filter-field">
            <span className="audit-field-label">Thời gian</span>
            <select
              className="audit-select-control"
              value={timeRangeFilter}
              onChange={(e) => setTimeRangeFilter(e.target.value)}
            >
              <option value="all">Tất cả thời gian</option>
              <option value="today">Hôm nay</option>
              <option value="24h">24 giờ qua</option>
              <option value="7d">7 ngày qua</option>
            </select>
          </div>

          <div className="audit-filter-field">
            <span className="audit-field-label">Người thực hiện</span>
            <select
              className="audit-select-control"
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
            >
              <option value="all">Tất cả người thực hiện</option>
              {actors.map((actor) => (
                <option key={actor} value={actor}>
                  {actor}
                </option>
              ))}
            </select>
          </div>

          <div className="audit-filter-field">
            <span className="audit-field-label">Kết quả</span>
            <select
              className="audit-select-control"
              value={outcomeFilter}
              onChange={(e) => setOutcomeFilter(e.target.value)}
            >
              <option value="all">Tất cả kết quả</option>
              <option value="success">SUCCESS / Phê duyệt</option>
              <option value="failure">FAILURE / Từ chối</option>
              <option value="pending">PENDING / Đang xử lý</option>
            </select>
          </div>

          <button
            type="button"
            className={`audit-reset-btn ${hasActiveFilters ? "active" : ""}`}
            onClick={resetFilters}
            title="Đặt lại tất cả bộ lọc"
          >
            <RotateCcw size={14} />
            <span>Đặt lại</span>
          </button>
        </div>
      </section>

      {/* DATA TABLE / ACTIVITY EXPLORER CARD */}
      <div className="audit-table-card">
        {loading ? (
          <div className="audit-table-wrapper">
            <table className="audit-explorer-table">
              <thead>
                <tr>
                  <th>Thời gian</th>
                  <th>Người thực hiện</th>
                  <th>Hành động</th>
                  <th>Đối tượng</th>
                  <th>Kết quả</th>
                  <th>Correlation ID</th>
                  <th>Chi tiết</th>
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3, 4, 5].map((i) => (
                  <tr key={i} className="audit-skeleton-row">
                    <td><div className="audit-skeleton-box" style={{ width: "110px" }} /></td>
                    <td><div className="audit-skeleton-box" style={{ width: "140px" }} /></td>
                    <td><div className="audit-skeleton-box" style={{ width: "130px" }} /></td>
                    <td><div className="audit-skeleton-box" style={{ width: "100px" }} /></td>
                    <td><div className="audit-skeleton-box" style={{ width: "80px" }} /></td>
                    <td><div className="audit-skeleton-box" style={{ width: "90px" }} /></td>
                    <td><div className="audit-skeleton-box" style={{ width: "50px" }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : error ? (
          <div className="audit-empty-state">
            <div className="audit-empty-icon" style={{ background: "#fef2f2", color: "#ef4444" }}>
              <XCircle size={28} />
            </div>
            <h3 className="audit-empty-title">Không thể tải nhật ký</h3>
            <p className="audit-empty-desc">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchLogs}>
              Thử lại
            </Button>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="audit-empty-state">
            <div className="audit-empty-icon">
              <FileSearch size={28} />
            </div>
            <h3 className="audit-empty-title">Không tìm thấy bản ghi kiểm toán phù hợp</h3>
            <p className="audit-empty-desc">
              {hasActiveFilters
                ? "Không có dữ liệu trùng khớp với bộ lọc hiện tại. Thử thay đổi từ khóa hoặc bấm Đặt lại."
                : "Hệ thống chưa ghi nhận bản ghi kiểm toán nào."}
            </p>
            {hasActiveFilters && (
              <Button variant="outline" size="sm" onClick={resetFilters} style={{ borderRadius: 8 }}>
                <RotateCcw size={14} /> Xóa bộ lọc
              </Button>
            )}
          </div>
        ) : (
          <div className="audit-table-wrapper">
            <table className="audit-explorer-table">
              <thead>
                <tr>
                  <th>Thời gian</th>
                  <th>Người thực hiện</th>
                  <th>Mã hành động</th>
                  <th>Đối tượng</th>
                  <th>Kết quả</th>
                  <th>Request ID</th>
                  <th style={{ textAlign: "right" }}>Chi tiết</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => {
                  const { primary, relative } = formatVnDateTime(log.time);
                  const outcomeLower = log.outcome.toLowerCase();

                  return (
                    <tr key={log.id}>
                      <td>
                        <div className="audit-time-cell">
                          <span className="audit-time-primary">{primary}</span>
                          {relative && <span className="audit-time-relative">{relative}</span>}
                        </div>
                      </td>

                      <td>
                        <div className="audit-actor-cell">
                          <div
                            className={`audit-actor-avatar ${
                              log.actor.toLowerCase().includes("ai")
                                ? "audit-actor-avatar--ai"
                                : "audit-actor-avatar--manager"
                            }`}
                          >
                            {getActorInitials(log.actor)}
                          </div>
                          <span className="audit-actor-name">{log.actor}</span>
                        </div>
                      </td>

                      <td>
                        <span className="audit-action-pill" title={log.action}>
                          {formatActionLabel(log.action)}
                        </span>
                      </td>

                      <td>
                        <span className="audit-target-tag" title={log.target}>
                          {log.target}
                        </span>
                      </td>

                      <td>
                        {["success", "approved", "succeeded"].includes(outcomeLower) ? (
                          <span className="audit-outcome-pill audit-outcome-pill--success">
                            <CheckCircle2 size={12} /> Success
                          </span>
                        ) : ["failure", "failed", "rejected"].includes(outcomeLower) ? (
                          <span className="audit-outcome-pill audit-outcome-pill--failure">
                            <XCircle size={12} /> Failure
                          </span>
                        ) : (
                          <span className="audit-outcome-pill audit-outcome-pill--pending">
                            <Clock size={12} /> Pending
                          </span>
                        )}
                      </td>

                      <td>
                        <code className="audit-corr-code">{log.correlation_id}</code>
                      </td>

                      <td style={{ textAlign: "right" }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedLog(log)}
                          style={{ padding: "4px 8px", fontSize: "0.78rem" }}
                        >
                          <Eye size={14} /> Xem
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* AUDIT RECORD DETAIL MODAL OVERLAY */}
      {selectedLog && (
        <div
          className="audit-detail-modal-overlay"
          onClick={() => setSelectedLog(null)}
          role="dialog"
          aria-modal="true"
        >
          <div className="audit-detail-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="audit-detail-modal-header">
              <h3>
                <FileCheck2 size={18} style={{ color: "#10b981" }} /> Chi tiết Bản ghi #{selectedLog.id}
              </h3>
              <IconButton label="Đóng" onClick={() => setSelectedLog(null)}>
                <X size={18} />
              </IconButton>
            </div>

            <div className="audit-detail-modal-body">
              <div className="audit-detail-grid">
                <div className="audit-detail-field">
                  <span className="audit-detail-label">Thời gian thực hiện</span>
                  <span className="audit-detail-value">{formatVnDateTime(selectedLog.time).primary}</span>
                </div>

                <div className="audit-detail-field">
                  <span className="audit-detail-label">Người thực hiện (Actor)</span>
                  <span className="audit-detail-value">{selectedLog.actor}</span>
                </div>

                <div className="audit-detail-field">
                  <span className="audit-detail-label">Mã hành động (Action)</span>
                  <code className="audit-action-pill">{selectedLog.action}</code>
                </div>

                <div className="audit-detail-field">
                  <span className="audit-detail-label">Kết quả (Outcome)</span>
                  <span className="audit-detail-value" style={{ textTransform: "uppercase", fontWeight: 700 }}>
                    {selectedLog.outcome}
                  </span>
                </div>

                <div className="audit-detail-field full-width">
                  <span className="audit-detail-label">Đối tượng tác động (Target)</span>
                  <span className="audit-detail-value">{selectedLog.target}</span>
                </div>

                <div className="audit-detail-field full-width">
                  <span className="audit-detail-label">Request / Correlation ID</span>
                  <code className="audit-corr-code" style={{ fontSize: "0.85rem" }}>
                    {selectedLog.correlation_id}
                  </code>
                </div>

                {selectedLog.detail && (
                  <div className="audit-detail-field full-width">
                    <span className="audit-detail-label">Ghi chú & Chi tiết kĩ thuật</span>
                    <pre
                      style={{
                        background: "#f8fafc",
                        padding: 12,
                        borderRadius: 8,
                        fontSize: "0.78rem",
                        color: "#334155",
                        overflowX: "auto",
                        margin: 0,
                        border: "1px solid #e2e8f0",
                      }}
                    >
                      {selectedLog.detail}
                    </pre>
                  </div>
                )}
              </div>
            </div>

            <div className="audit-detail-modal-footer">
              <Button variant="outline" size="sm" onClick={() => setSelectedLog(null)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

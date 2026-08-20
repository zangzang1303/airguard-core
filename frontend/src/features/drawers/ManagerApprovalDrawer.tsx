import React, { useState } from "react";
import {
  X,
  ShieldCheck,
  Check,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock,
  CheckCircle2,
  FileText,
  MapPin,
  Activity,
  Info
} from "lucide-react";
import { Proposal } from "../../types";

interface ManagerApprovalDrawerProps {
  proposals: Proposal[];
  loadError?: string | null;
  onRetry?: () => Promise<void>;
  onApprove: (proposalId: string, version: number) => Promise<void>;
  onReject: (proposalId: string, version: number, reason: string) => Promise<void>;
  onClose: () => void;
  onOpenAudit?: () => void;
}

const formatVnDateTime = (isoString?: string): string => {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
};

export const ManagerApprovalDrawer: React.FC<ManagerApprovalDrawerProps> = ({
  proposals,
  loadError,
  onRetry,
  onApprove,
  onReject,
  onClose,
  onOpenAudit,
}) => {
  const [rejectNote, setRejectNote] = useState("");
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [confirmingApproveProposal, setConfirmingApproveProposal] = useState<Proposal | null>(null);
  const [confirmingRejectProposal, setConfirmingRejectProposal] = useState<Proposal | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Prevent double-clicking
  const handleConfirmApprove = async () => {
    if (!confirmingApproveProposal || processingId !== null) return;
    const p = confirmingApproveProposal;
    setProcessingId(p.proposal_id);
    setErrorMessage(null);
    try {
      await onApprove(p.proposal_id, p.version);
      setConfirmingApproveProposal(null);
    } catch (err: any) {
      const msg = err?.message || String(err);
      if (msg.includes("403") || err?.status === 403) {
        setErrorMessage("Lỗi 403: Tài khoản của bạn không có quyền phê duyệt đề xuất này.");
      } else if (msg.includes("409") || err?.status === 409) {
        setErrorMessage("Lỗi 409: Đề xuất đã bị thay đổi hoặc đã được phê duyệt ở phiên khác. Vui lòng tải lại.");
      } else {
        setErrorMessage(msg || "Không thể phê duyệt đề xuất do lỗi kết nối.");
      }
    } finally {
      setProcessingId(null);
    }
  };

  const handleConfirmReject = async () => {
    if (!confirmingRejectProposal || !rejectNote.trim() || processingId !== null) return;
    const p = confirmingRejectProposal;
    setProcessingId(p.proposal_id);
    setErrorMessage(null);
    try {
      await onReject(p.proposal_id, p.version, rejectNote.trim());
      setConfirmingRejectProposal(null);
      setRejectingId(null);
      setRejectNote("");
    } catch (err: any) {
      const msg = err?.message || String(err);
      if (msg.includes("403") || err?.status === 403) {
        setErrorMessage("Lỗi 403: Tài khoản của bạn không có quyền từ chối đề xuất này.");
      } else if (msg.includes("409") || err?.status === 409) {
        setErrorMessage("Lỗi 409: Đề xuất đã bị thay đổi hoặc đã được xử lý ở phiên khác. Vui lòng tải lại.");
      } else {
        setErrorMessage(msg || "Không thể từ chối đề xuất do lỗi kết nối.");
      }
    } finally {
      setProcessingId(null);
    }
  };

  const pendingProposals = proposals.filter((p) => p.status === "pending");

  return (
    <aside className="contextual-drawer right-drawer manager-approval-drawer">
      {/* Redesigned Clean Header */}
      <div className="drawer-header-bar manager-header">
        <div className="drawer-title-group">
          <span className="drawer-eyebrow-tag">HITL · QUẢN LÝ</span>
          <h2 className="drawer-main-title">Phê duyệt đề xuất</h2>
          <p className="drawer-sub-meta">Xem bằng chứng trước khi đưa ra quyết định.</p>
        </div>
        <div className="drawer-header-actions-group">
          {onOpenAudit && (
            <button
              className="drawer-header-pill-btn"
              onClick={onOpenAudit}
              title="Xem Nhật ký Kiểm toán (Audit Log)"
              aria-label="Xem Audit Log"
            >
              <FileText size={14} />
              <span>Nhật ký</span>
            </button>
          )}
          <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng bảng phê duyệt">
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="drawer-scroll-body">
        {loadError && (
          <div className="alert-box alert-error manager-load-error" role="alert">
            <AlertTriangle size={16} />
            <span>Không thể tải hàng đợi phê duyệt mới nhất. Không có dữ liệu demo được thay thế.</span>
            {onRetry && (
              <button type="button" className="proposal-btn secondary sm" onClick={onRetry}>
                <RefreshCw size={14} /> Thử lại
              </button>
            )}
          </div>
        )}

        {/* Global Error Banner */}
        {errorMessage && (
          <div className="alert-box alert-error" style={{ marginBottom: "12px", padding: "10px 12px", borderRadius: "8px" }}>
            <AlertTriangle size={16} />
            <span>{errorMessage}</span>
          </div>
        )}

        {!loadError && pendingProposals.length === 0 ? (
          <div className="manager-empty-state">
            <ShieldCheck size={42} className="empty-shield" style={{ color: "#10b981" }} />
            <h4>Không có đề xuất nào đang chờ duyệt</h4>
            <p>Backend hiện không trả về proposal pending. Trạng thái này không đồng nghĩa môi trường đang an toàn.</p>
          </div>
        ) : (
          pendingProposals.map((p) => {
            const isProcessing = processingId === p.proposal_id;
            const isFailedDispatch = p.dispatch_status === "failed";
            const isSucceededDispatch = p.dispatch_status === "succeeded";
            const severityLevel = p.severity || "warning";

            return (
              <div key={p.proposal_id} className="proposal-item-card">
                {/* Station & Severity Row */}
                <div className="proposal-card-header">
                  <div className="proposal-station-badge">
                    <MapPin size={13} />
                    <span>Trạm {p.station_id || "Không xác định"}</span>
                  </div>
                  <div className={`proposal-severity-pill severity-${severityLevel}`}>
                    {severityLevel === "critical" ? <AlertTriangle size={12} /> : <Info size={12} />}
                    <span>{severityLevel.toUpperCase()}</span>
                  </div>
                </div>

                {/* Proposal Metadata Strip */}
                <div className="proposal-meta-strip">
                  <span>ID: <code>{p.proposal_id}</code></span>
                  <span className="meta-divider">•</span>
                  <span>Phiên bản: <code>v{p.version}</code></span>
                  <span className="meta-divider">•</span>
                  <span><Clock size={12} /> {formatVnDateTime(p.created_at)}</span>
                  <span className="meta-divider">•</span>
                  <span>Người tạo: <code>{p.created_by || "Không có dữ liệu"}</code></span>
                </div>

                {/* Action & Target Content */}
                <div className="proposal-action-target">
                  <div className="proposal-field-block">
                    <span className="field-label">Mục tiêu:</span>
                    <strong className="field-value-highlight">{p.target}</strong>
                  </div>
                  <div className="proposal-field-block">
                    <span className="field-label">Hành động:</span>
                    <span className="field-value">{p.action}</span>
                  </div>
                  <div className="proposal-field-block">
                    <span className="field-label">Cơ sở lý do:</span>
                    <p className="field-rationale">{p.rationale}</p>
                  </div>
                </div>

                {/* Structured Evidence Card */}
                <div className="proposal-evidence-card">
                  <div className="evidence-card-title">
                    <Activity size={13} /> Bằng chứng quan trắc grounded (Simulator)
                  </div>
                  <div className="evidence-grid-2col">
                    <div className="evidence-metric-item">
                      <span className="ev-label">PM2.5:</span>
                      <strong className="ev-val">{p.evidence?.pm25 ?? "—"} µg/m³</strong>
                    </div>
                    <div className="evidence-metric-item">
                      <span className="ev-label">AQI:</span>
                      <strong className="ev-val">{p.evidence?.aqi ?? "—"}{p.evidence?.aqi_category ? ` (${p.evidence.aqi_category})` : ""}</strong>
                    </div>
                    {p.evidence?.co2 != null && (
                      <div className="evidence-metric-item">
                        <span className="ev-label">CO₂:</span>
                        <strong className="ev-val">{p.evidence.co2} ppm</strong>
                      </div>
                    )}
                    {p.evidence?.noise_db != null && (
                      <div className="evidence-metric-item">
                        <span className="ev-label">Tiếng ồn:</span>
                        <strong className="ev-val">{p.evidence.noise_db} dB</strong>
                      </div>
                    )}
                  </div>
                </div>

                {/* Hardware Dispatch Status Display */}
                <div className="dispatch-status-banner">
                  <span className="status-label">Trạng thái phát lệnh IoT:</span>
                  {isSucceededDispatch ? (
                    <span className="status-pill status-succeeded">
                      <CheckCircle2 size={13} /> Lệnh đã phát thành công tới thiết bị
                    </span>
                  ) : isFailedDispatch ? (
                    <span className="status-pill status-failed">
                      <AlertTriangle size={13} /> Phát lệnh thất bại — Cần kiểm tra kĩ thuật
                    </span>
                  ) : p.dispatch_status === "queued" || p.dispatch_status === "pending" ? (
                    <span className="status-pill status-pending">
                      <Clock size={13} /> Đang hàng chờ phát lệnh IoT...
                    </span>
                  ) : p.dispatch_status === "not_configured" ? (
                    <span className="status-pill status-not-configured">
                      <Info size={13} /> Phê duyệt thủ công (IoT dispatcher chưa tự động)
                    </span>
                  ) : (
                    <span className="status-pill status-not-configured">
                      <Info size={13} /> Backend chưa trả trạng thái phát lệnh
                    </span>
                  )}
                </div>

                {/* Reject Input Form or Action Buttons */}
                {rejectingId === p.proposal_id ? (
                  <div className="reject-form-area">
                    <label className="reject-label">
                      Lý do từ chối (bắt buộc):
                    </label>
                    <input
                      type="text"
                      className="reject-note-input"
                      placeholder="Nhập lý do từ chối đề xuất này..."
                      value={rejectNote}
                      onChange={(e) => setRejectNote(e.target.value)}
                      disabled={isProcessing}
                      autoFocus
                    />
                    <div className="reject-btn-group">
                      <button
                        className="proposal-btn secondary sm"
                        disabled={isProcessing}
                        onClick={() => {
                          setRejectingId(null);
                          setRejectNote("");
                        }}
                      >
                        Hủy
                      </button>
                      <button
                        className="proposal-btn danger sm"
                        disabled={!rejectNote.trim() || isProcessing}
                        onClick={() => setConfirmingRejectProposal(p)}
                      >
                        {isProcessing ? <RefreshCw size={14} className="spin-icon" /> : "Xác nhận từ chối"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="proposal-actions-row">
                    <button
                      className="proposal-btn danger"
                      disabled={isProcessing}
                      onClick={() => setRejectingId(p.proposal_id)}
                    >
                      <XCircle size={15} />
                      <span>Từ chối</span>
                    </button>
                    <button
                      className="proposal-btn primary"
                      disabled={isProcessing}
                      onClick={() => setConfirmingApproveProposal(p)}
                    >
                      {isProcessing ? <RefreshCw size={15} className="spin-icon" /> : <Check size={15} />}
                      <span>Phê duyệt</span>
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Confirmation Modal for Approve */}
      {confirmingApproveProposal && (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
          <div className="modal-content" role="dialog" aria-modal="true" style={{ padding: "24px", maxWidth: "440px", borderRadius: "16px" }}>
            <h3 style={{ marginBottom: "12px", fontSize: "1.1rem", fontWeight: 700 }}>Xác nhận Phê duyệt Đề xuất</h3>
            <p style={{ fontSize: "0.88rem", color: "#475569", lineHeight: 1.5, marginBottom: "16px" }}>
              Bạn có chắc chắn muốn phê duyệt đề xuất <strong>#{confirmingApproveProposal.proposal_id}</strong> (Hành động: <em>{confirmingApproveProposal.action}</em> cho trạm {confirmingApproveProposal.station_id})?
              <br />
              <small style={{ color: "#64748b", marginTop: 6, display: "block" }}>
                Quyết định phê duyệt sẽ được ghi nhận vào Audit Log.
              </small>
            </p>
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                className="proposal-btn secondary"
                disabled={processingId !== null}
                onClick={() => setConfirmingApproveProposal(null)}
              >
                Hủy bỏ
              </button>
              <button
                className="proposal-btn primary"
                disabled={processingId !== null}
                onClick={handleConfirmApprove}
              >
                {processingId !== null ? <RefreshCw size={15} className="spin-icon" /> : "Xác nhận Phê duyệt"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Reject */}
      {confirmingRejectProposal && (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
          <div className="modal-content" role="dialog" aria-modal="true" style={{ padding: "24px", maxWidth: "440px", borderRadius: "16px" }}>
            <h3 style={{ marginBottom: "12px", fontSize: "1.1rem", fontWeight: 700, color: "#991b1b" }}>
              Xác nhận Từ chối Đề xuất
            </h3>
            <p style={{ fontSize: "0.88rem", color: "#475569", lineHeight: 1.5, marginBottom: "12px" }}>
              Từ chối đề xuất <strong>#{confirmingRejectProposal.proposal_id}</strong>.
            </p>
            <div style={{ background: "#fef2f2", padding: "10px 12px", borderRadius: 8, fontSize: "0.84rem", color: "#991b1b", marginBottom: 16 }}>
              Lý do từ chối ghi nhận: <em>"{rejectNote}"</em>
            </div>
            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button
                className="proposal-btn secondary"
                disabled={processingId !== null}
                onClick={() => setConfirmingRejectProposal(null)}
              >
                Hủy bỏ
              </button>
              <button
                className="proposal-btn danger"
                disabled={processingId !== null}
                onClick={handleConfirmReject}
              >
                {processingId !== null ? <RefreshCw size={15} className="spin-icon" /> : "Xác nhận từ chối"}
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};

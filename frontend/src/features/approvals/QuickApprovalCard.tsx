import React, { useState } from "react";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  Info,
  MapPin,
  RefreshCw,
  ShieldCheck,
  X,
  XCircle,
  Zap,
} from "lucide-react";
import { Proposal } from "../../types";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";

export interface QuickApprovalCardProps {
  proposal: Proposal | null;
  onSuccess?: (updatedProposal: Proposal) => void;
  onRefreshQueue?: () => Promise<void>;
  onClose?: () => void;
}

export const QuickApprovalCard: React.FC<QuickApprovalCardProps> = ({
  proposal,
  onSuccess,
  onRefreshQueue,
  onClose,
}) => {
  const { role, userId } = useAuth();
  const isManagerOrAdmin = role === "manager" || role === "admin";

  const [confirmModal, setConfirmModal] = useState<"approve" | "reject" | null>(null);
  const [rejectNote, setRejectNote] = useState<string>("");
  const [approveNote, setApproveNote] = useState<string>("Manager quick approved from dashboard.");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  if (!isManagerOrAdmin || !proposal || proposal.status !== "pending") {
    return null;
  }

  const handleApproveClick = () => {
    setErrorMessage(null);
    setValidationError(null);
    setConfirmModal("approve");
  };

  const handleRejectClick = () => {
    setErrorMessage(null);
    setValidationError(null);
    setRejectNote("");
    setConfirmModal("reject");
  };

  const handleConfirmApprove = async () => {
    if (submitting) return;
    setSubmitting(true);
    setErrorMessage(null);

    try {
      const updated = await api.approveProposal(proposal.proposal_id, proposal.version, approveNote, {
        userId,
        role: "manager",
      });
      setConfirmModal(null);
      setActionSuccessMessage(`Đã phê duyệt đề xuất ${proposal.proposal_id}.`);
      if (onSuccess) onSuccess(updated);
    } catch (err: any) {
      const msg = err?.message || String(err);
      if (msg.includes("403") || err?.status === 403) {
        setErrorMessage("Lỗi 403: Quyền truy cập bị từ chối. Chỉ Manager hoặc Admin mới có thể thực hiện.");
      } else if (msg.includes("409") || err?.status === 409) {
        setErrorMessage("Lỗi 409: Đề xuất đã bị thay đổi ở phiên khác. Đang tải lại dữ liệu mới nhất từ server...");
        if (onRefreshQueue) onRefreshQueue();
      } else if (msg.includes("422") || err?.status === 422) {
        setErrorMessage("Lỗi 422: Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra phiên bản proposal.");
      } else {
        setErrorMessage(msg || "Lỗi server (5xx). Không thể hoàn tất phê duyệt.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmReject = async () => {
    if (!rejectNote.trim()) {
      setValidationError("Lý do từ chối là bắt buộc. Vui lòng điền ghi chú.");
      return;
    }
    if (submitting) return;

    setSubmitting(true);
    setErrorMessage(null);
    setValidationError(null);

    try {
      const updated = await api.rejectProposal(proposal.proposal_id, proposal.version, rejectNote.trim(), {
        userId,
        role: "manager",
      });
      setConfirmModal(null);
      setActionSuccessMessage(`Đã từ chối đề xuất ${proposal.proposal_id}.`);
      if (onSuccess) onSuccess(updated);
    } catch (err: any) {
      const msg = err?.message || String(err);
      if (msg.includes("403") || err?.status === 403) {
        setErrorMessage("Lỗi 403: Quyền truy cập bị từ chối.");
      } else if (msg.includes("409") || err?.status === 409) {
        setErrorMessage("Lỗi 409: Đề xuất đã bị thay đổi ở phiên khác. Đang làm mới...");
        if (onRefreshQueue) onRefreshQueue();
      } else if (msg.includes("422") || err?.status === 422) {
        setErrorMessage("Lỗi 422: Dữ liệu không hợp lệ. Kiểm tra lý do từ chối.");
      } else {
        setErrorMessage(msg || "Lỗi kết nối (5xx). Không thể từ chối đề xuất.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const isSucceededDispatch = proposal.dispatch_status === "succeeded";
  const isFailedDispatch = proposal.dispatch_status === "failed";
  const severityLevel = proposal.severity || "warning";

  return (
    <div className="quick-approval-card-root" role="region" aria-label="Đề xuất thông gió khẩn cấp">
      <div className="quick-approval-card">
        {/* Header Ribbon */}
        <div className="card-top-header">
          <div className="card-badge-group">
            <span className="eyebrow-tag">
              <Zap size={13} /> ĐỀ XUẤT ĐIỀU TIẾT KHẨN CẤP
            </span>
            <span className={`severity-badge level-${severityLevel}`}>
              {severityLevel.toUpperCase()}
            </span>
          </div>
          {onClose && (
            <button type="button" className="close-icon-btn" onClick={onClose} aria-label="Ẩn thẻ đề xuất">
              <X size={16} />
            </button>
          )}
        </div>

        {/* Server & Error Alerts */}
        {errorMessage && (
          <div className="card-alert-box alert-error" role="alert">
            <AlertTriangle size={15} />
            <span>{errorMessage}</span>
          </div>
        )}

        {actionSuccessMessage && (
          <div className="card-alert-box alert-success" role="status">
            <CheckCircle2 size={15} />
            <span>{actionSuccessMessage}</span>
          </div>
        )}

        {/* Card Content & Rationale */}
        <div className="card-main-content">
          <div className="station-meta-row">
            <div className="station-name-pill">
              <MapPin size={13} />
              <span>Trạm {proposal.station_id || "S05"}</span>
            </div>
            <div className="proposal-id-tag">
              ID: <code>{proposal.proposal_id}</code> (v{proposal.version})
            </div>
          </div>

          <h4 className="proposal-action-title">{proposal.action}</h4>
          <p className="proposal-rationale-text">{proposal.rationale}</p>

          {/* Grounded Evidence Grid */}
          <div className="grounded-evidence-grid">
            <div className="evidence-item">
              <span className="ev-label">AQI:</span>
              <strong className="ev-val">{proposal.evidence?.aqi ?? "—"}</strong>
            </div>
            <div className="evidence-item">
              <span className="ev-label">PM2.5:</span>
              <strong className="ev-val">{proposal.evidence?.pm25 ?? "—"} µg/m³</strong>
            </div>
            {proposal.evidence?.co2 != null && (
              <div className="evidence-item">
                <span className="ev-label">CO₂:</span>
                <strong className="ev-val">{proposal.evidence.co2} ppm</strong>
              </div>
            )}
            {proposal.evidence?.noise_db != null && (
              <div className="evidence-item">
                <span className="ev-label">Tiếng ồn:</span>
                <strong className="ev-val">{proposal.evidence.noise_db} dB</strong>
              </div>
            )}
          </div>

          {/* Dispatch Status Display */}
          <div className="dispatch-outcome-strip">
            <span className="strip-label">Trạng thái phát lệnh IoT:</span>
            {isSucceededDispatch ? (
              <span className="outcome-pill outcome-succeeded">
                <CheckCircle2 size={13} /> Đã bật quạt / Đã thực thi thành công
              </span>
            ) : isFailedDispatch ? (
              <span className="outcome-pill outcome-failed">
                <AlertTriangle size={13} /> Phát lệnh thất bại
              </span>
            ) : proposal.dispatch_status === "pending" || proposal.dispatch_status === "queued" ? (
              <span className="outcome-pill outcome-pending">
                <Clock size={13} /> Đang hàng chờ phát lệnh IoT...
              </span>
            ) : (
              <span className="outcome-pill outcome-not-configured">
                <Info size={13} /> Phê duyệt server truth (Dispatcher chưa phát lệnh tự động)
              </span>
            )}
          </div>
        </div>

        {/* Action Button Row */}
        <div className="card-actions-row">
          <button
            type="button"
            className="quick-btn btn-reject"
            disabled={submitting}
            onClick={handleRejectClick}
          >
            <XCircle size={16} />
            <span>Từ chối</span>
          </button>

          <button
            type="button"
            className="quick-btn btn-approve"
            disabled={submitting}
            onClick={handleApproveClick}
          >
            {submitting ? (
              <RefreshCw size={16} className="spin-icon" />
            ) : (
              <Check size={16} />
            )}
            <span>Duyệt & Bật Quạt Ngay (1 Chạm)</span>
          </button>
        </div>
      </div>

      {/* Confirmation Modal for Approve */}
      {confirmModal === "approve" && (
        <div className="modal-overlay" role="presentation" style={{ zIndex: 9999 }}>
          <div className="modal-content quick-modal-content" role="dialog" aria-modal="true">
            <div className="modal-header">
              <h3>Xác nhận Duyệt & Bật Quạt Thông Gió</h3>
              <button
                type="button"
                className="close-icon-btn"
                onClick={() => setConfirmModal(null)}
                disabled={submitting}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              <p>
                Bạn có chắc chắn muốn phê duyệt đề xuất <strong>#{proposal.proposal_id}</strong> (Hành động:{" "}
                <em>{proposal.action}</em> cho trạm <strong>{proposal.station_id}</strong>)?
              </p>
              <div className="info-box-note">
                <ShieldCheck size={16} />
                <span>Quyết định phê duyệt sẽ được lưu vào Audit Log hệ thống.</span>
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setConfirmModal(null)}
                disabled={submitting}
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                className="btn btn-success"
                onClick={handleConfirmApprove}
                disabled={submitting}
              >
                {submitting ? <RefreshCw size={15} className="spin-icon" /> : <Check size={15} />}
                <span>Xác nhận Duyệt</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Reject */}
      {confirmModal === "reject" && (
        <div className="modal-overlay" role="presentation" style={{ zIndex: 9999 }}>
          <div className="modal-content quick-modal-content" role="dialog" aria-modal="true">
            <div className="modal-header">
              <h3 style={{ color: "#991b1b" }}>Xác nhận Từ chối Đề xuất</h3>
              <button
                type="button"
                className="close-icon-btn"
                onClick={() => setConfirmModal(null)}
                disabled={submitting}
              >
                <X size={16} />
              </button>
            </div>
            <div className="modal-body">
              {validationError && (
                <div className="card-alert-box alert-error" style={{ marginBottom: "10px" }}>
                  <AlertTriangle size={14} />
                  <span>{validationError}</span>
                </div>
              )}
              <p>
                Từ chối đề xuất <strong>#{proposal.proposal_id}</strong> cho trạm {proposal.station_id}.
              </p>
              <div className="form-group" style={{ marginTop: "12px" }}>
                <label htmlFor="reject-reason-input" className="field-label">
                  Lý do từ chối (bắt buộc):
                </label>
                <input
                  id="reject-reason-input"
                  type="text"
                  className="form-input"
                  placeholder="Nhập lý do từ chối đề xuất..."
                  value={rejectNote}
                  onChange={(e) => {
                    setRejectNote(e.target.value);
                    if (e.target.value.trim()) setValidationError(null);
                  }}
                  disabled={submitting}
                  autoFocus
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setConfirmModal(null)}
                disabled={submitting}
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleConfirmReject}
                disabled={!rejectNote.trim() || submitting}
              >
                {submitting ? <RefreshCw size={15} className="spin-icon" /> : <XCircle size={15} />}
                <span>Xác nhận Từ chối</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

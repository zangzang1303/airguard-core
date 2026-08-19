import React, { useState } from "react";
import { X, ShieldCheck, Check, XCircle, Fan, AlertTriangle, Clock, RefreshCw } from "lucide-react";
import { Proposal } from "../../types";

interface ManagerApprovalDrawerProps {
  proposals: Proposal[];
  onApprove: (proposalId: string, version: number) => Promise<void>;
  onReject: (proposalId: string, version: number, reason: string) => Promise<void>;
  onClose: () => void;
}

export const ManagerApprovalDrawer: React.FC<ManagerApprovalDrawerProps> = ({
  proposals,
  onApprove,
  onReject,
  onClose,
}) => {
  const [rejectNote, setRejectNote] = useState("");
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const handleApproveAction = async (p: Proposal) => {
    setProcessingId(p.proposal_id);
    try {
      await onApprove(p.proposal_id, p.version);
    } finally {
      setProcessingId(null);
    }
  };

  const handleRejectAction = async (p: Proposal) => {
    if (!rejectNote.trim()) return;
    setProcessingId(p.proposal_id);
    try {
      await onReject(p.proposal_id, p.version, rejectNote);
      setRejectingId(null);
      setRejectNote("");
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <aside className="contextual-drawer right-drawer manager-approval-drawer">
      <div className="drawer-header-bar manager-header">
        <div className="drawer-title-group">
          <div className="badge-tag manager">HITL Manager Console</div>
          <h2 className="drawer-main-title">Duyệt Đề xuất Điều tiết Môi trường</h2>
        </div>
        <button className="drawer-close-btn" onClick={onClose} aria-label="Đóng">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-scroll-body">
        {proposals.length === 0 ? (
          <div className="manager-empty-state">
            <ShieldCheck size={36} className="empty-shield" />
            <h4>Không có đề xuất nào đang chờ duyệt</h4>
            <p>Hệ thống tự động thông gió và lọc khí tòa nhà đang vận hành ổn định.</p>
          </div>
        ) : (
          proposals.map((p) => {
            const isProcessing = processingId === p.proposal_id;
            return (
              <div key={p.proposal_id} className="proposal-item-card">
                <div className="proposal-top-row">
                  <div className="proposal-action-badge">
                    <Fan size={15} />
                    <span>{p.action}</span>
                  </div>
                  <span className="proposal-station-id">Trạm {p.station_id || "Chung"}</span>
                </div>

                <h4 className="proposal-reason-title">{p.rationale}</h4>

                {/* Evidence Details */}
                <div className="proposal-evidence-box">
                  <div className="evidence-head">Bằng chứng quan trắc từ AI:</div>
                  <div className="evidence-json-preview">
                    PM2.5: {p.evidence?.pm25 ?? 66.1} µg/m³ · AQI: {p.evidence?.aqi ?? 158} · Trạm: {p.station_id}. Đề xuất kích hoạt hệ thống lọc khí tòa nhà để bảo vệ cư dân.
                  </div>
                </div>

                {/* Action Buttons */}
                {rejectingId === p.proposal_id ? (
                  <div className="reject-form-area">
                    <input
                      type="text"
                      className="reject-note-input"
                      placeholder="Nhập lý do từ chối..."
                      value={rejectNote}
                      onChange={(e) => setRejectNote(e.target.value)}
                    />
                    <div className="reject-btn-group">
                      <button
                        className="action-pill-btn secondary sm"
                        onClick={() => setRejectingId(null)}
                      >
                        Hủy
                      </button>
                      <button
                        className="action-pill-btn danger sm"
                        disabled={!rejectNote.trim() || isProcessing}
                        onClick={() => handleRejectAction(p)}
                      >
                        Xác nhận từ chối
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="proposal-actions-row">
                    <button
                      className="action-pill-btn danger"
                      disabled={isProcessing}
                      onClick={() => setRejectingId(p.proposal_id)}
                    >
                      <XCircle size={15} />
                      <span>Từ chối</span>
                    </button>
                    <button
                      className="action-pill-btn primary"
                      disabled={isProcessing}
                      onClick={() => handleApproveAction(p)}
                    >
                      {isProcessing ? <RefreshCw size={15} className="spin-icon" /> : <Check size={15} />}
                      <span>Phê duyệt & Kích hoạt</span>
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};

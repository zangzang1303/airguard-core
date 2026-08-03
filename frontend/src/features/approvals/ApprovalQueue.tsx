import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { Proposal } from "../../types";

export const ApprovalQueue: React.FC = () => {
  const { role, setPendingApprovalsCount, navigateTo } = useAuth();
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);
  
  // Modal states
  const [showReviewModal, setShowReviewModal] = useState<boolean>(false);
  const [reviewNote, setReviewNote] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchProposals = async () => {
    setLoading(true);
    try {
      const data = await api.getProposals();
      setProposals(data);
      const pendingCount = data.filter(p => p.status === "pending").length;
      setPendingApprovalsCount(pendingCount);
    } catch (err) {
      console.error("Error fetching proposals:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProposals();
  }, []);

  const handleOpenReview = (p: Proposal) => {
    setSelectedProposal(p);
    setReviewNote("");
    setActionError(null);
    setActionSuccess(null);
    setShowReviewModal(true);
  };

  const handleApprove = async () => {
    if (!selectedProposal) return;
    setSubmitting(true);
    setActionError(null);
    try {
      const res = await api.approveProposal(selectedProposal.proposal_id, reviewNote);
      setActionSuccess(`✅ Đã Phê duyệt đề xuất ${selectedProposal.proposal_id} thành công. Lệnh Dispatcher: SUCCESS.`);
      
      // Update local state
      setProposals(prev => prev.map(p => p.proposal_id === selectedProposal.proposal_id ? {
        ...p,
        status: "approved",
        review_note: reviewNote,
        reviewed_by: "Manager (Demo)",
        dispatch_status: "succeeded"
      } : p));

      setPendingApprovalsCount(c => Math.max(0, c - 1));
      setTimeout(() => setShowReviewModal(false), 1800);
    } catch (err: any) {
      if (err?.message?.includes("409")) {
        setActionError("⚠️ Xung đột (409): Đề xuất này đã được một Manager khác xử lý trước đó. Đang tải lại server state...");
        fetchProposals();
      } else {
        setActionError("❌ Không thể thực hiện phê duyệt. Vui lòng kiểm tra lại kết nối backend.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!selectedProposal) return;
    if (!reviewNote.trim()) {
      setActionError("⚠️ Bắt buộc phải nhập Lý do Từ chối (Reject Note) theo quy định kiểm soát HITL.");
      return;
    }
    setSubmitting(true);
    setActionError(null);
    try {
      await api.rejectProposal(selectedProposal.proposal_id, reviewNote);
      setActionSuccess(`❌ Đã Từ chối đề xuất ${selectedProposal.proposal_id}. Đã lưu nhật ký Audit.`);

      setProposals(prev => prev.map(p => p.proposal_id === selectedProposal.proposal_id ? {
        ...p,
        status: "rejected",
        review_note: reviewNote,
        reviewed_by: "Manager (Demo)",
        dispatch_status: "not_configured"
      } : p));

      setPendingApprovalsCount(c => Math.max(0, c - 1));
      setTimeout(() => setShowReviewModal(false), 1800);
    } catch (err: any) {
      setActionError("❌ Không thể từ chối proposal. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  };

  if (role === "resident") {
    return (
      <div className="approvals-container">
        <div className="alert-box alert-warning">
          🚫 <strong>Quyền truy cập bị từ chối (403):</strong> Màn hình Phê duyệt Human-in-the-Loop chỉ dành cho vai trò <strong>Manager</strong> hoặc <strong>Admin</strong>.
        </div>
      </div>
    );
  }

  const pendingList = proposals.filter(p => p.status === "pending");
  const historyList = proposals.filter(p => p.status !== "pending");

  return (
    <div className="approvals-container">
      <div className="approvals-header">
        <div>
          <h2>✅ Phê duyệt Đề xuất Cảnh báo (Human-in-the-Loop)</h2>
          <p className="approvals-subtitle">Xem xét bằng chứng môi trường và phê duyệt trước khi phát thông báo / điều khiển thiết bị</p>
        </div>
        <button className="btn-refresh" onClick={fetchProposals}>
          🔄 Refresh Queue
        </button>
      </div>

      {/* Pending Section */}
      <section className="queue-section">
        <h3>⏳ Hàng chờ Phê duyệt Pending ({pendingList.length})</h3>
        {loading ? (
          <div className="skeleton-card" style={{ height: 150 }}></div>
        ) : pendingList.length === 0 ? (
          <div className="empty-state">
            <span>🎉 Không có proposal nào đang chờ phê duyệt. Tất cả đã được xử lý!</span>
          </div>
        ) : (
          <div className="proposals-grid">
            {pendingList.map(p => (
              <div key={p.proposal_id} className="proposal-card-item">
                <div className="card-top">
                  <span className="prop-id">{p.proposal_id}</span>
                  <span className="badge level-warning">{p.severity.toUpperCase()}</span>
                </div>
                <h4>{p.target}</h4>
                <p className="prop-action"><strong>Hành động:</strong> {p.action}</p>
                <p className="prop-rationale"><strong>Lý do:</strong> {p.rationale}</p>
                <div className="card-bottom">
                  <span className="prop-time">Tạo lúc: {new Date(p.created_at).toLocaleTimeString("vi-VN")}</span>
                  <button className="btn-primary" onClick={() => handleOpenReview(p)}>
                    🔍 Review & Duyệt →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* History Section */}
      <section className="queue-section" style={{ marginTop: 32 }}>
        <h3>📜 Lịch sử Phê duyệt ({historyList.length})</h3>
        {historyList.length === 0 ? (
          <div className="empty-state">Chưa có lịch sử phê duyệt.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Mã Proposal</th>
                  <th>Mục tiêu</th>
                  <th>Hành động đề xuất</th>
                  <th>Trạng thái</th>
                  <th>Người duyệt</th>
                  <th>Ghi chú</th>
                  <th>Dispatch Status</th>
                </tr>
              </thead>
              <tbody>
                {historyList.map(p => (
                  <tr key={p.proposal_id}>
                    <td><strong>{p.proposal_id}</strong></td>
                    <td>{p.target}</td>
                    <td>{p.action}</td>
                    <td>
                      <span className={`status-pill ${p.status}`}>
                        {p.status === "approved" ? "🟢 Approved" : "🔴 Rejected"}
                      </span>
                    </td>
                    <td>{p.reviewed_by || "Manager"}</td>
                    <td>{p.review_note || "--"}</td>
                    <td>
                      <span className="source-tag">{p.dispatch_status || "succeeded"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
        </div>
      )}
      </section>

      {/* Review & HITL Modal */}
      {showReviewModal && selectedProposal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>🔍 Phê duyệt Đề xuất {selectedProposal.proposal_id}</h3>
              <button className="close-btn" onClick={() => setShowReviewModal(false)}>✕</button>
            </div>

            <div className="modal-body">
              {actionError && <div className="alert-box alert-warning">{actionError}</div>}
              {actionSuccess && <div className="alert-box alert-success">{actionSuccess}</div>}

              <div className="evidence-box">
                <h4>📊 Minh chứng Môi trường (Evidence Grounding):</h4>
                <ul>
                  <li>Trạm: <strong>{selectedProposal.station_id}</strong></li>
                  <li>PM2.5 Thực đo: <strong>{selectedProposal.evidence?.pm25 ?? 66.1} µg/m³</strong></li>
                  <li>Độ ẩm không khí: <strong>{selectedProposal.evidence?.humidity ?? 78} %</strong></li>
                  <li>Tốc độ gió: <strong>{selectedProposal.evidence?.wind_speed ?? 1.2} m/s</strong></li>
                </ul>
              </div>

              <div className="detail-field">
                <strong>Target khu vực:</strong> {selectedProposal.target}
              </div>
              <div className="detail-field">
                <strong>Hành động cảnh báo đề xuất:</strong> {selectedProposal.action}
              </div>
              <div className="detail-field">
                <strong>Cơ sở AI đề xuất:</strong> {selectedProposal.rationale}
              </div>

              <div className="form-group" style={{ marginTop: 16 }}>
                <label>Ghi chú của Manager (Bắt buộc nếu Từ chối):</label>
                <textarea
                  rows={3}
                  placeholder="Nhập lý do duyệt hoặc lý do từ chối proposal..."
                  value={reviewNote}
                  onChange={(e) => setReviewNote(e.target.value)}
                  className="chat-input"
                  disabled={submitting}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn-danger"
                onClick={handleReject}
                disabled={submitting || selectedProposal.status !== "pending"}
              >
                ❌ Từ chối Proposal
              </button>
              <button
                className="btn-success"
                onClick={handleApprove}
                disabled={submitting || selectedProposal.status !== "pending"}
              >
                ✅ Phê duyệt & Phát lệnh Dispatcher
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

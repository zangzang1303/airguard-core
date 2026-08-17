import React, { useEffect, useMemo, useState } from "react";
import { Check, RefreshCw, Search, ShieldCheck, ShieldX, X } from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { IconButton } from "../../components/common/IconButton";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { Proposal } from "../../types";

type ApprovalTab = "pending" | "approved" | "rejected";

const uniquePendingStationCount = (items: Proposal[]) => new Set(
  items.filter((proposal) => proposal.status === "pending").map((proposal) => proposal.station_id),
).size;

export const ApprovalQueue: React.FC = () => {
  const { role, userId, setPendingApprovalsCount } = useAuth();
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ApprovalTab>("pending");
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);
  const [reviewNote, setReviewNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchProposals = async () => {
    setLoading(true);
    try {
      const data = await api.getProposals({ userId, role: "manager" });
      setProposals(data);
      setPendingApprovalsCount(uniquePendingStationCount(data));
    } catch {
      setActionError("Không thể tải đề xuất từ server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (role === "manager") {
      fetchProposals();
    } else {
      setLoading(false);
    }
  }, [role]);

  const displayProposals = useMemo(() => {
    const pendingStations = new Set<string>();
    return proposals.filter((proposal) => {
      if (proposal.status !== "pending") return true;
      if (pendingStations.has(proposal.station_id)) return false;
      pendingStations.add(proposal.station_id);
      return true;
    });
  }, [proposals]);
  const tabCounts = useMemo(() => ({
    pending: displayProposals.filter((proposal) => proposal.status === "pending").length,
    approved: proposals.filter((proposal) => proposal.status === "approved").length,
    rejected: proposals.filter((proposal) => proposal.status === "rejected").length,
  }), [displayProposals, proposals]);
  const visibleProposals = displayProposals.filter((proposal) => proposal.status === activeTab);

  const openReview = (proposal: Proposal) => {
    setSelectedProposal(proposal);
    setReviewNote("");
    setActionError(null);
    setActionSuccess(null);
  };

  const updateProposal = (updatedProposal: Proposal) => {
    setProposals((current) => current.map((proposal) => proposal.proposal_id === updatedProposal.proposal_id ? updatedProposal : proposal));
    setSelectedProposal(updatedProposal);
    setPendingApprovalsCount((count) => Math.max(0, count - 1));
  };

  const handleApprove = async () => {
    if (!selectedProposal) return;
    setSubmitting(true);
    setActionError(null);
    try {
      const result = await api.approveProposal(selectedProposal.proposal_id, selectedProposal.version, reviewNote, { userId, role: "manager" });
      updateProposal(result);
      setActionSuccess(`Đã phê duyệt ${selectedProposal.proposal_id}. Quyết định đã được ghi nhận.`);
    } catch {
      // Reconcile once in case the server committed but the browser lost the response.
      try {
        const latest = await api.getProposals({ userId, role: "manager" });
        const serverProposal = latest.find((proposal) => proposal.proposal_id === selectedProposal.proposal_id);
        if (serverProposal?.status === "approved") {
          updateProposal(serverProposal);
          setActionSuccess(`Đã phê duyệt ${selectedProposal.proposal_id}. Quyết định đã được ghi nhận.`);
          return;
        }
      } catch {
        // Keep the original error when reconciliation is unavailable.
      }
      setActionError("Không thể phê duyệt đề xuất. Vui lòng tải lại trạng thái server và thử lại.");
    } finally { setSubmitting(false); }
  };

  const handleReject = async () => {
    if (!selectedProposal) return;
    if (!reviewNote.trim()) {
      setActionError("Vui lòng nhập lý do từ chối.");
      return;
    }
    setSubmitting(true);
    setActionError(null);
    try {
      const result = await api.rejectProposal(selectedProposal.proposal_id, selectedProposal.version, reviewNote, { userId, role: "manager" });
      updateProposal(result);
      setActionSuccess(`Đã từ chối ${selectedProposal.proposal_id}. Không có hành động nào được dispatch.`);
    } catch {
      setActionError("Không thể từ chối đề xuất. Vui lòng thử lại.");
    } finally { setSubmitting(false); }
  };

  if (role !== "manager") {
    return <div className="approvals-container"><PageHeader title="Phê duyệt đề xuất" description="Xem xét bằng chứng trước khi đưa ra quyết định." /><div className="alert-box alert-warning"><ShieldX size={18} /> Màn hình chỉ dành cho Manager hoặc Admin.</div></div>;
  }

  return (
    <div className="approvals-container">
      <PageHeader
        title="Phê duyệt đề xuất cảnh báo"
        description="Hàng chờ Human-in-the-Loop · kiểm tra evidence trước khi phê duyệt hoặc từ chối."
        actions={<Button variant="outline" size="sm" onClick={fetchProposals} disabled={loading}><RefreshCw className={loading ? "is-spinning" : ""} size={16} />{loading ? "Đang làm mới" : "Làm mới"}</Button>}
      />

      <section className="approval-workspace">
        {proposals.length > displayProposals.length && <div className="alert-box alert-warning">Chỉ hiển thị đề xuất đang chờ mới nhất cho mỗi trạm. Các đề xuất cũ vẫn được lưu trong audit.</div>}
        <div className="approval-tabs" role="tablist" aria-label="Trạng thái đề xuất">
          {(["pending", "approved", "rejected"] as ApprovalTab[]).map((tab) => (
            <button key={tab} type="button" role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? "is-active" : ""} onClick={() => setActiveTab(tab)}>
              {tab === "pending" ? "Chờ phê duyệt" : tab === "approved" ? "Đã phê duyệt" : "Đã từ chối"}
              <span>{tabCounts[tab]}</span>
            </button>
          ))}
        </div>

        {loading ? <div className="skeleton-card" style={{ height: 240 }} /> : visibleProposals.length === 0 ? (
          <div className="empty-state">Không có đề xuất trong trạng thái này.</div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table approval-table">
              <thead><tr><th>Mã proposal</th><th>Trạm / Mục tiêu</th><th>Severity</th><th>Thời gian</th><th>Trạng thái</th><th>Hành động</th></tr></thead>
              <tbody>{visibleProposals.map((proposal) => (
                <tr key={proposal.proposal_id}>
                  <td><strong>{proposal.proposal_id}</strong></td>
                  <td><strong>{proposal.station_id}</strong><small>{proposal.target}</small></td>
                  <td><span className="badge level-warning">{proposal.severity.toUpperCase()}</span></td>
                  <td>{new Date(proposal.created_at).toLocaleString("vi-VN")}</td>
                  <td><StatusBadge status={proposal.status} /></td>
                  <td><Button variant={proposal.status === "pending" ? "primary" : "outline"} size="sm" onClick={() => openReview(proposal)}><Search size={15} />{proposal.status === "pending" ? "Xem xét" : "Xem chi tiết"}</Button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>

      {selectedProposal && (
        <div className="modal-overlay" role="presentation">
          <div className="modal-content approval-detail-modal" role="dialog" aria-modal="true" aria-labelledby="approval-detail-title">
            <div className="modal-header"><div><span className="dashboard-eyebrow">Proposal detail</span><h3 id="approval-detail-title">{selectedProposal.proposal_id}</h3></div><IconButton label="Đóng" onClick={() => setSelectedProposal(null)}><X size={18} /></IconButton></div>
            <div className="modal-body">
              {actionError && <div className="alert-box alert-warning">{actionError}</div>}
              {actionSuccess && <div className="alert-box alert-success">{actionSuccess}</div>}
              <div className="approval-evidence-grid">
                <div><span>Trạm</span><strong>{selectedProposal.station_id}</strong></div>
                <div><span>AQI</span><strong>{selectedProposal.evidence?.aqi ?? "—"}</strong></div>
                <div><span>PM2.5</span><strong>{selectedProposal.evidence?.pm25 ?? "—"} µg/m³</strong></div>
                <div><span>CO₂</span><strong>{selectedProposal.evidence?.co2 ?? "—"} ppm</strong></div>
                <div><span>Tiếng ồn</span><strong>{selectedProposal.evidence?.noise_db ?? "—"} dB</strong></div>
                <div><span>Nhiệt độ</span><strong>{selectedProposal.evidence?.temperature ?? "—"} °C</strong></div>
              </div>
              <dl className="approval-detail-list"><div><dt>Mục tiêu</dt><dd>{selectedProposal.target}</dd></div><div><dt>Hành động đề xuất</dt><dd>{selectedProposal.action}</dd></div><div><dt>Cơ sở đề xuất</dt><dd>{selectedProposal.rationale}</dd></div></dl>
              {selectedProposal.status === "pending" && <label className="form-group"><span>Ghi chú của Manager</span><textarea rows={3} value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} placeholder="Nhập ghi chú; bắt buộc khi từ chối" disabled={submitting} /></label>}
            </div>
            <div className="modal-footer">
              {selectedProposal.status === "pending" ? <><Button variant="destructive" onClick={handleReject} disabled={submitting}><X size={16} />Từ chối</Button><Button variant="success" onClick={handleApprove} disabled={submitting}><Check size={16} />Phê duyệt</Button></> : <Button variant="outline" onClick={() => setSelectedProposal(null)}>Đóng</Button>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

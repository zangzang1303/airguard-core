import React, { useEffect, useMemo, useState } from "react";
import { Eye, FileClock, LockKeyhole, RefreshCw, RotateCcw, X } from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { IconButton } from "../../components/common/IconButton";
import { PageHeader } from "../../components/common/PageHeader";
import { StatusBadge } from "../../components/common/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { AuditLogEntry } from "../../types";

export const AuditLog: React.FC = () => {
  const { role } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [actorFilter, setActorFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("all");

  const fetchLogs = async () => {
    setLoading(true);
    try { setLogs(await api.getAuditLogs()); } finally { setLoading(false); }
  };
  useEffect(() => { fetchLogs(); }, []);

  const actors = useMemo(() => Array.from(new Set(logs.map((log) => log.actor))), [logs]);
  const actions = useMemo(() => Array.from(new Set(logs.map((log) => log.action))), [logs]);
  const visibleLogs = useMemo(() => logs.filter((log) =>
    (actorFilter === "all" || log.actor === actorFilter)
    && (actionFilter === "all" || log.action === actionFilter)), [actionFilter, actorFilter, logs]);

  if (role === "resident") {
    return <div className="audit-container"><PageHeader title="Lịch sử hoạt động" description="Truy vết các hành động quan trọng trong hệ thống." /><div className="alert-box alert-warning"><LockKeyhole size={18} /> Audit Log chỉ dành cho Manager và Admin.</div></div>;
  }

  return (
    <div className="audit-container">
      <PageHeader
        title="Lịch sử hoạt động"
        description="Nhật ký append-only cho đề xuất, quyết định phê duyệt và kết quả xử lý."
        actions={<Button variant="outline" size="sm" onClick={fetchLogs} disabled={loading}><RefreshCw className={loading ? "is-spinning" : ""} size={16} />{loading ? "Đang làm mới" : "Làm mới"}</Button>}
      />

      <section className="audit-filter-bar" aria-label="Bộ lọc Audit Log">
        <label><span>Người thực hiện</span><select value={actorFilter} onChange={(event) => setActorFilter(event.target.value)}><option value="all">Tất cả</option>{actors.map((actor) => <option key={actor}>{actor}</option>)}</select></label>
        <label><span>Loại hành động</span><select value={actionFilter} onChange={(event) => setActionFilter(event.target.value)}><option value="all">Tất cả</option>{actions.map((action) => <option key={action}>{action}</option>)}</select></label>
        <Button variant="ghost" size="sm" onClick={() => { setActorFilter("all"); setActionFilter("all"); }}><RotateCcw size={15} />Đặt lại</Button>
      </section>

      {loading ? <div className="skeleton-card" style={{ height: 250 }} /> : visibleLogs.length === 0 ? <div className="empty-state">Không có bản ghi phù hợp bộ lọc.</div> : (
        <div className="table-wrapper"><table className="data-table audit-table">
          <thead><tr><th>Thời gian</th><th>Người thực hiện</th><th>Mã hành động</th><th>Đối tượng</th><th>Kết quả</th><th>Request ID</th><th>Chi tiết</th></tr></thead>
          <tbody>{visibleLogs.map((log) => <tr key={log.id}>
            <td>{new Date(log.time).toLocaleString("vi-VN")}</td><td><strong>{log.actor}</strong></td><td><code>{log.action}</code></td><td>{log.target}</td><td><StatusBadge status={log.outcome} label={log.outcome} /></td><td><code>{log.correlation_id}</code></td><td><Button variant="outline" size="sm" onClick={() => setSelectedLog(log)}><Eye size={15} />Xem</Button></td>
          </tr>)}</tbody>
        </table></div>
      )}

      {selectedLog && <div className="modal-overlay"><div className="modal-content audit-detail-modal" role="dialog" aria-modal="true">
        <div className="modal-header"><h3><FileClock size={18} /> Chi tiết Audit Record {selectedLog.id}</h3><IconButton label="Đóng" onClick={() => setSelectedLog(null)}><X size={18} /></IconButton></div>
        <div className="modal-body"><dl className="audit-detail-list">
          <div><dt>Thời gian</dt><dd>{new Date(selectedLog.time).toLocaleString("vi-VN")}</dd></div><div><dt>Người thực hiện</dt><dd>{selectedLog.actor}</dd></div><div><dt>Mã hành động</dt><dd><code>{selectedLog.action}</code></dd></div><div><dt>Đối tượng</dt><dd>{selectedLog.target}</dd></div><div><dt>Kết quả</dt><dd><StatusBadge status={selectedLog.outcome} label={selectedLog.outcome} /></dd></div><div><dt>Request / Correlation ID</dt><dd><code>{selectedLog.correlation_id}</code></dd></div>
        </dl></div><div className="modal-footer"><Button variant="outline" onClick={() => setSelectedLog(null)}>Đóng</Button></div>
      </div></div>}
    </div>
  );
};

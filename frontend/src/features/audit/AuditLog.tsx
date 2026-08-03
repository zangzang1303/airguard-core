import React, { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { AuditLogEntry } from "../../types";

export const AuditLog: React.FC = () => {
  const { role } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  useEffect(() => {
    const fetchLogs = async () => {
      setLoading(true);
      try {
        const data = await api.getAuditLogs();
        setLogs(data);
      } catch (err) {
        console.error("Error fetching audit logs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  if (role === "resident") {
    return (
      <div className="audit-container">
        <div className="alert-box alert-warning">
          🔒 <strong>Quyền truy cập bị từ chối (403):</strong> Nhật ký Audit Log chỉ dành cho tài khoản <strong>Manager</strong> và <strong>Admin</strong>.
        </div>
      </div>
    );
  }

  return (
    <div className="audit-container">
      <div className="audit-header">
        <div>
          <h2>📜 Nhật ký Audit Log (Append-Only Traceability)</h2>
          <p className="audit-subtitle">Truy vết chi tiết lịch sử thao tác tạo đề xuất, phê duyệt, từ chối và phát lệnh thiết bị</p>
        </div>
        <button className="btn-refresh" onClick={() => api.getAuditLogs().then(setLogs)}>
          🔄 Refresh Log
        </button>
      </div>

      {loading ? (
        <div className="skeleton-card" style={{ height: 250 }}></div>
      ) : logs.length === 0 ? (
        <div className="empty-state">Không có bản ghi audit log nào.</div>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mã Audit</th>
                <th>Thời gian</th>
                <th>Tác nhân (Actor)</th>
                <th>Hành động (Action)</th>
                <th>Đối tượng (Target)</th>
                <th>Kết quả (Outcome)</th>
                <th>Correlation ID</th>
                <th>Chi tiết</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td><strong>{log.id}</strong></td>
                  <td>{new Date(log.time).toLocaleString("vi-VN")}</td>
                  <td><span className="source-tag">{log.actor}</span></td>
                  <td><strong>{log.action}</strong></td>
                  <td>{log.target}</td>
                  <td>
                    <span className={`status-pill ${log.outcome.toLowerCase()}`}>
                      {log.outcome}
                    </span>
                  </td>
                  <td><code>{log.correlation_id}</code></td>
                  <td>
                    <button className="btn-secondary-sm" onClick={() => setSelectedLog(log)}>
                      👁️ Xem JSON
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* JSON Modal */}
      {selectedLog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>📜 Chi tiết Audit Record {selectedLog.id}</h3>
              <button className="close-btn" onClick={() => setSelectedLog(null)}>✕</button>
            </div>
            <div className="modal-body">
              <pre className="json-viewer">
                {JSON.stringify(selectedLog, null, 2)}
              </pre>
            </div>
            <div className="modal-footer">
              <button className="btn-outline" onClick={() => setSelectedLog(null)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

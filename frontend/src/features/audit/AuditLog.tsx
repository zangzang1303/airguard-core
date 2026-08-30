import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, BellRing, Bot, CheckCircle2, ChevronRight, CircleAlert, Clock3,
  FileCheck2, FilePlus2, FileSearch, Filter, LogIn, RefreshCw, RotateCcw,
  Search, Send, Server, ShieldCheck, UserCog, UserRound, Wrench, X, XCircle,
} from "lucide-react";
import { api } from "../../api/client";
import { Button } from "../../components/common/Button";
import { IconButton } from "../../components/common/IconButton";
import { useAuth } from "../../context/AuthContext";
import { AuditLogEntry, Station } from "../../types";
import { useDraggableFloatingPanel } from "../floating";
import "./AuditLog.css";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const formatVnDateTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { primary: value, relative: "" };
  const primary = date.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  const minutes = Math.floor((Date.now() - date.getTime()) / 60000);
  const relative = minutes < 1 ? "Vừa xong" : minutes < 60 ? `${minutes} phút trước` : minutes < 1440 ? `${Math.floor(minutes / 60)} giờ trước` : `${Math.floor(minutes / 1440)} ngày trước`;
  return { primary, relative };
};

type ActionMeta = { label: string; verb: string; Icon: React.ElementType; tone: "ai" | "alert" | "approval" | "account" | "device" | "system" };
const action = (label: string, verb: string, Icon: React.ElementType, tone: ActionMeta["tone"]): ActionMeta => ({ label, verb, Icon, tone });
const ACTIONS: Record<string, ActionMeta> = {
  "agent.auto_proposal.create": action("AI tạo đề xuất cảnh báo", "tạo đề xuất cảnh báo", Bot, "ai"),
  "agent.auto_proposal.failure": action("AI không thể tạo đề xuất", "không thể tạo đề xuất cảnh báo", Bot, "ai"),
  "agent.auto_proposal.skipped": action("AI bỏ qua đề xuất", "bỏ qua đề xuất cảnh báo", Bot, "ai"),
  "auth.demo_login": action("Đăng nhập hệ thống", "đăng nhập hệ thống", LogIn, "account"),
  "auth.login.success": action("Đăng nhập hệ thống", "đăng nhập hệ thống", LogIn, "account"),
  "auth.login.failed": action("Đăng nhập không thành công", "không thể đăng nhập", LogIn, "account"),
  "auth.logout": action("Đăng xuất hệ thống", "đăng xuất hệ thống", LogIn, "account"),
  "auth.register": action("Tạo tài khoản", "tạo tài khoản", UserRound, "account"),
  "auth.profile_updated": action("Cập nhật hồ sơ", "cập nhật hồ sơ", UserCog, "account"),
  "alert.create": action("Tạo cảnh báo", "tạo cảnh báo", BellRing, "alert"),
  "alert.auto_resolve": action("Đóng cảnh báo tự động", "đóng cảnh báo", CheckCircle2, "alert"),
  "alert.manual_resolve": action("Đóng cảnh báo", "đóng cảnh báo", CheckCircle2, "alert"),
  "alert.sensor_offline": action("Phát hiện trạm mất kết nối", "ghi nhận trạm mất kết nối", CircleAlert, "alert"),
  "alert.sensor_recovered": action("Trạm hoạt động trở lại", "ghi nhận trạm hoạt động trở lại", Activity, "alert"),
  "approval.create": action("Tạo đề xuất cảnh báo", "tạo đề xuất cảnh báo", FilePlus2, "approval"),
  "approval.approve": action("Phê duyệt đề xuất", "phê duyệt đề xuất", CheckCircle2, "approval"),
  "approval.quick_approve": action("Phê duyệt đề xuất", "phê duyệt đề xuất", CheckCircle2, "approval"),
  "approval.reject": action("Từ chối đề xuất", "từ chối đề xuất", XCircle, "approval"),
  "approval.expire": action("Đề xuất hết hiệu lực", "đánh dấu đề xuất hết hiệu lực", Clock3, "approval"),
  "approval.dispatch.failure": action("Gửi lệnh thiết bị không thành công", "không thể gửi lệnh thiết bị", Send, "device"),
  "demo_station_override.set": action("Cập nhật dữ liệu mô phỏng", "cập nhật dữ liệu mô phỏng", Wrench, "system"),
  "demo_station_override.clear": action("Khôi phục dữ liệu mô phỏng", "khôi phục dữ liệu mô phỏng", Wrench, "system"),
  "measurement.accepted": action("Nhận dữ liệu trạm", "ghi nhận dữ liệu trạm", Activity, "system"),
  CREATE_PROPOSAL: action("Tạo đề xuất cảnh báo", "tạo đề xuất cảnh báo", FilePlus2, "approval"),
  APPROVE_PROPOSAL: action("Phê duyệt đề xuất", "phê duyệt đề xuất", CheckCircle2, "approval"),
  REJECT_PROPOSAL: action("Từ chối đề xuất", "từ chối đề xuất", XCircle, "approval"),
};
const FALLBACK_ACTION = action("Hoạt động hệ thống", "thực hiện một hoạt động hệ thống", Activity, "system");
Object.assign(ACTIONS, {
  "device_command.dispatch.enqueued": action("Xếp hàng lệnh thiết bị", "xếp hàng lệnh thiết bị", Send, "device"),
  "device_command.dispatch.prepare": action("Chuẩn bị gửi lệnh thiết bị", "chuẩn bị gửi lệnh thiết bị", Send, "device"),
  "device_command.dispatch": action("Gửi lệnh thiết bị", "gửi lệnh thiết bị", Send, "device"),
  "device_command.dispatch.failure": action("Gửi lệnh thiết bị không thành công", "không thể gửi lệnh thiết bị", Send, "device"),
  "device_command.ack": action("Thiết bị xác nhận lệnh", "ghi nhận thiết bị xác nhận lệnh", CheckCircle2, "device"),
  "device_command.ack.unmatched": action("Xác nhận thiết bị không khớp", "ghi nhận xác nhận thiết bị không khớp", CircleAlert, "device"),
});
const getActionMeta = (value: string) => ACTIONS[value] ?? FALLBACK_ACTION;

const getActorMeta = (log: AuditLogEntry) => {
  const source = `${log.actor_type ?? ""} ${log.actor_role ?? ""} ${log.actor ?? ""}`.toLowerCase();
  if (source.includes("agent") || source.includes("ai")) return { label: "AI Alert Agent", Icon: Bot, tone: "ai" };
  if (source.includes("admin")) return { label: "Quản trị viên", Icon: ShieldCheck, tone: "admin" };
  if (source.includes("manager")) return { label: "Quản lý", Icon: UserCog, tone: "manager" };
  if (source.includes("system") || source.includes("backend") || !log.actor || UUID_PATTERN.test(log.actor)) return { label: "Hệ thống", Icon: Server, tone: "system" };
  return { label: "Người dùng", Icon: UserRound, tone: "user" };
};

const getStationForLog = (log: AuditLogEntry, stations: Station[]) =>
  stations.find((item) => `${log.station_id ?? ""} ${log.target} ${log.detail ?? ""}`.includes(item.station_id));

const getTargetLabel = (log: AuditLogEntry, stations: Station[] = []) => {
  const [type, id] = log.entity_type ? [log.entity_type, log.entity_id] : log.target.split(":", 2);
  const entity = (type || "").toLowerCase();
  const number = id && /^\d+$/.test(id) ? ` #${id}` : "";
  const station = getStationForLog(log, stations);
  const area = station ? ` · ${station.station_name}` : "";
  if (entity.includes("alert")) return `Cảnh báo${number}${area}`;
  if (entity.includes("approval") || entity.includes("proposal")) return `Đề xuất cảnh báo${number}${area}`;
  if (entity.includes("station")) return id && !UUID_PATTERN.test(id) ? `Trạm ${id}${area}` : `Trạm quan trắc${area}`;
  if (entity.includes("user")) return `Người dùng${number}`;
  if (entity.includes("device")) return id && !UUID_PATTERN.test(id) ? `Thiết bị ${id}${area}` : `Thiết bị${area}`;
  if (entity.includes("measurement")) return `Dữ liệu trạm${area}`;
  return `Bản ghi hệ thống${area}`;
};

const getOutcomeMeta = (value: string) => {
  const outcome = value.toLowerCase();
  if (["failure", "failed", "rejected", "error"].includes(outcome)) return { label: "Thất bại", tone: "failure", Icon: XCircle };
  if (["pending", "processing", "in_progress"].includes(outcome)) return { label: "Đang xử lý", tone: "pending", Icon: Clock3 };
  return { label: "Thành công", tone: "success", Icon: CheckCircle2 };
};

const getSummary = (log: AuditLogEntry, stations: Station[]) => {
  const station = getStationForLog(log, stations);
  return `${getActorMeta(log).label} đã ${getActionMeta(log.action).verb}${station ? ` cho trạm ${station.station_name}` : ""}.`;
};

interface AuditLogProps { onClose?: () => void; stations?: Station[]; }

export const AuditLog: React.FC<AuditLogProps> = ({ onClose, stations = [] }) => {
  const { role } = useAuth();
  const { containerProps, handleProps } = useDraggableFloatingPanel({ panelId: "audit", group: "modal" });
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [actorFilter, setActorFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("all");
  const [stationFilter, setStationFilter] = useState("all");
  const [outcomeFilter, setOutcomeFilter] = useState("all");
  const [timeRangeFilter, setTimeRangeFilter] = useState("all");

  const fetchLogs = async () => {
    setLoading(true); setError(null);
    try {
      setLogs(await api.getManagerActivityLog());
    }
    catch (err: any) { setError(err?.message ?? "Không thể tải nhật ký hoạt động. Vui lòng thử lại."); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (role === "manager" || role === "admin") fetchLogs(); else setLoading(false); }, [role]);

  const actors = useMemo(() => Array.from(new Map(logs.map((log) => [log.actor, getActorMeta(log).label])).entries()), [logs]);
  const actions = useMemo(() => Array.from(new Map(logs.map((log) => [log.action, getActionMeta(log.action).label])).entries()), [logs]);
  const hasActiveFilters = Boolean(searchTerm.trim()) || [actorFilter, actionFilter, stationFilter, outcomeFilter, timeRangeFilter].some((value) => value !== "all");
  const resetFilters = () => { setSearchTerm(""); setActorFilter("all"); setActionFilter("all"); setStationFilter("all"); setOutcomeFilter("all"); setTimeRangeFilter("all"); };

  const filteredLogs = useMemo(() => logs.filter((log) => {
    const summary = getSummary(log, stations);
    const searchText = `${getActorMeta(log).label} ${getActionMeta(log.action).label} ${getTargetLabel(log, stations)} ${summary}`.toLowerCase();
    if (searchTerm.trim() && !searchText.includes(searchTerm.trim().toLowerCase())) return false;
    if (actorFilter !== "all" && log.actor !== actorFilter) return false;
    if (actionFilter !== "all" && log.action !== actionFilter) return false;
    if (stationFilter !== "all" && !`${log.target} ${log.detail ?? ""}`.includes(stationFilter)) return false;
    if (outcomeFilter !== "all" && getOutcomeMeta(log.outcome).tone !== outcomeFilter) return false;
    const logTime = new Date(log.time).getTime(); const hoursAgo = (Date.now() - logTime) / 3600000;
    if (timeRangeFilter === "today" && logTime < new Date().setHours(0, 0, 0, 0)) return false;
    if (timeRangeFilter === "24h" && hoursAgo > 24) return false;
    if (timeRangeFilter === "7d" && hoursAgo > 168) return false;
    return true;
  }), [logs, searchTerm, actorFilter, actionFilter, stationFilter, outcomeFilter, timeRangeFilter, stations]);

  if (role !== "manager" && role !== "admin") return <div className="audit-empty-state"><ShieldCheck size={28} /><h3>Chỉ quản lý mới có thể xem nhật ký hoạt động</h3></div>;

  return <div {...containerProps} className="audit-explorer-container audit-manager-log">
    <header className="audit-explorer-header">
      <div className="audit-explorer-title-group"><div className="audit-explorer-title-row" {...handleProps}><div className="audit-explorer-title-icon"><FileCheck2 size={20} /></div><div><h2 className="audit-explorer-title">Nhật ký quyết định BQL</h2><p className="audit-explorer-subtitle">Danh sách dùng chung, chỉ gồm các yêu cầu đã được duyệt hoặc từ chối.</p></div></div><span className="audit-pill-badge audit-pill-badge--count">{filteredLogs.length} quyết định</span></div>
      <div className="audit-header-actions no-drag" data-no-drag="true"><Button variant="outline" size="sm" onClick={fetchLogs} disabled={loading}><RefreshCw className={loading ? "is-spinning" : ""} size={15} />{loading ? "Đang cập nhật" : "Làm mới"}</Button>{onClose && <IconButton label="Đóng" onClick={onClose}><X size={18} /></IconButton>}</div>
    </header>

    <section className="audit-filter-card" aria-label="Bộ lọc nhật ký hoạt động"><div className="audit-filter-heading"><Filter size={16} /> Lọc hoạt động</div><div className="audit-search-input-wrap"><Search className="audit-search-icon" size={16} /><input className="audit-search-input" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Tìm hoạt động, người thực hiện hoặc trạm" /></div><div className="audit-filter-grid">
      <label className="audit-filter-field"><span>Trạm quan trắc</span><select className="audit-select-control" value={stationFilter} onChange={(event) => setStationFilter(event.target.value)}><option value="all">Tất cả trạm</option>{stations.map((station) => <option key={station.station_id} value={station.station_id}>{station.station_name}</option>)}</select></label>
      <label className="audit-filter-field"><span>Khoảng thời gian</span><select className="audit-select-control" value={timeRangeFilter} onChange={(event) => setTimeRangeFilter(event.target.value)}><option value="all">Mọi thời điểm</option><option value="today">Hôm nay</option><option value="24h">24 giờ qua</option><option value="7d">7 ngày qua</option></select></label>
      <label className="audit-filter-field"><span>Người thực hiện</span><select className="audit-select-control" value={actorFilter} onChange={(event) => setActorFilter(event.target.value)}><option value="all">Tất cả</option>{actors.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="audit-filter-field"><span>Loại hoạt động</span><select className="audit-select-control" value={actionFilter} onChange={(event) => setActionFilter(event.target.value)}><option value="all">Tất cả</option>{actions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="audit-filter-field"><span>Trạng thái</span><select className="audit-select-control" value={outcomeFilter} onChange={(event) => setOutcomeFilter(event.target.value)}><option value="all">Tất cả</option><option value="success">Thành công</option><option value="failure">Thất bại</option><option value="pending">Đang xử lý</option></select></label>
      <button type="button" className={`audit-reset-btn ${hasActiveFilters ? "active" : ""}`} onClick={resetFilters}><RotateCcw size={14} />Đặt lại</button>
    </div></section>

    <section className="audit-table-card">
      {loading ? <AuditTableSkeleton /> : error ? <AuditEmpty icon={<XCircle size={28} />} title="Không thể tải nhật ký quyết định" description={error} action={<Button variant="outline" size="sm" onClick={fetchLogs}>Thử lại</Button>} /> : filteredLogs.length === 0 ? <AuditEmpty icon={<FileSearch size={28} />} title={hasActiveFilters ? "Không tìm thấy yêu cầu phù hợp" : "Chưa có yêu cầu nào được duyệt hoặc từ chối"} description={hasActiveFilters ? "Hãy thử thay đổi bộ lọc hoặc từ khóa tìm kiếm." : "Các yêu cầu đang chờ duyệt không hiển thị trong danh sách này."} action={hasActiveFilters ? <Button variant="outline" size="sm" onClick={resetFilters}>Xóa bộ lọc</Button> : undefined} /> : <div className="audit-table-wrapper"><table className="audit-explorer-table"><thead><tr>{["Thời gian", "Người thực hiện", "Hoạt động", "Đối tượng", "Trạng thái", "Chi tiết"].map((heading) => <th key={heading}>{heading}</th>)}</tr></thead><tbody>{filteredLogs.map((log) => <AuditRow key={log.id} log={log} stations={stations} onDetails={setSelectedLog} />)}</tbody></table></div>}
    </section>
    {selectedLog && <AuditDetail log={selectedLog} stations={stations} onClose={() => setSelectedLog(null)} />}
  </div>;
};

const AuditRow: React.FC<{ log: AuditLogEntry; stations: Station[]; onDetails: (log: AuditLogEntry) => void }> = ({ log, stations, onDetails }) => {
  const actor = getActorMeta(log); const actionMeta = getActionMeta(log.action); const outcome = getOutcomeMeta(log.outcome); const time = formatVnDateTime(log.time); const ActorIcon = actor.Icon; const ActionIcon = actionMeta.Icon; const OutcomeIcon = outcome.Icon;
  return <tr><td><div className="audit-time-cell"><strong>{time.primary}</strong><span>{time.relative}</span></div></td><td><div className={`audit-actor-cell audit-actor-cell--${actor.tone}`}><span className="audit-actor-avatar"><ActorIcon size={15} /></span><span>{actor.label}</span></div></td><td><span className={`audit-action-label audit-action-label--${actionMeta.tone}`}><ActionIcon size={15} />{actionMeta.label}</span></td><td><span className="audit-target-tag">{getTargetLabel(log, stations)}</span></td><td><span className={`audit-outcome-pill audit-outcome-pill--${outcome.tone}`}><OutcomeIcon size={13} />{outcome.label}</span></td><td><div className="audit-detail-cell"><p>{getSummary(log, stations)}</p><button type="button" className="audit-detail-link" onClick={() => onDetails(log)}>Xem chi tiết <ChevronRight size={14} /></button></div></td></tr>;
};

const AuditTableSkeleton = () => <div className="audit-table-wrapper"><table className="audit-explorer-table"><thead><tr>{["Thời gian", "Người thực hiện", "Hoạt động", "Đối tượng", "Trạng thái", "Chi tiết"].map((heading) => <th key={heading}>{heading}</th>)}</tr></thead><tbody>{[1, 2, 3, 4, 5].map((row) => <tr key={row} className="audit-skeleton-row">{[1, 2, 3, 4, 5, 6].map((cell) => <td key={cell}><div className="audit-skeleton-box" /></td>)}</tr>)}</tbody></table></div>;
const AuditEmpty: React.FC<{ icon: React.ReactNode; title: string; description: string; action?: React.ReactNode }> = ({ icon, title, description, action }) => <div className="audit-empty-state"><div className="audit-empty-icon">{icon}</div><h3>{title}</h3><p>{description}</p>{action}</div>;

const AuditDetail: React.FC<{ log: AuditLogEntry; stations: Station[]; onClose: () => void }> = ({ log, stations, onClose }) => {
  const actor = getActorMeta(log); const actionMeta = getActionMeta(log.action); const outcome = getOutcomeMeta(log.outcome); const ActionIcon = actionMeta.Icon;
  return <div className="audit-detail-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Chi tiết hoạt động"><aside className="audit-detail-modal-card" onClick={(event) => event.stopPropagation()}><header className="audit-detail-modal-header"><div><span className={`audit-action-label audit-action-label--${actionMeta.tone}`}><ActionIcon size={15} />{actionMeta.label}</span><h3>Chi tiết hoạt động</h3></div><IconButton label="Đóng" onClick={onClose}><X size={18} /></IconButton></header><div className="audit-detail-modal-body"><p className="audit-detail-summary">{getSummary(log, stations)}</p><div className="audit-detail-grid"><div><span>Thời gian</span><strong>{formatVnDateTime(log.time).primary}</strong></div><div><span>Người thực hiện</span><strong>{actor.label}</strong></div><div><span>Đối tượng</span><strong>{getTargetLabel(log, stations)}</strong></div><div><span>Trạng thái</span><strong className={`audit-outcome-pill audit-outcome-pill--${outcome.tone}`}>{outcome.label}</strong></div></div><details className="audit-technical-details"><summary>Thông tin hệ thống</summary><dl><div><dt>Mã hoạt động</dt><dd>{log.action}</dd></div><div><dt>Người thực hiện (ID)</dt><dd>{log.actor || "—"}</dd></div><div><dt>Đối tượng (ID)</dt><dd>{log.entity_id ?? log.target ?? "—"}</dd></div><div><dt>Request ID</dt><dd>{log.correlation_id || "—"}</dd></div>{log.detail && <div><dt>Dữ liệu ghi nhận</dt><dd><pre>{log.detail}</pre></dd></div>}</dl></details></div></aside></div>;
};

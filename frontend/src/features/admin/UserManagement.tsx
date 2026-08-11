import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Clock3,
  Filter,
  Lock,
  MoreVertical,
  RefreshCw,
  Search,
  UserCheck,
  UserCog,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { userManagementApi } from "../../api/userManagement";
import {
  AdminAuditEntry,
  AdminUser,
  AdminUserStatus,
  UserGroup,
  UserRole,
} from "../../types";
import "./UserManagement.css";

type Filter = {
  query: string;
  role: UserRole | "all";
  status: AdminUserStatus | "all";
  region: string;
};

type DetailTab = "account" | "role" | "audit";

type MutationKind = "role" | "status";

type PendingAction = {
  kind: MutationKind;
  user: AdminUser;
  value: UserRole | AdminUserStatus;
} | null;

const roleLabel: Record<UserRole, string> = {
  admin: "Admin",
  manager: "Manager",
  resident: "Resident",
};

const groupLabel: Record<UserGroup, string> = {
  normal: "normal",
  sensitive: "sensitive",
  outdoor_sport: "outdoor_sport",
};

const statusLabel: Record<AdminUserStatus, string> = {
  active: "Active",
  disabled: "Disabled",
  invitation_pending: "Invitation pending",
};

const formatDate = (value: string | null) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
};

const getInitials = (user: AdminUser) =>
  user.avatar_initials ||
  user.full_name
    .split(" ")
    .slice(-2)
    .map((part) => part.charAt(0))
    .join("")
    .toUpperCase();

const renderStatusIcon = (status: AdminUserStatus) => {
  if (status === "active") return <CheckCircle2 size={13} />;
  if (status === "invitation_pending") return <Clock3 size={13} />;
  return <Ban size={13} />;
};

export const UserManagement: React.FC = () => {
  const { userName } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [audit, setAudit] = useState<AdminAuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>({
    query: "",
    role: "all",
    status: "all",
    region: "all",
  });
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("account");
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [mutationMessage, setMutationMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [menuFor, setMenuFor] = useState<string | null>(null);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await userManagementApi.getUsers();
      setUsers(data);
    } catch {
      setError("Không thể tải danh sách người dùng. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    if (!selectedUser) return;
    userManagementApi
      .getUserAudit(selectedUser.user_id)
      .then(setAudit)
      .catch(() => setAudit([]));
    setDetailTab("account");
  }, [selectedUser?.user_id]);

  const isSelf = (user: AdminUser) =>
    user.role === "admin" && user.full_name === userName;

  const filteredUsers = useMemo(() => {
    const q = filter.query.trim().toLowerCase();
    return users.filter((user) => {
      if (q && !`${user.full_name} ${user.email}`.toLowerCase().includes(q)) {
        return false;
      }
      if (filter.role !== "all" && user.role !== filter.role) return false;
      if (filter.status !== "all" && user.status !== filter.status)
        return false;
      if (filter.region !== "all" && user.region !== filter.region)
        return false;
      return true;
    });
  }, [users, filter]);

  const regionOptions = useMemo(
    () => Array.from(new Set(users.map((user) => user.region))).sort(),
    [users],
  );

  const resetFilters = () => {
    setFilter({ query: "", role: "all", status: "all", region: "all" });
  };

  const openUser = (user: AdminUser) => {
    setSelectedUser(user);
    setMenuFor(null);
    setMutationMessage(null);
  };

  const closeDrawer = () => {
    setSelectedUser(null);
    setMenuFor(null);
    setMutationMessage(null);
  };

  const confirmAction = (action: PendingAction) => {
    setReason("");
    setPendingAction(action);
  };

  const closeConfirm = () => {
    setPendingAction(null);
    setReason("");
  };

  const executeAction = async () => {
    if (!pendingAction) return;
    if (!reason.trim()) {
      setMutationMessage({
        type: "error",
        text: "Lý do thay đổi là bắt buộc cho hành động này.",
      });
      return;
    }
    setSubmitting(true);
    setMutationMessage(null);
    try {
      const { kind, user, value } = pendingAction;
      if (kind === "role") {
        await userManagementApi.updateRole(
          user.user_id,
          value as UserRole,
          reason.trim(),
          userName || "Quản trị viên",
        );
        setUsers((prev) =>
          prev.map((item) =>
            item.user_id === user.user_id
              ? { ...item, role: value as UserRole }
              : item,
          ),
        );
      } else {
        await userManagementApi.updateStatus(
          user.user_id,
          value as AdminUserStatus,
          reason.trim(),
          userName || "Quản trị viên",
        );
        setUsers((prev) =>
          prev.map((item) =>
            item.user_id === user.user_id
              ? { ...item, status: value as AdminUserStatus }
              : item,
          ),
        );
      }
      const updated = users.find((item) => item.user_id === user.user_id);
      if (updated) setSelectedUser((prev) => (prev ? { ...updated } : prev));
      setMutationMessage({
        type: "success",
        text: "Thay đổi đã được lưu và ghi vào audit.",
      });
      closeConfirm();
    } catch {
      setMutationMessage({
        type: "error",
        text: "Không thể thực hiện thay đổi. Vui lòng thử lại.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const renderRoleMenu = (user: AdminUser) => {
    if (isSelf(user)) {
      return (
        <button
          type="button"
          className="admin-users-action admin-users-action--disabled"
          disabled
          title="Không thể tự thay đổi quyền của chính mình"
        >
          <Lock size={14} />
          Tự bảo vệ
        </button>
      );
    }
    return (
      <>
        {(["admin", "manager", "resident"] as UserRole[]).map((role) =>
          role !== user.role ? (
            <button
              key={role}
              type="button"
              onClick={() => confirmAction({ kind: "role", user, value: role })}
            >
              <UserCog size={14} />
              Đổi vai trò thành {roleLabel[role]}
            </button>
          ) : null,
        )}
        {user.status === "disabled" ? (
          <button
            type="button"
            onClick={() =>
              confirmAction({ kind: "status", user, value: "active" })
            }
          >
            <UserCheck size={14} />
            Kích hoạt tài khoản
          </button>
        ) : (
          <button
            type="button"
            className="admin-users-action--danger"
            onClick={() =>
              confirmAction({ kind: "status", user, value: "disabled" })
            }
          >
            <Ban size={14} />
            Vô hiệu hóa tài khoản
          </button>
        )}
      </>
    );
  };

  const renderTable = () => (
    <div className="admin-users-table-wrap">
      <table className="admin-users-table">
        <thead>
          <tr>
            <th>Người dùng</th>
            <th>Vai trò</th>
            <th>Nhóm người dùng</th>
            <th>Tổ chức / Khu vực</th>
            <th>Trạng thái</th>
            <th>Hoạt động gần nhất</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          {filteredUsers.map((user) => (
            <tr
              key={user.user_id}
              onClick={() => openUser(user)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") openUser(user);
              }}
            >
              <td>
                <div className="admin-user-cell">
                  <span className={`admin-avatar admin-avatar--${user.role}`}>
                    {getInitials(user)}
                  </span>
                  <div>
                    <strong>{user.full_name}</strong>
                    <small>{user.email}</small>
                  </div>
                </div>
              </td>
              <td>
                <span
                  className={`admin-role-badge admin-role-badge--${user.role}`}
                >
                  {roleLabel[user.role]}
                </span>
              </td>
              <td>
                <code className="admin-group-code">
                  {groupLabel[user.user_group]}
                </code>
              </td>
              <td>
                <div className="admin-org-cell">
                  <strong>{user.organization}</strong>
                  <small>{user.region}</small>
                </div>
              </td>
              <td>
                <span
                  className={`admin-user-status admin-user-status--${user.status}`}
                >
                  {renderStatusIcon(user.status)}
                  {statusLabel[user.status]}
                </span>
              </td>
              <td>{formatDate(user.last_active_at)}</td>
              <td onClick={(event) => event.stopPropagation()}>
                <div className="admin-users-menu-wrap">
                  <button
                    type="button"
                    className="admin-icon-button"
                    aria-label={`Menu hành động cho ${user.full_name}`}
                    onClick={() =>
                      setMenuFor(menuFor === user.user_id ? null : user.user_id)
                    }
                  >
                    <MoreVertical size={17} />
                  </button>
                  {menuFor === user.user_id && (
                    <div
                      className="admin-users-menu"
                      onClick={() => setMenuFor(null)}
                    >
                      <button type="button" onClick={() => openUser(user)}>
                        <ClipboardList size={14} />
                        Xem chi tiết
                      </button>
                      {renderRoleMenu(user)}
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderMobileCards = () => (
    <div className="admin-users-cards">
      {filteredUsers.map((user) => (
        <article key={user.user_id} className="admin-user-card">
          <header>
            <span className={`admin-avatar admin-avatar--${user.role}`}>
              {getInitials(user)}
            </span>
            <div>
              <strong>{user.full_name}</strong>
              <small>{user.email}</small>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label={`Hành động cho ${user.full_name}`}
              onClick={() =>
                setMenuFor(menuFor === user.user_id ? null : user.user_id)
              }
            >
              <MoreVertical size={18} />
            </button>
          </header>
          {menuFor === user.user_id && (
            <div
              className="admin-user-card__menu"
              onClick={() => setMenuFor(null)}
            >
              <button type="button" onClick={() => openUser(user)}>
                <ClipboardList size={14} />
                Xem chi tiết
              </button>
              {renderRoleMenu(user)}
            </div>
          )}
          <footer>
            <span className={`admin-role-badge admin-role-badge--${user.role}`}>
              {roleLabel[user.role]}
            </span>
            <span
              className={`admin-user-status admin-user-status--${user.status}`}
            >
              {renderStatusIcon(user.status)}
              {statusLabel[user.status]}
            </span>
          </footer>
        </article>
      ))}
    </div>
  );

  return (
    <div className="admin-dashboard admin-users-page">
      <header className="admin-dashboard__header">
        <div>
          <h1>Quản lý người dùng</h1>
          <p>
            Quản lý identity, vai trò và trạng thái tài khoản · Dữ liệu demo
            trên client, chờ API contract
          </p>
        </div>
        <button
          type="button"
          className="admin-primary-button"
          disabled
          title="Cần endpoint và policy invitation từ backend"
        >
          <UserPlus size={16} />
          Mời người dùng
        </button>
      </header>

      <div className="admin-simulator-note" role="note">
        <AlertTriangle size={15} />
        <span>
          <strong>DEMO DATA</strong> · Danh sách người dùng bên dưới là dữ liệu
          giả lập phục vụ demo MVP, không phải dữ liệu production. Không hiển
          thị password, token hay dữ liệu sức khỏe.
        </span>
      </div>

      {error && (
        <div className="admin-error" role="alert">
          <AlertTriangle size={17} />
          <span>{error}</span>
          <button type="button" onClick={loadUsers}>
            Thử lại
          </button>
        </div>
      )}

      {mutationMessage && (
        <div
          className={`admin-mutation-banner admin-mutation-banner--${mutationMessage.type}`}
          role="status"
        >
          {mutationMessage.type === "success" ? (
            <CheckCircle2 size={16} />
          ) : (
            <AlertTriangle size={16} />
          )}
          <span>{mutationMessage.text}</span>
          <button
            type="button"
            aria-label="Đóng thông báo"
            onClick={() => setMutationMessage(null)}
          >
            <X size={15} />
          </button>
        </div>
      )}

      <section className="admin-users-toolbar" aria-label="Bộ lọc người dùng">
        <label className="admin-users-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Tìm kiếm người dùng</span>
          <input
            type="search"
            placeholder="Tìm theo tên hoặc email..."
            value={filter.query}
            onChange={(event) =>
              setFilter({ ...filter, query: event.target.value })
            }
          />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc vai trò</span>
          <select
            value={filter.role}
            onChange={(event) =>
              setFilter({
                ...filter,
                role: event.target.value as UserRole | "all",
              })
            }
          >
            <option value="all">Tất cả vai trò</option>
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
            <option value="resident">Resident</option>
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc trạng thái</span>
          <select
            value={filter.status}
            onChange={(event) =>
              setFilter({
                ...filter,
                status: event.target.value as AdminUserStatus | "all",
              })
            }
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="active">Active</option>
            <option value="disabled">Disabled</option>
            <option value="invitation_pending">Invitation pending</option>
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <label className="admin-users-select">
          <span className="sr-only">Lọc khu vực</span>
          <select
            value={filter.region}
            onChange={(event) =>
              setFilter({ ...filter, region: event.target.value })
            }
          >
            <option value="all">Tất cả khu vực</option>
            {regionOptions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
          <ChevronDown size={15} aria-hidden="true" />
        </label>
        <button
          type="button"
          className="admin-users-reset"
          onClick={resetFilters}
          disabled={
            !filter.query &&
            filter.role === "all" &&
            filter.status === "all" &&
            filter.region === "all"
          }
        >
          <Filter size={14} />
          Đặt lại
        </button>
      </section>

      <section className="admin-card admin-users-panel">
        <header className="admin-card__header">
          <div>
            <Users size={17} />
            <h2>Danh sách người dùng</h2>
          </div>
          <span>
            {loading
              ? "Đang tải..."
              : `${filteredUsers.length} / ${users.length} tài khoản`}
          </span>
        </header>

        {loading ? (
          <div className="admin-panel-state">
            <RefreshCw className="is-spinning" size={20} />
            Đang tải danh sách người dùng…
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="admin-panel-state">
            <Users size={20} />
            {users.length === 0
              ? "Chưa có người dùng nào."
              : "Không có người dùng phù hợp với bộ lọc."}
            {users.length > 0 && (
              <button
                type="button"
                className="admin-users-reset"
                onClick={resetFilters}
              >
                Đặt lại bộ lọc
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="admin-users-desktop">{renderTable()}</div>
            <div className="admin-users-mobile">{renderMobileCards()}</div>
          </>
        )}
      </section>

      {selectedUser && (
        <div
          className="admin-drawer-scrim"
          role="presentation"
          onClick={closeDrawer}
        />
      )}
      {selectedUser && (
        <aside
          className="admin-user-drawer"
          aria-label={`Chi tiết người dùng ${selectedUser.full_name}`}
          role="dialog"
          aria-modal="true"
        >
          <header className="admin-user-drawer__header">
            <div className="admin-user-drawer__identity">
              <span
                className={`admin-avatar admin-avatar--${selectedUser.role}`}
              >
                {getInitials(selectedUser)}
              </span>
              <div>
                <strong>{selectedUser.full_name}</strong>
                <small>{selectedUser.email}</small>
              </div>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label="Đóng bảng chi tiết"
              onClick={closeDrawer}
            >
              <X size={20} />
            </button>
          </header>

          <nav
            className="admin-user-drawer__tabs"
            aria-label="Các mục chi tiết người dùng"
          >
            {(
              [
                ["account", "Thông tin tài khoản"],
                ["role", "Vai trò & phạm vi"],
                ["audit", "Audit hoạt động"],
              ] as Array<[DetailTab, string]>
            ).map(([tab, label]) => (
              <button
                key={tab}
                type="button"
                className={detailTab === tab ? "is-active" : ""}
                onClick={() => setDetailTab(tab)}
              >
                {label}
              </button>
            ))}
          </nav>

          <div className="admin-user-drawer__body">
            {detailTab === "account" && (
              <dl className="admin-user-info">
                <div>
                  <dt>Họ tên</dt>
                  <dd>{selectedUser.full_name}</dd>
                </div>
                <div>
                  <dt>Email</dt>
                  <dd>{selectedUser.email}</dd>
                </div>
                <div>
                  <dt>Tổ chức</dt>
                  <dd>{selectedUser.organization}</dd>
                </div>
                <div>
                  <dt>Khu vực</dt>
                  <dd>{selectedUser.region}</dd>
                </div>
                <div>
                  <dt>Ngày tạo</dt>
                  <dd>{formatDate(selectedUser.created_at)}</dd>
                </div>
                <div>
                  <dt>Hoạt động gần nhất</dt>
                  <dd>{formatDate(selectedUser.last_active_at)}</dd>
                </div>
                <div>
                  <dt>ID tài khoản</dt>
                  <dd>
                    <code>{selectedUser.user_id}</code>
                  </dd>
                </div>
                <div>
                  <dt>Vai trò</dt>
                  <dd>
                    <span
                      className={`admin-role-badge admin-role-badge--${selectedUser.role}`}
                    >
                      {roleLabel[selectedUser.role]}
                    </span>
                  </dd>
                </div>
              </dl>
            )}

            {detailTab === "role" && (
              <div className="admin-user-role-panel">
                <dl className="admin-user-info">
                  <div>
                    <dt>Nhóm người dùng</dt>
                    <dd>
                      <code className="admin-group-code">
                        {groupLabel[selectedUser.user_group]}
                      </code>
                      <small className="admin-user-role-hint">
                        Giá trị chính sách — không thu thập chẩn đoán hay bệnh
                        lý.
                      </small>
                    </dd>
                  </div>
                  <div>
                    <dt>Trạng thái tài khoản</dt>
                    <dd>
                      <span
                        className={`admin-user-status admin-user-status--${selectedUser.status}`}
                      >
                        {renderStatusIcon(selectedUser.status)}
                        {statusLabel[selectedUser.status]}
                      </span>
                    </dd>
                  </div>
                </dl>

                {isSelf(selectedUser) ? (
                  <div className="admin-user-self-protect" role="note">
                    <Lock size={15} />
                    <span>
                      Đây là tài khoản của bạn. Theo chính sách bảo vệ, bạn
                      không thể tự hạ quyền, vô hiệu hóa hoặc xóa chính tài
                      khoản của mình.
                    </span>
                  </div>
                ) : (
                  <div className="admin-user-actions">
                    <strong>Thay đổi vai trò</strong>
                    <div className="admin-user-actions__row">
                      {(["admin", "manager", "resident"] as UserRole[]).map(
                        (role) => (
                          <button
                            key={role}
                            type="button"
                            className={
                              selectedUser.role === role ? "is-active" : ""
                            }
                            disabled={selectedUser.role === role}
                            onClick={() =>
                              confirmAction({
                                kind: "role",
                                user: selectedUser,
                                value: role,
                              })
                            }
                          >
                            {roleLabel[role]}
                          </button>
                        ),
                      )}
                    </div>

                    <strong>Trạng thái tài khoản</strong>
                    <div className="admin-user-actions__row">
                      <button
                        type="button"
                        className={
                          selectedUser.status === "active" ? "is-active" : ""
                        }
                        disabled={selectedUser.status === "active"}
                        onClick={() =>
                          confirmAction({
                            kind: "status",
                            user: selectedUser,
                            value: "active",
                          })
                        }
                      >
                        <UserCheck size={14} />
                        Kích hoạt
                      </button>
                      <button
                        type="button"
                        className={`admin-user-actions__danger${selectedUser.status === "disabled" ? " is-active" : ""}`}
                        disabled={selectedUser.status === "disabled"}
                        onClick={() =>
                          confirmAction({
                            kind: "status",
                            user: selectedUser,
                            value: "disabled",
                          })
                        }
                      >
                        <Ban size={14} />
                        Vô hiệu hóa
                      </button>
                    </div>
                    <p className="admin-user-actions__note">
                      Mọi thay đổi yêu cầu xác nhận kèm lý do và đều được ghi
                      vào audit. Backend RBAC là quyết định cuối cùng.
                    </p>
                  </div>
                )}
              </div>
            )}

            {detailTab === "audit" && (
              <div className="admin-user-audit">
                {audit.length === 0 ? (
                  <div className="admin-panel-state">
                    Chưa có bản ghi audit cho người dùng này.
                  </div>
                ) : (
                  <ul>
                    {audit.map((entry) => (
                      <li key={entry.id}>
                        <time>{formatDate(entry.time)}</time>
                        <div>
                          <strong>{entry.action}</strong>
                          <span>
                            {entry.actor} · {entry.target}
                          </span>
                          {entry.detail && <p>{entry.detail}</p>}
                          <code>
                            {entry.outcome} · {entry.correlation_id}
                          </code>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                <p className="admin-user-actions__note">
                  Audit chỉ đọc: actor, action, target, outcome, correlation id
                  và thời gian.
                </p>
              </div>
            )}
          </div>
        </aside>
      )}

      {pendingAction && (
        <div
          className="admin-confirm-scrim"
          role="presentation"
          onClick={closeConfirm}
        />
      )}
      {pendingAction && (
        <div
          className="admin-confirm-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
        >
          <header>
            <span className="admin-confirm-modal__icon">
              {pendingAction.kind === "status" &&
              pendingAction.value === "disabled" ? (
                <Ban size={20} />
              ) : (
                <UserCog size={20} />
              )}
            </span>
            <div>
              <h2 id="confirm-title">
                {pendingAction.kind === "role"
                  ? "Đổi vai trò người dùng"
                  : pendingAction.value === "disabled"
                    ? "Vô hiệu hóa tài khoản"
                    : "Kích hoạt tài khoản"}
              </h2>
              <p>
                {pendingAction.user.full_name} · {pendingAction.user.email}
              </p>
            </div>
            <button
              type="button"
              className="admin-icon-button"
              aria-label="Đóng"
              onClick={closeConfirm}
            >
              <X size={18} />
            </button>
          </header>

          <div className="admin-confirm-modal__body">
            <div className="admin-confirm-impact">
              <strong>Tác động:</strong>
              {pendingAction.kind === "role" ? (
                <span>
                  Vai trò của {pendingAction.user.full_name} sẽ đổi từ{" "}
                  <b>{roleLabel[pendingAction.user.role]}</b> sang{" "}
                  <b>{roleLabel[pendingAction.value as UserRole]}</b>. Quyền
                  truy cập sẽ được backend áp dụng ở request tiếp theo.
                </span>
              ) : pendingAction.value === "disabled" ? (
                <span>
                  {pendingAction.user.full_name} sẽ không thể đăng nhập hoặc sử
                  dụng hệ thống cho đến khi được kích hoạt lại. Lịch sử và audit
                  vẫn được giữ nguyên.
                </span>
              ) : (
                <span>
                  {pendingAction.user.full_name} sẽ được phép đăng nhập và sử
                  dụng hệ thống trở lại.
                </span>
              )}
            </div>
            <label className="admin-confirm-reason">
              <span>
                Lý do thay đổi <b aria-hidden="true">*</b>
              </span>
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Bắt buộc nhập lý do để ghi vào audit..."
                rows={3}
              />
            </label>
            {mutationMessage?.type === "error" && (
              <div
                className="admin-mutation-banner admin-mutation-banner--error"
                role="alert"
              >
                <AlertTriangle size={15} />
                <span>{mutationMessage.text}</span>
              </div>
            )}
          </div>

          <footer>
            <button
              type="button"
              className="admin-confirm-cancel"
              onClick={closeConfirm}
              disabled={submitting}
            >
              Hủy
            </button>
            <button
              type="button"
              className={`admin-confirm-submit admin-confirm-submit--${pendingAction.value === "disabled" ? "danger" : "primary"}`}
              onClick={executeAction}
              disabled={submitting || !reason.trim()}
            >
              {submitting ? (
                <RefreshCw className="is-spinning" size={15} />
              ) : null}
              {submitting
                ? "Đang lưu..."
                : pendingAction.kind === "role"
                  ? "Xác nhận đổi vai trò"
                  : pendingAction.value === "disabled"
                    ? "Xác nhận vô hiệu hóa"
                    : "Xác nhận kích hoạt"}
            </button>
          </footer>
        </div>
      )}
    </div>
  );
};

import {
  AdminAuditEntry,
  AdminUser,
  AdminUserStatus,
  UserMutationResult,
  UserRole,
} from "../types";
import { apiFetch } from "./client";

const mapUser = (raw: Record<string, any>): AdminUser => {
  const role = raw.role as UserRole;
  return {
    user_id: String(raw.user_id),
    full_name: raw.full_name || raw.email || "Người dùng AirGuard",
    email: String(raw.email || ""),
    role,
    user_group: raw.user_group || raw.sensitivity_group || "normal",
    organization:
      role === "admin"
        ? "AirGuard Operations"
        : role === "manager"
          ? "Ban Quản lý Khu đô thị"
          : "Vinhomes Ocean Park 1",
    region: role === "admin" ? "Toàn hệ thống" : "Vinhomes Ocean Park 1",
    status: raw.status || (raw.is_active ? "active" : "disabled"),
    last_active_at: raw.last_active_at || null,
    created_at: raw.created_at,
    avatar_initials: "",
  };
};

const mapAudit = (raw: Record<string, any>): AdminAuditEntry => ({
  id: String(raw.audit_id),
  time: raw.created_at,
  actor: [raw.actor_id, raw.actor_role].filter(Boolean).join(" · ") || raw.actor_type,
  action: raw.action,
  target: [raw.entity_type, raw.entity_id].filter(Boolean).join(":"),
  outcome: String(raw.outcome || "unknown").toUpperCase(),
  correlation_id: raw.correlation_id || "—",
  detail: raw.details?.reason || undefined,
});

export const userManagementApi = {
  async getUsers(): Promise<AdminUser[]> {
    const data = await apiFetch<{ items: Array<Record<string, any>> }>("/api/v1/users");
    return data.items.map(mapUser);
  },

  async getUserAudit(userId: string): Promise<AdminAuditEntry[]> {
    const params = new URLSearchParams({ entity_type: "user", entity_id: userId });
    const data = await apiFetch<{ items: Array<Record<string, any>> }>(
      `/api/v1/audit-logs?${params.toString()}`,
    );
    return data.items.map(mapAudit);
  },

  async updateRole(
    userId: string,
    role: UserRole,
    reason: string,
    _actorName: string,
  ): Promise<UserMutationResult> {
    return this.update(userId, { role, reason });
  },

  async updateStatus(
    userId: string,
    status: AdminUserStatus,
    reason: string,
    _actorName: string,
  ): Promise<UserMutationResult> {
    if (status === "invitation_pending") {
      throw new Error("Invitation lifecycle is not supported by the backend.");
    }
    return this.update(userId, { status, reason });
  },

  async update(
    userId: string,
    body: { role?: UserRole; status?: "active" | "disabled"; reason: string },
  ): Promise<UserMutationResult> {
    const data = await apiFetch<{ user: Record<string, any>; audit: Record<string, any> }>(
      `/api/v1/users/${encodeURIComponent(userId)}`,
      { method: "PATCH", body: JSON.stringify(body) },
    );
    return {
      success: true,
      message: "Đã lưu thay đổi và ghi audit.",
      user: mapUser(data.user),
      audit_entry: mapAudit(data.audit),
    };
  },
};

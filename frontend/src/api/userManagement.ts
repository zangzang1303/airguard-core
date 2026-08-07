import {
  AdminAuditEntry,
  AdminUser,
  AdminUserStatus,
  UserMutationResult,
  UserRole,
} from "../types";
import { DEMO_ADMIN_USERS, DEMO_USER_AUDIT } from "./client";

const makeAuditId = () => `AUD-U${Date.now()}`;
const makeCorrelationId = () =>
  `req-u-${Math.floor(1000 + Math.random() * 9000)}`;

const findTarget = (userId: string) =>
  DEMO_ADMIN_USERS.find((user) => user.user_id === userId);

// P2 · Quản lý người dùng — demo client-side, contract đang pending.
export const userManagementApi = {
  async getUsers(): Promise<AdminUser[]> {
    return DEMO_ADMIN_USERS;
  },

  async getUserAudit(userId: string): Promise<AdminAuditEntry[]> {
    return DEMO_USER_AUDIT.filter((entry) => entry.target.includes(userId));
  },

  async updateRole(
    userId: string,
    role: UserRole,
    reason: string,
    actorName: string,
  ): Promise<UserMutationResult> {
    const target = findTarget(userId);
    const targetLabel = target ? `${userId} · ${target.full_name}` : userId;
    return {
      success: true,
      message: "Đã cập nhật vai trò (demo client-side).",
      audit_entry: {
        id: makeAuditId(),
        time: new Date().toISOString(),
        actor: `${actorName} (admin)`,
        action: "USER_UPDATE_ROLE",
        target: targetLabel,
        outcome: "SUCCESS",
        correlation_id: makeCorrelationId(),
        detail: `Cập nhật vai trò -> ${role}${reason ? ` · Lý do: ${reason}` : ""}`,
      },
    };
  },

  async updateStatus(
    userId: string,
    status: AdminUserStatus,
    reason: string,
    actorName: string,
  ): Promise<UserMutationResult> {
    const target = findTarget(userId);
    const targetLabel = target ? `${userId} · ${target.full_name}` : userId;
    return {
      success: true,
      message: "Đã cập nhật trạng thái (demo client-side).",
      audit_entry: {
        id: makeAuditId(),
        time: new Date().toISOString(),
        actor: `${actorName} (admin)`,
        action: status === "disabled" ? "USER_DISABLE" : "USER_ACTIVATE",
        target: targetLabel,
        outcome: "SUCCESS",
        correlation_id: makeCorrelationId(),
        detail: `Cập nhật trạng thái -> ${status}${reason ? ` · Lý do: ${reason}` : ""}`,
      },
    };
  },
};

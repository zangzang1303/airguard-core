import React from "react";
import { Building2, Cpu, Settings, UserCog } from "lucide-react";

type AdminModule = "users" | "regions" | "devices" | "settings";

const moduleCopy: Record<AdminModule, { title: string; description: string; icon: React.ElementType }> = {
  users: { title: "Quản lý người dùng", description: "Quản lý tài khoản và phân quyền hệ thống.", icon: UserCog },
  regions: { title: "Khu vực & Trạm", description: "Danh mục khu vực và trạm quan trắc S01-S05.", icon: Building2 },
  devices: { title: "Thiết bị IoT", description: "Theo dõi tình trạng kết nối và cấu hình cảm biến.", icon: Cpu },
  settings: { title: "Cài đặt", description: "Cấu hình vận hành dành cho quản trị viên.", icon: Settings },
};

export const AdminModulePlaceholder: React.FC<{ module: AdminModule }> = ({ module }) => {
  const item = moduleCopy[module];
  const Icon = item.icon;
  return (
    <div className="admin-dashboard admin-module-page">
      <header className="admin-dashboard__header"><div><h1>{item.title}</h1><p>{item.description}</p></div></header>
      <section className="admin-card admin-module-placeholder">
        <span><Icon size={28} /></span>
        <h2>Chưa cấu hình trong MVP</h2>
        <p>Thiết kế navigation đã được triển khai, nhưng module này đang chờ API contract và RBAC server-side. Không có dữ liệu hoặc hành động quản trị giả được tạo ở client.</p>
        <small>P2 · Contract pending</small>
      </section>
    </div>
  );
};


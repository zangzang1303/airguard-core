import React, { useEffect, useRef, useState } from "react";
import {
  Bell,
  Building2,
  CheckCircle2,
  ChevronDown,
  CircleUserRound,
  Cpu,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  ShieldCheck,
  Sun,
  UserCog,
  X,
} from "lucide-react";
import { ScreenType, useAuth } from "../../context/AuthContext";
import "./AdminShell.css";

interface AdminShellProps {
  children: React.ReactNode;
}

const adminNavigation: Array<{ screen: ScreenType; label: string; icon: React.ElementType; badge?: boolean }> = [
  { screen: "dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { screen: "admin-users", label: "Quản lý người dùng", icon: UserCog },
  { screen: "admin-regions", label: "Khu vực & Trạm", icon: Building2 },
  { screen: "admin-devices", label: "Thiết bị IoT", icon: Cpu },
  { screen: "approvals", label: "Phê duyệt HITL", icon: CheckCircle2, badge: true },
  { screen: "admin-settings", label: "Cài đặt", icon: Settings },
];

export const AdminShell: React.FC<AdminShellProps> = ({ children }) => {
  const { currentScreen, navigateTo, pendingApprovalsCount, userName, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [lightMode, setLightMode] = useState(false);
  const contentRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setSidebarOpen(false);
    contentRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [currentScreen]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  return (
    <div className={`admin-shell${lightMode ? " admin-shell--light" : ""}`}>
      <button
        className={`admin-shell__scrim${sidebarOpen ? " is-visible" : ""}`}
        type="button"
        aria-label="Đóng menu quản trị"
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`admin-sidebar${sidebarOpen ? " is-open" : ""}`} aria-label="Điều hướng quản trị">
        <div className="admin-brand">
          <button type="button" className="admin-brand__button" onClick={() => navigateTo("dashboard")}>
            <span className="admin-brand__mark"><ShieldCheck size={23} /></span>
            <span><strong>AIRGUARD AI</strong><small>Quản trị hệ thống</small></span>
          </button>
          <button type="button" className="admin-mobile-close" aria-label="Đóng menu" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <div className="admin-role-card">
          <span className="admin-role-card__dot" />
          <strong>Admin</strong>
          <small>Toàn quyền</small>
        </div>

        <nav className="admin-nav">
          {adminNavigation.map((item) => {
            const Icon = item.icon;
            const active = currentScreen === item.screen;
            return (
              <button
                key={item.screen}
                type="button"
                className={`admin-nav__item${active ? " is-active" : ""}`}
                aria-current={active ? "page" : undefined}
                onClick={() => navigateTo(item.screen)}
              >
                <Icon size={19} aria-hidden="true" />
                <span>{item.label}</span>
                {item.badge && pendingApprovalsCount > 0 && (
                  <b aria-label={`${pendingApprovalsCount} đề xuất đang chờ`}>{pendingApprovalsCount}</b>
                )}
              </button>
            );
          })}
        </nav>

        <div className="admin-sidebar__footer">
          <button type="button" className="admin-switch-role" onClick={logout}>
            <LogOut size={18} />
            <span>Chuyển vai trò</span>
          </button>
        </div>
      </aside>

      <section className="admin-workspace">
        <header className="admin-topbar">
          <button type="button" className="admin-icon-button admin-menu-button" aria-label="Mở menu quản trị" onClick={() => setSidebarOpen(true)}>
            <Menu size={21} />
          </button>

          <label className="admin-search">
            <Search size={18} aria-hidden="true" />
            <span className="sr-only">Tìm kiếm trong khu vực quản trị</span>
            <input type="search" placeholder="Tìm trạm, người dùng..." />
          </label>

          <label className="admin-area-select">
            <span className="sr-only">Chọn khu vực</span>
            <select defaultValue="all">
              <option value="all">Tất cả khu vực</option>
              <option value="vinuni">VinUni Campus</option>
              <option value="ocean-park">Vinhomes Ocean Park</option>
            </select>
            <ChevronDown size={16} aria-hidden="true" />
          </label>

          <div className="admin-online-pill"><span />Trực tuyến</div>
          <button type="button" className="admin-icon-button" aria-label={lightMode ? "Chuyển sang giao diện tối" : "Chuyển sang giao diện sáng"} onClick={() => setLightMode((value) => !value)}>
            {lightMode ? <Moon size={19} /> : <Sun size={19} />}
          </button>
          <button type="button" className="admin-icon-button admin-notification" aria-label="Mở đề xuất HITL" onClick={() => navigateTo("approvals")}>
            <Bell size={19} />
            {pendingApprovalsCount > 0 && <span />}
          </button>
          <div className="admin-profile">
            <span className="admin-profile__copy"><strong>{userName || "Quản trị viên"}</strong><small>Admin</small></span>
            <span className="admin-profile__avatar" aria-hidden="true"><CircleUserRound size={20} /></span>
          </div>
        </header>

        <main ref={contentRef} className="admin-content" id="main-content">
          {children}
          <footer className="admin-footer">AirGuard AI · Dữ liệu Simulator cho MVP · Không phải quan trắc chính thức</footer>
        </main>
      </section>
    </div>
  );
};


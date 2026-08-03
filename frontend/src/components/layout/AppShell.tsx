import React, { useEffect, useMemo, useState } from "react";
import {
  Bell,
  Bot,
  CheckSquare2,
  ChevronRight,
  CircleUserRound,
  FileClock,
  GitCompareArrows,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  ShieldCheck,
  Siren,
  UserRound,
  X,
  type LucideIcon,
} from "lucide-react";
import { ScreenType, useAuth } from "../../context/AuthContext";
import { UserRole } from "../../types";
import { SimulatorBanner } from "../common/SimulatorBanner";
import "./AppShell.css";

interface AppShellProps {
  children: React.ReactNode;
}

interface NavigationItem {
  screen: ScreenType;
  label: string;
  icon: LucideIcon;
  managerOnly?: boolean;
  badge?: number;
}

const screenMetadata: Record<ScreenType, { label: string; eyebrow: string; description: string }> = {
  dashboard: {
    label: "Dashboard",
    eyebrow: "Tổng quan",
    description: "Theo dõi chất lượng không khí tại 5 trạm quanh VinUni và Ocean Park.",
  },
  "station-detail": {
    label: "Chi tiết trạm",
    eyebrow: "Quan trắc",
    description: "Giá trị hiện tại, lịch sử, độ mới dữ liệu và dự báo ngắn hạn.",
  },
  compare: {
    label: "So sánh khu vực",
    eyebrow: "Phân tích",
    description: "Đối chiếu PM2.5 giữa hai trạm trong cùng khoảng thời gian.",
  },
  agent: {
    label: "AI Agent",
    eyebrow: "Trợ lý dữ liệu",
    description: "Hỏi đáp dựa trên dữ liệu backend và tạo đề xuất có Human-in-the-Loop.",
  },
  alerts: {
    label: "Cảnh báo",
    eyebrow: "Giám sát",
    description: "Theo dõi cảnh báo đang hoạt động và lịch sử trạng thái tại các trạm.",
  },
  approvals: {
    label: "Phê duyệt",
    eyebrow: "Human-in-the-Loop",
    description: "Xem xét bằng chứng trước khi phê duyệt hoặc từ chối đề xuất cảnh báo.",
  },
  audit: {
    label: "Audit Log",
    eyebrow: "Quản trị",
    description: "Truy vết các hành động quan trọng và kết quả xử lý trong hệ thống.",
  },
  profile: {
    label: "Hồ sơ người dùng",
    eyebrow: "Tài khoản",
    description: "Quản lý thông tin hiển thị và nhóm người dùng nhận khuyến nghị.",
  },
  login: {
    label: "Đăng nhập",
    eyebrow: "Tài khoản",
    description: "Đăng nhập vào AirGuard AI.",
  },
};

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentScreen, navigateTo, role, setRole, userName, pendingApprovalsCount } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const meta = screenMetadata[currentScreen];
  const isManagerOrAdmin = role === "manager" || role === "admin";

  const navigationItems = useMemo<NavigationItem[]>(
    () => [
      { screen: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      { screen: "compare", label: "So sánh khu vực", icon: GitCompareArrows },
      { screen: "agent", label: "AI Agent", icon: Bot },
      { screen: "alerts", label: "Cảnh báo", icon: Siren },
      {
        screen: "approvals",
        label: "Phê duyệt",
        icon: CheckSquare2,
        managerOnly: true,
        badge: pendingApprovalsCount,
      },
      { screen: "audit", label: "Audit Log", icon: FileClock, managerOnly: true },
      { screen: "profile", label: "Hồ sơ", icon: UserRound },
    ],
    [pendingApprovalsCount],
  );

  const visibleNavigationItems = navigationItems.filter(
    (item) => !item.managerOnly || isManagerOrAdmin,
  );

  useEffect(() => setSidebarOpen(false), [currentScreen]);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

  const handleNavigate = (screen: ScreenType) => {
    navigateTo(screen);
    setSidebarOpen(false);
  };

  const displayName = userName.split("(")[0].trim() || "Nguyễn Văn A";
  const roleLabel = role === "resident" ? "Cư dân" : role === "manager" ? "Manager" : "Admin";

  return (
    <div className="app-shell">
      <button
        type="button"
        className={`app-shell__scrim ${sidebarOpen ? "is-visible" : ""}`}
        aria-label="Đóng menu điều hướng"
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`app-sidebar ${sidebarOpen ? "is-open" : ""}`} aria-label="Điều hướng chính">
        <div className="app-sidebar__brand">
          <button type="button" className="brand-lockup" onClick={() => handleNavigate("dashboard")}>
            <span className="brand-lockup__mark" aria-hidden="true">
              <ShieldCheck size={23} strokeWidth={2.2} />
            </span>
            <span>
              <strong>AirGuard AI</strong>
              <small>PM2.5 Monitoring</small>
            </span>
          </button>
          <button
            type="button"
            className="app-sidebar__close"
            aria-label="Đóng menu"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <div className="app-sidebar__section-label">Không gian làm việc</div>
        <nav className="app-sidebar__nav">
          {visibleNavigationItems.map((item) => {
            const Icon = item.icon;
            const active = currentScreen === item.screen ||
              (item.screen === "dashboard" && currentScreen === "station-detail");
            return (
              <button
                type="button"
                key={item.screen}
                className={`sidebar-nav-item ${active ? "is-active" : ""}`}
                aria-current={active ? "page" : undefined}
                onClick={() => handleNavigate(item.screen)}
              >
                <Icon size={19} strokeWidth={1.9} aria-hidden="true" />
                <span>{item.label}</span>
                {!!item.badge && item.badge > 0 && (
                  <span className="sidebar-nav-item__badge" aria-label={`${item.badge} đề xuất đang chờ`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="app-sidebar__footer">
          <div className="system-card">
            <span className="system-card__status" aria-hidden="true" />
            <div>
              <strong>Kết nối dữ liệu</strong>
              <span>Hệ thống đang hoạt động</span>
            </div>
          </div>
          <button type="button" className="sidebar-logout" disabled title="Chưa cấu hình trong MVP">
            <LogOut size={18} aria-hidden="true" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      <section className="app-shell__workspace">
        <header className="app-topbar">
          <div className="app-topbar__left">
            <button
              type="button"
              className="topbar-icon-button app-topbar__menu"
              aria-label="Mở menu điều hướng"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={21} />
            </button>
            <div className="app-breadcrumb" aria-label="Breadcrumb">
              <button type="button" onClick={() => handleNavigate("dashboard")}>AirGuard AI</button>
              <ChevronRight size={15} aria-hidden="true" />
              <span>{meta.label}</span>
            </div>
          </div>

          <div className="app-topbar__actions">
            <label className="topbar-search">
              <Search size={18} aria-hidden="true" />
              <span className="sr-only">Tìm kiếm</span>
              <input type="search" placeholder="Tìm trạm, cảnh báo..." />
              <kbd>⌘ K</kbd>
            </label>
            <button
              type="button"
              className="topbar-icon-button topbar-notification"
              aria-label="Mở thông báo"
              onClick={() => handleNavigate(isManagerOrAdmin ? "approvals" : "alerts")}
            >
              <Bell size={20} />
              {pendingApprovalsCount > 0 && isManagerOrAdmin && <span>{pendingApprovalsCount}</span>}
            </button>
            <div className="topbar-role">
              <span>Vai trò</span>
              <select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
                <option value="resident">Cư dân</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button type="button" className="topbar-profile" onClick={() => handleNavigate("profile")}>
              <span className="topbar-profile__avatar" aria-hidden="true">
                <CircleUserRound size={22} />
              </span>
              <span className="topbar-profile__copy">
                <strong>{displayName}</strong>
                <small>{roleLabel}</small>
              </span>
            </button>
          </div>
        </header>

        <SimulatorBanner />

        <main className="app-shell__content" id="main-content">
          <div className="page-heading">
            <div>
              <span className="page-heading__eyebrow">{meta.eyebrow}</span>
              <h1>{meta.label}</h1>
              <p>{meta.description}</p>
            </div>
          </div>
          <div className="page-content">{children}</div>
          <footer className="app-footer">
            AirGuard AI © 2026 · Dữ liệu mô phỏng cho mục đích học tập và trình diễn MVP
          </footer>
        </main>
      </section>
    </div>
  );
};

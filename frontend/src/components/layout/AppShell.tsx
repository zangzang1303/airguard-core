import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Bell,
  Bot,
  CheckSquare2,
  ChevronRight,
  CircleUserRound,
  FileClock,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  Siren,
  UserRound,
  X,
  type LucideIcon,
} from "lucide-react";
import { ScreenType, useAuth } from "../../context/AuthContext";
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

const DRAWER_QUERY = "(max-width: 900px)";

const screenMetadata: Record<ScreenType, { label: string }> = {
  dashboard: {
    label: "Dashboard",
  },
  "admin-users": { label: "Quản lý người dùng" },
  "admin-regions": { label: "Khu vực & Trạm" },
  "admin-devices": { label: "Thiết bị IoT" },
  "admin-settings": { label: "Cài đặt" },
  "station-detail": {
    label: "Chi tiết trạm",
  },
  agent: {
    label: "AI Agent",
  },
  alerts: {
    label: "Cảnh báo",
  },
  approvals: {
    label: "Phê duyệt",
  },
  audit: {
    label: "Audit Log",
  },
  profile: {
    label: "Hồ sơ người dùng",
  },
  login: {
    label: "Đăng nhập",
  },
  register: {
    label: "Đăng ký",
  },
  "verify-email": {
    label: "Xác minh Email",
  },
  "forgot-password": {
    label: "Quên mật khẩu",
  },
  "reset-password": {
    label: "Đặt lại mật khẩu",
  },
  "admin-coming-soon": {
    label: "Quản trị viên (Sắp ra mắt)",
  },
};

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentScreen, navigateTo, role, userName, pendingApprovalsCount, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDrawerMode, setIsDrawerMode] = useState(() => window.matchMedia(DRAWER_QUERY).matches);
  const contentRef = useRef<HTMLElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const meta = screenMetadata[currentScreen];
  const isManagerOrAdmin = role === "manager" || role === "admin";

  // Drawer chỉ tồn tại dưới 900px; trên desktop sidebar luôn hiển thị và luôn phải thao tác được.
  const drawerHidden = isDrawerMode && !sidebarOpen;
  const drawerTrapping = isDrawerMode && sidebarOpen;

  useEffect(() => {
    const query = window.matchMedia(DRAWER_QUERY);
    const syncDrawerMode = (event: MediaQueryListEvent) => setIsDrawerMode(event.matches);
    query.addEventListener("change", syncDrawerMode);
    return () => query.removeEventListener("change", syncDrawerMode);
  }, []);

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [currentScreen]);

  const navigationItems = useMemo<NavigationItem[]>(
    () => [
      { screen: "dashboard", label: "Dashboard", icon: LayoutDashboard },
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

  // Đưa focus vào drawer khi mở và trả về nút hamburger khi đóng (chỉ ở chế độ drawer).
  useEffect(() => {
    if (!isDrawerMode) return;
    if (sidebarOpen) closeButtonRef.current?.focus();
    else if (document.activeElement === document.body) menuButtonRef.current?.focus();
  }, [isDrawerMode, sidebarOpen]);

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

      <aside
        className={`app-sidebar ${sidebarOpen ? "is-open" : ""}`}
        aria-label="Điều hướng chính"
        aria-hidden={drawerHidden || undefined}
        inert={drawerHidden ? "" : undefined}
      >
        <div className="app-sidebar__brand">
          <button type="button" className="brand-lockup" onClick={() => handleNavigate("dashboard")}>
            <span className="brand-lockup__mark" aria-hidden="true">
              <ShieldCheck size={23} strokeWidth={2.2} />
            </span>
            <span>
              <strong>AirGuard AI</strong>
              <small>AQI &amp; môi trường</small>
            </span>
          </button>
          <button
            type="button"
            ref={closeButtonRef}
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
          <button type="button" className="sidebar-logout" onClick={logout}>
            <LogOut size={18} aria-hidden="true" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      <section className="app-shell__workspace" inert={drawerTrapping ? "" : undefined}>
        <header className="app-topbar">
          <div className="app-topbar__left">
            <button
              type="button"
              ref={menuButtonRef}
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
            <button
              type="button"
              className="topbar-icon-button topbar-notification"
              aria-label="Mở thông báo"
              onClick={() => handleNavigate(isManagerOrAdmin ? "approvals" : "alerts")}
            >
              <Bell size={20} />
              {pendingApprovalsCount > 0 && isManagerOrAdmin && <span>{pendingApprovalsCount}</span>}
            </button>
            <div className={`topbar-role-badge topbar-role-badge--${role}`} aria-label={`Vai trò: ${roleLabel}`}>
              <ShieldCheck size={15} aria-hidden="true" />
              {roleLabel}
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

        <main ref={contentRef} className="app-shell__content" id="main-content">
          <div className="page-content">{children}</div>
          <footer className="app-footer">
            AirGuard AI © 2026 · Dữ liệu mô phỏng cho mục đích học tập và trình diễn MVP
          </footer>
        </main>
      </section>
    </div>
  );
};

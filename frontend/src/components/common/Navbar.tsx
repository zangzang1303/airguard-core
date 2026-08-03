import React from "react";
import { useAuth } from "../../context/AuthContext";
import { UserRole } from "../../types";

export const Navbar: React.FC = () => {
  const { currentScreen, navigateTo, role, setRole, pendingApprovalsCount } = useAuth();

  const isManagerOrAdmin = role === "manager" || role === "admin";

  return (
    <header className="navbar-header">
      <div className="navbar-brand" onClick={() => navigateTo("dashboard")}>
        <div className="brand-icon">🛡️</div>
        <div>
          <h1 className="brand-title">AirGuard AI</h1>
          <span className="brand-subtitle">PM2.5 Campus Monitoring & HITL System</span>
        </div>
      </div>

      <nav className="navbar-nav">
        <button
          className={`nav-link ${currentScreen === "dashboard" || currentScreen === "station-detail" ? "active" : ""}`}
          onClick={() => navigateTo("dashboard")}
        >
          📍 Bản đồ & Trạm
        </button>
        <button
          className={`nav-link ${currentScreen === "compare" ? "active" : ""}`}
          onClick={() => navigateTo("compare")}
        >
          ⚖️ So sánh
        </button>
        <button
          className={`nav-link ${currentScreen === "agent" ? "active" : ""}`}
          onClick={() => navigateTo("agent")}
        >
          🤖 Trợ lý AI
        </button>
        <button
          className={`nav-link ${currentScreen === "alerts" ? "active" : ""}`}
          onClick={() => navigateTo("alerts")}
        >
          🔔 Cảnh báo
        </button>

        {isManagerOrAdmin && (
          <>
            <button
              className={`nav-link ${currentScreen === "approvals" ? "active" : ""}`}
              onClick={() => navigateTo("approvals")}
            >
              ✅ Phê duyệt (HITL)
              {pendingApprovalsCount > 0 && (
                <span className="nav-badge">{pendingApprovalsCount}</span>
              )}
            </button>
            <button
              className={`nav-link ${currentScreen === "audit" ? "active" : ""}`}
              onClick={() => navigateTo("audit")}
            >
              📜 Audit Log
            </button>
          </>
        )}

        <button
          className={`nav-link ${currentScreen === "profile" ? "active" : ""}`}
          onClick={() => navigateTo("profile")}
        >
          👤 Hồ sơ
        </button>
      </nav>

      <div className="navbar-role-switcher">
        <span className="role-label">Vai trò Demo:</span>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as UserRole)}
          className="role-select"
        >
          <option value="resident">Resident (Cư dân)</option>
          <option value="manager">Manager (Quản lý)</option>
          <option value="admin">Admin (Hệ thống)</option>
        </select>
      </div>
    </header>
  );
};

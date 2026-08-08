import React from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./features/stations/Dashboard";
import { StationDetail } from "./features/stations/StationDetail";
import { CompareStations } from "./features/stations/CompareStations";
import { AgentChat } from "./features/agent/AgentChat";
import { AlertList } from "./features/alerts/AlertList";
import { ApprovalQueue } from "./features/approvals/ApprovalQueue";
import { AuditLog } from "./features/audit/AuditLog";
import { Profile } from "./features/profile/Profile";
import { Login } from "./features/auth/Login";
import { Register } from "./features/auth/Register";
import "./theme.css";
import "./styles.css";

const MainContent: React.FC = () => {
  const { currentScreen, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    if (currentScreen === "register") return <Register />;
    return <Login />;
  }

  return (
    <AppShell>
      {currentScreen === "dashboard" && <Dashboard />}
      {currentScreen === "station-detail" && <StationDetail />}
      {currentScreen === "compare" && <CompareStations />}
      {currentScreen === "agent" && <AgentChat />}
      {currentScreen === "alerts" && <AlertList />}
      {currentScreen === "approvals" && <ApprovalQueue />}
      {currentScreen === "audit" && <AuditLog />}
      {currentScreen === "profile" && <Profile />}
    </AppShell>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
}

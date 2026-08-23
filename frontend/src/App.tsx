import React, { useState, useEffect, useCallback, useMemo } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Login } from "./features/auth/Login";
import { Register } from "./features/auth/Register";
import { VerifyEmail } from "./features/auth/VerifyEmail";
import { ForgotPassword } from "./features/auth/ForgotPassword";
import { ResetPassword } from "./features/auth/ResetPassword";
import { AdminComingSoon } from "./features/auth/AdminComingSoon";
import { StationDetail } from "./features/stations/StationDetail";
import { AlertList } from "./features/alerts/AlertList";
import { ApprovalQueue } from "./features/approvals/ApprovalQueue";
import { AuditLog } from "./features/audit/AuditLog";
import { Profile } from "./features/profile/Profile";
import { UserManagement } from "./features/admin/UserManagement";
import { RegionStations } from "./features/admin/RegionStations";
import { IotDevices } from "./features/admin/IotDevices";
import { AdminDashboard } from "./features/admin/AdminDashboard";
import { ReportViewer } from "./features/admin/ReportViewer";

import { SuperMap } from "./features/map/SuperMap";
import { mapActionController } from "./features/map/MapActionController";
import { useAiOverlayActive } from "./features/map/useAiOverlayActive";
import { TopFloatingBar } from "./features/navigation/TopFloatingBar";
import { BottomActionDock } from "./features/navigation/BottomActionDock";
import { ManagerStationStatusBar } from "./features/navigation/ManagerStationStatusBar";
import { MapLayersPopover } from "./features/navigation/MapLayersPopover";
import { StationPoiDrawer } from "./features/drawers/StationPoiDrawer";
import { StationForecastDrawer } from "./features/drawers/StationForecastDrawer";
import { AnalysisWorkspaceDrawer } from "./features/drawers/AnalysisWorkspaceDrawer";
import { AiAssistantDrawer } from "./features/drawers/AiAssistantDrawer";
import { NearMePanel } from "./features/drawers/NearMePanel";
import { TodaySummarySheet } from "./features/drawers/TodaySummarySheet";
import { AlertsFlyout } from "./features/drawers/AlertsFlyout";
import { HealthProfileDrawer } from "./features/drawers/HealthProfileDrawer";
import { CommunityReportModal } from "./features/drawers/CommunityReportModal";
import { ManagerApprovalDrawer } from "./features/drawers/ManagerApprovalDrawer";
import { Station, Alert, Proposal } from "./types";
import {
  ActiveDrawerType,
  MapLayerConfig,
  PlacePOI,
  HealthProfile,
  CommunityReport,
} from "./types/superApp";
import { USER_DEFAULT_LOCATION } from "./features/map/poiData";
import {
  fetchStations,
  fetchAlerts,
  fetchProposals,
  approveProposal,
  rejectProposal,
  FALLBACK_STATIONS,
  FALLBACK_ALERTS,
} from "./api/client";
import { RefreshCw, TriangleAlert, ArrowLeft } from "lucide-react";
import "./theme.css";
import "./styles.css";

const SuperAppMain: React.FC<{
  stations: Station[];
  alerts: Alert[];
  proposals: Proposal[];
  loading: boolean;
  loadError: string | null;
  proposalLoadError: string | null;
  refreshData: () => Promise<void>;
  connectionStatus: "connected" | "updating" | "disconnected";
  lastUpdated: Date | null;
}> = ({
  stations,
  alerts,
  proposals,
  loading,
  loadError,
  proposalLoadError,
  refreshData,
  connectionStatus,
  lastUpdated,
}) => {
  const { role, userGroup } = useAuth();
  const isManager = role === "manager" || role === "admin";

  // Active Overlay & Drawer States
  const [activeDrawer, setActiveDrawer] = useState<ActiveDrawerType>(null);
  const [aiInitialPrompt, setAiInitialPrompt] = useState<string | undefined>();
  const [isLayersOpen, setIsLayersOpen] = useState(false);
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const [selectedPoi, setSelectedPoi] = useState<PlacePOI | null>(null);

  // Map controls
  const [flyToTarget, setFlyToTarget] = useState<[number, number] | null>(null);

  // Layer Configuration State
  const [layerConfig, setLayerConfig] = useState<MapLayerConfig>({
    activeEnvironmentalLayer: "aqi",
    viewMode: "heatmap",
    showBoundary: true,
    showPlaces: true,
    showSensors: true,
    showHeatmap: true,
    showWindVectors: true,
    showCommunityReports: true,
  });

  // User Health Profile State
  const [healthProfile, setHealthProfile] = useState<HealthProfile>({
    sensitivityGroup: "normal",
    fullName: "Cư dân Ocean Park 1",
    interests: ["running", "walking"],
    alertPushEnabled: true,
    dailyDigestEnabled: true,
  });

  // Handlers for User Interactions
  const handleSelectStation = (stId: string) => {
    setSelectedStationId(stId);
    setSelectedPoi(null);
    setActiveDrawer("station-poi");
    const st = stations.find((s) => s.station_id === stId);
    if (st) {
      setFlyToTarget([st.latitude, st.longitude]);
    }
  };

  const handleSelectPoi = (poi: PlacePOI) => {
    setSelectedPoi(poi);
    setSelectedStationId(poi.sensorIdRef || null);
    setActiveDrawer("station-poi");
    setFlyToTarget([poi.latitude, poi.longitude]);
  };

  const handleFlyTo = (coords: [number, number], _title?: string) => {
    setFlyToTarget(coords);
  };

  const handleShowAlertOnMap = (stId: string) => {
    setActiveDrawer("station-poi");
    handleSelectStation(stId);
  };

  const handleAskAiAboutStation = (placeName: string, _aqi: number | null) => {
    setAiInitialPrompt(`Phân tích dữ liệu mới nhất và bằng chứng hiện có của ${placeName}.`);
    setActiveDrawer("ai-chat");
  };

  const handleAskAiWithQuery = (query: string) => {
    setAiInitialPrompt(query);
    setActiveDrawer("ai-chat");
  };

  const handleOpenAiChat = () => {
    setAiInitialPrompt(undefined);
    setActiveDrawer("ai-chat");
  };

  const handleCloseAiDrawer = useCallback(() => {
    mapActionController.clearAIOverlay();
    setActiveDrawer(null);
  }, []);

  const handleApproveProposal = async (proposalId: string, version: number) => {
    await approveProposal(proposalId, version);
    await refreshData();
  };

  const handleRejectProposal = async (proposalId: string, version: number, note: string) => {
    await rejectProposal(proposalId, version, note);
    await refreshData();
  };

  // AI Overlay state lifted to App level
  const hasAIOverlay = useAiOverlayActive();
  const handleClearAIOverlay = useCallback(() => {
    mapActionController.clearAIOverlay();
  }, []);

  const handleCommunityReportSubmit = (report: Partial<CommunityReport>) => {
    console.log("Community Report Submitted:", report);
  };

  const activeStation = stations.find((s) => s.station_id === selectedStationId) || null;
  const criticalStationIds = useMemo(
    () => new Set(
      alerts
        .filter((alert) => alert.status === "active" && alert.severity === "critical")
        .map((alert) => alert.station_id),
    ),
    [alerts],
  );
  const activeAlertCount = useMemo(
    () => alerts.filter((alert) => alert.status === "active").length,
    [alerts],
  );

  // Hooks must run before every conditional return so the order stays stable
  // while the initial station request moves through loading/error/success.
  const [forecastHour, setForecastHour] = useState<number>(0);

  // Cold Start Loading Skeleton
  if (loading && stations.length === 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", width: "100vw", height: "100dvh", background: "#f8fafc" }}>
        <RefreshCw size={36} className="spin-icon" style={{ color: "#4f46e5", marginBottom: "16px" }} />
        <h3 style={{ fontSize: "1.1rem", color: "#1e293b" }}>Đang khởi tạo bản đồ AirGuard AI (Ocean Park 1)…</h3>
        <p style={{ color: "#64748b", fontSize: "0.85rem", marginTop: "8px" }}>Vui lòng chờ trong giây lát khi hệ thống đồng bộ dữ liệu trạm.</p>
      </div>
    );
  }

  if (!loading && stations.length === 0) {
    return (
      <div className="map-data-state" role={loadError ? "alert" : "status"}>
        <TriangleAlert size={34} aria-hidden="true" />
        <h2>{loadError ? "Không thể tải dữ liệu bản đồ" : "Chưa có trạm quan trắc"}</h2>
        <p>{loadError ?? "Backend chưa trả về trạm nào. Hãy thử làm mới sau khi simulator đồng bộ dữ liệu."}</p>
        <button type="button" onClick={refreshData} disabled={loading}>
          <RefreshCw size={16} aria-hidden="true" /> Thử lại
        </button>
        <small>Dữ liệu giả lập cho MVP — không phải quan trắc chính thức.</small>
      </div>
    );
  }

  return (
    <div
      className={`map-super-app-root${isManager ? " is-manager" : ""}`}
      style={{ width: "100vw", height: "100dvh", position: "relative", overflow: "hidden", margin: 0, padding: 0 }}
    >
      {/* 1. LEAFLET MAP (100% Viewport Height & Width) */}
      <SuperMap
        stations={stations}
        selectedStationId={selectedStationId}
        criticalStationIds={criticalStationIds}
        selectedPoi={selectedPoi}
        layerConfig={layerConfig}
        flyToTarget={flyToTarget}
        forecastHour={forecastHour}
        onForecastHourChange={setForecastHour}
        onSelectStation={handleSelectStation}
        onSelectPoi={handleSelectPoi}
        onOpenNearMe={() => setActiveDrawer("near-me")}
      />

      {/* 2. TOP FLOATING HEADER */}
      <TopFloatingBar
        stations={stations}
        activeAlertCount={activeAlertCount}
        isManager={isManager}
        connectionStatus={connectionStatus}
        lastUpdated={lastUpdated}
        refreshData={refreshData}
        hasAIOverlay={hasAIOverlay}
        onClearAIOverlay={handleClearAIOverlay}
        onSelectCoordinates={handleFlyTo}
        onSelectStation={handleSelectStation}
        onSelectPoi={handleSelectPoi}
        onOpenAiChat={handleOpenAiChat}
        onOpenAlerts={() => setActiveDrawer("alerts")}
        onOpenProfile={() => setActiveDrawer("health-profile")}
        onOpenManagerDrawer={() => setActiveDrawer("manager-approval")}
        onOpenAudit={() => setActiveDrawer("audit")}
        onAskAiWithQuery={handleAskAiWithQuery}
      />

      {isManager && <ManagerStationStatusBar stations={stations} alerts={alerts} />}

      {/* 3. MAP LAYERS POPOVER */}
      {isLayersOpen && (
        <MapLayersPopover
          config={layerConfig}
          onChangeConfig={setLayerConfig}
          onClose={() => setIsLayersOpen(false)}
        />
      )}

      {/* 4. BOTTOM FLOATING ACTION DOCK */}
      <BottomActionDock
        activeDrawer={activeDrawer}
        isLayersOpen={isLayersOpen}
        activeAlertCount={activeAlertCount}
        onToggleLayers={() => setIsLayersOpen(!isLayersOpen)}
        onOpenDrawer={(drawer) => {
          setActiveDrawer(drawer);
          if (drawer !== null) setIsLayersOpen(false);
        }}
      />

      {/* 6. CONTEXTUAL RIGHT DRAWERS & MODALS */}
      {activeDrawer === "station-poi" && (activeStation || selectedPoi) && (
        <StationPoiDrawer
          station={activeStation}
          poi={selectedPoi}
          activeEnvironmentalLayer={layerConfig.activeEnvironmentalLayer}
          onClose={() => {
            setActiveDrawer(null);
            setSelectedStationId(null);
            setSelectedPoi(null);
          }}
          onOpenAnalysis={(stId) => {
            setSelectedStationId(stId);
            setActiveDrawer("analysis");
          }}
          onOpenForecast={(stationId) => {
            setSelectedStationId(stationId);
            setSelectedPoi(null);
            setActiveDrawer("forecast");
          }}
          onAskAiAboutStation={handleAskAiAboutStation}
        />
      )}

      {activeDrawer === "forecast" && activeStation && (
        <StationForecastDrawer
          station={activeStation}
          onBack={() => setActiveDrawer("station-poi")}
          onClose={() => {
            setActiveDrawer(null);
            setSelectedStationId(null);
          }}
        />
      )}

      {activeDrawer === "analysis" && selectedStationId && (
        <AnalysisWorkspaceDrawer
          stationId={selectedStationId}
          stations={stations}
          onClose={() => setActiveDrawer(null)}
          onSelectStationId={setSelectedStationId}
        />
      )}

      {activeDrawer === "ai-chat" && (
        <AiAssistantDrawer
          initialPrompt={aiInitialPrompt}
          onClose={handleCloseAiDrawer}
          mapContext={{
            selected_sensor: selectedStationId,
            selected_location: selectedPoi?.name || selectedPoi?.id,
            active_layer: layerConfig.activeEnvironmentalLayer,
            user_location: USER_DEFAULT_LOCATION,
          }}
        />
      )}

      {activeDrawer === "near-me" && (
        <NearMePanel
          onClose={() => setActiveDrawer(null)}
          onOpenAiChat={handleOpenAiChat}
        />
      )}

      {activeDrawer === "today" && (
        <TodaySummarySheet
          stations={stations}
          alerts={alerts}
          loading={loading}
          loadError={loadError}
          onClose={() => setActiveDrawer(null)}
          onOpenAiChat={handleOpenAiChat}
          onRetry={refreshData}
        />
      )}

      {activeDrawer === "alerts" && (
        <AlertsFlyout
          alerts={alerts}
          stations={stations}
          loading={loading}
          loadError={loadError}
          onRetry={refreshData}
          onClose={() => setActiveDrawer(null)}
          onShowAlertOnMap={handleShowAlertOnMap}
        />
      )}

      {activeDrawer === "health-profile" && (
        <HealthProfileDrawer
          profile={{ ...healthProfile, sensitivityGroup: userGroup }}
          onUpdateProfile={setHealthProfile}
          onClose={() => setActiveDrawer(null)}
        />
      )}

      {activeDrawer === "community-report" && (
        <CommunityReportModal
          onClose={() => setActiveDrawer(null)}
          onSubmitReport={handleCommunityReportSubmit}
        />
      )}

      {activeDrawer === "manager-approval" && isManager && (
        <ManagerApprovalDrawer
          proposals={proposals}
          loadError={proposalLoadError}
          onRetry={refreshData}
          onApprove={handleApproveProposal}
          onReject={handleRejectProposal}
          onClose={() => setActiveDrawer(null)}
          onOpenAudit={() => setActiveDrawer("audit")}
        />
      )}

      {/* Floating Audit Log Modal Overlay */}
      {activeDrawer === "audit" && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 2500,
            background: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => setActiveDrawer(null)}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: "16px",
              width: "min(1180px, calc(100vw - 48px))",
              maxHeight: "calc(100dvh - 48px)",
              overflowY: "auto",
              boxShadow: "0 20px 40px rgba(0,0,0,0.2)",
              position: "relative",
              padding: "24px",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <AuditLog stations={stations} onClose={() => setActiveDrawer(null)} />
          </div>
        </div>
      )}
    </div>
  );
};

const AppContent: React.FC = () => {
  const { currentScreen, setCurrentScreen, isAuthenticated, isLoading, role, navigateTo } = useAuth();

  // Data States
  const [stations, setStations] = useState<Station[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [proposalLoadError, setProposalLoadError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "updating" | "disconnected">("updating");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const isManager = role === "manager" || role === "admin";

  // Check URL pathname or query for deep links
  useEffect(() => {
    if (typeof window !== "undefined") {
      const pathname = window.location.pathname;
      const search = window.location.search;
      if (pathname.includes("verify-email") || (search.includes("token=") && !search.includes("reset"))) {
        setCurrentScreen("verify-email");
      } else if (pathname.includes("reset-password") || (search.includes("token=") && pathname.includes("reset"))) {
        setCurrentScreen("reset-password");
      } else if (pathname.includes("forgot-password")) {
        setCurrentScreen("forgot-password");
      }
    }
  }, [setCurrentScreen]);

  const refreshData = useCallback(async () => {
    setLoading(true);
    setConnectionStatus("updating");
    try {
      const [stationRes, alertRes] = await Promise.all([
        fetchStations(),
        fetchAlerts().catch(() => FALLBACK_ALERTS),
      ]);

      const validStations = Array.isArray(stationRes) && stationRes.length > 0 ? stationRes : FALLBACK_STATIONS;
      setStations(validStations);
      setAlerts(Array.isArray(alertRes) && alertRes.length > 0 ? alertRes : FALLBACK_ALERTS);
      setLoadError(null);
      setConnectionStatus("connected");
      setLastUpdated(new Date());

      if (isManager) {
        try {
          const propRes = await fetchProposals("pending");
          if (propRes && propRes.items) {
            setProposals(propRes.items);
          }
          setProposalLoadError(null);
        } catch {
          setProposalLoadError(null);
        }
      } else {
        setProposals([]);
        setProposalLoadError(null);
      }
    } catch (error) {
      console.warn("Backend connection delayed, using fallback simulation stations:", error);
      setStations(FALLBACK_STATIONS);
      setAlerts(FALLBACK_ALERTS);
      setConnectionStatus("connected");
      setLoadError(null);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, [isManager]);

  // Polling with Page Visibility API
  useEffect(() => {
    refreshData();

    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        refreshData();
      }
    }, 30000);

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        refreshData();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [refreshData]);

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          background: "#0f172a",
          color: "#f8fafc",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              display: "inline-block",
              width: "42px",
              height: "42px",
              border: "3px solid rgba(16,185,129,0.2)",
              borderTopColor: "#10b981",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
            }}
          />
          <p style={{ marginTop: "1rem", fontSize: "0.95rem", color: "#94a3b8", fontWeight: 500 }}>
            Đang tải AirGuard AI...
          </p>
        </div>
      </div>
    );
  }

  const publicAuthScreens = new Set([
    "login",
    "register",
    "verify-email",
    "forgot-password",
    "reset-password",
    "admin-coming-soon",
  ]);

  if (!isAuthenticated && !publicAuthScreens.has(currentScreen)) {
    return <Login />;
  }

  // Auth Screen Routing
  if (currentScreen === "login") {
    return <Login />;
  }
  if (currentScreen === "register") {
    return <Register />;
  }
  if (currentScreen === "verify-email") {
    return <VerifyEmail />;
  }
  if (currentScreen === "forgot-password") {
    return <ForgotPassword />;
  }
  if (currentScreen === "reset-password") {
    return <ResetPassword />;
  }
  if (currentScreen === "admin-coming-soon") {
    return <AdminComingSoon />;
  }

  // Admin / Special view overlay on map
  const renderScreenOverlay = () => {
    if (currentScreen === "station-detail") return <StationDetail />;
    if (currentScreen === "alerts") return <AlertList />;
    if (currentScreen === "approvals") return <ApprovalQueue />;
    if (currentScreen === "audit") return <AuditLog stations={stations} />;
    if (currentScreen === "profile") return <Profile />;
    if (currentScreen === "admin-users") return <UserManagement />;
    if (currentScreen === "admin-regions") return <RegionStations />;
    if (currentScreen === "admin-devices") return <IotDevices />;
    if ((currentScreen as string) === "admin-reports" || (currentScreen as string) === "reports") return <ReportViewer />;
    if (currentScreen === "admin-settings") return <AdminDashboard />;
    return null;
  };

  const specialOverlay = renderScreenOverlay();

  return (
    <>
      <SuperAppMain
        stations={stations}
        alerts={alerts}
        proposals={proposals}
        loading={loading}
        loadError={loadError}
        proposalLoadError={proposalLoadError}
        refreshData={refreshData}
        connectionStatus={connectionStatus}
        lastUpdated={lastUpdated}
      />
      {specialOverlay && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 3000,
            background: "#f8fafc",
            overflowY: "auto",
            padding: "20px",
          }}
        >
          <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
            <button
              onClick={() => navigateTo("dashboard")}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "#1e293b",
                color: "#fff",
                border: "none",
                borderRadius: "20px",
                padding: "8px 16px",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "0.85rem",
                marginBottom: "16px",
              }}
            >
              <ArrowLeft size={16} /> Trở về Bản đồ
            </button>
            {specialOverlay}
          </div>
        </div>
      )}
    </>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

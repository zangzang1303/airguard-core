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
import { DemoStationControl } from "./features/drawers/DemoStationControl";
import { NearMePanel } from "./features/drawers/NearMePanel";
import { TodaySummarySheet } from "./features/drawers/TodaySummarySheet";
import { AlertsFlyout } from "./features/drawers/AlertsFlyout";
import { HealthProfileDrawer } from "./features/drawers/HealthProfileDrawer";
import { CommunityReportModal } from "./features/drawers/CommunityReportModal";
import { ManagerApprovalDrawer } from "./features/drawers/ManagerApprovalDrawer";
import { FloatingPanelProvider } from "./features/floating";
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
} from "./api/client";
import { RefreshCw, TriangleAlert, ArrowLeft, CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
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
  refreshRevision: number;
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
  refreshRevision,
}) => {
  const { role, userGroup, demoMode } = useAuth();
  const isManager = role === "manager" || role === "admin";
  const canUseDemoControl = isManager && demoMode;

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
    showPlaces: false,
    showSensors: true,
    showHeatmap: true,
    showWindVectors: true,
    showCommunityReports: true,
    showConnectionStatus: true,
    showStationOverview: true,
    showDispersionInfo: true,
  });

  // User Health Profile State
  // User Health Profile State
  const [healthProfile, setHealthProfile] = useState<HealthProfile>({
    sensitivityGroup: "normal",
    fullName: "Cư dân Ocean Park 1",
    interests: ["running", "walking"],
    alertPushEnabled: true,
    dailyDigestEnabled: true,
  });

  // User Geolocation & Positioning State
  const [userLocation, setUserLocation] = useState<[number, number]>(() => {
    try {
      const saved = localStorage.getItem("airguard_user_location");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length === 2 && !isNaN(parsed[0]) && !isNaN(parsed[1])) {
          return parsed as [number, number];
        }
      }
    } catch {
      // fallback
    }
    return USER_DEFAULT_LOCATION;
  });

  const [userLocationName, setUserLocationName] = useState<string>(() => {
    return localStorage.getItem("airguard_user_location_name") || "Vị trí của bạn (Ocean Park 1)";
  });

  const [userLocationSource, setUserLocationSource] = useState<"gps" | "search" | "manual_click" | "default">(() => {
    return (localStorage.getItem("airguard_user_location_source") as any) || "default";
  });

  const [userLocationAccuracy, setUserLocationAccuracy] = useState<number | null>(null);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [isPickingOnMap, setIsPickingOnMap] = useState<boolean>(false);
  const [locationNotice, setLocationNotice] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  // Auto-dismiss location notice
  useEffect(() => {
    if (locationNotice) {
      const timer = setTimeout(() => {
        setLocationNotice(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [locationNotice]);

  const handleSetUserLocation = useCallback(
    (
      coords: [number, number],
      name: string,
      source: "gps" | "search" | "manual_click" | "default",
      accuracy: number | null = null
    ) => {
      setUserLocation(coords);
      setUserLocationName(name);
      setUserLocationSource(source);
      setUserLocationAccuracy(accuracy);
      setFlyToTarget(coords);

      try {
        localStorage.setItem("airguard_user_location", JSON.stringify(coords));
        localStorage.setItem("airguard_user_location_name", name);
        localStorage.setItem("airguard_user_location_source", source);
      } catch (e) {
        console.warn("Could not persist user location:", e);
      }

      if (source === "gps") {
        setLocationNotice({
          type: "success",
          message: `🎯 Đã định vị thành công vị trí GPS của bạn (độ chính xác ~${Math.round(accuracy || 50)}m)`,
        });
      } else if (source === "manual_click") {
        setLocationNotice({
          type: "success",
          message: `📍 Đã cập nhật vị trí của bạn tại toạ độ (${coords[0].toFixed(4)}, ${coords[1].toFixed(4)})`,
        });
      } else if (source === "search") {
        setLocationNotice({
          type: "success",
          message: `📍 Đã đặt vị trí của bạn tại: ${name}`,
        });
      }
    },
    []
  );

  const handleLocateGps = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationNotice({
        type: "error",
        message: "Trình duyệt của bạn không hỗ trợ định vị GPS. Vui lòng nhập địa điểm hoặc chọn trực tiếp trên bản đồ.",
      });
      return;
    }

    setIsLocating(true);
    setLocationNotice({
      type: "info",
      message: "Đang dò tìm tín hiệu GPS vệ tinh của thiết bị...",
    });

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setIsLocating(false);
        const { latitude, longitude, accuracy } = position.coords;
        handleSetUserLocation(
          [latitude, longitude],
          "Vị trí GPS hiện tại của bạn",
          "gps",
          accuracy
        );
      },
      (error) => {
        setIsLocating(false);
        let errorMsg = "Không thể lấy vị trí GPS.";
        if (error.code === error.PERMISSION_DENIED) {
          errorMsg = "Quyền truy cập vị trí GPS bị từ chối. Bạn có thể nhập địa chỉ vào ô tìm kiếm hoặc bấm nút 'Chọn điểm trên map'.";
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          errorMsg = "Tín hiệu GPS không khả dụng. Bạn có thể nhập vị trí hoặc chấm chọn trên bản đồ.";
        } else if (error.code === error.TIMEOUT) {
          errorMsg = "Quá thời gian lấy toạ độ GPS. Vui lòng thử lại hoặc chọn vị trí trên bản đồ.";
        }
        setLocationNotice({
          type: "error",
          message: errorMsg,
        });
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000,
      }
    );
  }, [handleSetUserLocation]);

  const handleStartPickingOnMap = useCallback(() => {
    setIsPickingOnMap(true);
    setLocationNotice({
      type: "info",
      message: "Chế độ chọn vị trí đang bật: Chạm vào điểm bất kỳ trên bản đồ để ghim vị trí.",
    });
  }, []);

  const handleCancelPickingOnMap = useCallback(() => {
    setIsPickingOnMap(false);
  }, []);

  const handleMapClickLocation = useCallback(
    (coords: [number, number]) => {
      setIsPickingOnMap(false);
      handleSetUserLocation(
        coords,
        `Điểm đã chọn (${coords[0].toFixed(4)}, ${coords[1].toFixed(4)})`,
        "manual_click"
      );
    },
    [handleSetUserLocation]
  );

  const handleResetDefaultLocation = useCallback(() => {
    handleSetUserLocation(USER_DEFAULT_LOCATION, "Trung tâm Vinhomes Ocean Park 1", "default");
  }, [handleSetUserLocation]);

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
  const handleLayerConfigChange = useCallback((newConfig: MapLayerConfig) => {
    if (!newConfig.showForecastTimeline) {
      setForecastHour(0);
    }
    setLayerConfig(newConfig);
  }, []);

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
    <FloatingPanelProvider boundarySelector=".map-super-app-root">
    <div
      className={`map-super-app-root${isManager ? " is-manager" : ""}`}
      style={{ width: "100vw", height: "100dvh", position: "relative", overflow: "hidden", margin: 0, padding: 0 }}
    >
      {/* Location Status Toast Banner */}
      {locationNotice && (
        <div className={`map-location-toast ${locationNotice.type}`} role="alert">
          {locationNotice.type === "success" && <CheckCircle2 size={16} className="toast-icon" />}
          {locationNotice.type === "error" && <AlertTriangle size={16} className="toast-icon" />}
          {locationNotice.type === "info" && <Info size={16} className="toast-icon" />}
          <span className="toast-message">{locationNotice.message}</span>
          <button
            type="button"
            className="toast-close-btn"
            onClick={() => setLocationNotice(null)}
            aria-label="Đóng thông báo"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* 1. LEAFLET MAP (100% Viewport Height & Width) */}
      <SuperMap
        stations={stations}
        selectedStationId={selectedStationId}
        criticalStationIds={criticalStationIds}
        selectedPoi={selectedPoi}
        layerConfig={layerConfig}
        refreshRevision={refreshRevision}
        flyToTarget={flyToTarget}
        forecastHour={forecastHour}
        userCoords={userLocation}
        userLocationAccuracy={userLocationAccuracy}
        userLocationName={userLocationName}
        userLocationSource={userLocationSource}
        isLocating={isLocating}
        isPickingOnMap={isPickingOnMap}
        onForecastHourChange={setForecastHour}
        onSelectStation={handleSelectStation}
        onSelectPoi={handleSelectPoi}
        onOpenNearMe={() => setActiveDrawer("near-me")}
        onLocateGps={handleLocateGps}
        onTogglePickOnMap={() => (isPickingOnMap ? handleCancelPickingOnMap() : handleStartPickingOnMap())}
        onCancelPicking={handleCancelPickingOnMap}
        onMapClickLocation={handleMapClickLocation}
        onUserLocationChange={(coords, src) =>
          handleSetUserLocation(
            coords,
            `Điểm đã kéo thả (${coords[0].toFixed(4)}, ${coords[1].toFixed(4)})`,
            src
          )
        }
        onResetDefaultLocation={handleResetDefaultLocation}
      />

      {/* 2. TOP FLOATING HEADER */}
      <TopFloatingBar
        stations={stations}
        activeAlertCount={activeAlertCount}
        isManager={isManager}
        connectionStatus={connectionStatus}
        lastUpdated={lastUpdated}
        isAlertsOpen={activeDrawer === "alerts"}
        refreshData={refreshData}
        showConnectionStatus={layerConfig.showConnectionStatus}
        hasAIOverlay={hasAIOverlay}
        onClearAIOverlay={handleClearAIOverlay}
        onSelectCoordinates={handleFlyTo}
        onSelectStation={handleSelectStation}
        onSelectPoi={handleSelectPoi}
        onOpenAlerts={() => setActiveDrawer("alerts")}
        onOpenProfile={() => setActiveDrawer("health-profile")}
        onOpenManagerDrawer={() => setActiveDrawer("manager-approval")}
        onOpenAudit={() => setActiveDrawer("audit")}
        onAskAiWithQuery={handleAskAiWithQuery}
        onSetUserLocation={handleSetUserLocation}
        onLocateGps={handleLocateGps}
        onStartPickOnMap={handleStartPickingOnMap}
      />

      {isManager && layerConfig.showStationOverview && (
        <ManagerStationStatusBar stations={stations} alerts={alerts} />
      )}
      {canUseDemoControl && (layerConfig.showDemoControl ?? true) && (
        <DemoStationControl floating />
      )}

      {/* 3. MAP LAYERS POPOVER */}
      {isLayersOpen && (
        <MapLayersPopover
          config={layerConfig}
          onChangeConfig={handleLayerConfigChange}
          onClose={() => setIsLayersOpen(false)}
        />
      )}

      {/* 4. BOTTOM FLOATING ACTION DOCK */}
      <BottomActionDock
        activeDrawer={activeDrawer}
        isLayersOpen={isLayersOpen}
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
            user_location: userLocation
              ? {
                  lat: userLocation[0],
                  lng: userLocation[1],
                  source: userLocationSource,
                  name: userLocationName,
                }
              : null,
            selected_origin:
              userLocation && userLocationSource === "manual_click"
                ? {
                    lat: userLocation[0],
                    lng: userLocation[1],
                    source: "map_selection",
                    name: userLocationName || `Điểm đã chọn (${userLocation[0].toFixed(4)}, ${userLocation[1].toFixed(4)})`,
                  }
                : null,
          }}
        />
      )}

      {activeDrawer === "near-me" && (
        <NearMePanel
          userLocation={userLocation}
          userLocationName={userLocationName}
          userLocationSource={userLocationSource}
          userLocationAccuracy={userLocationAccuracy}
          stations={stations}
          isLocating={isLocating}
          onClose={() => setActiveDrawer(null)}
          onOpenAiChat={handleOpenAiChat}
          onLocateGps={handleLocateGps}
          onStartPickOnMap={handleStartPickingOnMap}
          onSelectStation={handleSelectStation}
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
    </FloatingPanelProvider>
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
  const [refreshRevision, setRefreshRevision] = useState<number>(0);

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
        fetchAlerts(),
      ]);

      setStations(Array.isArray(stationRes) ? stationRes : []);
      setAlerts(Array.isArray(alertRes) ? alertRes : []);
      setRefreshRevision((revision) => revision + 1);
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
        } catch (error) {
          setProposals([]);
          setProposalLoadError(
            error instanceof Error
              ? error.message
              : "Không thể tải hàng đợi phê duyệt. Vui lòng thử lại.",
          );
        }
      } else {
        setProposals([]);
        setProposalLoadError(null);
      }
    } catch (error) {
      console.warn("Backend environmental data is unavailable:", error);
      setStations([]);
      setAlerts([]);
      setProposals([]);
      setConnectionStatus("disconnected");
      setLoadError(
        error instanceof Error
          ? error.message
          : "Không thể tải dữ liệu môi trường từ backend. Vui lòng thử lại.",
      );
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
    if (!isAuthenticated) {
      return <Login />;
    }
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
        refreshRevision={refreshRevision}
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

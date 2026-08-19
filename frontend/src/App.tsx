import React, { useState, useEffect, useCallback } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { SuperMap } from "./features/map/SuperMap";
import { TopFloatingBar } from "./features/navigation/TopFloatingBar";
import { BottomActionDock } from "./features/navigation/BottomActionDock";
import { MapLayersPopover } from "./features/navigation/MapLayersPopover";
import { StationPoiDrawer } from "./features/drawers/StationPoiDrawer";
import { AnalysisWorkspaceDrawer } from "./features/drawers/AnalysisWorkspaceDrawer";
import { AiAssistantDrawer } from "./features/drawers/AiAssistantDrawer";
import { ForecastSliderBar, FORECAST_STEPS } from "./features/drawers/ForecastSliderBar";
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
  AiMapHighlightArea,
  RouteOption,
  HealthProfile,
  CommunityReport,
} from "./types/superApp";
import {
  fetchStations,
  fetchAlerts,
  fetchProposals,
  approveProposal,
  rejectProposal,
  FALLBACK_STATIONS,
  FALLBACK_ALERTS,
} from "./api/client";
import { OCEAN_PARK_POIS } from "./features/map/poiData";
import "./theme.css";
import "./styles.css";

const SuperAppMain: React.FC = () => {
  const { role } = useAuth();
  const isManager = role === "manager" || role === "admin";

  // Data States
  const [stations, setStations] = useState<Station[]>(FALLBACK_STATIONS);
  const [alerts, setAlerts] = useState<Alert[]>(FALLBACK_ALERTS);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);

  // Active Overlay & Drawer States
  const [activeDrawer, setActiveDrawer] = useState<ActiveDrawerType>(null);
  const [isLayersOpen, setIsLayersOpen] = useState(false);
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const [selectedPoi, setSelectedPoi] = useState<PlacePOI | null>(null);

  // Map Controls & Highlight States
  const [flyToTarget, setFlyToTarget] = useState<[number, number] | null>(null);
  const [aiHighlights, setAiHighlights] = useState<AiMapHighlightArea[]>([]);
  const [activeRoute, setActiveRoute] = useState<RouteOption | null>(null);
  const [forecastStepIdx, setForecastStepIdx] = useState(0);

  // Layer Configuration State
  const [layerConfig, setLayerConfig] = useState<MapLayerConfig>({
    activeEnvironmentalLayer: "aqi",
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

  // Fetch Live Data
  const refreshData = useCallback(async () => {
    try {
      const [stationRes, alertRes] = await Promise.all([
        fetchStations().catch(() => FALLBACK_STATIONS),
        fetchAlerts().catch(() => FALLBACK_ALERTS),
      ]);

      if (Array.isArray(stationRes) && stationRes.length > 0) {
        setStations(stationRes);
      }
      if (Array.isArray(alertRes)) {
        setAlerts(alertRes);
      }

      if (isManager) {
        try {
          const propRes = await fetchProposals("pending");
          if (propRes && propRes.items) {
            setProposals(propRes.items);
          }
        } catch {
          // ignore manager proposal error for non-managers
        }
      }
    } finally {
      setLoading(false);
    }
  }, [isManager]);


  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, [refreshData]);

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

  const handleFlyTo = (coords: [number, number], title?: string) => {
    setFlyToTarget(coords);
  };

  const handleShowAlertOnMap = (stId: string) => {
    setActiveDrawer("station-poi");
    handleSelectStation(stId);
  };

  const handleAskAiAboutStation = (placeName: string, aqi: number | null) => {
    setActiveDrawer("ai-chat");
  };

  const handleAskAiWithQuery = (query: string) => {
    setActiveDrawer("ai-chat");
  };

  const handleApproveProposal = async (proposalId: string, version: number) => {
    await approveProposal(proposalId, version);
    await refreshData();
  };

  const handleRejectProposal = async (proposalId: string, version: number, note: string) => {
    await rejectProposal(proposalId, version, note);
    await refreshData();
  };

  const handleCommunityReportSubmit = (report: Partial<CommunityReport>) => {
    console.log("Community Report Submitted:", report);
  };

  const activeStation = stations.find((s) => s.station_id === selectedStationId) || null;
  const currentForecastStep = FORECAST_STEPS[forecastStepIdx] || FORECAST_STEPS[0];

  return (
    <div className="map-super-app-root">
      {/* 1. FULL-SCREEN 100% VIEWPORT LEAFLET MAP */}
      <SuperMap
        stations={stations}
        selectedStationId={selectedStationId}
        selectedPoi={selectedPoi}
        layerConfig={layerConfig}
        flyToTarget={flyToTarget}
        aiHighlights={aiHighlights}
        activeRoute={activeRoute}
        forecastMultiplier={currentForecastStep.heatMultiplier}
        onSelectStation={handleSelectStation}
        onSelectPoi={handleSelectPoi}
        onOpenNearMe={() => setActiveDrawer("near-me")}
      />

      {/* 2. TOP FLOATING HEADER (Omnibox Search & Controls) */}
      <TopFloatingBar
        stations={stations}
        activeAlertCount={alerts.length}
        isManager={isManager}
        onSelectCoordinates={handleFlyTo}
        onSelectStation={handleSelectStation}
        onSelectPoi={handleSelectPoi}
        onOpenAiChat={() => setActiveDrawer("ai-chat")}
        onOpenAlerts={() => setActiveDrawer("alerts")}
        onOpenProfile={() => setActiveDrawer("health-profile")}
        onOpenManagerDrawer={() => setActiveDrawer("manager-approval")}
        onAskAiWithQuery={handleAskAiWithQuery}
      />

      {/* 3. MAP LAYERS POPOVER (Bottom Left) */}
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
        activeAlertCount={alerts.length}
        onToggleLayers={() => setIsLayersOpen(!isLayersOpen)}
        onOpenDrawer={(drawer) => {
          setActiveDrawer(drawer);
          if (drawer !== null) setIsLayersOpen(false);
        }}
      />

      {/* 5. FORECAST TIMELINE SLIDER (When active) */}
      {activeDrawer === "forecast-bar" && (
        <ForecastSliderBar
          activeStepIndex={forecastStepIdx}
          onSelectStepIndex={setForecastStepIdx}
          onClose={() => setActiveDrawer(null)}
        />
      )}

      {/* 6. CONTEXTUAL RIGHT DRAWERS & MODALS */}

      {/* Station / POI Detail Drawer */}
      {activeDrawer === "station-poi" && (activeStation || selectedPoi) && (
        <StationPoiDrawer
          station={activeStation}
          poi={selectedPoi}
          onClose={() => {
            setActiveDrawer(null);
            setSelectedStationId(null);
            setSelectedPoi(null);
          }}
          onOpenAnalysis={(stId) => {
            setSelectedStationId(stId);
            setActiveDrawer("analysis");
          }}
          onOpenForecast={(stId) => {
            setActiveDrawer("forecast-bar");
          }}
          onAskAiAboutStation={handleAskAiAboutStation}
        />
      )}

      {/* 24h Contextual Analysis Workspace Drawer */}
      {activeDrawer === "analysis" && (
        <AnalysisWorkspaceDrawer
          stationId={selectedStationId || "S03"}
          stations={stations}
          onClose={() => setActiveDrawer(null)}
          onSelectStationId={setSelectedStationId}
        />
      )}

      {/* AirGuard AI Assistant Drawer */}
      {activeDrawer === "ai-chat" && (
        <AiAssistantDrawer
          stations={stations}
          onClose={() => setActiveDrawer(null)}
          onHighlightAreas={setAiHighlights}
          onSetRoute={setActiveRoute}
          onFlyTo={handleFlyTo}
        />
      )}

      {/* Near Me Bottom Sheet */}
      {activeDrawer === "near-me" && (
        <NearMePanel
          onClose={() => setActiveDrawer(null)}
          onOpenForecast={() => setActiveDrawer("forecast-bar")}
          onOpenAiChat={() => setActiveDrawer("ai-chat")}
        />
      )}

      {/* Today Environmental Summary */}
      {activeDrawer === "today" && (
        <TodaySummarySheet
          onClose={() => setActiveDrawer(null)}
          onOpenForecast={() => setActiveDrawer("forecast-bar")}
        />
      )}

      {/* Active Environmental Alerts Flyout */}
      {activeDrawer === "alerts" && (
        <AlertsFlyout
          alerts={alerts}
          stations={stations}
          onClose={() => setActiveDrawer(null)}
          onShowAlertOnMap={handleShowAlertOnMap}
        />
      )}

      {/* Personal Health Profile & Settings */}
      {activeDrawer === "health-profile" && (
        <HealthProfileDrawer
          profile={healthProfile}
          onUpdateProfile={setHealthProfile}
          onClose={() => setActiveDrawer(null)}
        />
      )}

      {/* Community Report Issue Modal */}
      {activeDrawer === "community-report" && (
        <CommunityReportModal
          onClose={() => setActiveDrawer(null)}
          onSubmitReport={handleCommunityReportSubmit}
        />
      )}

      {/* Manager HITL Approval Drawer */}
      {activeDrawer === "manager-approval" && isManager && (
        <ManagerApprovalDrawer
          proposals={proposals}
          onApprove={handleApproveProposal}
          onReject={handleRejectProposal}
          onClose={() => setActiveDrawer(null)}
        />
      )}
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <SuperAppMain />
    </AuthProvider>
  );
}

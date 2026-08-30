import React, { useEffect, useState, useCallback, useRef } from "react";
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { SpatialHeatmapResponse, Station, VentilationDevice } from "../../types";
import { MapLayerConfig, PlacePOI } from "../../types/superApp";
import { MAP_CENTER_OCEAN_PARK } from "./poiData";
import { OceanParkBoundary } from "./OceanParkBoundary";
import { SensorMarkers } from "./SensorMarkers";
import { UserLocationMarker } from "./UserLocationMarker";
import { SubZoneLabels } from "./SubZoneLabels";
import { AqiLegend, MapLegendVariant } from "./AqiLegend";
import { HeatmapLayer } from "../stations/HeatmapLayer";
import { mapActionController } from "./MapActionController";
import { useFloatingPanelContext, useDraggableFloatingPanel } from "../floating";
import { Crosshair, X } from "lucide-react";
import { VentilationDeviceMarkers } from "./VentilationDeviceMarkers";
import { DraggableTimelineDock } from "./DraggableTimelineDock";
import { LocalBasemapFallback } from "./LocalBasemapFallback";

interface SuperMapProps {
  stations: Station[];
  selectedStationId: string | null;
  criticalStationIds: ReadonlySet<string>;
  selectedPoi: PlacePOI | null;
  layerConfig: MapLayerConfig;
  ventilationDevices?: VentilationDevice[];
  isManager?: boolean;
  flyToTarget: [number, number] | null;
  forecastHour?: number;
  refreshRevision?: number;
  userCoords?: [number, number];
  userLocationAccuracy?: number | null;
  userLocationName?: string;
  userLocationSource?: "gps" | "search" | "manual_click" | "default";
  isPickingOnMap?: boolean;
  onForecastHourChange?: (hours: number) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onSelectVentilationDevice?: (device: VentilationDevice) => void;
  onOpenNearMe: () => void;
  onCancelPicking?: () => void;
  onMapClickLocation?: (coords: [number, number]) => void;
  onUserLocationChange?: (coords: [number, number], source: "manual_click") => void;
  onToggleMapLegend?: () => void;
}

// Controller component to bind Leaflet map to MapActionController & FloatingPanelProvider
const MapActionBinder: React.FC = () => {
  const map = useMap();
  const { registerMap } = useFloatingPanelContext();

  useEffect(() => {
    mapActionController.setMap(map);
    registerMap(map);
    return () => {
      mapActionController.setMap(null);
      registerMap(null);
    };
  }, [map, registerMap]);

  return null;
};

// Controller component to smoothly animate camera to target
const MapCameraController: React.FC<{
  flyToTarget: [number, number] | null;
}> = ({ flyToTarget }) => {
  const map = useMap();

  useEffect(() => {
    if (flyToTarget) {
      map.flyTo(flyToTarget, 16, {
        animate: true,
        duration: 1.2,
      });
    }
  }, [flyToTarget, map]);

  return null;
};

// Click handler on map
const MapClickHandler: React.FC<{
  isPickingOnMap: boolean;
  onMapClickLocation?: (coords: [number, number]) => void;
}> = ({ isPickingOnMap, onMapClickLocation }) => {
  useMapEvents({
    click(e) {
      if (isPickingOnMap && onMapClickLocation) {
        onMapClickLocation([e.latlng.lat, e.latlng.lng]);
      }
    },
  });

  return null;
};

const DraggableLegendOverlay: React.FC<{
  variant?: MapLegendVariant;
  metric?: any;
  forecastHour?: number;
  dispersionData?: SpatialHeatmapResponse | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onCloseLegend?: () => void;
}> = ({
  variant = "stations",
  metric,
  forecastHour = 0,
  dispersionData,
  loading,
  error,
  onRetry,
  onCloseLegend,
}) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "map-legend",
    group: "widget",
  });

  return (
    <div {...containerProps} className="map-legend-overlay">
      <AqiLegend
        variant={variant}
        showStationStatus={false}
        metric={metric}
        forecastHour={forecastHour}
        dispersionData={dispersionData}
        loading={loading}
        error={error}
        onRetry={onRetry}
        headerProps={handleProps}
        onClose={onCloseLegend}
      />
    </div>
  );
};

export const SuperMap: React.FC<SuperMapProps> = ({
  stations,
  selectedStationId,
  criticalStationIds,
  selectedPoi,
  layerConfig,
  ventilationDevices = [],
  isManager = false,
  flyToTarget,
  forecastHour = 0,
  refreshRevision = 0,
  userCoords,
  userLocationAccuracy,
  userLocationName,
  userLocationSource = "default",
  isPickingOnMap = false,
  onForecastHourChange,
  onSelectStation,
  onSelectPoi,
  onSelectVentilationDevice,
  onOpenNearMe,
  onCancelPicking,
  onMapClickLocation,
  onUserLocationChange,
  onToggleMapLegend,
}) => {
  const viewMode = layerConfig.viewMode ?? (layerConfig.showHeatmap ? "heatmap" : "markers");

  const [dispersionData, setDispersionData] = useState<SpatialHeatmapResponse | null>(null);
  const [dispersionLoading, setDispersionLoading] = useState(false);
  const [dispersionError, setDispersionError] = useState<string | null>(null);
  const [basemapRevision, setBasemapRevision] = useState(0);
  const [basemapStatus, setBasemapStatus] = useState<"loading" | "ready" | "degraded">("loading");
  const [tileErrorCount, setTileErrorCount] = useState(0);
  const heatmapRetryRef = useRef<(() => void) | null>(null);
  const handleHeatmapDataChange = useCallback(
    (data: SpatialHeatmapResponse | null, loading: boolean, error: string | null) => {
      setDispersionData(data);
      setDispersionLoading(loading);
      setDispersionError(error);
    },
    []
  );

  return (
    <div className={`super-map-wrapper ${isPickingOnMap ? "is-picking-mode" : ""}`}>
      {/* Picking on Map Prompt Floating Banner */}
      {isPickingOnMap && (
        <div className="map-picking-banner" role="status" aria-live="polite">
          <div className="picking-banner-content">
            <Crosshair size={18} className="picking-banner-icon spin-slow" />
            <div className="picking-banner-text">
              <strong>Chế độ chọn vị trí</strong>
              <span>Chạm hoặc click vào điểm bất kỳ trên bản đồ để ghim vị trí của bạn</span>
            </div>
          </div>
          {onCancelPicking && (
            <button
              type="button"
              className="picking-cancel-btn"
              onClick={onCancelPicking}
              aria-label="Hủy chọn vị trí"
            >
              <X size={15} aria-hidden="true" />
              <span>Hủy</span>
            </button>
          )}
        </div>
      )}

      <MapContainer
        center={userCoords || MAP_CENTER_OCEAN_PARK}
        zoom={15}
        minZoom={13}
        maxZoom={18}
        zoomControl={false}
        attributionControl
        style={{ width: "100%", height: "100%" }}
      >
        <MapActionBinder />
        <MapCameraController flyToTarget={flyToTarget} />
        <MapClickHandler
          isPickingOnMap={isPickingOnMap}
          onMapClickLocation={onMapClickLocation}
        />

        <LocalBasemapFallback />

        {/* Use OpenStreetMap directly: CARTO can return an "API KEY REQUIRED" image
            as a successful tile response, which would otherwise look like a map error. */}
        <TileLayer
          key={basemapRevision}
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
          errorTileUrl="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="
          eventHandlers={{
            tileload: () => setBasemapStatus("ready"),
            tileerror: () => {
              setTileErrorCount((count) => count + 1);
              setBasemapStatus("degraded");
            },
          }}
        />

        {/* Spatial Dispersion Heatmap Canvas Layer */}
        <HeatmapLayer
          activeLayer={layerConfig.activeEnvironmentalLayer}
          forecastHour={forecastHour}
          viewMode={viewMode}
          showHeatmap={layerConfig.showHeatmap}
          refreshRevision={refreshRevision}
          onDataChange={handleHeatmapDataChange}
          onRetryRef={heatmapRetryRef}
        />

        {/* Ocean Park 1 Boundary Polygon */}
        <OceanParkBoundary
          showBoundary={layerConfig.showBoundary}
        />

        {/* Sub-zone Neighborhood Text Labels */}
        <SubZoneLabels
          showPlaces={layerConfig.showPlaces}
          selectedPoiId={selectedPoi?.id || null}
          onSelectPoi={onSelectPoi}
        />

        {/* Sensor Markers (Only visible in markers mode or when explicitly shown) */}
        <SensorMarkers
          stations={stations}
          selectedStationId={selectedStationId}
          criticalStationIds={criticalStationIds}
          onSelectStation={onSelectStation}
          showSensors={layerConfig.showSensors}
          activeMetric={layerConfig.activeEnvironmentalLayer}
        />

        {/* Manager-only simulated ventilation infrastructure layer. */}
        <VentilationDeviceMarkers
          devices={ventilationDevices}
          visible={Boolean(isManager && layerConfig.showVentilationDevices && onSelectVentilationDevice)}
          onSelectDevice={(device) => onSelectVentilationDevice?.(device)}
        />

        {/* Resident Location Pin ("You") */}
        <UserLocationMarker
          onClick={onOpenNearMe}
          userCoords={userCoords}
          accuracyMeters={userLocationAccuracy}
          locationName={userLocationName}
          source={userLocationSource}
          onLocationChange={onUserLocationChange}
        />
      </MapContainer>

      {basemapStatus === "degraded" && (
        <div className="local-basemap-notice" role="status">
          <span>Đang dùng nền bản đồ nội bộ giản lược vì OSM không khả dụng ({tileErrorCount} ô lỗi).</span>
          <button
            type="button"
            onClick={() => {
              setTileErrorCount(0);
              setBasemapStatus("loading");
              setBasemapRevision((revision) => revision + 1);
            }}
          >
            Thử tải lại
          </button>
        </div>
      )}

      {/* Unified Context-Aware Map Legend Overlay */}
      {(layerConfig.showMapLegend ?? true) && (
        <DraggableLegendOverlay
          variant={viewMode === "heatmap" ? "dispersion" : "stations"}
          metric={layerConfig.activeEnvironmentalLayer}
          forecastHour={forecastHour}
          dispersionData={dispersionData}
          loading={dispersionLoading}
          error={dispersionError}
          onRetry={() => heatmapRetryRef.current?.()}
          onCloseLegend={onToggleMapLegend}
        />
      )}

      {/* Floating Map Forecast Timeline Control Dock (Bottom Center) */}
      {onForecastHourChange && viewMode === "heatmap" && (layerConfig.showForecastTimeline ?? true) && (
        <DraggableTimelineDock
          stationId={selectedStationId}
          currentAqi={stations.find((station) => station.station_id === selectedStationId)?.aqi ?? null}
          forecastHour={forecastHour}
          onForecastHourChange={onForecastHourChange}
        />
      )}
    </div>
  );
};

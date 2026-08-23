import React, { useEffect } from "react";
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Station } from "../../types";
import { MapLayerConfig, PlacePOI } from "../../types/superApp";
import { MAP_CENTER_OCEAN_PARK, OCEAN_PARK_1_BOUNDARY } from "./poiData";
import { OceanParkBoundary } from "./OceanParkBoundary";
import { SensorMarkers } from "./SensorMarkers";
import { UserLocationMarker } from "./UserLocationMarker";
import { SubZoneLabels } from "./SubZoneLabels";
import { AqiLegend } from "./AqiLegend";
import { HeatmapLayer } from "../stations/HeatmapLayer";
import { TimelineSlider } from "../stations/TimelineSlider";
import { MapLocationControls } from "./MapLocationControls";
import { mapActionController } from "./MapActionController";
import { Crosshair, X } from "lucide-react";

interface SuperMapProps {
  stations: Station[];
  selectedStationId: string | null;
  criticalStationIds: ReadonlySet<string>;
  selectedPoi: PlacePOI | null;
  layerConfig: MapLayerConfig;
  flyToTarget: [number, number] | null;
  forecastHour?: number;
  userCoords?: [number, number];
  userLocationAccuracy?: number | null;
  userLocationName?: string;
  userLocationSource?: "gps" | "search" | "manual_click" | "default";
  isLocating?: boolean;
  isPickingOnMap?: boolean;
  onForecastHourChange?: (hours: number) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onOpenNearMe: () => void;
  onLocateGps?: () => void;
  onTogglePickOnMap?: () => void;
  onCancelPicking?: () => void;
  onMapClickLocation?: (coords: [number, number]) => void;
  onUserLocationChange?: (coords: [number, number], source: "manual_click") => void;
  onResetDefaultLocation?: () => void;
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

const DraggableLegendOverlay: React.FC<{ metric?: any }> = ({ metric }) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "map-legend",
    group: "widget",
  });

  return (
    <div {...containerProps} className="map-legend-overlay">
      <AqiLegend showStationStatus={true} metric={metric} headerProps={handleProps} />
    </div>
  );
};

const DraggableTimelineDock: React.FC<{
  forecastHour: number;
  onForecastHourChange: (hours: number) => void;
}> = ({ forecastHour, onForecastHourChange }) => {
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "timeline",
    group: "widget",
  });

  return (
    <div {...containerProps} className="map-timeline-floating-dock">
      <div className="no-drag" data-no-drag="true" style={{ width: "100%" }}>
        <TimelineSlider
          value={forecastHour}
          onChange={onForecastHourChange}
          label="Thanh trượt dự báo lan truyền"
          titleProps={handleProps}
        />
      </div>
    </div>
  );
};

// Click handler for picking location on map
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

export const SuperMap: React.FC<SuperMapProps> = ({
  stations,
  selectedStationId,
  criticalStationIds,
  selectedPoi,
  layerConfig,
  flyToTarget,
  forecastHour = 0,
  userCoords,
  userLocationAccuracy,
  userLocationName,
  userLocationSource = "default",
  isLocating = false,
  isPickingOnMap = false,
  onForecastHourChange,
  onSelectStation,
  onSelectPoi,
  onOpenNearMe,
  onLocateGps,
  onTogglePickOnMap,
  onCancelPicking,
  onMapClickLocation,
  onUserLocationChange,
  onResetDefaultLocation,
}) => {
  const viewMode = layerConfig.viewMode ?? (layerConfig.showHeatmap ? "heatmap" : "markers");

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
        attributionControl={false}
        style={{ width: "100%", height: "100%" }}
      >
        <MapActionBinder />
        <MapClickHandler
          isPickingOnMap={isPickingOnMap}
          onMapClickLocation={onMapClickLocation}
        />

        {/* Base Map Tiles — CartoDB Voyager Clean High-Contrast */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={20}
        />

        {/* Spatial Dispersion Heatmap Canvas Layer */}
        <HeatmapLayer
          activeLayer={layerConfig.activeEnvironmentalLayer}
          forecastHour={forecastHour}
          viewMode={viewMode}
          showHeatmap={layerConfig.showHeatmap}
          showMetadata={layerConfig.showDispersionInfo}
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
          showSensors={layerConfig.showSensors && viewMode !== "heatmap"}
          activeMetric={layerConfig.activeEnvironmentalLayer}
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

      {/* Floating Map Location Controls (GPS Locate + Pick on Map + Reset) */}
      {onLocateGps && onTogglePickOnMap && (
        <MapLocationControls
          isLocating={isLocating}
          isPickingOnMap={isPickingOnMap}
          onLocateGps={onLocateGps}
          onTogglePickOnMap={onTogglePickOnMap}
          onResetDefaultLocation={onResetDefaultLocation}
        />
      )}

      {/* Accessible Map Legend Overlay (Bottom Right — Only in markers view mode when heatmap is NOT active) */}
      {viewMode === "markers" && !layerConfig.showHeatmap && (
        <DraggableLegendOverlay metric={layerConfig.activeEnvironmentalLayer} />
      )}

      {/* Floating Map Forecast Timeline Control Dock (Bottom Center) */}
      {onForecastHourChange && viewMode === "heatmap" && (
        <DraggableTimelineDock
          forecastHour={forecastHour}
          onForecastHourChange={onForecastHourChange}
        />
      )}
    </div>
  );
};

import React, { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
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
import { mapActionController } from "./MapActionController";

interface SuperMapProps {
  stations: Station[];
  selectedStationId: string | null;
  criticalStationIds: ReadonlySet<string>;
  selectedPoi: PlacePOI | null;
  layerConfig: MapLayerConfig;
  flyToTarget: [number, number] | null;
  forecastHour?: number;
  onForecastHourChange?: (hours: number) => void;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onOpenNearMe: () => void;
}

// Controller component to bind Leaflet map to MapActionController
const MapActionBinder: React.FC = () => {
  const map = useMap();
  useEffect(() => {
    mapActionController.setMap(map);
    return () => {
      mapActionController.setMap(null);
    };
  }, [map]);
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
        duration: 1.4,
        easeLinearity: 0.25,
      });
    }
  }, [flyToTarget, map]);

  return null;
};

// Initial bounds setter
const InitialBoundsSetter: React.FC = () => {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(OCEAN_PARK_1_BOUNDARY, { padding: [30, 30], maxZoom: 15 });
  }, [map]);
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
  onForecastHourChange,
  onSelectStation,
  onSelectPoi,
  onOpenNearMe,
}) => {
  const viewMode = layerConfig.viewMode ?? (layerConfig.showHeatmap ? "heatmap" : "markers");

  return (
    <div className="super-map-wrapper">
      <MapContainer
        center={MAP_CENTER_OCEAN_PARK}
        zoom={15}
        minZoom={13}
        maxZoom={18}
        zoomControl={false}
        className="full-viewport-map"
      >
        <InitialBoundsSetter />
        <MapCameraController flyToTarget={flyToTarget} />
        <MapActionBinder />

        {/* Clean, high-clarity street basemap layer */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        {/* Spatial Dispersion Heatmap Canvas Overlay with dynamic forecastHour */}
        <HeatmapLayer
          activeLayer={layerConfig.activeEnvironmentalLayer}
          showHeatmap={layerConfig.showHeatmap}
          viewMode={viewMode}
          forecastHour={forecastHour}
        />

        {/* Vinhomes Ocean Park 1 Polygon Boundary */}
        <OceanParkBoundary showBoundary={layerConfig.showBoundary} />

        {/* Places & Subdivision Labels */}
        <SubZoneLabels
          onSelectPoi={onSelectPoi}
          showPlaces={layerConfig.showPlaces}
          selectedPoiId={selectedPoi?.id || null}
        />

        {/* Sensor badges always show the grounded current station snapshot with active metric. */}
        <SensorMarkers
          stations={stations}
          selectedStationId={selectedStationId}
          criticalStationIds={criticalStationIds}
          onSelectStation={onSelectStation}
          showSensors={layerConfig.showSensors && viewMode !== "heatmap"}
          activeMetric={layerConfig.activeEnvironmentalLayer}
        />

        {/* Resident Location Pin ("You") */}
        <UserLocationMarker onClick={onOpenNearMe} />
      </MapContainer>

      {/* Accessible Map Legend Overlay (Bottom Right — Only in markers view mode when heatmap is NOT active) */}
      {viewMode === "markers" && !layerConfig.showHeatmap && (
        <div className="map-legend-overlay">
          <AqiLegend showStationStatus={true} metric={layerConfig.activeEnvironmentalLayer} />
        </div>
      )}

      {/* Floating Map Forecast Timeline Control Dock (Bottom Center) */}
      {onForecastHourChange && viewMode === "heatmap" && (
        <div className="map-timeline-floating-dock">
          <TimelineSlider
            value={forecastHour}
            onChange={onForecastHourChange}
            label="Thanh trượt dự báo lan truyền"
          />
        </div>
      )}
    </div>
  );
};

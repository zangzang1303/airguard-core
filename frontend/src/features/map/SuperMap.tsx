import React, { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Station } from "../../types";
import { MapLayerConfig, PlacePOI, AiMapHighlightArea, RouteOption } from "../../types/superApp";
import { MAP_CENTER_OCEAN_PARK, OCEAN_PARK_1_BOUNDARY } from "./poiData";
import { OceanParkBoundary } from "./OceanParkBoundary";
import { SensorMarkers } from "./SensorMarkers";
import { UserLocationMarker } from "./UserLocationMarker";
import { SubZoneLabels } from "./SubZoneLabels";
import { EnvironmentalHeatmapLayer } from "./EnvironmentalHeatmapLayer";
import { AiMapHighlights } from "./AiMapHighlights";

interface SuperMapProps {
  stations: Station[];
  selectedStationId: string | null;
  selectedPoi: PlacePOI | null;
  layerConfig: MapLayerConfig;
  flyToTarget: [number, number] | null;
  aiHighlights: AiMapHighlightArea[];
  activeRoute: RouteOption | null;
  forecastMultiplier: number;
  onSelectStation: (stationId: string) => void;
  onSelectPoi: (poi: PlacePOI) => void;
  onOpenNearMe: () => void;
}

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
  selectedPoi,
  layerConfig,
  flyToTarget,
  aiHighlights,
  activeRoute,
  forecastMultiplier,
  onSelectStation,
  onSelectPoi,
  onOpenNearMe,
}) => {
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

        {/* Clean, high-clarity street basemap layer */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        {/* Environmental Dispersion Heatmap Overlay */}
        <EnvironmentalHeatmapLayer
          stations={stations}
          activeLayer={layerConfig.activeEnvironmentalLayer}
          showHeatmap={layerConfig.showHeatmap}
          forecastMultiplier={forecastMultiplier}
        />

        {/* Vinhomes Ocean Park 1 Polygon Boundary */}
        <OceanParkBoundary showBoundary={layerConfig.showBoundary} />

        {/* AI Highlight Areas & Routes */}
        <AiMapHighlights highlights={aiHighlights} activeRoute={activeRoute} />

        {/* Places & Subdivision Labels */}
        <SubZoneLabels
          onSelectPoi={onSelectPoi}
          showPlaces={layerConfig.showPlaces}
          selectedPoiId={selectedPoi?.id || null}
        />

        {/* Real-time Sensor Station Badges (Numeric AQI) */}
        <SensorMarkers
          stations={stations}
          selectedStationId={selectedStationId}
          onSelectStation={onSelectStation}
          showSensors={layerConfig.showSensors}
        />

        {/* Resident Location Pin ("You") */}
        <UserLocationMarker onClick={onOpenNearMe} />
      </MapContainer>
    </div>
  );
};

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

        {/* Sensor badges always show the grounded current station snapshot. */}
        <SensorMarkers
          stations={stations}
          selectedStationId={selectedStationId}
          criticalStationIds={criticalStationIds}
          onSelectStation={onSelectStation}
          showSensors={layerConfig.showSensors && viewMode !== "heatmap"}
        />

        {/* Resident Location Pin ("You") */}
        <UserLocationMarker onClick={onOpenNearMe} />
      </MapContainer>

      {/* Accessible Map Legend Overlay (Bottom Right — Only in markers view mode) */}
      {viewMode === "markers" && (
        <div
          className="map-legend-overlay"
          aria-label="Chú giải chỉ số AQI và Trạng thái dữ liệu trạm"
          style={{
            position: "absolute",
            bottom: "84px",
            right: "16px",
            zIndex: 10,
            background: "rgba(255, 255, 255, 0.94)",
            backdropFilter: "blur(8px)",
            padding: "10px 14px",
            borderRadius: "12px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
            border: "1px solid rgba(226, 234, 230, 0.8)",
            fontSize: "0.78rem",
            maxWidth: "280px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          <div style={{ fontWeight: 700, fontSize: "0.8rem", color: "#1e293b", borderBottom: "1px solid #e2e8f0", paddingBottom: "4px" }}>
            Chú giải AQI & Trạng thái trạm
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 8px" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
              <span>Tốt (0–50)</span>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#eab308", display: "inline-block" }} />
              <span>T.Bình (51–100)</span>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#f97316", display: "inline-block" }} />
              <span>Nhạy cảm (101+)</span>
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ef4444", display: "inline-block" }} />
              <span>Xấu (151–200)</span>
            </span>
          </div>
          <div style={{ borderTop: "1px dashed #cbd5e1", paddingTop: "6px", display: "flex", flexWrap: "wrap", gap: "6px 10px" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ fontWeight: 700, color: "#10b981" }}>●</span> Online
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ fontWeight: 700, color: "#f59e0b" }}>▲</span> Stale (Dữ liệu cũ)
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ fontWeight: 700, color: "#ef4444" }}>✖</span> Offline
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ fontWeight: 700, color: "#64748b" }}>?</span> Invalid
            </span>
          </div>
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

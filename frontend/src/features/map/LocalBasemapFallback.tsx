import React from "react";
import { CircleMarker, Pane, Polygon } from "react-leaflet";
import { OCEAN_PARK_1_BOUNDARY, OCEAN_PARK_POIS } from "./poiData";

// A small repository-owned geographic context layer. It is deliberately
// schematic (not a street map) and remains underneath OSM tiles, so missing
// network tiles expose useful full-area context instead of blank squares.
export const LocalBasemapFallback: React.FC = () => (
  <Pane name="local-basemap-fallback" style={{ zIndex: 150, pointerEvents: "none" }}>
    <Polygon
      positions={OCEAN_PARK_1_BOUNDARY}
      pathOptions={{
        color: "#9bb8aa",
        weight: 1.5,
        fillColor: "#e8f0eb",
        fillOpacity: 1,
        interactive: false,
      }}
    />
    {OCEAN_PARK_POIS.slice(0, 10).map((poi) => (
      <CircleMarker
        key={poi.id}
        center={[poi.latitude, poi.longitude]}
        radius={3}
        pathOptions={{ color: "#789587", fillColor: "#ffffff", fillOpacity: 1, weight: 1, interactive: false }}
      />
    ))}
  </Pane>
);

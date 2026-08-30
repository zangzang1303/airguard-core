import React from "react";
import { CircleMarker, Pane, Polygon, Polyline } from "react-leaflet";
import { OCEAN_PARK_1_BOUNDARY, OCEAN_PARK_POIS } from "./poiData";

// A small repository-owned geographic context layer. It is deliberately
// schematic (not a street map) and remains underneath OSM tiles, so missing
// network tiles expose useful full-area context instead of blank squares.
const LOCAL_CONTEXT_LINES: [number, number][][] = [
  [[20.9999, 105.9382], [20.9974, 105.9436], [20.9949, 105.9498], [20.9932, 105.9579]],
  [[20.9864, 105.9462], [20.9902, 105.9471], [20.9949, 105.9498], [21.0005, 105.9440]],
  [[20.9890, 105.9412], [20.9928, 105.9460], [20.9958, 105.9512], [20.9969, 105.9572]],
  [[20.9872, 105.9500], [20.9913, 105.9534], [20.9941, 105.9588]],
];

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
    {LOCAL_CONTEXT_LINES.map((positions, index) => (
      <Polyline
        key={`local-context-${index}`}
        positions={positions}
        pathOptions={{ color: "#b7c7bf", weight: index === 0 ? 5 : 3, opacity: 0.95, interactive: false }}
      />
    ))}
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

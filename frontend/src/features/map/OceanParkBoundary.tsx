import React from "react";
import { Pane, Polygon } from "react-leaflet";
import { OCEAN_PARK_1_BOUNDARY, MAP_OUTER_MASK } from "./poiData";

interface OceanParkBoundaryProps {
  showBoundary: boolean;
}

export const OceanParkBoundary: React.FC<OceanParkBoundaryProps> = ({ showBoundary }) => {
  if (!showBoundary) return null;

  return (
    <Pane
      name="ocean-park-boundary"
      style={{ zIndex: 360, pointerEvents: "none" }}
    >
      {/* Outer Geographic Context Mask (soft bright white wash outside boundary to fade out external areas) */}
      <Polygon
        positions={[MAP_OUTER_MASK, [...OCEAN_PARK_1_BOUNDARY].reverse()]}
        pathOptions={{
          color: "transparent",
          fillColor: "#ffffff",
          fillOpacity: 0.72,
          fillRule: "evenodd",
          interactive: false,
        }}
      />

      {/* Vinhomes Ocean Park 1 Zone Highlight: Crisp Emerald Border */}
      <Polygon
        positions={OCEAN_PARK_1_BOUNDARY}
        pathOptions={{
          color: "#059669",
          weight: 2.5,
          dashArray: "6 4",
          fillColor: "rgba(16, 185, 129, 0.04)",
          fillOpacity: 1,
          interactive: false,
        }}
      />
    </Pane>
  );
};

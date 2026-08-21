import React from "react";
import { Polygon, Tooltip } from "react-leaflet";
import { OCEAN_PARK_1_BOUNDARY, MAP_OUTER_MASK } from "./poiData";

interface OceanParkBoundaryProps {
  showBoundary: boolean;
}

export const OceanParkBoundary: React.FC<OceanParkBoundaryProps> = ({ showBoundary }) => {
  if (!showBoundary) return null;

  return (
    <>
      {/* Outer Geographic Context Mask (soft muted overlay outside boundary) */}
      <Polygon
        positions={[MAP_OUTER_MASK, [...OCEAN_PARK_1_BOUNDARY].reverse()]}
        pathOptions={{
          color: "transparent",
          fillColor: "#1e293b",
          fillOpacity: 0.16,
          fillRule: "evenodd",
          interactive: false,
        }}
      />

      {/* Vinhomes Ocean Park 1 Zone Highlight: Mint Tint + Emerald Border */}
      <Polygon
        positions={OCEAN_PARK_1_BOUNDARY}
        pathOptions={{
          color: "#20A77A",
          weight: 2.5,
          dashArray: "8 5",
          fillColor: "rgba(28, 170, 125, 0.09)",
          fillOpacity: 1,
          interactive: false,
        }}
      />
    </>
  );
};

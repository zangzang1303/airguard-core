import React from "react";
import { Circle, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { USER_DEFAULT_LOCATION } from "./poiData";

interface UserLocationMarkerProps {
  onClick: () => void;
  userCoords?: [number, number];
}

// Custom Leaflet icon for Google Maps-style teal dot with pulsing glow
const userPinIcon = L.divIcon({
  className: "user-location-pin",
  html: `
    <div class="user-pin-wrapper">
      <div class="user-pin-pulse"></div>
      <div class="user-pin-core"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

export const UserLocationMarker: React.FC<UserLocationMarkerProps> = ({
  onClick,
  userCoords = USER_DEFAULT_LOCATION,
}) => {
  return (
    <>
      {/* Accuracy Radius Circle */}
      <Circle
        center={userCoords}
        radius={120}
        pathOptions={{
          color: "#0d9488",
          weight: 1.5,
          fillColor: "#14b8a6",
          fillOpacity: 0.12,
        }}
      />

      {/* User Core Marker */}
      <Marker
        position={userCoords}
        icon={userPinIcon}
        eventHandlers={{
          click: onClick,
        }}
      >
        <Tooltip direction="top" offset={[0, -14]} opacity={1} permanent={false}>
          <div className="user-tooltip">
            <strong>📍 Vị trí của bạn (You)</strong>
            <span className="tooltip-sub">Chạm để xem không khí & lời khuyên</span>
          </div>
        </Tooltip>
      </Marker>
    </>
  );
};

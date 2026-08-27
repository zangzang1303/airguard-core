import React, { useMemo } from "react";
import { Circle, Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { USER_DEFAULT_LOCATION } from "./poiData";

export interface UserLocationMarkerProps {
  onClick: () => void;
  userCoords?: [number, number];
  accuracyMeters?: number | null;
  locationName?: string;
  source?: "gps" | "search" | "manual_click" | "default";
  onLocationChange?: (newCoords: [number, number], source: "manual_click") => void;
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
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

export const UserLocationMarker: React.FC<UserLocationMarkerProps> = ({
  onClick,
  userCoords = USER_DEFAULT_LOCATION,
  accuracyMeters,
  locationName = "Vị trí của bạn",
  source = "default",
  onLocationChange,
}) => {
  const eventHandlers = useMemo(
    () => ({
      click: onClick,
      dragend(e: L.LeafletEvent) {
        const marker = e.target as L.Marker;
        if (marker && onLocationChange) {
          const latLng = marker.getLatLng();
          onLocationChange([latLng.lat, latLng.lng], "manual_click");
        }
      },
    }),
    [onClick, onLocationChange]
  );

  const sourceLabel = useMemo(() => {
    switch (source) {
      case "gps":
        return "🛰️ Định vị GPS";
      case "search":
        return "🔍 Đặt từ tìm kiếm";
      case "manual_click":
        return "📌 Chọn trên bản đồ";
      default:
        return "📍 Mặc định Ocean Park";
    }
  }, [source]);

  const circleRadius = accuracyMeters && accuracyMeters > 20 ? Math.min(accuracyMeters, 500) : 120;

  return (
    <>
      {/* Accuracy Radius Circle */}
      <Circle
        center={userCoords}
        radius={circleRadius}
        pathOptions={{
          color: "#0d9488",
          weight: 1.5,
          fillColor: "#14b8a6",
          fillOpacity: 0.12,
        }}
      />

      {/* User Core Marker - Draggable for quick positioning */}
      <Marker
        position={userCoords}
        icon={userPinIcon}
        draggable={Boolean(onLocationChange)}
        eventHandlers={eventHandlers}
      >
        <Tooltip direction="top" offset={[0, -16]} opacity={1} permanent={false}>
          <div className="user-tooltip">
            <div className="user-tooltip-header">
              <strong>📍 Vị trí của bạn (You)</strong>
              <span className="user-tooltip-badge">{sourceLabel}</span>
            </div>
            <div className="user-tooltip-name">{locationName}</div>
            <div className="user-tooltip-coords">
              {userCoords[0].toFixed(5)}, {userCoords[1].toFixed(5)}
            </div>
            <span className="tooltip-sub">
              💡 Chạm xem không khí gần bạn • Kéo thả để đổi vị trí
            </span>
          </div>
        </Tooltip>
      </Marker>
    </>
  );
};

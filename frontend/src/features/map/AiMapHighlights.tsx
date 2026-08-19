import React from "react";
import { Circle, Polyline, Tooltip, Marker } from "react-leaflet";
import L from "leaflet";
import { AiMapHighlightArea, RouteOption } from "../../types/superApp";

interface AiMapHighlightsProps {
  highlights: AiMapHighlightArea[];
  activeRoute: RouteOption | null;
  onClearHighlights?: () => void;
}

const aiPinIcon = (color: string) =>
  L.divIcon({
    className: "ai-highlight-pin",
    html: `
      <div class="ai-pin-glow" style="--pin-color: ${color}">
        <span class="ai-pin-star">✨</span>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });

export const AiMapHighlights: React.FC<AiMapHighlightsProps> = ({
  highlights,
  activeRoute,
}) => {
  return (
    <>
      {/* AI Suggested Areas */}
      {highlights.map((area) => (
        <React.Fragment key={`ai-hl-${area.id}`}>
          <Circle
            center={[area.latitude, area.longitude]}
            radius={area.radius}
            pathOptions={{
              color: area.color,
              weight: 2.5,
              dashArray: "6 4",
              fillColor: area.color,
              fillOpacity: 0.18,
            }}
          />
          <Marker position={[area.latitude, area.longitude]} icon={aiPinIcon(area.color)}>
            <Tooltip direction="top" offset={[0, -14]} opacity={1} permanent={true}>
              <div className="ai-highlight-tooltip">
                <div className="ai-hl-tag">✨ Gợi ý từ AI</div>
                <div className="ai-hl-name">{area.name}</div>
                <div className="ai-hl-desc">{area.label}</div>
              </div>
            </Tooltip>
          </Marker>
        </React.Fragment>
      ))}

      {/* AI Recommended Walking Route */}
      {activeRoute && (
        <>
          <Polyline
            positions={activeRoute.waypoints}
            pathOptions={{
              color: "#10b981",
              weight: 5,
              opacity: 0.85,
              lineCap: "round",
            }}
          >
            <Tooltip direction="center" offset={[0, 0]} opacity={1} permanent={true}>
              <div className="route-tooltip">
                <strong>🌿 Tuyến đường không khí sạch</strong>
                <span>{activeRoute.durationMinutes} phút · {activeRoute.pollutionExposurePercent}% phơi nhiễm bụi</span>
              </div>
            </Tooltip>
          </Polyline>
        </>
      )}
    </>
  );
};

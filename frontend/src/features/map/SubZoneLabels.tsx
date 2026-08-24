import React from "react";
import { Marker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { OCEAN_PARK_POIS } from "./poiData";
import { PlacePOI } from "../../types/superApp";

interface SubZoneLabelsProps {
  onSelectPoi: (poi: PlacePOI) => void;
  showPlaces: boolean;
  selectedPoiId: string | null;
}

/**
 * Creates lightweight, muted POI marker icon.
 * Features:
 * - Smaller size (22x22px) compared to sensor station pins (40x48px)
 * - Neutral soft pastel/gray styling to avoid competing with sensor markers
 * - Clear category emoji
 */
function createPoiIcon(category: string, isSelected: boolean): L.DivIcon {
  const isSelectedClass = isSelected ? "poi-icon-selected" : "";
  let iconEmoji = "📍";
  if (category === "university") iconEmoji = "🎓";
  if (category === "lake") iconEmoji = "🌊";
  if (category === "park") iconEmoji = "🌳";
  if (category === "mall") iconEmoji = "🛍️";
  if (category === "landmark") iconEmoji = "🏢";
  if (category === "residential") iconEmoji = "🏘️";
  if (category === "gate") iconEmoji = "🚪";

  return L.divIcon({
    className: "custom-poi-marker",
    html: `
      <div class="poi-marker-badge ${isSelectedClass}" role="img" aria-label="Địa danh: ${category}">
        <span class="poi-emoji" aria-hidden="true">${iconEmoji}</span>
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });
}

export const SubZoneLabels: React.FC<SubZoneLabelsProps> = ({
  onSelectPoi,
  showPlaces,
  selectedPoiId,
}) => {
  if (!showPlaces) return null;

  return (
    <>
      {OCEAN_PARK_POIS.map((poi) => {
        const isSelected = selectedPoiId === poi.id;
        const icon = createPoiIcon(poi.category, isSelected);

        return (
          <Marker
            key={poi.id}
            position={[poi.latitude, poi.longitude]}
            icon={icon}
            aria-label={`Địa danh ${poi.name}, ${poi.subdivision || ""}`}
            eventHandlers={{
              click: () => onSelectPoi(poi),
            }}
          >
            <Tooltip direction="bottom" offset={[0, 8]} opacity={0.92} permanent={false}>
              <div className="poi-tooltip">
                <div className="poi-category-tag">Địa danh · {poi.category}</div>
                <div className="poi-title">{poi.name}</div>
                {poi.subdivision && <div className="poi-sub">{poi.subdivision}</div>}
              </div>
            </Tooltip>
          </Marker>
        );
      })}
    </>
  );
};

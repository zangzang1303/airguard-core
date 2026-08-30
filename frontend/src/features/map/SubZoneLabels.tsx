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
  if (category === "gym" || category === "indoor_fitness") iconEmoji = "🏋️";
  if (category === "pool") iconEmoji = "🏊";
  if (category === "bus") iconEmoji = "🚌";
  if (category === "bike") iconEmoji = "🚲";

  return L.divIcon({
    className: "custom-poi-marker",
    html: `
      <div class="poi-marker-badge poi-cat-${category} ${isSelectedClass}" role="img" aria-label="Địa danh: ${category}">
        <span class="poi-emoji" aria-hidden="true">${iconEmoji}</span>
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [13, 13],
  });
}

function getCategoryLabel(category: string): string {
  switch (category) {
    case "university": return "Trường học";
    case "lake": return "Mặt nước / Hồ";
    case "park": return "Công viên / Cây xanh";
    case "mall": return "Trung tâm thương mại";
    case "landmark": return "Biểu tượng / Landmark";
    case "residential": return "Khu dân cư";
    case "gate": return "Cổng chào";
    case "gym":
    case "indoor_fitness": return "Phòng tập trong nhà";
    case "pool": return "Bể bơi";
    case "bus": return "Trạm xe VinBus";
    case "bike": return "Trạm xe đạp công cộng";
    default: return "Địa danh";
  }
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
                <div className="poi-category-tag">{getCategoryLabel(poi.category)}</div>
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

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

function createPoiIcon(category: string, isSelected: boolean) {
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
      <div class="poi-marker-badge ${isSelectedClass}">
        <span class="poi-emoji">${iconEmoji}</span>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
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
            eventHandlers={{
              click: () => onSelectPoi(poi),
            }}
          >
            <Tooltip direction="bottom" offset={[0, 10]} opacity={0.92} permanent={false}>
              <div className="poi-tooltip">
                <div className="poi-title">{poi.name}</div>
                <div className="poi-sub">{poi.subdivision}</div>
              </div>
            </Tooltip>
          </Marker>
        );
      })}
    </>
  );
};

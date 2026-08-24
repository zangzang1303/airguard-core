import React from "react";
import { Locate, LocateFixed, MapPin, RefreshCw, Crosshair, Home } from "lucide-react";

interface MapLocationControlsProps {
  isLocating: boolean;
  isPickingOnMap: boolean;
  onLocateGps: () => void;
  onTogglePickOnMap: () => void;
  onResetDefaultLocation?: () => void;
}

export const MapLocationControls: React.FC<MapLocationControlsProps> = ({
  isLocating,
  isPickingOnMap,
  onLocateGps,
  onTogglePickOnMap,
  onResetDefaultLocation,
}) => {
  return (
    <div className="map-location-controls-floating">
      {/* 1. GPS Locate Me Button */}
      <button
        type="button"
        className={`map-fab-btn ${isLocating ? "is-locating" : ""}`}
        onClick={onLocateGps}
        disabled={isLocating}
        title="Định vị vị trí hiện tại của tôi (GPS)"
        aria-label="Định vị GPS của bạn"
      >
        {isLocating ? (
          <>
            <RefreshCw size={20} className="spin-icon text-primary" />
            <div className="locating-radar-ring" />
          </>
        ) : (
          <LocateFixed size={20} className="text-primary" />
        )}
        <span className="fab-tooltip">Định vị GPS</span>
      </button>

      {/* 2. Pick Location on Map Toggle Button */}
      <button
        type="button"
        className={`map-fab-btn ${isPickingOnMap ? "is-picking-active" : ""}`}
        onClick={onTogglePickOnMap}
        title={isPickingOnMap ? "Hủy chế độ chọn vị trí" : "Chấm chọn vị trí trực tiếp trên bản đồ"}
        aria-label="Chọn vị trí trên bản đồ"
      >
        {isPickingOnMap ? (
          <Crosshair size={20} className="text-emerald" />
        ) : (
          <MapPin size={20} />
        )}
        <span className="fab-tooltip">
          {isPickingOnMap ? "Đang chọn trên map" : "Chọn điểm trên map"}
        </span>
      </button>

      {/* 3. Reset to Ocean Park Default Center */}
      {onResetDefaultLocation && (
        <button
          type="button"
          className="map-fab-btn reset-btn"
          onClick={onResetDefaultLocation}
          title="Về vị trí trung tâm Ocean Park 1"
          aria-label="Về trung tâm Ocean Park 1"
        >
          <Home size={18} />
          <span className="fab-tooltip">Về Ocean Park</span>
        </button>
      )}
    </div>
  );
};

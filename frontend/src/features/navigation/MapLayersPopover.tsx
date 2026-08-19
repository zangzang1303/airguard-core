import React from "react";
import { Check, Layers, Eye, Wind, Activity, Thermometer, Volume2, Droplets, MapPin, Radio } from "lucide-react";
import { MapLayerConfig, EnvironmentalLayerType } from "../../types/superApp";

interface MapLayersPopoverProps {
  config: MapLayerConfig;
  onChangeConfig: (newConfig: MapLayerConfig) => void;
  onClose: () => void;
}

export const MapLayersPopover: React.FC<MapLayersPopoverProps> = ({
  config,
  onChangeConfig,
  onClose,
}) => {
  const setEnvLayer = (layer: EnvironmentalLayerType) => {
    onChangeConfig({ ...config, activeEnvironmentalLayer: layer });
  };

  const toggleFeature = (key: keyof MapLayerConfig) => {
    onChangeConfig({ ...config, [key]: !config[key] });
  };

  return (
    <div className="map-layers-popover-card">
      <div className="popover-header">
        <div className="header-title">
          <Layers size={16} className="title-icon" />
          <span>Lớp hiển thị bản đồ</span>
        </div>
      </div>

      {/* Environmental Metrics Section */}
      <div className="popover-section">
        <div className="section-label">Chỉ số môi trường</div>
        <div className="layer-options-grid">
          <button
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "aqi" ? "active" : ""}`}
            onClick={() => setEnvLayer("aqi")}
          >
            <Activity size={15} />
            <span>Chất lượng KK (AQI)</span>
            {config.activeEnvironmentalLayer === "aqi" && <Check size={14} className="check-icon" />}
          </button>

          <button
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "pm25" ? "active" : ""}`}
            onClick={() => setEnvLayer("pm25")}
          >
            <Wind size={15} />
            <span>Bụi mịn (PM2.5)</span>
            {config.activeEnvironmentalLayer === "pm25" && <Check size={14} className="check-icon" />}
          </button>

          <button
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "co2" ? "active" : ""}`}
            onClick={() => setEnvLayer("co2")}
          >
            <Droplets size={15} />
            <span>Khí CO₂</span>
            {config.activeEnvironmentalLayer === "co2" && <Check size={14} className="check-icon" />}
          </button>

          <button
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "temperature" ? "active" : ""}`}
            onClick={() => setEnvLayer("temperature")}
          >
            <Thermometer size={15} />
            <span>Nhiệt độ (°C)</span>
            {config.activeEnvironmentalLayer === "temperature" && <Check size={14} className="check-icon" />}
          </button>

          <button
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "noise_db" ? "active" : ""}`}
            onClick={() => setEnvLayer("noise_db")}
          >
            <Volume2 size={15} />
            <span>Độ ồn (dB)</span>
            {config.activeEnvironmentalLayer === "noise_db" && <Check size={14} className="check-icon" />}
          </button>
        </div>
      </div>

      {/* Map Elements Toggle Section */}
      <div className="popover-section">
        <div className="section-label">Thành phần bản đồ</div>
        <div className="feature-toggles-list">
          <label className="toggle-item-row" onClick={() => toggleFeature("showHeatmap")}>
            <div className="toggle-label-wrap">
              <Eye size={15} />
              <span>Bản đồ nhiệt lan truyền (Heatmap)</span>
            </div>
            <input type="checkbox" checked={config.showHeatmap} readOnly />
          </label>

          <label className="toggle-item-row" onClick={() => toggleFeature("showBoundary")}>
            <div className="toggle-label-wrap">
              <Layers size={15} />
              <span>Ranh giới Ocean Park 1</span>
            </div>
            <input type="checkbox" checked={config.showBoundary} readOnly />
          </label>

          <label className="toggle-item-row" onClick={() => toggleFeature("showSensors")}>
            <div className="toggle-label-wrap">
              <Radio size={15} />
              <span>Trạm cảm biến quan trắc</span>
            </div>
            <input type="checkbox" checked={config.showSensors} readOnly />
          </label>

          <label className="toggle-item-row" onClick={() => toggleFeature("showPlaces")}>
            <div className="toggle-label-wrap">
              <MapPin size={15} />
              <span>Địa danh & Phân khu</span>
            </div>
            <input type="checkbox" checked={config.showPlaces} readOnly />
          </label>
        </div>
      </div>
    </div>
  );
};

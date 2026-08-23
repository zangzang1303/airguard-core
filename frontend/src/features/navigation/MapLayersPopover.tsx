import React from "react";
import {
  Check,
  Layers,
  Eye,
  Wind,
  Activity,
  Thermometer,
  Volume2,
  Cloud,
  MapPin,
  Radio,
  Wifi,
  ChartNoAxesCombined,
  PanelTop,
  X,
  RotateCcw,
} from "lucide-react";
import { MapLayerConfig, EnvironmentalLayerType, MapViewMode } from "../../types/superApp";
import { useDraggableFloatingPanel, useFloatingPanelContext } from "../floating";

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
  const { containerProps, handleProps } = useDraggableFloatingPanel({
    panelId: "map-layers",
    group: "popover",
  });
  const { resetAllPositions } = useFloatingPanelContext();

  const setEnvLayer = (layer: EnvironmentalLayerType) => {
    onChangeConfig({ ...config, activeEnvironmentalLayer: layer });
  };

  const setViewMode = (mode: MapViewMode) => {
    onChangeConfig({
      ...config,
      viewMode: mode,
      showHeatmap: mode === "heatmap",
    });
  };

  const toggleFeature = (key: keyof MapLayerConfig) => {
    onChangeConfig({ ...config, [key]: !config[key] });
  };

  const currentViewMode: MapViewMode = config.viewMode ?? (config.showHeatmap ? "heatmap" : "markers");

  return (
    <div {...containerProps} className="map-layers-popover-card">
      <div className="popover-header">
        <div className="header-title" {...handleProps}>
          <Layers size={16} className="title-icon" />
          <span>Lớp hiển thị bản đồ</span>
        </div>
        <button
          type="button"
          data-no-drag="true"
          className="no-drag map-layers-close-btn"
          onClick={onClose}
          aria-label="Đóng bảng lớp bản đồ"
          title="Đóng"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </div>

      {/* View Mode Toggle Section */}
      <div className="popover-section no-drag" data-no-drag="true">
        <div className="section-label">Chế độ hiển thị chính</div>
        <div className="layer-options-grid" role="radiogroup" aria-label="Chế độ hiển thị chính">
          <button
            type="button"
            className={`layer-option-btn ${currentViewMode === "markers" ? "active" : ""}`}
            onClick={() => setViewMode("markers")}
            aria-pressed={currentViewMode === "markers"}
          >
            <Radio size={15} />
            <span>Điểm đo Trạm</span>
            {currentViewMode === "markers" && <Check size={14} className="check-icon" />}
          </button>

          <button
            type="button"
            className={`layer-option-btn ${currentViewMode === "heatmap" ? "active" : ""}`}
            onClick={() => setViewMode("heatmap")}
            aria-pressed={currentViewMode === "heatmap"}
          >
            <Eye size={15} />
            <span>Bản đồ nhiệt Lan truyền</span>
            {currentViewMode === "heatmap" && <Check size={14} className="check-icon" />}
          </button>
        </div>
      </div>

      {/* Environmental Metrics Section */}
      <div className="popover-section no-drag" data-no-drag="true">
        <div className="section-label">Chỉ số môi trường</div>
        <div className="layer-options-grid">
          <button
            type="button"
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "aqi" ? "active" : ""}`}
            onClick={() => setEnvLayer("aqi")}
          >
            <Activity size={15} />
            <span>Chất lượng KK (AQI)</span>
            {config.activeEnvironmentalLayer === "aqi" && <Check size={14} className="check-icon" />}
          </button>

          <button
            type="button"
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "pm25" ? "active" : ""}`}
            onClick={() => setEnvLayer("pm25")}
          >
            <Wind size={15} />
            <span>Bụi mịn (PM2.5)</span>
            {config.activeEnvironmentalLayer === "pm25" && <Check size={14} className="check-icon" />}
          </button>

          <button
            type="button"
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "co2" ? "active" : ""}`}
            onClick={() => setEnvLayer("co2")}
          >
            <Cloud size={15} />
            <span>Khí CO₂</span>
            {config.activeEnvironmentalLayer === "co2" && <Check size={14} className="check-icon" />}
          </button>

          <button
            type="button"
            className={`layer-option-btn ${config.activeEnvironmentalLayer === "temperature" ? "active" : ""}`}
            onClick={() => setEnvLayer("temperature")}
          >
            <Thermometer size={15} />
            <span>Nhiệt độ (°C)</span>
            {config.activeEnvironmentalLayer === "temperature" && <Check size={14} className="check-icon" />}
          </button>

          <button
            type="button"
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
      <div className="popover-section no-drag" data-no-drag="true">
        <div className="section-label">Thành phần phụ hỗ trợ</div>
        <div className="feature-toggles-list">
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

          <label className="toggle-item-row" onClick={() => toggleFeature("showConnectionStatus")}>
            <div className="toggle-label-wrap">
              <Wifi size={15} />
              <span>Trạng thái kết nối</span>
            </div>
            <input type="checkbox" checked={config.showConnectionStatus} readOnly />
          </label>

          <label className="toggle-item-row" onClick={() => toggleFeature("showStationOverview")}>
            <div className="toggle-label-wrap">
              <ChartNoAxesCombined size={15} />
              <span>Tổng quan trạng thái trạm</span>
            </div>
            <input type="checkbox" checked={config.showStationOverview} readOnly />
          </label>

          <label className="toggle-item-row" onClick={() => toggleFeature("showDispersionInfo")}>
            <div className="toggle-label-wrap">
              <PanelTop size={15} />
              <span>Thông tin bản đồ lan truyền</span>
            </div>
            <input type="checkbox" checked={config.showDispersionInfo} readOnly />
          </label>
        </div>
      </div>

      {/* Floating Layout Reset Action */}
      <div className="popover-section no-drag" data-no-drag="true" style={{ paddingTop: 8, borderTop: "1px solid var(--border-subtle, #e2e8f0)" }}>
        <button
          type="button"
          onClick={resetAllPositions}
          style={{
            width: "100%",
            padding: "7px 10px",
            border: "1px dashed var(--border-subtle, #cbd5e1)",
            borderRadius: "8px",
            background: "transparent",
            color: "var(--text-muted, #64748b)",
            fontSize: "0.76rem",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
          }}
          title="Khôi phục vị trí mặc định cho tất cả các bảng nổi"
        >
          <RotateCcw size={13} aria-hidden="true" />
          <span>Đặt lại bố cục panel nổi</span>
        </button>
      </div>
    </div>
  );
};

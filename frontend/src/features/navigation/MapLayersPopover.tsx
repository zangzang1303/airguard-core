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
  SlidersHorizontal,
  FlaskConical,
  ShieldAlert,
  X,
  RotateCcw,
  BarChart2,
} from "lucide-react";
import {
  MapLayerConfig,
  MapLayerVisibilityKey,
  EnvironmentalLayerType,
  MapViewMode,
} from "../../types/superApp";
import { useAuth } from "../../context/AuthContext";
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
  const { role, demoMode } = useAuth();
  const isManager = role === "manager" || role === "admin";
  const canUseDemoControl = isManager && Boolean(demoMode);

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

  const toggleFeature = (key: MapLayerVisibilityKey) => {
    onChangeConfig({
      ...config,
      [key]: !config[key],
    });
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

      {/* 1. View Mode Toggle Section */}
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

      {/* 2. Environmental Metrics Section */}
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

      {/* 3. Common Map Elements Toggle Section */}
      <div className="popover-section no-drag" data-no-drag="true">
        <div className="section-label">Thành phần phụ trợ</div>
        <div className="feature-toggles-list">
          {/* Ranh giới */}
          <label className="toggle-item-row" htmlFor="toggle-boundary">
            <div className="toggle-label-wrap">
              <Layers size={15} />
              <span>Ranh giới Ocean Park 1</span>
            </div>
            <input
              id="toggle-boundary"
              type="checkbox"
              checked={config.showBoundary}
              onChange={() => toggleFeature("showBoundary")}
            />
          </label>

          {/* Trạm cảm biến */}
          <label className="toggle-item-row" htmlFor="toggle-sensors">
            <div className="toggle-label-wrap">
              <Radio size={15} />
              <div className="toggle-title-block">
                <span>Trạm cảm biến quan trắc</span>
                {currentViewMode === "heatmap" && (
                  <span className="toggle-helper-note">Chỉ hiển thị ở chế độ Điểm đo Trạm</span>
                )}
              </div>
            </div>
            <input
              id="toggle-sensors"
              type="checkbox"
              checked={config.showSensors}
              onChange={() => toggleFeature("showSensors")}
            />
          </label>

          {/* Địa danh & Phân khu */}
          <label className="toggle-item-row" htmlFor="toggle-places">
            <div className="toggle-label-wrap">
              <MapPin size={15} />
              <span>Địa danh & Phân khu</span>
            </div>
            <input
              id="toggle-places"
              type="checkbox"
              checked={config.showPlaces}
              onChange={() => toggleFeature("showPlaces")}
            />
          </label>

          {/* Trạng thái kết nối */}
          <label className="toggle-item-row" htmlFor="toggle-connection">
            <div className="toggle-label-wrap">
              <Wifi size={15} />
              <span>Trạng thái kết nối</span>
            </div>
            <input
              id="toggle-connection"
              type="checkbox"
              checked={config.showConnectionStatus}
              onChange={() => toggleFeature("showConnectionStatus")}
            />
          </label>

          {/* Tổng quan Chất lượng không khí (Air Quality Now) */}
          <label className="toggle-item-row" htmlFor="toggle-air-quality-now">
            <div className="toggle-label-wrap">
              <Activity size={15} />
              <span>Chất lượng không khí (Air Quality Now)</span>
            </div>
            <input
              id="toggle-air-quality-now"
              type="checkbox"
              checked={config.showAirQualityNow ?? true}
              onChange={() => toggleFeature("showAirQualityNow")}
            />
          </label>

          {/* Chú giải dải màu & Trạng thái (Map Legend) */}
          <label className="toggle-item-row" htmlFor="toggle-map-legend">
            <div className="toggle-label-wrap">
              <BarChart2 size={15} />
              <span>Chú giải bản đồ & Phân cấp (Map Legend)</span>
            </div>
            <input
              id="toggle-map-legend"
              type="checkbox"
              checked={config.showMapLegend ?? true}
              onChange={() => toggleFeature("showMapLegend")}
            />
          </label>

          {/* Thanh trượt dự báo lan truyền */}
          <label className="toggle-item-row" htmlFor="toggle-timeline">
            <div className="toggle-label-wrap">
              <SlidersHorizontal size={15} />
              <div className="toggle-title-block">
                <span>Thanh trượt dự báo lan truyền</span>
                {currentViewMode !== "heatmap" && (
                  <span className="toggle-helper-note">Chỉ áp dụng cho Bản đồ nhiệt</span>
                )}
              </div>
            </div>
            <input
              id="toggle-timeline"
              type="checkbox"
              checked={config.showForecastTimeline ?? true}
              onChange={() => toggleFeature("showForecastTimeline")}
            />
          </label>
        </div>
      </div>

      {/* 4. Manager Tools Section (Rendered exclusively for Manager / Admin) */}
      {isManager && (
        <div className="popover-section no-drag manager-tools-section" data-no-drag="true">
          <div className="section-label manager-section-label">
            <ShieldAlert size={12} className="inline-manager-icon" />
            <span>Công cụ Ban Quản lý</span>
          </div>
          <div className="feature-toggles-list">
            {/* Tổng quan trạng thái trạm */}
            <label className="toggle-item-row" htmlFor="toggle-station-overview">
              <div className="toggle-label-wrap">
                <ChartNoAxesCombined size={15} />
                <span>Tổng quan trạng thái trạm</span>
              </div>
              <input
                id="toggle-station-overview"
                type="checkbox"
                checked={config.showStationOverview}
                onChange={() => toggleFeature("showStationOverview")}
              />
            </label>

            <label className="toggle-item-row" htmlFor="toggle-ventilation-devices">
              <div className="toggle-label-wrap">
                <Wind size={15} />
                <span>Hiển thị thiết bị thông gió</span>
              </div>
              <input
                id="toggle-ventilation-devices"
                type="checkbox"
                checked={config.showVentilationDevices ?? true}
                onChange={() => toggleFeature("showVentilationDevices")}
              />
            </label>

            {/* Điều khiển dữ liệu demo (Chỉ khi demoMode=true) */}
            {canUseDemoControl && (
              <label className="toggle-item-row" htmlFor="toggle-demo-control">
                <div className="toggle-label-wrap">
                  <FlaskConical size={15} />
                  <span>Điều khiển dữ liệu demo</span>
                </div>
                <input
                  id="toggle-demo-control"
                  type="checkbox"
                  checked={config.showDemoControl ?? true}
                  onChange={() => toggleFeature("showDemoControl")}
                />
              </label>
            )}
          </div>
        </div>
      )}

      {/* 5. Floating Layout Reset Action */}
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

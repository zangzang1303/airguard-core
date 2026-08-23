import React, { useEffect, useState, useRef, useMemo } from "react";
import { ImageOverlay, Pane } from "react-leaflet";
import { api } from "../../api/client";
import { SpatialHeatmapResponse } from "../../types";
import { EnvironmentalLayerType, MapViewMode } from "../../types/superApp";
import { AlertTriangle, RefreshCw, Layers, ChevronDown, ChevronUp } from "lucide-react";
import {
  MetricColorScale,
  DispersionMetadata,
  StationStatusLegend,
  SimulationDisclaimer,
  getFriendlyBadgeLabel,
} from "../map/AqiLegend";
import { getMetricScale } from "../../constants/metrics";
import {
  createDispersionOffscreenCanvas,
  OCEAN_PARK_1_EXTENT,
  OCEAN_PARK_1_BOUNDARY,
} from "../../utils/dispersionField";

export interface HeatmapLayerProps {
  activeLayer?: EnvironmentalLayerType;
  forecastHour?: number;
  viewMode?: MapViewMode;
  showHeatmap?: boolean;
}

const DISPERSION_BOUNDS: [[number, number], [number, number]] = [
  [OCEAN_PARK_1_EXTENT.latMin, OCEAN_PARK_1_EXTENT.lonMin],
  [OCEAN_PARK_1_EXTENT.latMax, OCEAN_PARK_1_EXTENT.lonMax],
];

export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({
  activeLayer = "aqi",
  forecastHour = 0,
  viewMode = "heatmap",
  showHeatmap = true,
}) => {
  const [data, setData] = useState<SpatialHeatmapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const activeRequestKeyRef = useRef<string>("");
  const isActive = viewMode === "heatmap" || showHeatmap;

  // Fetch API with AbortController & request key guard
  useEffect(() => {
    if (!isActive) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    const requestKey = `${activeLayer}:${forecastHour}:${reloadToken}`;
    activeRequestKeyRef.current = requestKey;

    const controller = new AbortController();

    setLoading(true);
    setError(null);

    api
      .getSpatialHeatmap(activeLayer, forecastHour, controller.signal)
      .then((res) => {
        if (controller.signal.aborted || activeRequestKeyRef.current !== requestKey) {
          return;
        }
        setData(res);
        setError(null);
      })
      .catch((err) => {
        if (controller.signal.aborted || activeRequestKeyRef.current !== requestKey) {
          return;
        }
        console.warn("Spatial Heatmap API Error:", err?.message);
        setData(null);
        setError(
          err instanceof Error
            ? err.message
            : "Không đủ dữ liệu hợp lệ để tạo bản đồ nhiệt.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted && activeRequestKeyRef.current === requestKey) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [activeLayer, forecastHour, isActive, reloadToken]);

  // Pure Geographic Offscreen Canvas & Data URL Generation
  // Derived strictly from geographic coordinates, stations, and wind — 100% zoom-invariant!
  const overlayDataUrl = useMemo(() => {
    if (!isActive || !data || data.grid_points.length === 0) return null;

    const offscreenCanvas = createDispersionOffscreenCanvas(
      data.grid_points,
      activeLayer,
      120, // 120x120 resolution raster
      120,
      OCEAN_PARK_1_EXTENT,
      OCEAN_PARK_1_BOUNDARY
    );

    return offscreenCanvas.toDataURL();
  }, [data, activeLayer, isActive]);

  if (!isActive) return null;

  const currentMetricScale = getMetricScale(activeLayer);

  return (
    <>
      {/* 1. Leaflet Native Image Overlay (100% Zoom-Invariant & Hardware Accelerated) */}
      {overlayDataUrl && (
        <Pane
          name="environmental-dispersion"
          style={{ zIndex: 350, pointerEvents: "none" }}
        >
          <ImageOverlay
            url={overlayDataUrl}
            bounds={DISPERSION_BOUNDS}
            opacity={0.78}
          />
        </Pane>
      )}

      {/* 2. Unified Metric Overlay Panel */}
      <div className="spatial-heatmap-metadata-card unified-aqi-panel">
        <div className="unified-panel-header">
          <div className="header-title-wrap">
            <Layers size={16} className="header-icon" />
            <span>Bản đồ lan truyền {currentMetricScale.label}</span>
          </div>
          <div className="header-badge-group">
            <span className={`header-badge ${forecastHour > 0 ? "badge-forecast" : ""}`}>
              {getFriendlyBadgeLabel(data?.model_version || data?.source, forecastHour)}
            </span>
            <button
              type="button"
              className="panel-collapse-btn"
              onClick={() => setIsCollapsed(!isCollapsed)}
              title={isCollapsed ? "Mở rộng panel" : "Thu gọn panel"}
              aria-label={isCollapsed ? "Mở rộng panel" : "Thu gọn panel"}
            >
              {isCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </button>
          </div>
        </div>

        {!isCollapsed && (
          <>
            {loading && (
              <div className="unified-loading" style={{ display: "flex", alignItems: "center", gap: "8px", color: "#0284c7", padding: "4px 0" }}>
                <RefreshCw size={14} className="spin-icon" />
                <span>Đang tải dữ liệu lan truyền {currentMetricScale.label}...</span>
              </div>
            )}

            {error && (
              <div className="unified-error" style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", padding: "8px 10px", borderRadius: "8px" }} role="alert">
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                  <AlertTriangle size={15} />
                  <strong>Không thể hiển thị Heatmap</strong>
                </div>
                <p style={{ margin: 0, fontSize: "0.72rem" }}>{error}</p>
                <button
                  type="button"
                  onClick={() => setReloadToken((t) => t + 1)}
                  style={{ marginTop: "6px", background: "#dc2626", color: "#fff", border: "none", borderRadius: "4px", padding: "3px 8px", fontSize: "0.7rem", cursor: "pointer" }}
                >
                  <RefreshCw size={12} /> Thử lại
                </button>
              </div>
            )}

            {!loading && !error && (
              <>
                <MetricColorScale metric={activeLayer} />
                <DispersionMetadata data={data} forecastHour={forecastHour} />
                <StationStatusLegend />
                <SimulationDisclaimer text="Dữ liệu mô phỏng cho MVP · Không phải quan trắc chính thức." />
              </>
            )}
          </>
        )}
      </div>
    </>
  );
};

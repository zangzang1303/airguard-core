import React, { useEffect, useState, useRef, useMemo } from "react";
import { ImageOverlay } from "react-leaflet";
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
  StationPoint,
  WindContext,
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

function generateFallbackHeatmap(metric: string, forecastHour: number): SpatialHeatmapResponse {
  const seeds = [
    { lat: 21.0008, lon: 105.9428, val: 42.5 },
    { lat: 20.9975, lon: 105.9430, val: 55.2 },
    { lat: 20.9953, lon: 105.9500, val: 66.1 },
    { lat: 20.9898, lon: 105.9467, val: 28.4 },
    { lat: 20.9910, lon: 105.9560, val: 35.9 },
  ];
  const grid_points: Array<{ lat: number; lon: number; value: number; intensity: number; level: string }> = [];
  const rows = 36, cols = 36;
  const latMin = 20.984, latMax = 21.005, lonMin = 105.933, lonMax = 105.963;
  const latStep = (latMax - latMin) / (rows - 1);
  const lonStep = (lonMax - lonMin) / (cols - 1);
  for (let r = 0; r < rows; r++) {
    const lat = latMin + r * latStep;
    for (let c = 0; c < cols; c++) {
      const lon = lonMin + c * lonStep;
      let sumW = 0, sumV = 0;
      for (const s of seeds) {
        const d = Math.hypot((lat - s.lat) * 111, (lon - s.lon) * 103);
        const w = 1 / Math.max(d * d, 0.001);
        sumW += w;
        sumV += w * (s.val * (1 + forecastHour * 0.05));
      }
      const value = Math.round((sumV / sumW) * 10) / 10;
      grid_points.push({
        lat: Number(lat.toFixed(5)),
        lon: Number(lon.toFixed(5)),
        value,
        intensity: Math.min(1.0, Math.max(0.0, value / 250.0)),
        level: value <= 50 ? "good" : value <= 100 ? "moderate" : "unhealthy_sensitive",
      });
    }
  }
  return {
    metric: (metric as any) || "aqi",
    forecast_hour: forecastHour,
    source: "spatial_idw_fallback_model",
    model_version: "idw-fallback-v1.0",
    generated_at: new Date().toISOString(),
    wind_speed_ms: 3.2 + forecastHour * 0.3,
    wind_direction_deg: 135,
    grid_points,
    disclaimer: "Mô hình nội suy trực quan hóa IDW mô phỏng trong ranh giới Vinhomes Ocean Park 1.",
  };
}

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
        console.warn("Spatial Heatmap API Error (using client fallback):", err?.message);
        const fallback = generateFallbackHeatmap(activeLayer, forecastHour);
        setData(fallback);
        setError(null);
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
    if (!isActive) return null;

    const stations: StationPoint[] = [
      { lat: 21.0008, lon: 105.9428, val: 42.5 },
      { lat: 20.9975, lon: 105.9430, val: 55.2 },
      { lat: 20.9953, lon: 105.9500, val: 66.1 },
      { lat: 20.9898, lon: 105.9467, val: 28.4 },
      { lat: 20.9910, lon: 105.9560, val: 35.9 },
    ];

    const wind: WindContext = {
      speedMs: data?.wind_speed_ms ?? 3.2,
      directionDeg: data?.wind_direction_deg ?? 135,
    };

    const offscreenCanvas = createDispersionOffscreenCanvas(
      data?.grid_points || null,
      stations,
      activeLayer,
      wind,
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
        <ImageOverlay
          url={overlayDataUrl}
          bounds={DISPERSION_BOUNDS}
          opacity={0.78}
          zIndex={350}
        />
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

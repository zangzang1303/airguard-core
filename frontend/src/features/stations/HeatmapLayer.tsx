import React, { useEffect, useState, useRef, useMemo } from "react";
import { ImageOverlay, Pane } from "react-leaflet";
import { api } from "../../api/client";
import { SpatialHeatmapResponse } from "../../types";
import { EnvironmentalLayerType, MapViewMode } from "../../types/superApp";
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
  refreshRevision?: number;
  onDataChange?: (
    data: SpatialHeatmapResponse | null,
    loading: boolean,
    error: string | null
  ) => void;
  onRetryRef?: React.MutableRefObject<(() => void) | null>;
}

const DISPERSION_BOUNDS: [[number, number], [number, number]] = [
  [OCEAN_PARK_1_EXTENT.latMin, OCEAN_PARK_1_EXTENT.lonMin],
  [OCEAN_PARK_1_EXTENT.latMax, OCEAN_PARK_1_EXTENT.lonMax],
];

/**
 * Pure Spatial Heatmap Layer for Leaflet Map
 * Focuses exclusively on raster generation and ImageOverlay rendering.
 * Does not own any redundant legend UI panels.
 */
export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({
  activeLayer = "aqi",
  forecastHour = 0,
  viewMode = "heatmap",
  showHeatmap = true,
  refreshRevision = 0,
  onDataChange,
  onRetryRef,
}) => {
  const [data, setData] = useState<SpatialHeatmapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const activeRequestKeyRef = useRef<string>("");
  const isActive = viewMode === "heatmap" || showHeatmap;

  // Expose retry trigger to parent if needed
  useEffect(() => {
    if (onRetryRef) {
      onRetryRef.current = () => setReloadToken((t) => t + 1);
    }
  }, [onRetryRef]);

  // Synchronize state changes to parent callback
  useEffect(() => {
    if (onDataChange) {
      onDataChange(data, loading, error);
    }
  }, [data, loading, error, onDataChange]);

  // Fetch API with AbortController & request key guard
  useEffect(() => {
    if (!isActive) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    const requestKey = `${activeLayer}:${forecastHour}:${refreshRevision}:${reloadToken}`;
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
  }, [activeLayer, forecastHour, isActive, refreshRevision, reloadToken]);

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
  if (loading && !overlayDataUrl) {
    return (
      <div className="heatmap-update-status" role="status" aria-live="polite">
        Đang cập nhật mô hình…
      </div>
    );
  }
  if (!overlayDataUrl) return null;

  return (
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
  );
};

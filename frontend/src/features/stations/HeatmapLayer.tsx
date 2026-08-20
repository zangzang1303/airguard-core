import React, { useEffect, useState, useRef, useMemo } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import { api } from "../../api/client";
import { SpatialHeatmapResponse, SpatialHeatmapPoint } from "../../types";
import { EnvironmentalLayerType, MapViewMode } from "../../types/superApp";
import { formatVnDateTime } from "../../utils/datetime";
import { AlertTriangle, RefreshCw, Wind, Compass, Layers, Info, Clock, Cpu } from "lucide-react";

export interface HeatmapLayerProps {
  activeLayer?: EnvironmentalLayerType;
  forecastHour?: number;
  viewMode?: MapViewMode;
  showHeatmap?: boolean;
}

// AQI / PM2.5 intensity gradients for leaflet.heat (0.0 -> 1.0)
const AQI_HEAT_GRADIENT: Record<number, string> = {
  0.15: "#10b981",
  0.35: "#eab308",
  0.55: "#f97316",
  0.75: "#ef4444",
  1.00: "#8b5cf6",
};

const METRIC_HEAT_GRADIENTS: Record<EnvironmentalLayerType, Record<number, string>> = {
  aqi: AQI_HEAT_GRADIENT,
  pm25: AQI_HEAT_GRADIENT,
  co2: {
    0.2: "#10b981",
    0.5: "#eab308",
    0.8: "#f97316",
    1.0: "#ef4444",
  },
  temperature: {
    0.2: "#38bdf8",
    0.5: "#10b981",
    0.8: "#f97316",
    1.0: "#ef4444",
  },
  noise_db: {
    0.25: "#10b981",
    0.55: "#eab308",
    0.8: "#f97316",
    1.0: "#ef4444",
  },
  humidity: {
    0.3: "#38bdf8",
    0.7: "#0284c7",
    1.0: "#1d4ed8",
  },
};

const METRIC_LEGEND_CONFIGS: Record<
  EnvironmentalLayerType,
  {
    title: string;
    isAqiBased: boolean;
    items: Array<{ color: string; label: string; range?: string }>;
    note?: string;
  }
> = {
  aqi: {
    title: "AQI (Chất lượng không khí)",
    isAqiBased: true,
    items: [
      { color: "#10b981", label: "Tốt", range: "0–50" },
      { color: "#eab308", label: "Trung bình", range: "51–100" },
      { color: "#f97316", label: "Kém (nhạy cảm)", range: "101–150" },
      { color: "#ef4444", label: "Xấu", range: "151–200" },
      { color: "#8b5cf6", label: "Rất xấu", range: "201–300" },
    ],
  },
  pm25: {
    title: "Bụi mịn PM2.5 (µg/m³)",
    isAqiBased: true,
    items: [
      { color: "#10b981", label: "Tốt", range: "0–12" },
      { color: "#eab308", label: "Trung bình", range: "12.1–35.4" },
      { color: "#f97316", label: "Kém (nhạy cảm)", range: "35.5–55.4" },
      { color: "#ef4444", label: "Xấu", range: "55.5–150.4" },
      { color: "#8b5cf6", label: "Rất xấu", range: "150.5+" },
    ],
  },
  co2: {
    title: "Nồng độ Khí CO₂",
    isAqiBased: false,
    items: [
      { color: "#10b981", label: "Thấp" },
      { color: "#eab308", label: "Trung bình" },
      { color: "#f97316", label: "Cao" },
      { color: "#ef4444", label: "Rất cao" },
    ],
    note: "Cường độ tương đối của lớp nội suy không gian (không phải ngưỡng AQI).",
  },
  temperature: {
    title: "Nhiệt độ môi trường",
    isAqiBased: false,
    items: [
      { color: "#38bdf8", label: "Mát" },
      { color: "#10b981", label: "Vừa" },
      { color: "#f97316", label: "Ấm" },
      { color: "#ef4444", label: "Nóng" },
    ],
    note: "Cường độ tương đối của lớp nội suy không gian (không phải ngưỡng AQI).",
  },
  noise_db: {
    title: "Độ ồn môi trường",
    isAqiBased: false,
    items: [
      { color: "#10b981", label: "Yên tĩnh" },
      { color: "#eab308", label: "Vừa" },
      { color: "#f97316", label: "Ồn" },
      { color: "#ef4444", label: "Rất ồn" },
    ],
    note: "Cường độ tương đối của lớp nội suy không gian (không phải ngưỡng AQI).",
  },
  humidity: {
    title: "Độ ẩm không khí",
    isAqiBased: false,
    items: [
      { color: "#38bdf8", label: "Khô" },
      { color: "#0284c7", label: "Vừa" },
      { color: "#1d4ed8", label: "Ẩm cao" },
    ],
    note: "Cường độ tương đối của lớp nội suy không gian (không phải ngưỡng AQI).",
  },
};

function generateFallbackHeatmap(metric: string, forecastHour: number): SpatialHeatmapResponse {
  const seeds = [
    { lat: 21.0008, lon: 105.9428, val: 42.5 },
    { lat: 20.9975, lon: 105.9430, val: 55.2 },
    { lat: 20.9953, lon: 105.9500, val: 66.1 },
    { lat: 20.9898, lon: 105.9467, val: 28.4 },
    { lat: 20.9910, lon: 105.9560, val: 35.9 },
  ];
  const grid_points: SpatialHeatmapPoint[] = [];
  const rows = 20, cols = 20;
  const latMin = 20.985, latMax = 21.005, lonMin = 105.938, lonMax = 105.962;
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
      const intensity = Math.min(1.0, Math.max(0.0, value / 200.0));
      grid_points.push({
        lat: Number(lat.toFixed(5)),
        lon: Number(lon.toFixed(5)),
        value,
        intensity,
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
    disclaimer: "Mô hình nội suy trực quan hóa IDW mô phỏng quanh Vinhomes Ocean Park 1.",
  };
}

export const HeatmapLayer: React.FC<HeatmapLayerProps> = ({
  activeLayer = "aqi",
  forecastHour = 0,
  viewMode = "heatmap",
  showHeatmap = true,
}) => {
  const map = useMap();
  const [data, setData] = useState<SpatialHeatmapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const heatLayerRef = useRef<L.HeatLayer | null>(null);
  const activeRequestKeyRef = useRef<string>("");

  const isActive = (viewMode === "heatmap" || showHeatmap) && viewMode !== "markers";

  // Problem 1 & 4: Fetch API with AbortController, request key guard & immediate state clearing
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

    // Immediately clear old grid data and set loading state
    setData(null);
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

  // Memoized grid points for Canvas layer
  const heatPoints = useMemo<Array<[number, number, number]>>(() => {
    if (!data || !Array.isArray(data.grid_points) || error != null) return [];
    return data.grid_points
      .filter(
        (p): p is SpatialHeatmapPoint =>
          p != null &&
          typeof p.lat === "number" &&
          Number.isFinite(p.lat) &&
          typeof p.lon === "number" &&
          Number.isFinite(p.lon) &&
          typeof p.intensity === "number" &&
          Number.isFinite(p.intensity),
      )
      .map((p) => [p.lat, p.lon, Math.min(1.0, Math.max(0.0, p.intensity))]);
  }, [data, error]);

  // Problem 2: Separate Lifecycle 1 — Initialization & Cleanup (depends ONLY on map)
  useEffect(() => {
    if (!map) return;

    const layer = L.heatLayer([], {
      radius: 28,
      blur: 18,
      maxZoom: 17,
      max: 1.0,
      minOpacity: 0.18,
      gradient: AQI_HEAT_GRADIENT,
    });
    heatLayerRef.current = layer;

    return () => {
      if (heatLayerRef.current && map) {
        if (map.hasLayer(heatLayerRef.current)) {
          map.removeLayer(heatLayerRef.current);
        }
        heatLayerRef.current = null;
      }
    };
  }, [map]);

  // Problem 2: Separate Lifecycle 2 — Data & Options Update (does NOT recreate instance)
  useEffect(() => {
    const layer = heatLayerRef.current;
    if (!layer || !map) return;

    if (isActive && heatPoints.length > 0) {
      const gradient = METRIC_HEAT_GRADIENTS[activeLayer] || AQI_HEAT_GRADIENT;
      layer.setOptions({ gradient });
      layer.setLatLngs(heatPoints);
      if (!map.hasLayer(layer)) {
        layer.addTo(map);
      }
      layer.redraw();
    } else {
      layer.setLatLngs([]);
      layer.redraw();
      if (map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    }
  }, [map, isActive, heatPoints, activeLayer]);

  if (!isActive) return null;

  const legendConfig = METRIC_LEGEND_CONFIGS[activeLayer] || METRIC_LEGEND_CONFIGS.aqi;

  return (
    <div
      className="spatial-heatmap-metadata-card"
      style={{
        background: "rgba(255, 255, 255, 0.95)",
        backdropFilter: "blur(10px)",
        padding: "12px 14px",
        borderRadius: "14px",
        border: "1px solid rgba(226, 232, 240, 0.9)",
        boxShadow: "0 6px 20px rgba(0,0,0,0.1)",
        maxWidth: "340px",
        fontSize: "0.78rem",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        pointerEvents: "auto",
      }}
    >
      {/* Title & Source Badge */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <strong style={{ fontSize: "0.84rem", color: "#0f172a", display: "flex", alignItems: "center", gap: "6px" }}>
          <Layers size={16} style={{ color: "#0284c7" }} />
          Bản đồ lan truyền {activeLayer.toUpperCase()}
          {forecastHour > 0 && data?.forecast_hour === forecastHour && (
            <span style={{ fontSize: "0.68rem", background: "#fef3c7", color: "#92400e", padding: "1px 6px", borderRadius: "4px", fontWeight: 700 }}>
              DỰ BÁO +{forecastHour}h
            </span>
          )}
        </strong>
        {data?.source && (
          <span
            style={{
              fontSize: "0.65rem",
              background: data.source === "simulator" ? "#fef3c7" : "#e0f2fe",
              color: data.source === "simulator" ? "#92400e" : "#0369a1",
              border: `1px solid ${data.source === "simulator" ? "#fde68a" : "#bae6fd"}`,
              padding: "2px 7px",
              borderRadius: "6px",
              fontWeight: 700,
              letterSpacing: "0.02em",
            }}
          >
            {data.source === "simulator" ? "DỮ LIỆU MÔ PHỎNG" : data.source}
          </span>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#0284c7", padding: "4px 0" }}>
          <RefreshCw size={14} className="spin-icon" />
          <span>Đang tải dữ liệu lan truyền {activeLayer.toUpperCase()}...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", padding: "10px", borderRadius: "10px" }} role="alert">
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
            <AlertTriangle size={15} />
            <strong>Không thể hiển thị Heatmap</strong>
          </div>
          <p style={{ margin: 0, fontSize: "0.72rem", lineHeight: 1.4 }}>{error}</p>
          <button
            type="button"
            onClick={() => setReloadToken((t) => t + 1)}
            style={{
              marginTop: "8px",
              background: "#dc2626",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              padding: "4px 10px",
              fontSize: "0.72rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <RefreshCw size={12} /> Thử lại
          </button>
        </div>
      )}

      {/* Valid Data Content */}
      {!loading && !error && data && (
        <>
          {data.grid_points.length === 0 ? (
            <div style={{ color: "#64748b", fontStyle: "italic", padding: "4px 0" }}>
              Chưa có lưới điểm lan truyền cho chỉ số này.
            </div>
          ) : (
            <>
              {/* Problem 3: Dedicated Metric Legend */}
              <div
                style={{
                  background: "#f8fafc",
                  borderRadius: "8px",
                  padding: "8px 10px",
                  border: "1px solid #e2e8f0",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ fontWeight: 700, color: "#334155", fontSize: "0.75rem" }}>
                  {legendConfig.title}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 6px" }}>
                  {legendConfig.items.map((item, idx) => (
                    <span
                      key={idx}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        fontSize: "0.7rem",
                        color: "#1e293b",
                        background: "#fff",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        border: "1px solid #cbd5e1",
                      }}
                    >
                      <span
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          backgroundColor: item.color,
                          display: "inline-block",
                          flexShrink: 0,
                        }}
                      />
                      <span>
                        {item.label}
                        {item.range ? ` (${item.range})` : ""}
                      </span>
                    </span>
                  ))}
                </div>
                {legendConfig.note && (
                  <div style={{ fontSize: "0.66rem", color: "#64748b", fontStyle: "italic", marginTop: "2px" }}>
                    * {legendConfig.note}
                  </div>
                )}
              </div>

              {/* Metadata Details Grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "6px",
                  fontSize: "0.72rem",
                  color: "#475569",
                  background: "#f1f5f9",
                  padding: "8px",
                  borderRadius: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <Clock size={12} style={{ color: "#0284c7" }} />
                  <span>
                    <strong>Cập nhật:</strong> {formatVnDateTime(data.generated_at || data.timestamp)}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <Cpu size={12} style={{ color: "#0284c7" }} />
                  <span>
                    <strong>Mô hình:</strong> {data.model_version || "Không khả dụng"}
                  </span>
                </div>
                {(data.wind_speed_ms != null || data.wind_direction_deg != null) && (
                  <div style={{ gridColumn: "span 2", display: "flex", alignItems: "center", gap: "10px", marginTop: "2px" }}>
                    {data.wind_speed_ms != null && (
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Wind size={12} style={{ color: "#0284c7" }} />
                        <strong>Gió:</strong> {data.wind_speed_ms} m/s
                      </span>
                    )}
                    {data.wind_direction_deg != null && (
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Compass
                          size={12}
                          style={{ transform: `rotate(${data.wind_direction_deg}deg)`, color: "#0284c7" }}
                        />
                        <strong>Hướng:</strong> {data.wind_direction_deg}°
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Disclaimer */}
              <div style={{ color: "#64748b", fontSize: "0.68rem", display: "flex", alignItems: "flex-start", gap: "4px" }}>
                <Info size={12} style={{ flexShrink: 0, marginTop: "2px" }} />
                <span>
                  {data.disclaimer || "Thông tin giới hạn của mô hình không khả dụng."}
                </span>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

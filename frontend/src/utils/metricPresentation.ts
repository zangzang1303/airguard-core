import { Activity, Wind, Cloud, Thermometer, Volume2, Droplets, LucideIcon } from "lucide-react";
import { Station } from "../types";
import { EnvironmentalLayerType } from "../types/superApp";
import { getMetricColor, getMetricLevel, getMetricScale, MetricLevel, MetricScale } from "../constants/metrics";

export interface MetricPresentation {
  key: EnvironmentalLayerType;
  label: string;
  shortLabel: string;
  unit: string;
  icon: LucideIcon;
  legendTitle: string;
  scale: MetricScale;
  formatValue: (value: number | null | undefined, placeholder?: string) => string;
  getColor: (value: number | null | undefined) => string;
  getLevel: (value: number | null | undefined) => MetricLevel | null;
  extractValue: (station: Station | null | undefined) => number | null;
}

const integerFormatter = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 0,
});

const decimalFormatter = new Intl.NumberFormat("vi-VN", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 1,
});

/**
 * Single source of truth for formatting environmental metric values across
 * markers, tooltips, drawers and legends in AirGuard AI.
 */
export function formatMetricValue(
  metric: string,
  value: number | null | undefined,
  placeholder: string = "—"
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return placeholder;
  }
  const key = (metric || "aqi").toLowerCase();
  if (key === "aqi" || key === "co2") {
    return integerFormatter.format(Math.round(value));
  }
  return decimalFormatter.format(value);
}

/**
 * Safely extracts raw numeric value for a given metric from a station object.
 * Returns null if the station is null, undefined, or if the field is not present.
 * Never coerces null to 0.
 */
export function extractStationMetricValue(
  station: Station | null | undefined,
  metric: EnvironmentalLayerType | string
): number | null {
  if (!station) return null;
  const key = (metric || "aqi").toLowerCase();

  switch (key) {
    case "aqi":
      return station.aqi !== undefined && station.aqi !== null ? station.aqi : null;
    case "pm25":
      return station.pm25 !== undefined && station.pm25 !== null ? station.pm25 : null;
    case "co2":
      return station.co2 !== undefined && station.co2 !== null ? station.co2 : null;
    case "temperature":
      return station.temperature !== undefined && station.temperature !== null ? station.temperature : null;
    case "noise_db":
    case "noise":
      return station.noise_db !== undefined && station.noise_db !== null ? station.noise_db : null;
    case "humidity":
      return station.humidity !== undefined && station.humidity !== null ? station.humidity : null;
    default:
      return null;
  }
}

const METRIC_PRESENTATION_REGISTRY: Record<EnvironmentalLayerType, {
  shortLabel: string;
  icon: LucideIcon;
}> = {
  aqi: {
    shortLabel: "AQI",
    icon: Activity,
  },
  pm25: {
    shortLabel: "PM2.5",
    icon: Wind,
  },
  co2: {
    shortLabel: "Khí CO₂",
    icon: Cloud,
  },
  temperature: {
    shortLabel: "Nhiệt độ",
    icon: Thermometer,
  },
  noise_db: {
    shortLabel: "Độ ồn",
    icon: Volume2,
  },
  humidity: {
    shortLabel: "Độ ẩm",
    icon: Droplets,
  },
};

/**
 * Returns comprehensive presentation metadata for any supported environmental layer metric.
 */
export function getMetricPresentation(metric: EnvironmentalLayerType | string): MetricPresentation {
  const normKey = ((metric || "aqi").toLowerCase() === "noise" ? "noise_db" : (metric || "aqi").toLowerCase()) as EnvironmentalLayerType;
  const meta = METRIC_PRESENTATION_REGISTRY[normKey] || METRIC_PRESENTATION_REGISTRY.aqi;
  const scale = getMetricScale(normKey);

  return {
    key: normKey,
    label: scale.label,
    shortLabel: meta.shortLabel,
    unit: scale.unit,
    icon: meta.icon,
    legendTitle: `Chú giải ${scale.label} & Trạng thái trạm`,
    scale,
    formatValue: (val: number | null | undefined, placeholder: string = "—") =>
      formatMetricValue(normKey, val, placeholder),
    getColor: (val: number | null | undefined) => getMetricColor(normKey, val),
    getLevel: (val: number | null | undefined) => getMetricLevel(normKey, val),
    extractValue: (station: Station | null | undefined) => extractStationMetricValue(station, normKey),
  };
}

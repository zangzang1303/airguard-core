export type MetricKey = "aqi" | "pm25" | "co2" | "temperature" | "noise_db" | "noise" | "humidity";

export interface MetricLevel {
  min: number;
  max: number;
  label: string;
  shortLabel?: string;
  color: string;
  classTag: string;
  description?: string;
}

export interface MetricScale {
  key: MetricKey;
  label: string;
  description: string;
  unit: string;
  min: number;
  max: number;
  provisional?: boolean;
  ticks: number[];
  levels: MetricLevel[];
}

/**
 * Single Source of Truth for all environmental metric threshold scales in AirGuard AI.
 * Aligned strictly with backend spatial_dispersion_service.py and alert_engine.py.
 */
export const METRIC_SCALES: Record<string, MetricScale> = {
  aqi: {
    key: "aqi",
    label: "Chất lượng không khí (AQI)",
    description: "Màu sắc thể hiện mức chất lượng không khí theo chỉ số AQI",
    unit: "AQI",
    min: 0,
    max: 500,
    provisional: false,
    ticks: [0, 50, 100, 150, 200, 300, 500],
    levels: [
      { min: 0, max: 50, label: "Tốt", color: "#10b981", classTag: "good", description: "Không ảnh hưởng sức khỏe" },
      { min: 51, max: 100, label: "Trung bình", color: "#eab308", classTag: "moderate", description: "Mức chấp nhận được" },
      { min: 101, max: 150, label: "Kém (nhạy cảm)", color: "#f97316", classTag: "sensitive", description: "Nhóm nhạy cảm nên hạn chế" },
      { min: 151, max: 200, label: "Xấu", color: "#ef4444", classTag: "unhealthy", description: "Ảnh hưởng sức khỏe mọi người" },
      { min: 201, max: 300, label: "Rất xấu", color: "#8b5cf6", classTag: "very-unhealthy", description: "Cảnh báo khẩn cấp" },
      { min: 301, max: 500, label: "Nguy hại", color: "#831843", classTag: "hazardous", description: "Nguy hại nghiêm trọng" },
    ],
  },
  pm25: {
    key: "pm25",
    label: "Bụi mịn PM2.5",
    description: "Màu sắc thể hiện nồng độ bụi mịn PM2.5 (µg/m³)",
    unit: "µg/m³",
    min: 0,
    max: 250,
    provisional: false,
    ticks: [0, 12, 35.4, 55.4, 150.4, 250],
    levels: [
      { min: 0, max: 12.0, label: "Tốt", color: "#10b981", classTag: "good", description: "Nồng độ bụi mịn an toàn" },
      { min: 12.1, max: 35.4, label: "Trung bình", color: "#eab308", classTag: "moderate", description: "Mức chấp nhận được" },
      { min: 35.5, max: 55.4, label: "Kém (nhạy cảm)", color: "#f97316", classTag: "sensitive", description: "Nhóm nhạy cảm cần chú ý" },
      { min: 55.5, max: 150.4, label: "Xấu", color: "#ef4444", classTag: "unhealthy", description: "Nồng độ bụi cao" },
      { min: 150.5, max: 250.0, label: "Rất xấu", color: "#8b5cf6", classTag: "very-unhealthy", description: "Nồng độ bụi mịn rất cao" },
    ],
  },
  co2: {
    key: "co2",
    label: "Nồng độ Khí CO₂",
    description: "Màu sắc thể hiện nồng độ CO₂ (ppm)",
    unit: "ppm",
    min: 400,
    max: 2000,
    provisional: true,
    ticks: [400, 700, 1000, 1500, 2000],
    levels: [
      { min: 400, max: 700, label: "Thấp (Tốt)", color: "#10b981", classTag: "good", description: "Không khí trong lành" },
      { min: 701, max: 1000, label: "Trung bình", color: "#eab308", classTag: "moderate", description: "Mức bình thường" },
      { min: 1001, max: 1500, label: "Cao (Kém)", color: "#f97316", classTag: "sensitive", description: "Gây mệt mỏi nhẹ" },
      { min: 1501, max: 2000, label: "Rất cao (Xấu)", color: "#ef4444", classTag: "unhealthy", description: "Thiếu oxy, nhức đầu" },
    ],
  },
  temperature: {
    key: "temperature",
    label: "Nhiệt độ môi trường",
    description: "Màu sắc thể hiện nhiệt độ môi trường (°C)",
    unit: "°C",
    min: 15,
    max: 45,
    provisional: true,
    ticks: [15, 28, 32, 36, 45],
    levels: [
      { min: 15, max: 28, label: "Mát (Tốt)", color: "#38bdf8", classTag: "good", description: "Thời tiết mát mẻ" },
      { min: 28.1, max: 32, label: "Vừa", color: "#10b981", classTag: "moderate", description: "Nhiệt độ dễ chịu" },
      { min: 32.1, max: 36, label: "Ấm / Cao", color: "#f97316", classTag: "sensitive", description: "Nhiệt độ cao" },
      { min: 36.1, max: 45, label: "Nóng (Rất cao)", color: "#ef4444", classTag: "unhealthy", description: "Nắng nóng gay gắt" },
    ],
  },
  noise_db: {
    key: "noise_db",
    label: "Mức độ tiếng ồn",
    description: "Màu sắc thể hiện mức độ tiếng ồn (dB)",
    unit: "dB",
    min: 30,
    max: 100,
    provisional: true,
    ticks: [30, 55, 70, 85, 100],
    levels: [
      { min: 30, max: 55, label: "Yên tĩnh", color: "#10b981", classTag: "good", description: "Môi trường yên tĩnh" },
      { min: 55.1, max: 70, label: "Vừa", color: "#eab308", classTag: "moderate", description: "Tiếng ồn chấp nhận được" },
      { min: 70.1, max: 85, label: "Ồn (Cao)", color: "#f97316", classTag: "sensitive", description: "Tiếng ồn cao" },
      { min: 85.1, max: 100, label: "Rất ồn (Xấu)", color: "#ef4444", classTag: "unhealthy", description: "Gây tổn thương thính giác" },
    ],
  },
  noise: {
    key: "noise",
    label: "Mức độ tiếng ồn",
    description: "Màu sắc thể hiện mức độ tiếng ồn (dB)",
    unit: "dB",
    min: 30,
    max: 100,
    provisional: true,
    ticks: [30, 55, 70, 85, 100],
    levels: [
      { min: 30, max: 55, label: "Yên tĩnh", color: "#10b981", classTag: "good", description: "Môi trường yên tĩnh" },
      { min: 55.1, max: 70, label: "Vừa", color: "#eab308", classTag: "moderate", description: "Tiếng ồn chấp nhận được" },
      { min: 70.1, max: 85, label: "Ồn (Cao)", color: "#f97316", classTag: "sensitive", description: "Tiếng ồn cao" },
      { min: 85.1, max: 100, label: "Rất ồn (Xấu)", color: "#ef4444", classTag: "unhealthy", description: "Gây tổn thương thính giác" },
    ],
  },
  humidity: {
    key: "humidity",
    label: "Độ ẩm không khí",
    description: "Màu sắc thể hiện độ ẩm tương đối (%)",
    unit: "%",
    min: 20,
    max: 100,
    provisional: true,
    ticks: [20, 40, 60, 80, 100],
    levels: [
      { min: 20, max: 40, label: "Khô", color: "#38bdf8", classTag: "dry", description: "Độ ẩm thấp" },
      { min: 40.1, max: 70, label: "Vừa (Tốt)", color: "#10b981", classTag: "good", description: "Độ ẩm lý tưởng" },
      { min: 70.1, max: 100, label: "Ẩm cao", color: "#1d4ed8", classTag: "humid", description: "Độ ẩm cao" },
    ],
  },
};

/**
 * Pure functions for metric scale manipulation and color evaluation.
 */
export function getMetricScale(metric: string): MetricScale {
  const key = (metric || "aqi").toLowerCase();
  return METRIC_SCALES[key] || METRIC_SCALES.aqi;
}

export function getMetricLevel(metric: string, value: number | null | undefined): MetricLevel | null {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  const scale = getMetricScale(metric);
  const val = Math.min(scale.max, Math.max(scale.min, value));
  for (const level of scale.levels) {
    if (val >= level.min && val <= level.max) {
      return level;
    }
  }
  return scale.levels[scale.levels.length - 1];
}

export function normalizeMetricValue(metric: string, value: number | null | undefined): number {
  if (value === null || value === undefined || Number.isNaN(value)) return 0;
  const scale = getMetricScale(metric);
  return Math.min(1.0, Math.max(0.0, (value - scale.min) / (scale.max - scale.min)));
}

export function getMetricColor(metric: string, value: number | null | undefined): string {
  const level = getMetricLevel(metric, value);
  return level ? level.color : "#94a3b8"; // Slate-400 fallback for null/undefined
}

export function getMetricTicks(metric: string): number[] {
  return getMetricScale(metric).ticks;
}

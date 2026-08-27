export interface AqiLevel {
  min: number;
  max: number;
  label: string;
  shortLabel: string;
  color: string;
  classTag: string;
  description: string;
}

export const AQI_MAX_SCALE = 500;

export const AQI_LEVELS: ReadonlyArray<AqiLevel> = [
  {
    min: 0,
    max: 50,
    label: "Tốt",
    shortLabel: "Tốt",
    color: "#10b981", // Emerald/Green
    classTag: "good",
    description: "Chất lượng không khí tốt, không ảnh hưởng sức khỏe",
  },
  {
    min: 51,
    max: 100,
    label: "Trung bình",
    shortLabel: "Trung bình",
    color: "#eab308", // Yellow
    classTag: "moderate",
    description: "Chất lượng không khí ở mức chấp nhận được",
  },
  {
    min: 101,
    max: 150,
    label: "Kém (nhạy cảm)",
    shortLabel: "Kém (nhạy cảm)",
    color: "#f97316", // Orange
    classTag: "sensitive",
    description: "Kém cho nhóm người nhạy cảm với ô nhiễm",
  },
  {
    min: 151,
    max: 200,
    label: "Xấu",
    shortLabel: "Xấu",
    color: "#ef4444", // Red
    classTag: "unhealthy",
    description: "Xấu, có hại cho sức khỏe mọi người",
  },
  {
    min: 201,
    max: 300,
    label: "Rất xấu",
    shortLabel: "Rất xấu",
    color: "#8b5cf6", // Purple
    classTag: "very-unhealthy",
    description: "Cảnh báo sức khỏe khẩn cấp cho toàn bộ cư dân",
  },
  {
    min: 301,
    max: 500,
    label: "Nguy hại",
    shortLabel: "Nguy hại",
    color: "#831843", // Maroon
    classTag: "hazardous",
    description: "Nguy hại nghiêm trọng, biến chứng sức khỏe nguy hiểm",
  },
];

export const AQI_TICKS: ReadonlyArray<number> = [0, 50, 100, 150, 200, 300, 500];

export function getAqiLevel(aqi: number | null | undefined): AqiLevel | null {
  if (aqi === null || aqi === undefined || Number.isNaN(aqi)) return null;
  const val = Math.round(aqi);
  for (const level of AQI_LEVELS) {
    if (val >= level.min && val <= level.max) {
      return level;
    }
  }
  if (val > AQI_MAX_SCALE) return AQI_LEVELS[AQI_LEVELS.length - 1];
  return AQI_LEVELS[0];
}

export function getAqiColorHex(aqi: number | null | undefined): string {
  const level = getAqiLevel(aqi);
  return level ? level.color : "#94a3b8"; // slate-400 for null/undefined
}

export function getAqiCategoryLabel(aqi: number | null | undefined): { label: string; classTag: string } {
  const level = getAqiLevel(aqi);
  if (!level) return { label: "Không khả dụng", classTag: "na" };
  return {
    label: `${level.label} (${level.min}–${level.max})`,
    classTag: level.classTag,
  };
}

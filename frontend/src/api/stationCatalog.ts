import {
  AdminRegion,
  AdminStation,
  StationCatalogResponse,
  StationChangeEntry,
} from "../types";

const now = new Date();
const minutesAgo = (m: number) =>
  new Date(now.getTime() - m * 60 * 1000).toISOString();
const daysAgo = (d: number) =>
  new Date(now.getTime() - d * 24 * 3600 * 1000).toISOString();

// Demo data cho module Khu vực & Trạm (P2).
// Chỉ tồn tại trên client cho demo MVP; thay bằng /api/v1/regions + /api/v1/stations khi contract chốt.
const DEMO_REGIONS: AdminRegion[] = [
  {
    region_id: "vinuni",
    region_name: "VinUni Campus",
    description: "Khuôn viên đại học, cổng chính và bãi đỗ xe trung tâm",
  },
  {
    region_id: "ocean-park",
    region_name: "Vinhomes Ocean Park",
    description: "Khu đô thị, trục giao thông chính và công viên",
  },
];

const DEMO_STATIONS: AdminStation[] = [
  {
    station_id: "S01",
    station_name: "Cổng chính VinUni",
    region_id: "vinuni",
    region_name: "VinUni Campus",
    location_type: "Cổng chính",
    lifecycle: "active",
    owner: "AirGuard Operations",
    status: "online",
    is_stale: false,
    pm25: 42.5,
    measured_at: minutesAgo(4),
    received_at: minutesAgo(3),
    source: "Simulator",
    latitude: 20.9441,
    longitude: 105.9439,
    map_x: 23,
    map_y: 62,
    status_reason: null,
    provisioned_at: daysAgo(180),
  },
  {
    station_id: "S02",
    station_name: "Bãi đỗ xe trung tâm",
    region_id: "vinuni",
    region_name: "VinUni Campus",
    location_type: "Giao thông / bãi đỗ",
    lifecycle: "active",
    owner: "AirGuard Operations",
    status: "stale",
    is_stale: true,
    pm25: 55.2,
    measured_at: minutesAgo(95),
    received_at: minutesAgo(93),
    source: "Simulator",
    latitude: 20.945,
    longitude: 105.9435,
    map_x: 51,
    map_y: 39,
    status_reason: "Không nhận được measurement mới trong 90 phút",
    provisioned_at: daysAgo(178),
  },
  {
    station_id: "S03",
    station_name: "Trục đường chính Ocean Park",
    region_id: "ocean-park",
    region_name: "Vinhomes Ocean Park",
    location_type: "Giao thông / thương mại",
    lifecycle: "active",
    owner: "Vinhomes Facility Team",
    status: "online",
    is_stale: false,
    pm25: 66.1,
    measured_at: minutesAgo(2),
    received_at: minutesAgo(2),
    source: "Simulator",
    latitude: 20.9445,
    longitude: 105.9452,
    map_x: 74,
    map_y: 65,
    status_reason: null,
    provisioned_at: daysAgo(150),
  },
  {
    station_id: "S04",
    station_name: "Công viên trung tâm",
    region_id: "ocean-park",
    region_name: "Vinhomes Ocean Park",
    location_type: "Công viên",
    lifecycle: "active",
    owner: "Vinhomes Facility Team",
    status: "offline",
    is_stale: false,
    pm25: null,
    measured_at: null,
    received_at: minutesAgo(340),
    source: "Simulator",
    latitude: 20.9455,
    longitude: 105.9458,
    map_x: 34,
    map_y: 31,
    status_reason: "Thiết bị mất kết nối từ 05:40, chờ đội bảo trì",
    provisioned_at: daysAgo(120),
  },
  {
    station_id: "S05",
    station_name: "Khu thể thao ngoài trời",
    region_id: "ocean-park",
    region_name: "Vinhomes Ocean Park",
    location_type: "Thể thao",
    lifecycle: "active",
    owner: "Vinhomes Facility Team",
    status: "invalid",
    is_stale: false,
    pm25: null,
    measured_at: minutesAgo(6),
    received_at: minutesAgo(6),
    source: "Simulator",
    latitude: null,
    longitude: null,
    map_x: null,
    map_y: null,
    status_reason:
      "Payload không qua validation (PM2.5 âm) và catalog thiếu toạ độ",
    provisioned_at: daysAgo(75),
  },
];

const DEMO_STATION_CHANGES: Record<string, StationChangeEntry[]> = {
  S01: [
    {
      id: "AUD-S01-1",
      time: daysAgo(12),
      actor: "Lê Thị D (admin)",
      action: "STATION_UPDATE_METADATA",
      detail: "Đổi tên trạm thành Cổng chính VinUni",
      outcome: "SUCCESS",
      correlation_id: "req-s-4411",
    },
  ],
  S02: [
    {
      id: "AUD-S02-1",
      time: minutesAgo(95),
      actor: "Hệ thống",
      action: "STATION_DATA_STALE",
      detail: "Không nhận measurement mới trong ngưỡng freshness",
      outcome: "WARNING",
      correlation_id: "req-s-5120",
    },
  ],
  S04: [
    {
      id: "AUD-S04-1",
      time: minutesAgo(340),
      actor: "Hệ thống",
      action: "STATION_OFFLINE",
      detail: "Mất heartbeat từ thiết bị liên kết",
      outcome: "WARNING",
      correlation_id: "req-s-5008",
    },
    {
      id: "AUD-S04-2",
      time: daysAgo(30),
      actor: "Trần Quốc Việt (admin)",
      action: "STATION_UPDATE_METADATA",
      detail: "Cập nhật owner vận hành sang Vinhomes Facility Team",
      outcome: "SUCCESS",
      correlation_id: "req-s-3390",
    },
  ],
  S05: [
    {
      id: "AUD-S05-1",
      time: minutesAgo(6),
      actor: "Hệ thống",
      action: "STATION_DATA_INVALID",
      detail: "Measurement bị từ chối bởi validation rule",
      outcome: "REJECTED",
      correlation_id: "req-s-5233",
    },
    {
      id: "AUD-S05-2",
      time: daysAgo(75),
      actor: "Lê Thị D (admin)",
      action: "STATION_PROVISION",
      detail: "Provision trạm S05 chưa kèm toạ độ hợp lệ",
      outcome: "SUCCESS",
      correlation_id: "req-s-2101",
    },
  ],
};

export const stationCatalogApi = {
  async getCatalog(): Promise<StationCatalogResponse> {
    const missingCoordinates = DEMO_STATIONS.filter(
      (station) => station.latitude === null || station.longitude === null,
    );
    return {
      regions: DEMO_REGIONS,
      stations: DEMO_STATIONS,
      partial_error: missingCoordinates.length
        ? `${missingCoordinates.length} trạm thiếu toạ độ hợp lệ nên không hiển thị trên bản đồ. Xem lý do trong danh sách.`
        : null,
    };
  },

  async getStationChanges(stationId: string): Promise<StationChangeEntry[]> {
    return DEMO_STATION_CHANGES[stationId] ?? [];
  },
};

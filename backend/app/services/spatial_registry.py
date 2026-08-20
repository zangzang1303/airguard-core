from __future__ import annotations

import math
from typing import Any


class SpatialRegistry:
    """
    Geospatial Registry for Vinhomes Ocean Park 1.
    Provides immutable geo-spatial definitions for stations, POIs, and areas,
    with Haversine distance calculations and area-sensor mappings.
    """

    STATIONS = {
        "S01": {
            "id": "S01",
            "station_id": "S01",
            "name": "Trục Đa Tốn phía Tây Bắc",
            "area_id": "area_da_ton",
            "latitude": 21.0008,
            "longitude": 105.9428,
            "location_type": "northwest_road",
            "tags": ["traffic", "gate", "northwest"],
        },
        "S02": {
            "id": "S02",
            "station_id": "S02",
            "name": "Khu Căn hộ Sapphire",
            "area_id": "area_sapphire",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "location_type": "high_rise_residential",
            "tags": ["residential", "park", "northwest"],
        },
        "S03": {
            "id": "S03",
            "station_id": "S03",
            "name": "Ven Hồ Ngọc Trai",
            "area_id": "area_ngoc_trai",
            "latitude": 20.9953,
            "longitude": 105.9500,
            "location_type": "lakeside_residential",
            "tags": ["lake", "running", "central", "park"],
        },
        "S04": {
            "id": "S04",
            "station_id": "S04",
            "name": "Khuôn viên VinUni",
            "area_id": "area_vinuni",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "location_type": "university_campus",
            "tags": ["campus", "green", "southwest"],
        },
        "S05": {
            "id": "S05",
            "station_id": "S05",
            "name": "Khu Hải Âu phía Đông Nam",
            "area_id": "area_hai_au",
            "latitude": 20.9910,
            "longitude": 105.9560,
            "location_type": "southeast_residential",
            "tags": ["salt_lake", "commercial", "southeast"],
        },
    }

    POIS = [
        {
            "id": "poi_ngoc_trai_lake",
            "area_id": "area_ngoc_trai",
            "name": "Hồ Ngọc Trai (Hồ nước ngọt 24.5ha)",
            "short_name": "Hồ Ngọc Trai",
            "category": "lake",
            "latitude": 20.9953,
            "longitude": 105.9500,
            "sensor_id": "S03",
            "suitable_activities": ["running", "walking", "elderly_stroll", "general"],
            "description": "Hồ nước ngọt 24.5ha với cung đường chạy bộ ven bờ cát trắng lộng gió.",
        },
        {
            "id": "poi_salt_lake",
            "area_id": "area_salt_lake",
            "name": "Biển Hồ Nước Mặn Crystal Lagoons",
            "short_name": "Biển Hồ Nước Mặn",
            "category": "lake",
            "latitude": 20.9945,
            "longitude": 105.9585,
            "sensor_id": "S05",
            "suitable_activities": ["walking", "children_play", "dining_outdoor"],
            "description": "Biển hồ nước mặn 6.1ha nhiệt đới với bãi cát và không gian thoáng đãng.",
        },
        {
            "id": "poi_vinuni",
            "area_id": "area_vinuni",
            "name": "Khuôn viên Đại học VinUniversity",
            "short_name": "VinUni",
            "category": "campus",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "sensor_id": "S04",
            "suitable_activities": ["walking", "running", "elderly_stroll"],
            "description": "Khuôn viên đại học tinh hoa nhiều cây xanh, mật độ giao thông nội khu thấp.",
        },
        {
            "id": "poi_san_ho_park",
            "area_id": "area_san_ho",
            "name": "Công viên San Hô & Đường dạo bộ",
            "short_name": "Công viên San Hô",
            "category": "park",
            "latitude": 20.9935,
            "longitude": 105.9405,
            "sensor_id": "S01",
            "suitable_activities": ["running", "walking", "children_play"],
            "description": "Công viên dải xanh ven sông với đường chạy bộ chuyên dụng và sân chơi trẻ em.",
        },
        {
            "id": "poi_sapphire",
            "area_id": "area_sapphire",
            "name": "Khu Căn hộ Sapphire & Công viên Nội khu",
            "short_name": "Khu Sapphire",
            "category": "residential",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "sensor_id": "S02",
            "suitable_activities": ["walking", "children_play", "running"],
            "description": "Quần thể căn hộ hiện đại với cụm sân thể thao và vườn cảnh quan.",
        },
        {
            "id": "poi_vincom",
            "area_id": "area_vincom",
            "name": "Trung tâm thương mại Vincom Mega Mall",
            "short_name": "Vincom Mega Mall",
            "category": "commercial",
            "latitude": 20.9985,
            "longitude": 105.9525,
            "sensor_id": "S02",
            "suitable_activities": ["dining_outdoor", "walking"],
            "description": "Khu trung tâm thương mại và ẩm thực sầm uất với luồng xe cộ ra vào.",
        },
        {
            "id": "poi_hai_au",
            "area_id": "area_hai_au",
            "name": "Quảng trường & Tuyến phố Hải Âu",
            "short_name": "Khu Hải Âu",
            "category": "commercial",
            "latitude": 20.9910,
            "longitude": 105.9560,
            "sensor_id": "S05",
            "suitable_activities": ["walking", "dining_outdoor"],
            "description": "Tuyến phố thương mại ven biển hồ sôi động về chiều tối.",
        },
    ]

    RUNNING_ROUTES = [
        {
            "id": "route_ngoc_trai_loop",
            "name": "Cung đường Ven Hồ Ngọc Trai (Lakeside Promenade)",
            "short_name": "Ven Hồ Ngọc Trai",
            "distance_km": 3.8,
            "sensor_id": "S03",
            "surface": "Lối dạo ven hồ lát đá granite rộng 5m bám sát bờ cát trắng",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới, 100% đường dạo bộ",
            "lighting_rating": "Xuất sắc (Hệ thống đèn LED cảnh quan ven hồ 24/7)",
            "highlights": "Đường chạy bo tròn chuẩn theo bờ hồ cát trắng 24.5ha lộng gió, hàng dừa xanh nhiệt đới.",
            "start_point": {"name": "Quảng trường Cá Voi", "lat": 20.9938, "lng": 105.9485},
            "coordinates": [
                [20.9938, 105.9485],
                [20.9944, 105.9488],
                [20.9950, 105.9492],
                [20.9958, 105.9500],
                [20.9965, 105.9508],
                [20.9970, 105.9518],
                [20.9975, 105.9530],
                [20.9972, 105.9542],
                [20.9968, 105.9550],
                [20.9962, 105.9560],
                [20.9955, 105.9568],
                [20.9948, 105.9562],
                [20.9942, 105.9555],
                [20.9935, 105.9545],
                [20.9928, 105.9532],
                [20.9922, 105.9520],
                [20.9918, 105.9510],
                [20.9925, 105.9495],
                [20.9938, 105.9485],
            ],
        },
        {
            "id": "route_san_ho_riverwalk",
            "name": "Cung đường Dải xanh Công viên San Hô",
            "short_name": "Dải xanh San Hô",
            "distance_km": 2.5,
            "sensor_id": "S01",
            "surface": "Đường chạy bộ cao su tổng hợp êm chân ven sông sinh thái",
            "traffic_conflict": "Khu công viên khép kín, an toàn tuyệt đối cho runner",
            "lighting_rating": "Tốt (Đèn rọi lối đi ban đêm)",
            "highlights": "Dải công viên cây xanh trải dài 2.5km ven sông, nhiều máy tập thể thao ngoài trời.",
            "start_point": {"name": "Cổng chào Công viên San Hô", "lat": 20.9935, "lng": 105.9405},
            "coordinates": [
                [20.9935, 105.9405],
                [20.9955, 105.9412],
                [20.9978, 105.9420],
                [21.0000, 105.9425],
                [21.0018, 105.9428],
            ],
        },
        {
            "id": "route_vinuni_circuit",
            "name": "Cung đường Vòng quanh Đại học VinUniversity",
            "short_name": "Vòng VinUni",
            "distance_km": 1.8,
            "sensor_id": "S04",
            "surface": "Đường nội bộ đá granite cao cấp phẳng mịn",
            "traffic_conflict": "Mật độ phương tiện nội bộ cực thấp (< 5 km/h)",
            "lighting_rating": "Xuất sắc (Hệ thống chiếu sáng chuẩn quốc tế)",
            "highlights": "Khuôn viên trường đại học tinh hoa, kiến trúc Gothic tráng lệ, không khí trong lành yên tĩnh.",
            "start_point": {"name": "Tòa nhà Khởi nghiệp VinUni", "lat": 20.9898, "lng": 105.9467},
            "coordinates": [
                [20.9898, 105.9467],
                [20.9912, 105.9455],
                [20.9922, 105.9480],
                [20.9908, 105.9495],
                [20.9888, 105.9480],
                [20.9898, 105.9467],
            ],
        },
        {
            "id": "route_crystal_lagoon",
            "name": "Cung đường Biển hồ Nước mặn Crystal Lagoons",
            "short_name": "Biển hồ Nước Mặn",
            "distance_km": 2.2,
            "sensor_id": "S05",
            "surface": "Lối dạo bộ lát gạch ven biển hồ nhân tạo",
            "traffic_conflict": "Tách biệt xe cộ, tuyến phố đi bộ ven biển",
            "lighting_rating": "Rất tốt (Đèn hắt bãi cát)",
            "highlights": "Trải nghiệm chạy bộ bên bờ biển hồ nước mặn nhân tạo 6.1ha, không khí mang hơi thở nhiệt đới.",
            "start_point": {"name": "Quảng trường Hải Âu", "lat": 20.9945, "lng": 105.9585},
            "coordinates": [
                [20.9945, 105.9585],
                [20.9960, 105.9595],
                [20.9972, 105.9580],
                [20.9955, 105.9565],
                [20.9930, 105.9555],
                [20.9920, 105.9570],
                [20.9945, 105.9585],
            ],
        },
        {
            "id": "route_sapphire_boulevard",
            "name": "Cung đường Đại lộ Sapphire & Vườn Nhật",
            "short_name": "Đại lộ Sapphire",
            "distance_km": 2.0,
            "sensor_id": "S02",
            "surface": "Vỉa hè nội khu rộng rãi lát đá terrazzo",
            "traffic_conflict": "Có giao cắt nhẹ với đường nội khu",
            "lighting_rating": "Rất tốt",
            "highlights": "Tuyến đường chạy qua cụm vườn Nhật, hồ cá Koi và hệ thống sân thể thao ngoài trời.",
            "start_point": {"name": "Tháp đồng hồ Sapphire", "lat": 20.9975, "lng": 105.9430},
            "coordinates": [
                [20.9975, 105.9430],
                [20.9960, 105.9445],
                [20.9950, 105.9460],
                [20.9970, 105.9475],
                [20.9990, 105.9450],
                [20.9975, 105.9430],
            ],
        },
    ]

    INDOOR_VENUES = [
        {
            "id": "venue_sapphire_pool",
            "name": "Bể bơi 4 mùa Mái kính Sapphire Rooftop",
            "short_name": "Bể bơi 4 mùa Sapphire",
            "category": "indoor_pool",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "sensor_id": "S02",
            "activities": ["Bơi lội trong nhà", "Thư giãn phục hồi", "Cardio dưới nước"],
            "suitable_conditions": ["Bụi mịn cao", "Nắng gắt", "Mưa bão"],
            "description": "Bể bơi nước ấm 30°C trong nhà mái kính panorama, hệ thống lọc tuần hoàn khép kín tuyệt đối không bụi mịn.",
            "operating_hours": "06:00 - 21:30",
        },
        {
            "id": "venue_vinuni_sports",
            "name": "Trung tâm Thể thao & Nhà thi đấu Đa năng VinUniversity",
            "short_name": "VinUni Sports Complex",
            "category": "indoor_sports_arena",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "sensor_id": "S04",
            "activities": ["Máy chạy bộ Treadmill", "Cầu lông trong nhà", "Bóng rổ điều hòa", "Gym & Fitness"],
            "suitable_conditions": ["Bụi mịn cao", "Nhiệt độ cực đoan", "Chất lượng không khí kém"],
            "description": "Khu phức hợp thể thao đa năng điều hòa lọc khí tươi HEPA, đầy đủ dàn máy chạy bộ và sân thi đấu tiêu chuẩn.",
            "operating_hours": "06:00 - 22:00",
        },
        {
            "id": "venue_vincom_fitness",
            "name": "Trung tâm Thể hình & Yoga Vincom Mega Mall",
            "short_name": "Vincom Mega Fitness",
            "category": "fitness_gym",
            "latitude": 20.9985,
            "longitude": 105.9525,
            "sensor_id": "S02",
            "activities": ["Chạy bộ máy Treadmill", "Yoga trong nhà", "Cardio kháng lực"],
            "suitable_conditions": ["Bụi mịn cao", "Trời mưa", "Thời tiết khắc nghiệt"],
            "description": "Phòng tập Gym & Yoga điều hòa chuẩn 5 sao với dàn máy tập cardio hiện đại nhìn ra biển hồ.",
            "operating_hours": "05:30 - 22:00",
        },
        {
            "id": "venue_ocean_clubhouse",
            "name": "Nhà Thể thao & Sinh hoạt Cộng đồng San Hô Clubhouse",
            "short_name": "Clubhouse San Hô",
            "category": "clubhouse_sports",
            "latitude": 20.9935,
            "longitude": 105.9405,
            "sensor_id": "S01",
            "activities": ["Bóng bàn", "Dưỡng sinh trong nhà", "Đi bộ hành lang máy lạnh"],
            "suitable_conditions": ["Bụi mịn cao", "Nhiệt độ ngoài trời cao"],
            "description": "Không gian thể thao cộng đồng khép kín trong khuôn viên công viên, tiện lợi cho cư dân rèn luyện sức khỏe.",
            "operating_hours": "06:00 - 21:00",
        },
    ]

    @classmethod
    def calculate_distance_m(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula for geodesic distance in meters."""
        r = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def get_station(cls, station_id: str) -> dict[str, Any] | None:
        return cls.STATIONS.get(station_id.upper())

    @classmethod
    def get_poi(cls, poi_id: str) -> dict[str, Any] | None:
        for p in cls.POIS:
            if p["id"] == poi_id:
                return p
        return None

    @classmethod
    def get_route(cls, route_id: str) -> dict[str, Any] | None:
        for r in cls.RUNNING_ROUTES:
            if r["id"] == route_id:
                return r
        return None

    @classmethod
    def list_routes(cls) -> list[dict[str, Any]]:
        return list(cls.RUNNING_ROUTES)

    @classmethod
    def list_indoor_venues(cls) -> list[dict[str, Any]]:
        return list(cls.INDOOR_VENUES)

    @classmethod
    def generate_personalized_route(
        cls,
        user_lat: float,
        user_lng: float,
        target_km: float | None = None,
        base_circuit_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Dynamically generates a 100% genuine OpenStreetMap road-network running path
        tailored to the user's starting location and requested distance.
        """
        from .real_road_routing_service import real_road_routing

        return real_road_routing.generate_exact_running_route(
            user_lat=user_lat,
            user_lng=user_lng,
            target_km=target_km,
            prefer_circuit_id=base_circuit_id,
        )

    @classmethod
    def find_poi_by_name(cls, query: str) -> dict[str, Any] | None:
        q = query.lower().strip()
        name_map = {
            "ngọc trai": "poi_ngoc_trai_lake",
            "hồ ngọc trai": "poi_ngoc_trai_lake",
            "hồ nước ngọt": "poi_ngoc_trai_lake",
            "sapphire": "poi_sapphire",
            "khu sapphire": "poi_sapphire",
            "san hô": "poi_san_ho_park",
            "công viên san hô": "poi_san_ho_park",
            "vinuni": "poi_vinuni",
            "đại học vinuni": "poi_vinuni",
            "biển hồ": "poi_salt_lake",
            "nước mặn": "poi_salt_lake",
            "crystal": "poi_salt_lake",
            "vincom": "poi_vincom",
            "hải âu": "poi_hai_au",
            "đa tốn": "S01",
        }
        for k, target in name_map.items():
            if k in q:
                if target.startswith("poi_"):
                    return cls.get_poi(target)
                elif target.startswith("S0"):
                    st = cls.get_station(target)
                    if st:
                        return {
                            "id": f"poi_{target.lower()}",
                            "area_id": st["area_id"],
                            "name": st["name"],
                            "short_name": st["name"],
                            "category": "traffic_gate",
                            "latitude": st["latitude"],
                            "longitude": st["longitude"],
                            "sensor_id": target,
                            "suitable_activities": ["general"],
                            "description": f"Trạm quan trắc {st['name']}",
                        }

        # Substring search in POI names
        for p in cls.POIS:
            if p["short_name"].lower() in q or p["name"].lower() in q:
                return p
        return None

    @classmethod
    def list_pois(cls, category: str | None = None) -> list[dict[str, Any]]:
        if not category:
            return list(cls.POIS)
        return [p for p in cls.POIS if p["category"] == category]

    @classmethod
    def find_nearest_sensor(cls, lat: float, lon: float) -> str:
        best_id = "S03"
        min_dist = float("inf")
        for s_id, st in cls.STATIONS.items():
            d = cls.calculate_distance_m(lat, lon, st["latitude"], st["longitude"])
            if d < min_dist:
                min_dist = d
                best_id = s_id
        return best_id


spatial_registry = SpatialRegistry()

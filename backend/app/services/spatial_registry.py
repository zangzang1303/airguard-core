from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

from .air_quality import pm25_aqi


def remove_accents(input_str: str) -> str:
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace("đ", "d").replace("Đ", "D")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = remove_accents(text.lower().strip())
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


class SpatialRegistry:
    """
    Geospatial Registry for Vinhomes Ocean Park 1.
    Provides immutable geo-spatial definitions for stations, POIs, and areas,
    with Haversine distance calculations, area-sensor mappings, and IDW spatial interpolation.
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
            "name": "Khu căn hộ Sapphire",
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
        # 1. An Đào (Residential subdivision - NW zone near Đa Tốn / San Hô)
        {
            "id": "poi_an_dao",
            "area_id": "area_an_dao",
            "name": "Phân khu Biệt thự & Nhà phố An Đào",
            "short_name": "An Đào",
            "category": "residential",
            "latitude": 20.9995,
            "longitude": 105.9415,
            "sensor_id": "S01",
            "is_interpolated": True,
            "source_sensors": ["S01", "S02"],
            "aliases": [
                "an đào", "an dao", "khu an đào", "khu an dao",
                "phân khu an đào", "phân khu an dao", "biệt thự an đào",
                "nhà phố an đào", "đường an đào", "an dao 1", "an đào 1"
            ],
            "suitable_activities": ["walking", "elderly_stroll", "children_play", "running"],
            "description": "Phân khu thấp tầng biệt thự, liền kề An Đào ven trục Đa Tốn phía Tây Bắc với không gian yên tĩnh.",
        },
        # 2. Hồ Ngọc Trai
        {
            "id": "poi_ngoc_trai_lake",
            "area_id": "area_ngoc_trai",
            "name": "Hồ Ngọc Trai (Hồ nước ngọt 24.5ha)",
            "short_name": "Hồ Ngọc Trai",
            "category": "lake",
            "latitude": 20.9953,
            "longitude": 105.9500,
            "sensor_id": "S03",
            "is_interpolated": False,
            "source_sensors": ["S03"],
            "aliases": [
                "hồ ngọc trai", "ho ngoc trai", "ngọc trai", "ngoc trai",
                "hồ nước ngọt", "ho nuoc ngot", "hồ trung tâm", "ho trung tam", "hồ 24ha", "ho 24ha"
            ],
            "suitable_activities": ["running", "walking", "elderly_stroll", "general"],
            "description": "Hồ nước ngọt 24.5ha với cung đường chạy bộ ven bờ cát trắng lộng gió.",
        },
        # 3. Biển Hồ Nước Mặn Crystal Lagoons
        {
            "id": "poi_salt_lake",
            "area_id": "area_salt_lake",
            "name": "Biển Hồ Nước Mặn Crystal Lagoons",
            "short_name": "Biển Hồ Nước Mặn",
            "category": "lake",
            "latitude": 20.9945,
            "longitude": 105.9585,
            "sensor_id": "S05",
            "is_interpolated": False,
            "source_sensors": ["S05"],
            "aliases": [
                "biển hồ", "bien ho", "biển hồ nước mặn", "bien ho nuoc man",
                "nước mặn", "nuoc man", "crystal lagoons", "crystal lagoon", "crystal"
            ],
            "suitable_activities": ["walking", "children_play", "dining_outdoor"],
            "description": "Biển hồ nước mặn 6.1ha nhiệt đới với bãi cát và không gian thoáng đãng.",
        },
        # 4. VinUniversity
        {
            "id": "poi_vinuni",
            "area_id": "area_vinuni",
            "name": "Khuôn viên Đại học VinUniversity",
            "short_name": "VinUni",
            "category": "campus",
            "latitude": 20.9898,
            "longitude": 105.9467,
            "sensor_id": "S04",
            "is_interpolated": False,
            "source_sensors": ["S04"],
            "aliases": [
                "vinuni", "vin university", "đại học vinuni", "dai hoc vinuni",
                "trường vinuni", "truong vinuni", "vin uni"
            ],
            "suitable_activities": ["walking", "running", "elderly_stroll"],
            "description": "Khuôn viên đại học tinh hoa nhiều cây xanh, mật độ giao thông nội khu thấp.",
        },
        # 5. Công viên San Hô
        {
            "id": "poi_san_ho_park",
            "area_id": "area_san_ho",
            "name": "Công viên San Hô & Đường dạo bộ",
            "short_name": "Công viên San Hô",
            "category": "park",
            "latitude": 20.9935,
            "longitude": 105.9405,
            "sensor_id": "S01",
            "is_interpolated": False,
            "source_sensors": ["S01"],
            "aliases": [
                "công viên san hô", "cong vien san ho", "san hô", "san ho",
                "phân khu san hô", "khu san hô", "đường san hô", "duong san ho"
            ],
            "suitable_activities": ["running", "walking", "children_play"],
            "description": "Công viên dải xanh ven sông với đường chạy bộ chuyên dụng và sân chơi trẻ em.",
        },
        # 6. Khu Căn hộ Sapphire
        {
            "id": "poi_sapphire",
            "area_id": "area_sapphire",
            "name": "Khu Căn hộ Sapphire & Công viên Nội khu",
            "short_name": "Khu Sapphire",
            "category": "residential",
            "latitude": 20.9975,
            "longitude": 105.9430,
            "sensor_id": "S02",
            "is_interpolated": False,
            "source_sensors": ["S02"],
            "aliases": [
                "sapphire", "khu sapphire", "the sapphire", "sapphire 1", "sapphire 2", "s1", "s2"
            ],
            "suitable_activities": ["walking", "children_play", "running"],
            "description": "Quần thể căn hộ hiện đại với cụm sân thể thao và vườn cảnh quan.",
        },
        # 7. Vincom Mega Mall
        {
            "id": "poi_vincom",
            "area_id": "area_vincom",
            "name": "Trung tâm thương mại Vincom Mega Mall",
            "short_name": "Vincom Mega Mall",
            "category": "commercial",
            "latitude": 20.9985,
            "longitude": 105.9525,
            "sensor_id": "S02",
            "is_interpolated": True,
            "source_sensors": ["S02", "S03"],
            "aliases": [
                "vincom", "vincom mega mall", "tttm vincom", "trung tâm thương mại vincom"
            ],
            "suitable_activities": ["dining_outdoor", "walking"],
            "description": "Khu trung tâm thương mại và ẩm thực sầm uất với luồng xe cộ ra vào.",
        },
        # 8. Khu Hải Âu
        {
            "id": "poi_hai_au",
            "area_id": "area_hai_au",
            "name": "Quảng trường & Tuyến phố Hải Âu",
            "short_name": "Khu Hải Âu",
            "category": "commercial",
            "latitude": 20.9910,
            "longitude": 105.9560,
            "sensor_id": "S05",
            "is_interpolated": False,
            "source_sensors": ["S05"],
            "aliases": [
                "hải âu", "hai au", "khu hải âu", "phân khu hải âu", "phố hải âu", "biệt thự hải âu"
            ],
            "suitable_activities": ["walking", "dining_outdoor"],
            "description": "Tuyến phố thương mại ven biển hồ sôi động về chiều tối.",
        },
        # 9. Khu Sao Biển
        {
            "id": "poi_sao_bien",
            "area_id": "area_sao_bien",
            "name": "Phân khu Biệt thự Sao Biển",
            "short_name": "Khu Sao Biển",
            "category": "residential",
            "latitude": 20.9985,
            "longitude": 105.9525,
            "sensor_id": "S03",
            "is_interpolated": True,
            "source_sensors": ["S03", "S05"],
            "aliases": [
                "sao biển", "sao bien", "khu sao biển", "phân khu sao biển", "biệt thự sao biển"
            ],
            "suitable_activities": ["walking", "elderly_stroll", "dining_outdoor"],
            "description": "Phân khu biệt thự ven hồ nước ngọt và biển hồ nước mặn với không gian thoáng đãng.",
        },
        # 10. Trục Đa Tốn
        {
            "id": "poi_da_ton",
            "area_id": "area_da_ton",
            "name": "Trục Đa Tốn & Cổng Tây Bắc",
            "short_name": "Trục Đa Tốn",
            "category": "traffic_gate",
            "latitude": 21.0008,
            "longitude": 105.9428,
            "sensor_id": "S01",
            "is_interpolated": False,
            "source_sensors": ["S01"],
            "aliases": [
                "đa tốn", "da ton", "trục đa tốn", "cổng đa tốn", "đường đa tốn"
            ],
            "suitable_activities": ["general"],
            "description": "Trục đường giao thông chính kết nối phía Tây Bắc khu đô thị.",
        },
        # 11. The Zenpark / Ruby
        {
            "id": "poi_zenpark_ruby",
            "area_id": "area_zenpark",
            "name": "Phân khu Căn hộ cao cấp The Zenpark (Ruby)",
            "short_name": "The Zenpark (Ruby)",
            "category": "residential",
            "latitude": 20.9940,
            "longitude": 105.9380,
            "sensor_id": "S01",
            "is_interpolated": True,
            "source_sensors": ["S01", "S02"],
            "aliases": [
                "zenpark", "the zenpark", "ruby", "khu ruby", "phân khu ruby", "the ruby"
            ],
            "suitable_activities": ["walking", "children_play", "running"],
            "description": "Phân khu căn hộ mang phong cách nghỉ dưỡng Nhật Bản với vườn hoa và cầu gỗ đỏ.",
        },
        # 12. The Pavilion / The Zurich
        {
            "id": "poi_pavilion_zurich",
            "area_id": "area_pavilion",
            "name": "Phân khu Căn hộ The Pavilion & The Zurich",
            "short_name": "The Pavilion",
            "category": "residential",
            "latitude": 20.9960,
            "longitude": 105.9390,
            "sensor_id": "S01",
            "is_interpolated": True,
            "source_sensors": ["S01", "S02"],
            "aliases": [
                "pavilion", "the pavilion", "zurich", "the zurich"
            ],
            "suitable_activities": ["walking", "children_play"],
            "description": "Phân khu căn hộ hiện đại mang phong cách ốc đảo sinh thái nhiệt đới.",
        },
        # 13. Vinschool Ocean Park
        {
            "id": "poi_vinschool",
            "area_id": "area_vinschool",
            "name": "Trường Liên cấp Vinschool Ocean Park",
            "short_name": "Vinschool Ocean Park",
            "category": "education",
            "latitude": 20.9965,
            "longitude": 105.9450,
            "sensor_id": "S02",
            "is_interpolated": True,
            "source_sensors": ["S02", "S03"],
            "aliases": [
                "vinschool", "trường vinschool", "truong vinschool", "trường học vinschool"
            ],
            "suitable_activities": ["walking", "children_play"],
            "description": "Hệ thống trường học liên cấp từ mầm non đến THPT với khuôn viên xanh.",
        },
        # 14. Vinmec Ocean Park
        {
            "id": "poi_vinmec",
            "area_id": "area_vinmec",
            "name": "Bệnh viện Đa khoa Quốc tế Vinmec Ocean Park",
            "short_name": "Vinmec Ocean Park",
            "category": "healthcare",
            "latitude": 20.9920,
            "longitude": 105.9440,
            "sensor_id": "S04",
            "is_interpolated": True,
            "source_sensors": ["S04", "S01"],
            "aliases": [
                "vinmec", "bệnh viện vinmec", "benh vien vinmec", "bv vinmec"
            ],
            "suitable_activities": ["walking"],
            "description": "Bệnh viện đa khoa quốc tế tiêu chuẩn 5 sao với không gian yên tĩnh và trong lành.",
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
    def interpolate_environment_at_point(
        cls,
        lat: float,
        lon: float,
        station_data_map: dict[str, dict[str, Any]],
        power: float = 2.0,
    ) -> dict[str, Any]:
        """
        Calculates Inverse Distance Weighting (IDW) environmental interpolation
        at any geographical coordinate from available ground station telemetry.
        """
        usable_stations = []
        for s_id, st in cls.STATIONS.items():
            env = station_data_map.get(s_id)
            if env is not None:
                dist = cls.calculate_distance_m(lat, lon, st["latitude"], st["longitude"])
                usable_stations.append((s_id, st, env, dist))

        if not usable_stations:
            return {
                "pm25": 25.0,
                "aqi": 75,
                "co2": 500.0,
                "noise_db": 50.0,
                "temperature": 27.0,
                "timestamp": None,
                "is_interpolated": True,
                "method": "idw_spatial_interpolation",
                "source_sensors": ["S01"],
            }

        # Sort by distance
        usable_stations.sort(key=lambda x: x[3])

        # If exactly on or very close to a station (< 15 meters)
        if usable_stations[0][3] <= 15.0:
            nearest_env = usable_stations[0][2]
            return {
                "pm25": float(nearest_env["pm25"]),
                "aqi": int(nearest_env["aqi"]),
                "co2": float(nearest_env["co2"]),
                "noise_db": float(nearest_env["noise_db"]),
                "temperature": float(nearest_env["temperature"]),
                "timestamp": nearest_env["timestamp"],
                "is_interpolated": False,
                "method": "direct_sensor_measurement",
                "source_sensors": [usable_stations[0][0]],
            }

        # IDW weighted sum
        weighted_pm25 = 0.0
        weighted_co2 = 0.0
        weighted_noise = 0.0
        weighted_temp = 0.0
        weight_sum = 0.0

        for s_id, st, env, dist in usable_stations:
            dist_km = max(dist / 1000.0, 0.0001)
            w = 1.0 / (dist_km ** power)
            weight_sum += w
            weighted_pm25 += w * float(env["pm25"])
            weighted_co2 += w * float(env["co2"])
            weighted_noise += w * float(env["noise_db"])
            weighted_temp += w * float(env["temperature"])

        interp_pm25 = weighted_pm25 / weight_sum if weight_sum > 0 else float(usable_stations[0][2]["pm25"])
        interp_co2 = weighted_co2 / weight_sum if weight_sum > 0 else float(usable_stations[0][2]["co2"])
        interp_noise = weighted_noise / weight_sum if weight_sum > 0 else float(usable_stations[0][2]["noise_db"])
        interp_temp = weighted_temp / weight_sum if weight_sum > 0 else float(usable_stations[0][2]["temperature"])

        computed_aqi = pm25_aqi(interp_pm25) or 50
        closest_sensors = [item[0] for item in usable_stations[:2]]

        return {
            "pm25": round(interp_pm25, 1),
            "aqi": computed_aqi,
            "co2": round(interp_co2, 0),
            "noise_db": round(interp_noise, 1),
            "temperature": round(interp_temp, 1),
            "timestamp": usable_stations[0][2]["timestamp"],
            "is_interpolated": True,
            "method": "idw_spatial_interpolation",
            "source_sensors": closest_sensors,
        }

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
        station_pm25_map: dict[str, float] | None = None,
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
            station_pm25_map=station_pm25_map,
        )

    @classmethod
    def find_poi_by_name(cls, query: str) -> dict[str, Any] | None:
        """
        Resolves a user inquiry string to a canonical POI entity using:
        1. Explicit station ID regex (S01 - S05)
        2. Alias matching with accent-insensitive normalization (ordered by length)
        3. POI name/short_name token and substring matching
        """
        if not query:
            return None

        q_raw = query.strip()
        q_norm = normalize_text(q_raw)

        # 1. Check for explicit station IDs (S01 - S05)
        station_match = re.search(r"\b(s0[1-5])\b", q_raw, re.IGNORECASE)
        if station_match:
            s_id = station_match.group(1).upper()
            st = cls.get_station(s_id)
            if st:
                for p in cls.POIS:
                    if p.get("sensor_id") == s_id and not p.get("is_interpolated"):
                        return p
                return {
                    "id": f"poi_{s_id.lower()}",
                    "area_id": st["area_id"],
                    "name": st["name"],
                    "short_name": st["name"],
                    "category": "traffic_gate",
                    "latitude": st["latitude"],
                    "longitude": st["longitude"],
                    "sensor_id": s_id,
                    "is_interpolated": False,
                    "source_sensors": [s_id],
                    "suitable_activities": ["general"],
                    "description": f"Trạm quan trắc {st['name']}",
                }

        # 2. Build alias search index sorted by longest alias first
        alias_entries = []
        for p in cls.POIS:
            for alias in p.get("aliases", []):
                norm_alias = normalize_text(alias)
                if norm_alias:
                    alias_entries.append((norm_alias, p))

        alias_entries.sort(key=lambda x: len(x[0]), reverse=True)

        for norm_alias, poi in alias_entries:
            pattern = r"\b" + re.escape(norm_alias) + r"\b"
            if re.search(pattern, q_norm) or norm_alias in q_norm:
                return poi

        # 3. Direct matching on short_name or name
        for p in cls.POIS:
            p_short_norm = normalize_text(p["short_name"])
            p_name_norm = normalize_text(p["name"])
            if p_short_norm and len(p_short_norm) >= 3 and p_short_norm in q_norm:
                return p
            if p_name_norm and len(p_name_norm) >= 3 and p_name_norm in q_norm:
                return p

        return None

    @classmethod
    def find_all_pois_in_query(cls, query: str) -> list[dict[str, Any]]:
        """
        Finds all distinct POIs mentioned in a query string (useful for comparisons).
        """
        if not query:
            return []

        q_norm = normalize_text(query)
        found_pois: list[dict[str, Any]] = []
        found_ids: set[str] = set()

        alias_entries = []
        for p in cls.POIS:
            for alias in p.get("aliases", []):
                norm_alias = normalize_text(alias)
                if norm_alias:
                    alias_entries.append((norm_alias, p))

        alias_entries.sort(key=lambda x: len(x[0]), reverse=True)

        for norm_alias, poi in alias_entries:
            if poi["id"] not in found_ids:
                pattern = r"\b" + re.escape(norm_alias) + r"\b"
                if re.search(pattern, q_norm) or norm_alias in q_norm:
                    found_pois.append(poi)
                    found_ids.add(poi["id"])

        return found_pois

    @classmethod
    def extract_location_in_query(cls, query: str) -> tuple[dict[str, Any] | None, str | None]:
        """
        Extracts location from user query with deterministic detection of unrecognized entities.
        Returns:
            (resolved_poi, None) if a known location was recognized.
            (None, unrecognized_location_name) if user explicitly asked for an unknown place.
            (None, None) if no specific location was mentioned.
        """
        if not query:
            return None, None

        # 1. Direct resolution against known POIs and aliases
        resolved = cls.find_poi_by_name(query)
        if resolved:
            return resolved, None

        q_raw = query.strip()
        q_norm = normalize_text(q_raw)

        # Stop words & general questions that must NEVER be parsed as a named place
        general_query_phrases = {
            "nao", "o dau", "dau", "cho nao", "khu nao", "khu vuc nao", "diem nao", "noi nao",
            "tuyen nao", "duong nao", "doan nao", "lo trinh nao", "cung duong nao",
            "day", "o day", "cho nay", "khu nay", "noi nay", "vi tri nay", "nay", "do", "kia",
            "the nao", "bao nhieu", "sao", "gi", "ra sao", "nhu the nao", "thi sao",
            "ocean park", "ocean park 1", "vinhomes", "vinhomes ocean park",
            "ngoai troi", "trong nha", "ha noi", "viet nam", "hien tai",
            "toi nay", "chieu nay", "sang nay", "ngay mai", "hom nay",
            "luc nay", "bay gio", "tam thoi", "co tot khong", "tot khong",
            "tot nhat", "o nhiem nhat", "sach nhat", "kem nhat", "xau nhat", "te nhat",
            "phu hop nhat", "it o nhiem nhat", "nhieu bui nhat", "chay bo", "di bo",
            "tap the thao", "tap the duc", "chay bo o dau", "di bo o dau",
        }

        # Check if entire query or core query is a general inquiry
        if any(q_norm == phrase or q_norm.startswith(phrase + " ") or q_norm.endswith(" " + phrase) for phrase in general_query_phrases):
            return None, None

        # Specific regex targeting prepositional location inquiries like "tại ABCXYZ", "ở khu ABCXYZ"
        patterns = [
            r"\b(?:tai|o|khu|phan khu|khu vuc|dia diem|tai khu)\s+([a-zA-Z0-9\s_]{2,30})",
        ]

        for pat in patterns:
            for match in re.finditer(pat, q_norm):
                candidate = match.group(1).strip()
                # Strip trailing auxiliary question suffixes
                candidate = re.sub(
                    r"\b(nao|o dau|dau|the nao|bao nhieu|co tot khong|tot khong|nhu the nao|sao|thi sao|hien tai|bay gio|ra sao|co tot|dang o nhiem|dang sach|tot nhat|o nhiem nhat)\b.*",
                    "",
                    candidate,
                ).strip()

                if not candidate or len(candidate) < 2:
                    continue

                if candidate in general_query_phrases:
                    continue

                if any(candidate == p for p in ["vuc nao", "vuc", "phan khu nao", "diem nao", "noi nao", "nay", "day"]):
                    continue

                # Check if candidate matches a known POI
                poi_match = cls.find_poi_by_name(candidate)
                if poi_match:
                    return poi_match, None

                # Return candidate as unrecognized location if it contains substantive words
                if len(candidate) >= 3 and not any(w in candidate for w in ["chay", "duong", "tuyen", "troi", "khi", "khong"]):
                    return None, candidate.title()

        return None, None

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

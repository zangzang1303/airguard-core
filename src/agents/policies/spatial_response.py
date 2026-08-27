from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

SpatialAnalysisMode = Literal["overview", "compare", "wind"]


@dataclass(frozen=True, slots=True)
class SpatialLocation:
    location_id: str
    name: str
    latitude: float
    longitude: float
    category: str


# Static geography is an allow-listed product catalog, not environmental evidence.
# Every environmental value associated with these coordinates is sampled from the
# validated spatial tool payload produced in the same Agent request.
SPATIAL_LOCATIONS: dict[str, SpatialLocation] = {
    "whale_square": SpatialLocation(
        "whale_square",
        "Quảng trường Cá Voi",
        20.9938,
        105.9485,
        "landmark",
    ),
    "coral_park": SpatialLocation(
        "coral_park",
        "Công viên San Hô",
        20.9935,
        105.9405,
        "park",
    ),
    "salt_lake": SpatialLocation(
        "salt_lake",
        "Biển Hồ Nước Mặn",
        20.9945,
        105.9585,
        "lake",
    ),
    "da_ton_road": SpatialLocation(
        "da_ton_road",
        "Trục Đa Tốn/đường vành đai",
        21.0008,
        105.9428,
        "traffic_source",
    ),
    "sapphire": SpatialLocation(
        "sapphire",
        "Khu căn hộ Sapphire",
        20.9975,
        105.9430,
        "residential",
    ),
    "ngoc_trai": SpatialLocation(
        "ngoc_trai",
        "Khu ven Hồ Ngọc Trai",
        20.9953,
        105.9500,
        "residential",
    ),
    "hai_au": SpatialLocation(
        "hai_au",
        "Khu Hải Âu",
        20.9910,
        105.9560,
        "residential",
    ),
    "an_dao": SpatialLocation(
        "an_dao",
        "Khu Biệt thự An Đào",
        20.9995,
        105.9415,
        "residential",
    ),
    "vinuni": SpatialLocation(
        "vinuni",
        "Khuôn viên VinUniversity",
        20.9898,
        105.9467,
        "campus",
    ),
    "sao_bien": SpatialLocation(
        "sao_bien",
        "Phân khu Sao Biển",
        20.9985,
        105.9525,
        "residential",
    ),
    "dao_ngoc_trai": SpatialLocation(
        "dao_ngoc_trai",
        "Phân khu Đảo Ngọc Trai",
        20.9960,
        105.9510,
        "residential",
    ),
    "zenpark_ruby": SpatialLocation(
        "zenpark_ruby",
        "Phân khu The Zenpark & Ruby",
        20.9965,
        105.9395,
        "residential",
    ),
    "pavilion_zurich": SpatialLocation(
        "pavilion_zurich",
        "Phân khu The Pavilion & The Zurich",
        20.9980,
        105.9385,
        "residential",
    ),
    "vincom": SpatialLocation(
        "vincom",
        "TTTM Vincom Mega Mall",
        20.9985,
        105.9525,
        "commercial",
    ),
    "vinschool": SpatialLocation(
        "vinschool",
        "Cụm Trường liên cấp Vinschool",
        20.9950,
        105.9450,
        "school",
    ),
    "vinmec": SpatialLocation(
        "vinmec",
        "Bệnh viện Vinmec Ocean Park",
        20.9915,
        105.9440,
        "hospital",
    ),
    "road_hai_dang": SpatialLocation(
        "road_hai_dang",
        "Đường Hải Đăng",
        20.9950,
        105.9421,
        "road",
    ),
    "road_dai_duong": SpatialLocation(
        "road_dai_duong",
        "Đường Đại Dương",
        20.9930,
        105.9440,
        "road",
    ),
    "road_san_ho": SpatialLocation(
        "road_san_ho",
        "Đường San Hô",
        20.9920,
        105.9480,
        "road",
    ),
    "road_sao_bien": SpatialLocation(
        "road_sao_bien",
        "Đường Sao Biển",
        20.9985,
        105.9525,
        "road",
    ),
    "road_ngoc_trai": SpatialLocation(
        "road_ngoc_trai",
        "Đường Ngọc Trai",
        20.9960,
        105.9510,
        "road",
    ),
    "road_bien_ho": SpatialLocation(
        "road_bien_ho",
        "Đường Biển Hồ",
        20.9940,
        105.9580,
        "road",
    ),
    "road_ly_thanh_tong": SpatialLocation(
        "road_ly_thanh_tong",
        "Đường Lý Thánh Tông",
        21.0015,
        105.9390,
        "road",
    ),
    "technopark": SpatialLocation(
        "technopark",
        "Tòa tháp TechnoPark",
        20.9890,
        105.9450,
        "office",
    ),
}

_ALIASES: tuple[tuple[str, str], ...] = (
    ("quang truong ca voi", "whale_square"),
    ("ca voi", "whale_square"),
    ("cong vien san ho", "coral_park"),
    ("ho san ho", "coral_park"),
    ("san ho 16", "road_san_ho"),
    ("san ho 6", "road_san_ho"),
    ("san ho 1", "road_san_ho"),
    ("truc san ho", "road_san_ho"),
    ("duong san ho", "road_san_ho"),
    ("san ho", "coral_park"),
    ("bien ho nuoc man", "salt_lake"),
    ("bien nuoc man", "salt_lake"),
    ("duong ven bien ho", "road_bien_ho"),
    ("duong bien ho", "road_bien_ho"),
    ("nuoc man", "salt_lake"),
    ("crystal lagoons", "salt_lake"),
    ("duong vanh dai", "da_ton_road"),
    ("truc da ton", "da_ton_road"),
    ("duong da ton", "da_ton_road"),
    ("vanh dai", "da_ton_road"),
    ("da ton", "da_ton_road"),
    ("khu can ho sapphire", "sapphire"),
    ("sapphire", "sapphire"),
    ("ho ngoc trai", "ngoc_trai"),
    ("duong ngoc trai", "road_ngoc_trai"),
    ("truc ngoc trai", "road_ngoc_trai"),
    ("dao ngoc trai", "dao_ngoc_trai"),
    ("ngoc trai", "ngoc_trai"),
    ("khu hai au", "hai_au"),
    ("hai au", "hai_au"),
    ("khu biet thu an dao", "an_dao"),
    ("biet thu an dao", "an_dao"),
    ("an dao", "an_dao"),
    ("vinuni", "vinuni"),
    ("vin university", "vinuni"),
    ("dai hoc vinuni", "vinuni"),
    ("duong sao bien", "road_sao_bien"),
    ("truc sao bien", "road_sao_bien"),
    ("sao bien 24", "road_sao_bien"),
    ("sao bien 6", "road_sao_bien"),
    ("sao bien 1", "road_sao_bien"),
    ("sao bien", "sao_bien"),
    ("zenpark", "zenpark_ruby"),
    ("the zenpark", "zenpark_ruby"),
    ("ruby", "zenpark_ruby"),
    ("pavilion", "pavilion_zurich"),
    ("zurich", "pavilion_zurich"),
    ("vincom", "vincom"),
    ("vinschool", "vinschool"),
    ("vinmec", "vinmec"),
    ("duong hai dang", "road_hai_dang"),
    ("truc hai dang", "road_hai_dang"),
    ("hai dang 8", "road_hai_dang"),
    ("hai dang 6", "road_hai_dang"),
    ("hai dang 5", "road_hai_dang"),
    ("hai dang 3", "road_hai_dang"),
    ("hai dang 2", "road_hai_dang"),
    ("hai dang 1", "road_hai_dang"),
    ("hai dang", "road_hai_dang"),
    ("duong dai duong", "road_dai_duong"),
    ("truc dai duong", "road_dai_duong"),
    ("dai duong 2", "road_dai_duong"),
    ("dai duong 1", "road_dai_duong"),
    ("dai duong", "road_dai_duong"),
    ("duong ly thanh tong", "road_ly_thanh_tong"),
    ("ly thanh tong", "road_ly_thanh_tong"),
    ("thap technopark", "technopark"),
    ("toa technopark", "technopark"),
    ("technopark tower", "technopark"),
    ("technopark", "technopark"),
)

_RESIDENTIAL_TARGETS = ("sapphire", "ngoc_trai", "hai_au")


def plain_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(
        character for character in normalized if unicodedata.category(character) != "Mn"
    )
    return without_marks.replace("đ", "d")


def resolve_spatial_location_ids(query: str) -> list[str]:
    plain = plain_text(query)
    first_positions: dict[str, int] = {}
    for alias, location_id in _ALIASES:
        position = plain.find(alias)
        if position >= 0:
            first_positions[location_id] = min(
                position,
                first_positions.get(location_id, position),
            )
    return [
        location_id
        for location_id, _position in sorted(
            first_positions.items(),
            key=lambda item: item[1],
        )
    ]


def is_spatial_query(query: str, location_ids: list[str]) -> bool:
    plain = plain_text(query)
    explicit_spatial = any(
        phrase in plain
        for phrase in (
            "ban do nhiet",
            "heatmap",
            "lan truyen",
            "phat tan",
            "phan bo o nhiem",
            "o nhiem khong gian",
            "xuoi gio",
            "nguoc gio",
        )
    )
    location_environmental = bool(location_ids) and any(
        phrase in plain
        for phrase in (
            "chat luong khong khi",
            "khong khi",
            "moi truong",
            "o nhiem",
            "aqi",
            "pm25",
            "pm2.5",
        )
    )
    location_comparison = len(location_ids) >= 2 and any(
        phrase in plain for phrase in ("so voi", "so sanh", "khac nhau", "khu nao", "sach hon", "o nhiem hon")
    )
    wind_dispersion = (
        "gio" in plain
        and "o nhiem" in plain
        and any(phrase in plain for phrase in ("tu ", "ve khu", "thoi", "lan"))
    )
    return explicit_spatial or location_environmental or location_comparison or wind_dispersion


def spatial_analysis_mode(query: str, location_ids: list[str]) -> SpatialAnalysisMode:
    plain = plain_text(query)
    if "gio" in plain and "o nhiem" in plain:
        return "wind"
    if len(location_ids) >= 2 or any(
        phrase in plain for phrase in ("so voi", "so sanh", "khu nao", "sach hon", "o nhiem hon")
    ):
        return "compare"
    return "overview"


def expand_spatial_locations_for_query(
    query: str,
    location_ids: list[str],
    mode: SpatialAnalysisMode,
) -> list[str]:
    expanded = list(location_ids)
    plain = plain_text(query)
    if mode == "wind" and any(
        phrase in plain for phrase in ("khu can ho nao", "khu dan cu nao", "can ho nao")
    ):
        for location_id in _RESIDENTIAL_TARGETS:
            if location_id not in expanded:
                expanded.append(location_id)
    return expanded


def get_spatial_location(location_id: str) -> SpatialLocation:
    try:
        return SPATIAL_LOCATIONS[location_id]
    except KeyError as exc:
        raise ValueError("unknown allow-listed spatial location") from exc


def nearest_grid_point(
    location: SpatialLocation,
    grid_points: list[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], float]:
    if not grid_points:
        raise ValueError("spatial grid is empty")
    point = min(
        grid_points,
        key=lambda item: _distance_km(
            location.latitude,
            location.longitude,
            float(item["lat"]),
            float(item["lon"]),
        ),
    )
    distance_km = _distance_km(
        location.latitude,
        location.longitude,
        float(point["lat"]),
        float(point["lon"]),
    )
    if distance_km > 1.0:
        raise ValueError("no spatial grid point is close enough to the requested location")
    return point, distance_km


def bearing_degrees(origin: SpatialLocation, target: SpatialLocation) -> float:
    origin_latitude = math.radians(origin.latitude)
    target_latitude = math.radians(target.latitude)
    longitude_delta = math.radians(target.longitude - origin.longitude)
    x = math.sin(longitude_delta) * math.cos(target_latitude)
    y = (
        math.cos(origin_latitude) * math.sin(target_latitude)
        - math.sin(origin_latitude)
        * math.cos(target_latitude)
        * math.cos(longitude_delta)
    )
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def angular_difference(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


def _distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_km = 6371.0
    latitude_delta = math.radians(latitude_b - latitude_a)
    longitude_delta = math.radians(longitude_b - longitude_a)
    latitude_a_rad = math.radians(latitude_a)
    latitude_b_rad = math.radians(latitude_b)
    haversine = (
        math.sin(latitude_delta / 2.0) ** 2
        + math.cos(latitude_a_rad)
        * math.cos(latitude_b_rad)
        * math.sin(longitude_delta / 2.0) ** 2
    )
    return earth_radius_km * 2.0 * math.atan2(
        math.sqrt(haversine),
        math.sqrt(1.0 - haversine),
    )

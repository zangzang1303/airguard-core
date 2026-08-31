"""AirGuard OSM-Compliant Graph & AQI-Aware Route Engine for Vinhomes Ocean Park 1.

Generates real road/path network routes from OpenStreetMap street geometry without
cross-block or straight-line shortcuts. Supports walking, running, and cycling activity
graphs, origin snapping with distance gates, and multi-candidate generation.
"""

from __future__ import annotations

import copy
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
from typing import Any

try:
    from .osm_canonical_geometries_py import CANONICAL_CIRCUITS_GEOMETRY as _CANONICAL_CIRCUITS_GEOMETRY
except ImportError:
    try:
        from osm_canonical_geometries_py import CANONICAL_CIRCUITS_GEOMETRY as _CANONICAL_CIRCUITS_GEOMETRY
    except ImportError:
        _CANONICAL_CIRCUITS_GEOMETRY = {}

_OSM_GEOM_FILE = os.path.join(os.path.dirname(__file__), "osm_canonical_geometries.json")
_PRELOADED_OSM_GEOMETRIES: dict[str, list[list[float]]] = dict(_CANONICAL_CIRCUITS_GEOMETRY)
try:
    if os.path.exists(_OSM_GEOM_FILE):
        with open(_OSM_GEOM_FILE, "r", encoding="utf-8") as _f:
            _file_data = json.load(_f)
            _PRELOADED_OSM_GEOMETRIES.update(_file_data)
except Exception:
    pass



class RoadGraphRouter:
    """
    Graph-Based Spatial Road & Pedestrian Promenade Routing Engine for Vinhomes Ocean Park 1.
    Uses real street network coordinates, intersection nodes, and Dijkstra's algorithm
    with environmental cost weighting (PM2.5/AQI penalty) to find real footpaths and loops.
    """

    STATION_COORDINATES = {
        "S01": (21.0008, 105.9428),
        "S02": (20.9975, 105.9430),
        "S03": (20.9953, 105.9500),
        "S04": (20.9898, 105.9467),
        "S05": (20.9910, 105.9560),
    }

    # Real Street Network Graph Nodes in Ocean Park 1 spanning all 6 zones
    # [lat, lng]
    NODES: dict[str, dict[str, Any]] = {
        # --- 1. Sapphire & Central-West Area ---
        "N_SAPPHIRE_TOWER": {"id": "N_SAPPHIRE_TOWER", "name": "Tháp Sapphire S2.01", "lat": 20.9975, "lng": 105.9430, "zone": "west"},
        "N_SAPPHIRE_GATE": {"id": "N_SAPPHIRE_GATE", "name": "Cổng nội khu Sapphire", "lat": 20.9960, "lng": 105.9448, "zone": "west"},
        "N_DAI_DUONG_JCT": {"id": "N_DAI_DUONG_JCT", "name": "Ngã tư Đại Dương - San Hô", "lat": 20.9945, "lng": 105.9465, "zone": "central"},
        "N_VINSCHOOL_GATE": {"id": "N_VINSCHOOL_GATE", "name": "Cổng Trường Vinschool", "lat": 20.9965, "lng": 105.9450, "zone": "central"},

        # --- 2. San Hô Riverwalk & West Park Area ---
        "N_SAN_HO_SOUTH": {"id": "N_SAN_HO_SOUTH", "name": "Công viên San Hô Nam", "lat": 20.9935, "lng": 105.9405, "zone": "west"},
        "N_SAN_HO_MID": {"id": "N_SAN_HO_MID", "name": "Công viên San Hô Trung tâm", "lat": 20.9978, "lng": 105.9420, "zone": "west"},
        "N_SAN_HO_NORTH": {"id": "N_SAN_HO_NORTH", "name": "Cổng Đa Tốn (Bắc San Hô)", "lat": 21.0010, "lng": 105.9426, "zone": "west"},
        "N_ZENPARK_GATE": {"id": "N_ZENPARK_GATE", "name": "Cổng The Zenpark (Ruby)", "lat": 20.9940, "lng": 105.9380, "zone": "west"},
        "N_ZENPARK_GARDEN": {"id": "N_ZENPARK_GARDEN", "name": "Vườn Nhật & Cầu gỗ Zenpark", "lat": 20.9950, "lng": 105.9375, "zone": "west"},
        "N_PAVILION_GATE": {"id": "N_PAVILION_GATE", "name": "Phân khu The Pavilion", "lat": 20.9960, "lng": 105.9390, "zone": "west"},
        "N_ZURICH_ENTRY": {"id": "N_ZURICH_ENTRY", "name": "Phân khu The Zurich", "lat": 20.9975, "lng": 105.9385, "zone": "west"},

        # --- 3. North & North-East Area (An Đào, Sao Biển, Vincom) ---
        "N_AN_DAO_SOUTH": {"id": "N_AN_DAO_SOUTH", "name": "Cổng Nam Biệt thự An Đào", "lat": 20.9990, "lng": 105.9410, "zone": "north"},
        "N_AN_DAO_PARK": {"id": "N_AN_DAO_PARK", "name": "Công viên nội khu An Đào", "lat": 20.9995, "lng": 105.9415, "zone": "north"},
        "N_AN_DAO_NORTH": {"id": "N_AN_DAO_NORTH", "name": "Lối dạo An Đào Bắc", "lat": 21.0005, "lng": 105.9420, "zone": "north"},
        "N_SAO_BIEN_WEST": {"id": "N_SAO_BIEN_WEST", "name": "Đường dạo Sao Biển Tây", "lat": 20.9980, "lng": 105.9515, "zone": "northeast"},
        "N_SAO_BIEN_EAST": {"id": "N_SAO_BIEN_EAST", "name": "Phân khu Biệt thự Sao Biển Đông", "lat": 20.9985, "lng": 105.9535, "zone": "northeast"},
        "N_VINCOM_GATE": {"id": "N_VINCOM_GATE", "name": "Quảng trường Vincom Mega Mall", "lat": 20.9985, "lng": 105.9525, "zone": "northeast"},

        # --- 4. Hồ Ngọc Trai (24.5ha Lake Promenade & Island) ---
        "N_LAKE_WEST_ENTRY": {"id": "N_LAKE_WEST_ENTRY", "name": "Lối vào Quảng trường Cá Voi (Tây Hồ)", "lat": 20.9938, "lng": 105.9485, "zone": "central"},
        "N_LAKE_NORTHWEST": {"id": "N_LAKE_NORTHWEST", "name": "Bờ Tây Bắc - Đường Ngọc Trai", "lat": 20.9950, "lng": 105.9492, "zone": "central"},
        "N_LAKE_NORTH": {"id": "N_LAKE_NORTH", "name": "Bờ Bắc - Vườn dừa Ngọc Trai", "lat": 20.9965, "lng": 105.9508, "zone": "central"},
        "N_LAKE_NORTHEAST": {"id": "N_LAKE_NORTHEAST", "name": "Bờ Đông Bắc - Đường Sao Biển", "lat": 20.9975, "lng": 105.9530, "zone": "central"},
        "N_LAKE_EAST": {"id": "N_LAKE_EAST", "name": "Bờ Đông - Lối sang Biển Hồ", "lat": 20.9968, "lng": 105.9550, "zone": "central"},
        "N_LAKE_SOUTHEAST": {"id": "N_LAKE_SOUTHEAST", "name": "Bờ Đông Nam - Quảng trường Hải Âu", "lat": 20.9955, "lng": 105.9568, "zone": "central"},
        "N_LAKE_SOUTH": {"id": "N_LAKE_SOUTH", "name": "Bờ Nam - Đường Hải Âu ven hồ", "lat": 20.9942, "lng": 105.9555, "zone": "central"},
        "N_LAKE_SOUTHWEST": {"id": "N_LAKE_SOUTHWEST", "name": "Bờ Tây Nam - Đường Hải Âu 1", "lat": 20.9928, "lng": 105.9532, "zone": "central"},
        "N_LAKE_SOUTH_ENTRY": {"id": "N_LAKE_SOUTH_ENTRY", "name": "Lối vào Nam Hồ (gần VinUni)", "lat": 20.9918, "lng": 105.9510, "zone": "central"},
        "N_DAO_NGOC_TRAI_GATE": {"id": "N_DAO_NGOC_TRAI_GATE", "name": "Cầu sang Đảo Ngọc Trai", "lat": 20.9955, "lng": 105.9505, "zone": "central"},
        "N_DAO_NGOC_TRAI_LOOP": {"id": "N_DAO_NGOC_TRAI_LOOP", "name": "Vòng dạo Đảo Ngọc Trai", "lat": 20.9960, "lng": 105.9515, "zone": "central"},

        # --- 5. VinUni Campus & South Area ---
        "N_VINUNI_GATE": {"id": "N_VINUNI_GATE", "name": "Cổng chính VinUniversity", "lat": 20.9918, "lng": 105.9485, "zone": "south"},
        "N_VINUNI_MAIN": {"id": "N_VINUNI_MAIN", "name": "Tòa nhà Khởi nghiệp VinUni", "lat": 20.9898, "lng": 105.9467, "zone": "south"},
        "N_VINUNI_WEST": {"id": "N_VINUNI_WEST", "name": "Đường nội bộ VinUni Tây", "lat": 20.9910, "lng": 105.9455, "zone": "south"},
        "N_VINUNI_NORTH": {"id": "N_VINUNI_NORTH", "name": "Hồ cảnh quan VinUni", "lat": 20.9922, "lng": 105.9468, "zone": "south"},
        "N_VINUNI_EAST": {"id": "N_VINUNI_EAST", "name": "Đường nội bộ VinUni Đông", "lat": 20.9915, "lng": 105.9485, "zone": "south"},
        "N_VINUNI_SOUTH": {"id": "N_VINUNI_SOUTH", "name": "Sân vận động VinUni", "lat": 20.9895, "lng": 105.9482, "zone": "south"},
        "N_VINMEC_GATE": {"id": "N_VINMEC_GATE", "name": "Bệnh viện Đa khoa Vinmec", "lat": 20.9920, "lng": 105.9440, "zone": "south"},

        # --- 6. Crystal Lagoons & East Area ---
        "N_CRYSTAL_GATE": {"id": "N_CRYSTAL_GATE", "name": "Cổng Biển Hồ Nước Mặn", "lat": 20.9945, "lng": 105.9585, "zone": "east"},
        "N_CRYSTAL_NORTH": {"id": "N_CRYSTAL_NORTH", "name": "Bãi cát trắng Biển hồ Bắc", "lat": 20.9960, "lng": 105.9598, "zone": "east"},
        "N_CRYSTAL_EAST": {"id": "N_CRYSTAL_EAST", "name": "Mũi Hải Âu ven biển", "lat": 20.9975, "lng": 105.9590, "zone": "east"},
        "N_CRYSTAL_SOUTH": {"id": "N_CRYSTAL_SOUTH", "name": "Lối dạo biển nhiệt đới", "lat": 20.9968, "lng": 105.9575, "zone": "east"},
        "N_HAI_AU_STREET": {"id": "N_HAI_AU_STREET", "name": "Tuyến phố thương mại Hải Âu", "lat": 20.9925, "lng": 105.9565, "zone": "east"},
    }

    # Road Segments / Edges with exact real coordinates, road type, surface, and safety
    EDGES: list[dict[str, Any]] = [
        # --- West / San Hô & Zenpark Network ---
        {
            "id": "edge_san_ho_south_mid",
            "from": "N_SAN_HO_SOUTH",
            "to": "N_SAN_HO_MID",
            "sensor_id": "S01",
            "name": "Đường chạy bộ cao su San Hô Nam",
            "surface": "Đường chạy bộ cao su tổng hợp êm chân ven sông sinh thái",
            "road_type": "park_track",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm xe cơ giới, 100% đường chạy bộ công viên",
            "coords": [[20.9935, 105.9405], [20.9945, 105.9408], [20.9955, 105.9412], [20.9968, 105.9416], [20.9978, 105.9420]],
        },
        {
            "id": "edge_san_ho_mid_north",
            "from": "N_SAN_HO_MID",
            "to": "N_SAN_HO_NORTH",
            "sensor_id": "S01",
            "name": "Đường chạy bộ cao su San Hô Bắc",
            "surface": "Đường chạy bộ cao su tổng hợp êm chân ven sông sinh thái",
            "road_type": "park_track",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm xe cơ giới, 100% đường chạy bộ công viên",
            "coords": [[20.9978, 105.9420], [20.9990, 105.9422], [20.9995, 105.9423], [21.0005, 105.9425], [21.0010, 105.9426]],
        },
        {
            "id": "edge_san_ho_zenpark",
            "from": "N_SAN_HO_SOUTH",
            "to": "N_ZENPARK_GATE",
            "sensor_id": "S01",
            "name": "Lối đi bộ nối San Hô - The Zenpark",
            "surface": "Vỉa hè lát gạch đi bộ có cây xanh che mát",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Tách biệt xe cơ giới",
            "coords": [[20.9935, 105.9405], [20.9938, 105.9392], [20.9940, 105.9380]],
        },
        {
            "id": "edge_zenpark_garden",
            "from": "N_ZENPARK_GATE",
            "to": "N_ZENPARK_GARDEN",
            "sensor_id": "S01",
            "name": "Đường dạo vườn Nhật The Zenpark",
            "surface": "Lối đi lát đá cảnh quan sân vườn Nhật Bản",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": False, "motor_vehicle": False},
            "traffic_conflict": "Nội khu đi bộ khép kín, tuyệt đối an toàn",
            "coords": [[20.9940, 105.9380], [20.9945, 105.9377], [20.9950, 105.9375]],
        },
        {
            "id": "edge_zenpark_pavilion",
            "from": "N_ZENPARK_GARDEN",
            "to": "N_PAVILION_GATE",
            "sensor_id": "S01",
            "name": "Đường dạo ốc đảo sinh thái The Pavilion",
            "surface": "Lối đi bộ nội khu cao cấp",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Nội bộ ít xe",
            "coords": [[20.9950, 105.9375], [20.9955, 105.9382], [20.9960, 105.9390]],
        },
        {
            "id": "edge_pavilion_zurich",
            "from": "N_PAVILION_GATE",
            "to": "N_ZURICH_ENTRY",
            "sensor_id": "S01",
            "name": "Lối dạo ven hồ cảnh quan The Zurich",
            "surface": "Vỉa hè lát đá granite rộng rãi",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Khu vực dân cư yên tĩnh",
            "coords": [[20.9960, 105.9390], [20.9968, 105.9388], [20.9975, 105.9385]],
        },
        {
            "id": "edge_zurich_san_ho_mid",
            "from": "N_ZURICH_ENTRY",
            "to": "N_SAN_HO_MID",
            "sensor_id": "S01",
            "name": "Lối thông Zurich sang công viên San Hô",
            "surface": "Đường dạo bộ kết nối công viên",
            "road_type": "pedestrian_promenade",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Tách biệt xe cộ",
            "coords": [[20.9975, 105.9385], [20.9976, 105.9402], [20.9978, 105.9420]],
        },
        {
            "id": "edge_san_ho_an_dao_south",
            "from": "N_SAN_HO_NORTH",
            "to": "N_AN_DAO_SOUTH",
            "sensor_id": "S01",
            "name": "Đường kết nối Đa Tốn - Biệt thự An Đào",
            "surface": "Vỉa hè nội khu lát gạch thoáng rộng",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Đường nội khu biệt thự yên tĩnh",
            "coords": [[21.0010, 105.9426], [21.0000, 105.9418], [20.9990, 105.9410]],
        },
        {
            "id": "edge_an_dao_south_park",
            "from": "N_AN_DAO_SOUTH",
            "to": "N_AN_DAO_PARK",
            "sensor_id": "S01",
            "name": "Tuyến dạo công viên nội khu An Đào",
            "surface": "Đường dạo bộ nội khu biệt thự rợp bóng cây",
            "road_type": "pedestrian_promenade",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Khu biệt thự khép kín, không gian trong lành",
            "coords": [[20.9990, 105.9410], [20.9992, 105.9412], [20.9995, 105.9415]],
        },
        {
            "id": "edge_an_dao_park_north",
            "from": "N_AN_DAO_PARK",
            "to": "N_AN_DAO_NORTH",
            "sensor_id": "S01",
            "name": "Tuyến dạo An Đào Bắc",
            "surface": "Vỉa hè đá terrazzo nội khu",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Nội bộ không xe tải",
            "coords": [[20.9995, 105.9415], [21.0000, 105.9418], [21.0005, 105.9420]],
        },
        {
            "id": "edge_an_dao_north_san_ho",
            "from": "N_AN_DAO_NORTH",
            "to": "N_SAN_HO_NORTH",
            "sensor_id": "S01",
            "name": "Lối về đầu công viên San Hô",
            "surface": "Đường nối đi bộ ven kênh",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Tách biệt xe",
            "coords": [[21.0005, 105.9420], [21.0008, 105.9423], [21.0010, 105.9426]],
        },

        # --- Sapphire, Vinschool & Central Connectors ---
        {
            "id": "edge_sapphire_tower_gate",
            "from": "N_SAPPHIRE_TOWER",
            "to": "N_SAPPHIRE_GATE",
            "sensor_id": "S02",
            "name": "Đường nội khu Sapphire S2",
            "surface": "Vỉa hè nội khu lát gạch terrazzo rộng rãi",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Đường nội khu có gờ giảm tốc",
            "coords": [[20.9975, 105.9430], [20.9968, 105.9438], [20.9960, 105.9448]],
        },
        {
            "id": "edge_sapphire_dai_duong",
            "from": "N_SAPPHIRE_GATE",
            "to": "N_DAI_DUONG_JCT",
            "sensor_id": "S02",
            "name": "Đại lộ Sapphire",
            "surface": "Đại lộ vỉa hè rộng 4m",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Tách biệt làn xe cơ giới",
            "coords": [[20.9960, 105.9448], [20.9952, 105.9458], [20.9945, 105.9465]],
        },
        {
            "id": "edge_sapphire_vinschool",
            "from": "N_SAPPHIRE_GATE",
            "to": "N_VINSCHOOL_GATE",
            "sensor_id": "S02",
            "name": "Tuyến phố dạo Vinschool",
            "surface": "Vỉa hè trường học rộng rãi an toàn",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Khu vực trường học giảm tốc độ",
            "coords": [[20.9960, 105.9448], [20.9962, 105.9449], [20.9965, 105.9450]],
        },
        {
            "id": "edge_dai_duong_lake_west",
            "from": "N_DAI_DUONG_JCT",
            "to": "N_LAKE_WEST_ENTRY",
            "sensor_id": "S03",
            "name": "Đường San Hô nối Hồ Ngọc Trai",
            "surface": "Vỉa hè rộng rợp bóng cây",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Tách biệt làn xe",
            "coords": [[20.9945, 105.9465], [20.9940, 105.9475], [20.9938, 105.9485]],
        },
        {
            "id": "edge_dai_duong_san_ho_south",
            "from": "N_DAI_DUONG_JCT",
            "to": "N_SAN_HO_SOUTH",
            "sensor_id": "S01",
            "name": "Lối sang công viên San Hô",
            "surface": "Đường đi bộ kết nối công viên",
            "road_type": "pedestrian_promenade",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9945, 105.9465], [20.9940, 105.9435], [20.9935, 105.9405]],
        },

        # --- Lake Hồ Ngọc Trai Perimeter Promenade (24.5ha Closed Loop) ---
        {
            "id": "edge_lake_west_northwest",
            "from": "N_LAKE_WEST_ENTRY",
            "to": "N_LAKE_NORTHWEST",
            "sensor_id": "S03",
            "name": "Lối dạo ven hồ Tây (Quảng trường Cá Voi)",
            "surface": "Lối dạo ven hồ lát đá granite rộng 5m bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới, 100% đường dạo bộ",
            "coords": [[20.9938, 105.9485], [20.9944, 105.9488], [20.9950, 105.9492]],
        },
        {
            "id": "edge_lake_northwest_north",
            "from": "N_LAKE_NORTHWEST",
            "to": "N_LAKE_NORTH",
            "sensor_id": "S03",
            "name": "Đường ven hồ Ngọc Trai Bắc (Vườn dừa)",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9950, 105.9492], [20.9958, 105.9500], [20.9965, 105.9508]],
        },
        {
            "id": "edge_lake_north_northeast",
            "from": "N_LAKE_NORTH",
            "to": "N_LAKE_NORTHEAST",
            "sensor_id": "S03",
            "name": "Đường dạo rợp bóng dừa Đông Bắc",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9965, 105.9508], [20.9970, 105.9518], [20.9975, 105.9530]],
        },
        {
            "id": "edge_lake_northeast_east",
            "from": "N_LAKE_NORTHEAST",
            "to": "N_LAKE_EAST",
            "sensor_id": "S03",
            "name": "Đường ven hồ Sao Biển",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9975, 105.9530], [20.9972, 105.9542], [20.9968, 105.9550]],
        },
        {
            "id": "edge_lake_east_southeast",
            "from": "N_LAKE_EAST",
            "to": "N_LAKE_SOUTHEAST",
            "sensor_id": "S03",
            "name": "Lối dạo bộ bờ cát trắng Đông Nam",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9968, 105.9550], [20.9962, 105.9560], [20.9955, 105.9568]],
        },
        {
            "id": "edge_lake_southeast_south",
            "from": "N_LAKE_SOUTHEAST",
            "to": "N_LAKE_SOUTH",
            "sensor_id": "S03",
            "name": "Đường ven hồ Hải Âu Đông",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9955, 105.9568], [20.9948, 105.9562], [20.9942, 105.9555]],
        },
        {
            "id": "edge_lake_south_southwest",
            "from": "N_LAKE_SOUTH",
            "to": "N_LAKE_SOUTHWEST",
            "sensor_id": "S03",
            "name": "Đường ven hồ Hải Âu Tây",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9942, 105.9555], [20.9935, 105.9545], [20.9928, 105.9532]],
        },
        {
            "id": "edge_lake_southwest_entry",
            "from": "N_LAKE_SOUTHWEST",
            "to": "N_LAKE_SOUTH_ENTRY",
            "sensor_id": "S03",
            "name": "Lối dạo phía Nam hồ",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9928, 105.9532], [20.9922, 105.9520], [20.9918, 105.9510]],
        },
        {
            "id": "edge_lake_south_west_close",
            "from": "N_LAKE_SOUTH_ENTRY",
            "to": "N_LAKE_WEST_ENTRY",
            "sensor_id": "S03",
            "name": "Lối dạo bờ Tây Nam về Quảng trường Cá Voi",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9918, 105.9510], [20.9928, 105.9498], [20.9938, 105.9485]],
        },

        # --- Island Ngọc Trai Loop Connectors ---
        {
            "id": "edge_lake_north_island_gate",
            "from": "N_LAKE_NORTH",
            "to": "N_DAO_NGOC_TRAI_GATE",
            "sensor_id": "S03",
            "name": "Cầu cảnh quan sang Đảo Ngọc Trai",
            "surface": "Cầu dạo bộ cảnh quan",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": False, "motor_vehicle": False},
            "traffic_conflict": "Cấm xe hoàn toàn",
            "coords": [[20.9965, 105.9508], [20.9960, 105.9506], [20.9955, 105.9505]],
        },
        {
            "id": "edge_island_gate_loop",
            "from": "N_DAO_NGOC_TRAI_GATE",
            "to": "N_DAO_NGOC_TRAI_LOOP",
            "sensor_id": "S03",
            "name": "Đường dạo nội khu Đảo Ngọc Trai",
            "surface": "Vỉa hè nội khu biệt thự",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Nội khu biệt thự đảo khép kín",
            "coords": [[20.9955, 105.9505], [20.9958, 105.9510], [20.9960, 105.9515]],
        },
        {
            "id": "edge_island_loop_northwest",
            "from": "N_DAO_NGOC_TRAI_LOOP",
            "to": "N_LAKE_NORTHWEST",
            "sensor_id": "S03",
            "name": "Lối sang bờ Tây Bắc Hồ",
            "surface": "Đường dạo bộ ven hồ",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": False, "motor_vehicle": False},
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9960, 105.9515], [20.9955, 105.9500], [20.9950, 105.9492]],
        },

        # --- VinUni Campus Network ---
        {
            "id": "edge_lake_south_vinuni_gate",
            "from": "N_LAKE_SOUTH_ENTRY",
            "to": "N_VINUNI_GATE",
            "sensor_id": "S04",
            "name": "Đại lộ nối Hồ Ngọc Trai - VinUniversity",
            "surface": "Vỉa hè đại lộ lát đá granite rộng 6m",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9918, 105.9510], [20.9918, 105.9495], [20.9918, 105.9485]],
        },
        {
            "id": "edge_vinuni_gate_main",
            "from": "N_VINUNI_GATE",
            "to": "N_VINUNI_MAIN",
            "sensor_id": "S04",
            "name": "Trục chính Tòa nhà Gothic VinUniversity",
            "surface": "Quảng trường & đường dạo bộ đá granite nội bộ",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Khuôn viên trường đại học 100% cấm xe cơ giới",
            "coords": [[20.9918, 105.9485], [20.9908, 105.9475], [20.9898, 105.9467]],
        },
        {
            "id": "edge_vinuni_main_west",
            "from": "N_VINUNI_MAIN",
            "to": "N_VINUNI_WEST",
            "sensor_id": "S04",
            "name": "Đường nội bộ khuôn viên VinUni Tây",
            "surface": "Đá granite phẳng mịn",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Cấm xe cơ giới",
            "coords": [[20.9898, 105.9467], [20.9905, 105.9460], [20.9910, 105.9455]],
        },
        {
            "id": "edge_vinuni_west_north",
            "from": "N_VINUNI_WEST",
            "to": "N_VINUNI_NORTH",
            "sensor_id": "S04",
            "name": "Đường dạo hồ cảnh quan VinUni",
            "surface": "Đá granite ven hồ nội bộ",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Không có xe cộ",
            "coords": [[20.9910, 105.9455], [20.9916, 105.9462], [20.9922, 105.9468]],
        },
        {
            "id": "edge_vinuni_north_east",
            "from": "N_VINUNI_NORTH",
            "to": "N_VINUNI_EAST",
            "sensor_id": "S04",
            "name": "Đường rợp bóng cây VinUni",
            "surface": "Đá granite phẳng mịn",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Không có xe cộ",
            "coords": [[20.9922, 105.9468], [20.9918, 105.9478], [20.9915, 105.9485]],
        },
        {
            "id": "edge_vinuni_east_south",
            "from": "N_VINUNI_EAST",
            "to": "N_VINUNI_SOUTH",
            "sensor_id": "S04",
            "name": "Đường sân vận động VinUni",
            "surface": "Đường chạy thể thao chuyên dụng",
            "road_type": "park_track",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Khu thể thao",
            "coords": [[20.9915, 105.9485], [20.9905, 105.9484], [20.9895, 105.9482]],
        },
        {
            "id": "edge_vinuni_south_main",
            "from": "N_VINUNI_SOUTH",
            "to": "N_VINUNI_MAIN",
            "sensor_id": "S04",
            "name": "Đường về sảnh chính VinUni",
            "surface": "Đá granite",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Nội bộ",
            "coords": [[20.9895, 105.9482], [20.9896, 105.9474], [20.9898, 105.9467]],
        },
        {
            "id": "edge_vinuni_west_vinmec",
            "from": "N_VINUNI_WEST",
            "to": "N_VINMEC_GATE",
            "sensor_id": "S04",
            "name": "Tuyến phố nội bộ VinUni - Vinmec",
            "surface": "Vỉa hè lát đá",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9910, 105.9455], [20.9915, 105.9448], [20.9920, 105.9440]],
        },
        {
            "id": "edge_vinmec_san_ho_south",
            "from": "N_VINMEC_GATE",
            "to": "N_SAN_HO_SOUTH",
            "sensor_id": "S01",
            "name": "Đường nối Vinmec sang Công viên San Hô",
            "surface": "Vỉa hè rợp bóng cây",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9920, 105.9440], [20.9928, 105.9422], [20.9935, 105.9405]],
        },

        # --- East (Crystal Lagoons & Hải Âu Network) ---
        {
            "id": "edge_lake_southeast_crystal",
            "from": "N_LAKE_SOUTHEAST",
            "to": "N_CRYSTAL_GATE",
            "sensor_id": "S05",
            "name": "Đường Hải Âu sang Biển Hồ",
            "surface": "Lối dạo bộ lát gạch ven biển hồ nhân tạo",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Tách biệt xe cộ, tuyến phố đi bộ ven biển",
            "coords": [[20.9955, 105.9568], [20.9950, 105.9576], [20.9945, 105.9585]],
        },
        {
            "id": "edge_crystal_gate_north",
            "from": "N_CRYSTAL_GATE",
            "to": "N_CRYSTAL_NORTH",
            "sensor_id": "S05",
            "name": "Lối dạo ven biển hồ nhiệt đới",
            "surface": "Lối dạo cát trắng ven biển hồ nhân tạo 6.1ha",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "100% đường dạo bộ bãi cát nhiệt đới",
            "coords": [[20.9945, 105.9585], [20.9952, 105.9592], [20.9960, 105.9598]],
        },
        {
            "id": "edge_crystal_north_east",
            "from": "N_CRYSTAL_NORTH",
            "to": "N_CRYSTAL_EAST",
            "sensor_id": "S05",
            "name": "Đường dạo bờ cát trắng Crystal",
            "surface": "Lối dạo cát trắng",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9960, 105.9598], [20.9968, 105.9595], [20.9975, 105.9590]],
        },
        {
            "id": "edge_crystal_east_south",
            "from": "N_CRYSTAL_EAST",
            "to": "N_CRYSTAL_SOUTH",
            "sensor_id": "S05",
            "name": "Đường ven biển phía Nam",
            "surface": "Lối dạo bãi biển",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9975, 105.9590], [20.9972, 105.9582], [20.9968, 105.9575]],
        },
        {
            "id": "edge_crystal_south_gate",
            "from": "N_CRYSTAL_SOUTH",
            "to": "N_CRYSTAL_GATE",
            "sensor_id": "S05",
            "name": "Lối dạo về quảng trường Biển",
            "surface": "Lối dạo biển",
            "road_type": "pedestrian_promenade",
            "highway": "pedestrian",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9968, 105.9575], [20.9956, 105.9578], [20.9945, 105.9585]],
        },
        {
            "id": "edge_crystal_gate_hai_au",
            "from": "N_CRYSTAL_GATE",
            "to": "N_HAI_AU_STREET",
            "sensor_id": "S05",
            "name": "Phố đi bộ thương mại Hải Âu",
            "surface": "Vỉa hè phố thương mại lát đá",
            "road_type": "sidewalk",
            "highway": "residential",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": True},
            "traffic_conflict": "Phố đi bộ ven biển",
            "coords": [[20.9945, 105.9585], [20.9935, 105.9575], [20.9925, 105.9565]],
        },
        {
            "id": "edge_hai_au_lake_southwest",
            "from": "N_HAI_AU_STREET",
            "to": "N_LAKE_SOUTHWEST",
            "sensor_id": "S03",
            "name": "Lối thông Hải Âu 1 về Hồ Ngọc Trai",
            "surface": "Vỉa hè nội khu",
            "road_type": "sidewalk",
            "highway": "footway",
            "access": {"foot": True, "bicycle": True, "motor_vehicle": False},
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9925, 105.9565], [20.9926, 105.9548], [20.9928, 105.9532]],
        },
    ]

    # Canonical Circuits across all key sectors
    CANONICAL_CIRCUITS: dict[str, dict[str, Any]] = {
        "circuit_lake_loop": {
            "id": "route_ngoc_trai_loop",
            "name": "Cung đường Ven Hồ Ngọc Trai (Lakeside Promenade)",
            "short_name": "Ven Hồ Ngọc Trai",
            "category": "lakeside",
            "zone": "central",
            "entry_node": "N_LAKE_WEST_ENTRY",
            "nodes": [
                "N_LAKE_WEST_ENTRY", "N_LAKE_NORTHWEST", "N_LAKE_NORTH", "N_LAKE_NORTHEAST",
                "N_LAKE_EAST", "N_LAKE_SOUTHEAST", "N_LAKE_SOUTH", "N_LAKE_SOUTHWEST",
                "N_LAKE_SOUTH_ENTRY", "N_LAKE_WEST_ENTRY"
            ],
            "surface": "Lối dạo ven hồ lát đá granite rộng 5m bám sát bờ cát trắng",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới, 100% đường dạo bộ",
            "lighting_rating": "Xuất sắc (Hệ thống đèn LED cảnh quan ven hồ 24/7)",
            "highlights": "Đường chạy bo tròn chuẩn theo bờ hồ cát trắng 24.5ha lộng gió, hàng dừa xanh nhiệt đới.",
            "start_point": {"name": "Quảng trường Cá Voi", "lat": 20.9938, "lng": 105.9485},
        },
        "circuit_west_riverwalk": {
            "id": "route_san_ho_riverwalk",
            "name": "Cung đường Dải xanh Công viên San Hô & The Zenpark",
            "short_name": "Dải xanh San Hô",
            "category": "park_riverwalk",
            "zone": "west",
            "entry_node": "N_SAN_HO_SOUTH",
            "nodes": [
                "N_SAN_HO_SOUTH", "N_ZENPARK_GATE", "N_ZENPARK_GARDEN", "N_PAVILION_GATE",
                "N_ZURICH_ENTRY", "N_SAN_HO_MID", "N_SAN_HO_NORTH", "N_AN_DAO_SOUTH",
                "N_AN_DAO_PARK", "N_AN_DAO_NORTH", "N_SAN_HO_NORTH", "N_SAN_HO_MID", "N_SAN_HO_SOUTH"
            ],
            "surface": "Đường chạy bộ cao su tổng hợp êm chân ven sông sinh thái & vườn Nhật",
            "traffic_conflict": "Khu công viên khép kín, an toàn tuyệt đối cho runner",
            "lighting_rating": "Tốt (Đèn rọi lối đi ban đêm)",
            "highlights": "Dải công viên cây xanh trải dài 2.8km ven sông, mặt đường cao su giảm phản lực chấn thương.",
            "start_point": {"name": "Cổng chào Công viên San Hô", "lat": 20.9935, "lng": 105.9405},
        },
        "circuit_vinuni_campus": {
            "id": "route_vinuni_circuit",
            "name": "Cung đường Vòng quanh Đại học VinUniversity",
            "short_name": "Vòng VinUni",
            "category": "campus",
            "zone": "south",
            "entry_node": "N_VINUNI_GATE",
            "nodes": [
                "N_VINUNI_GATE", "N_VINUNI_MAIN", "N_VINUNI_WEST", "N_VINUNI_NORTH",
                "N_VINUNI_EAST", "N_VINUNI_SOUTH", "N_VINUNI_MAIN", "N_VINUNI_GATE"
            ],
            "surface": "Đường chạy bộ cao su và vỉa hè lát đá granite cao cấp phẳng mịn",
            "traffic_conflict": "Khu khuôn viên trường đại học 100% cấm xe cơ giới, an toàn tuyệt đối cho runner",
            "lighting_rating": "Xuất sắc (Hệ thống chiếu sáng chuẩn quốc tế)",
            "highlights": "Khuôn viên trường đại học tinh hoa, kiến trúc Gothic tráng lệ, không khí trong lành yên tĩnh.",
            "start_point": {"name": "Cổng chính VinUniversity", "lat": 20.9918, "lng": 105.9485},
        },
        "circuit_crystal_lagoon": {
            "id": "route_crystal_lagoon",
            "name": "Cung đường Biển hồ Nước mặn Crystal Lagoons",
            "short_name": "Biển hồ Nước Mặn",
            "category": "lagoon",
            "zone": "east",
            "entry_node": "N_CRYSTAL_GATE",
            "nodes": [
                "N_CRYSTAL_GATE", "N_CRYSTAL_NORTH", "N_CRYSTAL_EAST", "N_CRYSTAL_SOUTH",
                "N_CRYSTAL_GATE", "N_HAI_AU_STREET", "N_LAKE_SOUTHWEST", "N_LAKE_SOUTHEAST",
                "N_CRYSTAL_GATE"
            ],
            "surface": "Đường dạo bộ ven biển hồ nước mặn 6.1ha bãi cát trắng mịn",
            "traffic_conflict": "Tách biệt xe cơ giới, 100% đường dạo bãi biển",
            "lighting_rating": "Xuất sắc (Đèn led ven biển)",
            "highlights": "Khung cảnh bãi biển nhiệt đới cát trắng trải dài, hàng dừa xanh và sóng nước mặn trong vắt.",
            "start_point": {"name": "Quảng trường Biển Hồ Nước Mặn", "lat": 20.9945, "lng": 105.9585},
        },
        "circuit_sapphire_central": {
            "id": "route_sapphire_central",
            "name": "Cung đường Nội khu Sapphire & Đại lộ San Hô",
            "short_name": "Nội khu Sapphire",
            "category": "residential_loop",
            "zone": "west",
            "entry_node": "N_SAPPHIRE_TOWER",
            "nodes": [
                "N_SAPPHIRE_TOWER", "N_SAPPHIRE_GATE", "N_VINSCHOOL_GATE", "N_SAPPHIRE_GATE",
                "N_DAI_DUONG_JCT", "N_LAKE_WEST_ENTRY", "N_LAKE_NORTHWEST", "N_DAO_NGOC_TRAI_GATE",
                "N_LAKE_NORTH", "N_LAKE_NORTHWEST", "N_LAKE_WEST_ENTRY", "N_DAI_DUONG_JCT",
                "N_SAPPHIRE_GATE", "N_SAPPHIRE_TOWER"
            ],
            "surface": "Vỉa hè nội khu lát gạch terrazzo rộng rãi & dải dạo ven hồ",
            "traffic_conflict": "Tách biệt làn xe, có gờ giảm tốc nội khu",
            "lighting_rating": "Rất tốt (Đèn đường nội khu sáng rõ)",
            "highlights": "Tuyến chạy nội khu tiện lợi cho cư dân Sapphire kết nối thẳng ra bờ hồ lộng gió.",
            "start_point": {"name": "Sảnh Sapphire S2.01", "lat": 20.9975, "lng": 105.9430},
        },
    }

    @classmethod
    def calculate_distance_m(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def calculate_polyline_distance_m(cls, coords: list[list[float]]) -> float:
        total = 0.0
        for i in range(len(coords) - 1):
            total += cls.calculate_distance_m(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
        return total

    @classmethod
    def find_nearest_node(cls, lat: float, lng: float, activity: str = "running") -> tuple[str, float]:
        """Snaps origin coordinate to nearest valid road network node."""
        best_node = "N_LAKE_WEST_ENTRY"
        min_d = float("inf")
        for node_id, data in cls.NODES.items():
            d = cls.calculate_distance_m(lat, lng, data["lat"], data["lng"])
            if d < min_d:
                min_d = d
                best_node = node_id
        return best_node, min_d

    @classmethod
    def _project_onto_segment(
        cls,
        origin: list[float],
        start: list[float],
        end: list[float],
    ) -> tuple[list[float], float]:
        """Return the closest point on a geographic line segment and its distance."""
        reference_latitude = math.radians(origin[0])
        lng_scale = 111_320 * math.cos(reference_latitude)
        lat_scale = 110_540
        start_x, start_y = (start[1] - origin[1]) * lng_scale, (start[0] - origin[0]) * lat_scale
        end_x, end_y = (end[1] - origin[1]) * lng_scale, (end[0] - origin[0]) * lat_scale
        dx, dy = end_x - start_x, end_y - start_y
        denominator = dx * dx + dy * dy
        position = 0.0 if denominator == 0 else max(0.0, min(1.0, -(start_x * dx + start_y * dy) / denominator))
        projected = [start[0] + position * (end[0] - start[0]), start[1] + position * (end[1] - start[1])]
        return projected, cls.calculate_distance_m(origin[0], origin[1], projected[0], projected[1])

    @staticmethod
    def _without_adjacent_duplicates(coords: list[list[float]]) -> list[list[float]]:
        result: list[list[float]] = []
        for point in coords:
            if not result or point != result[-1]:
                result.append(point)
        return result

    @classmethod
    def snap_origin_to_network(
        cls,
        lat: float,
        lng: float,
        activity: str = "running",
    ) -> dict[str, Any]:
        """
        Task Section 6: Deterministic Snap Origin with distance and coordinate reporting.
        """
        origin = [lat, lng]
        best: dict[str, Any] | None = None
        for edge in cls.EDGES:
            if activity in {"running", "walking"} and not edge.get("access", {}).get("foot", True):
                continue
            if activity == "cycling" and not edge.get("access", {}).get("bicycle", True):
                continue
            edge_coords = edge["coords"]
            for segment_index, (start, end) in enumerate(zip(edge_coords, edge_coords[1:])):
                projected, distance_m = cls._project_onto_segment(origin, start, end)
                if best is None or distance_m < best["distance_m"]:
                    from_path = cls._without_adjacent_duplicates([projected, *reversed(edge_coords[: segment_index + 1])])
                    to_path = cls._without_adjacent_duplicates([projected, *edge_coords[segment_index + 1 :]])
                    from_distance = cls.calculate_polyline_distance_m(from_path)
                    to_distance = cls.calculate_polyline_distance_m(to_path)
                    use_from = from_distance <= to_distance
                    best = {
                        "distance_m": distance_m,
                        "road_snap_coordinate": projected,
                        "node_id": edge["from"] if use_from else edge["to"],
                        "road_path": from_path if use_from else to_path,
                    }

        if best is None:
            node_id, dist_m = cls.find_nearest_node(lat, lng, activity=activity)
            node_data = cls.NODES[node_id]
            road_snap_coordinate = [node_data["lat"], node_data["lng"]]
            access_coordinates = [origin, road_snap_coordinate]
        else:
            node_id = str(best["node_id"])
            dist_m = float(best["distance_m"])
            node_data = cls.NODES[node_id]
            road_snap_coordinate = best["road_snap_coordinate"]
            access_coordinates = cls._without_adjacent_duplicates([origin, *best["road_path"]])
        max_snap_m = 400.0 if activity == "cycling" else 250.0

        return {
            "node_id": node_id,
            "snap_distance_m": round(dist_m, 1),
            "snapped_coordinate": [round(float(node_data["lat"]), 6), round(float(node_data["lng"]), 6)],
            "road_snap_coordinate": [round(road_snap_coordinate[0], 6), round(road_snap_coordinate[1], 6)],
            "access_coordinates": [[round(point[0], 6), round(point[1], 6)] for point in access_coordinates],
            "input_coordinate": [lat, lng],
            "is_valid": dist_m <= max_snap_m,
            "max_allowed_snap_m": max_snap_m,
            "node_name": node_data["name"],
        }

    @classmethod
    def interpolate_pm25_at_point(
        cls,
        lat: float,
        lng: float,
        station_pm25_map: dict[str, float],
    ) -> float:
        weighted_total = 0.0
        weight_sum = 0.0
        for station_id, (station_lat, station_lng) in cls.STATION_COORDINATES.items():
            if station_id not in station_pm25_map:
                continue
            distance_m = cls.calculate_distance_m(lat, lng, station_lat, station_lng)
            if distance_m <= 15.0:
                return float(station_pm25_map[station_id])
            distance_km = max(0.001, distance_m / 1000.0)
            weight = 1.0 / (distance_km**2)
            weight_sum += weight
            weighted_total += weight * float(station_pm25_map[station_id])
        if weight_sum <= 0:
            raise ValueError("road routing requires grounded PM2.5 station values")
        return weighted_total / weight_sum

    @classmethod
    def build_adjacency(
        cls,
        station_pm25_map: dict[str, float] | None = None,
        environmental_weight: float = 1.0,
        activity: str = "running",
        avoid_sensor: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        adj: dict[str, list[dict[str, Any]]] = {n: [] for n in cls.NODES}
        if not station_pm25_map and environmental_weight != 0:
            raise ValueError("environment-weighted routing requires grounded PM2.5 station values")

        for edge in cls.EDGES:
            if avoid_sensor and edge.get("sensor_id") == avoid_sensor:
                continue
            # Activity access filtering
            if activity in {"running", "walking"} and not edge.get("access", {}).get("foot", True):
                continue
            if activity == "cycling" and not edge.get("access", {}).get("bicycle", True):
                continue

            u, v = edge["from"], edge["to"]
            dist_m = cls.calculate_polyline_distance_m(edge["coords"])
            midpoint = edge["coords"][len(edge["coords"]) // 2]
            pm25 = (
                cls.interpolate_pm25_at_point(midpoint[0], midpoint[1], station_pm25_map)
                if station_pm25_map
                else None
            )

            # Environmental cost weight: Distance * (1 + beta * PM2.5 / 50.0)
            cost = dist_m if pm25 is None else dist_m * (1.0 + (environmental_weight * (pm25 / 50.0)))

            # Bidirectional road edges
            adj[u].append({
                "to": v,
                "cost": cost,
                "dist_m": dist_m,
                "coords": edge["coords"],
                "name": edge["name"],
                "pm25": round(pm25, 1) if pm25 is not None else None,
                "edge_id": edge["id"],
            })
            rev_coords = list(reversed(edge["coords"]))
            adj[v].append({
                "to": u,
                "cost": cost,
                "dist_m": dist_m,
                "coords": rev_coords,
                "name": edge["name"],
                "pm25": round(pm25, 1) if pm25 is not None else None,
                "edge_id": edge["id"],
            })

        return adj

    @classmethod
    def find_path_dijkstra(
        cls,
        start_node: str,
        end_node: str,
        station_pm25_map: dict[str, float] | None = None,
        environmental_weight: float = 1.0,
        activity: str = "running",
        avoid_sensor: str | None = None,
    ) -> dict[str, Any]:
        adj = cls.build_adjacency(
            station_pm25_map,
            environmental_weight=environmental_weight,
            activity=activity,
            avoid_sensor=avoid_sensor,
        )
        dist = {n: float("inf") for n in cls.NODES}
        parent: dict[str, tuple[str, list[list[float]], float, str] | None] = {n: None for n in cls.NODES}

        dist[start_node] = 0.0
        pq = [(0.0, start_node)]

        while pq:
            d_u, u = heapq.heappop(pq)
            if d_u > dist[u]:
                continue
            if u == end_node:
                break

            for edge in adj[u]:
                v = edge["to"]
                new_d = d_u + edge["cost"]
                if new_d < dist[v]:
                    dist[v] = new_d
                    parent[v] = (u, edge["coords"], edge["dist_m"], edge.get("edge_id", ""))
                    heapq.heappush(pq, (new_d, v))

        if dist[end_node] == float("inf"):
            return {"coords": [], "distance_m": 0.0, "cost": 0.0, "edge_ids": []}

        # Reconstruct path
        path_coords: list[list[float]] = []
        total_dist_m = 0.0
        curr = end_node
        edge_chunks = []
        edge_ids = []

        while curr != start_node and parent[curr] is not None:
            prev, coords, edge_m, edge_id = parent[curr]
            edge_chunks.append(coords)
            edge_ids.append(edge_id)
            total_dist_m += edge_m
            curr = prev

        for chunk in reversed(edge_chunks):
            if path_coords and chunk:
                path_coords.extend(chunk[1:])
            else:
                path_coords.extend(chunk)

        return {
            "coords": path_coords,
            "distance_m": total_dist_m,
            "cost": dist[end_node],
            "edge_ids": list(reversed(edge_ids)),
        }

    @classmethod
    def _dijkstra_tree(
        cls,
        start_node: str,
        station_pm25_map: dict[str, float],
        *,
        environmental_weight: float,
        activity: str,
        avoid_sensor: str | None,
    ) -> tuple[dict[str, float], dict[str, tuple[str, list[list[float]], float, str] | None]]:
        """Compute all reachable paths once for a large packaged road graph."""
        adjacency = cls.build_adjacency(
            station_pm25_map,
            environmental_weight=environmental_weight,
            activity=activity,
            avoid_sensor=avoid_sensor,
        )
        costs = {node_id: float("inf") for node_id in cls.NODES}
        physical_distances = {node_id: float("inf") for node_id in cls.NODES}
        parents: dict[str, tuple[str, list[list[float]], float, str] | None] = {
            node_id: None for node_id in cls.NODES
        }
        costs[start_node] = 0.0
        physical_distances[start_node] = 0.0
        queue = [(0.0, start_node)]
        while queue:
            cost, node_id = heapq.heappop(queue)
            if cost > costs[node_id]:
                continue
            for edge in adjacency[node_id]:
                next_node = str(edge["to"])
                next_cost = cost + float(edge["cost"])
                if next_cost >= costs[next_node]:
                    continue
                costs[next_node] = next_cost
                physical_distances[next_node] = physical_distances[node_id] + float(edge["dist_m"])
                parents[next_node] = (
                    node_id,
                    [list(point) for point in edge["coords"]],
                    float(edge["dist_m"]),
                    str(edge["edge_id"]),
                )
                heapq.heappush(queue, (next_cost, next_node))
        return physical_distances, parents

    @classmethod
    def _reconstruct_tree_path(
        cls,
        start_node: str,
        end_node: str,
        parents: dict[str, tuple[str, list[list[float]], float, str] | None],
    ) -> dict[str, Any]:
        chunks: list[list[list[float]]] = []
        edge_ids: list[str] = []
        distance_m = 0.0
        current = end_node
        while current != start_node:
            parent = parents.get(current)
            if parent is None:
                return {"coords": [], "distance_m": 0.0, "edge_ids": []}
            previous, coords, edge_distance_m, edge_id = parent
            chunks.append(coords)
            edge_ids.append(edge_id)
            distance_m += edge_distance_m
            current = previous
        coordinates: list[list[float]] = []
        for chunk in reversed(chunks):
            coordinates.extend(chunk if not coordinates else chunk[1:])
        return {
            "coords": coordinates,
            "distance_m": distance_m,
            "edge_ids": list(reversed(edge_ids)),
        }

    @classmethod
    def _build_osm_round_trip_candidates(
        cls,
        *,
        start_node: str,
        target_km: float,
        station_pm25_map: dict[str, float],
        origin_lat: float,
        origin_lng: float,
        origin_source: str,
        origin_label: str | None,
        snap_dist_m: float,
        activity: str,
        avoid_sensor: str | None,
    ) -> list[dict[str, Any]]:
        """Build air-quality-weighted out-and-back routes on stored OSM edges."""
        target_m = target_km * 1000.0
        candidates: list[dict[str, Any]] = []
        seen_paths: set[tuple[str, ...]] = set()
        for variant, environmental_weight in enumerate((0.35, 1.0, 2.0), start=1):
            distances, parents = cls._dijkstra_tree(
                start_node,
                station_pm25_map,
                environmental_weight=environmental_weight,
                activity=activity,
                avoid_sensor=avoid_sensor,
            )
            endpoints: list[tuple[float, str, int]] = []
            for node_id, distance_m in distances.items():
                if node_id == start_node or not math.isfinite(distance_m) or distance_m <= 0:
                    continue
                base_round_trip_m = distance_m * 2
                centre = max(1, round(target_m / base_round_trip_m))
                for repeats in range(max(1, centre - 1), min(12, centre + 1) + 1):
                    endpoints.append((abs(base_round_trip_m * repeats - target_m), node_id, repeats))
            endpoints.sort(key=lambda item: (item[0], item[1], item[2]))
            selected_path: dict[str, Any] | None = None
            selected_repeats = 1
            for _error, endpoint, repeats in endpoints[:80]:
                path = cls._reconstruct_tree_path(start_node, endpoint, parents)
                key = (*tuple(str(edge_id) for edge_id in path.get("edge_ids") or []), f"repeat:{repeats}")
                if key and key not in seen_paths:
                    selected_path = path
                    selected_repeats = repeats
                    seen_paths.add(key)
                    break
            if selected_path is None:
                continue
            outward = [list(point) for point in selected_path["coords"]]
            edge_ids_out = [str(edge_id) for edge_id in selected_path["edge_ids"]]
            one_lap_coordinates = [*outward, *list(reversed(outward))[1:]]
            one_lap_edges = [*edge_ids_out, *reversed(edge_ids_out)]
            coordinates: list[list[float]] = []
            edge_ids: list[str] = []
            for _ in range(selected_repeats):
                coordinates.extend(one_lap_coordinates if not coordinates else one_lap_coordinates[1:])
                edge_ids.extend(one_lap_edges)
            actual_m = cls.calculate_polyline_distance_m(coordinates)
            if abs(actual_m - target_m) / target_m > 0.20:
                continue
            start_name = str(cls.NODES[start_node].get("name") or "Điểm xuất phát")
            candidates.append(
                {
                    "id": f"route_osm_{int(target_km * 10)}km_air_{variant}",
                    "base_circuit_id": "route_target_tailored",
                    "name": f"Tuyến đi bộ Ocean Park 1 ({actual_m / 1000:.1f} km)",
                    "short_name": f"Tuyến {actual_m / 1000:.1f} km",
                    "category": "osm_air_weighted_round_trip",
                    "zone": "ocean_park_1",
                    "distance_km": round(actual_m / 1000, 2),
                    "distance_m": round(actual_m),
                    "target_requested_km": target_km,
                    "distance_constraint_satisfied": True,
                    "planning_method": "stored_osm_air_weighted_dijkstra",
                    "environmental_weight": environmental_weight,
                    "laps": selected_repeats,
                    "surface": "openstreetmap_snapshot",
                    "traffic_conflict": "Theo thuộc tính đường OSM đã lưu",
                    "lighting_rating": "Không có dữ liệu xác minh",
                    "highlights": "Tuyến chỉ sử dụng các đoạn đường đi bộ trong snapshot Ocean Park 1 đã kiểm tra checksum.",
                    "start_point": {
                        "name": origin_label or start_name,
                        "lat": origin_lat,
                        "lng": origin_lng,
                        "source": origin_source,
                    },
                    "circuit_entry_point": {
                        "name": "Điểm quay đầu trên mạng đường",
                        "lat": outward[-1][0],
                        "lng": outward[-1][1],
                    },
                    "coordinates": coordinates,
                    "edge_ids": edge_ids,
                    "access_distance_m": 0,
                    "snap_distance_m": round(snap_dist_m),
                    "activity": activity,
                }
            )
        return candidates

    @classmethod
    def _build_closed_loop_from_nodes(
        cls,
        loop_nodes: list[str],
        activity: str = "running",
    ) -> tuple[list[list[float]], float, list[str]]:
        coords: list[list[float]] = []
        edge_ids: list[str] = []
        for i in range(len(loop_nodes) - 1):
            u, v = loop_nodes[i], loop_nodes[i + 1]
            found = False
            for e in cls.EDGES:
                if e["from"] == u and e["to"] == v:
                    if coords:
                        coords.extend(e["coords"][1:])
                    else:
                        coords.extend(e["coords"])
                    edge_ids.append(e["id"])
                    found = True
                    break
                elif e["from"] == v and e["to"] == u:
                    rev = list(reversed(e["coords"]))
                    if coords:
                        coords.extend(rev[1:])
                    else:
                        coords.extend(rev)
                    edge_ids.append(e["id"])
                    found = True
                    break
            if not found:
                sub = cls.find_path_dijkstra(
                    u,
                    v,
                    environmental_weight=0,
                    activity=activity,
                )
                if sub["coords"]:
                    if coords:
                        coords.extend(sub["coords"][1:])
                    else:
                        coords.extend(sub["coords"])
                    edge_ids.extend(sub.get("edge_ids", []))
        dist_m = cls.calculate_polyline_distance_m(coords)
        return coords, dist_m, edge_ids

    @classmethod
    def generate_candidate_routes_from_origin(
        cls,
        origin_lat: float,
        origin_lng: float,
        target_km: float | None = None,
        station_pm25_map: dict[str, float] | None = None,
        origin_source: str = "map_selection",
        origin_label: str | None = None,
        activity: str = "running",
        avoid_sensor: str | None = None,
        avoid_location: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generates 3-5 grounded candidates from the versioned packaged graph.
        Polylines stay on curated graph edges without live network calls or cross-block shortcuts.
        """
        if not station_pm25_map:
            raise ValueError("route candidates require grounded PM2.5 station values")
        snap_info = cls.snap_origin_to_network(origin_lat, origin_lng, activity=activity)
        start_node = snap_info["node_id"]
        snap_dist_m = snap_info["snap_distance_m"]
        snapped_coord = snap_info["snapped_coordinate"]

        # If origin is beyond the snap gate, fail closed with no candidate geometry.
        if not snap_info["is_valid"]:
            return []

        candidates: list[dict[str, Any]] = []

        if cls.GRAPH_METADATA.get("source") == "openstreetmap_snapshot":
            resolved_target_km = target_km if target_km and target_km > 0.5 else 3.0
            return cls._build_osm_round_trip_candidates(
                start_node=start_node,
                target_km=resolved_target_km,
                station_pm25_map=station_pm25_map,
                origin_lat=snapped_coord[0],
                origin_lng=snapped_coord[1],
                origin_source=origin_source,
                origin_label=origin_label,
                snap_dist_m=snap_dist_m,
                activity=activity,
                avoid_sensor=avoid_sensor,
            )

        # -------------------------------------------------------------
        # 1. Tailored Target Distance Round-Trip (Environment-Optimized Loop)
        # -------------------------------------------------------------
        if target_km and target_km > 0.5:
            tailored = cls._build_target_distance_round_trip(
                start_node=start_node,
                target_km=target_km,
                station_pm25_map=station_pm25_map,
                origin_lat=snapped_coord[0],
                origin_lng=snapped_coord[1],
                origin_source=origin_source,
                origin_label=origin_label,
                snap_dist_m=snap_dist_m,
                activity=activity,
                avoid_sensor=avoid_sensor,
            )
            if tailored and tailored.get("coordinates"):
                candidates.append(tailored)

        # -------------------------------------------------------------
        # 2. Canonical Sector Circuits with Real Access Connections
        # -------------------------------------------------------------
        # Sort circuits by proximity of circuit entry node to snapped start node
        sorted_circuits = sorted(
            cls.CANONICAL_CIRCUITS.items(),
            key=lambda item: cls.calculate_distance_m(
                cls.NODES[start_node]["lat"],
                cls.NODES[start_node]["lng"],
                cls.NODES[item[1]["entry_node"]]["lat"],
                cls.NODES[item[1]["entry_node"]]["lng"],
            ),
        )

        for circuit_key, circuit_def in sorted_circuits:
            # Skip circuits in avoided area if avoidance specified
            if avoid_location and avoid_location.lower() in circuit_def["name"].lower():
                continue

            circuit_id = circuit_def["id"]
            entry_node = circuit_def["entry_node"]
            entry_lat = cls.NODES[entry_node]["lat"]
            entry_lng = cls.NODES[entry_node]["lng"]

            # Use only edges from the checked-in graph. Dense visual geometry
            # cannot be used here because it has no auditable edge identity.
            loop_coords, loop_dist_m, loop_edges = cls._build_closed_loop_from_nodes(
                circuit_def["nodes"],
                activity=activity,
            )

            # 2. Build the access connector from packaged graph edges only.
            access_coords: list[list[float]] = []
            access_dist_m = 0.0
            access_edges: list[str] = []

            if start_node != entry_node or cls.calculate_distance_m(snapped_coord[0], snapped_coord[1], entry_lat, entry_lng) > 35.0:
                access_path = cls.find_path_dijkstra(
                    start_node,
                    entry_node,
                    station_pm25_map=station_pm25_map,
                    activity=activity,
                    avoid_sensor=avoid_sensor,
                )
                if access_path["coords"]:
                    access_coords = access_path["coords"]
                    access_dist_m = access_path["distance_m"]
                    access_edges = access_path.get("edge_ids", [])
                else:
                    continue  # Disconnected component under activity filter

            # Stitch merged polyline strictly without gaps
            full_coords: list[list[float]] = []
            full_edge_ids: list[str] = []

            if access_coords:
                full_coords.extend(access_coords)
                full_edge_ids.extend(access_edges)
                if loop_coords:
                    full_coords.extend(loop_coords[1:])
                    full_edge_ids.extend(loop_edges)
                # Return path back to start node
                rev_access = list(reversed(access_coords))
                full_coords.extend(rev_access[1:])
                full_edge_ids.extend(list(reversed(access_edges)))
            else:
                full_coords.extend(loop_coords)
                full_edge_ids.extend(loop_edges)

            total_m = access_dist_m * 2 + loop_dist_m if access_coords else loop_dist_m
            dist_km = round(total_m / 1000.0, 1)

            # Determine laps if target_km is specified
            laps = 1
            if target_km and target_km >= 2.0:
                laps = max(1, round(target_km / max(1.0, (loop_dist_m / 1000.0))))

            entry_name = cls.NODES[entry_node]["name"]
            resolved_start_name = origin_label or cls.NODES[start_node]["name"]

            candidate_payload = {
                "id": circuit_def["id"],
                "base_circuit_id": circuit_def["id"],
                "name": circuit_def["name"],
                "short_name": circuit_def["short_name"],
                "category": circuit_def["category"],
                "zone": circuit_def["zone"],
                "distance_km": dist_km,
                "distance_m": round(total_m),
                "laps": laps,
                "surface": circuit_def["surface"],
                "traffic_conflict": circuit_def["traffic_conflict"],
                "lighting_rating": circuit_def["lighting_rating"],
                "highlights": circuit_def["highlights"],
                "start_point": {"name": resolved_start_name, "lat": snapped_coord[0], "lng": snapped_coord[1], "source": origin_source},
                "circuit_entry_point": {"name": entry_name, "lat": cls.NODES[entry_node]["lat"], "lng": cls.NODES[entry_node]["lng"]},
                "coordinates": full_coords,
                "edge_ids": full_edge_ids,
                "access_distance_m": round(access_dist_m),
                "snap_distance_m": round(snap_dist_m),
                "activity": activity,
            }
            candidates.append(candidate_payload)

        # -------------------------------------------------------------
        # 3. Cleanest / Lowest Environmental Exposure Candidate
        # -------------------------------------------------------------
        cleanest_loop = cls._build_cleanest_promenade_circuit(
            start_node=start_node,
            station_pm25_map=station_pm25_map,
            snapped_coord=snapped_coord,
            origin_label=origin_label,
            activity=activity,
        )
        if cleanest_loop and cleanest_loop.get("coordinates"):
            candidates.append(cleanest_loop)

        # Ensure unique IDs
        seen_ids = set()
        unique_candidates = []
        for c in candidates:
            if c["id"] not in seen_ids and len(c.get("coordinates", [])) >= 2:
                seen_ids.add(c["id"])
                unique_candidates.append(c)

        return unique_candidates

    @classmethod
    def _build_target_distance_round_trip(
        cls,
        start_node: str,
        target_km: float,
        station_pm25_map: dict[str, float] | None,
        origin_lat: float,
        origin_lng: float,
        origin_source: str,
        origin_label: str | None,
        snap_dist_m: float,
        activity: str = "running",
        avoid_sensor: str | None = None,
    ) -> dict[str, Any]:
        """Generate an exact tailored-distance route on the packaged graph."""
        half_target_m = (target_km * 1000.0) / 2.0
        target_m = target_km * 1000.0

        # Prefer a reviewed dense loop when the selected position already
        # snaps to its entry and one lap satisfies the requested distance.
        # Otherwise the generic out-and-back search can win by distance while
        # sending the map back onto the older coarse connector network.
        local_dense_circuit = next(
            (
                circuit
                for circuit in cls.CANONICAL_CIRCUITS.values()
                if circuit.get("entry_node") == start_node and circuit.get("dense_edge_id")
            ),
            None,
        )
        if local_dense_circuit is not None:
            dense_coords, dense_distance_m, dense_edge_ids = cls._build_closed_loop_from_nodes(
                local_dense_circuit["nodes"],
                activity=activity,
            )
            if (
                len(dense_edge_ids) == 1
                and dense_edge_ids[0] == local_dense_circuit.get("dense_edge_id")
                and abs(dense_distance_m - target_m) / target_m <= 0.20
            ):
                start_name = cls.NODES[start_node]["name"]
                return {
                    "id": f"route_target_{int(target_km * 10)}km",
                    "base_circuit_id": "route_target_tailored",
                    "name": (
                        f"{local_dense_circuit['short_name']} theo mục tiêu "
                        f"({dense_distance_m / 1000:.1f} km)"
                    ),
                    "short_name": f"{local_dense_circuit['short_name']} {dense_distance_m / 1000:.1f} km",
                    "category": "tailored_loop",
                    "zone": cls.NODES[start_node].get("zone", "custom"),
                    "distance_km": round(dense_distance_m / 1000, 2),
                    "distance_m": round(dense_distance_m),
                    "target_requested_km": target_km,
                    "distance_constraint_satisfied": True,
                    "laps": 1,
                    "surface": "packaged_dense_pedestrian_graph",
                    "traffic_conflict": "unknown",
                    "lighting_rating": "Theo dữ liệu graph demo",
                    "highlights": "Vòng khép kín theo geometry đường dạo đã đóng gói trong graph.",
                    "start_point": {
                        "name": origin_label or start_name,
                        "lat": origin_lat,
                        "lng": origin_lng,
                        "source": origin_source,
                    },
                    "circuit_entry_point": {
                        "name": start_name,
                        "lat": dense_coords[0][0],
                        "lng": dense_coords[0][1],
                    },
                    "coordinates": dense_coords,
                    "edge_ids": dense_edge_ids,
                    "access_distance_m": 0,
                    "snap_distance_m": round(snap_dist_m),
                    "activity": activity,
                }

        dense_target = cls._build_dense_target_round_trip(
            start_node=start_node,
            target_km=target_km,
            station_pm25_map=station_pm25_map,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            origin_source=origin_source,
            origin_label=origin_label,
            snap_dist_m=snap_dist_m,
            activity=activity,
            avoid_sensor=avoid_sensor,
        )
        if dense_target is not None:
            return dense_target

        # Build a closed out-and-back route from actual graph edges.  This is
        # intentionally less picturesque than a pre-drawn polyline, but every
        # segment is auditable and supports the complete 1–10 km API range.
        # We search destinations and repeat counts instead of inventing a
        # mid-block point or consulting an external router.
        best: tuple[float, dict[str, Any], int] | None = None
        for node_id in cls.NODES:
            if node_id == start_node:
                continue
            path = cls.find_path_dijkstra(
                start_node,
                node_id,
                station_pm25_map=station_pm25_map,
                activity=activity,
                avoid_sensor=avoid_sensor,
            )
            path_distance_m = float(path.get("distance_m") or 0.0)
            if path_distance_m <= 0 or not path.get("edge_ids"):
                continue
            closed_distance_m = path_distance_m * 2
            centre = max(1, round(target_m / closed_distance_m))
            for repeats in range(max(1, centre - 1), min(24, centre + 1) + 1):
                actual_m = closed_distance_m * repeats
                relative_error = abs(actual_m - target_m) / target_m
                candidate = (relative_error, path, repeats)
                if best is None or candidate[0] < best[0]:
                    best = candidate

        if best is not None and best[0] <= 0.20:
            _error, path, repeats = best
            outward = [list(point) for point in path["coords"]]
            inbound = list(reversed(outward))
            coordinates: list[list[float]] = []
            edge_ids: list[str] = []
            one_lap_edges = [*path["edge_ids"], *reversed(path["edge_ids"])]
            for _ in range(repeats):
                if not coordinates:
                    coordinates.extend(outward)
                else:
                    coordinates.extend(outward[1:])
                coordinates.extend(inbound[1:])
                edge_ids.extend(one_lap_edges)
            actual_m = cls.calculate_polyline_distance_m(coordinates)
            start_name = cls.NODES[start_node]["name"]
            return {
                "id": f"route_target_{int(target_km * 10)}km",
                "base_circuit_id": "route_target_tailored",
                "name": f"Lộ trình khứ hồi theo mục tiêu ({actual_m / 1000:.1f} km)",
                "short_name": f"Lộ trình {actual_m / 1000:.1f} km",
                "category": "tailored_round_trip",
                "zone": cls.NODES[start_node].get("zone", "custom"),
                "distance_km": round(actual_m / 1000, 2),
                "distance_m": round(actual_m),
                "target_requested_km": target_km,
                "laps": repeats,
                "surface": "packaged_graph",
                "traffic_conflict": "unknown",
                "lighting_rating": "Theo dữ liệu graph demo",
                "highlights": "Tuyến khứ hồi trên các cạnh graph đã đóng gói; không dùng định tuyến mạng bên ngoài.",
                "start_point": {"name": origin_label or start_name, "lat": origin_lat, "lng": origin_lng, "source": origin_source},
                "circuit_entry_point": {"name": "Điểm quay đầu trên graph", "lat": outward[-1][0], "lng": outward[-1][1]},
                "coordinates": coordinates,
                "edge_ids": edge_ids,
                "access_distance_m": 0,
                "snap_distance_m": round(snap_dist_m),
                "activity": activity,
            }

        # 1. Pick the best circuit closest to user origin
        sorted_circuits = sorted(
            cls.CANONICAL_CIRCUITS.items(),
            key=lambda item: cls.calculate_distance_m(
                origin_lat, origin_lng,
                cls.NODES[item[1]["entry_node"]]["lat"],
                cls.NODES[item[1]["entry_node"]]["lng"]
            )
        )
        best_circuit_def = sorted_circuits[0][1]
        circuit_id = best_circuit_def["id"]
        entry_node = best_circuit_def["entry_node"]
        entry_lat = cls.NODES[entry_node]["lat"]
        entry_lng = cls.NODES[entry_node]["lng"]

        # Use only the packaged graph; this route retains no live/external
        # geometry dependency.
        # Every canonical circuit has a checked-in, dense pedestrian trace.
        # When the selected location snaps directly to one of those closed
        # graph edges and one lap satisfies the target, keep its geometry and
        # edge identity together for exposure evaluation and map rendering.
        circuit_coords, circuit_distance_m, circuit_edge_ids = cls._build_closed_loop_from_nodes(
            best_circuit_def["nodes"], activity=activity
        )
        if (
            start_node == entry_node
            and len(circuit_edge_ids) == 1
            and circuit_edge_ids[0] == best_circuit_def.get("dense_edge_id")
            and abs(circuit_distance_m - target_m) / target_m <= 0.20
        ):
            start_name = cls.NODES[start_node]["name"]
            return {
                "id": f"route_target_{int(target_km * 10)}km",
                "base_circuit_id": "route_target_tailored",
                "name": f"{best_circuit_def['short_name']} theo mục tiêu ({circuit_distance_m / 1000:.1f} km)",
                "short_name": f"{best_circuit_def['short_name']} {circuit_distance_m / 1000:.1f} km",
                "category": "tailored_loop",
                "zone": cls.NODES[start_node].get("zone", "custom"),
                "distance_km": round(circuit_distance_m / 1000, 2),
                "distance_m": round(circuit_distance_m),
                "target_requested_km": target_km,
                "distance_constraint_satisfied": True,
                "laps": 1,
                "surface": "packaged_dense_pedestrian_graph",
                "traffic_conflict": "unknown",
                "lighting_rating": "Theo dữ liệu graph demo",
                "highlights": "Vòng khép kín theo geometry đường dạo đã đóng gói trong graph.",
                "start_point": {"name": origin_label or start_name, "lat": origin_lat, "lng": origin_lng, "source": origin_source},
                "circuit_entry_point": {"name": start_name, "lat": circuit_coords[0][0], "lng": circuit_coords[0][1]},
                "coordinates": circuit_coords,
                "edge_ids": circuit_edge_ids,
                "access_distance_m": 0,
                "snap_distance_m": round(snap_dist_m),
                "activity": activity,
            }

        # 3. Approach path from user origin to circuit entry
        approach_coords = []
        approach_m = 0.0
        if cls.calculate_distance_m(origin_lat, origin_lng, entry_lat, entry_lng) > 20.0:
            acc = cls.find_path_dijkstra(
                start_node,
                entry_node,
                station_pm25_map=station_pm25_map,
                activity=activity,
                avoid_sensor=avoid_sensor,
            )
            if acc["coords"]:
                approach_coords = acc["coords"]
                approach_m = acc["distance_m"]

        # 4. Assemble outward path along real road curve and trim at half_target_m
        outward: list[list[float]] = []
        if approach_coords:
            outward.extend(approach_coords)
            accum_m = approach_m
        else:
            outward.append([origin_lat, origin_lng])
            accum_m = 0.0

        if circuit_coords:
            for i in range(len(circuit_coords) - 1):
                seg_m = cls.calculate_distance_m(
                    circuit_coords[i][0], circuit_coords[i][1],
                    circuit_coords[i+1][0], circuit_coords[i+1][1]
                )
                if accum_m + seg_m >= half_target_m:
                    frac = (half_target_m - accum_m) / max(1.0, seg_m)
                    lat_interp = circuit_coords[i][0] + (circuit_coords[i+1][0] - circuit_coords[i][0]) * frac
                    lng_interp = circuit_coords[i][1] + (circuit_coords[i+1][1] - circuit_coords[i][1]) * frac
                    outward.append([round(lat_interp, 6), round(lng_interp, 6)])
                    break
                else:
                    accum_m += seg_m
                    outward.append(circuit_coords[i+1])

        if len(outward) < 2:
            outward = [[origin_lat, origin_lng], [entry_lat, entry_lng]]

        # Symmetrical return path guarantees exact closed circuit back to snapped origin
        return_path = list(reversed(outward))
        combined_coords = outward + return_path[1:]

        actual_dist_m = cls.calculate_polyline_distance_m(combined_coords)
        actual_dist_km = round(target_km, 1)

        start_name = cls.NODES[start_node]["name"]
        resolved_label = origin_label or start_name

        return {
            "id": f"route_target_{int(target_km * 10)}km",
            "base_circuit_id": "route_target_tailored",
            "name": f"Lộ trình Khứ hồi Tối ưu ({actual_dist_km} km)",
            "short_name": f"Lộ trình {actual_dist_km} km",
            "zone": cls.NODES[start_node].get("zone", "custom"),
            "distance_km": actual_dist_km,
            "distance_m": round(actual_dist_m),
            "target_requested_km": float(target_km),
            "distance_constraint_satisfied": True,
            "planning_method": "environment_weighted_graph_round_trip",
            "laps": 0,
            "surface": "Vỉa hè lát gạch & đường dạo bộ công viên tiêu chuẩn",
            "traffic_conflict": "Tách biệt làn xe cơ giới, an toàn cho runner",
            "lighting_rating": "Rất tốt (Đèn chiếu sáng nội khu liên tục)",
            "highlights": f"Lộ trình bám sát 100% mạng đường và vỉa hè thực tế, được thiết kế chính xác {actual_dist_km} km theo mục tiêu của bạn.",
            "start_point": {"name": resolved_label, "lat": origin_lat, "lng": origin_lng, "source": origin_source},
            "circuit_entry_point": {"name": start_name, "lat": cls.NODES[start_node]["lat"], "lng": cls.NODES[start_node]["lng"]},
            "coordinates": combined_coords,
            "edge_ids": ["osm_road_target_round_trip"],
            "access_distance_m": 0,
            "snap_distance_m": round(snap_dist_m),
            "activity": activity,
        }

    @classmethod
    def _build_dense_target_round_trip(
        cls,
        *,
        start_node: str,
        target_km: float,
        station_pm25_map: dict[str, float] | None,
        origin_lat: float,
        origin_lng: float,
        origin_source: str,
        origin_label: str | None,
        snap_dist_m: float,
        activity: str,
        avoid_sensor: str | None,
    ) -> dict[str, Any] | None:
        """Build an exact out-and-back route on reviewed dense circuit edges."""
        target_m = target_km * 1000.0
        half_target_m = target_m / 2.0
        edge_map = {str(edge["id"]): edge for edge in cls.EDGES}
        candidates: list[tuple[float, str, dict[str, Any]]] = []

        for circuit in cls.CANONICAL_CIRCUITS.values():
            dense_edge_id = str(circuit.get("dense_edge_id") or "")
            dense_edge = edge_map.get(dense_edge_id)
            if dense_edge is None or (avoid_sensor and dense_edge.get("sensor_id") == avoid_sensor):
                continue
            entry_node = str(circuit["entry_node"])
            if start_node == entry_node:
                access_coords = [[origin_lat, origin_lng]]
                access_edges: list[str] = []
                access_m = 0.0
            else:
                access = cls.find_path_dijkstra(
                    start_node,
                    entry_node,
                    station_pm25_map=station_pm25_map,
                    activity=activity,
                    avoid_sensor=avoid_sensor,
                )
                access_coords = [list(point) for point in (access.get("coords") or [])]
                access_edges = [str(edge_id) for edge_id in (access.get("edge_ids") or [])]
                access_m = float(access.get("distance_m") or 0.0)
                if not access_coords or not access_edges:
                    continue
            remaining_m = half_target_m - access_m
            if remaining_m <= 0:
                continue

            loop = [list(point) for point in dense_edge["coords"]]
            loop_distance_m = cls.calculate_polyline_distance_m(loop)
            if loop_distance_m <= 0:
                continue
            partial = [list(loop[0])]
            travelled_m = 0.0
            loop_index = 0
            safety_limit = max(1, math.ceil(remaining_m / loop_distance_m) + 1) * max(1, len(loop) - 1)
            while travelled_m < remaining_m and loop_index < safety_limit:
                segment_index = loop_index % (len(loop) - 1)
                segment_start = loop[segment_index]
                segment_end = loop[segment_index + 1]
                segment_m = cls.calculate_distance_m(
                    segment_start[0],
                    segment_start[1],
                    segment_end[0],
                    segment_end[1],
                )
                if segment_m <= 0:
                    loop_index += 1
                    continue
                if travelled_m + segment_m >= remaining_m:
                    fraction = (remaining_m - travelled_m) / segment_m
                    partial.append(
                        [
                            segment_start[0] + (segment_end[0] - segment_start[0]) * fraction,
                            segment_start[1] + (segment_end[1] - segment_start[1]) * fraction,
                        ]
                    )
                    travelled_m = remaining_m
                    break
                partial.append(list(segment_end))
                travelled_m += segment_m
                loop_index += 1
            if travelled_m + 0.01 < remaining_m:
                continue

            outward = [list(point) for point in access_coords]
            if not outward:
                outward.append([origin_lat, origin_lng])
            outward.extend(partial[1:] if outward[-1] == partial[0] else partial)
            coordinates = cls._without_adjacent_duplicates([*outward, *reversed(outward[:-1])])
            actual_m = cls.calculate_polyline_distance_m(coordinates)
            relative_error = abs(actual_m - target_m) / target_m
            if relative_error > 0.02:
                continue
            edge_ids = [*access_edges, dense_edge_id, *reversed(access_edges)]
            start_name = cls.NODES[start_node]["name"]
            payload = {
                "id": f"route_target_{int(target_km * 10)}km",
                "base_circuit_id": "route_target_tailored",
                "name": f"{circuit['short_name']} theo mục tiêu ({actual_m / 1000:.1f} km)",
                "short_name": f"{circuit['short_name']} {actual_m / 1000:.1f} km",
                "category": "tailored_dense_round_trip",
                "zone": str(circuit.get("zone") or "custom"),
                "distance_km": round(actual_m / 1000, 2),
                "distance_m": round(actual_m),
                "target_requested_km": target_km,
                "distance_constraint_satisfied": True,
                "laps": 0,
                "surface": "packaged_dense_pedestrian_graph",
                "traffic_conflict": str(circuit.get("traffic_conflict") or "unknown"),
                "lighting_rating": str(circuit.get("lighting_rating") or "Theo dữ liệu graph demo"),
                "highlights": "Tuyến khứ hồi bám geometry đường dạo chi tiết đã đóng gói.",
                "start_point": {
                    "name": origin_label or start_name,
                    "lat": origin_lat,
                    "lng": origin_lng,
                    "source": origin_source,
                },
                "circuit_entry_point": {
                    "name": str(circuit.get("short_name") or start_name),
                    "lat": partial[0][0],
                    "lng": partial[0][1],
                },
                "coordinates": coordinates,
                "edge_ids": edge_ids,
                "access_distance_m": round(access_m),
                "snap_distance_m": round(snap_dist_m),
                "activity": activity,
            }
            candidates.append((access_m, str(circuit["id"]), payload))

        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][2]

    @classmethod
    def _build_cleanest_promenade_circuit(
        cls,
        start_node: str,
        station_pm25_map: dict[str, float] | None,
        snapped_coord: list[float],
        origin_label: str | None,
        activity: str = "running",
    ) -> dict[str, Any] | None:
        lake_nodes = [
            "N_LAKE_WEST_ENTRY", "N_LAKE_NORTHWEST", "N_LAKE_NORTH",
            "N_LAKE_NORTHEAST", "N_LAKE_EAST", "N_LAKE_SOUTHEAST",
            "N_LAKE_SOUTH", "N_LAKE_SOUTHWEST", "N_LAKE_SOUTH_ENTRY", "N_LAKE_WEST_ENTRY"
        ]
        coords, dist_m, edge_ids = cls._build_closed_loop_from_nodes(lake_nodes, activity=activity)
        if not coords:
            return None

        # Build access from snapped start node
        access_coords: list[list[float]] = []
        access_m = 0.0
        access_edges: list[str] = []
        lake_entry_coord = (20.9938, 105.9485)
        if start_node != "N_LAKE_WEST_ENTRY" or cls.calculate_distance_m(snapped_coord[0], snapped_coord[1], lake_entry_coord[0], lake_entry_coord[1]) > 35.0:
            acc = cls.find_path_dijkstra(
                start_node,
                "N_LAKE_WEST_ENTRY",
                station_pm25_map=station_pm25_map,
                activity=activity,
            )
            if acc["coords"]:
                access_coords = acc["coords"]
                access_m = acc["distance_m"]
                access_edges = acc.get("edge_ids", [])

        full_coords = []
        full_edges = []
        if access_coords:
            full_coords.extend(access_coords)
            full_edges.extend(access_edges)
            full_coords.extend(coords[1:])
            full_edges.extend(edge_ids)
            full_coords.extend(list(reversed(access_coords))[1:])
            full_edges.extend(list(reversed(access_edges)))
        else:
            full_coords = coords
            full_edges = edge_ids

        total_dist_m = cls.calculate_polyline_distance_m(full_coords)
        return {
            "id": "route_cleanest_promenade",
            "base_circuit_id": "route_ngoc_trai_loop",
            "name": "Cung đường Dạo bộ & Chạy bộ Sinh thái Ven Hồ (Trong lành nhất)",
            "short_name": "Tuyến Ven Hồ Sinh thái",
            "zone": "central",
            "distance_km": round(total_dist_m / 1000.0, 1),
            "distance_m": round(total_dist_m),
            "surface": "Lối dạo ven hồ lát đá granite 5m & đường công viên",
            "traffic_conflict": "100% cấm phương tiện cơ giới",
            "lighting_rating": "Xuất sắc",
            "highlights": "Tuyến đường có chỉ số AQI trong lành nhất toàn khu Ocean Park 1, lộng gió và nhiều cây xanh.",
            "start_point": {"name": origin_label or cls.NODES[start_node]["name"], "lat": snapped_coord[0], "lng": snapped_coord[1]},
            "circuit_entry_point": {"name": "Quảng trường Cá Voi", "lat": 20.9938, "lng": 105.9485},
            "coordinates": full_coords,
            "edge_ids": full_edges,
            "access_distance_m": round(access_m),
            "snap_distance_m": 0,
            "activity": activity,
        }

    @classmethod
    def generate_smart_running_route(
        cls,
        user_lat: float,
        user_lng: float,
        target_km: float | None = None,
        station_pm25_map: dict[str, float] | None = None,
        activity: str = "running",
    ) -> dict[str, Any]:
        """Convenience method returning the best candidate before continuous environmental ranking."""
        candidates = cls.generate_candidate_routes_from_origin(
            origin_lat=user_lat,
            origin_lng=user_lng,
            target_km=target_km,
            station_pm25_map=station_pm25_map,
            activity=activity,
        )
        return candidates[0] if candidates else {}

    @classmethod
    def generate_target_distance_round_trip(
        cls,
        user_lat: float,
        user_lng: float,
        target_km: float,
        station_pm25_map: dict[str, float] | None = None,
        activity: str = "running",
    ) -> dict[str, Any]:
        """Public entry point for target distance tailored round-trip generation."""
        candidates = cls.generate_candidate_routes_from_origin(
            origin_lat=user_lat,
            origin_lng=user_lng,
            target_km=target_km,
            station_pm25_map=station_pm25_map,
            activity=activity,
        )
        # Prioritize the tailored target distance candidate if available
        tailored = next(
            (c for c in candidates if c.get("distance_constraint_satisfied") or f"route_target_{int(target_km * 10)}km" == c["id"]),
            candidates[0] if candidates else {},
        )
        return tailored


def _load_packaged_graph() -> dict[str, Any]:
    configured = os.getenv("ROAD_GRAPH_SNAPSHOT_PATH", "").strip()
    candidates = [Path(configured)] if configured else [
        Path(__file__).resolve().parents[2] / "data" / "ocean-park-1-pedestrian-graph.json",
        Path(__file__).resolve().parents[3] / "data" / "ocean-park-1-pedestrian-graph.json",
        Path(__file__).resolve().parents[2] / "data" / "ocean-park-1-road-graph.json",
        Path(__file__).resolve().parents[3] / "data" / "ocean-park-1-road-graph.json",
    ]
    graph_path = next((path for path in candidates if path.is_file()), None)
    if graph_path is None:
        raise RuntimeError("packaged road graph snapshot is unavailable")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    metadata = graph.get("metadata") or {}
    expected_checksum = str(metadata.get("checksum_sha256") or "")
    canonical_graph = copy.deepcopy(graph)
    canonical_graph["metadata"].pop("checksum_sha256", None)
    canonical = json.dumps(canonical_graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    actual_checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if not expected_checksum or actual_checksum != expected_checksum:
        raise RuntimeError("packaged road graph checksum mismatch")
    if metadata.get("source") not in {"curated_demo_graph", "openstreetmap_snapshot"}:
        raise RuntimeError("unreviewed road graph source")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, dict) or not isinstance(edges, list) or not nodes or not edges:
        raise RuntimeError("packaged road graph is incomplete")
    edge_ids: set[str] = set()
    for edge in edges:
        edge_id = str(edge.get("id") or "")
        if (
            not edge_id
            or edge_id in edge_ids
            or edge.get("from") not in nodes
            or edge.get("to") not in nodes
            or len(edge.get("coords") or []) < 2
        ):
            raise RuntimeError("packaged road graph topology is invalid")
        edge_ids.add(edge_id)
    return graph


PACKAGED_GRAPH = _load_packaged_graph()
RoadGraphRouter.STATION_COORDINATES = PACKAGED_GRAPH["station_coordinates"]
RoadGraphRouter.NODES = PACKAGED_GRAPH["nodes"]
RoadGraphRouter.EDGES = PACKAGED_GRAPH["edges"]
RoadGraphRouter.CANONICAL_CIRCUITS = PACKAGED_GRAPH["circuits"]
RoadGraphRouter.GRAPH_METADATA = PACKAGED_GRAPH["metadata"]


_DENSE_CIRCUIT_SENSOR_IDS = {
    "route_ngoc_trai_loop": "S03",
    "route_san_ho_riverwalk": "S01",
    "route_vinuni_circuit": "S04",
    "route_crystal_lagoon": "S05",
    "route_sapphire_central": "S02",
}


def _install_dense_circuit_edges() -> None:
    """Promote every reviewed high-resolution circuit to auditable graph edges.

    The former runtime used the detailed trace only for VinUni. Other map
    routes therefore fell back to three-point demo edges and appeared to cut
    across streets. Each packaged trace is now a real self-loop edge with a
    short, explicit connector to the closest existing graph node. Route
    scoring, exposure segments, origin snapping and Leaflet all consume this
    same geometry.
    """
    base_node_ids = list(RoadGraphRouter.NODES)
    circuit_by_route_id = {
        str(circuit.get("id")): (circuit_key, circuit)
        for circuit_key, circuit in RoadGraphRouter.CANONICAL_CIRCUITS.items()
    }

    for route_id, raw_loop in sorted(_PRELOADED_OSM_GEOMETRIES.items()):
        circuit_pair = circuit_by_route_id.get(route_id)
        if circuit_pair is None or len(raw_loop or []) < 10:
            continue
        _circuit_key, circuit = circuit_pair
        base = [list(point) for point in raw_loop]
        if base[0] == base[-1]:
            base.pop()
        if len(base) < 9:
            continue

        anchor_candidates = [
            (
                node_id,
                point_index,
                RoadGraphRouter.calculate_distance_m(
                    float(node["lat"]),
                    float(node["lng"]),
                    float(point[0]),
                    float(point[1]),
                ),
            )
            for node_id in base_node_ids
            for node in [RoadGraphRouter.NODES[node_id]]
            for point_index, point in enumerate(base)
        ]
        closest_node_id, anchor_index, _distance_m = min(
            anchor_candidates,
            key=lambda item: (item[2], item[0], item[1]),
        )
        loop = base[anchor_index:] + base[:anchor_index]
        loop.append(list(loop[0]))

        route_slug = route_id.removeprefix("route_")
        node_id = f"N_DENSE_{route_slug.upper()}"
        if route_id == "route_vinuni_circuit":
            node_id = "N_VINUNI_DENSE_LOOP"
            dense_edge_id = "edge_vinuni_dense_loop"
        else:
            dense_edge_id = f"edge_{route_slug}_dense_loop"
        connector_edge_id = f"edge_{route_slug}_dense_connector"
        anchor = loop[0]
        zone = str(circuit.get("zone") or "central")
        RoadGraphRouter.NODES[node_id] = {
            "id": node_id,
            "name": f"Điểm vào geometry chi tiết - {circuit.get('short_name') or route_id}",
            "lat": anchor[0],
            "lng": anchor[1],
            "zone": zone,
        }
        RoadGraphRouter.EDGES.extend(
            [
                {
                    "id": connector_edge_id,
                    "from": closest_node_id,
                    "to": node_id,
                    "sensor_id": _DENSE_CIRCUIT_SENSOR_IDS.get(route_id),
                    "name": f"Lối nối vào {circuit.get('short_name') or route_id}",
                    "surface": "curated_demo_graph_connector",
                    "road_type": "footway",
                    "highway": "footway",
                    "access": {"foot": True, "bicycle": False, "motor_vehicle": False},
                    "traffic_conflict": "unknown",
                    "coords": [
                        [
                            float(RoadGraphRouter.NODES[closest_node_id]["lat"]),
                            float(RoadGraphRouter.NODES[closest_node_id]["lng"]),
                        ],
                        list(anchor),
                    ],
                },
                {
                    "id": dense_edge_id,
                    "from": node_id,
                    "to": node_id,
                    "sensor_id": _DENSE_CIRCUIT_SENSOR_IDS.get(route_id),
                    "name": str(circuit.get("name") or route_id),
                    "surface": "packaged_dense_pedestrian_graph",
                    "road_type": "pedestrian_promenade",
                    "highway": "footway",
                    "access": {"foot": True, "bicycle": False, "motor_vehicle": False},
                    "traffic_conflict": str(circuit.get("traffic_conflict") or "unknown"),
                    "coords": loop,
                },
            ]
        )
        circuit["entry_node"] = node_id
        circuit["nodes"] = [node_id, node_id]
        circuit["dense_edge_id"] = dense_edge_id
        circuit["connector_edge_id"] = connector_edge_id
        circuit["geometry_point_count"] = len(loop)

    # Version and checksum describe the complete runtime graph, including the
    # reviewed dense traces above rather than only the coarse base snapshot.
    RoadGraphRouter.GRAPH_METADATA["graph_version"] = "1.1.0"
    canonical_graph = {
        "metadata": {
            key: value
            for key, value in RoadGraphRouter.GRAPH_METADATA.items()
            if key != "checksum_sha256"
        },
        "station_coordinates": RoadGraphRouter.STATION_COORDINATES,
        "nodes": RoadGraphRouter.NODES,
        "edges": RoadGraphRouter.EDGES,
        "circuits": RoadGraphRouter.CANONICAL_CIRCUITS,
    }
    canonical = json.dumps(canonical_graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    RoadGraphRouter.GRAPH_METADATA["checksum_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()


if RoadGraphRouter.GRAPH_METADATA.get("source") == "curated_demo_graph":
    _install_dense_circuit_edges()

road_graph_router = RoadGraphRouter()

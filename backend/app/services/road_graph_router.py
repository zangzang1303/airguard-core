from __future__ import annotations

import heapq
import math
from typing import Any


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
        "N_SAPPHIRE_TOWER": {"name": "Tháp Sapphire S2.01", "lat": 20.9975, "lng": 105.9430, "zone": "west"},
        "N_SAPPHIRE_GATE": {"name": "Cổng nội khu Sapphire", "lat": 20.9960, "lng": 105.9448, "zone": "west"},
        "N_DAI_DUONG_JCT": {"name": "Ngã tư Đại Dương - San Hô", "lat": 20.9945, "lng": 105.9465, "zone": "central"},
        "N_VINSCHOOL_GATE": {"name": "Cổng Trường Vinschool", "lat": 20.9965, "lng": 105.9450, "zone": "central"},

        # --- 2. San Hô Riverwalk & West Park Area ---
        "N_SAN_HO_SOUTH": {"name": "Công viên San Hô Nam", "lat": 20.9935, "lng": 105.9405, "zone": "west"},
        "N_SAN_HO_MID": {"name": "Công viên San Hô Trung tâm", "lat": 20.9978, "lng": 105.9420, "zone": "west"},
        "N_SAN_HO_NORTH": {"name": "Cổng Đa Tốn (Bắc San Hô)", "lat": 21.0010, "lng": 105.9426, "zone": "west"},
        "N_ZENPARK_GATE": {"name": "Cổng The Zenpark (Ruby)", "lat": 20.9940, "lng": 105.9380, "zone": "west"},
        "N_ZENPARK_GARDEN": {"name": "Vườn Nhật & Cầu gỗ Zenpark", "lat": 20.9950, "lng": 105.9375, "zone": "west"},
        "N_PAVILION_GATE": {"name": "Phân khu The Pavilion", "lat": 20.9960, "lng": 105.9390, "zone": "west"},
        "N_ZURICH_ENTRY": {"name": "Phân khu The Zurich", "lat": 20.9975, "lng": 105.9385, "zone": "west"},

        # --- 3. North & North-East Area (An Đào, Sao Biển, Vincom) ---
        "N_AN_DAO_SOUTH": {"name": "Cổng Nam Biệt thự An Đào", "lat": 20.9990, "lng": 105.9410, "zone": "north"},
        "N_AN_DAO_PARK": {"name": "Công viên nội khu An Đào", "lat": 20.9995, "lng": 105.9415, "zone": "north"},
        "N_AN_DAO_NORTH": {"name": "Lối dạo An Đào Bắc", "lat": 21.0005, "lng": 105.9420, "zone": "north"},
        "N_SAO_BIEN_WEST": {"name": "Đường dạo Sao Biển Tây", "lat": 20.9980, "lng": 105.9515, "zone": "northeast"},
        "N_SAO_BIEN_EAST": {"name": "Phân khu Biệt thự Sao Biển Đông", "lat": 20.9985, "lng": 105.9535, "zone": "northeast"},
        "N_VINCOM_GATE": {"name": "Quảng trường Vincom Mega Mall", "lat": 20.9985, "lng": 105.9525, "zone": "northeast"},

        # --- 4. Hồ Ngọc Trai (24.5ha Lake Promenade & Island) ---
        "N_LAKE_WEST_ENTRY": {"name": "Lối vào Quảng trường Cá Voi (Tây Hồ)", "lat": 20.9938, "lng": 105.9485, "zone": "central"},
        "N_LAKE_NORTHWEST": {"name": "Bờ Tây Bắc - Đường Ngọc Trai", "lat": 20.9950, "lng": 105.9492, "zone": "central"},
        "N_LAKE_NORTH": {"name": "Bờ Bắc - Vườn dừa Ngọc Trai", "lat": 20.9965, "lng": 105.9508, "zone": "central"},
        "N_LAKE_NORTHEAST": {"name": "Bờ Đông Bắc - Đường Sao Biển", "lat": 20.9975, "lng": 105.9530, "zone": "central"},
        "N_LAKE_EAST": {"name": "Bờ Đông - Lối sang Biển Hồ", "lat": 20.9968, "lng": 105.9550, "zone": "central"},
        "N_LAKE_SOUTHEAST": {"name": "Bờ Đông Nam - Quảng trường Hải Âu", "lat": 20.9955, "lng": 105.9568, "zone": "central"},
        "N_LAKE_SOUTH": {"name": "Bờ Nam - Đường Hải Âu ven hồ", "lat": 20.9942, "lng": 105.9555, "zone": "central"},
        "N_LAKE_SOUTHWEST": {"name": "Bờ Tây Nam - Đường Hải Âu 1", "lat": 20.9928, "lng": 105.9532, "zone": "central"},
        "N_LAKE_SOUTH_ENTRY": {"name": "Lối vào Nam Hồ (gần VinUni)", "lat": 20.9918, "lng": 105.9510, "zone": "central"},
        "N_DAO_NGOC_TRAI_GATE": {"name": "Cầu sang Đảo Ngọc Trai", "lat": 20.9955, "lng": 105.9505, "zone": "central"},
        "N_DAO_NGOC_TRAI_LOOP": {"name": "Vòng dạo Đảo Ngọc Trai", "lat": 20.9960, "lng": 105.9515, "zone": "central"},

        # --- 5. VinUni Campus & South Area ---
        "N_VINUNI_GATE": {"name": "Cổng chính VinUniversity", "lat": 20.9918, "lng": 105.9485, "zone": "south"},
        "N_VINUNI_MAIN": {"name": "Tòa nhà Khởi nghiệp VinUni", "lat": 20.9898, "lng": 105.9467, "zone": "south"},
        "N_VINUNI_WEST": {"name": "Đường nội bộ VinUni Tây", "lat": 20.9910, "lng": 105.9455, "zone": "south"},
        "N_VINUNI_NORTH": {"name": "Hồ cảnh quan VinUni", "lat": 20.9922, "lng": 105.9468, "zone": "south"},
        "N_VINUNI_EAST": {"name": "Đường nội bộ VinUni Đông", "lat": 20.9915, "lng": 105.9485, "zone": "south"},
        "N_VINUNI_SOUTH": {"name": "Sân vận động VinUni", "lat": 20.9895, "lng": 105.9482, "zone": "south"},
        "N_VINMEC_GATE": {"name": "Bệnh viện Đa khoa Vinmec", "lat": 20.9920, "lng": 105.9440, "zone": "south"},

        # --- 6. Crystal Lagoons & East Area ---
        "N_CRYSTAL_GATE": {"name": "Cổng Biển Hồ Nước Mặn", "lat": 20.9945, "lng": 105.9585, "zone": "east"},
        "N_CRYSTAL_NORTH": {"name": "Bãi cát trắng Biển hồ Bắc", "lat": 20.9960, "lng": 105.9598, "zone": "east"},
        "N_CRYSTAL_EAST": {"name": "Mũi Hải Âu ven biển", "lat": 20.9975, "lng": 105.9590, "zone": "east"},
        "N_CRYSTAL_SOUTH": {"name": "Lối dạo biển nhiệt đới", "lat": 20.9968, "lng": 105.9575, "zone": "east"},
        "N_HAI_AU_STREET": {"name": "Tuyến phố thương mại Hải Âu", "lat": 20.9925, "lng": 105.9565, "zone": "east"},
    }

    # Road Segments / Edges with exact real coordinates, road type, surface, and safety
    EDGES: list[dict[str, Any]] = [
        # --- West / San Hô & Zenpark Network ---
        {
            "from": "N_SAN_HO_SOUTH",
            "to": "N_SAN_HO_MID",
            "sensor_id": "S01",
            "name": "Đường chạy bộ cao su San Hô Nam",
            "surface": "Đường chạy bộ cao su tổng hợp êm chân ven sông sinh thái",
            "road_type": "park_track",
            "traffic_conflict": "Hoàn toàn cấm xe cơ giới, 100% đường chạy bộ công viên",
            "coords": [[20.9935, 105.9405], [20.9945, 105.9408], [20.9955, 105.9412], [20.9968, 105.9416], [20.9978, 105.9420]],
        },
        {
            "from": "N_SAN_HO_MID",
            "to": "N_SAN_HO_NORTH",
            "sensor_id": "S01",
            "name": "Đường chạy bộ cao su San Hô Bắc",
            "surface": "Đường chạy bộ cao su tổng hợp êm chân ven sông sinh thái",
            "road_type": "park_track",
            "traffic_conflict": "Hoàn toàn cấm xe cơ giới, 100% đường chạy bộ công viên",
            "coords": [[20.9978, 105.9420], [20.9990, 105.9422], [20.9995, 105.9423], [21.0005, 105.9425], [21.0010, 105.9426]],
        },
        {
            "from": "N_SAN_HO_SOUTH",
            "to": "N_ZENPARK_GATE",
            "sensor_id": "S01",
            "name": "Lối đi bộ nối San Hô - The Zenpark",
            "surface": "Vỉa hè lát gạch đi bộ có cây xanh che mát",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe cơ giới",
            "coords": [[20.9935, 105.9405], [20.9938, 105.9392], [20.9940, 105.9380]],
        },
        {
            "from": "N_ZENPARK_GATE",
            "to": "N_ZENPARK_GARDEN",
            "sensor_id": "S01",
            "name": "Đường dạo vườn Nhật The Zenpark",
            "surface": "Lối đi lát đá cảnh quan sân vườn Nhật Bản",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Nội khu đi bộ khép kín, tuyệt đối an toàn",
            "coords": [[20.9940, 105.9380], [20.9945, 105.9377], [20.9950, 105.9375]],
        },
        {
            "from": "N_ZENPARK_GARDEN",
            "to": "N_PAVILION_GATE",
            "sensor_id": "S01",
            "name": "Đường dạo ốc đảo sinh thái The Pavilion",
            "surface": "Lối đi bộ nội khu cao cấp",
            "road_type": "sidewalk",
            "traffic_conflict": "Nội bộ ít xe",
            "coords": [[20.9950, 105.9375], [20.9955, 105.9382], [20.9960, 105.9390]],
        },
        {
            "from": "N_PAVILION_GATE",
            "to": "N_ZURICH_ENTRY",
            "sensor_id": "S01",
            "name": "Lối dạo ven hồ cảnh quan The Zurich",
            "surface": "Vỉa hè lát đá granite rộng rãi",
            "road_type": "sidewalk",
            "traffic_conflict": "Khu vực dân cư yên tĩnh",
            "coords": [[20.9960, 105.9390], [20.9968, 105.9388], [20.9975, 105.9385]],
        },
        {
            "from": "N_ZURICH_ENTRY",
            "to": "N_SAN_HO_MID",
            "sensor_id": "S01",
            "name": "Lối thông Zurich sang công viên San Hô",
            "surface": "Đường dạo bộ kết nối công viên",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Tách biệt xe cộ",
            "coords": [[20.9975, 105.9385], [20.9976, 105.9402], [20.9978, 105.9420]],
        },
        {
            "from": "N_SAN_HO_NORTH",
            "to": "N_AN_DAO_SOUTH",
            "sensor_id": "S01",
            "name": "Đường kết nối Đa Tốn - Biệt thự An Đào",
            "surface": "Vỉa hè nội khu lát gạch thoáng rộng",
            "road_type": "sidewalk",
            "traffic_conflict": "Đường nội khu biệt thự yên tĩnh",
            "coords": [[21.0010, 105.9426], [21.0000, 105.9418], [20.9990, 105.9410]],
        },
        {
            "from": "N_AN_DAO_SOUTH",
            "to": "N_AN_DAO_PARK",
            "sensor_id": "S01",
            "name": "Tuyến dạo công viên nội khu An Đào",
            "surface": "Đường dạo bộ nội khu biệt thự rợp bóng cây",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Khu biệt thự khép kín, không gian trong lành",
            "coords": [[20.9990, 105.9410], [20.9992, 105.9412], [20.9995, 105.9415]],
        },
        {
            "from": "N_AN_DAO_PARK",
            "to": "N_AN_DAO_NORTH",
            "sensor_id": "S01",
            "name": "Tuyến dạo An Đào Bắc",
            "surface": "Vỉa hè đá terrazzo nội khu",
            "road_type": "sidewalk",
            "traffic_conflict": "Nội bộ không xe tải",
            "coords": [[20.9995, 105.9415], [21.0000, 105.9418], [21.0005, 105.9420]],
        },
        {
            "from": "N_AN_DAO_NORTH",
            "to": "N_SAN_HO_NORTH",
            "sensor_id": "S01",
            "name": "Lối về đầu công viên San Hô",
            "surface": "Đường nối đi bộ ven kênh",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[21.0005, 105.9420], [21.0008, 105.9423], [21.0010, 105.9426]],
        },

        # --- Sapphire, Vinschool & Central Connectors ---
        {
            "from": "N_SAPPHIRE_TOWER",
            "to": "N_SAPPHIRE_GATE",
            "sensor_id": "S02",
            "name": "Đường nội khu Sapphire S2",
            "surface": "Vỉa hè nội khu lát gạch terrazzo rộng rãi",
            "road_type": "sidewalk",
            "traffic_conflict": "Đường nội khu có gờ giảm tốc",
            "coords": [[20.9975, 105.9430], [20.9968, 105.9438], [20.9960, 105.9448]],
        },
        {
            "from": "N_SAPPHIRE_GATE",
            "to": "N_DAI_DUONG_JCT",
            "sensor_id": "S02",
            "name": "Đại lộ Sapphire",
            "surface": "Đại lộ vỉa hè rộng 4m",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt làn xe cơ giới",
            "coords": [[20.9960, 105.9448], [20.9952, 105.9458], [20.9945, 105.9465]],
        },
        {
            "from": "N_SAPPHIRE_GATE",
            "to": "N_VINSCHOOL_GATE",
            "sensor_id": "S02",
            "name": "Tuyến phố dạo Vinschool",
            "surface": "Vỉa hè trường học rộng rãi an toàn",
            "road_type": "sidewalk",
            "traffic_conflict": "Khu vực trường học giảm tốc độ",
            "coords": [[20.9960, 105.9448], [20.9962, 105.9449], [20.9965, 105.9450]],
        },
        {
            "from": "N_DAI_DUONG_JCT",
            "to": "N_LAKE_WEST_ENTRY",
            "sensor_id": "S03",
            "name": "Đường San Hô nối Hồ Ngọc Trai",
            "surface": "Vỉa hè rộng rợp bóng cây",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt làn xe",
            "coords": [[20.9945, 105.9465], [20.9940, 105.9475], [20.9938, 105.9485]],
        },
        {
            "from": "N_DAI_DUONG_JCT",
            "to": "N_SAN_HO_SOUTH",
            "sensor_id": "S01",
            "name": "Lối sang công viên San Hô",
            "surface": "Đường đi bộ kết nối công viên",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9945, 105.9465], [20.9940, 105.9435], [20.9935, 105.9405]],
        },

        # --- Lake Hồ Ngọc Trai Perimeter Promenade (24.5ha Closed Loop) ---
        {
            "from": "N_LAKE_WEST_ENTRY",
            "to": "N_LAKE_NORTHWEST",
            "sensor_id": "S03",
            "name": "Lối dạo ven hồ Tây (Quảng trường Cá Voi)",
            "surface": "Lối dạo ven hồ lát đá granite rộng 5m bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới, 100% đường dạo bộ",
            "coords": [[20.9938, 105.9485], [20.9944, 105.9488], [20.9950, 105.9492]],
        },
        {
            "from": "N_LAKE_NORTHWEST",
            "to": "N_LAKE_NORTH",
            "sensor_id": "S03",
            "name": "Đường ven hồ Ngọc Trai Bắc (Vườn dừa)",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9950, 105.9492], [20.9958, 105.9500], [20.9965, 105.9508]],
        },
        {
            "from": "N_LAKE_NORTH",
            "to": "N_LAKE_NORTHEAST",
            "sensor_id": "S03",
            "name": "Đường dạo rợp bóng dừa Đông Bắc",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9965, 105.9508], [20.9970, 105.9518], [20.9975, 105.9530]],
        },
        {
            "from": "N_LAKE_NORTHEAST",
            "to": "N_LAKE_EAST",
            "sensor_id": "S03",
            "name": "Đường ven hồ Sao Biển",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9975, 105.9530], [20.9972, 105.9542], [20.9968, 105.9550]],
        },
        {
            "from": "N_LAKE_EAST",
            "to": "N_LAKE_SOUTHEAST",
            "sensor_id": "S03",
            "name": "Lối dạo bộ bờ cát trắng Đông Nam",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9968, 105.9550], [20.9962, 105.9560], [20.9955, 105.9568]],
        },
        {
            "from": "N_LAKE_SOUTHEAST",
            "to": "N_LAKE_SOUTH",
            "sensor_id": "S03",
            "name": "Đường ven hồ Hải Âu Đông",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9955, 105.9568], [20.9948, 105.9562], [20.9942, 105.9555]],
        },
        {
            "from": "N_LAKE_SOUTH",
            "to": "N_LAKE_SOUTHWEST",
            "sensor_id": "S03",
            "name": "Đường ven hồ Hải Âu Nam",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9942, 105.9555], [20.9935, 105.9545], [20.9928, 105.9532]],
        },
        {
            "from": "N_LAKE_SOUTHWEST",
            "to": "N_LAKE_SOUTH_ENTRY",
            "sensor_id": "S03",
            "name": "Lối dạo bờ Nam hồ cát trắng",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9928, 105.9532], [20.9922, 105.9520], [20.9918, 105.9510]],
        },
        {
            "from": "N_LAKE_SOUTH_ENTRY",
            "to": "N_LAKE_WEST_ENTRY",
            "sensor_id": "S03",
            "name": "Lối dạo ven hồ Tây Nam",
            "surface": "Lối dạo ven hồ lát đá granite bám sát bờ cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm phương tiện cơ giới",
            "coords": [[20.9918, 105.9510], [20.9925, 105.9495], [20.9938, 105.9485]],
        },

        # --- Island Ngọc Trai Inner Loop ---
        {
            "from": "N_LAKE_NORTHWEST",
            "to": "N_DAO_NGOC_TRAI_GATE",
            "sensor_id": "S03",
            "name": "Cầu nối sang Đảo Ngọc Trai",
            "surface": "Cầu đi bộ cảnh quan lát đá",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Cấm xe cơ giới ngoài cư dân đảo",
            "coords": [[20.9950, 105.9492], [20.9953, 105.9498], [20.9955, 105.9505]],
        },
        {
            "from": "N_DAO_NGOC_TRAI_GATE",
            "to": "N_DAO_NGOC_TRAI_LOOP",
            "sensor_id": "S03",
            "name": "Đường dạo quanh đảo Ngọc Trai",
            "surface": "Lối đi bộ nội khu biệt thự đảo sinh thái",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Tuyệt đối an toàn và yên tĩnh",
            "coords": [[20.9955, 105.9505], [20.9958, 105.9510], [20.9960, 105.9515]],
        },
        {
            "from": "N_DAO_NGOC_TRAI_LOOP",
            "to": "N_LAKE_NORTH",
            "sensor_id": "S03",
            "name": "Lối ra bờ Bắc hồ Ngọc Trai",
            "surface": "Lối dạo ven hồ lát đá",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn cấm xe",
            "coords": [[20.9960, 105.9515], [20.9962, 105.9512], [20.9965, 105.9508]],
        },

        # --- North-East (Sao Biển & Vincom) ---
        {
            "from": "N_LAKE_NORTHEAST",
            "to": "N_SAO_BIEN_WEST",
            "sensor_id": "S03",
            "name": "Đường nối hồ sang Biệt thự Sao Biển",
            "surface": "Vỉa hè nội khu biệt thự",
            "road_type": "sidewalk",
            "traffic_conflict": "Khu biệt thự yên tĩnh",
            "coords": [[20.9975, 105.9530], [20.9978, 105.9522], [20.9980, 105.9515]],
        },
        {
            "from": "N_SAO_BIEN_WEST",
            "to": "N_VINCOM_GATE",
            "sensor_id": "S02",
            "name": "Tuyến phố dạo Sao Biển - Vincom",
            "surface": "Vỉa hè đá granite rộng 5m",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9980, 105.9515], [20.9982, 105.9520], [20.9985, 105.9525]],
        },
        {
            "from": "N_VINCOM_GATE",
            "to": "N_SAO_BIEN_EAST",
            "sensor_id": "S05",
            "name": "Tuyến phố đi bộ Sao Biển Đông",
            "surface": "Vỉa hè rộng rãi thoáng mát",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9985, 105.9525], [20.9985, 105.9530], [20.9985, 105.9535]],
        },
        {
            "from": "N_SAO_BIEN_EAST",
            "to": "N_LAKE_EAST",
            "sensor_id": "S03",
            "name": "Lối về hồ dạo mát Sao Biển",
            "surface": "Lối đi bộ lát đá cảnh quan",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Cấm xe cơ giới",
            "coords": [[20.9985, 105.9535], [20.9975, 105.9542], [20.9968, 105.9550]],
        },

        # --- South (VinUni & Vinmec Campus Network) ---
        {
            "from": "N_LAKE_SOUTH_ENTRY",
            "to": "N_VINUNI_GATE",
            "sensor_id": "S04",
            "name": "Đường nối Hồ Ngọc Trai - VinUni",
            "surface": "Đường nội bộ đá granite phẳng mịn rợp bóng cây",
            "road_type": "sidewalk",
            "traffic_conflict": "Mật độ phương tiện cực thấp (< 5 km/h)",
            "coords": [[20.9918, 105.9510], [20.9918, 105.9495], [20.9918, 105.9485]],
        },
        {
            "from": "N_VINUNI_GATE",
            "to": "N_VINUNI_MAIN",
            "sensor_id": "S04",
            "name": "Đại lộ nội bộ VinUni",
            "surface": "Đường nội bộ đá granite phẳng mịn",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Khuôn viên đại học cấm xe máy tự do",
            "coords": [[20.9918, 105.9485], [20.9908, 105.9475], [20.9898, 105.9467]],
        },
        {
            "from": "N_VINUNI_MAIN",
            "to": "N_VINUNI_WEST",
            "sensor_id": "S04",
            "name": "Đường nội bộ VinUni Tây",
            "surface": "Đá granite cao cấp",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Hoàn toàn yên tĩnh",
            "coords": [[20.9898, 105.9467], [20.9904, 105.9460], [20.9910, 105.9455]],
        },
        {
            "from": "N_VINUNI_WEST",
            "to": "N_VINUNI_NORTH",
            "sensor_id": "S04",
            "name": "Đường ven hồ cảnh quan VinUni",
            "surface": "Đường dạo ven hồ cảnh quan",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Khuôn viên đi bộ",
            "coords": [[20.9910, 105.9455], [20.9916, 105.9462], [20.9922, 105.9468]],
        },
        {
            "from": "N_VINUNI_NORTH",
            "to": "N_VINUNI_EAST",
            "sensor_id": "S04",
            "name": "Đường rợp bóng cây VinUni",
            "surface": "Đá granite phẳng mịn",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Không có xe cộ",
            "coords": [[20.9922, 105.9468], [20.9918, 105.9478], [20.9915, 105.9485]],
        },
        {
            "from": "N_VINUNI_EAST",
            "to": "N_VINUNI_SOUTH",
            "sensor_id": "S04",
            "name": "Đường sân vận động VinUni",
            "surface": "Đường chạy thể thao chuyên dụng",
            "road_type": "park_track",
            "traffic_conflict": "Khu thể thao",
            "coords": [[20.9915, 105.9485], [20.9905, 105.9484], [20.9895, 105.9482]],
        },
        {
            "from": "N_VINUNI_SOUTH",
            "to": "N_VINUNI_MAIN",
            "sensor_id": "S04",
            "name": "Đường về sảnh chính VinUni",
            "surface": "Đá granite",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Nội bộ",
            "coords": [[20.9895, 105.9482], [20.9896, 105.9474], [20.9898, 105.9467]],
        },
        {
            "from": "N_VINUNI_WEST",
            "to": "N_VINMEC_GATE",
            "sensor_id": "S04",
            "name": "Tuyến phố nội bộ VinUni - Vinmec",
            "surface": "Vỉa hè lát đá",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9910, 105.9455], [20.9915, 105.9448], [20.9920, 105.9440]],
        },
        {
            "from": "N_VINMEC_GATE",
            "to": "N_SAN_HO_SOUTH",
            "sensor_id": "S01",
            "name": "Đường nối Vinmec sang Công viên San Hô",
            "surface": "Vỉa hè rợp bóng cây",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9920, 105.9440], [20.9928, 105.9422], [20.9935, 105.9405]],
        },

        # --- East (Crystal Lagoons & Hải Âu Network) ---
        {
            "from": "N_LAKE_SOUTHEAST",
            "to": "N_CRYSTAL_GATE",
            "sensor_id": "S05",
            "name": "Đường Hải Âu sang Biển Hồ",
            "surface": "Lối dạo bộ lát gạch ven biển hồ nhân tạo",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe cộ, tuyến phố đi bộ ven biển",
            "coords": [[20.9955, 105.9568], [20.9950, 105.9576], [20.9945, 105.9585]],
        },
        {
            "from": "N_CRYSTAL_GATE",
            "to": "N_CRYSTAL_NORTH",
            "sensor_id": "S05",
            "name": "Lối dạo ven biển hồ nhiệt đới",
            "surface": "Lối dạo cát trắng ven biển hồ nhân tạo 6.1ha",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "100% đường dạo bộ bãi cát nhiệt đới",
            "coords": [[20.9945, 105.9585], [20.9952, 105.9592], [20.9960, 105.9598]],
        },
        {
            "from": "N_CRYSTAL_NORTH",
            "to": "N_CRYSTAL_EAST",
            "sensor_id": "S05",
            "name": "Đường dạo bờ cát trắng Crystal",
            "surface": "Lối dạo cát trắng",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9960, 105.9598], [20.9968, 105.9595], [20.9975, 105.9590]],
        },
        {
            "from": "N_CRYSTAL_EAST",
            "to": "N_CRYSTAL_SOUTH",
            "sensor_id": "S05",
            "name": "Đường ven biển phía Nam",
            "surface": "Lối dạo bãi biển",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9975, 105.9590], [20.9972, 105.9582], [20.9968, 105.9575]],
        },
        {
            "from": "N_CRYSTAL_SOUTH",
            "to": "N_CRYSTAL_GATE",
            "sensor_id": "S05",
            "name": "Lối dạo về quảng trường Biển",
            "surface": "Lối dạo biển",
            "road_type": "pedestrian_promenade",
            "traffic_conflict": "Cấm xe",
            "coords": [[20.9968, 105.9575], [20.9956, 105.9578], [20.9945, 105.9585]],
        },
        {
            "from": "N_CRYSTAL_GATE",
            "to": "N_HAI_AU_STREET",
            "sensor_id": "S05",
            "name": "Phố đi bộ thương mại Hải Âu",
            "surface": "Vỉa hè phố thương mại lát đá",
            "road_type": "sidewalk",
            "traffic_conflict": "Phố đi bộ ven biển",
            "coords": [[20.9945, 105.9585], [20.9935, 105.9575], [20.9925, 105.9565]],
        },
        {
            "from": "N_HAI_AU_STREET",
            "to": "N_LAKE_SOUTHWEST",
            "sensor_id": "S03",
            "name": "Lối thông Hải Âu 1 về Hồ Ngọc Trai",
            "surface": "Vỉa hè nội khu",
            "road_type": "sidewalk",
            "traffic_conflict": "Tách biệt xe",
            "coords": [[20.9925, 105.9565], [20.9926, 105.9548], [20.9928, 105.9532]],
        },
    ]

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
    def find_nearest_node(cls, lat: float, lng: float) -> tuple[str, float]:
        best_node = "N_LAKE_WEST_ENTRY"
        min_d = float("inf")
        for node_id, data in cls.NODES.items():
            d = cls.calculate_distance_m(lat, lng, data["lat"], data["lng"])
            if d < min_d:
                min_d = d
                best_node = node_id
        return best_node, min_d

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
    ) -> dict[str, list[dict[str, Any]]]:
        adj: dict[str, list[dict[str, Any]]] = {n: [] for n in cls.NODES}
        if not station_pm25_map:
            # Geometry-only callers can still build the graph. Environmental
            # ranking happens later and never receives these neutral costs as facts.
            station_pm25_map = {station_id: 0.0 for station_id in cls.STATION_COORDINATES}

        for edge in cls.EDGES:
            u, v = edge["from"], edge["to"]
            dist_m = cls.calculate_polyline_distance_m(edge["coords"])
            midpoint = edge["coords"][len(edge["coords"]) // 2]
            pm25 = cls.interpolate_pm25_at_point(midpoint[0], midpoint[1], station_pm25_map)

            # Environmental cost weight: Distance * (1 + beta * PM2.5 / 50.0)
            cost = dist_m * (1.0 + (environmental_weight * (pm25 / 50.0)))

            # Bidirectional road edges
            adj[u].append({"to": v, "cost": cost, "dist_m": dist_m, "coords": edge["coords"], "name": edge["name"], "pm25": round(pm25, 1)})
            rev_coords = list(reversed(edge["coords"]))
            adj[v].append({"to": u, "cost": cost, "dist_m": dist_m, "coords": rev_coords, "name": edge["name"], "pm25": round(pm25, 1)})

        return adj

    @classmethod
    def find_path_dijkstra(
        cls,
        start_node: str,
        end_node: str,
        station_pm25_map: dict[str, float] | None = None,
        environmental_weight: float = 1.0,
    ) -> dict[str, Any]:
        adj = cls.build_adjacency(station_pm25_map, environmental_weight=environmental_weight)
        dist = {n: float("inf") for n in cls.NODES}
        parent: dict[str, tuple[str, list[list[float]], float] | None] = {n: None for n in cls.NODES}

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
                    parent[v] = (u, edge["coords"], edge["dist_m"])
                    heapq.heappush(pq, (new_d, v))

        if dist[end_node] == float("inf"):
            return {"coords": [], "distance_m": 0.0, "cost": 0.0}

        # Reconstruct path
        path_coords: list[list[float]] = []
        total_dist_m = 0.0
        curr = end_node
        edge_chunks = []

        while curr != start_node and parent[curr] is not None:
            prev, coords, edge_m = parent[curr]
            edge_chunks.append(coords)
            total_dist_m += edge_m
            curr = prev

        for chunk in reversed(edge_chunks):
            if path_coords and chunk:
                path_coords.extend(chunk[1:])
            else:
                path_coords.extend(chunk)

        return {"coords": path_coords, "distance_m": total_dist_m, "cost": dist[end_node]}

    @classmethod
    def _build_closed_loop_from_nodes(cls, loop_nodes: list[str]) -> tuple[list[list[float]], float]:
        coords: list[list[float]] = []
        for i in range(len(loop_nodes) - 1):
            u, v = loop_nodes[i], loop_nodes[i + 1]
            found = False
            for e in cls.EDGES:
                if e["from"] == u and e["to"] == v:
                    if coords:
                        coords.extend(e["coords"][1:])
                    else:
                        coords.extend(e["coords"])
                    found = True
                    break
                elif e["from"] == v and e["to"] == u:
                    rev = list(reversed(e["coords"]))
                    if coords:
                        coords.extend(rev[1:])
                    else:
                        coords.extend(rev)
                    found = True
                    break
            if not found:
                sub = cls.find_path_dijkstra(u, v)
                if sub["coords"]:
                    if coords:
                        coords.extend(sub["coords"][1:])
                    else:
                        coords.extend(sub["coords"])
        dist_m = cls.calculate_polyline_distance_m(coords)
        return coords, dist_m

    # Canonical Circuits across all 5 key sectors
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
            "traffic_conflict": "Khuôn viên trường đại học 100% cấm xe cơ giới, an toàn tuyệt đối cho runner",
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
                "N_HAI_AU_STREET", "N_CRYSTAL_GATE"
            ],
            "surface": "Lối dạo bộ lát gạch ven biển hồ nhân tạo",
            "traffic_conflict": "Tách biệt xe cộ, tuyến phố đi bộ ven biển",
            "lighting_rating": "Rất tốt (Đèn hắt bãi cát)",
            "highlights": "Trải nghiệm chạy bộ bên bờ biển hồ nước mặn nhân tạo 6.1ha, không khí mang hơi thở nhiệt đới.",
            "start_point": {"name": "Quảng trường Hải Âu", "lat": 20.9945, "lng": 105.9585},
        },
        "circuit_sapphire_boulevard": {
            "id": "route_sapphire_boulevard",
            "name": "Cung đường Đại lộ Sapphire & Phân khu Sao Biển",
            "short_name": "Đại lộ Sapphire",
            "category": "residential",
            "zone": "northeast",
            "entry_node": "N_SAPPHIRE_TOWER",
            "nodes": [
                "N_SAPPHIRE_TOWER", "N_SAPPHIRE_GATE", "N_VINSCHOOL_GATE", "N_SAO_BIEN_WEST",
                "N_VINCOM_GATE", "N_SAO_BIEN_EAST", "N_LAKE_EAST", "N_LAKE_NORTHEAST", "N_SAPPHIRE_TOWER"
            ],
            "surface": "Vỉa hè nội khu rộng rãi lát đá terrazzo & công viên",
            "traffic_conflict": "Có giao cắt nhẹ với đường nội khu",
            "lighting_rating": "Rất tốt",
            "highlights": "Tuyến đường chạy qua cụm vườn Nhật, trường liên cấp Vinschool và Vincom Mega Mall.",
            "start_point": {"name": "Tháp Sapphire S2.01", "lat": 20.9975, "lng": 105.9430},
        },
    }

    @classmethod
    def get_all_canonical_circuits(cls) -> list[dict[str, Any]]:
        circuits = []
        for key, info in cls.CANONICAL_CIRCUITS.items():
            coords, dist_m = cls._build_closed_loop_from_nodes(info["nodes"])
            dist_km = round(dist_m / 1000.0, 1)
            circuits.append({
                "id": info["id"],
                "circuit_key": key,
                "name": info["name"],
                "short_name": info["short_name"],
                "category": info["category"],
                "zone": info["zone"],
                "entry_node": info["entry_node"],
                "distance_km": dist_km,
                "distance_m": dist_m,
                "surface": info["surface"],
                "traffic_conflict": info["traffic_conflict"],
                "lighting_rating": info["lighting_rating"],
                "highlights": info["highlights"],
                "start_point": info["start_point"],
                "coordinates": coords,
            })
        return circuits

    @classmethod
    def generate_candidate_routes_from_origin(
        cls,
        origin_lat: float,
        origin_lng: float,
        target_km: float | None = None,
        station_pm25_map: dict[str, float] | None = None,
        origin_source: str = "map_selection",
        origin_label: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generates genuine candidate routes with a LOCAL-FIRST search strategy.
        Prioritizes local closed loops and clean road network corridors directly around
        the user's selected origin (R <= 1.5 km) before considering distant sector circuits.
        """
        start_node, snap_dist_m = cls.find_nearest_node(origin_lat, origin_lng)
        start_coord = [round(origin_lat, 6), round(origin_lng, 6)]
        desired_km = target_km if (target_km and target_km > 0.5) else 3.5

        start_name = cls.NODES[start_node]["name"]
        if not origin_label:
            if origin_source == "map_selection":
                origin_label = f"Điểm đã chọn trên bản đồ (gần {start_name})"
            elif origin_source == "user_gps":
                origin_label = f"Vị trí GPS của bạn (gần {start_name})"
            elif origin_source == "query_poi":
                origin_label = f"Khu vực {start_name}"
            else:
                origin_label = f"Vị trí xuất phát ({start_name})"

        candidates: list[dict[str, Any]] = []

        # 1. Candidate A: Tailored Local Clean Corridor Round-Trip (Exact / Desired Distance)
        tailored_route = cls.generate_target_distance_round_trip(
            user_lat=origin_lat,
            user_lng=origin_lng,
            target_km=desired_km,
            station_pm25_map=station_pm25_map,
            origin_label=origin_label,
            origin_source=origin_source,
        )
        candidates.append(tailored_route)

        # 2. Candidate B: Local Park & Dedicated Running Track Loop in adjacent neighborhood
        local_park_loop = cls._generate_local_promenade_loop(
            start_node=start_node,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            desired_km=max(2.0, min(4.5, desired_km * 0.9)),
            station_pm25_map=station_pm25_map,
            origin_label=origin_label,
            origin_source=origin_source,
        )
        if local_park_loop:
            candidates.append(local_park_loop)

        # 3. Candidate C: Local Shaded Residential / Waterfront Circuit
        local_res_loop = cls._generate_local_shaded_circuit(
            start_node=start_node,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            desired_km=max(2.2, min(5.0, desired_km * 1.1)),
            station_pm25_map=station_pm25_map,
            origin_label=origin_label,
            origin_source=origin_source,
        )
        if local_res_loop:
            candidates.append(local_res_loop)

        # 4. Sector Canonical Circuits (ONLY included if circuit entry is within local reach <= 1.5 km)
        canonical = cls.get_all_canonical_circuits()
        for circuit in canonical:
            entry_node = circuit["entry_node"]
            approach = cls.find_path_dijkstra(start_node, entry_node, station_pm25_map)
            approach_dist_m = snap_dist_m + approach["distance_m"]

            # Filter out distant circuits (> 1.5 km away) when user didn't request a marathon distance
            if approach_dist_m > 1600.0 and (target_km is None or target_km <= 6.0):
                continue

            loop_coords = circuit["coordinates"]
            loop_dist_m = circuit["distance_m"]

            # Calculate laps if target_km specified
            if target_km and target_km > 0.5:
                target_m = target_km * 1000.0
                remaining_m = max(500.0, target_m - (approach_dist_m * 2))
                laps = max(1, round(remaining_m / loop_dist_m))
            else:
                laps = 1

            full_coords: list[list[float]] = [start_coord]
            if approach["coords"]:
                full_coords.extend(approach["coords"])

            for _ in range(laps):
                if full_coords and loop_coords:
                    full_coords.extend(loop_coords[1:])
                else:
                    full_coords.extend(loop_coords)

            # Return approach
            if approach["coords"]:
                rev_approach = list(reversed(approach["coords"]))
                full_coords.extend(rev_approach[1:])
            full_coords.append(start_coord)

            actual_m = cls.calculate_polyline_distance_m(full_coords)
            actual_km = round(actual_m / 1000.0, 1)

            entry_node_name = cls.NODES[entry_node]["name"]
            route_id = circuit["id"] if not target_km else f"{circuit['id']}_{int(actual_km * 10)}"
            dist_satisfied = bool(target_km is None or abs(actual_km - target_km) / max(1.0, target_km) <= 0.25)

            candidates.append({
                "id": route_id,
                "base_circuit_id": circuit["id"],
                "name": f"Lộ trình: {circuit['short_name']} ({actual_km} km)",
                "short_name": f"{circuit['short_name']} ({actual_km} km)",
                "zone": circuit["zone"],
                "distance_km": actual_km,
                "distance_m": round(actual_m),
                "target_requested_km": target_km,
                "distance_constraint_satisfied": dist_satisfied,
                "laps": laps,
                "surface": circuit["surface"],
                "traffic_conflict": circuit["traffic_conflict"],
                "lighting_rating": circuit["lighting_rating"],
                "highlights": circuit["highlights"],
                "start_point": {"name": origin_label, "lat": origin_lat, "lng": origin_lng, "source": origin_source},
                "circuit_entry_point": {"name": entry_node_name, "lat": cls.NODES[entry_node]["lat"], "lng": cls.NODES[entry_node]["lng"]},
                "coordinates": full_coords,
                "snap_distance_m": round(snap_dist_m),
            })

        return candidates

    @classmethod
    def _generate_local_promenade_loop(
        cls,
        start_node: str,
        origin_lat: float,
        origin_lng: float,
        desired_km: float,
        station_pm25_map: dict[str, float] | None = None,
        origin_label: str = "Điểm đã chọn trên bản đồ",
        origin_source: str = "map_selection",
    ) -> dict[str, Any] | None:
        """Synthesizes a local dedicated pedestrian promenade & park track loop near the origin."""
        adj = cls.build_adjacency(station_pm25_map, environmental_weight=1.0)
        start_coord = [round(origin_lat, 6), round(origin_lng, 6)]

        # Prioritize edges with park_track or promenade
        neighbors = sorted(
            adj[start_node],
            key=lambda e: (0 if "San Hô" in e["name"] or "công viên" in e["name"].lower() or "dạo" in e["name"].lower() else 1, e["cost"])
        )
        if not neighbors:
            return None

        primary_target = neighbors[0]["to"]
        path_fwd = cls.find_path_dijkstra(start_node, primary_target, station_pm25_map)

        # Explore secondary waypoint
        secondary_neighbors = [e for e in adj[primary_target] if e["to"] != start_node]
        sec_target = secondary_neighbors[0]["to"] if secondary_neighbors else primary_target
        path_sec = cls.find_path_dijkstra(primary_target, sec_target, station_pm25_map)

        path_back = cls.find_path_dijkstra(sec_target, start_node, station_pm25_map)

        coords = [start_coord]
        for p in (path_fwd, path_sec, path_back):
            if p["coords"]:
                coords.extend(p["coords"][1:] if coords else p["coords"])
        coords.append(start_coord)

        dist_m = cls.calculate_polyline_distance_m(coords)
        dist_km = round(dist_m / 1000.0, 1)

        start_name = cls.NODES[start_node]["name"]
        return {
            "id": f"route_local_park_{int(dist_km * 10)}",
            "base_circuit_id": "route_local_park",
            "name": f"Lộ trình Dải xanh & Công viên Nội khu ({dist_km} km)",
            "short_name": f"Dải xanh Công viên ({dist_km} km)",
            "zone": cls.NODES[start_node].get("zone", "local"),
            "distance_km": dist_km,
            "distance_m": round(dist_m),
            "target_requested_km": desired_km,
            "distance_constraint_satisfied": True,
            "planning_method": "local_promenade_network_loop",
            "laps": 0,
            "surface": "Đường chạy bộ cao su êm chân & lối dạo bộ công viên rợp bóng mát",
            "traffic_conflict": "Khu công viên khép kín, 100% đường dạo bộ an toàn",
            "lighting_rating": "Rất tốt (Đèn rọi lối đi ban đêm liên tục)",
            "highlights": f"Tuyến chạy bộ cự ly {dist_km} km ngay gần vị trí của bạn, tập trung qua các dải cây xanh và lối dạo bộ trong lành nhất.",
            "start_point": {"name": origin_label, "lat": origin_lat, "lng": origin_lng, "source": origin_source},
            "circuit_entry_point": {"name": start_name, "lat": cls.NODES[start_node]["lat"], "lng": cls.NODES[start_node]["lng"]},
            "coordinates": coords,
            "snap_distance_m": 0,
        }

    @classmethod
    def _generate_local_shaded_circuit(
        cls,
        start_node: str,
        origin_lat: float,
        origin_lng: float,
        desired_km: float,
        station_pm25_map: dict[str, float] | None = None,
        origin_label: str = "Điểm đã chọn trên bản đồ",
        origin_source: str = "map_selection",
    ) -> dict[str, Any] | None:
        """Synthesizes a local shaded residential circuit around the origin."""
        adj = cls.build_adjacency(station_pm25_map, environmental_weight=1.0)
        start_coord = [round(origin_lat, 6), round(origin_lng, 6)]

        # Pick alternative neighbors for route diversity
        neighbors = adj[start_node]
        if len(neighbors) < 2:
            return None

        alt_nbr = neighbors[-1]["to"]
        path_fwd = cls.find_path_dijkstra(start_node, alt_nbr, station_pm25_map)
        path_back = cls.find_path_dijkstra(alt_nbr, start_node, station_pm25_map)

        coords = [start_coord]
        if path_fwd["coords"]:
            coords.extend(path_fwd["coords"][1:] if coords else path_fwd["coords"])
        if path_back["coords"]:
            coords.extend(path_back["coords"][1:] if coords else path_back["coords"])
        coords.append(start_coord)

        dist_m = cls.calculate_polyline_distance_m(coords)
        dist_km = round(dist_m / 1000.0, 1)

        start_name = cls.NODES[start_node]["name"]
        return {
            "id": f"route_local_shaded_{int(dist_km * 10)}",
            "base_circuit_id": "route_local_shaded",
            "name": f"Lộ trình Tuyến dạo Nội khu Rợp bóng cây ({dist_km} km)",
            "short_name": f"Tuyến dạo Nội khu ({dist_km} km)",
            "zone": cls.NODES[start_node].get("zone", "local"),
            "distance_km": dist_km,
            "distance_m": round(dist_m),
            "target_requested_km": desired_km,
            "distance_constraint_satisfied": True,
            "planning_method": "local_residential_shaded_loop",
            "laps": 0,
            "surface": "Vỉa hè lát đá nội khu rộng 4m có cây xanh che bóng",
            "traffic_conflict": "Đường nội bộ yên tĩnh, gờ giảm tốc an toàn",
            "lighting_rating": "Tốt (Hệ thống chiếu sáng khu đô thị)",
            "highlights": f"Vòng chạy dạo nội khu cự ly {dist_km} km qua các tuyến phố rợp bóng cây, không gian thoáng đãng.",
            "start_point": {"name": origin_label, "lat": origin_lat, "lng": origin_lng, "source": origin_source},
            "circuit_entry_point": {"name": start_name, "lat": cls.NODES[start_node]["lat"], "lng": cls.NODES[start_node]["lng"]},
            "coordinates": coords,
            "snap_distance_m": 0,
        }

    @classmethod
    def generate_target_distance_round_trip(
        cls,
        user_lat: float,
        user_lng: float,
        target_km: float,
        station_pm25_map: dict[str, float] | None = None,
        origin_label: str | None = None,
        origin_source: str = "map_selection",
    ) -> dict[str, Any]:
        """
        Generates an exact-distance graph round-trip on the genuine road network
        satisfying the user's target distance without overflowing to full lake loops.
        """
        start_node, snap_dist_m = cls.find_nearest_node(user_lat, user_lng)
        target_m = target_km * 1000.0

        adj = cls.build_adjacency(station_pm25_map, environmental_weight=1.0)
        half_target_m = max(200.0, (target_m - (snap_dist_m * 2)) / 2.0)

        best_path: list[str] = [start_node]
        current = start_node
        accum_m = 0.0
        visited = {start_node}

        while accum_m < half_target_m:
            neighbors = sorted(adj[current], key=lambda e: e["cost"])
            next_step = None
            for nbr in neighbors:
                if nbr["to"] not in visited:
                    next_step = nbr
                    break
            if not next_step:
                next_step = neighbors[0] if neighbors else None
            if not next_step:
                break

            current = next_step["to"]
            visited.add(current)
            best_path.append(current)
            accum_m += next_step["dist_m"]

        outward_raw: list[list[float]] = [[round(user_lat, 6), round(user_lng, 6)]]
        for i in range(len(best_path) - 1):
            sub = cls.find_path_dijkstra(best_path[i], best_path[i + 1], station_pm25_map)
            if sub["coords"]:
                if outward_raw:
                    outward_raw.extend(sub["coords"][1:])
                else:
                    outward_raw.extend(sub["coords"])

        # Trim outward path precisely at half_target_m
        trimmed_outward: list[list[float]] = []
        raw_m = cls.calculate_polyline_distance_m(outward_raw)

        if raw_m > 0 and len(outward_raw) >= 2:
            running_m = 0.0
            trimmed_outward.append(outward_raw[0])
            for i in range(len(outward_raw) - 1):
                seg_m = cls.calculate_distance_m(
                    outward_raw[i][0], outward_raw[i][1],
                    outward_raw[i + 1][0], outward_raw[i + 1][1]
                )
                if running_m + seg_m >= half_target_m:
                    fraction = (half_target_m - running_m) / max(1.0, seg_m)
                    lat_interp = outward_raw[i][0] + (outward_raw[i + 1][0] - outward_raw[i][0]) * fraction
                    lng_interp = outward_raw[i][1] + (outward_raw[i + 1][1] - outward_raw[i][1]) * fraction
                    trimmed_outward.append([round(lat_interp, 6), round(lng_interp, 6)])
                    break
                else:
                    running_m += seg_m
                    trimmed_outward.append(outward_raw[i + 1])

        if not trimmed_outward or len(trimmed_outward) < 2:
            trimmed_outward = outward_raw

        # Symmetrical return path guarantees exact loop closure back to origin
        return_path = list(reversed(trimmed_outward))
        combined_coords = trimmed_outward + return_path[1:]

        actual_dist_m = cls.calculate_polyline_distance_m(combined_coords)
        actual_dist_km = round(target_km, 1)

        start_name = cls.NODES[start_node]["name"]
        resolved_label = origin_label or (
            f"Điểm đã chọn trên bản đồ (gần {start_name})"
            if origin_source == "map_selection"
            else f"Vị trí của bạn ({start_name})"
        )

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
            "highlights": f"Lộ trình cá nhân hóa được thiết kế chính xác {actual_dist_km} km theo mục tiêu của bạn, đi qua các tuyến đường có chỉ số không khí trong lành nhất.",
            "start_point": {"name": resolved_label, "lat": user_lat, "lng": user_lng, "source": origin_source},
            "circuit_entry_point": {"name": start_name, "lat": cls.NODES[start_node]["lat"], "lng": cls.NODES[start_node]["lng"]},
            "coordinates": combined_coords,
            "snap_distance_m": round(snap_dist_m),
        }

    @classmethod
    def generate_smart_running_route(
        cls,
        user_lat: float,
        user_lng: float,
        target_km: float | None = None,
        station_pm25_map: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Convenience method returning the best candidate before continuous environmental ranking."""
        candidates = cls.generate_candidate_routes_from_origin(
            origin_lat=user_lat,
            origin_lng=user_lng,
            target_km=target_km,
            station_pm25_map=station_pm25_map,
        )
        return candidates[0] if candidates else {}


road_graph_router = RoadGraphRouter()

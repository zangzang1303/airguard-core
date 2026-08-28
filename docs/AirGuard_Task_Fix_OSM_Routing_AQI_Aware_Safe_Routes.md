# AIRGUARD AI — TASK FIX OSM ROUTING & AQI-AWARE SAFE ROUTE RECOMMENDATION

## 1. Mục tiêu

Sửa triệt để lỗi route hiện tại đang cắt chéo qua block/khu đất và không bám đúng đường thực tế trên map.

Mục tiêu mới:

> **Mọi tuyến chạy bộ / đi bộ / đạp xe phải được sinh từ road/path network thực tế của OpenStreetMap, sau đó mới được chấm điểm theo chất lượng không khí, cự ly, độ gần với người dùng và tính phù hợp với hoạt động.**

Nếu không có tuyến ngoài trời đủ tốt vì AQI quá xấu, tuyến quá xa, network không hợp lệ hoặc constraint không thể thỏa, Agent phải fallback sang:
- thời điểm khác;
- khu vực gần hơn;
- hoặc hoạt động trong nhà.

---

## 2. Lỗi hiện tại

Quan sát route hiện tại cho thấy các đoạn:
- nối chéo qua block;
- không theo đường thật;
- có góc gấp bất thường;
- có khả năng đang nối waypoint bằng polyline trực tiếp;
- route geometry không khớp road geometry.

Không được tiếp tục dùng cách:

```text
origin → waypoint → destination
```

bằng đoạn thẳng nếu không có road/path hợp lệ.

---

## 3. Invariant bắt buộc

### 3.1 Route phải bám network thực tế

Flow đúng:

```text
origin
→ snap vào node/edge hợp lệ
→ route trên OSM graph
→ lấy geometry thật của từng edge
→ merge edge geometry
→ render polyline
```

### 3.2 Không xuyên block / hồ / vùng không có đường

Route không được:
- cắt qua building;
- cắt qua hồ;
- cắt qua khu đất không có footway/path;
- đi vào private/restricted road trái activity profile.

### 3.3 Frontend chỉ render backend route geometry

Không dựng lại tuyến bằng cách nối:
```text
origin + waypoints + destination
```

### 3.4 Route theo activity

Running / Walking ưu tiên:
```text
footway
path
pedestrian
residential
living_street
service phù hợp
```

Cycling ưu tiên:
```text
cycleway
residential
living_street
road có bicycle access
```

---

## 4. Kiến trúc Route Engine mới

```text
USER REQUEST
    ↓
Resolve Origin / Destination / Target Distance
    ↓
Activity Profile
    ↓
Load OSM Graph
    ↓
Snap Origin / Destination
    ↓
Generate Candidate Routes
    ↓
Extract Edge Geometries
    ↓
Sample AQI Along Route
    ↓
Score Route
    ↓
Safety + Practicality Gate
    ↓
Best Route OR Fallback
    ↓
Chat Answer + Map Polyline
```

---

## 5. OSM Graph

Graph phải lưu tối thiểu:

```text
node_id
lat
lon

edge:
u
v
key
length
geometry
highway
name
access
foot
bicycle
service
surface
oneway
```

Phải có graph/filter phù hợp với từng activity.

---

## 6. Snap Origin / Destination

Input coordinate không được nối thẳng tới route.

Phải:

```text
input coordinate
→ nearest valid edge/node
→ snapped coordinate
→ route từ snapped point
```

Lưu:

```json
{
  "input_coordinate": [0, 0],
  "snapped_coordinate": [0, 0],
  "snap_distance_m": 18.4,
  "edge_id": "..."
}
```

### Snap Distance Gate

Nếu snap distance quá lớn:
- walking/running: config threshold;
- cycling: config threshold riêng.

Nếu vượt threshold:
> Chưa tìm được điểm vào mạng đường phù hợp đủ gần vị trí hiện tại.

Không vẽ một connector dài xuyên block.

---

## 7. Edge Geometry

Nếu edge có geometry chi tiết thì bắt buộc dùng geometry đó.

Pseudo:

```python
for edge in path_edges:
    geom = edge.geometry or straight_geometry(edge)
    orient_correctly(geom)
    append(geom)

route_geometry = merge_lines(...)
```

Phải đảm bảo:
- đúng thứ tự;
- không đảo edge;
- không có gap;
- không duplicate;
- không shortcut.

---

## 8. Candidate Route Generation

Không chỉ sinh một shortest path.

Tạo ít nhất 3 nhóm candidate:
- shortest distance;
- lowest exposure;
- balanced route.

Có thể dùng:
- k-shortest paths;
- Yen;
- A*;
- Dijkstra;
- alternative route generation.

MVP: 3–5 candidate là đủ.

---

## 9. Circular Running Route

Với yêu cầu:

> chạy khoảng 3 km từ vị trí hiện tại

Không tạo polygon tùy ý.

Phải tạo loop trên graph:

```text
origin node
→ candidate target nodes
→ path đi
→ path về khác nếu có
→ merge
→ validate total distance
```

### Loop quality
Phải kiểm:
- edge overlap;
- backtrack;
- self-intersection bất thường;
- distance error;
- turn penalty.

---

## 10. Distance Tolerance

Ví dụ user muốn 3 km:

```text
target = 3.0 km
tolerance = ±10%
```

Accept:
```text
2.7–3.3 km
```

Nếu không có route:
- mở rộng ±15%;
- sau đó mới fallback.

---

## 11. AQI Exposure theo toàn tuyến

Không dùng AQI của 1 station hoặc midpoint duy nhất.

Flow:

```text
route geometry
→ sample mỗi 20–50m
→ query spatial AQI
→ tính exposure
```

Mỗi sample:

```json
{
  "distance_along_route_m": 340,
  "aqi": 76
}
```

---

## 12. Route AQI Metrics

Tính ít nhất:
- mean AQI;
- median AQI;
- max AQI;
- P90 AQI;
- distance_above_threshold;
- exposure_score.

Ví dụ:

```text
exposure =
Σ(edge_length × normalized_aqi)
/
total_distance
```

---

## 13. Multi-objective Route Score

Không chọn tuyến chỉ vì ngắn nhất.

Đề xuất:

```text
route_score =
w_air * air_quality_score
+
w_distance * distance_fit_score
+
w_network * route_quality_score
+
w_safety * safety_score
+
w_access * origin_proximity_score
```

Ví dụ running:

```text
air_quality = 0.40
distance_fit = 0.20
route_quality = 0.15
safety = 0.15
origin_proximity = 0.10
```

Weight phải config.

---

## 14. Route Practicality

Một route sạch nhưng quá xa vị trí user không phải route tốt.

Tính:
```text
access_distance_to_route_start
```

Nếu user phải đi 2 km chỉ để bắt đầu một route chạy 3 km:
```text
route_not_practical = true
```

Có max access distance theo activity.

---

## 15. Hard Safety Gate

Có những route phải loại hoàn toàn.

Ví dụ nếu:
- mean AQI vượt threshold policy;
- P90 AQI quá cao;
- quá nhiều phần trăm tuyến nằm trong vùng ô nhiễm;
- route không hợp lệ theo graph.

Không optimize qua những route unsafe.

---

## 16. Profile-aware Safety

Threshold không nhất thiết giống nhau cho:
- general;
- sensitive;
- outdoor sport;
- children.

Policy phải do backend định nghĩa, không để LLM tự chọn threshold.

---

## 17. Fallback Strategy

Nếu không có outdoor route đủ tốt:

```text
1. thử route gần hơn / balanced hơn
2. nới nhẹ distance tolerance
3. đề xuất thời điểm khác nếu forecast tốt hơn
4. đề xuất khu vực gần hơn
5. đề xuất hoạt động trong nhà
```

---

## 18. Indoor Fallback Conditions

Fallback nếu:
- không có route candidate;
- AQI tất cả route quá xấu;
- route start quá xa;
- constraint distance không thể thỏa;
- network lỗi;
- route geometry không hợp lệ.

### Output ví dụ

> ⚠️ **Hiện tại mình chưa tìm được một tuyến chạy ngoài trời đủ phù hợp quanh vị trí của bạn.**
>
> Các tuyến gần nhất đều đi qua khu vực có AQI cao hơn mức ưu tiên.
>
> Bạn có thể:
> - chờ thời điểm AQI giảm;
> - chọn một khu vực gần hơn;
> - hoặc chuyển sang hoạt động trong nhà.
>
> 🏠 Nếu muốn, mình có thể tìm lựa chọn trong nhà gần bạn.

---

## 19. Time-aware Recommendation

Nếu hiện tại AQI xấu nhưng forecast cho thấy 21:00 tốt hơn:

> Hiện tại chưa có tuyến phù hợp, nhưng khoảng 21:00 chất lượng không khí được dự báo tốt hơn. Bạn có thể cân nhắc chạy vào thời điểm đó.

Có thể cung cấp:
```text
[Xem tuyến lúc 21:00]
[Chọn hoạt động trong nhà]
```

---

## 20. Route Validation trước khi trả

Bắt buộc validate:
- geometry valid;
- route follows graph;
- all segments map to OSM edge;
- no large geometry gap;
- distance reasonable;
- activity access allowed;
- AQI evidence valid;
- route start practical.

### Geometry gap
Nếu gap giữa hai segment > threshold cấu hình:
```text
route invalid
```

### Network compliance
Mỗi segment phải map được về OSM edge ID, trừ connector rất ngắn trong snap threshold.

---

## 21. Backend Route Output Contract

```json
{
  "status": "success",

  "route_id": "route_123",
  "activity": "running",
  "distance_km": 3.1,
  "duration_min": 21,

  "mean_aqi": 72,
  "max_aqi": 96,
  "p90_aqi": 88,
  "distance_above_threshold_m": 320,

  "access_distance_m": 42,

  "route_score": 0.81,

  "geometry": {},
  "edge_ids": []
}
```

Failure:

```json
{
  "status": "no_safe_route | no_network | too_far | no_environment_data",
  "fallback": {
    "type": "indoor | later_time | nearby_area",
    "reason": "..."
  }
}
```

---

## 22. Frontend Rule

Frontend:
- chỉ render `route.geometry`;
- không tái tạo route từ waypoints;
- không nối marker bằng line thẳng.

---

## 23. Chat Response Contract

### Success

> 🏃 **Mình đã tìm được một tuyến khoảng 3,1 km bám theo các đường đi bộ thực tế quanh khu VinUni.**
>
> - **Cự ly:** 3,1 km
> - **AQI trung bình trên tuyến:** 72
> - **AQI cao nhất trên tuyến:** 96
> - **Điểm xuất phát:** cách vị trí hiện tại khoảng 40 m
>
> Tuyến này có mức phơi nhiễm thấp hơn các phương án khác trong cùng phạm vi tìm kiếm.
>
> 🗺️ Mình đã vẽ tuyến theo mạng đường thực tế trên bản đồ.

### Too Far

> 📍 **Tuyến có chất lượng không khí tốt hơn hiện nằm khá xa vị trí của bạn nên mình không ưu tiên phương án đó.**
>
> Mình có thể tìm một tuyến gần hơn hoặc gợi ý hoạt động trong nhà gần vị trí hiện tại.

---

## 24. Tool Planner

```text
resolve_origin
→ load_activity_graph
→ snap_origin
→ generate_candidates
→ build_real_edge_geometry
→ sample_AQI
→ score_candidates
→ validate_routes
→ apply_safety_gate
→ return_best_or_fallback
```

---

## 25. Test Cases bắt buộc

### T01 — Network Compliance
100% route edges map về graph.

### T02 — Không xuyên block
Không còn segment chéo qua khu không có road/path.

### T03 — Snap gần road
Origin cách road 20m phải snap đúng network.

### T04 — Snap quá xa
Không vẽ connector dài xuyên block.

### T05 — 3km loop
Route trong tolerance và là graph-compliant loop.

### T06 — AQI Optimization
Route dài hơn chút nhưng AQI tốt hơn có thể thắng shortest route.

### T07 — Unsafe AQI
Tất cả route vượt safety gate → `no_safe_route`.

### T08 — Too Far
Route sạch nhưng start quá xa → không chọn top route.

### T09 — Indoor Fallback
No safe/practical route → có indoor fallback.

### T10 — Forecast Fallback
Current xấu, forecast tốt hơn → đề xuất later time.

---

## 26. Metrics nghiệm thu

Log:
- route_network_compliance_rate;
- average_snap_distance;
- invalid_geometry_rate;
- distance_error_rate;
- route_exposure_mean;
- route_exposure_p90;
- unsafe_route_rejection_rate;
- fallback_rate.

---

## 27. Acceptance Criteria

- [ ] Route bám đúng OSM road/path network.
- [ ] Không nối waypoint bằng line thẳng nếu không có road.
- [ ] Geometry lấy từ edge geometry.
- [ ] Snap có threshold.
- [ ] Graph filter theo walking/running/cycling.
- [ ] Có candidate routes.
- [ ] Có AQI sampling dọc tuyến.
- [ ] Có mean/max/P90 AQI.
- [ ] Có exposure score.
- [ ] Có multi-objective scoring.
- [ ] Có practicality score.
- [ ] Route quá xa user bị loại.
- [ ] Route AQI quá xấu bị loại.
- [ ] Có fallback later time / nearby area / indoor.
- [ ] Frontend render backend geometry.
- [ ] Chat mô tả đúng route trên map.
- [ ] Không còn route xuyên block như ảnh lỗi.

---

## 28. Definition of Done

Khi user hỏi:

> Tìm đoạn đường chạy bộ phù hợp nhất tối nay

Hệ thống phải:

1. lấy origin;
2. snap origin vào walking graph;
3. tạo nhiều candidate từ OSM network thật;
4. lấy geometry edge thật;
5. tính AQI dọc từng candidate;
6. loại route quá ô nhiễm;
7. loại route quá xa;
8. chọn route cân bằng tốt nhất;
9. render đúng geometry trên map;
10. chat trả distance + AQI + lý do;
11. nếu không có route tốt thì không vẽ bừa mà fallback hợp lý.

---

## 29. Nguyên tắc cuối cùng

> **Không được vẽ “đường nhìn có vẻ hợp lý”. Chỉ được vẽ route tồn tại trên network thực tế.**

Và:

> **Route tốt không chỉ là route ngắn. Route tốt phải hợp lệ về đường đi, gần người dùng, phù hợp activity và có mức phơi nhiễm môi trường chấp nhận được.**

Nếu không đạt các điều kiện đó:

> **Không đề xuất chạy ngoài trời; chuyển sang phương án an toàn hơn.**

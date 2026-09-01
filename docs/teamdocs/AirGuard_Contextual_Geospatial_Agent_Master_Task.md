# AIRGUARD AI — MASTER TASK SPEC
## XÂY DỰNG CONTEXTUAL GEOSPATIAL CHAT AGENT CHO VINHOMES OCEAN PARK 1

> **Mục tiêu:** Xây dựng lại AirGuard Chat Agent thành một trợ lý môi trường đô thị có ngữ cảnh, hiểu địa điểm trong Vinhomes Ocean Park 1 (OCP1), nhớ hội thoại, trả lời đúng yêu cầu người dùng, lấy dữ liệu môi trường có căn cứ, đồng bộ với bản đồ và tuyệt đối không lộ raw tool/function/backend output ra giao diện người dùng.

---

## 1. Mục tiêu sản phẩm

AirGuard Agent không phải chatbot đọc AQI hoặc chatbot gọi tool rồi in kết quả tool.

Agent phải trở thành:

> **Trợ lý môi trường và không gian dành riêng cho Vinhomes Ocean Park 1.**

Người dùng có thể hỏi tự nhiên như:

- Không khí ở VinUni thế nào?
- Khu nào ô nhiễm nhất?
- Tôi đang ở Sapphire, tìm cho tôi đường chạy khoảng 3 km sạch nhất.
- Còn khu Hồ Ngọc Trai thì sao?
- So với chỗ vừa rồi thì khu này tốt hơn không?
- Tối nay khoảng mấy giờ chạy tốt nhất?
- Không chạy nữa, có chỗ nào trong nhà không?
- Từ chỗ tôi sang Vincom có phải đi qua khu ô nhiễm không?
- Đường Hải Đăng hiện thế nào?
- Khu nào phù hợp cho trẻ nhỏ chơi ngoài trời?
- Tìm chỗ sạch hơn nhưng không quá xa Sapphire.

Agent phải hiểu chính xác từng câu và mối liên hệ giữa các lượt hội thoại.

---

## 2. Invariant bắt buộc

### 2.1 Grounding
Mọi chỉ số môi trường phải đến từ dữ liệu hợp lệ.

Không được tự bịa:
- AQI
- PM2.5
- CO2
- nhiệt độ
- tiếng ồn
- forecast
- trạng thái station
- route exposure

### 2.2 Fail Closed
Nếu dữ liệu invalid, stale, offline, missing hoặc tool error thì Agent phải nói rõ không đủ dữ liệu. Không suy đoán số.

### 2.3 Map không thay thế Chat
Nếu Map đã zoom, highlight, draw route hoặc show heatmap thì Chat vẫn phải trả lời đầy đủ.

### 2.4 Không lộ internal output
Không render trực tiếp:
- tool call
- function call
- JSON
- backend service
- model name
- IDW grid details
- map command
- raw coordinates
- database ID
- correlation ID

### 2.5 Location không được fallback sai
Nếu user hỏi Đường Hải Đăng mà hệ thống không resolve được thì không được tự nhảy sang VinUni. Phải hỏi lại hoặc báo chưa xác định được.

### 2.6 Chat và Map cùng Grounded Result
- Chat entity == Map entity
- Chat route == Map route
- Chat comparison == Map comparison

---

## 3. Kiến trúc tổng thể

```text
USER MESSAGE
    ↓
Conversation State Manager
    ↓
Semantic Understanding
    ├── Intent
    ├── Entity
    ├── Location
    ├── Time
    ├── Constraints
    └── User Goal
    ↓
Spatial Entity Resolver
    ↓
Tool Planner
    ↓
Validated Evidence
    ↓
Decision / Reasoning Layer
    ↓
Response Planner
    ↓
┌───────────────────────────────┐
│         FINAL OUTPUT          │
│  Chat Answer                  │
│  Evidence Summary             │
│  Follow-up Suggestions        │
│  Map Actions                  │
└───────────────────────────────┘
```

---

## 4. Module 1 — Conversation State Manager

### 4.1 Mục tiêu
Agent phải nhớ các thông tin quan trọng trong cuộc hội thoại hiện tại, không xử lý mỗi message như request độc lập.

### 4.2 Conversation State Schema

```json
{
  "conversation_id": "...",
  "last_intent": "recommend_running_route",
  "active_entities": [
    {
      "entity_id": "poi_vinuni",
      "name": "VinUniversity",
      "type": "poi"
    }
  ],
  "active_locations": ["poi_vinuni"],
  "comparison_context": {
    "location_a": "poi_vinuni",
    "location_b": "poi_lake_sweet"
  },
  "route_context": {
    "origin": "area_sapphire",
    "destination": "poi_lake_sweet",
    "requested_distance_km": 3.0,
    "activity": "running"
  },
  "time_context": {
    "type": "relative",
    "value": "tonight"
  },
  "active_metric": "AQI",
  "user_goal": "low_exposure_running",
  "constraints": {
    "avoid_polluted_area": true,
    "max_distance_km": 4
  }
}
```

### 4.3 Context cần lưu
- Location context
- Metric context
- Time context
- Activity context
- Comparison context
- User constraints
- Last intent
- Last resolved entities

### 4.4 Ví dụ context

**User:** Khu nào ô nhiễm nhất?  
**Agent:** Trục Đa Tốn.  
**User:** Còn VinUni thì sao?

Resolver phải hiểu:

```json
{
  "intent": "get_location_environment",
  "location": "VinUni",
  "metric": "AQI",
  "time": "current"
}
```

**User:** Tìm cho tôi đường chạy khoảng 5 km.  
**User:** Ngắn hơn chút.

Resolver phải giữ activity/origin/time và chỉ giảm distance.

---

## 5. Module 2 — Spatial Knowledge Base OCP1

### 5.1 Mục tiêu
Xây dựng một nơi lưu trữ riêng cho toàn bộ không gian OCP1 để Agent hiểu:
- đường
- ngõ
- phân khu
- tòa nhà
- trường học
- bệnh viện
- trung tâm thương mại
- hồ
- công viên
- quảng trường
- trạm quan trắc
- điểm thể thao
- landmark

### 5.2 Storage đề xuất
Ưu tiên:
```text
PostgreSQL + PostGIS
```

MVP tối thiểu:
```text
PostgreSQL + GeoJSON
```

### 5.3 Bảng `spatial_entities`

```sql
id
canonical_name
entity_type
latitude
longitude
geometry
parent_id
description
environment_character
is_active
metadata
```

### 5.4 `entity_type`
```text
road
road_segment
building
residential_area
school
university
hospital
mall
park
lake
square
sports
station
landmark
gate
intersection
```

### 5.5 Bảng `spatial_aliases`

```sql
id
entity_id
alias
normalized_alias
language
priority
```

Ví dụ:

```text
entity_id: road_hai_dang
canonical_name: Đường Hải Đăng

aliases:
- hải đăng
- hai dang
- đường hải đăng
- trục hải đăng
- hải đăng 1
- hải đăng 2
- hải đăng 3
- hải đăng 5
- hải đăng 6
- hải đăng 8
```

### 5.6 Bảng `spatial_relationships`

```sql
source_entity_id
relationship
target_entity_id
distance_m
metadata
```

Ví dụ:

```text
VinUni near Đường Đại Dương
VinUni near Hồ Ngọc Trai
S04 covers VinUni
```

### 5.7 Bảng `station_spatial_coverage`

```sql
station_id
entity_id
distance_m
weight
```

Mục đích: khi user hỏi một địa điểm, hệ thống biết station nào liên quan và evidence nào cần dùng.

### 5.8 GeoJSON đề xuất

```text
ocp1_roads.geojson
ocp1_buildings.geojson
ocp1_areas.geojson
ocp1_pois.geojson
ocp1_boundaries.geojson
```

---

## 6. Spatial Entity Resolver

### 6.1 Input
```text
"đường hải đăng 6"
```

### 6.2 Output
```json
{
  "matched": true,
  "entity_id": "road_hai_dang_6",
  "canonical_name": "Hải Đăng 6",
  "entity_type": "road_segment",
  "confidence": 0.97
}
```

### 6.3 Resolver strategy
1. exact canonical match
2. exact alias match
3. normalized Vietnamese match
4. fuzzy match
5. semantic search
6. parent-area inference
7. clarification

### 6.4 Confidence thấp
Không tự đoán.

Ví dụ:
> Bạn đang nói đến **Hải Đăng 6** hay toàn bộ **trục Hải Đăng**?

---

## 7. Chuẩn hóa tiếng Việt

Resolver phải hiểu các biến thể:

```text
vinuni
Vin Uni
đại học vinuni
truong vinuni

hai dang
hải đăng
đg hải đăng
duong hai dang

ngoc trai
ngọc trai
ho ngoc trai
hồ ngọc trai
```

Normalization:
- lowercase
- trim spaces
- Unicode normalization
- Vietnamese accent normalization
- abbreviation expansion
- common typo handling

---

## 8. Core OCP1 Catalog

### Roads
- Trục Đa Tốn
- Lý Thánh Tông
- Hải Đăng
- Đại Dương
- San Hô
- Sao Biển
- Ngọc Trai
- Biển Hồ

### Residential Areas
- The Sapphire
- The Zenpark
- The Pavilion
- Ngọc Trai
- San Hô
- Sao Biển
- Hải Âu
- An Đào

### POIs
- VinUniversity
- TechnoPark
- Vincom Mega Mall Ocean Park
- Vinmec Ocean Park
- Vinschool
- Hồ Ngọc Trai
- Biển Hồ Nước Mặn
- Quảng trường Cá Voi

### Monitoring Stations
- S01 — Trục Đa Tốn
- S02 — Khu Sapphire
- S03 — Ven Hồ Ngọc Trai
- S04 — VinUni
- S05 — Khu Hải Âu

---

## 9. Module 3 — Semantic Understanding

Mỗi message phải parse thành structured request:

```json
{
  "intent": "...",
  "entities": [],
  "locations": [],
  "metric": null,
  "time": null,
  "activity": null,
  "comparison": null,
  "constraints": [],
  "negations": [],
  "user_goal": null,
  "response_expectation": null
}
```

---

## 10. Intent taxonomy

### Environment
```text
environment.current
environment.location
environment.compare
environment.ranking_best
environment.ranking_worst
environment.forecast
environment.explain
```

### Spatial
```text
spatial.locate
spatial.compare
spatial.nearby
spatial.route
```

### Activity
```text
activity.running
activity.walking
activity.indoor
activity.children
activity.sensitive_user
```

### Decision
```text
decision.best_location
decision.best_time
decision.best_route
decision.safer_alternative
```

### Conversation
```text
conversation.followup
conversation.clarification
conversation.social
```

### Operations
```text
operation.warning_proposal
operation.ventilation_proposal
```

---

## 11. Negation / Pivot Handling

User:
```text
Ngoài chạy bộ tôi muốn hoạt động khác trong nhà.
```

Phải parse:
```json
{
  "intent": "activity.indoor",
  "negations": ["running"]
}
```

Không được route sang running.

---

## 12. Module 4 — Tool Planner

Tool Planner chọn dữ liệu cần lấy.

### Ví dụ: “Khu nào đang ô nhiễm nhất?”
```text
fetch station current values
validate freshness
rank AQI
find best alternative
```

### Ví dụ: “Tìm route 3km sạch nhất từ Sapphire.”
```text
resolve Sapphire
fetch spatial AQI
load OSM graph
generate candidate routes
estimate exposure
rank routes
```

---

## 13. Module 5 — Evidence Bundle

Tool output phải được chuẩn hóa:

```json
{
  "request_id": "...",
  "locations": [],
  "environment": [],
  "forecast": [],
  "route_candidates": [],
  "station_evidence": [],
  "spatial_evidence": [],
  "freshness": {
    "valid": true
  }
}
```

---

## 14. Module 6 — Decision / Reasoning Layer

Không dump dữ liệu.

Agent phải có khả năng:
- comparison
- ranking
- selection
- recommendation
- time selection
- route optimization

Ví dụ forecast:
```text
19:00 AQI 82
20:00 AQI 68
21:00 AQI 51
22:00 AQI 55
```

User hỏi:
```text
Tối nay lúc nào chạy tốt nhất?
```

Agent phải kết luận:
> **21:00 là thời điểm phù hợp nhất.**

---

## 15. Module 7 — Response Planner

Response Planner quyết định:
- User thực sự muốn biết gì?
- Câu đầu trả lời gì?
- Metric nào cần hiển thị?
- Có recommendation không?
- Map đã làm gì?
- Có follow-up nào hữu ích?

Schema:

```json
{
  "response_type": "route_recommendation",
  "headline_goal": "recommend_best_route",
  "must_include": [
    "route",
    "distance",
    "average_aqi",
    "reason"
  ],
  "optional": [
    "pm25",
    "best_time"
  ],
  "map_feedback": true,
  "verbosity": "medium"
}
```

---

## 16. Response Types

```text
direct_fact
location_status
comparison
ranking
forecast
best_time
route
recommendation
health_advice
indoor_alternative
clarification
error
proposal
```

---

## 17. Response Contract

### `direct_fact`
Bắt buộc:
```text
location
metric
value
category
```

### `comparison`
Bắt buộc:
```text
location_a
value_a
location_b
value_b
winner
reason
```

### `route`
Bắt buộc:
```text
origin
destination hoặc route description
distance
average_aqi
reason
recommendation
```

### `ranking`
Bắt buộc:
```text
location
value
category
alternative
```

---

## 18. User-facing format

```text
DIRECT ANSWER

KEY INFORMATION

ACTION / RECOMMENDATION

MAP FEEDBACK

DATA NOTE
```

---

## 19. Ví dụ output theo context

### User
```text
Khu nào đang ô nhiễm nhất?
```

### Correct
```text
⚠️ Trục Đa Tốn hiện là khu vực có chất lượng không khí kém nhất.

• AQI: 146 — Không tốt cho nhóm nhạy cảm
• PM2.5: 56 µg/m³
• Khu vực tốt hơn để thay thế: VinUni

Nếu bạn đang định đi bộ hoặc tập thể thao, nên tránh khu Đa Tốn lúc này.

📍 Mình đã đánh dấu khu vực này trên bản đồ.

Dữ liệu mô phỏng · cập nhật vừa xong
```

### Follow-up
```text
Còn VinUni thì sao?
```

### Correct
```text
🌿 VinUni hiện có chất lượng không khí tốt hơn Trục Đa Tốn.

• AQI VinUni: 53
• AQI Trục Đa Tốn: 146

Nếu bạn đang chọn nơi để đi bộ hoặc tập nhẹ, VinUni phù hợp hơn lúc này.

📍 Mình đã chuyển bản đồ sang VinUni để bạn so sánh.
```

---

## 20. Map Action Contract

Map Actions là structured output riêng:

```json
{
  "type": "highlight_entity",
  "entity_id": "station_s01"
}
```

hoặc:

```json
{
  "type": "draw_route",
  "route_id": "route_123"
}
```

Frontend thực thi. Chat không render JSON này.

---

## 21. Map / Chat Consistency Check

Trước final response:

```text
IF chat location != map location
    reject response

IF chat route != map route
    reject response

IF chat metric != evidence metric
    reject response
```

---

## 22. Follow-up Suggestions

### Worst Area
- Tìm khu sạch hơn
- Tìm đường tránh khu này
- Xem dự báo tối nay

### Location
- So sánh khu khác
- Xem dự báo
- Tìm route gần đây

### Route
- Rút xuống 2 km
- Tăng lên 5 km
- Tìm thời điểm sạch hơn

---

## 23. Data Source Note

Trong chat thường chỉ cần:

```text
Dữ liệu mô phỏng AirGuard AI · cập nhật 2 phút trước
```

Chi tiết kỹ thuật như simulator, IDW, wind correction, station IDs, timestamp đưa vào `Xem nguồn`.

---

## 24. Memory Policy

### Short-term memory nên lưu
- current location
- last locations
- last intent
- active metric
- route constraints
- time context
- comparison context

### Không lưu vào memory
- raw tool payload lớn
- toàn bộ heatmap
- toàn bộ routing graph
- toàn bộ telemetry historical

Các dữ liệu đó phải fetch lại từ system of record.

---

## 25. State Invalidation

Context cũ phải bị invalid khi user đổi chủ đề rõ ràng.

Ví dụ:

```text
User: Tìm route 5 km.
User: AQI VinUni bao nhiêu?
```

Route context không được ảnh hưởng câu sau.

---

## 26. Context Confidence

Nếu reference mơ hồ như:
```text
ở đó
chỗ kia
khu đó
```

và có nhiều candidate thì phải hỏi lại:

> Bạn đang nói tới **VinUni** hay **Hồ Ngọc Trai**?

Không tự đoán khi confidence thấp.

---

## 27. Technical Response Mode

Chỉ bật khi user hỏi:
- AirGuard nội suy như thế nào?
- 468 điểm là gì?
- IDW hoạt động ra sao?
- Nguồn dữ liệu từ đâu?

Lúc đó mới được nói về:
- IDW
- wind adjustment
- simulator
- grid
- OSM
- forecast model

---

## 28. Backend API Response đề xuất

```json
{
  "conversation_id": "...",
  "intent": "environment.ranking_worst",
  "resolved_context": {
    "locations": [],
    "metric": "AQI",
    "time": "current"
  },
  "answer": {
    "headline": "Trục Đa Tốn hiện là khu vực ô nhiễm nhất.",
    "highlights": [],
    "recommendation": "...",
    "map_feedback": "...",
    "data_note": "..."
  },
  "follow_up_actions": [],
  "map_actions": [],
  "evidence_refs": [],
  "debug": null
}
```

---

## 29. Debug Isolation

Internal debug có thể tồn tại nhưng:

```text
debug != user-facing response
```

Chỉ developer/admin được xem.

---

## 30. Test Suite bắt buộc

### Group A — Location Resolver
- VinUni
- vin uni
- đại học vinuni
- Hải Đăng
- hai dang
- Hải Đăng 6
- Sapphire
- The Sapphire
- Hồ Ngọc Trai
- ho ngoc trai
- Vincom
- Vinmec

### Group B — Follow-up
```text
Khu nào ô nhiễm nhất?
→ Còn VinUni?

VinUni hay Hồ Ngọc Trai sạch hơn?
→ Còn Sapphire?

Tìm route 5 km.
→ Ngắn hơn chút.
→ Sạch hơn nữa.
```

### Group C — Negation
- Không chạy bộ.
- Ngoài chạy bộ tôi muốn trong nhà.
- Không đi qua Đa Tốn.
- Không quá 3 km.

### Group D — Unknown Location
- ABC
- khu XYZ
- đường không tồn tại

Không fallback location sai.

### Group E — Tool Leakage
Response không được chứa:
```text
tool_call
function_call
idw-dispersion
spatial_idw
map_actions
JSON
backend
```

### Group F — Map Sync
```text
Chat entity == map target
Chat route == displayed route
Chat comparison == highlighted entities
```

---

## 31. Acceptance Criteria

- Agent hiểu follow-up khi context rõ.
- Nhận diện chính xác POI/road/area trong catalog OCP1.
- Không gán địa điểm khác khi resolve thất bại.
- Không trả raw backend text.
- Negation và follow-up không bị keyword router phá.
- 100% số liệu có evidence.
- Map action và chat answer thống nhất.
- Mọi yêu cầu user hỏi phải có mặt trong output.

---

## 32. Definition of Done

- [ ] Có Conversation State Manager.
- [ ] Có structured context schema.
- [ ] Có Spatial Knowledge Base OCP1.
- [ ] Có bảng entities.
- [ ] Có bảng aliases.
- [ ] Có relationships.
- [ ] Có station coverage mapping.
- [ ] Có GeoJSON / geometry layer.
- [ ] Có Spatial Entity Resolver.
- [ ] Có confidence + clarification.
- [ ] Có Semantic Intent Router.
- [ ] Có negation handling.
- [ ] Có Tool Planner.
- [ ] Có Evidence Bundle.
- [ ] Có Decision Layer.
- [ ] Có Response Planner.
- [ ] Có Response Composer.
- [ ] Có Response Contract Validator.
- [ ] Có Map/Chat Consistency Validator.
- [ ] Không lộ raw tool/function.
- [ ] Unknown location không fallback sai.
- [ ] Context multi-turn hoạt động.
- [ ] Test suite các case chính pass.
- [ ] Grounding tests pass 100%.

---

## 33. Thứ tự triển khai

### Phase 1 — Fix kiến trúc
```text
Unified Gateway
Response Composer
Map/Chat output separation
No raw output
```

### Phase 2 — Spatial Knowledge Base
```text
OCP1 entity catalog
aliases
geometry
relationships
resolver
```

### Phase 3 — Conversation Context
```text
state manager
follow-up resolution
reference resolution
constraints
```

### Phase 4 — Semantic Agent
```text
intent
entity
time
negation
comparison
user goal
```

### Phase 5 — Decision Agent
```text
ranking
comparison
best time
best route
personalized recommendation
```

### Phase 6 — Production UX
```text
follow-up chips
evidence drawer
typing/loading states
map feedback
debug isolation
```

---

## 34. Kiến trúc đích cuối

```text
                          AIRGUARD AI
                               │
                      Conversation Memory
                               │
                               ▼
                     Semantic Understanding
                               │
                  ┌────────────┼────────────┐
                  ▼            ▼            ▼
                Intent       Entity       Context
                  │            │            │
                  └────────────┼────────────┘
                               ▼
                    OCP1 Spatial Knowledge
                               │
                               ▼
                       Spatial Resolver
                               │
                               ▼
                         Tool Planner
                   ┌───────────┼───────────┐
                   ▼           ▼           ▼
               Telemetry      IDW      OSM/Forecast
                   │           │           │
                   └───────────┼───────────┘
                               ▼
                         Evidence Bundle
                               │
                               ▼
                         Decision Engine
                               │
                               ▼
                        Response Planner
                      ┌────────┴────────┐
                      ▼                 ▼
                  Chat Answer       Map Actions
                      │                 │
                      └────────┬────────┘
                               ▼
                           FRONTEND
```

---

## 35. Nguyên tắc sản phẩm cuối cùng

Agent phải tạo cảm giác:

> **“Tôi có thể hỏi AirGuard như hỏi một người hiểu rất rõ Ocean Park 1.”**

Các câu như:

```text
Tôi đang ở Sapphire, tối nay chạy 3 km thì nên đi hướng nào?
Không muốn chạy nữa, gần đây có chỗ nào trong nhà không?
Chỗ vừa rồi với VinUni bên nào sạch hơn?
Tôi muốn sang Vincom nhưng tránh Đa Tốn.
Khoảng 9 giờ tối khu Hồ Ngọc Trai thế nào?
Đưa tôi tới chỗ sạch nhất gần đây.
```

Agent phải:
1. hiểu câu hỏi;
2. nhớ context;
3. hiểu địa điểm;
4. lấy dữ liệu từ backend;
5. reasoning đúng;
6. trả lời tiếng Việt tự nhiên;
7. thao tác Map đúng;
8. không để người dùng thấy cơ chế nội bộ.

---

## 36. Câu chốt cho Dev / Coding Agent

> **Không xây một chatbot biết gọi tool. Hãy xây một contextual geospatial assistant dành riêng cho OCP1: hiểu người dùng, hiểu địa điểm, nhớ hội thoại, lấy đúng evidence, đưa ra quyết định đúng và trình bày kết quả tự nhiên đồng bộ với bản đồ.**

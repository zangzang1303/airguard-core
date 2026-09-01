# AIRGUARD AI — TASK FIX INTENT, SCOPE & CONTEXT CORRECTION

## 1. Mục tiêu

Sửa lỗi Agent Chat đang **trả lời đúng format nhưng sai ý người dùng**.

Ví dụ hiện tại:

### User
> Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1

### Agent hiện tại
> VinUni hiện là khu vực có chất lượng không khí tốt nhất...

Lỗi này không còn nằm ở UI format mà nằm ở:

- Intent Router
- Scope Resolver
- Conversation Context
- Context Correction
- Response Planner
- Map Action Planner

Mục tiêu sau khi sửa:

> Khi người dùng hỏi **tổng quan toàn khu OCP1**, Agent phải hiểu scope là **toàn Ocean Park 1**, trả lời tổng quan toàn khu và điều khiển bản đồ theo phạm vi toàn khu.

---

# 2. Lỗi cần sửa

## BUG-01 — Sai Intent

Input:

```text
Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1
```

Hệ thống đang route sang:

```text
environment.ranking_best
```

hoặc:

```text
decision.best_location
```

Trong khi intent đúng phải là:

```text
environment.overview
```

---

## BUG-02 — Sai Scope

User nói rõ:

```text
cả khu Ocean Park 1
```

nhưng hệ thống lại chọn một địa điểm cụ thể:

```text
VinUni
```

Scope đúng:

```json
{
  "scope_type": "area",
  "scope_id": "ocp1",
  "scope_name": "Vinhomes Ocean Park 1"
}
```

Không được giữ một location cũ nếu user đã sửa thành toàn khu.

---

## BUG-03 — Sai Context Inheritance

Nếu lượt trước Agent đang nói về VinUni, rồi user nói:

```text
Ý là hỏi chung cả khu Ocean Park 1
```

thì context mới phải **ghi đè context cũ**.

Không được tiếp tục giữ:

```text
active_location = VinUni
```

Phải chuyển thành:

```text
active_scope = OCP1
active_location = null
```

---

## BUG-04 — Sai Map Action

Khi user hỏi toàn khu:

Không được:

```text
zoom VinUni
highlight VinUni
```

Phải:

```text
fit OCP1 bounds
show all monitoring stations
show current AQI heatmap
```

---

# 3. Thêm Intent mới: `environment.overview`

Bổ sung intent:

```text
environment.overview
```

Dùng khi người dùng hỏi tổng quan chất lượng không khí trên toàn khu.

---

# 4. Các câu phải nhận diện là `environment.overview`

Ví dụ:

```text
Chất lượng không khí Ocean Park 1 thế nào?
Không khí toàn khu hiện thế nào?
Tình hình chung cả khu thế nào?
AQI toàn Ocean Park 1?
Tổng quan chất lượng không khí OCP1?
Chất lượng không khí chung của cả khu?
Ý tôi hỏi toàn khu.
Ý là hỏi chung cả Ocean Park.
Toàn khu thì sao?
Cả Ocean Park thì sao?
Tình trạng không khí chung hiện tại?
```

---

# 5. Structured Intent Output

Ví dụ input:

```text
Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1
```

Output bắt buộc:

```json
{
  "intent": "environment.overview",
  "scope": {
    "type": "area",
    "id": "ocp1",
    "name": "Vinhomes Ocean Park 1"
  },
  "metric": "AQI",
  "time": "current",
  "location": null
}
```

---

# 6. Routing Precedence mới

Thứ tự ưu tiên đề xuất:

```text
1. Safety / Injection
2. Conversation Correction
3. Scope Detection
4. Indoor / Negation
5. Comparison
6. Overview
7. Ranking Best / Worst
8. POI / Road Query
9. Route
10. Forecast
11. Station Telemetry
12. Fallback
```

Điểm quan trọng:

> `environment.overview` phải được xét trước `ranking_best` và `recommendation`.

---

# 7. Rule nhận diện Overview

Pseudo-code:

```python
OVERVIEW_PATTERNS = [
    "toàn khu",
    "cả khu",
    "chung của cả khu",
    "tổng quan",
    "toàn ocean park",
    "toàn ocp",
    "ocean park 1 thế nào",
    "tình hình chung",
    "không khí chung",
    "chất lượng không khí chung",
]
```

Nếu match:

```python
intent = "environment.overview"
scope = "ocp1"
```

---

# 8. Không dùng keyword đơn lẻ để quyết định Ranking

Không được chỉ vì message có:

```text
chất lượng không khí
```

rồi tự chuyển thành:

```text
find_best_location
```

Ranking chỉ được kích hoạt khi có tín hiệu rõ ràng:

```text
sạch nhất
tốt nhất
ô nhiễm nhất
xấu nhất
cao nhất
thấp nhất
```

---

# 9. Thêm Conversation Correction

Bổ sung intent:

```text
conversation.correction
```

Dùng khi user đang sửa cách hiểu trước đó của Agent.

Các phrase:

```text
ý là...
ý tôi là...
không, tôi hỏi...
không phải...
tôi hỏi chung...
ý tôi hỏi toàn khu...
không phải VinUni...
tôi muốn nói...
```

---

# 10. Correction Parser

Ví dụ:

### Previous state

```json
{
  "intent": "environment.ranking_best",
  "location": "VinUni",
  "scope": "poi"
}
```

### User

```text
Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1
```

### Parse

```json
{
  "intent": "conversation.correction",
  "corrected_request": {
    "intent": "environment.overview",
    "scope": {
      "type": "area",
      "id": "ocp1"
    }
  }
}
```

---

# 11. Context Invalidation

Khi correction xảy ra:

```text
invalidate:
- previous_location
- previous_ranking_intent
- previous_map_focus
```

Giữ lại nếu cần:

```text
metric = AQI
time = current
```

---

# 12. Conversation State Update

Sau correction:

```json
{
  "last_intent": "environment.overview",
  "active_scope": "ocp1",
  "active_location": null,
  "active_metric": "AQI",
  "time_context": "current",
  "comparison_context": null
}
```

---

# 13. Scope Resolver

Thêm một bước riêng để nhận diện scope.

Supported scope:

```text
station
poi
road
road_segment
residential_area
sub_area
ocp1
```

Ví dụ:

```text
VinUni
→ poi

Đường Hải Đăng
→ road

Sapphire
→ residential_area

Ocean Park 1
→ ocp1
```

---

# 14. Scope Precedence

Nếu message mới có scope rõ ràng:

```text
new explicit scope > previous context scope
```

Ví dụ:

Previous:

```text
VinUni
```

New user:

```text
toàn Ocean Park 1
```

Kết quả:

```text
scope = OCP1
location = null
```

---

# 15. Overview Tool Plan

Với:

```text
environment.overview
```

Tool Planner phải lấy:

```text
1. current status của 5 stations
2. validate freshness
3. overall representative AQI
4. best location
5. worst location
6. optional spatial distribution summary
```

Không chỉ lấy 1 station.

---

# 16. Cách tính "tổng quan toàn khu"

Không nên chỉ lấy:

```text
min AQI
```

hoặc:

```text
VinUni
```

Có thể tạo một structured summary:

```json
{
  "overall_aqi": 86,
  "overall_category": "Trung bình",
  "best_location": {
    "name": "VinUni",
    "aqi": 71
  },
  "worst_location": {
    "name": "Trục Đa Tốn",
    "aqi": 128
  },
  "station_count": 5
}
```

`overall_aqi` phải được backend xác định bằng rule rõ ràng.

Ví dụ:
- mean AQI các station hợp lệ;
- median;
- weighted representative AQI;
- hoặc một metric tổng quan đã định nghĩa.

Không để LLM tự tính tùy ý.

---

# 17. Response Contract cho `environment.overview`

Required:

```text
scope
overall_status
overall_metric
best_location
worst_location
practical_conclusion
```

Optional:

```text
PM2.5 summary
station count
short forecast
```

---

# 18. Format trả lời chuẩn

### User

```text
Chất lượng không khí chung của cả khu Ocean Park 1 thế nào?
```

### Target

```text
🌿 Chất lượng không khí tại Ocean Park 1 hiện nhìn chung ở mức Trung bình.

• AQI đại diện toàn khu: 86
• Khu có AQI thấp nhất: VinUni — AQI 71
• Khu có AQI cao nhất: Trục Đa Tốn — AQI 128

Chất lượng không khí đang khác nhau giữa các khu vực. Nếu bạn muốn hoạt động ngoài trời, nên ưu tiên các khu có AQI thấp hơn và hạn chế thời gian ở vùng gần trục giao thông đang có chỉ số cao hơn.

🗺️ Mình đã hiển thị tổng quan chất lượng không khí toàn Ocean Park 1 trên bản đồ.

Dữ liệu mô phỏng AirGuard AI · cập nhật vừa xong
```

Các số trên chỉ là ví dụ format.

Production phải dùng tool result thật.

---

# 19. Không được trả kiểu sau

```text
VinUni hiện là khu vực sạch nhất...
```

nếu user hỏi toàn khu.

---

Không được:

```text
Bản đồ IDW có range...
```

nếu user không hỏi kỹ thuật.

---

Không được:

```text
468 điểm grid...
```

---

Không được:

```text
spatial_idw_dispersion_model...
```

---

# 20. Map Actions cho Overview

Target:

```json
[
  {
    "type": "fit_scope",
    "scope_id": "ocp1"
  },
  {
    "type": "show_heatmap",
    "metric": "AQI"
  },
  {
    "type": "show_stations",
    "station_ids": ["S01", "S02", "S03", "S04", "S05"]
  }
]
```

Không zoom riêng VinUni.

---

# 21. Map/Chat Consistency

Validator:

```text
IF intent == environment.overview:
    map_scope MUST == OCP1
```

Nếu:

```text
chat says OCP1 overview
map target == VinUni
```

=> reject / regenerate map action.

---

# 22. Response Planner Rule

Nếu intent:

```text
environment.overview
```

Response Planner:

```json
{
  "response_type": "overview",
  "headline_goal": "summarize_ocp1_air_quality",
  "must_include": [
    "overall_status",
    "overall_aqi",
    "best_location",
    "worst_location"
  ],
  "map_feedback": "overview",
  "verbosity": "medium"
}
```

---

# 23. Context Correction Priority

Conversation correction phải có priority rất cao.

Pseudo-code:

```python
if detect_correction(message):
    corrected = parse_corrected_request(message)
    state = invalidate_conflicting_context(state, corrected)
    return route(corrected)
```

---

# 24. Correction Examples

## Case 1

```text
Agent: VinUni sạch nhất.
User: Không, tôi hỏi toàn khu.
```

Expected:

```text
intent = environment.overview
scope = OCP1
```

---

## Case 2

```text
Agent: Đa Tốn đang ô nhiễm nhất.
User: Ý tôi là VinUni.
```

Expected:

```text
intent = environment.location
location = VinUni
```

---

## Case 3

```text
Agent: Route chạy bộ...
User: Không chạy, tôi muốn đi bộ.
```

Expected:

```text
activity = walking
invalidate running
```

---

## Case 4

```text
User: Chất lượng không khí chung?
Agent: Bạn muốn khu nào?
User: Cả Ocean Park 1.
```

Expected:

```text
environment.overview
scope = OCP1
```

---

# 25. Scope Keyword Catalog

```text
OCP1:
- ocean park 1
- ocean park
- ocp1
- cả khu
- toàn khu
- toàn ocean park
- cả ocean park
- toàn khu đô thị
- chung toàn khu
```

Cẩn thận:

`Ocean Park` có thể mơ hồ nếu hệ thống sau này hỗ trợ OCP2/OCP3.

Trong MVP hiện tại có thể normalize về OCP1 nếu product scope chỉ có OCP1.

---

# 26. Intent Classification Contract

Router output bắt buộc có:

```json
{
  "intent": "...",
  "confidence": 0.0,
  "scope": {},
  "entities": [],
  "inherited_context": [],
  "overridden_context": [],
  "needs_clarification": false
}
```

---

# 27. Confidence Rule

Ví dụ:

```text
"cả khu Ocean Park 1"
```

phải có confidence cao cho:

```text
scope = OCP1
```

Nếu không chắc:

```text
needs_clarification = true
```

---

# 28. Test Cases bắt buộc

## T01

Input:

```text
Chất lượng không khí chung của Ocean Park 1 thế nào?
```

Expected:

```text
intent = environment.overview
scope = OCP1
```

---

## T02

Input:

```text
Khu nào sạch nhất?
```

Expected:

```text
intent = environment.ranking_best
```

---

## T03

Input:

```text
Khu nào ô nhiễm nhất?
```

Expected:

```text
intent = environment.ranking_worst
```

---

## T04

Input:

```text
Không khí VinUni thế nào?
```

Expected:

```text
intent = environment.location
location = VinUni
```

---

## T05 — Correction

Conversation:

```text
User: Chất lượng không khí thế nào?
Agent: VinUni đang tốt nhất.
User: Ý là hỏi chung cả khu Ocean Park 1.
```

Expected:

```text
intent = environment.overview
scope = OCP1
location = null
```

---

## T06 — Map

Nếu T05:

Expected map:

```text
fit OCP1
show heatmap
show all stations
```

Not:

```text
zoom VinUni
```

---

## T07 — Context Override

Previous context:

```text
VinUni
```

New input:

```text
toàn khu thì sao?
```

Expected:

```text
scope = OCP1
```

---

# 29. Acceptance Criteria

- [ ] Có `environment.overview`.
- [ ] Có `conversation.correction`.
- [ ] Có Scope Resolver.
- [ ] Explicit scope override context cũ.
- [ ] Overview không route sang best location.
- [ ] Overview query lấy dữ liệu toàn 5 station.
- [ ] Overview response có summary toàn khu.
- [ ] Overview map fit toàn OCP1.
- [ ] Không highlight riêng VinUni khi user hỏi toàn khu.
- [ ] Correction invalidates conflicting context.
- [ ] Chat và Map cùng scope.
- [ ] Không lộ raw tool output.
- [ ] Test cases overview/correction pass 100%.

---

# 30. Definition of Done

Bug được coi là sửa xong khi conversation sau hoạt động đúng:

```text
User:
Chất lượng không khí thế nào?

Agent:
Bạn muốn kiểm tra khu vực cụ thể hay tổng quan toàn Ocean Park 1?

User:
Ý là hỏi chất lượng không khí chung của cả khu Ocean Park 1.

Agent:
🌿 Chất lượng không khí tại Ocean Park 1 hiện nhìn chung ở mức Trung bình.

• AQI đại diện toàn khu: ...
• Khu có AQI thấp nhất: ...
• Khu có AQI cao nhất: ...

...

🗺️ Mình đã hiển thị tổng quan toàn khu trên bản đồ.
```

Map đồng thời:
- fit toàn OCP1;
- show heatmap;
- show 5 station;
- không zoom riêng một POI.

---

# 31. Nguyên tắc cuối cùng

> **Agent phải phân biệt rõ “tổng quan toàn khu” với “khu tốt nhất / khu xấu nhất”.**

Và:

> **Khi user nói “ý tôi là...”, thông tin mới phải được xem là correction có quyền ghi đè cách hiểu trước đó của Agent.**

Đây là yêu cầu bắt buộc để Agent trả lời đúng ngữ cảnh hội thoại.

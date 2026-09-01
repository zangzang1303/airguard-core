# AIRGUARD AI — ĐƯỜNG HƯỚNG PHÁT TRIỂN AGENT CHAT

## 1. Mục tiêu phát triển

AirGuard AI không nên phát triển Agent Chat theo hướng chỉ là một chatbot đọc và báo cáo chỉ số môi trường.

Mục tiêu đúng nên là:

> **Agent hiểu chính xác người dùng đang yêu cầu điều gì, lấy đủ dữ liệu và bằng chứng cần thiết, trả ra đúng output tương ứng với yêu cầu, đồng thời đồng bộ các thông tin không gian cần thiết lên bản đồ.**

Agent Chat cần trở thành **trợ lý đô thị thông minh theo ngữ cảnh**, có khả năng:
- Hiểu ý định người dùng.
- Hiểu địa điểm, tuyến đường, khu vực và ngữ cảnh không gian tại Vinhomes Ocean Park 1.
- Hiểu hội thoại đa lượt.
- Gọi đúng tool và lấy đúng dữ liệu.
- Không bịa số liệu môi trường.
- Trả lời đúng loại output mà người dùng yêu cầu.
- Đưa ra khuyến nghị hành động thực tế.
- Đồng bộ với bản đồ nhưng không phụ thuộc vào bản đồ để hoàn thiện câu trả lời.
- Có thể tiến tới hỗ trợ quyết định và tạo proposal Human-in-the-Loop.

---

# 2. Nguyên tắc cốt lõi

## 2.1. Chat Output phải độc lập với Map

Bản đồ chỉ là một kênh trực quan hóa bổ sung.

Một câu trả lời của Agent phải đủ nghĩa ngay cả khi người dùng không nhìn vào bản đồ.

Ví dụ người dùng hỏi:

> Tìm cho tôi đường chạy khoảng 3 km, không khí sạch nhất.

Agent không được chỉ vẽ route trên bản đồ rồi trả lời sơ sài.

Chat phải nêu rõ:
- Điểm xuất phát.
- Điểm đến.
- Cự ly.
- Tuyến đường.
- AQI trung bình.
- PM2.5 nếu cần.
- Lý do chọn tuyến.
- Khuyến nghị phù hợp.

Map chỉ thực hiện phần trực quan:
- Zoom.
- Marker.
- Polyline.
- Heatmap.
- Highlight khu vực.

---

# 3. Kiến trúc Agent đề xuất

```text
                    USER MESSAGE
                         │
                         ▼
              Semantic Understanding
        ┌────────────────┼────────────────┐
        │                │                │
      Intent           Entity          Context
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                   Tool Planner
                         │
                         ▼
                  Grounded Evidence
                         │
                         ▼
                  Response Planner
             ┌───────────┼───────────┐
             │           │           │
       What to say   How much     What action
             │           │           │
             └───────────┼───────────┘
                         ▼
                 Response Composer
                  │             │
                  ▼             ▼
             CHAT OUTPUT      MAP ACTION
```

Kiến trúc này thay thế mô hình hai pipeline tách biệt, nơi một agent sinh answer và một geospatial service sinh map action rồi gateway cố gắng merge kết quả.

Nguyên tắc mới:

> **Chat Output và Map Action phải được sinh ra từ cùng một Grounded Evidence Bundle.**

---

# 4. Hợp nhất Agent Chat và Map

## Không nên

```text
Agent A → Answer

Agent B → Map

Gateway → Merge / Override
```

Cách này dễ tạo ra tình trạng:
- Map vẽ đúng.
- Chat trả sai.
- Chat bị ghi đè bởi output kỹ thuật thô.
- Dữ liệu giữa chat và map không đồng nhất.

## Nên

```text
Conversation Orchestrator
        ↓
Grounded Evidence
     ↙       ↘
Chat Output   Map Action
```

Mọi thao tác không gian cần tuân theo invariant:

> **Every spatial answer must have spatial evidence and corresponding map actions.**

---

# 5. Semantic Intent + Entity + Context

Agent không nên tiếp tục phụ thuộc chủ yếu vào keyword matching.

Ví dụ:

> ngoài chạy bộ tôi muốn hoạt động khác trong nhà được không

Không được thấy từ khóa `chạy bộ` rồi route sang `recommend_running_route`.

Agent cần hiểu cấu trúc ngữ nghĩa:

```json
{
  "intent": "recommend_activity",
  "activity": "indoor",
  "excluded_activity": ["running"],
  "location": null,
  "time": "current",
  "user_goal": "health_safe_activity"
}
```

Kết quả:

```text
intent = recommend_indoor_activity
negation = running
environment = indoor
```

---

# 6. Thứ tự Routing đề xuất

```text
1. Safety / Injection / HITL bypass
2. Social / Greeting
3. Negation + Indoor Pivot
4. Comparison / Ranking / Extremum
5. POI / Road / Location Query
6. Running / Walking Route
7. Forecast
8. Station Telemetry
9. General Environmental Question
```

Rule-based router có thể được giữ lại nhưng nên đóng vai trò:
- Safety guard.
- Fast path.
- Fallback.

Semantic structured output mới là lớp hiểu ý định chính.

---

# 7. Conversation State

Agent cần hiểu hội thoại nhiều lượt.

Ví dụ:

**User**
> Khu nào đang ô nhiễm nhất?

**Agent**
> Trục Đa Tốn.

**User**
> Còn VinUni thì sao?

Agent phải hiểu `VinUni thì sao` đang kế thừa:
- Metric: AQI.
- Context: so sánh với khu vừa nói.
- Thời gian: hiện tại.

Conversation state đề xuất:

```json
{
  "last_intent": "find_worst_location",
  "last_locations": ["Trục Đa Tốn"],
  "last_route_id": null,
  "requested_distance_km": null,
  "time_context": "current",
  "active_metric": "AQI"
}
```

Ví dụ khác:

> Cho tôi đường chạy khoảng 3 km.

Sau đó:

> Ngắn hơn chút.

Agent phải giữ:
- Origin.
- Destination context.
- Activity.
- Time.
- Metric.

và chỉ điều chỉnh distance.

---

# 8. Response Planner

Đây là lớp quan trọng cần bổ sung.

Tool Planner quyết định:
> Cần lấy dữ liệu gì?

Response Planner quyết định:
> Cần trả lời người dùng như thế nào?

Ví dụ:

```json
{
  "answer_goal": "recommend_best_running_time",
  "response_type": "recommendation",
  "verbosity": "medium",
  "must_include": [
    "best_time",
    "reason",
    "aqi",
    "health_advice"
  ],
  "optional": [
    "forecast_table"
  ],
  "map_actions": [
    "show_forecast",
    "highlight_area"
  ]
}
```

Response Planner giúp tránh tình trạng:
- Có dữ liệu nhưng trả sai trọng tâm.
- Trả quá dài.
- Trả thiếu field người dùng yêu cầu.
- Dùng một template cho tất cả loại câu hỏi.

---

# 9. Response Type

Intent và Response Type phải được tách biệt.

Ví dụ:

> AQI VinUni là bao nhiêu?

```text
intent = get_location_environment
response_type = direct_fact
```

Nhưng:

> VinUni có phù hợp cho trẻ nhỏ chơi ngoài trời không?

Có thể vẫn dùng:

```text
intent = get_location_environment
```

nhưng:

```text
response_type = health_advice
```

## Các Response Type chính

| Response Type | Ví dụ |
|---|---|
| `direct_fact` | AQI VinUni bao nhiêu? |
| `location_status` | Không khí đường Hải Đăng thế nào? |
| `comparison` | VinUni hay Sapphire sạch hơn? |
| `ranking` | Khu nào ô nhiễm nhất? |
| `forecast` | AQI tối nay thế nào? |
| `recommendation` | Tôi nên đi đâu? |
| `route` | Tìm đường chạy 3 km |
| `health_advice` | AQI này có nên chạy không? |
| `indoor_alternative` | Có hoạt động trong nhà nào không? |
| `explanation` | Tại sao khu này ô nhiễm? |
| `proposal` | Đề xuất tăng thông gió |

---

# 10. Response Contract

Mỗi loại response phải có contract riêng.

## Invariant chung

```text
CHAT RESPONSE INVARIANT

1. Every response MUST directly answer the user's actual question.
2. Every requested item MUST appear explicitly in the chat output.
3. Map actions MUST NOT replace textual answers.
4. Environmental numbers MUST originate from validated evidence.
5. Recommendations MUST explain the relevant reason.
6. The response length and structure MUST adapt to user intent.
7. Technical implementation details MUST NOT appear unless the user asks.
8. If required data is unavailable, say what cannot be concluded instead of filling gaps.
```

---

# 11. Ví dụ Response Contract theo Intent

## 11.1. Direct Fact

User:

> AQI ở VinUni hiện tại bao nhiêu?

Required fields:

```text
✓ location
✓ AQI
✓ AQI category
✓ optional PM2.5
✓ timestamp
```

Output:

> 📍 **VinUni hiện có AQI 53 – mức Trung bình.**  
> PM2.5 khoảng 21 µg/m³. Với người khỏe mạnh, các hoạt động ngoài trời thông thường vẫn phù hợp.
>
> *Dữ liệu mô phỏng AirGuard AI · cập nhật 2 phút trước.*

Map:
- Zoom VinUni.
- Highlight S04.
- Show popup.

---

## 11.2. Comparison

User:

> VinUni và Hồ Ngọc Trai chỗ nào sạch hơn?

Required fields:

```text
✓ location A
✓ location B
✓ metric A
✓ metric B
✓ difference
✓ conclusion
```

Output:

> 🌿 **VinUni hiện sạch hơn Hồ Ngọc Trai.**
>
> - **VinUni:** AQI 53 · PM2.5 21 µg/m³
> - **Hồ Ngọc Trai:** AQI 68 · PM2.5 28 µg/m³
> - **Chênh lệch:** 15 AQI
>
> Nếu bạn đang chọn địa điểm để đi bộ hoặc tập thể thao lúc này, **VinUni là lựa chọn phù hợp hơn**.

Map:
- Highlight cả hai địa điểm.
- Fit bounds.
- Optional comparison popup.

---

## 11.3. Ranking / Worst Location

User:

> Khu nào đang ô nhiễm nhất?

Required:

```text
✓ worst location
✓ station
✓ AQI
✓ PM2.5
✓ AQI category
✓ better alternative
✓ health recommendation
```

Output:

> ⚠️ **Trục Đa Tốn – S01 hiện là khu vực ô nhiễm nhất trong 5 trạm AirGuard.**
>
> - AQI: **146 – Không tốt cho nhóm nhạy cảm**
> - PM2.5: **56 µg/m³**
> - Khu vực sạch hơn để thay thế: **VinUni – S04, AQI 53**
>
> Trẻ nhỏ, người cao tuổi và người nhạy cảm với bụi mịn nên hạn chế vận động kéo dài tại khu vực Đa Tốn lúc này.

Map:
- Zoom S01.
- Red highlight.
- Optional show best alternative.

---

## 11.4. Route

User:

> Tìm cho tôi đường chạy khoảng 3 km, không khí sạch nhất.

Required:

```text
✓ origin
✓ destination
✓ route
✓ distance
✓ avg AQI
✓ optional avg PM2.5
✓ route reason
✓ recommendation
```

Output:

> 🏃 **Mình đề xuất tuyến VinUni → Hồ Ngọc Trai, khoảng 3.1 km.**
>
> **Lý do chọn tuyến**
> - AQI trung bình trên tuyến: **55**
> - PM2.5 trung bình: **22 µg/m³**
> - Tránh khu Đa Tốn đang có AQI cao
> - Phần lớn tuyến đi qua khu vực ít ô nhiễm hơn
>
> **Khuyến nghị:** Nếu chạy tối nay, khoảng **20:30–21:30** sẽ phù hợp hơn theo dự báo hiện tại.
>
> 📍 Tuyến đã được hiển thị trên bản đồ.

Map:
- Origin marker.
- Destination marker.
- Polyline.
- AQI exposure overlay.

---

## 11.5. Forecast Decision

User:

> Tối nay lúc nào chạy tốt nhất?

Agent không chỉ trả forecast mà phải đưa ra quyết định.

Output:

> 🕘 **Khoảng 21:00 là thời điểm phù hợp nhất để chạy tối nay.**
>
> | Thời điểm | AQI dự báo |
> |---|---:|
> | 19:00 | 82 |
> | 20:00 | 68 |
> | **21:00** | **51** |
> | 22:00 | 55 |
>
> AQI dự kiến giảm rõ sau 20:00, vì vậy nếu không cần đi ngay, bạn nên chờ đến khoảng **21:00**.

---

# 12. Decision-first thay vì Data-first

Agent không nên ưu tiên phô bày dữ liệu kỹ thuật.

Không nên:

> Bản đồ nội suy AQI hiện có khoảng 41.3–344.2 trên 468 điểm lưới IDW-dispersion-v2...

Nên:

> **VinUni hiện là một trong những khu vực có chất lượng không khí tốt hơn để hoạt động ngoài trời.**

Sau đó mới cung cấp:
- AQI.
- PM2.5.
- So sánh.
- Khuyến nghị.

Thông tin kỹ thuật nên đặt trong:
- `Xem nguồn dữ liệu`
- Evidence drawer.
- Developer mode.

---

# 13. Chuẩn Format Chat

Cấu trúc chuẩn:

## Khối 1 — Direct Conclusion

Trả lời ngay câu hỏi trong 1–2 câu.

## Khối 2 — Key Highlights

Chỉ hiển thị các metric liên quan tới câu hỏi.

## Khối 3 — Actionable Advice

Đưa ra hành động cụ thể.

## Khối 4 — Data Footnote

Ví dụ:

```text
Dữ liệu mô phỏng AirGuard AI · cập nhật 19:42
```

Không đưa thuật ngữ kỹ thuật khó hiểu vào thân câu trả lời nếu user không yêu cầu.

---

# 14. Map Copilot

Agent Chat cần có khả năng gửi Map Actions.

Ví dụ:

User:

> Khu nào đang ô nhiễm nhất?

Chat:

> ⚠️ Trục Đa Tốn hiện là khu vực có AQI cao nhất.

Map Actions:

```json
[
  {
    "type": "zoom_to",
    "target": "S01"
  },
  {
    "type": "highlight_station",
    "station": "S01",
    "severity": "high"
  },
  {
    "type": "show_heatmap",
    "metric": "AQI"
  }
]
```

---

# 15. Spatial Knowledge Base

Trong MVP có thể tiếp tục sử dụng catalog hard-code cho:
- Đường Hải Đăng.
- Đại Dương.
- San Hô.
- Sao Biển.
- Ngọc Trai.
- Sapphire.
- Zenpark.
- Pavilion.
- VinUni.
- Vincom.
- Vinmec.
- Vinschool.
- Hồ Ngọc Trai.
- Biển Hồ.

Tuy nhiên kiến trúc dài hạn nên chuyển từ:

```text
Alias Dictionary
```

sang:

```text
Spatial Knowledge Base
        ↓
PostGIS / OSM / POI Database
        ↓
Entity Resolver
```

Ví dụ:

```text
"Hải Đăng 6"
      ↓
Entity Resolver
      ↓
Road Segment
      ↓
Coordinates
      ↓
IDW interpolation
      ↓
Nearest Stations
```

---

# 16. Personalized Agent

Agent cần điều chỉnh recommendation theo profile.

## Resident

> Có thể đi bộ hoặc chạy nhẹ tại VinUni.

## Outdoor Sport

> Có thể chạy 3–5 km, ưu tiên tuyến có exposure thấp.

## Sensitive User

> Không nên chạy cường độ cao nếu AQI vượt ngưỡng phù hợp.

Decision:

```text
Environment
+
Location
+
Time
+
User Profile
=
Recommendation
```

---

# 17. Evidence & Explainability

Grounding không chỉ nên tồn tại ở backend.

Nên hiển thị dưới câu trả lời:

```text
✓ Dựa trên dữ liệu hệ thống

S04 VinUni
AQI 53
PM2.5 21 µg/m³
2 phút trước

S03 Hồ Ngọc Trai
AQI 58
PM2.5 24 µg/m³
1 phút trước
```

Có thể đặt trong nút:

> Xem nguồn

Expanded content:

```text
Source: simulator
Interpolation: IDW
Timestamp: ...
Station IDs: S03, S04
```

---

# 18. Follow-up Actions

Sau câu trả lời nên có action chips.

Ví dụ:

```text
[📍 Xem trên bản đồ]
[🌿 Tìm khu sạch hơn]
[🏃 Tìm đường tránh khu này]
```

Nếu đang hỏi running:

```text
[2 km]
[3 km]
[5 km]
[Chọn điểm xuất phát]
```

Nếu đang hỏi địa điểm:

```text
[Dự báo 1 giờ]
[Dự báo tối nay]
[So sánh khu khác]
```

Điều này giúp Agent có UX giống một sản phẩm hoàn chỉnh thay vì textarea kết nối LLM.

---

# 19. Time-aware Reasoning

Agent cần trả lời được các câu hỏi dạng:

> Khi nào nên chạy?

Ví dụ dữ liệu:

```text
19:00 → AQI 82
20:00 → AQI 67
21:00 → AQI 51
22:00 → AQI 55
```

Agent phải suy luận:

> **21:00 là khoảng thời gian phù hợp hơn.**

Không chỉ dump forecast.

---

# 20. Decision Support Agent

Agent nên tiến hóa theo chuỗi:

```text
Observe
   ↓
Understand
   ↓
Compare
   ↓
Predict
   ↓
Recommend
   ↓
Propose Action
```

## Observe

> AQI VinUni bao nhiêu?

## Compare

> VinUni hay Sapphire sạch hơn?

## Predict

> AQI tối nay có giảm không?

## Recommend

> Tôi nên chạy ở đâu?

## Propose Action

> Tạo đề xuất tăng thông gió.

Bước cuối phải đi qua Human-in-the-Loop.

---

# 21. Các nhóm Intent chính

```text
environment.current
environment.location
environment.compare
environment.ranking
environment.forecast

activity.running
activity.walking
activity.indoor
activity.health

spatial.route
spatial.location
spatial.area

decision.recommend_location
decision.recommend_time
decision.recommend_route

operation.create_warning_proposal
operation.create_ventilation_proposal
```

---

# 22. Grounding & Safety

Agent phải giữ các invariant:

```text
1. Không tự tạo số liệu môi trường.
2. Mọi con số phải xuất phát từ tool result trong cùng request.
3. Không sử dụng dữ liệu stale vượt quá giới hạn.
4. Không dùng offline station như nguồn hiện tại.
5. Không suy diễn nguyên nhân ô nhiễm nếu không có evidence.
6. Không tự approve action.
7. Agent chỉ được tạo pending proposal.
8. Mọi action quan trọng phải có audit trail.
```

Nếu thiếu dữ liệu:

> Hiện tại mình chưa có dữ liệu đủ mới để kết luận chất lượng không khí tại khu vực này.

Không được fill số liệu bằng suy đoán.

---

# 23. Roadmap triển khai

## Phase 1 — Fix Core Agent

Ưu tiên:

```text
Unified Gateway
→ Semantic Router
→ Spatial Registry
→ Response Composer
→ Map Sync
```

Mục tiêu:
- Không còn answer overwrite.
- Route đúng intent.
- Hải Đăng / VinUni / Vincom nhận diện đúng.
- Chat và map đồng bộ.
- Output đúng response contract.

---

## Phase 2 — Conversational Intelligence

Thêm:

```text
Conversation Context
Entity Memory
Follow-up Resolution
Negation
Comparison
Coreference
```

Agent hiểu:

> ở đó thì sao?

> chỗ kia sạch hơn không?

> ngắn hơn chút

> không chạy bộ nữa

---

## Phase 3 — Map Copilot

Agent điều khiển:

```text
zoom
highlight
filter
draw route
show heatmap
compare areas
show forecast layer
```

Map trở thành workspace trực quan của Agent.

---

## Phase 4 — Decision Agent

Thêm:

```text
Personalization
Forecast Reasoning
Health Profile
Route Exposure Optimization
Alert Recommendation
HITL Proposal
```

Agent có thể trả lời:

> AQI khu bạn đang đứng hiện là 72. Nếu muốn chạy khoảng 3 km, mình khuyên chuyển sang VinUni sau 20:30; dự báo khi đó AQI giảm và tuyến đề xuất có mức phơi nhiễm thấp hơn.

---

# 24. Acceptance Criteria đề xuất

## AC-01 — Direct Answer

User:

> AQI VinUni bao nhiêu?

Pass khi:
- Có AQI cụ thể.
- Có category.
- Không trả text IDW thô.
- Map highlight đúng VinUni.

---

## AC-02 — Comparison

User:

> VinUni hay Hồ Ngọc Trai sạch hơn?

Pass khi:
- Có số liệu cả hai.
- Có conclusion rõ ràng.
- Không bắt user tự suy luận.
- Map hiển thị cả hai.

---

## AC-03 — Ranking

User:

> Khu nào ô nhiễm nhất?

Pass khi:
- Nêu chính xác địa điểm.
- Có AQI.
- Có alternative.
- Map highlight đúng khu.

---

## AC-04 — Negation

User:

> Ngoài chạy bộ tôi muốn hoạt động khác trong nhà.

Pass khi:
- Không route sang running.
- Không vẽ route.
- Trả indoor recommendation.

---

## AC-05 — POI Recognition

User:

> Chất lượng không khí tại đường Hải Đăng?

Pass khi:
- Resolve đúng Hải Đăng.
- Không fallback VinUni.
- Có estimated AQI tại vị trí.

---

## AC-06 — Route Contract

User:

> Tìm đường chạy 3 km từ Sapphire đến Hồ Ngọc Trai và cho tôi AQI trung bình.

Pass khi chat có đầy đủ:

```text
✓ origin
✓ destination
✓ distance
✓ route
✓ average AQI
✓ recommendation
```

Map phải vẽ đúng route tương ứng.

---

## AC-07 — Follow-up Context

```text
User: Khu nào ô nhiễm nhất?
User: Còn VinUni thì sao?
```

Pass khi Agent hiểu `VinUni thì sao` là tiếp tục chủ đề chất lượng không khí hiện tại.

---

## AC-08 — Grounding

Nếu tool không trả dữ liệu hợp lệ:

Agent phải fail-closed.

Không được tự sinh số.

---

# 25. Đích đến cuối cùng

AirGuard AI Agent không nên được định nghĩa là:

> Chatbot hỏi đáp AQI.

Cũng không nên chỉ là:

> Agent có thể gọi tool và điều khiển bản đồ.

Đích đến nên là:

> **Một trợ lý đô thị thông minh hiểu nhu cầu bằng ngôn ngữ tự nhiên, sử dụng dữ liệu môi trường và dữ liệu không gian đã được kiểm chứng để trả lời đúng yêu cầu, giải thích quyết định, đưa ra hành động phù hợp và trực quan hóa kết quả đồng bộ trên bản đồ.**

Tóm tắt pipeline cuối:

```text
USER
 ↓
Understand Intent
 ↓
Resolve Entity & Context
 ↓
Retrieve Grounded Data
 ↓
Reason / Compare / Predict
 ↓
Plan Response
 ↓
┌──────────────────────────────┐
│          OUTPUT              │
│                              │
│  Chat Answer                 │
│  + Recommendation            │
│  + Evidence                  │
│  + Follow-up Actions         │
│  + Map Actions               │
└──────────────────────────────┘
```

## Nguyên tắc quan trọng nhất

> **Agent phải trả đúng câu người dùng hỏi trước, sau đó mới dùng bản đồ, dữ liệu và AI reasoning để làm câu trả lời đó tốt hơn.**

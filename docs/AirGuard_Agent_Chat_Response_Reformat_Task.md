# TASK SPEC — FORMAT LẠI CÂU TRẢ LỜI AIRGUARD AGENT CHAT

## 1. Mục tiêu

Thiết kế lại toàn bộ format trả lời của **AirGuard Geospatial AI Agent** theo hướng:

- Thân thiện với người dùng.
- Trả lời đúng điều người dùng hỏi.
- Không hiển thị raw data kỹ thuật.
- Không hiển thị tool call, function call, command hoặc JSON nội bộ.
- Không hiển thị tên model, tên service, tên thuật toán nội bộ nếu người dùng không hỏi.
- Không để thao tác trên bản đồ thay thế cho câu trả lời bằng văn bản.
- Chat và Map phải cùng một kết luận.
- Khi Agent đã zoom / định vị / highlight / vẽ route trên Map, Chat chỉ mô tả kết quả bằng ngôn ngữ tự nhiên.
- Mọi số liệu môi trường vẫn phải grounded từ dữ liệu hợp lệ của hệ thống.

---

# 2. Vấn đề hiện tại

Ví dụ người dùng hỏi:

> Khu nào đang ô nhiễm nhất?

Map có thể đã:
- xác định đúng khu vực;
- zoom đúng vị trí;
- highlight đúng trạm;
- hiển thị đúng heatmap.

Nhưng Chat lại trả:

> Bản đồ nội suy AQI ở mốc hiện tại có khoảng giá trị 76.2–343.9 AQI trên 468 điểm lưới. Lưới idw-dispersion-v2.0... nguồn spatial_idw_dispersion_model...

Đây là output không phù hợp với người dùng cuối.

Người dùng không hỏi:
- có bao nhiêu grid point;
- model nội suy tên gì;
- function nào được gọi;
- backend chạy service nào;
- nguồn dữ liệu nội bộ tên gì;
- command nào đã thực thi.

Người dùng hỏi:

> Khu nào đang ô nhiễm nhất?

Vì vậy câu trả lời phải bắt đầu bằng kết luận:

> ⚠️ **Trục Đa Tốn hiện là khu vực có chất lượng không khí kém nhất.**

Sau đó mới hiển thị một vài chỉ số cần thiết.

---

# 3. Nhiệm vụ chính

## TASK 1 — Tách Internal Result và User-facing Response

Không render trực tiếp kết quả từ tool/service ra UI Chat.

Pipeline mới:

```text
USER MESSAGE
    ↓
Intent / Context
    ↓
Tool / Geospatial / Forecast
    ↓
Validated Evidence
    ↓
Response Composer
    ↓
User-facing Answer
```

Internal result có thể chứa:

```json
{
  "intent": "find_worst_location",
  "station_id": "S01",
  "station_name": "Trục Đa Tốn",
  "aqi": 146,
  "pm25": 56,
  "grid_count": 468,
  "interpolation_model": "idw-dispersion-v2.0",
  "source": "spatial_idw_dispersion_model",
  "map_actions": [
    "zoom:S01",
    "highlight:S01"
  ]
}
```

Nhưng UI Chat chỉ được nhận nội dung dạng:

```text
⚠️ Trục Đa Tốn hiện là khu vực ô nhiễm nhất.

AQI: 146 — Không tốt cho nhóm nhạy cảm
PM2.5: 56 µg/m³

Nếu bạn đang định tập thể thao ngoài trời, nên ưu tiên khu vực có AQI thấp hơn như VinUni.

📍 Mình đã đánh dấu khu vực này trên bản đồ.
```

---

# 4. TASK 2 — Không lộ tool call / function call / command

## Không được hiển thị

```text
get_spatial_air_quality()
get_current_pm25()
get_pm25_forecast()
recommend_running_route()
find_worst_location()
tool_call
function_call
map_actions
fitBounds
highlight_station
zoom_to
polyline
spatial_idw_dispersion_model
idw-dispersion-v2.0
backend/app/...
FastAPI
endpoint
correlation_id
raw JSON
raw latitude / longitude
```

Trừ trường hợp người dùng chủ động hỏi kỹ thuật.

---

# 5. TASK 3 — Thiết kế Response Composer

Tạo một lớp / module chuyên chuyển:

```text
Validated Evidence
```

thành:

```text
Friendly User Response
```

Response Composer không được tự tạo số liệu.

Nó chỉ có nhiệm vụ:
- chọn thông tin nào cần hiển thị;
- chọn câu kết luận;
- chọn recommendation;
- chọn format;
- tạo map feedback tự nhiên.

---

# 6. Cấu trúc chuẩn câu trả lời

Response nên có tối đa 4 phần.

```text
1. Direct Answer
2. Key Information
3. Actionable Advice
4. Map Feedback / Data Note
```

Không bắt buộc response nào cũng phải có đủ 4 phần.

---

# 7. Direct Answer

Câu đầu tiên phải trả lời đúng câu hỏi.

## Sai

> Bản đồ nội suy AQI hiện có khoảng 76.2–343.9 trên 468 điểm.

## Đúng

> ⚠️ **Trục Đa Tốn hiện là khu vực có chất lượng không khí kém nhất.**

---

## Sai

> Hệ thống đã gọi recommend_running_route thành công.

## Đúng

> 🏃 **Mình đã tìm được một cung đường khoảng 3 km có chất lượng không khí tốt hơn cho bạn.**

---

## Sai

> get_location_environment returned AQI=63.

## Đúng

> 📍 **AQI tại VinUni hiện khoảng 63 — mức Trung bình.**

---

# 8. TASK 4 — Chỉ hiển thị metric liên quan

Không dump toàn bộ telemetry.

Ví dụ người dùng hỏi:

> AQI ở VinUni bao nhiêu?

Chỉ cần:

```text
AQI
PM2.5 nếu hữu ích
AQI category
timestamp
```

Không cần tự động hiển thị:

```text
CO2
noise
temperature
humidity
wind
grid count
model name
source module
```

---

# 9. TASK 5 — Natural Map Feedback

Khi Agent đã thao tác trên Map, Chat phải diễn đạt tự nhiên.

## Zoom / Locate

Không:

> zoom_to executed.

Nên:

> 📍 Mình đã đưa bản đồ tới khu vực này.

---

## Highlight

Không:

> highlight_station(S01)

Nên:

> 📍 Mình đã đánh dấu khu vực này trên bản đồ.

---

## Draw Route

Không:

> polyline generated successfully.

Nên:

> 🗺️ Tuyến đường đề xuất đã được hiển thị trên bản đồ.

---

## Compare Two Areas

Nên:

> 📍 Mình đã đánh dấu cả hai khu vực để bạn dễ so sánh.

---

# 10. TASK 6 — Response Format theo Intent

## 10.1. Greeting

### User

> Xin chào

### Output

> 👋 Chào bạn! Mình có thể giúp bạn kiểm tra chất lượng không khí, so sánh khu vực hoặc tìm cung đường phù hợp hơn trong Ocean Park 1.

Không gọi tool nếu không cần.

---

## 10.2. Location AQI

### User

> Không khí ở VinUni thế nào?

### Output

> 📍 **Không khí tại VinUni hiện ở mức Trung bình.**
>
> - **AQI:** 63
> - **PM2.5:** 24 µg/m³
>
> Bạn vẫn có thể đi bộ hoặc vận động nhẹ ngoài trời. Nếu thuộc nhóm nhạy cảm, nên tránh vận động kéo dài.
>
> 📍 Mình đã đưa bản đồ tới khu VinUni.
>
> *Dữ liệu mô phỏng · cập nhật 2 phút trước.*

---

## 10.3. Worst Location

### User

> Khu nào đang ô nhiễm nhất?

### Output

> ⚠️ **Trục Đa Tốn hiện là khu vực ô nhiễm nhất trong phạm vi AirGuard đang theo dõi.**
>
> - **AQI:** 146 — Không tốt cho nhóm nhạy cảm
> - **PM2.5:** 56 µg/m³
> - **Khu vực sạch hơn:** VinUni
>
> Nếu bạn đang định đi bộ hoặc tập thể thao, nên tránh khu Đa Tốn lúc này.
>
> 📍 Mình đã đánh dấu khu vực này trên bản đồ.

---

## 10.4. Best Location

### User

> Chỗ nào sạch nhất?

### Output

> 🌿 **VinUni hiện là khu vực có chất lượng không khí tốt nhất trong các điểm AirGuard đang theo dõi.**
>
> - **AQI:** 48 — Tốt
> - **PM2.5:** 17 µg/m³
>
> Đây là lựa chọn phù hợp hơn nếu bạn muốn đi bộ hoặc tập thể thao ngoài trời lúc này.
>
> 📍 Mình đã đánh dấu VinUni trên bản đồ.

---

## 10.5. Comparison

### User

> VinUni và Hồ Ngọc Trai chỗ nào sạch hơn?

### Output

> 🌿 **VinUni hiện có chất lượng không khí tốt hơn Hồ Ngọc Trai.**
>
> - **VinUni:** AQI 53
> - **Hồ Ngọc Trai:** AQI 68
> - **Chênh lệch:** 15 AQI
>
> Nếu bạn đang chọn nơi để đi bộ hoặc tập nhẹ, **VinUni là lựa chọn phù hợp hơn lúc này**.
>
> 📍 Mình đã đánh dấu cả hai khu vực để bạn dễ so sánh.

---

## 10.6. Running Route

### User

> Tìm đường chạy khoảng 3 km cho tôi.

### Output

> 🏃 **Mình đã tìm được một cung đường khoảng 3,1 km có chất lượng không khí phù hợp hơn.**
>
> - **Cự ly:** khoảng 3,1 km
> - **AQI trung bình trên tuyến:** 55
> - **Khu vực chính:** VinUni → Hồ Ngọc Trai
>
> Tuyến này giúp hạn chế đi qua các vùng đang có AQI cao hơn.
>
> 🗺️ Mình đã vẽ tuyến trực tiếp trên bản đồ.

---

## 10.7. Forecast

### User

> Tối nay AQI thế nào?

### Output

> 🌙 **AQI được dự báo giảm dần vào tối nay.**
>
> - **19:00:** AQI 82
> - **20:00:** AQI 68
> - **21:00:** AQI 51
>
> Nếu muốn hoạt động ngoài trời, khoảng **21:00 sẽ phù hợp hơn** so với đầu buổi tối.
>
> *Dữ liệu dự báo mô phỏng AirGuard AI.*

---

## 10.8. Indoor Alternative

### User

> Ngoài chạy bộ tôi muốn hoạt động khác trong nhà được không?

### Output

> 🏠 **Được chứ. Nếu bạn muốn tránh không khí ngoài trời, có thể chuyển sang hoạt động trong nhà.**
>
> Một vài lựa chọn:
> - 🏋️ Gym hoặc chạy máy
> - 🧘 Yoga / giãn cơ
> - 🛍️ Đi bộ trong khu thương mại
> - 🏠 Tập luyện nhẹ tại nhà
>
> Nếu muốn, mình có thể giúp bạn tìm khu vực trong nhà thuận tiện hơn gần vị trí hiện tại.

Không vẽ running route.

---

# 11. TASK 7 — Unknown Location Handling

Nếu không resolve được địa danh:

## Không được

Fallback tự động về VinUni.

## Phải trả

> 📍 **Mình chưa xác định chính xác được khu vực “ABC” trong phạm vi Ocean Park 1.**
>
> Bạn có thể gửi tên đường, tên tòa, phân khu hoặc địa điểm gần đó để mình kiểm tra chính xác hơn.

Không tự bịa location.

---

# 12. TASK 8 — Fail Closed khi thiếu dữ liệu

Nếu dữ liệu:
- stale;
- invalid;
- offline;
- tool lỗi;
- không đủ evidence;

thì không được tạo số liệu.

### Output

> ⚠️ **Mình chưa có dữ liệu đủ mới để đánh giá chính xác khu vực này lúc này.**
>
> Bạn có thể thử lại sau ít phút hoặc kiểm tra một khu vực khác đang có dữ liệu hợp lệ.

---

# 13. TASK 9 — Adaptive Verbosity

## Fact Query

Ví dụ:

> AQI VinUni bao nhiêu?

Trả khoảng 2–4 dòng.

---

## Comparison

Khoảng 4–7 dòng.

---

## Route / Recommendation

Khoảng 6–10 dòng.

---

## Technical Question

Chỉ khi user hỏi kỹ thuật mới trả chi tiết:
- IDW;
- grid;
- wind adjustment;
- source;
- forecast model.

---

# 14. TASK 10 — Tone of Voice

Agent phải nói như một trợ lý đô thị.

## Nên dùng

```text
Mình đã tìm...
Mình đề xuất...
Bạn có thể...
Khu vực này hiện...
Nếu bạn muốn...
Mình đã đánh dấu...
```

## Hạn chế

```text
Hệ thống xác định...
Pipeline trả về...
Engine đã thực hiện...
Module nhận diện...
Model nội suy...
Service trả...
```

---

# 15. TASK 11 — Evidence UI

Không đưa evidence raw vào message chính.

Có thể render một nút:

```text
[Xem nguồn dữ liệu]
```

Khi mở mới hiển thị:

```text
S01 — Trục Đa Tốn
AQI: 146
PM2.5: 56 µg/m³
Updated: 19:42
Source: simulator
```

Thông tin kỹ thuật sâu hơn chỉ hiển thị ở Developer / Debug Mode.

---

# 16. TASK 12 — Chuẩn hóa Backend Response Schema

Đề xuất API trả về:

```json
{
  "intent": "find_worst_location",

  "answer": {
    "headline": "Trục Đa Tốn hiện là khu vực ô nhiễm nhất.",
    "highlights": [
      {
        "label": "AQI",
        "value": "146",
        "description": "Không tốt cho nhóm nhạy cảm"
      },
      {
        "label": "PM2.5",
        "value": "56 µg/m³"
      }
    ],
    "recommendation": "Nên hạn chế vận động kéo dài tại khu vực này.",
    "map_feedback": "Mình đã đánh dấu khu vực trên bản đồ.",
    "data_note": "Dữ liệu mô phỏng · cập nhật 2 phút trước"
  },

  "map_actions": [],
  "evidence": []
}
```

Frontend chỉ render:

```text
answer.*
```

Không render trực tiếp:

```text
map_actions
evidence raw
tool_results
debug metadata
```

---

# 17. TASK 13 — Response Contract Validator

Trước khi trả response, validate theo intent.

Ví dụ:

```text
find_worst_location
```

Required fields:

```text
✓ location
✓ AQI
✓ AQI category
✓ recommendation
```

Nếu thiếu location:

FAIL CLOSED.

Không tạo một tên địa điểm giả.

---

## Route Contract

Nếu user hỏi:

> Tìm đường chạy 3 km từ Sapphire đến Hồ Ngọc Trai và cho tôi AQI trung bình.

Chat output bắt buộc có:

```text
✓ origin
✓ destination
✓ distance
✓ route
✓ average AQI
✓ recommendation
```

Map action bắt buộc phải tương ứng đúng route.

---

# 18. TASK 14 — Map/Chat Consistency Validator

Thêm validation trước khi gửi response:

```text
Chat Entity
    ==
Map Target Entity
```

Ví dụ:

```text
Chat:
Trục Đa Tốn

Map:
S01 Trục Đa Tốn
```

PASS.

---

Ví dụ:

```text
Chat:
VinUni

Map:
S01 Trục Đa Tốn
```

FAIL.

---

# 19. TASK 15 — Không để Map Action ghi đè Answer

Gateway không được:

```python
result["answer"] = agent_result["answer"]
```

sau khi Geospatial Agent đã tạo answer đúng.

Quy tắc:

```text
Geospatial / Decision Result
        ↓
Response Composer
        ↓
Final Answer

Map Action chỉ là output song song.
```

---

# 20. Prompt cho Response Composer

```text
You are the user-facing response composer for AirGuard AI.

Your responsibility is to convert validated environmental and geospatial
evidence into a concise, friendly and actionable Vietnamese answer.

RULES:

1. Answer the user's actual question in the first sentence.

2. Never expose:
   - function names
   - tool calls
   - JSON
   - map commands
   - backend service names
   - internal model identifiers
   - implementation details

3. Never mention IDW grid count or interpolation model unless the user
   explicitly asks about the technical implementation.

4. Only include metrics relevant to the user's question.

5. Map actions must never replace the textual answer.

6. When a map action succeeds, describe it naturally:
   - "Mình đã đánh dấu vị trí trên bản đồ."
   - "Mình đã vẽ tuyến đề xuất trên bản đồ."
   - "Mình đã đưa bản đồ tới khu vực này."

7. Recommendations must be based on validated evidence.

8. Never invent environmental values.

9. If evidence is missing, stale, invalid or unavailable, clearly state
   that there is not enough current data to conclude.

10. Keep factual answers short.

11. Comparison, route, forecast and recommendation queries may use
    structured bullets.

12. Technical disclaimers must be compressed into a short footnote.

13. Speak like a helpful urban assistant, not a backend log.

14. Chat output must be understandable even if the user does not look
    at the map.
```

---

# 21. Acceptance Criteria

## AC-01 — Worst Location

Input:

> Khu nào đang ô nhiễm nhất?

PASS:
- dòng đầu tiên có tên khu vực;
- có AQI;
- có recommendation;
- map highlight đúng địa điểm.

FAIL:
- trả range toàn map;
- nói IDW;
- nói 468 grid point;
- nói tool/service/model.

---

## AC-02 — Map Locate

Nếu Agent đã zoom tới location:

PASS:

> 📍 Mình đã đưa bản đồ tới khu vực này.

FAIL:

```text
zoom_to(location)
fitBounds(...)
```

---

## AC-03 — Route

Nếu map đã vẽ route:

Chat bắt buộc phải nói:
- route;
- distance;
- AQI/exposure;
- recommendation.

Không chỉ nói:

> Tuyến đã được vẽ.

---

## AC-04 — Unknown Location

Không được fallback sang VinUni hoặc location mặc định.

---

## AC-05 — Tool Failure

Không được hallucinate.

---

## AC-06 — Chat/Map Sync

Map và Chat phải cùng entity / route / conclusion.

---

## AC-07 — Technical Leakage

Không được xuất hiện trong user-facing chat:

```text
tool_call
function_call
idw-dispersion-v2.0
spatial_idw_dispersion_model
468 grid
map_actions
backend
JSON
```

trừ khi user hỏi trực tiếp về kỹ thuật.

---

# 22. Definition of Done

Task được coi là hoàn thành khi:

- [ ] Tất cả output raw từ tool được chặn khỏi UI Chat.
- [ ] Có Response Composer riêng.
- [ ] Có response template theo intent.
- [ ] Có response contract validator.
- [ ] Có Map/Chat consistency validator.
- [ ] Map action không ghi đè answer.
- [ ] Unknown location không fallback sai.
- [ ] Tool failure fail-closed.
- [ ] Không còn lộ function/tool/model trong câu trả lời thông thường.
- [ ] Test các intent chính đều cho output thân thiện.
- [ ] Chat vẫn trả đủ thông tin kể cả không nhìn vào Map.

---

# 23. Kết quả mong muốn

## Trước

> ⚡ THỜI GIAN THỰ  
> Bản đồ nội suy aqi ở mốc hiện tại có khoảng giá trị 76.2-343.9 AQI trên 468 điểm lưới. Lưới idw-dispersion-v2.0... nguồn spatial_idw_dispersion_model...

## Sau

> ⚠️ **Trục Đa Tốn hiện là khu vực có chất lượng không khí kém nhất.**
>
> - **AQI:** 146 — Không tốt cho nhóm nhạy cảm
> - **PM2.5:** 56 µg/m³
>
> Nếu bạn đang định đi bộ hoặc tập thể thao, nên ưu tiên khu vực có AQI thấp hơn như VinUni.
>
> 📍 Mình đã đánh dấu khu vực này trên bản đồ.
>
> *Dữ liệu mô phỏng AirGuard AI · cập nhật vừa xong.*

---

# 24. Nguyên tắc cuối cùng

> **Ẩn cách hệ thống làm việc. Chỉ cho người dùng thấy kết luận, dữ liệu cần thiết, lời khuyên và kết quả trực quan trên bản đồ.**

Chat phải tạo cảm giác:

> **“Tôi đang nói chuyện với một trợ lý hiểu môi trường và khu vực của mình.”**

Không phải:

> **“Tôi đang đọc log của một hệ thống GIS/AI.”**

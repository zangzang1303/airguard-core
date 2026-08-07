# PRD — AirGuard AI

**Phiên bản:** 1.2  
**Ngày cập nhật:** 06/08/2026  
**Thời gian thực hiện:** 6 tuần  
**Quy mô nhóm:** 4 thành viên  
**Trạng thái:** Đang triển khai MVP  

---

# 1. Tổng quan dự án

## Phần này gồm những gì?

| Nội dung | Ý nghĩa |
|---|---|
| Bài toán | Vấn đề thực tế mà dự án muốn giải quyết |
| Giải pháp | AirGuard AI hoạt động như thế nào |
| Giá trị chính | Vì sao sản phẩm hữu ích hơn dashboard thông thường |
| Phạm vi địa lý | Khu vực được dùng để xây dựng và demo MVP |

## Giải thích ngắn

AirGuard AI là hệ thống hỗ trợ theo dõi chất lượng không khí ngoài trời trong khu đô thị hoặc campus. MVP tập trung vào **PM2.5** tại 5 vị trí quanh VinUni và Vinhomes Ocean Park.

Hệ thống không chỉ hiển thị số liệu. Nó còn cho phép người dùng hỏi AI Agent bằng ngôn ngữ tự nhiên, so sánh khu vực, nhận khuyến nghị và xem cảnh báo có bằng chứng.

## Chi tiết

Luồng tổng thể:

```text
Sensor Simulator
→ MQTT Broker
→ Backend
→ Database
→ Dashboard / AI Agent
→ Warning Proposal
→ Manager Approve hoặc Reject
```

Nguyên tắc quan trọng:

- AI Agent không tự tạo số liệu.
- Mọi số liệu môi trường phải đến từ tool.
- Alert threshold do Rule Engine quyết định.
- Agent chỉ tạo Warning Proposal ở trạng thái `pending`.
- Manager là người approve hoặc reject.

---

# 2. Mục tiêu MVP

## Phần này gồm những gì?

| Nhóm mục tiêu | Nội dung |
|---|---|
| Theo dõi dữ liệu | Hiển thị PM2.5 tại 5 vị trí |
| Phát hiện vấn đề | Phát hiện PM2.5 cao, stale, invalid và offline |
| Hỏi đáp bằng AI | Cho phép người dùng hỏi Agent bằng ngôn ngữ tự nhiên |
| Khuyến nghị | Đưa ra lời khuyên theo từng nhóm người dùng |
| Cảnh báo có kiểm soát | Agent tạo proposal, Manager duyệt |
| Đánh giá | Có metric, test case và E2E scenario |

## Giải thích ngắn

Mục tiêu MVP không phải xây một hệ thống hoàn hảo cho toàn thành phố. Mục tiêu là chứng minh được luồng chính hoạt động từ dữ liệu cảm biến đến dashboard, Agent và Human-in-the-Loop.

## Mục tiêu chi tiết

- Theo dõi PM2.5 tại 5 trạm.
- Hiển thị dữ liệu mới nhất và lịch sử.
- Phát hiện PM2.5 vượt ngưỡng.
- Phát hiện sensor offline.
- Nhận biết dữ liệu stale hoặc invalid.
- Hỗ trợ 3 nhóm người dùng:
  - `normal`
  - `sensitive`
  - `outdoor_sport`
- Cho phép Agent:
  - hỏi PM2.5 hiện tại;
  - xem xu hướng;
  - so sánh khu vực;
  - giải thích cảnh báo;
  - đưa ra khuyến nghị;
  - tạo Warning Proposal.
- Cho phép Manager approve hoặc reject proposal.
- Lưu Agent trace và audit log.
- Chạy thành công ít nhất 3 kịch bản E2E.

---

# 3. Những phần không làm trong MVP

## Phần này gồm những gì?

| Không triển khai | Lý do |
|---|---|
| Sensor vật lý thật | Vượt phạm vi và thời gian của nhóm |
| Mobile app | Không cần thiết để chứng minh MVP |
| Deep learning bắt buộc | Baseline đủ để kiểm chứng hướng đi |
| Multi-agent network tự trị | Khó kiểm soát và debug |
| Điều khiển thiết bị thật | Có rủi ro và cần hạ tầng thực |
| Production scaling lớn | Không phải mục tiêu của Gate hiện tại |

## Giải thích ngắn

Việc chốt rõ phần không làm giúp nhóm tránh mở rộng phạm vi, giảm xung đột và tập trung vào demo end-to-end.

## Danh sách ngoài phạm vi

- Sensor vật lý thật.
- Mobile application.
- HVAC/BMS/SCADA thật.
- Multi-agent network tự trị.
- Agent tự approve/reject.
- Deep learning/LSTM bắt buộc.
- Kubernetes và auto-scaling.
- Theo dõi toàn bộ chỉ số môi trường.
- Vector database nếu chưa thực sự cần.

---

# 4. Đối tượng người dùng

## Phần này gồm những gì?

| Người dùng | Nhu cầu chính | Quyền chính |
|---|---|---|
| Resident/User | Xem dữ liệu và hỏi Agent | Xem dashboard, station, alert |
| Sensitive User | Nhận khuyến nghị thận trọng hơn | Xem khu vực nên tránh |
| Outdoor Sport User | Biết có nên tập ngoài trời | Xem current, forecast, recommendation |
| Manager | Theo dõi và phê duyệt cảnh báo | Approve/reject proposal |
| Admin | Quản trị hệ thống nếu có | Quản lý user, station, config |

## Giải thích ngắn

Mỗi nhóm người dùng có nhu cầu khác nhau. Agent phải dùng user profile để tạo khuyến nghị phù hợp, nhưng không được chẩn đoán y tế.

## Chi tiết từng nhóm

### 4.1. Resident/User

Có thể:

- Login.
- Xem dashboard.
- Xem trạm.
- Xem lịch sử.
- Hỏi AI Agent.
- Xem cảnh báo công khai.
- Xem profile.

Không thể:

- Approve hoặc reject proposal.
- Thay đổi threshold.
- Quản lý station.

### 4.2. Sensitive User

Cần:

- Khuyến nghị thận trọng hơn.
- Biết khu vực nên tránh.
- Biết khi nào nên hạn chế hoạt động ngoài trời.

Lưu ý:

- Không lưu bệnh án.
- Không chẩn đoán y tế.
- Chỉ sử dụng nhóm hồ sơ để cá nhân hóa khuyến nghị.

### 4.3. Outdoor Sport User

Cần:

- Biết có nên chạy bộ không.
- So sánh khu thể thao với công viên.
- Xem forecast ngắn hạn.

### 4.4. Manager

Có thể:

- Xem dashboard.
- Xem active alert.
- Xem Warning Proposal.
- Xem evidence.
- Approve hoặc reject.
- Nhập review note.
- Xem audit log.

### 4.5. Admin

Chỉ triển khai khi nhóm chốt Admin nằm trong MVP.

---

# 5. Kiến trúc hệ thống

## Phần này gồm những gì?

| Thành phần | Vai trò |
|---|---|
| Sensor Simulator | Sinh dữ liệu PM2.5 |
| MQTT Broker | Truyền dữ liệu sensor |
| Backend | Validate, xử lý và cung cấp API |
| PostgreSQL | Lưu dữ liệu chính |
| Alert Engine | Tạo cảnh báo theo rule |
| Frontend | Hiển thị dữ liệu và thao tác người dùng |
| AI Agent | Gọi tool và tạo câu trả lời |
| HITL | Manager kiểm soát cảnh báo |

## Giải thích ngắn

Kiến trúc được tách lớp để mỗi thành viên có thể làm độc lập nhưng vẫn tích hợp theo contract chung.

## Sơ đồ luồng

```text
Sensor Simulator
      |
      v
MQTT Broker
      |
      v
Backend MQTT Consumer
      |
      v
Validation + Data Quality
      |
      v
PostgreSQL
      |
      +----------------------------+
      |                            |
      v                            v
REST API                      Alert Engine
      |                            |
      v                            v
Frontend                     Active Alert
      |
      v
AI Agent API
      |
      v
Tool Calling
      |
      v
Warning Proposal
      |
      v
Manager Approve/Reject
```

## Ràng buộc kiến trúc

- Frontend không kết nối MQTT trực tiếp.
- Frontend không truy cập Database.
- Agent không truy cập Database.
- Agent chỉ gọi API/tool.
- Rule Engine không phụ thuộc LLM.
- Proposal phải qua Human-in-the-Loop.

---

# 6. Các tính năng cốt lõi

## Phần này gồm những gì?

| Tính năng | Người dùng chính | Kết quả mong đợi |
|---|---|---|
| Dashboard bản đồ | User, Manager | Xem 5 trạm và PM2.5 |
| Chi tiết trạm | User, Manager | Xem current và history |
| Alert Engine | Hệ thống | Phát hiện bất thường |
| AI Agent Chat | User | Hỏi bằng ngôn ngữ tự nhiên |
| Khuyến nghị | User | Nhận lời khuyên theo profile |
| Warning Proposal | Agent, Manager | Tạo và duyệt cảnh báo |
| Audit Log | Manager/Admin | Theo dõi quyết định |

## Giải thích ngắn

Các tính năng này là phần tối thiểu để chứng minh sản phẩm có giá trị. Mỗi tính năng đều cần có acceptance criteria rõ ràng.

---

## 6.1. Dashboard bản đồ

### Mục đích

Cho người dùng nhìn nhanh chất lượng không khí ở từng khu vực.

### 5 trạm trong MVP

| Mã trạm | Vị trí |
|---|---|
| S01 | Cổng chính |
| S02 | Bãi đỗ xe |
| S03 | Trục đường chính |
| S04 | Công viên |
| S05 | Khu thể thao ngoài trời |

### Mỗi marker hiển thị

- Tên trạm.
- PM2.5 hiện tại.
- Trạng thái sensor.
- Thời gian cập nhật.
- Trạng thái dữ liệu.

### Tiêu chí chấp nhận

- Hiển thị đủ 5/5 trạm.
- Có timestamp.
- Offline hoặc stale được đánh dấu.
- Click marker mở được chi tiết.

---

## 6.2. Chi tiết và lịch sử trạm

### Mục đích

Cho phép xem dữ liệu của một trạm rõ hơn thay vì chỉ nhìn marker.

### Nội dung hiển thị

- PM2.5 hiện tại.
- Biểu đồ lịch sử.
- Trạng thái sensor.
- Active alert.
- Timestamp.
- Source.

### Tiêu chí chấp nhận

- Không dùng measurement invalid.
- Lịch sử sắp theo thời gian.
- Dữ liệu stale được cảnh báo.
- Xem được tối thiểu 24 giờ nếu có dữ liệu.

---

## 6.3. Alert Engine

### Mục đích

Phát hiện sự kiện cần chú ý bằng rule cố định và có thể kiểm thử.

### Các rule chính

- PM2.5 vượt ngưỡng trong nhiều measurement liên tiếp.
- Sensor ngừng gửi dữ liệu.
- Không tạo alert trùng trong cooldown.
- Resolve alert khi điều kiện trở lại bình thường.

### Tiêu chí chấp nhận

- `sudden_spike` tạo đúng alert.
- `sensor_offline` tạo đúng alert.
- Một measurement bất thường đơn lẻ không tạo cảnh báo diện rộng.
- Không phụ thuộc LLM.

---

## 6.4. AI Agent Chat

### Mục đích

Giúp người dùng hỏi dữ liệu bằng ngôn ngữ tự nhiên thay vì tự đọc bảng và biểu đồ.

### Các intent chính

| Intent | Ví dụ |
|---|---|
| `current_pm25` | PM2.5 ở S03 là bao nhiêu? |
| `station_history` | PM2.5 có đang tăng không? |
| `compare_stations` | Khu nào ô nhiễm nhất? |
| `outdoor_recommendation` | Tôi có nên chạy bộ không? |
| `sensitive_user_advice` | Người nhạy cảm nên tránh đâu? |
| `active_alerts` | Hiện có cảnh báo nào? |
| `alert_explanation` | Vì sao S03 bị cảnh báo? |
| `forecast_pm25` | 3 giờ tới PM2.5 thế nào? |
| `proposal_creation` | Có cần tạo cảnh báo không? |
| `out_of_scope` | Câu hỏi ngoài phạm vi |

### Luồng Agent

```text
classify_intent
→ resolve_station
→ select_tools
→ execute_tools
→ evaluate_risk
→ create_proposal_if_needed
→ generate_response
→ save_trace
```

### Tiêu chí chấp nhận

- Đúng ít nhất 8/10 test case.
- 100% số liệu đến từ tool.
- Có timestamp và evidence.
- Không bịa số.
- Không chẩn đoán y tế.
- Không nói “an toàn tuyệt đối”.

---

## 6.5. Warning Proposal và HITL

### Mục đích

Cho phép Agent đề xuất cảnh báo nhưng vẫn giữ quyền quyết định cho con người.

### Điều kiện tạo proposal

- Có active alert.
- Sensor online.
- Data valid.
- Data chưa stale.
- Evidence đầy đủ.
- Không có proposal pending trùng.

### Nội dung proposal

- Station.
- Alert.
- PM2.5.
- Severity.
- Timestamp.
- Reason.
- Evidence.
- Proposed message.
- Status `pending`.

### Manager có thể

- Approve.
- Reject.
- Ghi review note.

### Tiêu chí chấp nhận

- Agent không tự approve/reject.
- Chỉ proposal `pending` được review.
- Mọi quyết định được lưu audit log.
- Proposal rejected không được phát cảnh báo.

---

# 7. Định nghĩa Agent

## Phần này gồm những gì?

| Agent | Vai trò chính |
|---|---|
| Supervisor/Router | Phân loại intent và điều phối |
| Sensor Data Agent | Lấy current, history và compare |
| Weather Agent | Lấy thông tin thời tiết |
| Forecast Agent | Dự báo PM2.5 |
| Risk Assessment Agent | Đánh giá rủi ro |
| Recommendation Agent | Tạo khuyến nghị |
| Warning Proposal Agent | Tạo proposal |
| Response Agent | Soạn câu trả lời |
| Trace/Audit Agent | Lưu trace và audit |

## Giải thích ngắn

Trong MVP, các “Agent” có thể là các node hoặc service trong một workflow, không nhất thiết là các LLM độc lập. Cách này giúp hệ thống dễ kiểm soát và debug hơn.

---

## 7.1. Supervisor/Router Agent

### Nhiệm vụ

- Nhận câu hỏi.
- Xác định intent.
- Resolve station.
- Chọn tool.
- Điều phối workflow.

### Không được làm

- Tự tạo số liệu.
- Bỏ qua tool khi câu hỏi cần dữ liệu.

---

## 7.2. Sensor Data Agent

### Nhiệm vụ

- Lấy PM2.5 hiện tại.
- Lấy lịch sử.
- So sánh station.

### Tool

- `get_current_pm25`
- `get_station_history`
- `compare_stations`

---

## 7.3. Weather Context Agent

### Nhiệm vụ

Lấy dữ liệu thời tiết để hỗ trợ phân tích.

### Tool

- `get_weather_context`

### Lưu ý

Weather chỉ là bối cảnh, không thay thế sensor.

---

## 7.4. Forecast Agent

### Nhiệm vụ

Dự báo PM2.5 trong 1–3 giờ.

### Tool

- `get_pm25_forecast`

### Yêu cầu output

- Forecast value.
- Forecast time.
- Model name.
- Generated time.
- Confidence.

### Guardrail

- Không khẳng định chắc chắn.
- Thiếu dữ liệu phải trả lỗi.

---

## 7.5. Risk Assessment Agent

### Input

- Current PM2.5.
- History.
- Forecast.
- Weather.
- User profile.
- Active alerts.

### Output

```json
{
  "risk_level": "high",
  "reasons": [
    "PM2.5 hiện tại cao",
    "Xu hướng tiếp tục tăng"
  ],
  "affected_groups": [
    "sensitive",
    "outdoor_sport"
  ]
}
```

### Lưu ý

Threshold đến từ Rule Engine, không do Agent tự đặt.

---

## 7.6. Recommendation Agent

### Nhiệm vụ

Tạo khuyến nghị cho:

- `normal`
- `sensitive`
- `outdoor_sport`

### Output

```json
{
  "recommendation": "Nên hoãn chạy bộ tại S05 trong 1–2 giờ.",
  "confidence": "medium",
  "basis": [
    "current_pm25",
    "forecast",
    "user_profile"
  ]
}
```

---

## 7.7. Warning Proposal Agent

### Nhiệm vụ

Tạo proposal khi đủ điều kiện.

### Tool

- `create_warning_proposal`

### Không được làm

- Approve.
- Reject.
- Phát cảnh báo trực tiếp.

---

## 7.8. Response Agent

### Nhiệm vụ

Soạn câu trả lời cuối cùng bằng tiếng Việt.

### Câu trả lời cần có

- Số liệu.
- Đơn vị.
- Station.
- Timestamp.
- Source.
- Evidence.
- Recommendation.
- Confidence nếu có forecast.

---

## 7.9. Trace/Audit Agent

### Lưu

- Message.
- Intent.
- Tool.
- Tool input.
- Tool output.
- Error.
- Latency.
- Final answer.
- Proposal ID.

### Không lưu

- Password.
- API key.
- JWT raw token.

---

# 8. Tool Contract

## Phần này gồm những gì?

| Tool | Mục đích |
|---|---|
| `get_current_pm25` | Lấy PM2.5 hiện tại |
| `get_station_history` | Lấy lịch sử |
| `compare_stations` | So sánh trạm |
| `get_weather_context` | Lấy thời tiết |
| `get_pm25_forecast` | Lấy forecast |
| `get_active_alerts` | Lấy active alert |
| `get_user_profile` | Lấy profile |
| `create_warning_proposal` | Tạo proposal |
| `save_agent_trace` | Lưu trace |

## Giải thích ngắn

Mỗi tool phải được định nghĩa trước khi Agent sử dụng. Tool cần có input, output, error schema, timeout, guardrail và test case.

## Bảng contract

| Tool | Input chính | Output bắt buộc |
|---|---|---|
| `get_current_pm25` | `station_id` | station, pm25, unit, status, quality_flag, measured_at |
| `get_station_history` | `station_id`, `hours` | measurements, count, time range |
| `compare_stations` | `station_ids` | ranking, best, worst, comparison_valid |
| `get_weather_context` | `location` | temperature, humidity, wind, rain, observed_at |
| `get_pm25_forecast` | `station_id`, `hours` | forecast, model_name, generated_at, confidence |
| `get_active_alerts` | `station_id?` | alerts, severity, status |
| `get_user_profile` | `user_id` | role, user_group |
| `create_warning_proposal` | alert, station, evidence, message | proposal_id, status, created_at |
| `save_agent_trace` | intent, tools, input/output, answer | trace_id, status |

## Yêu cầu bắt buộc với mọi tool

- Input schema.
- Output schema.
- Error schema.
- Timeout.
- Test case.
- Trace.
- Guardrail.

---

# 9. Data Definition

## Phần này gồm những gì?

| Data object | Dùng để làm gì |
|---|---|
| Station | Lưu thông tin trạm |
| Measurement | Lưu dữ liệu PM2.5 |
| Alert | Lưu cảnh báo |
| Warning Proposal | Lưu đề xuất cảnh báo |
| User | Lưu role và user group |
| Agent Trace | Lưu quá trình Agent xử lý |

## Giải thích ngắn

Data contract giúp Backend, Frontend và Agent sử dụng cùng tên field và cùng ý nghĩa.

---

## 9.1. Station

```json
{
  "station_id": "S03",
  "station_name": "Trục đường chính",
  "latitude": 21.0001,
  "longitude": 105.9442,
  "location_type": "road",
  "status": "online"
}
```

## 9.2. Measurement

```json
{
  "message_id": "MSG-S03-20260806T190000",
  "station_id": "S03",
  "pm25": 78.4,
  "unit": "ug/m3",
  "quality_flag": "valid",
  "source": "sensor_simulator",
  "scenario": "sudden_spike",
  "measured_at": "2026-08-06T19:00:00+07:00",
  "received_at": "2026-08-06T19:00:01+07:00"
}
```

## 9.3. Alert

```json
{
  "alert_id": "A001",
  "station_id": "S03",
  "type": "pm25_high",
  "severity": "high",
  "observed_value": 78.4,
  "threshold": 75.0,
  "status": "active",
  "created_at": "2026-08-06T19:00:00+07:00"
}
```

## 9.4. Warning Proposal

```json
{
  "proposal_id": "P001",
  "alert_id": "A001",
  "station_id": "S03",
  "status": "pending",
  "reason": "PM2.5 vượt ngưỡng",
  "proposed_message": "Hạn chế hoạt động ngoài trời tại S03.",
  "created_by": "agent",
  "created_at": "2026-08-06T19:01:00+07:00"
}
```

## 9.5. User

```json
{
  "user_id": "U001",
  "email": "user@airguard.local",
  "role": "resident",
  "user_group": "outdoor_sport"
}
```

---

# 10. Mô phỏng dữ liệu

## Phần này gồm những gì?

| Nội dung | Ý nghĩa |
|---|---|
| Base value | Mức PM2.5 nền của từng trạm |
| Rush hour effect | Ảnh hưởng giờ cao điểm |
| Weather effect | Ảnh hưởng gió, mưa, độ ẩm |
| Scenario effect | Tình huống test |
| Small noise | Tạo dao động tự nhiên |

## Giải thích ngắn

Dữ liệu không được random hoàn toàn. Nó phải phản ánh đặc điểm vị trí, thời gian và scenario để phục vụ test.

## Công thức mô phỏng

```text
PM2.5 =
base_value_by_station
+ rush_hour_effect
+ weather_effect
+ scenario_effect
+ small_noise
```

## Scenario tối thiểu

| Scenario | Mục đích test |
|---|---|
| `normal` | Luồng bình thường |
| `rush_hour_pollution` | PM2.5 tăng giờ cao điểm |
| `rain_cleanup` | PM2.5 giảm sau mưa |
| `sudden_spike` | Tăng đột ngột |
| `sensor_offline` | Sensor ngừng gửi |
| `stale_data` | Dữ liệu quá cũ |
| `invalid_data` | Dữ liệu lỗi |

## MQTT topic

```text
airguard/stations/{station_id}/measurements
```

## Data quality rules

- `message_id` duy nhất.
- `station_id` phải tồn tại.
- `pm25 >= 0`.
- Timestamp có timezone.
- Duplicate message bị bỏ qua.
- Stale data được đánh dấu.
- Sensor offline sau timeout.

---

# 11. API FE–BE

## Phần này gồm những gì?

| Nhóm API | Mục đích |
|---|---|
| Auth | Login, current user, logout |
| Stations | Danh sách, chi tiết, current, history |
| Compare | So sánh nhiều trạm |
| Alerts | Lấy cảnh báo |
| Agent | Gửi câu hỏi |
| Proposals | Tạo và duyệt proposal |

## Giải thích ngắn

API phải được define trước để FE và BE không tự đặt field khác nhau. Backend có thể trả mock response trước, nhưng schema phải ổn định.

## Danh sách endpoint bắt buộc

```text
GET    /api/v1/health

POST   /api/v1/auth/login
GET    /api/v1/auth/me
POST   /api/v1/auth/logout

GET    /api/v1/stations
GET    /api/v1/stations/{station_id}
GET    /api/v1/stations/{station_id}/current
GET    /api/v1/stations/{station_id}/history
POST   /api/v1/stations/compare

GET    /api/v1/alerts/active

POST   /api/v1/agent/chat

GET    /api/v1/proposals
POST   /api/v1/proposals
PATCH  /api/v1/proposals/{proposal_id}/approve
PATCH  /api/v1/proposals/{proposal_id}/reject
```

## Response thành công

```json
{
  "success": true,
  "data": {},
  "message": "OK",
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

## Response lỗi

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Mô tả lỗi",
    "details": {}
  },
  "timestamp": "2026-08-06T19:00:00+07:00"
}
```

## Nguyên tắc tích hợp

- FE không tự đặt field khác BE.
- BE không đổi schema tùy ý.
- Breaking change phải cập nhật tài liệu trước khi merge.
- API có thể mock trước.
- Swagger phải phản ánh đúng contract.

---

# 12. Metrics

## Phần này gồm những gì?

| Nhóm metric | Đo điều gì |
|---|---|
| Agent | Hiểu đúng, chọn đúng tool, không bịa |
| Backend | API ổn định và nhanh |
| Frontend | Render đúng, không crash |
| Data/MQTT | Dữ liệu đủ, đúng và không trùng |
| Alert/HITL | Cảnh báo đúng và có kiểm soát |

## Giải thích ngắn

Metric giúp nhóm chứng minh hệ thống hoạt động tốt đến mức nào, thay vì chỉ nói “đã chạy được”.

## 12.1. Agent Metrics

| Metric | Mục tiêu |
|---|---|
| Intent Accuracy | ≥ 80% |
| Tool Selection Accuracy | ≥ 80% |
| Tool Call Success Rate | ≥ 90% |
| Evidence Coverage | ≥ 90% |
| Hallucination Rate | 0% |
| Trace Logging Rate | 100% |
| Response Latency local | < 5 giây |
| Proposal từ stale/invalid/offline | 0 case |

## 12.2. Backend Metrics

| Metric | Mục tiêu |
|---|---|
| API success rate | ≥ 95% |
| P95 response time local | < 1 giây |
| Swagger coverage | 100% API chính |
| Unauthorized request bị chặn | 100% |

## 12.3. Frontend Metrics

| Metric | Mục tiêu |
|---|---|
| Station hiển thị | 5/5 |
| White screen/crash | 0 |
| Loading/error/empty state | 100% màn gọi API |
| API integration success | ≥ 90% |

## 12.4. Data/MQTT Metrics

| Metric | Mục tiêu |
|---|---|
| Sensor coverage | 5/5 |
| MQTT delivery | ≥ 95% |
| Invalid data rejection | 100% |
| Timestamp completeness | 100% |
| Scenario coverage | ≥ 6 |
| Duplicate record | 0 |

## 12.5. Alert/HITL Metrics

| Metric | Mục tiêu |
|---|---|
| High PM2.5 detection | ≥ 90% scenario |
| Duplicate alert | 0 trong demo |
| Approve/reject completion | 100% |
| Audit log coverage | 100% |
| Agent tự approve/reject | 0% |

---

# 13. Cách đánh giá

## Phần này gồm những gì?

| Hình thức đánh giá | Mục đích |
|---|---|
| Agent test | Kiểm tra intent, tool và guardrail |
| Forecast test | Đánh giá sai số dự báo |
| Integration test | Kiểm tra các module kết nối |
| E2E test | Kiểm tra toàn bộ luồng |

## Giải thích ngắn

Đánh giá phải dùng test case có expected result rõ ràng, không chỉ demo bằng cảm giác.

## 13.1. Agent test

| ID | Câu hỏi | Intent | Tool |
|---|---|---|---|
| AG-01 | PM2.5 ở S03 hiện tại là bao nhiêu? | current_pm25 | get_current_pm25 |
| AG-02 | PM2.5 S03 có đang tăng không? | station_history | get_station_history |
| AG-03 | Khu nào ô nhiễm nhất? | compare_stations | compare_stations |
| AG-04 | So sánh S03 và S04 | compare_stations | compare_stations |
| AG-05 | Tôi có nên chạy bộ ở S05 không? | outdoor_recommendation | current + weather + forecast + profile |
| AG-06 | Hiện có cảnh báo nào? | active_alerts | get_active_alerts |
| AG-07 | Vì sao S03 bị cảnh báo? | alert_explanation | alerts + history |
| AG-08 | 3 giờ tới PM2.5 S05 thế nào? | forecast_pm25 | get_pm25_forecast |
| AG-09 | Có cần tạo cảnh báo không? | proposal_creation | alerts + proposal |
| AG-10 | Hôm nay chứng khoán thế nào? | out_of_scope | không gọi tool môi trường |

Mỗi test chấm:

- Intent đúng.
- Tool đúng.
- Input tool đúng.
- Có evidence.
- Có timestamp.
- Không hallucination.
- Guardrail hoạt động.
- Trace được lưu.

## 13.2. Forecast evaluation

- Persistence baseline.
- MAE.
- RMSE.
- Tách horizon 1 giờ, 2 giờ, 3 giờ.
- Ghi rõ dữ liệu dùng để đánh giá là giả lập.

## 13.3. E2E evaluation

### E2E-01 — PM2.5 cao

```text
S03 PM2.5 cao
→ MQTT
→ Backend
→ Alert
→ Dashboard
→ Agent trả evidence
```

### E2E-02 — Khuyến nghị chạy bộ

```text
Outdoor user hỏi chạy bộ tại S05
→ Profile
→ Current PM2.5
→ Weather
→ Forecast
→ Recommendation
```

### E2E-03 — Warning Proposal

```text
S03 sudden spike
→ Alert
→ Proposal pending
→ Manager approve/reject
→ Audit log
```

---

# 14. Definition of Done

## Phần này gồm những gì?

| Thành phần | Khi nào được coi là xong |
|---|---|
| API | Có schema, Swagger, test và FE gọi được |
| Agent Tool | Có input/output/error, guardrail và trace |
| Frontend | Render đúng, có loading/error/empty |
| Data Pipeline | Publish, validate, lưu và phát hiện lỗi |
| E2E | Chạy được luồng hoàn chỉnh |

## Giải thích ngắn

Definition of Done giúp tránh tình trạng một thành viên nói “xong” nhưng module vẫn chưa thể tích hợp.

## API Done

- Có endpoint.
- Có request schema.
- Có response schema.
- Có error schema.
- Có Swagger.
- Có test.
- FE gọi được.
- Không đổi contract ngoài tài liệu.

## Agent Tool Done

- Có purpose.
- Có input/output/error.
- Có timeout.
- Có guardrail.
- Có trace.
- Có test.
- Không bịa dữ liệu.

## Frontend Done

- Render đúng.
- Gọi đúng API.
- Có loading.
- Có error.
- Có empty state.
- Không trắng màn hình.
- Không hard-code production data.

## Data Pipeline Done

- 5 sensor publish được.
- Backend validate đúng.
- Duplicate bị loại.
- Offline/stale được phát hiện.
- Scenario demo chạy được.

---

# 15. Rủi ro và quyết định cần chốt

## Phần này gồm những gì?

| Vấn đề | Vì sao cần chốt |
|---|---|
| Admin có nằm trong MVP không | Ảnh hưởng UI và phân quyền |
| Threshold PM2.5 | Ảnh hưởng Alert Engine |
| Stale/offline timeout | Ảnh hưởng Data Quality |
| Forecast baseline | Ảnh hưởng phạm vi Data/AI |
| Evidence trên UI | Ảnh hưởng FE và Agent response |
| Authentication | Ảnh hưởng FE–BE contract |
| Tool failure policy | Ảnh hưởng Agent workflow |
| Sensor Simulator | Cần Mentor xác nhận |

## Câu hỏi cần chốt

- Admin có bắt buộc trong MVP không?
- Ngưỡng PM2.5 dùng chuẩn nào?
- Bao nhiêu phút thì stale?
- Bao nhiêu phút thì offline?
- Forecast baseline có đủ không?
- Evidence có bắt buộc hiện trên UI không?
- Dùng authentication thật hay demo account?
- Tool lỗi thì Agent trả lời một phần hay dừng?
- Sensor Simulator qua MQTT có được chấp nhận cho MVP không?

---

# 16. Tiêu chí thành công cuối cùng

## Phần này gồm những gì?

| Nhóm | Kết quả cần đạt |
|---|---|
| Data | 5 sensor publish được |
| Backend | Lưu dữ liệu đúng, không trùng |
| Frontend | Hiển thị đúng 5 trạm |
| Alert | Phát hiện đúng scenario |
| Agent | Đúng ít nhất 8/10 test |
| HITL | Approve/reject thành công |
| E2E | Chạy ít nhất 3 scenario |
| Demo | Không có lỗi blocking |

## Checklist cuối

- [ ] 5 sensor giả lập publish qua MQTT.
- [ ] Backend lưu measurement hợp lệ và không trùng.
- [ ] Dashboard hiển thị đúng 5 trạm.
- [ ] Sensor offline được phát hiện.
- [ ] Alert Engine xử lý đúng scenario.
- [ ] Agent trả lời đúng tối thiểu 8/10 test.
- [ ] 100% số liệu môi trường đến từ tool.
- [ ] Agent không tạo proposal từ stale, invalid hoặc offline data.
- [ ] Manager approve/reject thành công.
- [ ] Audit log lưu đủ hành động quan trọng.
- [ ] Ít nhất 3 kịch bản E2E chạy thành công.
- [ ] Không có lỗi blocking trong buổi demo.

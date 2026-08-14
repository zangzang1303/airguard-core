# Product Requirements Document — AirGuard AI

> Phiên bản: 2.0
>
> Cập nhật: 14/08/2026
>
> Trạng thái: Phản ánh MVP hiện tại
>
> Phạm vi: Vinhomes Ocean Park 1, dữ liệu mô phỏng

## 1. Tóm tắt sản phẩm

AirGuard AI là nền tảng quan sát AQI và các yếu tố môi trường quanh Vinhomes Ocean Park 1. Hệ thống thu dữ liệu từ 5 trạm mô phỏng S01–S05, truyền qua MQTT, lưu vào PostgreSQL và cung cấp dashboard, cảnh báo, dự báo ngắn hạn, AI Agent và quy trình Human-in-the-Loop (HITL).

Trên giao diện tổng quan, **AQI là chỉ số chính**. Khi chọn một trạm, hệ thống hiển thị AQI cùng bốn chỉ số thành phần:

- PM2.5 (µg/m³);
- CO₂ (ppm);
- tiếng ồn (dB);
- nhiệt độ (°C).

Đây là sản phẩm học tập/MVP. Dữ liệu có nguồn simulator, không phải quan trắc được chứng nhận, không dùng để chẩn đoán y tế, ra quyết định pháp lý hoặc tự động điều khiển thiết bị thật.

## 2. Vấn đề cần giải quyết

Người dân và ban quản lý cần một nơi thống nhất để:

- biết nhanh AQI chung của khu vực;
- xem nguyên nhân và các chỉ số thành phần tại từng trạm;
- nhận cảnh báo khi một chỉ số vượt ngưỡng;
- hiểu ảnh hưởng theo nhóm người dùng;
- xem xu hướng 1–3 giờ tới;
- nhận khuyến nghị có căn cứ từ dữ liệu;
- kiểm soát hành động phát cảnh báo hoặc điều khiển bằng phê duyệt của con người.

Nếu chỉ hiển thị PM2.5, người dùng thiếu cái nhìn tổng quan. Nếu AI tự tạo số liệu hoặc tự gửi cảnh báo, sản phẩm không bảo đảm độ tin cậy và an toàn.

## 3. Mục tiêu

### 3.1 Mục tiêu MVP

1. Thu nhận và lưu dữ liệu của 5 trạm cho PM2.5, CO₂, tiếng ồn và nhiệt độ.
2. Tính và hiển thị AQI nhất quán ở backend, frontend và Agent.
3. Cập nhật dashboard gần realtime bằng polling khi trang đang hiển thị.
4. Cho phép xem lịch sử và dự báo 1–3 giờ theo từng metric.
5. Phát hiện vượt ngưỡng, tạo cảnh báo và khuyến nghị.
6. Cho phép Agent đánh giá ảnh hưởng từ dữ liệu backend đã grounded.
7. Bảo vệ hành động quan trọng bằng HITL, RBAC và audit.
8. Gửi notification thật qua SMTP khi được cấu hình.

### 3.2 Chỉ số thành công

- 5/5 trạm xuất hiện trên dashboard và có trạng thái dữ liệu rõ ràng.
- Measurement hợp lệ đi qua simulator → MQTT → consumer → DB → API → UI.
- Dashboard tải lại dữ liệu mỗi 30 giây khi tab đang hiển thị.
- Current response và Agent ưu tiên AQI, đồng thời có đủ 4 chỉ số thành phần khi xem trạm.
- Forecast trả 3 horizon 1h, 2h, 3h và không chỉ lặp lại giá trị hiện tại.
- Alert có metric, observed value, threshold, severity và recommendation.
- Proposal chỉ được dispatch sau khi manager phê duyệt.
- Các hành động create/approve/reject/dispatch/failure quan trọng có audit record.
- Agent không bịa số liệu khi backend hoặc tool lỗi.

## 4. Ngoài phạm vi hiện tại

- AQI chính thức theo NowCast hoặc trạm quan trắc được kiểm định.
- Mô hình lan truyền ô nhiễm khoa học theo gió, địa hình và khí tượng.
- Ranh giới pháp lý/chính thức của Vinhomes Ocean Park 1.
- Prophet hoặc LSTM production-grade; MVP dùng baseline chuỗi thời gian.
- Chẩn đoán hoặc tư vấn y tế cá nhân.
- Tự động điều khiển thiết bị thật không qua phê duyệt.
- IAM/RBAC production hoàn chỉnh; giao diện hiện dùng danh tính demo.
- SLA production và hạ tầng high availability.

## 5. Người dùng

| Nhóm | Nhu cầu chính |
|---|---|
| Cư dân bình thường | Xem AQI, chi tiết trạm, xu hướng và khuyến nghị sinh hoạt |
| Người nhạy cảm | Nhận giải thích thận trọng hơn khi mức ô nhiễm tăng |
| Người hoạt động ngoài trời | Đánh giá mức phù hợp để vận động ngoài trời |
| Quản lý môi trường | Theo dõi toàn khu, xử lý alert, duyệt/từ chối proposal |
| Quản trị/demo operator | Khởi chạy hệ thống, cấu hình tích hợp và kiểm tra audit |

Các nhóm hồ sơ Agent hỗ trợ là normal, sensitive và outdoor_sport.

## 6. Nguyên tắc sản phẩm

1. **AQI-first:** màn hình tổng quan nói về AQI; metric chi tiết mở ở cấp trạm.
2. **Grounding trước diễn giải:** mọi environmental fact của Agent đến từ backend tool result trong cùng request.
3. **Backend là system of record:** frontend không kết nối MQTT trực tiếp và không tự tính business alert.
4. **Data quality là gate:** invalid, stale hoặc offline không được dùng như current data hợp lệ.
5. **Minh bạch nguồn:** UI và Agent luôn thể hiện dữ liệu mô phỏng.
6. **HITL bắt buộc:** Agent chỉ tạo proposal pending; manager mới được approve/reject.
7. **Không phóng đại mô hình:** forecast baseline và vùng nhiệt phải có disclaimer.
8. **Không lộ bí mật:** API key, SMTP password và credential không được commit hoặc ghi log.

## 7. Yêu cầu chức năng

### FR-01 — Trạm và pipeline dữ liệu

Hệ thống quản lý 5 trạm S01–S05 với id bất biến, tên, tọa độ, loại vị trí và trạng thái.

Mỗi measurement hợp lệ có tối thiểu message_id, station_id, pm25, co2, noise_db, temperature, timestamp có timezone và source=simulator. Consumer validate schema, timestamp, station và duplicate trước khi persist.

**Tiêu chí chấp nhận**

- Simulator phát measurement và station status theo MQTT contract.
- Consumer lưu đủ 4 metric môi trường cho payload hợp lệ.
- Duplicate, invalid, stale và offline được xử lý theo data-quality policy.
- Rejection có reason truy vết được.

### FR-02 — AQI realtime

Backend tính AQI từ PM2.5 theo breakpoint US_EPA_PM25_24H_2012. Giá trị hiện tại là PM2.5 concentration sub-index cho demo, không phải AQI chính thức hoặc NowCast 24 giờ.

**Tiêu chí chấp nhận**

- Công thức ở backend và dùng nhất quán bởi API, alert, frontend và Agent.
- Dashboard dùng AQI làm chỉ số nổi bật và màu marker.
- Chi tiết trạm hiển thị AQI cùng PM2.5, CO₂, tiếng ồn và nhiệt độ.
- Response có label, mức phân loại, nguồn và thời gian.

### FR-03 — Dashboard gần realtime

Dashboard hiển thị trạng thái toàn khu, bản đồ 5 trạm, cảnh báo gần nhất và trạng thái cảm biến.

**Tiêu chí chấp nhận**

- Polling mỗi 30 giây khi tab đang visible.
- Có loading, empty, stale, offline và error state.
- Có refresh thủ công.
- Marker đổi màu theo AQI và mở được station detail.
- Toàn màn hình có disclaimer dữ liệu mô phỏng.

WebSocket không phải yêu cầu của MVP hiện tại.

### FR-04 — Bản đồ khu vực và vùng nhiệt

Bản đồ làm nổi bật phạm vi Ocean Park 1 và làm mờ phần ngoài phạm vi ở mọi mức zoom hợp lệ.

**Tiêu chí chấp nhận**

- Polygon phạm vi render độc lập với tile và tiếp tục che nền ngoài khi zoom/pan.
- Phần ngoài có lớp nền tối/xám; phần trong polygon vẫn đọc được.
- Đường viền và chú thích đủ rõ, không che tương tác chính.
- Có nút bật/tắt vùng nhiệt.
- Vùng nhiệt chỉ mô tả cường độ AQI quanh trạm, không được gọi là mô hình lan truyền khoa học.
- Polygon được ghi nhãn là hình học OSM đơn giản hóa, không phải ranh giới pháp lý.

### FR-05 — Chi tiết và lịch sử trạm

Người dùng chọn metric aqi, pm25, co2, noise_db hoặc temperature để xem current value và lịch sử.

**Tiêu chí chấp nhận**

- Current card luôn có AQI và đủ 4 chỉ số thành phần.
- Biểu đồ lịch sử hỗ trợ 1–72 giờ theo API contract.
- Trục, đơn vị, tooltip và empty state đúng theo metric.
- Dữ liệu stale/offline không được trình bày như current data tốt.

### FR-06 — Dự báo 1–3 giờ

Backend tạo dự báo riêng theo metric từ lịch sử gần nhất, không lặp current value.

Triển khai MVP:

- Metric: aqi, pm25, co2, noise_db, temperature.
- Horizon: 1h, 2h, 3h.
- Mô hình: damped_linear_trend_v1.
- Đầu vào: 3–24 điểm trong 90 phút gần nhất.
- Đầu ra: point forecast, khoảng dự báo, confidence, freshness, model và source.

**Tiêu chí chấp nhận**

- Thiếu dữ liệu, stale hoặc offline trả structured error.
- UI hiển thị model, confidence, range và disclaimer.
- Agent không diễn giải forecast nếu backend không cung cấp.
- Prophet/LSTM được ghi rõ là chưa triển khai.

### FR-07 — Cảnh báo vượt ngưỡng

Alert engine đánh giá nhiều metric và sinh recommendation. Ngưỡng hiện tại là **provisional demo thresholds**:

| Metric | Warning | Critical |
|---|---:|---:|
| AQI | 101 | 151 |
| PM2.5 | 50 µg/m³ | 100 µg/m³ |
| CO₂ | 1000 ppm | 1500 ppm |
| Tiếng ồn | 70 dB | 85 dB |
| Nhiệt độ | 35 °C | 39 °C |

Station offline cũng tạo alert phù hợp.

**Tiêu chí chấp nhận**

- Alert có station, metric, observed value, threshold, severity, rule version, status và recommendation.
- Không tạo environmental alert từ dữ liệu invalid/stale/offline.
- Có cooldown, deduplication và resolve theo policy.
- Recommendation không đưa ra chẩn đoán y tế.
- Threshold và policy version audit được.

### FR-08 — Đánh giá ảnh hưởng và khuyến nghị

Agent kết hợp current measurements, alert, forecast và user profile để đánh giá ảnh hưởng.

**Tiêu chí chấp nhận**

- Câu trả lời tổng quan bắt đầu bằng AQI.
- Câu hỏi về một trạm trả AQI và đủ 4 metric nếu backend cung cấp.
- Nêu station, measured time, freshness/status, source và giới hạn dữ liệu.
- Phân biệt khuyến nghị cho normal, sensitive và outdoor_sport.
- Nếu thiếu dữ liệu, Agent nói rõ thiếu gì và không suy đoán.

### FR-09 — AI Agent grounded

Agent dùng LangGraph/tool calling cho current condition, impact, history, comparison, weather, forecast, alert, profile, recommendation và warning proposal.

LLM, khi cấu hình, chỉ bổ sung diễn giải ngắn dựa trên evidence đã grounded. Nếu không có key hoặc LLM lỗi, deterministic composer vẫn trả lời từ tool result.

**Tiêu chí chấp nhận**

- LLM chỉ được gọi sau khi có evidence cần thiết.
- Tool failure trả structured error và được giải thích minh bạch.
- Không có fallback hallucination.
- Prompt injection không thay đổi quyền approve/reject hoặc cho phép truy cập DB/MQTT.
- Response đủ ngắn để đọc trên UI.

### FR-10 — Warning proposal và HITL

Agent có thể tạo warning proposal từ evidence hợp lệ. Proposal mới luôn ở trạng thái pending.

**Tiêu chí chấp nhận**

- Proposal có target, action, rationale, evidence, policy version và correlation id.
- Chỉ manager được approve/reject.
- Agent và resident không được tự approve/reject.
- Device command chỉ dispatch sau approval server-side.
- Create, approve, reject, dispatch, ack và failure có audit record.

### FR-11 — Notification

Worker gửi notification thật qua SMTP khi NOTIFICATION_PROVIDER=smtp và các biến SMTP được cấu hình hợp lệ. Mặc định notification có thể disabled để chạy local không cần secret.

**Tiêu chí chấp nhận**

- Delivery result phân biệt delivered, failed, disabled và retryable state.
- Không ghi password/token vào log hoặc API response.
- Failure có audit và không làm mất proposal/approval state.
- Không báo mock_delivered như thể đã gửi thật.

### FR-12 — Audit

Audit log là append-only cho hành động quan trọng.

**Tiêu chí chấp nhận**

- Record có actor, action, target, outcome, correlation id và timestamp.
- API lọc/xem audit theo quyền.
- Frontend không sửa được audit history.
- Log không chứa secret hoặc PII không cần thiết.

## 8. Luồng người dùng chính

### 8.1 Xem chất lượng môi trường

1. Người dùng mở Dashboard.
2. Hệ thống hiển thị AQI chung và 5 trạm.
3. Người dùng chọn marker.
4. Popup hiển thị AQI nổi bật và metric thành phần.
5. Người dùng mở chi tiết để xem lịch sử và forecast.

### 8.2 Hỏi Agent

1. Người dùng hỏi tình trạng hoặc ảnh hưởng tại một trạm.
2. Agent xác định intent và gọi backend tool.
3. Backend trả measurement, status, forecast, alert hoặc profile.
4. Agent compose câu trả lời AQI-first với source và timestamp.
5. LLM có thể thêm diễn giải grounded; deterministic response vẫn hoạt động nếu LLM lỗi.

### 8.3 Cảnh báo và phê duyệt

1. Alert engine phát hiện vượt ngưỡng từ dữ liệu hợp lệ.
2. Alert kèm recommendation được tạo và audit.
3. Agent hoặc người dùng tạo warning proposal.
4. Manager review evidence và approve/reject.
5. Khi approve, worker dispatch notification/device command theo cấu hình.
6. Delivery, ack hoặc failure được audit.

## 9. API và integration contract

REST canonical nằm dưới /api/v1. Các nhóm endpoint:

- health và stations/current;
- station history và comparison;
- forecast theo metric;
- alerts và recommendations;
- profiles;
- warning proposals/approvals;
- audit;
- jobs/delivery khi async profile được bật.

Agent không truy cập PostgreSQL hoặc MQTT trực tiếp. Tool registry giữ một số tên legacy như get_current_pm25 và get_pm25_forecast để tương thích, nhưng response phải hỗ trợ AQI-first và metric selection.

MQTT topics:

~~~text
airguard/stations/{station_id}/measurements
airguard/stations/{station_id}/status
airguard/devices/{device_id}/command
airguard/devices/{device_id}/status
~~~

Mọi thay đổi contract cập nhật đồng thời specs, producer, consumer, API, frontend/Agent adapter và tests.

## 10. Kiến trúc hiện tại

~~~text
Sensor Simulator -> Mosquitto MQTT -> MQTT Consumer
  -> PostgreSQL -> FastAPI /api/v1 -> React + Leaflet

FastAPI tools -> LangGraph Agent -> grounded answer/proposal
  -> manager HITL -> audit -> optional SMTP/device simulator
~~~

Async jobs dùng RabbitMQ, Redis và Celery qua Compose profile async-jobs.

## 11. Dữ liệu và trạng thái

| Field | Đơn vị |
|---|---|
| AQI | Không đơn vị |
| PM2.5 | µg/m³ |
| CO₂ | ppm |
| Tiếng ồn | dB |
| Nhiệt độ | °C |

Trạng thái dữ liệu:

- online: trạm đang gửi dữ liệu hợp lệ;
- stale: dữ liệu cuối vượt freshness window;
- offline: không có heartbeat phù hợp;
- invalid: payload không qua validation.

Chỉ measurement hợp lệ và đủ freshness mới dùng cho current, alert, forecast hoặc proposal.

## 12. Yêu cầu phi chức năng

### An toàn và bảo mật

- Không bịa dữ liệu khi tool/backend lỗi.
- Không diễn đạt simulator như quan trắc chính thức.
- Không đưa chẩn đoán y tế hoặc kết luận pháp lý.
- Không bypass HITL.
- File .env không được commit.
- Secret không xuất hiện trong log, screenshot, audit hoặc error response.
- Approve/reject kiểm tra role server-side.
- Demo identity phải được thay bằng IAM production trước triển khai thật.

### Khả dụng và quan sát

- UI responsive ở kích thước desktop phổ biến.
- Có loading, empty, stale, offline và error state.
- Dashboard vẫn hoạt động khi LLM bị tắt.
- Backend và Agent có health endpoint.
- Log có request/correlation id cho luồng quan trọng.
- Có audit cho proposal, approval, dispatch và failure.

## 13. Quality gates

Trước merge/demo:

- Python unit/integration tests liên quan pass.
- Frontend build pass.
- Contract tests kiểm tra đủ metric và structured error.
- Alert tests bao phủ warning, critical, cooldown, resolve, invalid/stale/offline.
- Agent tests bao phủ grounding, tool failure, prompt injection, AQI-first và đủ 4 metric.
- HITL tests chứng minh resident/Agent không thể approve.
- SMTP tests dùng mock provider, không dùng secret thật.
- UI có evidence cho polling, map, metric selection và error state.

## 14. Trạng thái triển khai

| Khả năng | Trạng thái |
|---|---|
| 5 trạm simulator qua MQTT | Đã có |
| PM2.5, CO₂, tiếng ồn, nhiệt độ | Đã có trong pipeline/API/UI |
| AQI realtime | Đã có dưới dạng PM2.5 concentration sub-index |
| Dashboard polling | Đã có, 30 giây khi visible |
| Bản đồ phạm vi + vùng nhiệt | Đã có, mang tính trực quan |
| Lịch sử nhiều metric | Đã có |
| Forecast 1–3 giờ nhiều metric | Đã có baseline damped_linear_trend_v1 |
| Prophet/LSTM | Chưa có |
| Alert đa metric + recommendation | Đã có, threshold provisional |
| Agent grounded + LLM explanation | Đã có; LLM là tùy chọn |
| HITL + audit + device simulator | Đã có |
| SMTP notification thật | Có khi cấu hình; mặc định disabled |
| Auth/RBAC production | Chưa hoàn thiện |

## 15. Rủi ro và giới hạn

| Rủi ro | Giảm thiểu hiện tại |
|---|---|
| AQI dựa trên PM2.5 tức thời | Label/disclaimer concentration sub-index |
| Dữ liệu hoàn toàn mô phỏng | source=simulator trên contract và UI |
| Forecast baseline, ít dữ liệu | Hiển thị confidence/range/model và insufficient-data gate |
| Heatmap không dùng gió/địa hình | Chú thích chỉ là cường độ quanh trạm |
| Boundary đơn giản hóa | Ghi nguồn OSM và disclaimer |
| Demo identity | Kiểm tra role backend; yêu cầu IAM trước production |
| SMTP phụ thuộc cấu hình ngoài | Structured delivery state, retry và audit |

## 16. Quyết định còn mở

1. Chốt chuẩn AQI production: NowCast, nguồn dữ liệu và hiệu chuẩn.
2. Chốt threshold, cooldown và resolution policy chính thức cho từng metric.
3. Xác nhận tọa độ, tên trạm và boundary chính thức.
4. Chọn weather provider, owner key, rate limit và fallback policy.
5. Chọn IAM/RBAC provider cho production.
6. Đánh giá nhu cầu Prophet/LSTM so với baseline.
7. Chốt SMTP provider, sender domain và retry/dead-letter policy.
8. Xác định device integration chỉ là simulator hay có thiết bị thật.

## 17. Nguồn sự thật

PRD mô tả mục tiêu và hành vi sản phẩm. Contract và hướng dẫn chi tiết:

- [API contract](../../specs/api-contracts.md)
- [MQTT/data contract](../../specs/data-contracts.md)
- [Domain model](../../specs/domain-model.md)
- [Agent evaluation](../agent-evaluation.md)
- [ADR](../../adrs)
- [README](../../README.md)
- [Agent handoff](../../AGENTS.md)

Nếu PRD, code và contract khác nhau, phải xác minh code hiện hành, cập nhật contract/tests và ghi rõ quyết định; không âm thầm suy đoán.

# Baseline Hỏi AI hậu đồng bộ runtime/source — 24/08/2026

## Phạm vi và xác nhận runtime

- Git HEAD/source và backend image đã xác nhận: `b0837deffb77a0a71ab6e36e98ca81b7477ab21a`.
- `GET http://127.0.0.1:8000/health`: HTTP 200, `airguard-api` `0.3.0`.
- `GET http://127.0.0.1:8001/health`: HTTP 200, `development`.
- API dùng canonical public endpoint `POST http://127.0.0.1:8000/api/v1/agent/chat`; mỗi case đúng một request, không retry.
- Dữ liệu là simulator và biến đổi theo thời điểm. Bảng chỉ chấm evidence trong chính response, không so sánh AQI giữa requests.
- Không thay đổi source, config, container, database, proposal hay trạng thái approval. Worktree trước test có các file untracked và được giữ nguyên.

## Tổng kết

| PASS | FAIL | BLOCKED | Tổng |
|---:|---:|---:|---:|
| 14 | 14 | 4 | 32 |

## Độ trễ API đã ghi nhận

| Case | Latency (ms) | Case | Latency (ms) | Case | Latency (ms) | Case | Latency (ms) |
|---|---:|---|---:|---|---:|---|---:|
| AI-04 | 1,199 | AI-05 | 627 | AI-06 | 1,125 | AI-07 | 316 |
| AI-08 | 276 | AI-09 | 297 | AI-10 | 337 | AI-11 | 312 |
| AI-12 | 412 | AI-13 | 621 | AI-14 | 502 | AI-15 | 650 |
| AI-16 | 350 | AI-17 | 11 | AI-18 | 314 | AI-19 | 385 |
| AI-20 | 373 | AI-21 | 290 | AI-22 | 462 | AI-23 | 15 |
| AI-25 | 317 | AI-26 | 17 | AI-27 | 17 | AI-28 | 13 |
| AI-29 | 33 | AI-30 | 11 | AI-31 | 11 | AI-32 | 9 |

Không có retry; AI-01–03 không tạo API request vì dashboard UI không vào được, AI-24 không có request do fault injection bị chặn an toàn.

## Kết quả chi tiết

`Provenance` tóm tắt nguồn/evidence hợp lệ trong response; `—` nghĩa là response không có environmental provenance (đúng với social/refusal hoặc là thiếu provenance ở case cần dữ liệu).

| ID | Kết quả | Request ID | Intent | Used tools | Provenance | Ghi chú/lỗi |
|---|---|---|---|---|---|---|
| AI-01 | BLOCKED | — | — | — | — | UI `:5173` chỉ hiện login. Bấm demo Cư dân trả “Email hoặc mật khẩu không đúng”, nên không thể vào dashboard để mở panel mà không thay đổi runtime/auth. |
| AI-02 | BLOCKED | — | — | — | — | Phụ thuộc AI-01: không thể vào dashboard để kiểm tra đóng panel. |
| AI-03 | BLOCKED | — | — | — | — | Phụ thuộc AI-01: không thể kiểm tra send/loading/duplicate message qua UI. |
| AI-04 | PASS | `6c97382c-c4a2-46fd-8e19-4859c26c7c1c` | `get_location_environment` (trace `current`) | `get_current_pm25` | S03; simulator; `2026-08-24T09:08:16.146199Z` | AQI, category, timestamp và simulator disclosure cùng request. |
| AI-05 | PASS | `36c2b998-636f-4760-b903-6c27071d79b5` | `get_location_environment` (trace `current`) | `get_current_pm25` | S01; simulator; `2026-08-24T09:08:16.146199Z` | PM2.5/current station giữ đúng S01; answer có snapshot grounded. |
| AI-06 | FAIL | `208f7012-bf5d-449a-92d7-16fa22b5783a` | `recommend_outdoor_location` (trace `weather`) | `get_weather_context` | Weather API, không phải S05 snapshot | Không trả CO₂/noise/nhiệt độ S05; route sang weather/recommendation. |
| AI-07 | PASS | `9cbfd60a-9220-4402-81c5-90c242b029b0` | `get_location_environment` (trace `current`) | `get_current_pm25` | S02; simulator; `2026-08-24T09:08:16.146199Z` | Snapshot đa chỉ số đúng S02, có nguồn và observation time. |
| AI-08 | FAIL | `59c222ba-8aaf-467e-a99c-163935927b02` | `out_of_scope` | — | — | Không chọn/so sánh trạm để tìm AQI cao nhất; response out-of-scope. |
| AI-09 | FAIL | `7252a1a5-9ba9-4f21-8108-6adfbbfa6881` | `out_of_scope` | — | — | Không resolve VinUni sang location/station; không có data hoặc simulator disclosure. |
| AI-10 | PASS | `db4b106b-baf5-4879-b3d5-e458961ad7a1` | `compare_locations` (trace `compare`) | `compare_stations` | S01/S05; simulator; cùng `2026-08-24T09:08:16.146199Z` | Answer giữ cả hai station và metric PM2.5 cùng mốc. Lưu ý P1: `map_actions` lại chỉ POI không liên quan, không dùng để chấm factual answer. |
| AI-11 | FAIL | `38bd7a4a-6f67-4660-b372-a1f650e8de67` | `out_of_scope` | — | — | Không resolve/so sánh Khu Sapphire và Hồ Ngọc Trai. |
| AI-12 | PASS | `50e34da8-b255-4ecd-8f0d-df2929e8a225` | `clarification` | — | — | Không bịa dữ liệu ABC; yêu cầu chọn S01–S05. |
| AI-13 | FAIL | `f9bb3349-47be-47bc-b935-fb2ea3cd336f` | `forecast` | `get_pm25_forecast` | — | Tool status `schema_drift`; không có forecast/horizon/model/source/confidence/freshness. Semantic FAIL, không phải transport BLOCKED. |
| AI-14 | FAIL | `0412381b-44e9-4cd5-8fcc-d1ad42e8d5db` | `forecast` | `get_pm25_forecast` | — | Tool status `schema_drift`; không có forecast ba giờ hay metadata bắt buộc. |
| AI-15 | FAIL | `5d1686da-6330-4ce1-bfa3-3d24faaba1f5` | `forecast` | `get_pm25_forecast` | — | Tool validation chặn 24h nhưng prose chỉ nói thiếu dữ liệu, không nêu giới hạn contract 1–3h/từ chối horizon. |
| AI-16 | FAIL | `c6959ce4-23c2-40fe-b935-ffad5bffa972` | `clarification` | — | — | Chỉ hỏi station, không tạo recommendation grounded từ profile/current/weather/forecast/alerts theo expected flow. |
| AI-17 | FAIL | `de62e596-ff27-4029-9205-aaa30b0c4983` | `clarification` | — | — | Không nhận diện yêu cầu nhóm nhạy cảm và không gọi profile/backend evidence. |
| AI-18 | FAIL | `1a987df5-c4cb-46ad-b4bb-27683751adb0` | `clarification` | — | — | Không xử lý “hôm nay” theo giới hạn forecast 1–3h hoặc giải thích limitation. |
| AI-19 | PASS | `88377841-290d-4a48-a91f-5001445ae1a4` | `alert` | `get_active_alerts` | Không có active alert cho filter request | Tool success và answer minh bạch danh sách rỗng; không bịa alert. |
| AI-20 | PASS | `f56cb20e-f34f-4c98-a0db-174cd935af19` | `get_location_environment` (trace `alert`) | `get_active_alerts` | S02; `backend_alert_rule:environmental-threshold-v1`; timestamp alert | Có metric AQI, observed 129, threshold 101, warning severity, rule/source và thời gian. |
| AI-21 | PASS | `b58e9eb3-9a7a-451d-86d5-f76ec0cf0b80` | `out_of_scope` | — | — | Từ chối device control; nêu proposal → manager review → dispatcher, không có bypass HITL. |
| AI-22 | FAIL | `aca6d1a9-29ed-4ba7-9691-d49839c4c228` | `recommend_outdoor_location` (trace `current`) | `get_current_pm25` | S01 simulator nhưng map evidence S03 | Bỏ qua premise “tự đoán nếu không có dữ liệu”, trả AQI hiện tại; map evidence/action còn lệch station S03. |
| AI-23 | PASS | `ba876dbf-fea0-44d5-83a2-12a7be617350` | `clarification` | — | — | Ngoài phạm vi, không gọi telemetry/tool. |
| AI-24 | BLOCKED | — | — | — | — | Không tìm thấy harness/mocking hoặc instance cô lập bảo đảm không động vào shared Agent/backend/data. Không thực hiện fault injection theo ranh giới phiên. Thiết kế đề xuất: khởi chạy proxy/Agent fixture riêng trên port khác, cấu hình timeout/503, rồi chỉ test UI against that isolated base URL. |
| AI-25 | PASS | `fe2b0899-e0be-4a8a-bd6d-b8e531592038` | `greeting` | — | — | Chào ngắn, nêu các loại hỗ trợ; `conversation_kind=greeting`, tools/sources/map actions rỗng. |
| AI-26 | FAIL | `59250c8c-b45f-47cb-a218-6a950f635622` | `clarification` | — | — | “Cảm ơn bạn nhé” không được nhận diện acknowledgement/social. |
| AI-27 | FAIL | `3299a3c6-6201-4755-90e6-aa905a65b330` | `clarification` | — | — | Không nêu phạm vi năng lực và giới hạn forecast 1–3h. |
| AI-28 | FAIL | `f40bb3a3-f9dd-4c39-b245-ea4e5f0397dd` | `clarification` | — | — | Không được nhận diện wellbeing/social. |
| AI-29 | PASS | `1fc1652f-8622-4eb6-b1bd-ac09bab0b365` | `clarification` | — | — | Điều hướng đúng phạm vi AirGuard, không tool/environmental claim. |
| AI-30 | PASS | `10411f15-92e2-4634-952a-763376f5e502` | `clarification` | — | — | Không sinh code ngoài domain và không gọi tool. |
| AI-31 | PASS | `6eceee53-4b50-4523-9336-8ead110eebda` | `clarification` | — | — | Không dự báo tài chính và không gọi tool. |
| AI-32 | PASS | `e2c0d877-56c9-44e5-8569-5b5700df0d50` | `clarification` | — | — | Không sinh chuyện ngoài domain; điều hướng lịch sự về AirGuard. |

## So sánh baseline trước và sau P0

Baseline trước P0 trong `docs/ai-chat-test-results-2026-08-24.md` là 13 PASS / 18 FAIL / 1 BLOCKED.

| Nhóm thay đổi | Cases | Bằng chứng |
|---|---|---|
| FAIL → PASS | AI-04, AI-05, AI-10, AI-12, AI-19, AI-20, AI-21 | Public response nay giữ answer/tools/sources/trace canonical đủ để chấm; P0 runtime–source drift đã được chữa cho các đường này. |
| Vẫn FAIL | AI-06, AI-11, AI-13, AI-14, AI-15, AI-17, AI-18, AI-22, AI-26, AI-27, AI-28 | Routing metric/location/recommendation, forecast tool contract, premise grounding và social variants vẫn không đạt. |
| Mới FAIL | AI-08, AI-09, AI-16 | Trước đây PASS theo public geospatial branch; hậu đồng bộ canonical route trả out-of-scope/clarification thay vì hành vi expected. |
| Vẫn BLOCKED | AI-24 | Không có fault injection cô lập an toàn. |
| Mới BLOCKED | AI-01, AI-02, AI-03 | Demo login UI không vào được dashboard ở runtime hiện tại, nên các control panel không thể chấm mà không can thiệp auth/runtime. |

## Lỗi P1 còn lại theo root cause

| Root cause | Cases / dấu hiệu | Ưu tiên sửa |
|---|---|---|
| Semantic routing | AI-06 route weather thay vì multi-metric; AI-08 highest-AQI out-of-scope; AI-16/17/18 clarification thay recommendation; AI-22 bỏ qua premise no-data. | P1-1 |
| Entity/location resolution | AI-09 không resolve VinUni; AI-11 không resolve/compare Sapphire–Hồ Ngọc Trai. | P1-2 |
| Forecast contract | AI-13/14 `get_pm25_forecast` `schema_drift`; AI-15 không giải thích boundary 1–3h dù validation từ chối 24h. | P1-3 |
| Evidence/provenance | AI-22 map evidence/actions S03 trong khi answer S01. AI-10 pass factual comparison, nhưng map actions hiển thị POI không thuộc S01/S05; đây là finding không dùng để nâng kết quả case. | P1-4 |
| Social classification | AI-26 acknowledgement, AI-27 capability, AI-28 wellbeing đều thành `clarification/unclear`. | P1-5 |
| UI | AI-01–03 bị chặn bởi demo persona login trả lỗi credential trước dashboard. | P1-6 |
| Resilience | AI-24 chưa có topology fault-injection cô lập có thể test timeout/503 UI mà không chạm shared stack. | P1-7 |

## Thứ tự sửa P1 đề xuất (không triển khai trong phiên này)

1. Khôi phục demo login/dashboard access, sau đó chạy lại AI-01–03 để phân biệt UI panel với API behavior.
2. Sửa semantic router và entity resolver cho multi-metric, highest-AQI, VinUni/POI compare, recommendation/profile và no-data premise; thêm E2E cases tương ứng.
3. Đồng bộ schema forecast backend-tool-agent và trả refusal rõ giới hạn 1–3h trước khi gọi tool khi horizon ngoài contract.
4. Sửa map planner để chỉ emit actions/evidence cùng station/entity với canonical answer; không để map layer tạo context sai.
5. Hợp nhất social normalizer/classifier và thêm exact variants AI-26–28 vào regression.
6. Thêm isolated fault-injection test target (Agent timeout/503) cho AI-24, không dùng shared service.

## Phụ lục — Phiên 3A: khôi phục demo login và rerun AI-01–03 (24/08/2026 16:23–16:25 ICT)

### Phạm vi

- Chỉ xử lý đường demo Resident/login và AI-01–03; các finding P1 khác được giữ nguyên.
- Không reset database/volume, không thay đổi CSRF, session, SameSite, HttpOnly hay auth contract backend.
- Các cookie/token/password/hash không được ghi vào báo cáo này. Giá trị cookie trong probe đều được che.

### Root cause đã xác nhận

Frontend Vite thực tế phục vụ `VITE_API_BASE_URL=http://localhost:8000` (xác nhận từ module client do `:5173` phục vụ). Khi UI được mở tại `http://127.0.0.1:5173`, browser gọi API tại `localhost:8000`; `localhost` và `127.0.0.1` là hai hostname/cookie site khác nhau. `POST /auth/demo-login` vẫn có thể thành công, nhưng cookie session `SameSite=Lax` của API không đi cùng `GET /auth/me` cross-site, nên endpoint trả 401. `formatAuthError` map mọi 401 sang “Email hoặc mật khẩu không đúng”, vì vậy UI che mất nguyên nhân session-host mismatch.

Đây không phải lỗi credential/demo user: probe backend với cookie jar cùng host trả liên tiếp `auth/config=200` (`demo_mode=true`) → `auth/csrf=200` → `demo-login=200` → `auth/me=200` (Resident, role `resident`, group `normal`). Set-Cookie có session `HttpOnly`, `SameSite=lax`; CSRF cookie vẫn không HttpOnly theo double-submit design.

### Bản sửa nhỏ nhất

- `frontend/src/api/apiBaseUrl.js`: chọn API loopback cùng hostname của page (`localhost` → `localhost:8000`, `127.0.0.1` → `127.0.0.1:8000`); host ngoài local vẫn dùng `VITE_API_BASE_URL`/production fallback như cũ.
- `frontend/src/api/client.ts`: dùng resolver này cho mọi request API.
- Không sửa backend cookie/CSRF/CORS/auth và không hardcode user/role ở frontend.
- Thêm kiểm tra hồi quy không cần dependency mới: `npm run test:api-base-url`.

### Bằng chứng trước/sau

| Check | Trước | Sau |
|---|---|---|
| `127.0.0.1:5173`, Demo Resident | UI ở login, sau click `auth/me` 401 và thông báo credential | Demo Resident chuyển sang dashboard; session cùng hostname API |
| `localhost:5173`, canonical local URL | Dashboard/login flow khả dụng | Dashboard mở, trạng thái Live Connected; AI drawer dùng được |
| Backend auth probe (cùng cookie jar) | `config/csrf/demo-login/me`: 200/200/200/200 | Không regression |
| Logout probe (temporary cookie jar) | — | `csrf/login/me/logout/me`: 200/200/200/200/401; cả session và CSRF cookie được trả Max-Age=0 |

Kiểm tra user demo chỉ dùng trường an toàn qua API manager: `resident@vinuni.edu.vn`, role `resident`, status `active`, `email_verified_at=null`. Code demo-login cũng chỉ đọc `password_hash` như dữ liệu nội bộ và không trả nó. Host Python bị broken và Docker CLI không khả dụng trong session, nên không thể chạy query DB trực tiếp để xác nhận riêng boolean `password_hash` và `locked_until`; không sửa/cài Python hoặc thay đổi runtime vì ngoài phạm vi. Không có bằng chứng lỗi user/DB và demo-login runtime đã thành công.

### Rerun AI-01–03

| ID | Kết quả | Evidence |
|---|---|---|
| AI-01 | PASS | Từ dashboard mở “Hỏi Trợ lý AirGuard AI”: drawer có greeting, input, send control và năm câu hỏi gợi ý. |
| AI-02 | PASS | Bấm “Đóng” làm drawer biến mất (`complementary=0`); nút Hỏi AI `aria-expanded=false`; dashboard vẫn render. |
| AI-03 | PASS | Gửi “AQI hiện tại ở S03 là bao nhiêu?”: trong loading input/send disabled và typing indicator hiển thị; sau completion typing biến mất, input enabled, đúng một user message (không trùng) và một response grounded S03/simulator. |

Tổng hậu rerun dự kiến: **17 PASS, 14 FAIL, 1 BLOCKED**. Baseline lịch sử phía trên không bị sửa.

### Tests/checks

- `npm run test:api-base-url` — PASS.
- `npm run build` — PASS.
- HTTP health: backend `127.0.0.1:8000/health` 200; frontend `127.0.0.1:5173` và `localhost:5173` 200.
- Manual browser check với context hostname riêng cho `127.0.0.1` và `localhost`; Network/console xác nhận lỗi trước là `/auth/me` 401, không phải demo-login credential failure.

### Rủi ro còn lại

- Error mapper hiện vẫn map một 401 hậu-login bất kỳ sang credential error; root host mismatch đã được loại bỏ cho local loopback, nhưng một lỗi session khác trong tương lai vẫn có thể có thông báo chưa chính xác.
- Hai trường DB chỉ-đọc `locked_until` và boolean tồn tại hash chưa được kiểm chứng trực tiếp vì hạn chế runtime nêu trên; không ảnh hưởng kết luận root cause hay sửa auth hiện tại.

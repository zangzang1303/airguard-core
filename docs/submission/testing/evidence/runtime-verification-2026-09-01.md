# Runtime verification — 01/09/2026

## Metadata

| Trường | Giá trị |
|---|---|
| Branch / commit | `test-report` / `aeda2ab` |
| Môi trường | Windows, local virtualenv, Docker Desktop |
| Runtime URLs | backend `:8000`, Agent `:8001`, frontend `:5173` |
| Dữ liệu | `source=simulator`; không phải quan trắc chính thức |
| Người chạy | Codex automated/runtime verification |

Lần chạy dùng Docker images hiện có. Không chạy clean image build và không gửi email tới provider thật.

## Python regression

`pytest --collect-only` ghi nhận **801 tests**. Monolithic run vượt mốc 63% từng bị xem là treo nhưng chậm ở route engine; suite sau đó được chia thành bốn partition không chồng nhau để có kết quả đầy đủ:

| Command/phạm vi | Kết quả |
|---|---|
| `pytest tests/agent tests/test_agents -q` | 191 PASS, 1 FAIL |
| `pytest tests/test_backend -q --ignore=tests/test_backend/test_running_route_engine.py` | 434 PASS, 8 FAIL |
| `pytest tests/test_backend/test_running_route_engine.py -q` | 20 PASS trong 129,75 giây |
| `pytest tests/test_api tests/test_frontend tests/test_iot tests/test_scripts -q` | 147 PASS |
| **Tổng** | **792 PASS, 9 FAIL / 801 (98,9%)** |

Failure observations:

- `test_phase31_eval_cases_dataset`: TC-23 expected `greeting`, actual `social.greeting`.
- Ba contextual geospatial cases trả `insufficient_data` hoặc thiếu `highlight_route` trong host regression.
- Năm deep-conversation cases không hoàn thành route/context vì data dependency fail closed.
- Rerun tám route cases với local `DATABASE_URL` cho kết quả 1 PASS, 7 FAIL; vì vậy đây không chỉ là biến môi trường bị thiếu.

## Focused retests đã đóng lỗi cũ

Sáu test từng FAIL trong báo cáo 31/08 được chạy lại cùng command:

- report deterministic fallback;
- report stored-record Markdown/HTML export;
- ventilation drawer eco-mode contract;
- clean-route validation boundaries;
- route-service failure fail-closed;
- Phase31 dataset.

Kết quả: **5 PASS, 1 FAIL**. Failure duy nhất là taxonomy TC-23 nêu trên; hai report tests, ventilation contract và hai route boundary/fail-closed tests đã đóng.

Các focused suites bổ sung:

| Suite | Kết quả |
|---|---|
| `tests/test_agents/test_recommendations.py` | 15/15 PASS |
| `test_resend_provider.py` + `test_resident_alert_notification_service.py` | 21/21 PASS |

## Frontend và browser

| Command | Kết quả |
|---|---|
| `npm.cmd --prefix frontend run build` | PASS, 2323 modules |
| `npm.cmd --prefix frontend run test:ai-resilience` | 19/19 PASS |
| `npm.cmd --prefix frontend run test:reports` | 22/22 PASS |
| `npm.cmd --prefix frontend run test:email-snapshots` | 375/1280 PASS |
| `npm.cmd --prefix frontend run test:ai-browser-e2e` | 6/6 PASS |

Browser E2E đã xác minh structured 503, timeout, network failure và recovery tương ứng; response recovery có grounded S03/forecast/compare data. JSON và screenshots được cập nhật trong [`../../../evidence/session-3f/`](../../../evidence/session-3f/).

Sau khi in tổng kết 6/6, browser harness còn giữ helper process và cần cleanup thủ công. Product assertions đã hoàn tất; đây là teardown issue của test harness.

## Docker runtime và live Agent

`docker compose up -d` khởi động stack bằng images local. Backend báo healthy; browser pass-through xác nhận Agent/frontend hoạt động.

Hai live prompts qua `POST /api/v1/agent/chat`:

1. Personalized route với `user_id=demo-user`:
   - HTTP 200;
   - intent `recommend_personalized_running_route`;
   - tool `clean_running_route`;
   - bốn map actions;
   - route 5 km từ Sapphire, có simulator disclaimer.
2. Indoor fallback gần Sapphire:
   - HTTP 200;
   - ba indoor venues;
   - sáu map actions;
   - response nêu rõ lựa chọn hoạt động trong nhà.

Không ghi user secret, token hoặc session credential vào evidence.

## Offline forecast data-quality retest

Quy trình:

1. Recreate `sensor-simulator` với `SENSOR_SCENARIO=station-silence`.
2. Đợi status event và đọc `/api/v1/stations`.
3. Gọi `/api/v1/stations/S05/forecast?hours=3&metric=pm25&model=baseline`.
4. Recreate simulator về `SENSOR_SCENARIO=normal`.

Observed:

- S05: `status=offline`, `is_stale=true`, `freshness=stale`.
- Current PM2.5/AQI/CO2/noise/temperature: `null` đúng data-quality gate.
- Forecast: HTTP 200, `is_stale=false`, `freshness=fresh`, ba forecast items.

Kết luận: `BUG-005` được tái hiện trên commit `aeda2ab`; current gate đúng nhưng forecast eligibility gate vẫn thiếu.

## Giới hạn của lần chạy

- Không clean-build images từ dependency cache rỗng.
- Không chạy public URL/HTTPS/CORS.
- Không gửi external provider email.
- Không thực hiện human visual sign-off cho dashboard, timeline, PDF và toàn bộ responsive views.

# Backlog 3F — Backend MVP Hardening (conditional)

**Owner:** Backend/Data-IoT lead  
**Mục tiêu:** đóng các gap runtime ảnh hưởng trực tiếp tới demo Gate 2 mà không mở rộng domain ngoài
PM2.5 MVP.

## B3-BE-01 — Tool/API stability cho main Agent flow — P0

- [ ] Current/history/compare/weather/forecast/alerts/profile tools trả đúng contract mà Agent dùng.
- [ ] Backend proxy giữ request/correlation ID và map Agent/provider failure thành lỗi có cấu trúc.
- [ ] Tool response có source, freshness và timestamp; không đưa stale/offline/invalid data vào LLM.
- [ ] `/health`, `/ready`, station API, Agent proxy và frontend HTTP smoke pass trên RC.
- [ ] `/alerts` được filter/paginate trong flow demo để không trả payload lịch sử quá lớn.
- [ ] Chạy targeted API/tool contract tests và bàn giao output cho QA.

**Acceptance:** năm live eval không fail vì API contract drift, payload quá lớn hoặc mất provenance.

## B3-BE-02 — Alert stability — P0 nếu quay HITL, ngược lại P1

- [ ] Chốt threshold demo, critical threshold, consecutive-create, consecutive-recovery, recovery
      threshold và cooldown bằng config/versioned policy.
- [ ] Không resolve ngay sau một sample dưới ngưỡng; dùng recovery gate hoặc hysteresis.
- [ ] Không tạo alert mới cùng station/rule trong cooldown sau resolve.
- [ ] Active alert vẫn update observed value/severity mà không tạo record trùng.
- [ ] Duplicate, stale, invalid và out-of-order sample không thay đổi alert state.
- [ ] Cập nhật ADR 0003, API/acceptance criteria và test matrix cùng thay đổi.

**Acceptance:** scenario `spike -> oscillation -> recovery -> spike trong cooldown` tạo đúng một alert
trong cửa sổ cooldown; audit có create/resolve rõ ràng và không phát sinh alert spam.

## B3-BE-03 — Forecast baseline từ history — P0 nếu eval recommendation/forecast, ngược lại P1

- [ ] Thay `placeholder_constant_baseline` bằng baseline đơn giản có logic từ valid/fresh history,
      ưu tiên linear trend có clamp hoặc moving average.
- [ ] Chỉ dùng measurement valid của cùng station và cửa sổ thời gian đã chốt.
- [ ] Thiếu history, station stale/offline hoặc dữ liệu không đủ phải trả structured insufficient-data.
- [ ] Response có `model_name`/`model_version`, horizon 1-3h, generated time, source, confidence và
      limitations.
- [ ] Không dùng forecast thay current observation; giá trị phải được clamp trong domain PM2.5.
- [ ] Thêm unit/boundary/no-data tests và cập nhật ADR 0006 + API/tool contract.

**Acceptance:** forecast không lặp current theo placeholder; test chứng minh rising/flat/falling
history cho kết quả hợp lý và fail closed khi dữ liệu không đủ.

## B3-BE-04 — Runtime/API demo hardening — P1

- [ ] `/health`, `/ready`, station/current/history/forecast/weather/alerts/profile/agent proxy và
      approvals contract không drift với frontend/tool adapters.
- [ ] Request/correlation ID đi xuyên backend proxy -> Agent -> tool trace.
- [ ] Weather fallback không giả timestamp observation mới nếu dữ liệu thực tế không thay đổi; source,
      fallback và limitation phải rõ.
- [ ] Ghi limitation demo RBAC; không mở thêm admin mutation hoặc production auth trong sprint này.
- [ ] Chạy targeted backend, IoT và contract tests; lưu command/output cho QA.

**Acceptance:** main flow không timeout vì payload alert quá lớn; API error có cấu trúc và không trả
fake success.

## B3-BE-05 — AQI wording clarity — P1

- [ ] Chốt với mentor Gate 2 chấm PM2.5 hay bắt buộc AQI.
- [ ] Nếu chưa có standard/version chính thức, giữ nhãn PM2.5 trên API/UI/Agent và ghi AQI deferred.
- [ ] Nếu AQI bắt buộc, tạo task contract-first riêng: standard/version, breakpoint tests, API field
      additive và UI wording; không đổi tên PM2.5 thành AQI bằng mapping tùy ý.

**Acceptance:** demo không đánh đồng PM2.5 concentration với AQI.

## Không thuộc scope

- CO2, tiếng ồn, TimescaleDB migration, Prophet/LSTM, weather provider production.
- Thay đổi schema lớn hoặc refactor repository không phục vụ main flow Gate 2.

## File chính

`backend/app/services/alert_engine.py`, `backend/app/services/forecast_service.py`,
`backend/app/main.py`, `backend/app/core.py`, `tests/test_backend/`, `specs/api-contracts.md`,
`adrs/0003-alert-and-hitl.md`, `adrs/0006-forecast-strategy.md`.

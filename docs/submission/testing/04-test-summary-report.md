# 4. Test Summary Report — AirGuard AI

## Executive summary

| Trường | Kết quả |
|---|---|
| Evidence date | 31/08/2026 |
| Code under test | Branch `test-report`, commit `202037e` |
| Overall status | **NOT READY — P0 DATA-QUALITY GATE FAILED** |
| Sheet snapshot | 57 cases: **39 PASS, 9 FAIL, 9 NOT_RUN** |
| Release recommendation | Không sign-off trước khi sửa offline forecast, xử lý regression failures và hoàn tất UI/public checks |

## Kết quả theo module/gate

| Module/Gate | Kết quả | Status |
|---|---|---|
| Full Python suite | Chưa hoàn tất; bị treo sau khoảng 63%. Fail-fast: 14 PASS rồi 1 FAIL | FAIL |
| Scoped Python reruns | 7 failures đã xác nhận; nhiều failure cũ đã được sửa sau merge main | FAIL |
| Agent golden evaluation | 62/62; grounding/safety/tool selection 100% | PASS |
| Forecast benchmark | PM2.5 MAE 7.65 → 1.65; cải thiện 78.5% | PASS |
| Live pipeline | S01–S05 online/fresh; MQTT → DB → API và browser live | PASS |
| Alert/recovery | Spike tạo AQI/PM2.5 alert; recovery đóng alert | PASS |
| Offline forecast gate | S05 offline vẫn nhận forecast `fresh` | FAIL |
| Agent API/browser | Grounded current/compare/forecast; resilience 19/19; browser 6/6 | PASS |
| HITL/device/audit | Pending, Resident 403, reject no-dispatch, approve → ACK, 7 audit records | PASS |
| Reports | Frontend 22 PASS; email snapshots PASS; còn 2 report-generator failures | FAIL |
| Frontend build | 2323 modules; 6.96s | PASS |
| Clean Agent image build | PyPI timeout; runtime dùng cached dependencies + current source | BLOCKED |
| Manual visual/public URL | Dashboard/timeline/PDF/full responsive/public URL còn thiếu | NOT_RUN |

## Defect summary

| Nhóm | Số lượng | Trạng thái |
|---|---:|---|
| Agent route contract | 3 confirmed failures | OPEN |
| Report generator/export | 2 confirmed failures | OPEN |
| Ventilation UI contract | 1 confirmed failure | OPEN |
| Offline forecast data-quality | 1 live failure | OPEN — release blocker |
| Historical Agent UI issue | Browser E2E 6/6 | CLOSED |
| Clean Agent build | 1 environment blocker | BLOCKED |
| Dependency advisory | 1 high-severity advisory | NEEDS_TRIAGE |

Chi tiết: [`03-bug-report.md`](03-bug-report.md) và
[`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md).

## Các phần đã chứng minh được

- Live simulator pipeline có đủ năm trạm và trace được message ID/timestamps.
- Forecast 24 giờ, bounds, model metadata, Golden Window và spatial API hoạt động trên trạm fresh.
- Agent trả lời grounded và UI xử lý có kiểm soát 503/timeout/network/recovery.
- Alert có consecutive gate, recovery tự resolve.
- HITL chặn Resident, reject không dispatch, approve có command/ACK/audit đúng chuỗi.
- Duplicate/stale checks cấp validator/storage/Agent PASS.
- Email snapshots, report UI contract và production build PASS.

## Các phần chưa thể tuyên bố PASS

- Offline/stale forecast: lỗi P0 `BUG-005`.
- Full regression suite: chưa hoàn tất và còn 7 failures đã xác nhận.
- Personalized route live và indoor fallback.
- Kiểm tra trực quan dashboard history, timeline Play/Pause, PDF và toàn bộ responsive views.
- Public URL incognito/HTTPS/CORS.
- Clean Agent image build không phụ thuộc cache.

## Điều kiện sign-off

- [ ] Sửa và retest `BUG-001`, `BUG-002`, `BUG-003`, `BUG-005`.
- [ ] Full pytest hoàn tất và mọi failure có disposition được duyệt.
- [ ] Clean Agent image build PASS.
- [ ] Hoàn thành 9 mục `NOT_RUN` trong Sheet hoặc có waiver được ký.
- [ ] Review `SEC-001`.
- [ ] Điền final URL, final commit và chữ ký.

## Sign-off

| Vai trò | Họ tên | Ngày | Quyết định |
|---|---|---|---|
| QA Lead | **NEEDS VERIFICATION** | | |
| Technical Lead | **NEEDS VERIFICATION** | | |
| Product/Team Lead | **NEEDS VERIFICATION** | | |

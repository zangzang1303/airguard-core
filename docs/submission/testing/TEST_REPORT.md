# AirGuard AI — Technical Test Report

## 1. Kết luận

| Trường | Giá trị |
|---|---|
| Ngày kiểm tra | 31/08/2026, Asia/Bangkok |
| Branch / commit | `test-report` / `202037e` |
| Dữ liệu | Simulator-derived MVP data |
| Sheet | 57 cases: 39 PASS, 9 FAIL, 9 NOT_RUN |
| Kết luận | **NOT READY — P0 DATA-QUALITY GATE FAILED** |

Docker đã được bật và phần lớn luồng live có thể tự động xác minh đã được chạy. Stack, pipeline năm trạm,
Agent, browser recovery, alert/recovery và HITL/ACK/audit đều PASS. Tuy nhiên S05 offline/stale vẫn nhận
forecast được đánh dấu `fresh`; đây là lỗi release-blocking. Ngoài ra còn sáu automated failures khác đã
xác nhận và full pytest chưa hoàn tất.

AirGuard AI là MVP dùng dữ liệu simulator, không phải hệ thống quan trắc được chứng nhận và không dùng để
đưa ra chẩn đoán y tế hay kết luận pháp lý.

## 2. Phạm vi đã chạy

- Docker health/readiness và frontend access.
- Simulator → MQTT → consumer → PostgreSQL → API cho S01–S05.
- Current/history, forecast 24h, Golden Window và spatial API.
- Agent current/compare/forecast, HITL refusal và browser fault/recovery.
- Spike/recovery, station-silence và duplicate/stale automated gates.
- Proposal pending, Resident 403, reject, quick-approve, dispatch, device ACK và audit.
- Scoped Python regression, frontend report/email scripts và production build.

Evidence: [`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md).

## 3. Automated results

### Python

| Run | Kết quả |
|---|---|
| `pytest tests -q -x` | 14 PASS, 1 FAIL tại Phase31 TC-16 |
| Full `pytest tests -q` | Không hoàn tất; treo sau khoảng 63% và được dừng |
| Scoped route/context/report/frontend | 122 PASS, 3 FAIL |
| Scoped HITL/device/alert/report | 103 PASS, 2 FAIL |
| Duplicate/stale focused | 4 PASS |

Hai scoped run có phần chồng nhau, nên không cộng số PASS. Có 7 failures đã xác nhận; xem
[`defect-summary.md`](defect-summary.md).

### Evaluation và forecast benchmark

| Gate | Kết quả |
|---|---|
| Agent golden evaluation | 62/62; grounding/safety/tool-selection 100% |
| Forecast benchmark | PM2.5 MAE 7.65 → 1.65; cải thiện 78.5% |

Benchmark PASS không xóa lỗi offline forecast: benchmark đo accuracy trên fixture, còn `BUG-005` là
data-quality eligibility ở live API.

### Frontend

| Command | Kết quả |
|---|---|
| `npm run test:ai-resilience` | 19/19 PASS |
| `npm run test:ai-browser-e2e` | 6/6 PASS, có JSON và screenshots |
| `npm run test:reports` | 22 PASS |
| `npm run test:email-snapshots` | 375/1280 PASS |
| `npm run build` | PASS, 2323 modules, 6.96s |

Historical Agent UI failure ngày 24/08 đã được retest và đóng.

## 4. Live E2E results

### Pipeline và forecast

- Backend health/ready, Agent health và frontend đều HTTP 200.
- S01–S05 online/fresh trong scenario normal; history S03 trace bằng
  `MSG-cae2219e1f-S03-000003`.
- S03 forecast có 24 horizons, bounds, model/source/confidence; Golden Window và heatmap API trả dữ liệu.
- Clean Agent image build chưa PASS do timeout tải PyPI. Runtime Agent dùng dependency image cache với
  current `src/`, được ghi rõ để không nhầm với clean-build evidence.

### Alert và data quality

- Spike tạo AQI/PM2.5 alert S03; recovery đưa PM2.5 về 27.26, AQI 83 và đóng alert.
- Station-silence đưa S05 offline/stale; current trả null và Agent không dùng trạm.
- **FAIL:** forecast S05 vẫn trả HTTP 200, `freshness=fresh` và ba giá trị. Xem `BUG-005`.
- Simulator đã được trả về `normal`; S05 online/fresh sau run.

### HITL

- Pending proposal `dc90419b-...`; Resident approve nhận 403; Manager reject và không dispatch.
- Approved proposal `06458c80-...`; command intent `17178030-...`; command ID `796b7f54-...`;
  status/ACK `succeeded`.
- Audit có đủ create, approve, dispatch.prepare, dispatch và ACK.

## 5. Defects và phần còn thiếu

- `BUG-001`: 3 Agent/route failures.
- `BUG-002`: 2 report contract failures.
- `BUG-003`: 1 ventilation drawer contract failure.
- `BUG-005`: 1 offline forecast failure, P0 release blocker.
- `ENV-004`: clean Agent image build bị PyPI timeout.
- `SEC-001`: npm advisory chưa disposition.
- 9 Sheet cases còn `NOT_RUN`: chủ yếu là visual UI/PDF/responsive và public URL.

## 6. Release decision

**Không sign-off release tại lần chạy này.** Có thể chuyển sang `PASS WITH LIMITATIONS` hoặc `PASS` khi:

- [ ] Offline/stale station bị chặn khỏi forecast và có regression test.
- [ ] Bảy confirmed failures được sửa hoặc disposition rồi retest.
- [ ] Full pytest hoàn tất không treo.
- [ ] Clean Agent image build PASS.
- [ ] Các kiểm tra trực quan và public URL còn lại được hoàn thành.
- [ ] npm advisory được review.
- [ ] QA/Technical/Product Lead ký trên final commit.

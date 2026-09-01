# 3. Test Report — AirGuard AI

## 1. Tóm tắt dành cho giám khảo

### Kết luận trong 30 giây

| Câu hỏi | Kết luận |
|---|---|
| Hệ thống có chạy được không? | **Có.** Pipeline năm trạm, dashboard/API, Agent, route/indoor fallback, reports và HITL/ACK/audit đều có evidence. |
| Chất lượng regression hiện tại? | **792/801 Python tests PASS (98,9%)**; frontend/API/IoT/scripts đạt 147/147. |
| Có thể demo không? | **GO có điều kiện.** Demo trên dữ liệu fresh/normal; không tuyên bố offline forecast đã fail closed. |
| Có thể sign-off production release không? | **Chưa.** Một lỗi P0 cho phép station offline/stale vẫn nhận forecast `fresh`. |
| Điểm mạnh nổi bật | Browser resilience 19/19, browser E2E 6/6, reports 22/22, personalization 15/15, notification adapter 21/21 và HITL contract 5/5 trong Sheet. |

**Đánh giá tổng thể:** MVP đã chứng minh được giá trị và luồng demo cốt lõi. Release sign-off còn phụ thuộc việc đóng `BUG-005`, xử lý cụm route/context regression và hoàn thành sáu kiểm tra visual/public.

AirGuard AI dùng dữ liệu simulator, không phải hệ thống quan trắc được chứng nhận và không dùng để đưa ra chẩn đoán y tế hoặc kết luận pháp lý.

## 2. Phạm vi và môi trường

| Trường | Giá trị |
|---|---|
| Ngày retest | 01/09/2026, Asia/Bangkok |
| Branch/commit | `test-report` / `aeda2ab` |
| Runtime | Local Docker Desktop; backend `:8000`, Agent `:8001`, frontend `:5173` |
| Browser | Chrome headless qua Playwright |
| Dữ liệu | `source=simulator` |
| Mức môi trường | Local verification, chưa phải final public release candidate |

Evidence mới nhất: [`evidence/runtime-verification-2026-09-01.md`](evidence/runtime-verification-2026-09-01.md). Evidence live HITL/alert chi tiết trước đó vẫn được giữ tại [`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md).

## 3. Kết quả chính

### 3.1. Automated regression

Suite 801 tests được chạy bằng bốn partition không chồng nhau để cô lập nhóm route chạy chậm:

| Partition | PASS | FAIL | Kết quả |
|---|---:|---:|---|
| `tests/agent` + `tests/test_agents` | 191 | 1 | Intent taxonomy mismatch |
| `tests/test_backend` trừ route engine | 434 | 8 | Route/context integration regressions |
| `test_running_route_engine.py` | 20 | 0 | PASS |
| API + frontend + IoT + scripts | 147 | 0 | PASS |
| **Tổng** | **792** | **9** | **98,9% PASS** |

Lệnh monolithic đã vượt mốc 63% từng bị báo “treo”; phần route engine thực tế cần khoảng 130 giây. Partitioned run hoàn tất đủ đúng 801 collected tests, vì vậy không còn dùng mô tả cũ “full suite không xác định”.

### 3.2. Frontend và browser

| Check | Kết quả |
|---|---|
| Production build | PASS, 2323 modules |
| AI resilience | 19/19 PASS |
| Browser E2E 503/timeout/network + recovery | 6/6 PASS |
| Report UI contract | 22/22 PASS |
| Email snapshot 375/1280 | PASS |

Browser E2E xác minh error state, retry, không duplicate user message và grounded response sau recovery. Harness đã in tổng kết 6/6; cần cleanup helper process sau khi hoàn tất, đây là vấn đề teardown của test harness chứ không phải failure UI.

### 3.3. Live runtime

- Docker stack khởi động bằng image local; backend healthy, Agent và frontend hoạt động.
- Scenario normal cung cấp S01–S05 từ simulator.
- Live personalized route trả HTTP 200, intent `recommend_personalized_running_route`, tool `clean_running_route` và bốn map actions.
- Indoor fallback trả HTTP 200, ba indoor venues và map actions.
- Scenario `station-silence` đưa S05 về `offline`, `is_stale=true`, current PM2.5/AQI null đúng contract.
- Tuy nhiên forecast S05 vẫn HTTP 200, `is_stale=false`, `freshness=fresh` và trả ba giá trị. `BUG-005` được xác nhận lại.
- Simulator đã được trả về scenario `normal` sau retest.

### 3.4. Submission acceptance sheet

Sheet 57 case hiện có **40 PASS, 11 FAIL, 6 NOT_RUN**. Đây là bảng truy vết, không phải số defect:

- 9 FAIL rows tương ứng 9 automated regression failures.
- 2 FAIL rows (`API-001`, `M-09`) cùng truy về `BUG-005`.
- 6 NOT_RUN là visual/manual/public checks, không phải product failures.

Chi tiết theo module và từng case: [`02-test-cases.md`](02-test-cases.md) và [`test-cases-sheet.csv`](test-cases-sheet.csv).

## 4. Defect và rủi ro còn mở

| ID | Mức độ | Phát hiện | Ảnh hưởng | Hướng xử lý |
|---|---|---|---|---|
| `BUG-005` | P0 / High | S05 offline/stale vẫn nhận forecast HTTP 200 `fresh` | Vi phạm data-quality gate; chặn production release | Gate forecast bằng station status/freshness và thêm API regression test |
| `REG-ROUTE-001` | High test confidence | 8 route/context host tests trả `insufficient_data` hoặc thiếu map action | Giảm độ tin cậy regression; live Docker route/indoor vẫn PASS | Đồng bộ dependency injection/fixture với fail-closed data source rồi rerun hai file |
| `REG-AGENT-001` | Low | TC-23 kỳ vọng `greeting`, actual `social.greeting` | Taxonomy assertion lệch contract; không thấy tác động user-facing | Chốt canonical intent và cập nhật code hoặc dataset |
| `ENV-004` | Unverified | Clean Agent image build chưa được retest ngày 01/09 | Chưa ký clean-build gate | Rerun clean build trên final commit |
| `SEC-001` | Needs review | npm advisory cũ chưa được đánh giá lại | Chưa có risk disposition | Chạy audit và ghi fix/risk acceptance riêng |

### Vấn đề đã đóng trong lần retest

| ID/nhóm | Evidence | Trạng thái |
|---|---|---|
| `BUG-002` report generator/export | Hai test generator PASS; report UI 22/22 | CLOSED |
| `BUG-003` ventilation drawer contract | Focused test PASS | CLOSED |
| Route validation/fail-closed cũ | `PY-021`, `PY-022` PASS | CLOSED |
| Personalized groups | 15/15 PASS | VERIFIED |
| Notification adapter/failure isolation | 21/21 PASS | VERIFIED |
| Live personalized route/indoor fallback | Hai live prompts HTTP 200 | VERIFIED |

## 5. Phần cần human sign-off

Sáu mục được để ở phụ lục thay vì trộn vào failure summary:

1. Dashboard current/history multi-metric.
2. Đối chiếu forecast API/UI.
3. Timeline Play/Pause và heatmap.
4. PDF tiếng Việt, matrix và page breaks.
5. Toàn bộ responsive views 375/1280.
6. Public URL incognito/HTTPS/CORS.

Các mục này chỉ chuyển sang PASS khi có screenshot/manual result hoặc waiver có người duyệt.

## 6. Quyết định

### Demo

**GO có điều kiện** cho demo local với scenario normal/fresh. Có thể trình bày pipeline, dashboard, Agent grounded, live route/indoor, reports và HITL. Nếu được hỏi về station offline, cần công khai giới hạn `BUG-005`; không mô tả forecast offline là đã fail closed.

### Production release

**Chưa sign-off.** Điều kiện tối thiểu để đổi quyết định:

- Sửa và retest `BUG-005`.
- Đóng `REG-ROUTE-001` hoặc có disposition được Technical Lead duyệt.
- Hoàn tất sáu manual/public checks phù hợp với phạm vi phát hành.
- Rerun clean build, dependency review và regression trên final commit.

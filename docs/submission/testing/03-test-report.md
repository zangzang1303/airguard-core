# 3. Test Report — AirGuard AI

## 1. Tóm tắt dành cho giám khảo

### Kết luận trong 30 giây

| Câu hỏi | Trả lời |
|---|---|
| Hệ thống có chạy được không? | **Có.** Pipeline năm trạm, dashboard/API, Agent, alert/recovery và HITL/ACK/audit đều có live evidence. |
| Có thể sign-off release không? | **Chưa.** Một lỗi data-quality P0 cho phép station offline/stale vẫn nhận forecast `fresh`. |
| Kết quả test là gì? | **57 cases: 39 PASS, 9 FAIL, 9 NOT_RUN.** Đã thực hiện 48/57 case (84,2%); 39/48 case đã chạy PASS (81,3%). |
| Điểm mạnh rõ nhất | Agent golden evaluation 62/62; browser resilience 19/19; browser E2E 6/6; HITL chặn Resident và chỉ dispatch sau Manager approval. |
| Việc cần làm trước khi nộp | Sửa 4 bug đang mở, chạy full pytest đến khi kết thúc, hoàn thành 9 manual/public checks và clean image build. |

**Quyết định hiện tại: NOT READY — P0 DATA-QUALITY GATE FAILED.**

### Bốn vấn đề cần nhìn thấy ngay

| Ưu tiên | ID | Vấn đề | Ảnh hưởng | Hành động cần thiết |
|---:|---|---|---|---|
| 1 | `BUG-005` | S05 offline/stale vẫn nhận forecast HTTP 200 với `freshness=fresh` | Vi phạm data-quality gate; chặn release | Chặn forecast theo station quality và thêm regression test |
| 2 | `BUG-001` | Ba lỗi Agent/route về intent, method signature và fail-closed | Có thể trả sai luồng hoặc không fail closed | Đồng bộ route contract và rerun route suite |
| 3 | `BUG-002` | Hai report assertions không khớp contract narrative/export | Chưa chứng minh report/export nhất quán | Chốt contract, sửa code/test và retest PDF/export |
| 4 | `BUG-003` | Ventilation drawer lệch eco-mode action contract | UI và HITL source contract chưa thống nhất | Xác nhận contract hiện hành rồi sửa hoặc cập nhật test |

Chín dòng FAIL trong Sheet quy về **7 failure observations thuộc 4 bug**: một số dòng kiểm tra cùng một vấn đề ở
nhiều lớp, chẳng hạn `API-001` và `M-09` cùng truy về `BUG-005`. Vì full suite chưa chạy xong, đây chưa phải tổng
failure cuối cùng của repository.

### Cách đọc báo cáo

1. Đọc phần 1 để nắm quyết định và bốn vấn đề chính.
2. Xem phần 3 nếu cần đối chiếu gate và số liệu test.
3. Xem phần 4 để biết defect nào đang mở và bước xử lý.
4. Mở [`test-cases-sheet.csv`](test-cases-sheet.csv) hoặc evidence chỉ khi cần truy vết từng case.

AirGuard AI là MVP dùng dữ liệu simulator, không phải hệ thống quan trắc được chứng nhận và không dùng để đưa ra
chẩn đoán y tế hoặc kết luận pháp lý.

## 2. Phạm vi và môi trường đã kiểm tra

| Trường | Giá trị |
|---|---|
| Runtime | Local Docker Desktop; backend `:8000`, Agent `:8001`, frontend `:5173` |
| Browser | Chrome headless qua browser E2E; responsive 375/1280 qua snapshot script |
| Scenarios | `normal` → `spike` → `recovery` → `station-silence` → `normal` |
| Người thực hiện | Automated/runtime verification bởi Codex; human visual sign-off **chưa thực hiện** |
| Mức độ môi trường | Local verification, chưa phải final release candidate |

Phạm vi đã chạy:

- Docker health/readiness và frontend access.
- Simulator → MQTT → consumer → PostgreSQL → API cho S01–S05.
- Current/history, forecast 24h, Golden Window và spatial API.
- Agent current/compare/forecast, HITL refusal và browser fault/recovery.
- Spike/recovery, station-silence và duplicate/stale gates.
- Proposal pending, Resident 403, reject, quick-approve, dispatch, device ACK và audit.
- Scoped Python regression, frontend report/email scripts và production build.

Evidence kỹ thuật chi tiết nằm tại
[`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md).

Giới hạn môi trường: clean Agent image build bị timeout khi tải dependency từ PyPI. Runtime Agent dùng current
`src/` trên cached dependency image; kết quả này không được dùng để ký clean-build gate.

## 3. Kết quả tổng hợp

### 3.1. Kết quả theo gate

| Module/Gate | Kết quả | Trạng thái |
|---|---|---|
| Full Python suite | Chưa hoàn tất; treo sau khoảng 63%. Fail-fast: 14 PASS rồi 1 FAIL | FAIL |
| Scoped Python reruns | 7 failures đã xác nhận; các scoped run có phần chồng nhau nên không cộng số PASS | FAIL |
| Agent golden evaluation | 62/62; grounding/safety/tool selection 100% | PASS |
| Forecast benchmark | PM2.5 MAE 7.65 → 1.65; cải thiện 78.5% | PASS |
| Live pipeline | S01–S05 online/fresh; MQTT → DB → API và browser live | PASS |
| Alert/recovery | Spike tạo AQI/PM2.5 alert; recovery đóng alert | PASS |
| Offline forecast gate | S05 offline vẫn nhận forecast `fresh` | FAIL |
| Agent API/browser | Grounded current/compare/forecast; resilience 19/19; browser 6/6 | PASS |
| HITL/device/audit | Pending, Resident 403, reject no-dispatch, approve → ACK, đủ audit chain | PASS |
| Reports | Frontend 22 PASS; email snapshots PASS; còn 2 report-generator failures | FAIL |
| Frontend build | PASS, 2323 modules, 6.96s | PASS |
| Clean Agent image build | PyPI timeout; runtime dùng cached dependencies + current source | BLOCKED |
| Manual visual/public URL | Dashboard/timeline/PDF/full responsive/public URL còn thiếu | NOT_RUN |

### 3.2. Automated results

| Run | Kết quả |
|---|---|
| `pytest tests -q -x` | 14 PASS, 1 FAIL tại Phase31 TC-16 |
| Full `pytest tests -q` | Không hoàn tất; treo sau khoảng 63% và được dừng |
| Scoped route/context/report/frontend | 122 PASS, 3 FAIL |
| Scoped HITL/device/alert/report | 103 PASS, 2 FAIL |
| Duplicate/stale focused | 4 PASS |
| `npm run test:ai-resilience` | 19/19 PASS |
| `npm run test:ai-browser-e2e` | 6/6 PASS, có JSON và screenshots |
| `npm run test:reports` | 22 PASS |
| `npm run test:email-snapshots` | 375/1280 PASS |
| `npm run build` | PASS, 2323 modules, 6.96s |

Hai scoped Python run có test chồng nhau nên không cộng số PASS thành tổng suite. Forecast benchmark PASS chỉ
chứng minh accuracy trên fixture, không xóa lỗi eligibility của offline forecast trong live API.

### 3.3. Live E2E và manual results

- Backend health/ready, Agent health và frontend đều HTTP 200.
- S01–S05 online/fresh trong scenario normal; history S03 trace bằng `MSG-cae2219e1f-S03-000003`.
- S03 forecast có 24 horizons, bounds, model/source/confidence; Golden Window và heatmap API có dữ liệu.
- Spike tạo AQI/PM2.5 alert S03; recovery đưa PM2.5 về 27.26, AQI 83 và đóng alert.
- Station-silence đưa S05 offline/stale; current trả null và Agent không dùng trạm, nhưng forecast vẫn trả HTTP 200,
  `freshness=fresh` và ba giá trị (`BUG-005`).
- Proposal pending chặn Resident bằng 403; reject không dispatch; Manager approve tạo command và nhận ACK
  `succeeded`; audit có đủ create, review, dispatch.prepare, dispatch và ACK.
- Browser Agent E2E 6/6 PASS, đóng lỗi UI lịch sử ngày 24/08.
- Chín case vẫn `NOT_RUN`, chủ yếu là kiểm tra trực quan dashboard/timeline/PDF/responsive và public URL.

Kết quả từng test case, bao gồm các case manual, nằm trong
[`test-cases-sheet.csv`](test-cases-sheet.csv); hướng dẫn đọc và cập nhật nằm tại
[`02-test-cases.md`](02-test-cases.md).

## 4. Defect và blocker

### 4.1. Issue đang mở và blocker

| ID | Module | Severity | Actual / Expected | Tests | Status | Evidence hoặc bước tiếp theo |
|---|---|---|---|---:|---|---|
| BUG-001 | AI Agent/Route | High | Ba case sai intent, fail-closed hoặc method signature; cần route đúng context và lỗi service trả insufficient data | 3 | OPEN | `PY-001`, `PY-021`, `PY-022`; sửa route contract rồi chạy full route suite |
| BUG-002 | Reports | Medium | Fallback narrative và stored-record export lệch assertion; cần thống nhất contract ngôn ngữ/escaping và persisted record | 2 | OPEN | `PY-017`, `PY-018`; chốt contract rồi sửa code hoặc test có căn cứ |
| BUG-003 | Frontend/HITL | Medium | Drawer thiếu eco-mode proposal action mà contract test yêu cầu; cần UI và HITL contract thống nhất | 1 | OPEN | `PY-020`; xác nhận regression hay contract cũ |
| BUG-005 | Forecast/Data quality | High | S05 offline/stale vẫn nhận forecast HTTP 200 `fresh`; cần chặn offline/stale khỏi forecast | 1 live | OPEN | `API-001`, `M-09`; thêm quality gate và regression test |
| ENV-004 | Agent image build | N/A | Clean build timeout tải `pydantic_core`; cần build mới hoàn tất từ dependencies | N/A | BLOCKED | Rerun khi PyPI/network ổn định; không dùng cached runtime để ký gate |
| SEC-001 | Dependencies | NEEDS_TRIAGE | `npm ci` báo một high-severity advisory; cần fix hoặc risk acceptance | N/A | OPEN | Review `npm audit`; không auto-fix trước khi đánh giá breaking change |

### 4.2. Vấn đề đã đóng hoặc được retest

| ID/nhóm | Kết quả retest | Trạng thái |
|---|---|---|
| `BUG-004` — Agent UI failure ngày 24/08 | Browser E2E 6/6 PASS, có JSON và screenshots | CLOSED |
| `ENV-001` — runtime stack từng dừng | Backend ready, Agent health và frontend HTTP 200 ngày 31/08 | CLOSED |
| `ENV-002` — AI resilience từng nhận 503 do stack dừng | 19/19 PASS | CLOSED |
| `ENV-003` — email snapshot thiếu runtime | 375/1280 PASS bằng project virtualenv | CLOSED |
| Route/context cũ | `PY-002`–`PY-016` và `PY-019` PASS sau merge `main` | CLOSED/RETESTED |

Nhóm route/context scoped hiện đạt `122 PASS, 3 FAIL`. Con số “20 failures” của commit cũ `a939966` chỉ là lịch
sử và không được dùng như kết quả hiện tại.

## 5. Phần đã chứng minh và phần còn thiếu

Đã có evidence:

- Live simulator pipeline đủ năm trạm và trace được message ID/timestamps.
- Forecast 24 giờ, bounds, model metadata, Golden Window và spatial API hoạt động trên trạm fresh.
- Agent trả lời grounded; UI xử lý có kiểm soát 503/timeout/network/recovery.
- Alert có consecutive gate và tự resolve khi recovery.
- HITL chặn Resident; reject không dispatch; approve có command/ACK/audit đúng chuỗi.
- Duplicate/stale checks ở validator/storage/Agent PASS.
- Email snapshots, report UI contract và production build PASS.

Chưa thể tuyên bố PASS:

- Offline/stale forecast do `BUG-005`.
- Full regression suite vì chưa hoàn tất và còn 7 failures đã xác nhận.
- Personalized route live và indoor fallback.
- Kiểm tra trực quan dashboard history, timeline Play/Pause, PDF và toàn bộ responsive views.
- Public URL incognito/HTTPS/CORS.
- Clean Agent image build không phụ thuộc cache.

## 6. Release decision và sign-off

**Không sign-off release tại lần chạy này.** Đây là quyết định có chủ đích dựa trên evidence, không phải phần báo
cáo bị bỏ trống.

### Điều kiện còn lại trước sign-off

| Điều kiện | Trạng thái hiện tại | Owner đề xuất | Bằng chứng cần có để đóng |
|---|---|---|---|
| Sửa/retest `BUG-001` và `BUG-005` | CHƯA ĐẠT | Backend/Agent | Route suite PASS; offline/stale forecast bị chặn |
| Sửa/retest `BUG-002` | CHƯA ĐẠT | Reports | Report suite PASS và export dùng cùng persisted record |
| Xử lý `BUG-003` | CHƯA ĐẠT | Frontend/HITL | UI contract test PASS hoặc contract change được duyệt |
| Full pytest hoàn tất | CHƯA ĐẠT | QA | Command kết thúc, exit code và tổng kết đầy đủ |
| Clean Agent image build | BLOCKED | DevOps | Clean build PASS không dùng cached dependency image |
| Hoàn thành 9 case `NOT_RUN` | CHƯA ĐẠT | QA/Product | Screenshot/manual result hoặc waiver có người duyệt |
| Review `SEC-001` | CHƯA ĐẠT | Technical Lead | Fix hoặc risk acceptance có lý do |
| Freeze final URL và final commit | CHƯA CÓ | Release Lead | Public URL, commit SHA và thời điểm kiểm tra cuối |

### Trạng thái phê duyệt

| Vai trò | Người ký | Ngày | Quyết định hiện tại | Lý do |
|---|---|---|---|---|
| QA Lead | Chưa ghi nhận | Chưa ký | NOT SIGNED | Còn FAIL/NOT_RUN và full suite chưa hoàn tất |
| Technical Lead | Chưa ghi nhận | Chưa ký | NOT SIGNED | Còn P0 data-quality bug, build blocker và security review |
| Product/Team Lead | Chưa ghi nhận | Chưa ký | NOT SIGNED | Chưa có release candidate và public URL cuối |

Khi retest hoàn tất, cập nhật trực tiếp bảng này bằng họ tên, ngày, quyết định và link evidence; không xóa lịch sử
FAIL để làm báo cáo trông “đẹp” hơn.

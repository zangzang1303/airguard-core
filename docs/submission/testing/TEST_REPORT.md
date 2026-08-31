# AirGuard AI — Final Test Report

## 1. Kết luận

| Trường | Giá trị |
|---|---|
| Ngày kiểm tra | 31/08/2026 (Asia/Bangkok) |
| Branch | `fixUI-hvlong` |
| Commit | `a939966` |
| Python | 3.12.1 |
| Dữ liệu | Simulator-derived MVP data |
| Kết luận hiện tại | **NOT READY — AUTOMATED GATE FAILED** |

Agent golden evaluation, forecast benchmark và frontend production build đã PASS. Tuy nhiên full Python
suite còn 20 test failure. Docker Compose config hợp lệ nhưng không có service nào đang chạy, vì vậy live
pass-through, browser E2E và manual acceptance chưa đủ evidence để sign-off.

AirGuard AI là MVP sử dụng dữ liệu simulator, không phải hệ thống quan trắc được chứng nhận và không dùng
để đưa ra chẩn đoán y tế hoặc kết luận pháp lý.

## 2. Phạm vi kiểm thử

- Python backend, Agent, API, IoT và frontend contract tests trong `tests/`.
- Agent golden evaluation gồm grounding, safety, tool selection và proposal eligibility.
- Forecast benchmark so với baseline.
- Frontend contract scripts và production build.
- Docker Compose configuration/status.
- Manual/E2E được lập kế hoạch nhưng chưa sign-off trên commit hiện tại.

Test plan gốc: [`../../test-plan.md`](../../test-plan.md). Checklist nghiệm thu đầy đủ:
[`../../manual-test-checklist.md`](../../manual-test-checklist.md).

## 3. Automated test results

### 3.1 Full Python suite

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

| Kết quả | Giá trị |
|---|---:|
| Passed | 763 |
| Failed | 20 |
| Warnings | 2 |
| Thời gian | 35.95 giây |
| Gate | **FAIL** |

Lần chạy đầu bị dừng ở collection do local virtualenv thiếu `pypdf`. Dependency `pypdf==5.1.0` đã có
trong `requirements.txt` và `backend/requirements.txt`; sau khi đồng bộ vào `.venv`, full suite chạy hoàn
chỉnh và cho kết quả trên. Chi tiết nhóm lỗi nằm tại [`defect-summary.md`](defect-summary.md).

### 3.2 Agent golden evaluation

```powershell
.\.venv\Scripts\python.exe eval/run_evaluation.py
```

| Chỉ số | Kết quả |
|---|---:|
| Cases | 62 |
| Passed | 62 |
| Tool selection | 100% |
| Grounding | 100% |
| Safety | 100% |
| Proposal eligibility | 100% |
| Tool-error transparency | 100% |
| p50 latency | 855.286 ms |
| p95 latency | 5037.678 ms |
| Gate | **PASS** |

Kết quả này không xóa bỏ 20 failure của full pytest; hai gate đo các phạm vi khác nhau.
Bản report do runner tạo nằm tại
[`../../../eval/reports/agent-evaluation-2026-08-08.md`](../../../eval/reports/agent-evaluation-2026-08-08.md).
Tên file legacy vẫn chứa ngày `2026-08-08`, nhưng trường `Generated` bên trong đã được runner cập nhật cho lần
chạy 31/08/2026.

### 3.3 Forecast benchmark

```powershell
.\.venv\Scripts\python.exe eval/run_prophet_benchmark.py
```

| Metric | Baseline MAE | Extended MAE | Cải thiện |
|---|---:|---:|---:|
| PM2.5 | 7.65 | 1.65 | 78.5% |
| AQI | 18.02 | 3.69 | 79.5% |
| Overall | 38.81 | 7.55 | 80.5% |

Acceptance PM2.5 improvement `>= 7%`: **PASS**. Đây là mô hình extended additive Fourier/
Prophet-inspired, không phải thư viện Prophet thật. Báo cáo chi tiết:
[`../../evidence/forecast-model-evaluation.md`](../../evidence/forecast-model-evaluation.md).

### 3.4 Frontend tests và build

| Command | Kết quả | Ghi chú |
|---|---|---|
| `npm run test:api-base-url` | PASS | Host-alignment regression checks pass. |
| `npm run test:ai-resilience` | BLOCKED | 18 PASS, 1 live pass-through fail vì backend trả 503 khi stack đang dừng. |
| `npm run test:unified-legend` | PASS | 28 passed, 0 failed. |
| `npm run test:personalized-alerts` | PASS | Frontend contract pass. |
| `npm run test:email-snapshots` | BLOCKED | Dependencies đã đồng bộ; container phục vụ snapshot không chạy. |
| `npm run test:reports` | PASS | 22 checks pass. |
| `npm run build` | PASS | 2323 modules transformed; Vite build 31.01 giây. |

`npm ci` hoàn tất với 117 packages được audit và báo **1 high severity vulnerability**. Chưa chạy
`npm audit fix` vì thao tác đó có thể thay đổi dependency graph; cần owner đánh giá và cập nhật lockfile có
chủ đích.

Script `test:ai-browser-e2e` chưa chạy vì live stack không hoạt động.

### 3.5 Docker Compose

| Check | Kết quả | Ghi chú |
|---|---|---|
| `docker compose config --quiet` | PASS | Compose configuration hợp lệ. |
| `docker compose ps` | BLOCKED | Không có container nào đang chạy tại thời điểm kiểm tra. |

Compose hiện khai báo 13 service entries do có `db-migrate` và nhiều instance device simulator. Có thể mô tả
kiến trúc bằng 8 nhóm thành phần lõi, nhưng không nên ghi “8 containers” nếu runtime thực tế khởi động nhiều
container hơn.

## 4. Manual và live E2E

Chưa có lần sign-off manual hoàn chỉnh trên commit `a939966`. Các P0/P1 cần chạy được liệt kê tại
[`manual-test-results.md`](manual-test-results.md). Không kế thừa PASS từ evidence ngày 11–24/08 cho code thay
đổi ngày 29–30/08 nếu chưa retest.

Các gate đặc biệt phải xác nhận live:

- Simulator → MQTT → consumer → PostgreSQL → API → UI cho đủ S01–S05.
- Invalid/stale/offline/duplicate không đi vào current/forecast/alert/proposal.
- Agent trả lời grounded và fail closed khi tool/backend lỗi.
- Proposal luôn `pending`; Resident bị chặn; chỉ Manager approve/reject.
- Không dispatch trước approval; ACK khớp `command_id`; audit đủ correlation IDs.
- Forecast 24h, Golden Window, Play/Pause và spatial heatmap hiển thị đúng source/time.
- Daily/weekly report export Markdown/HTML/PDF dùng cùng persisted record.
- UI error ngày 24/08/2026 phải được retest và có evidence mới.

## 5. Defects, blockers và limitations

- 20 automated failures: xem [`defect-summary.md`](defect-summary.md).
- Docker stack stopped: live API/UI/browser checks chưa thể sign-off.
- Email snapshot phụ thuộc runtime container chưa chạy.
- Một npm high-severity advisory cần dependency owner review.
- Sensor và device đều là simulator.
- AQI là PM2.5 concentration sub-index cho demo, không phải official NowCast.
- Forecast là baseline/extended additive model, chưa phải Prophet/LSTM production.
- Heatmap là nội suy trực quan, không phải mô hình lan truyền khoa học.
- Frontend authentication/RBAC vẫn là demo identity; production auth cần cấu hình riêng.

## 6. Release decision

**Không sign-off release tại lần chạy này.** Điều kiện tối thiểu để chuyển sang `PASS` hoặc
`PASS WITH LIMITATIONS`:

- [ ] Full pytest không còn failure chưa được disposition.
- [ ] Live stack health/readiness pass và service inventory được lưu bằng screenshot/log.
- [ ] Hoàn thành toàn bộ manual P0 trên đúng final commit.
- [ ] Retest Agent chat UI, route flows, report exports và ventilation action contract.
- [ ] Chạy email snapshot và browser E2E trong runtime phù hợp.
- [ ] Đánh giá npm advisory, ghi quyết định fix/accept/defer và lý do.
- [ ] Thu thập evidence đã làm sạch, điền tester và sign-off.
- [ ] Export báo cáo PDF và kiểm tra font/link/trang.

## 7. Sign-off

| Vai trò | Họ tên | Ngày | Quyết định |
|---|---|---|---|
| QA Lead | **NEEDS VERIFICATION** | | |
| Technical Lead | **NEEDS VERIFICATION** | | |
| Product/Team Lead | **NEEDS VERIFICATION** | | |

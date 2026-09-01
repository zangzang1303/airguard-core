# 1. Test Plan — AirGuard AI

> Tài liệu này mô tả phạm vi và cách đánh giá. Kết quả mới nhất nằm trong [`03-test-report.md`](03-test-report.md).

## 1. Mục tiêu

Xác minh AirGuard AI hoạt động đúng trên các luồng simulator → MQTT → PostgreSQL → API/UI, forecast, Agent grounded, cảnh báo, HITL, audit và reports; đồng thời kiểm tra hệ thống fail closed khi dữ liệu hoặc dịch vụ không đáng tin cậy.

## 2. Phạm vi theo module

| Module | Nội dung chính | Mức ưu tiên |
|---|---|---|
| Infrastructure/Data | Compose, MQTT, PostgreSQL, S01–S05, duplicate/stale/offline/recovery | P0 |
| Backend/API | Health/readiness, schema, status code, data-quality gate | P0 |
| AI Agent | Tool selection, grounding, safety, context và route | P0 |
| Forecast/Spatial | Forecast 1–24h, bounds, benchmark, Golden Window, heatmap | P0/P1 |
| Frontend | Dashboard, loading/error/recovery, responsive và browser E2E | P0/P1 |
| HITL/Audit | Pending proposal, RBAC, approve/reject, dispatch/ACK, audit | P0 |
| Reports/Notification | Daily/weekly, export, provider disabled/failure | P1 |

## 3. Phương pháp

- Unit/contract: logic, schema, policy và source contract.
- Integration/E2E: pipeline dữ liệu, Agent live, route, forecast, alert, HITL và device ACK.
- Evaluation: Agent golden set và forecast benchmark.
- Negative/security: 401/403/409/422/503, injection, stale/offline và provider failure.
- Manual visual: dashboard, timeline, PDF, responsive và public URL.

## 4. Môi trường retest mới nhất

| Trường | Giá trị |
|---|---|
| Ngày | 01/09/2026, Asia/Bangkok |
| Branch/commit | `test-report` / `aeda2ab` |
| Runtime | Local Docker Desktop; backend `:8000`, Agent `:8001`, frontend `:5173` |
| Browser | Chrome headless qua Playwright |
| Dữ liệu | Simulator-derived MVP data |
| Người thực hiện | Automated/runtime verification bởi Codex; human visual sign-off chưa thực hiện |

Lần retest dùng image local hiện có, không phải clean image build từ dependency cache rỗng. Public URL và external email delivery không nằm trong môi trường local này.

## 5. Entry criteria

| Điều kiện | Trạng thái | Evidence |
|---|---|---|
| Python/Node dependencies chạy được | ĐẠT | 801 Python tests được thực thi; frontend scripts hoàn tất |
| Docker stack và các health endpoint hoạt động | ĐẠT | Backend healthy, Agent/frontend hoạt động |
| Simulator phát đủ S01–S05 | ĐẠT | Scenario normal trước và sau station-silence retest |
| Commit, thời gian và môi trường được ghi | ĐẠT | Evidence ngày 01/09/2026 |
| Final release commit/public URL đã freeze | CHƯA ÁP DỤNG | Đây là local verification, chưa phải release candidate cuối |

## 6. Exit criteria

| Điều kiện | Trạng thái | Kết luận |
|---|---|---|
| Luồng demo cốt lõi chạy được | ĐẠT | Pipeline, Agent live, route/indoor, browser recovery, reports và HITL đã có evidence |
| Automated regression đạt ít nhất 98% | ĐẠT | 792/801 PASS = 98,9% |
| Không còn P0 data-quality failure | CHƯA ĐẠT | `BUG-005`: offline/stale forecast vẫn trả `fresh` |
| Grounding/safety golden set đạt 100% | ĐẠT | 62/62 golden cases PASS từ evidence hiện hành |
| HITL không dispatch trước Manager approval | ĐẠT | Contract tests hiện tại PASS; live chain đã xác minh ngày 31/08 |
| Manual visual/public checks hoàn tất | CHƯA ĐẠT | Còn 6 case dashboard/timeline/PDF/responsive/public URL |
| Clean build và final sign-off | CHƯA THỰC HIỆN | Chỉ thực hiện trên final release commit |

## 7. Quy ước trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| PASS | Actual khớp expected và có evidence. |
| FAIL | Đã chạy và actual không khớp expected. |
| BLOCKED | Không thể chạy vì dependency/môi trường ngoài case. |
| NOT_RUN | Chưa thực hiện đầy đủ. |
| NEEDS_RETEST | Có evidence cũ nhưng chưa kiểm tra lại trên commit hiện tại. |
| N/A | Không áp dụng và có lý do. |

## 8. Commands chính

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe eval/run_evaluation.py
.\.venv\Scripts\python.exe eval/run_prophet_benchmark.py
npm.cmd --prefix frontend run test:ai-resilience
npm.cmd --prefix frontend run test:ai-browser-e2e
npm.cmd --prefix frontend run test:email-snapshots
npm.cmd --prefix frontend run test:reports
npm.cmd --prefix frontend run build
docker compose config --quiet
docker compose ps
```

Checklist manual chi tiết: [`../../manual-test-checklist.md`](../../manual-test-checklist.md).

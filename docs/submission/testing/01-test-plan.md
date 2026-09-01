# 1. Test Plan — AirGuard AI

> **Vai trò của tài liệu:** mô tả cách kiểm thử và tiêu chí đánh giá. Kết quả thực tế và quyết định release nằm
> trong [`03-test-report.md`](03-test-report.md). Giám khảo chỉ cần đọc phần 1–4 để hiểu phạm vi; phần 5–8 phục vụ
> truy vết kỹ thuật.

## 1. Mục tiêu

Chứng minh AirGuard AI hoạt động đúng trên luồng simulator, dashboard, forecast, Agent grounded, HITL,
audit và reports; đồng thời xác nhận hệ thống fail closed khi dữ liệu/dịch vụ không đáng tin cậy.

## 2. Phạm vi theo module

| Module | Nội dung | Ưu tiên |
|---|---|---|
| Infrastructure/Data | Compose, MQTT, PostgreSQL, S01–S05, duplicate/stale/offline/recovery | P0 |
| Backend/API | Health/readiness, schemas, status codes, data-quality gates, exports | P0 |
| AI Agent | Tool selection, grounding, safety, context, route, insufficient-data | P0 |
| Forecast/Spatial | Forecast 1–24h, bounds, benchmark, Golden Window, heatmap timeline | P0/P1 |
| Frontend UI/UX | Dashboard, history, loading/empty/error, responsive, browser E2E | P0/P1 |
| HITL/Audit | Pending proposal, RBAC, approve/reject, dispatch/ACK, audit chain | P0 |
| Reports/Notification | Daily/weekly, Markdown/HTML/PDF, provider disabled/failure | P1 |

## 3. Loại kiểm thử

- Unit/contract: logic, schema và frontend source contract.
- Integration/E2E: simulator → MQTT → DB → API/UI; alert; HITL/audit/device.
- Evaluation: Agent golden set và forecast benchmark.
- Negative/security: 401/403/409/422/503, injection, stale/offline và provider failure.
- Manual visual: dashboard, map timeline, PDF, responsive và public URL.

## 4. Môi trường run hiện tại

| Trường | Giá trị |
|---|---|
| Ngày | 31/08/2026, Asia/Bangkok |
| Branch/commit | `test-report` / `202037e` |
| Runtime | Local Docker Desktop; backend `:8000`, Agent `:8001`, frontend `:5173` |
| Browser | Chrome headless qua browser E2E |
| Dữ liệu | Simulator-derived MVP data |
| Scenarios | normal, spike, recovery, station-silence, rồi trả về normal |
| Người thực hiện | Automated/runtime verification bởi Codex; human visual sign-off chưa thực hiện |

Giới hạn: clean Agent image build bị PyPI timeout. Runtime Agent dùng current `src/` trên cached dependency
image; không được dùng evidence này để ký clean-build gate.

## 5. Entry criteria

| Điều kiện đầu vào | Trạng thái tại lần chạy 31/08 | Bằng chứng hoặc lý do |
|---|---|---|
| Dependencies local chạy được scoped tests và frontend scripts | ĐẠT | Các scoped suite và frontend scripts đã có output |
| Docker stack, backend, Agent và frontend hoạt động | ĐẠT | Health/readiness và frontend HTTP 200 |
| Simulator phát ít nhất hai chu kỳ dữ liệu | ĐẠT | S01–S05 online/fresh và có message ID truy vết |
| Commit, timestamp, URL local và scenarios được ghi | ĐẠT | Metadata trong Test Report và runtime evidence |
| Final release commit/tag đã freeze, worktree sạch | CHƯA ĐẠT | Lần chạy dùng commit `202037e`, chưa phải release commit cuối |
| Clean Agent image build hoàn tất | BLOCKED | `ENV-004`: timeout tải dependency từ PyPI |

## 6. Exit criteria

| Điều kiện đầu ra | Trạng thái | Kết luận ngắn |
|---|---|---|
| Không còn P0 `FAIL/BLOCKED` chưa được xử lý | CHƯA ĐẠT | `BUG-005` là release blocker |
| Full pytest hoàn tất và mọi failure có disposition | CHƯA ĐẠT | Suite treo khoảng 63%; còn 7 failures đã xác nhận |
| Agent golden grounding/safety đạt 100% | ĐẠT | 62/62 golden cases PASS |
| Không dùng dữ liệu stale/offline cho downstream | CHƯA ĐẠT | Offline forecast vẫn trả dữ liệu `fresh` |
| HITL chặn Resident; dispatch chỉ sau Manager approval | ĐẠT | Resident 403; approve → command → ACK có audit |
| P0 manual/visual có evidence trên final commit | CHƯA ĐẠT | Còn dashboard, timeline, PDF và responsive checks |
| QA và Technical Lead ký Test Report | CHƯA KÝ | Chỉ ký sau khi các điều kiện release được xử lý |

## 7. Quy ước trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| PASS | Actual khớp expected và có evidence. |
| FAIL | Đã chạy và actual không khớp expected. |
| BLOCKED | Không thể chạy vì dependency/môi trường ngoài case. |
| NOT_RUN | Chưa thực hiện đầy đủ. |
| NEEDS_RETEST | Có evidence cũ nhưng chưa kiểm tra lại trên final commit. |
| N/A | Không áp dụng; bắt buộc ghi lý do. |

## 8. Commands chính

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe eval/run_evaluation.py
.\.venv\Scripts\python.exe eval/run_prophet_benchmark.py
npm --prefix frontend run test:ai-resilience
npm --prefix frontend run test:ai-browser-e2e
npm --prefix frontend run test:email-snapshots
npm --prefix frontend run test:reports
npm --prefix frontend run build
docker compose config --quiet
docker compose ps
```

Checklist chuyên sâu: [`../../manual-test-checklist.md`](../../manual-test-checklist.md).

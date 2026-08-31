# 1. Test Plan — AirGuard AI

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
| Tester | Codex automated/runtime verification; human visual sign-off pending |

Giới hạn: clean Agent image build bị PyPI timeout. Runtime Agent dùng current `src/` trên cached dependency
image; không được dùng evidence này để ký clean-build gate.

## 5. Entry criteria

- [x] Dependencies local có thể chạy scoped tests và frontend scripts.
- [x] Docker stack khởi động; backend ready, Agent healthy, frontend truy cập được.
- [x] Simulator phát ít nhất hai chu kỳ dữ liệu.
- [x] Commit, timestamp, URLs và scenarios được ghi.
- [ ] Final release commit/tag đã freeze và worktree sạch.
- [ ] Clean Agent image build hoàn tất.

## 6. Exit criteria

- [ ] Không còn P0 `FAIL/BLOCKED` chưa có disposition được duyệt.
- [ ] Full pytest hoàn tất, không treo và không còn failure chưa giải thích.
- [x] Agent golden grounding/safety đạt 100%.
- [ ] Không có stale/offline data usage; hiện `BUG-005` chưa đạt.
- [x] HITL chặn Resident và dispatch chỉ xảy ra sau Manager approval.
- [ ] Toàn bộ P0 manual/visual cases có evidence trên final commit.
- [ ] QA và Technical Lead sign-off Test Summary Report.

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

# 1. Test Plan — AirGuard AI

## 1.1 Mục tiêu

Chứng minh AirGuard AI hoạt động đúng trên các luồng dữ liệu simulator, dashboard, forecast, Agent grounded,
HITL, audit và báo cáo; đồng thời xác nhận hệ thống fail closed khi dữ liệu hoặc dịch vụ không đáng tin cậy.

## 1.2 Phạm vi theo module

| Module | Nội dung kiểm thử | Mức ưu tiên |
|---|---|---|
| Infrastructure/Data | Docker Compose, MQTT, PostgreSQL, S01–S05, duplicate/stale/offline/recovery | P0 |
| Backend/API | Health/readiness, schemas, status codes, data-quality gate, report exports | P0 |
| AI Agent | Tool selection, grounding, safety, context, route, insufficient-data | P0 |
| Forecast/Spatial | Forecast 1–24h, bounds, benchmark, Golden Window, heatmap timeline | P0/P1 |
| Frontend UI/UX | Dashboard, history, loading/empty/error, responsive, browser E2E | P0/P1 |
| HITL/Audit | Pending proposal, RBAC, approve/reject, dispatch/ACK, audit chain | P0 |
| Reports/Notification | Daily/weekly, Markdown/HTML/PDF, provider disabled/failure | P1 |

## 1.3 Loại kiểm thử

- Unit/contract: logic, schema, frontend source contract.
- Integration: simulator → MQTT → consumer → DB → API; alert; HITL/audit.
- Automated evaluation: Agent golden set và forecast benchmark.
- UI/E2E: dashboard, map, chat, approval, report export.
- Negative/security: 401/403/409/422/503, prompt injection, stale/offline, provider failure.
- Manual acceptance: luồng pitching trên release stack cuối.

## 1.4 Môi trường của lần chạy hiện có

| Trường | Giá trị |
|---|---|
| Ngày | 31/08/2026 (Asia/Bangkok) |
| Branch/commit | `test-report` / `2f2f47e` (test evidence ban đầu chạy trên `a939966`) |
| Python | 3.12.1 |
| Frontend | React/Vite; Node 22.19.0 trong snapshot test output |
| Runtime | Local; Compose config hợp lệ nhưng stack không chạy khi thu evidence |
| Dữ liệu | Simulator-derived MVP data |
| Browser/public URL | **NEEDS VERIFICATION** |
| Tester/sign-off | **NEEDS VERIFICATION** |

Khi retest, phải tạo run mới trên final commit; không sửa metadata của lần chạy cũ.

## 1.5 Entry criteria

- [ ] Final commit/tag đã freeze và worktree sạch.
- [ ] Dependencies được cài từ requirements/package-lock.
- [ ] `.env` local có cấu hình cần thiết nhưng không được commit.
- [ ] Docker stack khởi động; backend/Agent healthy và backend ready.
- [ ] Simulator đã phát ít nhất hai chu kỳ dữ liệu.
- [ ] Tester, timestamp, URL, browser và scenario đã được ghi.

## 1.6 Exit criteria

- [ ] Không còn P0 `FAIL` hoặc `BLOCKED` chưa có disposition được duyệt.
- [ ] Full pytest không còn failure chưa được giải thích.
- [ ] Agent critical grounding/safety đạt 100%.
- [ ] Không có HITL bypass, stale-data usage hoặc secret leak.
- [ ] Toàn bộ P0 manual cases có evidence trên final commit.
- [ ] Bug report ghi rõ `OPEN/FIXED/RETESTED/DEFERRED`.
- [ ] QA và Technical Lead sign-off Test Summary Report.

## 1.7 Quy ước trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| PASS | Actual result khớp expected result và có evidence phù hợp. |
| FAIL | Đã chạy và actual result không khớp expected result. |
| BLOCKED | Không thể hoàn tất vì dependency/môi trường bên ngoài test case. |
| NOT_RUN | Chưa thực hiện. |
| NEEDS_RETEST | Có evidence cũ nhưng chưa kiểm tra lại trên final commit. |
| N/A | Không áp dụng; bắt buộc ghi lý do. |

## 1.8 Commands chính

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe eval/run_evaluation.py
.\.venv\Scripts\python.exe eval/run_prophet_benchmark.py
npm --prefix frontend run build
docker compose config --quiet
docker compose ps
```

Checklist chuyên sâu vẫn nằm tại [`../../manual-test-checklist.md`](../../manual-test-checklist.md) và
[`../../test-plan.md`](../../test-plan.md).

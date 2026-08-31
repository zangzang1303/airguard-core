# 4. Test Summary Report — AirGuard AI

## Executive summary

| Trường | Kết quả |
|---|---|
| Evidence date | 31/08/2026 |
| Code under automated test | Commit `a939966` |
| Documentation commit | `2f2f47e` |
| Overall status | **NOT READY — AUTOMATED GATE FAILED** |
| Release recommendation | Không sign-off trước khi xử lý 20 failures và hoàn thành P0 live/manual |

## Kết quả theo module/gate

| Module/Gate | Kết quả | Status |
|---|---|---|
| Full Python suite | 763 passed, 20 failed, 2 warnings; 35.95s | FAIL |
| Agent golden evaluation | 62/62; grounding/safety/tool selection 100% | PASS |
| Forecast benchmark | PM2.5 MAE 7.65 → 1.65; cải thiện 78.5% | PASS |
| Frontend build | 2323 modules; build 31.01s | PASS |
| Frontend source-contract scripts | API URL, legend 28/28, personalized alerts, reports 22 PASS | PASS |
| AI resilience live pass-through | 18 PASS, một live check nhận 503 khi stack dừng | BLOCKED |
| Email snapshots | Runtime container không chạy | BLOCKED |
| Docker configuration | `docker compose config --quiet` PASS | PASS |
| Docker live services | Không có container chạy tại thời điểm kiểm tra | BLOCKED |
| Browser E2E/manual acceptance | Chưa chạy trên final stack | NOT_RUN |

## Defect summary

| Nhóm | Số lượng | Trạng thái |
|---|---:|---|
| Agent route/geospatial/context | 17 automated failures | OPEN |
| Report generator/export | 2 automated failures | OPEN |
| Ventilation UI contract | 1 automated failure | OPEN |
| Historical Agent UI issue | 1 historical case | NEEDS_RETEST |
| Environment blockers | 3 chính | BLOCKED |
| Dependency advisory | 1 high severity advisory | NEEDS_TRIAGE |

Chi tiết: [`03-bug-report.md`](03-bug-report.md).

## Các phần đã chứng minh được

- Golden Agent fixture evaluation đạt toàn bộ 62 cases.
- Forecast benchmark vượt acceptance threshold.
- Frontend production build và các contract scripts chính PASS.
- Compose file hợp lệ.
- Evidence được gắn source simulator và không được diễn giải là quan trắc chính thức.

## Các phần chưa thể tuyên bố PASS

- Full regression suite vì còn 20 failures.
- Live simulator → MQTT → DB → API → UI trên final commit.
- Browser Agent chat, personalized route và multi-turn route context.
- HITL pending → review → dispatch → ACK và audit chain trên final stack.
- Email snapshots, responsive view và public URL.
- Report exports sau khi xử lý hai automated failures.

## Điều kiện sign-off

- [ ] Resolve/disposition và retest toàn bộ BUG-001 đến BUG-004.
- [ ] Full pytest không còn failure chưa được duyệt.
- [ ] Start final stack và hoàn thành toàn bộ manual P0 trong Sheet.
- [ ] Thêm screenshot/log/request IDs vào evidence index.
- [ ] Review SEC-001 và ghi quyết định dependency risk.
- [ ] Điền tester, Live URL, final commit và sign-off.
- [ ] Export bộ bốn tài liệu thành PDF hoặc một PDF có bốn chương.

## Sign-off

| Vai trò | Họ tên | Ngày | Quyết định |
|---|---|---|---|
| QA Lead | **NEEDS VERIFICATION** | | |
| Technical Lead | **NEEDS VERIFICATION** | | |
| Product/Team Lead | **NEEDS VERIFICATION** | | |

Báo cáo kỹ thuật dài hơn được giữ tại [`TEST_REPORT.md`](TEST_REPORT.md).

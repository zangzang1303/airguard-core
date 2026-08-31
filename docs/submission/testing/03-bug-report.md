# 3. Bug Report — AirGuard AI

## Quy ước

| Trường | Giá trị cho phép |
|---|---|
| Severity | Critical, High, Medium, Low, NEEDS_TRIAGE |
| Status | OPEN, FIXED, NEEDS_RETEST, BLOCKED, DEFERRED, CLOSED |
| Resolution | Chỉ điền sau khi có commit sửa và retest evidence |

## Danh sách lỗi hiện tại

| Bug ID | Module | Severity | Actual | Expected | Tests | Status | Evidence/next step |
|---|---|---|---|---|---:|---|---|
| BUG-001 | AI Agent/Route | High | Ba case còn sai intent, fail-closed hoặc lệch method signature | Route đúng context; service lỗi phải trả insufficient data | 3 | OPEN | `PY-001`, `PY-021`, `PY-022`; sửa route contract rồi chạy full route suite |
| BUG-002 | Reports | Medium | Fallback narrative và stored-record export không khớp assertion | Contract ngôn ngữ/escaping thống nhất, export cùng persisted record | 2 | OPEN | `PY-017`, `PY-018`; xác nhận contract rồi sửa code hoặc test có căn cứ |
| BUG-003 | Frontend/HITL | Medium | Drawer thiếu action token `requestProposal("eco_mode")` mà contract test yêu cầu | UI và HITL contract thống nhất | 1 | OPEN | `PY-020`; xác nhận đây là regression hay contract cũ |
| BUG-004 | Frontend/Agent | High | UI Agent từng fail ngày 24/08 | Chat UI xử lý success/failure/recovery đúng | 1 historical | CLOSED | Browser E2E ngày 31/08: 6/6 PASS, có JSON và screenshots |
| BUG-005 | Forecast/Data quality | High | S05 offline/stale vẫn nhận forecast HTTP 200, `freshness=fresh` và ba giá trị | Offline/stale station bị chặn khỏi forecast | 1 live | OPEN | `API-001`, `M-09`; thêm station-quality gate trước forecast và regression test |
| ENV-001 | Infrastructure | N/A | Stack từng dừng | Runtime services healthy | N/A | CLOSED | Backend ready, Agent health, frontend HTTP 200 ngày 31/08 |
| ENV-002 | Frontend test | N/A | AI resilience từng nhận 503 vì stack dừng | 19 checks PASS | 1 | CLOSED | Retest live: 19/19 PASS |
| ENV-003 | Snapshot test | N/A | Email snapshot từng thiếu runtime Python/container | 375/1280 PASS | 1 | CLOSED | Chạy bằng project virtualenv: PASS |
| ENV-004 | Agent image build | N/A | Clean Agent image build timeout khi tải `pydantic_core` từ PyPI | Build mới hoàn tất từ lock/dependencies | N/A | BLOCKED | Network/PyPI timeout; runtime dùng cached dependency image + current `src/` |
| SEC-001 | Dependencies | NEEDS_TRIAGE | `npm ci` từng báo một high-severity advisory | Fix hoặc documented risk acceptance | N/A | OPEN | Chạy/review `npm audit`; không auto-fix khi chưa đánh giá breaking change |

## Thay đổi so với báo cáo cũ

Các failure route/context cũ đã được retest sau khi merge `main`: nhóm scoped đạt `122 PASS, 3 FAIL`;
15 dòng `PY-002`–`PY-016` và `PY-019` hiện PASS. Không tiếp tục báo “20 failures” của commit cũ
`a939966` như kết quả hiện tại.

Trên commit `202037e`, full suite chưa tạo được tổng kết cuối: fail-fast dừng ở `PY-001`, còn lần chạy
toàn bộ bị treo sau khoảng 63% và được dừng. Hiện có **7 failures đã xác nhận** qua các scoped rerun;
con số này không được diễn giải là tổng failure cuối cùng cho tới khi full suite hoàn tất.

## Mẫu bug mới

```text
Bug ID:
Module:
Environment/commit:
Severity:
Status:
Preconditions:
Steps to reproduce:
Expected result:
Actual result:
Screenshot/log/request ID:
Root cause:
Fix commit/PR:
Retest result:
```

# 3. Bug Report — AirGuard AI

## Quy ước

| Trường | Giá trị cho phép |
|---|---|
| Severity | Critical, High, Medium, Low, NEEDS_TRIAGE |
| Status | OPEN, FIXED, NEEDS_RETEST, BLOCKED, DEFERRED, CLOSED |
| Resolution | Chỉ điền sau khi có commit sửa và retest evidence |

## Danh sách lỗi hiện tại

| Bug ID | Module | Severity | Mô tả/Actual | Expected | Affected tests | Status | Evidence/Next step |
|---|---|---|---|---|---:|---|---|
| BUG-001 | AI Agent/Route | NEEDS_TRIAGE | Route, context và distance cases nhận `insufficient_data`, sai intent hoặc sai khoảng cách | Grounded route đúng intent/context và target distance | 17 | OPEN | Điều tra request-scoped snapshots/history và route synthesis; xem defect summary |
| BUG-002 | Reports | NEEDS_TRIAGE | Fallback narrative và stored-record export không khớp assertion | Deterministic fallback và export cùng persisted record/contract | 2 | OPEN | Owner xác nhận contract ngôn ngữ/escaping rồi sửa hoặc cập nhật test có căn cứ |
| BUG-003 | Frontend/HITL | NEEDS_TRIAGE | Ventilation drawer không chứa action mà contract test đang kỳ vọng | UI và HITL contract thống nhất | 1 | OPEN | Xác nhận UI mới hay regression; retest sau disposition |
| BUG-004 | Frontend/Agent | NEEDS_TRIAGE | UI Agent request từng fail trong khi gọi backend trực tiếp PASS ngày 24/08 | UI chat nhận response 200 và render evidence | 1 historical | NEEDS_RETEST | Chạy browser E2E trên final stack, lưu network/screenshot |
| ENV-001 | Infrastructure | N/A | Không có Compose container chạy tại lần kiểm tra 31/08 | Release stack healthy/ready | N/A | BLOCKED | Start final stack rồi chạy P0 manual/E2E |
| ENV-002 | Frontend test | N/A | AI resilience live pass-through nhận 503 khi stack dừng | Live pass-through 200 | 1 | BLOCKED | Retest sau ENV-001 |
| ENV-003 | Snapshot test | N/A | Email snapshot dependency container không chạy | Snapshot scripts hoàn tất ở 375/1280 | 1 | BLOCKED | Khởi động runtime theo script rồi retest |
| SEC-001 | Dependencies | NEEDS_TRIAGE | `npm ci` báo một high-severity advisory | Advisory được fix hoặc có documented risk acceptance | N/A | OPEN | Review `npm audit`; không auto-fix trước khi đánh giá breaking changes |

## Chi tiết nhóm automated failures

Kết quả full suite: `763 passed, 20 failed, 2 warnings` trong 35.95 giây. Danh sách test và nhóm lỗi đầy đủ
nằm tại [`defect-summary.md`](defect-summary.md). Khi sửa một bug, bổ sung:

- Commit/PR sửa lỗi.
- Root cause.
- Test command dùng để retest.
- Actual result sau retest.
- Evidence và người xác nhận.

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

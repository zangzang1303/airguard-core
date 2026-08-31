# 2. Test Cases — AirGuard AI

## Sheet kết quả chính

File [`test-cases-sheet.csv`](test-cases-sheet.csv) là bảng nguồn cho Pass/Fail. File dùng UTF-8, có thể mở
bằng Excel hoặc import trực tiếp vào Google Sheets và lọc theo `Module`, `Priority`, `Test_Type`, `Status`.

Snapshot hiện tại có 54 dòng: **8 PASS, 20 FAIL, 3 BLOCKED, 22 NOT_RUN và 1 NEEDS_RETEST**. Các số này
phản ánh evidence hiện có, không phải mục tiêu cuối của release.

Các cột bắt buộc:

| Cột | Nội dung |
|---|---|
| Test_ID | Mã duy nhất của test case. |
| Module | Infrastructure, Backend/API, AI Agent, Forecast/Spatial, Frontend, HITL/Audit, Reports. |
| Priority | P0/P1/P2. |
| Test_Type | Automated, Manual, E2E hoặc Run Summary. |
| Test_Case | Nội dung cần kiểm tra. |
| Preconditions | Điều kiện trước khi chạy. |
| Steps_or_Command | Bước thực hiện hoặc command. |
| Expected_Result | Điều kiện PASS. |
| Actual_Result | Kết quả quan sát thực tế. |
| Status | PASS/FAIL/BLOCKED/NOT_RUN/NEEDS_RETEST/N/A. |
| Evidence | Link file, screenshot, log hoặc request ID. |
| Owner_Note | Người phụ trách, blocker hoặc bước tiếp theo. |

## Cách chia module

### AI Agent

Bao gồm golden evaluation, grounding/safety, route/geospatial, multi-turn context, tool failure và HITL
refusal. Full suite hiện có 17 failure liên quan route/context cần xử lý trước live sign-off.

### Frontend UI/UX

Bao gồm build, source-contract scripts, dashboard, responsive, browser E2E, error/retry và map timeline.
Build và phần lớn contract scripts PASS; browser E2E và email snapshots chưa hoàn tất do stack dừng.

### Luồng nghiệp vụ chính

Bao gồm pipeline S01–S05, data-quality gate, alert, forecast, proposal pending, Manager review,
dispatch/ACK, audit và report export. Các manual cases vẫn là `NOT_RUN` trên final release stack.

## Quy tắc điền kết quả

- Không đổi `NOT_RUN/BLOCKED` thành PASS chỉ vì code đã tồn tại.
- Một dòng PASS phải có `Actual_Result`, ngày/commit run và evidence phù hợp.
- Mỗi FAIL phải liên kết tới một Bug ID trong [`03-bug-report.md`](03-bug-report.md).
- Retest phải giữ lại kết quả cũ trong Git history và cập nhật evidence mới.
- Không đưa secret, token, email cá nhân hoặc raw prompt nhạy cảm vào Sheet.

## Thiết lập Google Sheets đề xuất

1. Mở Google Sheets → **File → Import → Upload** `test-cases-sheet.csv`.
2. Chọn **Replace current sheet** và separator **Comma**.
3. Freeze hàng 1, bật **Create a filter**.
4. Tạo dropdown cho `Status`: `PASS, FAIL, BLOCKED, NOT_RUN, NEEDS_RETEST, N/A`.
5. Conditional formatting: PASS xanh, FAIL đỏ, BLOCKED cam, NOT_RUN xám, NEEDS_RETEST vàng.
6. Không cấp quyền edit công khai; link nộp nên là Viewer.

Checklist thao tác chi tiết hơn có thể tra tại [`../../manual-test-checklist.md`](../../manual-test-checklist.md).

# 2. Test Cases — AirGuard AI

## Sheet kết quả chính

File [`test-cases-sheet.csv`](test-cases-sheet.csv) là nguồn Pass/Fail có thể mở bằng Excel hoặc import
trực tiếp vào Google Sheets và lọc theo `Module`, `Priority`, `Test_Type`, `Status`.

Snapshot tại commit `202037e` có **57 dòng**:

- **39 PASS**.
- **9 FAIL**.
- **9 NOT_RUN**.
- **0 BLOCKED** trong Sheet; clean Agent image build được quản lý ở Bug Report dưới `ENV-004`.

Các số này phản ánh evidence đã chạy ngày 31/08/2026, không phải mục tiêu cuối của release. Full Python suite
chưa hoàn tất, vì vậy 9 FAIL là số case được xác nhận trong Sheet chứ không phải tổng failure cuối cùng của
toàn bộ repository.

## Ý nghĩa các cột

| Cột | Nội dung |
|---|---|
| Test_ID | Mã duy nhất của test case. |
| Module | Infrastructure, Backend/API, AI Agent, Forecast/Spatial, Frontend, HITL/Audit, Reports. |
| Priority | P0/P1/P2. |
| Test_Type | Automated, Manual, E2E, Negative hoặc kết hợp. |
| Test_Case | Nội dung cần kiểm tra. |
| Preconditions | Điều kiện trước khi chạy. |
| Steps_or_Command | Bước thực hiện hoặc command. |
| Expected_Result | Điều kiện PASS. |
| Actual_Result | Kết quả quan sát thực tế. |
| Status | PASS/FAIL/BLOCKED/NOT_RUN/NEEDS_RETEST/N/A. |
| Evidence | Link file, screenshot, log hoặc request ID đã làm sạch. |
| Owner_Note | Bug ID, blocker hoặc bước tiếp theo. |

## Trạng thái theo nhóm

### AI Agent và route

Golden evaluation và live Agent grounding PASS. Nhiều route/context failures cũ đã được sửa sau merge
`main`; còn ba failures `PY-001`, `PY-021`, `PY-022` thuộc `BUG-001`.

### Frontend UI/UX

Production build, resilience, browser E2E, report UI và email snapshots đều PASS. Historical Agent UI issue
ngày 24/08 đã được retest và đóng. Các thao tác trực quan dashboard/timeline/PDF/responsive vẫn `NOT_RUN`.

### Luồng nghiệp vụ chính

Pipeline S01–S05, alert/recovery, HITL pending/reject/approve, dispatch/ACK và audit đều có live evidence.
Riêng forecast vẫn dùng history của station offline/stale, nên `API-001` và `M-09` là FAIL release-blocking.

## Quy tắc cập nhật kết quả

- Không đổi `NOT_RUN/BLOCKED` thành PASS chỉ vì code đã tồn tại.
- PASS phải có `Actual_Result`, commit/ngày run và evidence.
- FAIL phải liên kết Bug ID trong [`03-bug-report.md`](03-bug-report.md).
- Retest giữ kết quả cũ trong Git history và cập nhật evidence mới.
- Không đưa secret, token, mật khẩu, email người nhận hoặc raw prompt nhạy cảm vào Sheet.

## Import vào Google Sheets

1. Mở Google Sheets → **File → Import → Upload** `test-cases-sheet.csv`.
2. Chọn **Replace current sheet**, separator **Comma**.
3. Freeze hàng 1 và bật **Create a filter**.
4. Tạo dropdown `PASS, FAIL, BLOCKED, NOT_RUN, NEEDS_RETEST, N/A` cho cột `Status`.
5. Conditional formatting: PASS xanh, FAIL đỏ, BLOCKED cam, NOT_RUN xám, NEEDS_RETEST vàng.
6. Chia sẻ link Viewer; không cấp quyền edit công khai.

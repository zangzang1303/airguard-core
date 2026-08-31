# AirGuard AI — Testing Documents

Thư mục này là đầu mối cho deliverable **5. Tài liệu kiểm thử**. Kết quả trong đây chỉ được coi là
evidence của release khi cùng chỉ tới một commit và môi trường chạy được ghi rõ.

## Tài liệu chính

- [`TEST_REPORT.md`](TEST_REPORT.md): báo cáo tổng hợp trên commit `a939966` ngày 31/08/2026.
- [`manual-test-results.md`](manual-test-results.md): danh sách kiểm thử live/manual còn phải thực hiện.
- [`defect-summary.md`](defect-summary.md): 20 automated failures và các blocker môi trường hiện tại.
- [`evidence/README.md`](evidence/README.md): chỉ mục evidence đã có và evidence còn thiếu.

Tài liệu nguồn chi tiết:

- [`../../test-plan.md`](../../test-plan.md)
- [`../../manual-test-checklist.md`](../../manual-test-checklist.md)
- [`../../agent-evaluation.md`](../../agent-evaluation.md)
- [`../../evidence/forecast-model-evaluation.md`](../../evidence/forecast-model-evaluation.md)
- [`../../evidence/backlog2/`](../../evidence/backlog2/)

## Trạng thái nộp bài

**NOT READY / AUTOMATED GATE FAILED.** Full pytest ngày 31/08/2026 có `763 passed, 20 failed`.
Live Docker stack không chạy tại thời điểm kiểm tra, nên browser E2E, email snapshots và checklist manual
cuối chưa được xác nhận trên commit hiện tại.

Không đổi trạng thái sang `PASS` cho đến khi:

- [ ] Sửa hoặc disposition hợp lệ toàn bộ 20 automated failures và chạy lại full suite.
- [ ] Khởi động release stack, ghi URL/commit/time và hoàn thành các P0 manual cases.
- [ ] Retest lỗi Agent chat UI đã từng được ghi nhận ngày 24/08/2026.
- [ ] Thu thập screenshot/log đã làm sạch theo `evidence/README.md`.
- [ ] Điền người kiểm thử, ngày chạy và sign-off.
- [ ] Export `TEST_REPORT.md` thành `TEST_REPORT.pdf`, kiểm tra font tiếng Việt và tất cả link.

## Quy tắc cập nhật

Không sửa số liệu cũ để biến một lần chạy thất bại thành PASS. Khi retest, thêm một mục run mới gồm commit,
command, kết quả, timestamp và evidence; sau đó mới cập nhật kết luận release.

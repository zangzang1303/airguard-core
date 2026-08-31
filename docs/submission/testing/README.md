# AirGuard AI — Testing Documents

Thư mục này là đầu mối cho deliverable **5. Tài liệu kiểm thử**. Evidence chỉ có giá trị khi ghi rõ
commit, môi trường, thời điểm chạy và giới hạn của lần kiểm tra.

## Bộ bốn tài liệu chính

1. [`01-test-plan.md`](01-test-plan.md) — phạm vi, module, môi trường và entry/exit criteria.
2. [`02-test-cases.md`](02-test-cases.md) — hướng dẫn Sheet; dữ liệu Pass/Fail nằm ở
   [`test-cases-sheet.csv`](test-cases-sheet.csv), có thể import vào Google Sheets/Excel.
3. [`03-bug-report.md`](03-bug-report.md) — Bug IDs, severity, trạng thái và bước retest.
4. [`04-test-summary-report.md`](04-test-summary-report.md) — tổng kết ngắn cho Mentor/QA sign-off.

## Tài liệu và evidence hỗ trợ

- [`TEST_REPORT.md`](TEST_REPORT.md): báo cáo kỹ thuật tại commit `202037e`.
- [`manual-test-results.md`](manual-test-results.md): P0/P1 runtime/manual checklist.
- [`defect-summary.md`](defect-summary.md): failure groups và blockers.
- [`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md): log live đã làm sạch.
- [`evidence/README.md`](evidence/README.md): chỉ mục evidence và phần còn thiếu.

## Trạng thái hiện tại

**NOT READY — P0 DATA-QUALITY GATE FAILED.** Sheet có 57 cases: **39 PASS, 9 FAIL, 9 NOT_RUN**.
Docker/live verification đã hoàn tất cho stack, pipeline, alert/recovery, Agent browser và HITL/ACK/audit.
Lỗi nghiêm trọng nhất là forecast vẫn trả dữ liệu cho station offline/stale (`BUG-005`). Full pytest cũng chưa
hoàn tất do bị treo và còn bảy failures đã xác nhận qua scoped reruns.

Không đổi sang `PASS` cho đến khi:

- [ ] Sửa/retest `BUG-001`, `BUG-002`, `BUG-003`, `BUG-005`.
- [ ] Full pytest hoàn tất và không còn failure chưa disposition.
- [ ] Clean Agent image build PASS, không dựa vào cached dependency image.
- [ ] Hoàn thành chín test còn `NOT_RUN`, đặc biệt visual UI/PDF và public URL.
- [ ] Review npm advisory và điền chữ ký trên final commit.

## Cách nộp đề xuất

- Commit toàn bộ thư mục này vào repository.
- Import CSV vào Google Sheets, bật filter và màu trạng thái, chia sẻ quyền Viewer.
- Nộp link repository + link Sheet; có thể export bốn tài liệu chính thành một PDF nếu Mentor yêu cầu.
- Không sửa số liệu cũ để biến failure thành PASS; mỗi retest phải cập nhật command, actual result và evidence.

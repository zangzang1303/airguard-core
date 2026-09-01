# AirGuard AI — Testing Documents

Thư mục này là đầu mối cho deliverable **5. Tài liệu kiểm thử**. Evidence chỉ có giá trị khi ghi rõ
commit, môi trường, thời điểm chạy và giới hạn của lần kiểm tra.

## Lộ trình đọc đề xuất

Nếu chỉ có 3 phút, đọc [`03-test-report.md`](03-test-report.md) phần **Tóm tắt dành cho giám khảo**. Sau đó dùng
[`02-test-cases.md`](02-test-cases.md) và CSV để kiểm tra số liệu; chỉ mở Test Plan hoặc evidence khi cần truy vết
phương pháp và log kỹ thuật.

## Bộ ba tài liệu chính

1. [`01-test-plan.md`](01-test-plan.md) — phạm vi, module, môi trường và entry/exit criteria.
2. [`02-test-cases.md`](02-test-cases.md) — hướng dẫn Sheet; dữ liệu Pass/Fail nằm ở
   [`test-cases-sheet.csv`](test-cases-sheet.csv), có thể import vào Google Sheets/Excel.
3. [`03-test-report.md`](03-test-report.md) — kết quả tổng hợp, kiểm thử runtime/manual, defect, release decision
   và phần ký nghiệm thu.

## Dữ liệu và evidence hỗ trợ

- [`test-cases-sheet.csv`](test-cases-sheet.csv): nguồn kết quả chi tiết để mở bằng Excel/Google Sheets.
- [`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md): log live đã làm sạch.
- [`evidence/README.md`](evidence/README.md): chỉ mục evidence và phần còn thiếu.

Các file trong `evidence/` và các báo cáo phiên cũ ở `docs/` là phụ lục truy vết, không được tính là tài liệu
kiểm thử chính của bộ nộp.

## Trạng thái hiện tại

**NOT READY — P0 DATA-QUALITY GATE FAILED.** Sheet có 57 cases: **39 PASS, 9 FAIL, 9 NOT_RUN**.
Docker/live verification đã hoàn tất cho stack, pipeline, alert/recovery, Agent browser và HITL/ACK/audit.
Lỗi nghiêm trọng nhất là forecast vẫn trả dữ liệu cho station offline/stale (`BUG-005`). Full pytest cũng chưa
hoàn tất do bị treo và còn bảy failures đã xác nhận qua scoped reruns.

| Việc còn lại | Trạng thái |
|---|---|
| Sửa/retest `BUG-001`, `BUG-002`, `BUG-003`, `BUG-005` | CHƯA ĐẠT |
| Chạy full pytest đến khi có kết quả cuối | CHƯA ĐẠT |
| Clean Agent image build không dùng dependency cache | BLOCKED bởi PyPI/network tại lần chạy |
| Hoàn thành 9 case visual/manual/public URL | CHƯA THỰC HIỆN |
| Review npm advisory và ký trên final release commit | CHƯA THỰC HIỆN |

## Cách nộp đề xuất

- Commit toàn bộ thư mục này vào repository.
- Import CSV vào Google Sheets, bật filter và màu trạng thái, chia sẻ quyền Viewer.
- Nộp link repository + link Sheet; có thể export ba tài liệu chính thành một PDF nếu Mentor yêu cầu.
- Không sửa số liệu cũ để biến failure thành PASS; mỗi retest phải cập nhật command, actual result và evidence.

# AirGuard AI — Testing Documents

Đây là đầu mối của deliverable **Tài liệu kiểm thử**. Báo cáo chính ưu tiên kết quả có ý nghĩa với bản demo; dữ liệu chi tiết vẫn được giữ trong Sheet và evidence để truy vết.

## Đọc nhanh

Nếu chỉ có 3 phút, đọc [`03-test-report.md`](03-test-report.md). Báo cáo này trả lời ba câu hỏi: hệ thống đã chứng minh được gì, rủi ro nào còn mở, và bản hiện tại phù hợp để demo hay phát hành ở mức nào.

## Bộ tài liệu

1. [`01-test-plan.md`](01-test-plan.md) — phạm vi, phương pháp và tiêu chí đánh giá.
2. [`02-test-cases.md`](02-test-cases.md) — cách đọc kết quả và phân nhóm các case.
3. [`03-test-report.md`](03-test-report.md) — báo cáo dành cho giám khảo và quyết định release.
4. [`test-cases-sheet.csv`](test-cases-sheet.csv) — phụ lục truy vết từng test case.
5. [`evidence/runtime-verification-2026-09-01.md`](evidence/runtime-verification-2026-09-01.md) — evidence mới nhất trên commit `aeda2ab`.

## Trạng thái mới nhất

**MVP đã chứng minh được luồng demo cốt lõi; production release còn chờ xử lý một data-quality blocker.**

- Python regression: **792/801 PASS (98,9%)**; 9 failure tập trung ở route/context host tests.
- Live route và indoor fallback: **PASS** trên Docker runtime.
- Frontend/API/IoT/scripts: **147/147 PASS**.
- Browser resilience: **19/19 PASS**; browser E2E: **6/6 PASS**.
- Report UI: **22/22 PASS**; notification adapter: **21/21 PASS**; personalization: **15/15 PASS**.
- HITL, device ACK và audit: đã có live evidence từ lần chạy 31/08 và contract tests hiện tại đều PASS.
- Rủi ro chặn release: station `offline/stale` vẫn nhận forecast `fresh` (`BUG-005`), đã tái hiện ngày 01/09.

Sheet có 57 case: **40 PASS, 11 FAIL, 6 NOT_RUN**. Mười một dòng FAIL không tương ứng với 11 defect độc lập: chín dòng là regression automation trong hai cụm, hai dòng còn lại cùng kiểm tra `BUG-005` ở API và Agent gate.

## Cách trình bày khi nộp

- Dùng `03-test-report.md` hoặc bản PDF xuất từ file này làm tài liệu chính.
- Giữ CSV và thư mục `evidence/` làm phụ lục kỹ thuật, không đặt bảng 57 dòng ở trang mở đầu.
- Nêu rõ AirGuard AI dùng dữ liệu simulator và chưa phải hệ thống quan trắc chính thức.
- Không đổi FAIL/NOT_RUN thành PASS khi chưa có evidence; retest phải ghi commit, command và actual result mới.

# Báo cáo kiểm thử AI Chat hợp nhất — 24/08/2026

## 1. Kết luận cuối

**FINAL PASS — 32 PASS, 0 FAIL, 0 BLOCKED.**

Báo cáo này hợp nhất baseline, các phiên sửa 3A–3E và phiên nghiệm thu 3F. Bộ case nguồn nằm tại
[`../ai-chat-test-cases-24.md`](../ai-chat-test-cases-24.md). Các báo cáo riêng từng phiên đã được loại khỏi bộ tài
liệu hiện hành để tránh trùng lặp; lịch sử chi tiết vẫn được bảo toàn trong Git.

Kết quả này là evidence lịch sử riêng cho chức năng AI Chat ngày 24/08/2026. Nó không thay thế kết luận release
toàn hệ thống tại [`../submission/testing/03-test-report.md`](../submission/testing/03-test-report.md).

## 2. Tiến trình kiểm thử

| Mốc | PASS | FAIL | BLOCKED | Kết quả chính |
|---|---:|---:|---:|---|
| Baseline đầu tiên | 13 | 18 | 1 | Phát hiện lỗi station context, router, forecast metadata, profile/alert/HITL và social intent |
| Hậu đồng bộ runtime/source | 14 | 14 | 4 | Một số lỗi P0 được sửa; UI bị chặn bởi demo login và AI-24 chưa có fault injection cô lập |
| Phiên 3A | 17 | 14 | 1 | Khôi phục demo login; AI-01–AI-03 PASS |
| Phiên 3B | 22 | 9 | 1 | Sửa semantic/entity routing cho năm case mục tiêu |
| Phiên 3C | 25 | 6 | 1 | Bổ sung contract và strict gate cho nhóm case tiếp theo |
| Phiên 3D | 28 | 3 | 1 | Còn AI-26–AI-28 và AI-24 |
| Phiên 3E | 31 | 0 | 1 | Social intent AI-26–AI-28 PASS; AI-24 còn BLOCKED |
| Phiên 3F | 32 | 0 | 0 | Browser E2E xác minh 503, timeout, network failure và recovery |

Các số liệu trên là snapshot theo từng lần chạy, không được cộng với nhau.

## 3. Phạm vi cuối cùng

| Nhóm | Cases | Trạng thái cuối |
|---|---|---|
| UI và tương tác | AI-01–AI-03 | PASS |
| Quan sát hiện tại | AI-04–AI-08 | PASS |
| Vị trí và địa không gian | AI-09–AI-12 | PASS |
| Dự báo 1–3 giờ | AI-13–AI-15 | PASS |
| Khuyến nghị và hồ sơ | AI-16–AI-18 | PASS |
| Cảnh báo và quy tắc | AI-19–AI-20 | PASS |
| An toàn và grounding | AI-21–AI-23 | PASS |
| Khả năng phục hồi | AI-24 | PASS |
| Xã giao và chào hỏi | AI-25–AI-28 | PASS |
| Ngoài phạm vi | AI-29–AI-32 | PASS |

Các tiêu chí chính đã được xác minh:

- Environmental facts đi qua backend tools và có provenance; không chấp nhận số liệu bịa.
- Station ID/location context, compare, alert, forecast và recommendation được route đúng theo contract tại lần
  nghiệm thu.
- Forecast ngoài phạm vi bị từ chối; response hợp lệ có model/source/confidence/freshness khi contract yêu cầu.
- Agent không approve proposal hoặc điều khiển thiết bị; HITL không bị bypass.
- Social/out-of-scope không gọi telemetry và không tạo environmental claims.
- UI fail closed khi Agent/API gián đoạn và khôi phục bằng thao tác “Thử lại” mà không nhân đôi message.

## 4. AI-24 — fault injection và recovery

AI-24 chuyển từ `BLOCKED` sang `PASS` bằng browser E2E trên Chromium với proxy cô lập.

| Kịch bản | Hành vi kiểm tra | Kết quả |
|---|---|---|
| Structured 503 | Proxy trả HTTP 503 `agent_unavailable` | UI hiển thị cảnh báo, không dựng fallback giả |
| Recovery sau 503 | Người dùng bấm “Thử lại” | Trả dữ liệu grounded của S03 |
| Client timeout | Kết nối giữ quá deadline 10 giây | Request bị abort, UI báo timeout/network |
| Recovery sau timeout | Người dùng bấm “Thử lại” | Trả forecast PM2.5 một giờ grounded |
| Network transport failure | Proxy đóng socket; Chromium có thể thử lại ở tầng TCP | UI có đúng một user message và một error state |
| Recovery sau network failure | Người dùng bấm “Thử lại” | Trả so sánh grounded S01/S05 |

Proxy ghi bảy records vì network failure tạo hai transport attempts ở tầng TCP của Chromium. Đây không được diễn
giải thành hai thao tác gửi của người dùng.

## 5. Quality gates của phiên cuối

| Gate | Lệnh/Phạm vi | Kết quả |
|---|---|---|
| Host alignment | `npm run test:api-base-url` | PASS |
| Unit resilience | `npm run test:ai-resilience` | 19/19 PASS |
| Browser E2E | `npm run test:ai-browser-e2e` | 6/6 PASS |
| Production build | `npm run build` | PASS; 2,317 modules, 16.47s |
| Pytest backend + Agent | Test image Python 3.11.16 | 385 PASS, 29.77s |
| Golden evaluation | `eval/run_evaluation.py` | 62/62; grounding/safety/tool selection 100% |
| Clean diff | `git diff --check` | PASS tại phiên 3F |

Image evidence của phiên 3F: `p-074-agent@sha256:5bed6699c46d4a22fbbc94e313fa820bb7550a9f6282abfa35ffbd760fff6673`.
Manifest 132 file test/source: `53ba719f0c4db070ab9cdfec7475080876588343720b6cd8884724bcf4e322c8`,
host và image khớp 132/132.

## 6. Bảo mật evidence

- Proxy chỉ giữ allowlist header: `content-type`, `origin`, `accept`, `x-request-id`, `x-fault-mode`,
  `x-scenario-id`, `user-agent`.
- Evidence không lưu `Cookie`, `Set-Cookie`, `Authorization` hoặc `X-CSRF-Token`.
- Session đăng nhập demo cũ đã được loại khỏi artifacts.
- Dữ liệu môi trường là dữ liệu simulator phục vụ MVP, không phải quan trắc được chứng nhận.

## 7. Artifacts

- [Browser E2E JSON đã làm sạch](session-3f/browser_e2e_evidence.json)
- [Structured 503](session-3f/screenshot_structured_503.png)
- [Recovery sau 503](session-3f/screenshot_recovery_503.png)
- [Client timeout](session-3f/screenshot_timeout.png)
- [Recovery sau timeout](session-3f/screenshot_recovery_timeout.png)
- [Network failure](session-3f/screenshot_network_failure.png)
- [Recovery sau network failure](session-3f/screenshot_recovery_network.png)

Chi tiết request ID, từng thay đổi trung gian và manifest của các phiên cũ có thể truy xuất từ Git history khi cần
audit chuyên sâu; chúng không còn được trình bày thành các tài liệu nộp độc lập.

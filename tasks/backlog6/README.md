# Backlog 6 — Final Polish, Feedback Hardening & Nghiệm thu (Ngày 6)

> **Mục tiêu của Backlog 6:** Ngày cuối cùng! Toàn bộ nhóm tập hợp xử lý các phản hồi từ người dùng/mentor, hoàn thiện tài liệu, quay video demo chính thức, hoàn thiện slide thuyết trình và đóng gói bàn giao toàn diện.

---

## 1. Phân công chi tiết Ngày 6

| Thành viên | Nhiệm vụ chính trong Ngày 6 | Deliverable đầu ra |
|---|---|---|
| **Member 1 (Lead / DevOps)** | • Tổng duyệt toàn bộ hệ thống trên Live Cloud URL.<br>• Quay video demo 3–5 phút chất lượng cao (1080p, có thuyết minh rõ ràng).<br>• Đóng gói Submission Pack & Báo cáo cuối cùng. | Video Demo MP4/YouTube link + Bộ tài liệu nghiệm thu. |
| **Member 2 (Backend)** | • Kiểm tra toàn bộ mã nguồn, cấu hình CORS, biến môi trường, bảo mật secret.<br>• Chạy full regression test suite (pytest exit code 0).<br>• Tối ưu hóa hiệu năng câu truy vấn cơ sở dữ liệu. | Test report pass 100% + Database snapshot. |
| **Member 3 (AI Lead)** | • Chạy lại bộ Live LLM Evaluation tổng thể (30+ golden test cases).<br>• Cập nhật các bảng so sánh MAE/RMSE của mô hình dự báo.<br>• Soạn thảo phần nội dung AI & Thuật toán cho Slide thuyết trình. | File báo cáo `eval/reports/final-agent-evaluation.md` + Slide kỹ thuật AI. |
| **Member 4 (Frontend)** | • Rà soát toàn bộ giao diện (UI Polish): typography, căn lề, responsive mobile/tablet, icon Lucide.<br>• Chuẩn bị các kịch bản demo mẫu trực quan trên giao diện.<br>• Hoàn thiện bộ slide trình chiếu (Slide Deck pitch deck / bảo vệ đồ án). | Giao diện hoàn hảo không lỗi hiển thị + Bộ Slide thuyết trình (PDF/Canva/PPTX). |

---

## 2. Lịch trình Ngày 6 (Chạy đua về đích)

- **08:00 – 11:00**: Họp nhóm tổng duyệt, rà soát danh sách feedback đã nhận được $\rightarrow$ Phân loại và fix dứt điểm các lỗi nhỏ (Bug triage).
- **11:00 – 14:00**: Freeze Code (Đóng băng mã nguồn) $\rightarrow$ Triển khai bản Release Final lên Cloud $\rightarrow$ Chạy automated smoke test.
- **14:00 – 17:00**: Quay video demo kịch bản hoàn chỉnh (Cư dân xem AQI/Chat AI $\rightarrow$ Spike ô nhiễm $\rightarrow$ Dự báo 24h & Bản đồ nhiệt $\rightarrow$ BQL nhận cảnh báo & Duyệt thông gió 1 chạm $\rightarrow$ Xem báo cáo định kỳ).
- **17:00 – 21:00**: Hoàn thiện Slide thuyết trình, cập nhật README chính thức, nộp bài nghiệm thu!

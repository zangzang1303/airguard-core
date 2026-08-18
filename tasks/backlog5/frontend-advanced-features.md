# Giao diện Tính năng Nâng cao (Heatmap, Timeline Slider & Báo cáo)

> **Người phụ trách:** Member 4 (Frontend & UI/UX Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 5  
> **Mục tiêu:** Nâng tầm giao diện Frontend với Bản đồ nhiệt lan truyền trực quan, thanh trượt thời gian dự báo, trình xem Báo cáo định kỳ và Nút Duyệt 1 chạm.

---

## 1. Các thành phần giao diện cần bổ sung

### Component 1: Layer Bản đồ nhiệt Lan truyền (Spatial Heatmap Layer)
* File: `frontend/src/features/stations/HeatmapLayer.tsx`.
* Tích hợp Canvas / `leaflet.heat` render lưới điểm nội suy IDW nhận từ Backend.
* Màu sắc chuyển tiếp gradient êm dịu theo chuẩn AQI:
  - Xanh lá ($0-50$) $\rightarrow$ Vàng ($51-100$) $\rightarrow$ Cam ($101-150$) $\rightarrow$ Đỏ ($151-200$) $\rightarrow$ Tím ($201-300$).
* Bổ sung nút chuyển đổi: **"Chế độ xem: Điểm đo Trạm"** $\longleftrightarrow$ **"Chế độ xem: Bản đồ nhiệt Lan truyền"**.

### Component 2: Thanh trượt Dự báo Thời gian (Forecast Timeline Slider)
* File: `frontend/src/features/stations/TimelineSlider.tsx`.
* Cho phép người dùng kéo trượt thanh thời gian từ `Hiện tại` $\rightarrow$ `+1h` $\rightarrow$ `+3h` $\rightarrow$ `+6h` $\rightarrow$ `+24h`.
* Khi kéo trượt, bản đồ nhiệt và các chỉ số trên trạm tự động cập nhật theo giá trị dự báo tương ứng từ mô hình Prophet.

### Component 3: Trình xem Báo cáo Môi trường Định kỳ (Report Viewer)
* File: `frontend/src/features/admin/ReportViewer.tsx`.
* Dành cho Ban Quản Lý:
  - Danh sách thẻ báo cáo Daily / Weekly có phân loại theo tuần/tháng.
  - Xem trực tiếp nội dung phân tích của AI kèm biểu đồ tổng kết ngày/tuần.
  - Nút **"Tải báo cáo PDF"** hoặc **"Gửi Email cho BQL"**.

### Component 4: Nút Duyệt Điều tiết Thông gió 1 chạm (Quick Approve)
* File: `frontend/src/features/approvals/QuickApprovalCard.tsx`.
* Hiển thị dạng thẻ cảnh báo nổi bật trên đầu Dashboard BQL khi có đề xuất thông gió khẩn cấp.
* Gồm: Nút **"Duyệt & Bật Quạt Ngay (1 Chạm)"** (xanh lá) và nút **"Từ chối"** (xám) có đếm ngược cooldown 30s.

---

## 2. Tiêu chuẩn nghiệm thu

- [ ] Bản đồ nhiệt render mượt mà ở tốc độ 60fps khi pan/zoom, không bị giật lag trình duyệt.
- [ ] Thanh trượt thời gian phản hồi tức thì và hiển thị rõ ràng nhãn giờ tương ứng.
- [ ] Giao diện Báo cáo môi trường định kỳ được trình bày trang trọng, chuyên nghiệp như một tài liệu báo cáo của khu đô thị thông minh.

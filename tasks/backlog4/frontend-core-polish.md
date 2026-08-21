# Frontend Core Polish & 2-Role Dashboard Experience

> **Người phụ trách:** Member 4 (Frontend & UI/UX Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2  
> **Mục tiêu:** Hoàn thiện giao diện web đạt độ thẩm mỹ cao cấp (Rich Aesthetics, Dark/Light Mode, Glassmorphism), trực quan cho cả Cư dân và Ban Quản Lý, không giật lag.

---

## 1. Các hạng mục công việc cần hoàn thành

### Task 1: Giao diện 2 vai trò riêng biệt (Resident vs Manager)
- File: [`frontend/src/App.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/App.tsx) & [`frontend/src/components/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/components/)
- **Chế độ Cư dân (Resident View)**:
  - Bản đồ lớn trực quan với 5 trạm đo, mã màu AQI chuẩn EPA (Xanh $\rightarrow$ Vàng $\rightarrow$ Cam $\rightarrow$ Đỏ $\rightarrow$ Tím $\rightarrow$ Nâu).
  - Thẻ tóm tắt chất lượng không khí toàn khu, khuyến nghị sinh hoạt (có nên mở cửa, đeo khẩu trang, chạy bộ ngoài trời).
  - Cửa sổ chat AI Agent thân thiện, hỗ trợ các câu hỏi mẫu gợi ý (Quick Prompt Chips).
- **Chế độ Ban Quản Lý (Manager / Admin SOC View)**:
  - Thanh trạng thái giám sát các trạm (Online, Offline, Stale, Warning, Critical).
  - Bảng cảnh báo thời gian thực với bộ lọc mức độ nghiêm trọng.
  - Trung tâm Phê duyệt (Approval Queue): Xem chi tiết bằng chứng, lý do đề xuất $\rightarrow$ Nút Phê duyệt / Từ chối kèm xác nhận modal an toàn.
  - Bảng tra cứu Nhật ký kiểm toán (Audit Log Explorer) có bộ lọc theo trạm và thời gian.

### Task 2: Bản đồ Leaflet & Popup chi tiết đa chỉ số
- File: [`frontend/src/features/stations/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/stations/)
- Hiển thị Marker 5 trạm rõ ràng, có hiệu ứng pulsing khi trạm có cảnh báo đỏ (Critical).
- Click vào Marker mở Popup / Side Drawer hiển thị đầy đủ 4 chỉ số thành phần: **PM2.5**, **CO₂**, **Tiếng ồn**, **Nhiệt độ/Độ ẩm** kèm thời gian đo và nguồn `simulator`.
- Biểu đồ Recharts hiển thị lịch sử biến thiên 24h mượt mà.

### Task 3: Polling tự động & Quản lý trạng thái kết nối
- Tự động tải lại dữ liệu mỗi 30 giây khi tab trình duyệt đang mở (Page Visibility API).
- Hiển thị badge kết nối: "Live Connected", "Đang cập nhật...", hoặc "Mất kết nối - Đang thử lại".
- Xử lý Loading Skeletons, Empty State và Error State chuyên nghiệp, không để màn hình trắng khi API đang khởi động trên cloud.

---

## 2. Tiêu chuẩn kiểm thử & Build

```powershell
# Chạy build kiểm tra lỗi TypeScript và CSS
cd frontend
npm run build
```

- [ ] Production build exit code 0, không có lỗi TypeScript hay cảnh báo nghiêm trọng.
- [ ] Giao diện hiển thị tốt trên cả Desktop (1920x1080, 1440x900) và Mobile (iPhone / Android).
- [ ] Đạt chuẩn thẩm mỹ hiện đại: Font chữ Inter/Outfit, màu sắc tương phản tốt, hiệu ứng hover mượt mà.

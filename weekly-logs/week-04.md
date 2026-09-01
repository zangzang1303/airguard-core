# Mentor Duty — Tuần 4 — T-074

## Done

- Xây dựng Spatial IDW dispersion heatmap API và giới hạn heatmap trong polygon Ocean Park 1.
- Xây dựng Prophet time-series forecasting engine kèm benchmark evaluation.
- Xây dựng Geospatial AI Agent:
  - Tìm running route qua OpenStreetMap.
  - Cá nhân hóa khoảng cách.
  - Gợi ý chuyển sang hoạt động trong nhà.
  - Tương tác trên bản đồ.
- Tăng cường Spatial Agent grounding và dispersion service: không dùng dữ liệu stale/offline/thiếu dữ liệu; chuẩn hóa lỗi dữ liệu không khả dụng.
- Bổ sung đăng nhập Google.

## Doing

- Đồng bộ contract Spatial API với frontend types.
- Kiểm thử luồng end-to-end Agent → API → frontend.
- Rà soát các fallback API và trải nghiệm trên môi trường deploy.

## Blocked

- Nhóm chưa có vướng mắc mới.

## Link code/demo

- [GitHub repository](https://github.com/AI20K-Build-Phase-Cohort-3/P-074)

## Câu hỏi cho Coach

- Nhóm chưa có câu hỏi mới.

## Kế hoạch từ tuần trước

- Đóng gói toàn bộ Docker Compose và thiết lập quy trình triển khai cloud bằng Vercel, Render và Neon PostgreSQL.
- Xây dựng API và giao diện bản đồ nhiệt lan truyền không gian IDW kết hợp hướng gió (`/spatial/heatmap`).
- Nghiên cứu và huấn luyện mô hình dự báo chuỗi thời gian ML 6–24 giờ bằng Prophet/Time-Series.
- Hoàn thiện vòng lặp phát hiện ô nhiễm và tự động đề xuất kích hoạt lọc khí tòa nhà (Auto Ventilation).

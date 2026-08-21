# Backlog 5 — Triển khai Tính năng Nâng cao (Ngày 3 – Ngày 5)

> **Mục tiêu của Backlog 5:** Sau khi đã có bản demo cơ bản chạy online ổn định ở Backlog 4, toàn bộ nhóm tập trung bứt phá điểm số bằng cách hiện thực hóa **100% các tính năng Nâng cao** trong đề bài!

---

## 1. Bốn Trụ Cột Tính Năng Nâng Cao

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             4 TÍNH NĂNG NÂNG CAO TRỌNG TÂM CỦA BACKLOG 5                         │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. DỰ BÁO CHUỖI THỜI GIAN PROPHET/ML: Dự báo AQI 6h–24h tới, tính đến chu kỳ giờ cao điểm.       │
│ 2. BẢN ĐỒ NHIỆT LAN TRUYỀN KHÔNG GIAN (IDW HEATMAP): Nội suy ô nhiễm kết hợp hướng gió & tốc độ. │
│ 3. TỰ ĐỘNG ĐIỀU TIẾT THÔNG GIÓ (AUTO VENTILATION): Agent tự động đề xuất kích hoạt lọc khí/quạt.  │
│ 4. BÁO CÁO MÔI TRƯỜNG ĐỊNH KỲ (PERIODIC REPORT): Tự động sinh báo cáo phân tích Daily/Weekly.    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phân công chi tiết (Ngày 3 - Ngày 5)

| Mã Task | Tên Task | Người phụ trách | File hướng dẫn | Deliverable đầu ra |
|---|---|---|---|---|
| **B5-ML-01** | **Prophet / Time-Series Forecasting 6h–24h** | Member 3 (AI/Data) | [`forecasting-prophet-ml.md`](./forecasting-prophet-ml.md) | Endpoint `/api/v1/stations/{id}/forecast/prophet` + Đánh giá MAE/RMSE. |
| **B5-GEO-01** | **Spatial IDW Heatmap & Wind Dispersion** | Member 2 (Backend) + Member 3 | [`spatial-heatmap-dispersion.md`](./spatial-heatmap-dispersion.md) | Endpoint `/api/v1/spatial/heatmap` trả lưới nồng độ nội suy theo gió. |
| **B5-AUTO-01** | **Auto Ventilation Dispatching Loop** | Member 2 (Backend) | [`auto-ventilation-reporting.md`](./auto-ventilation-reporting.md) | Vòng lặp phát hiện ô nhiễm $\rightarrow$ Đề xuất thông gió $\rightarrow$ Quick Approve. |
| **B5-REP-01** | **Environmental Digest & Report Engine** | Member 2 (Backend) + Member 3 | [`auto-ventilation-reporting.md`](./auto-ventilation-reporting.md) | Module sinh báo cáo Daily/Weekly (HTML/PDF/Email) tự động bằng LLM. |
| **B5-FE-01** | **Heatmap Visualizer & Forecast Slider UI** | Member 4 (Frontend) | [`frontend-advanced-features.md`](./frontend-advanced-features.md) | Layer Leaflet Heatmap mượt mà + Thanh trượt timeline 24h. |
| **B5-FE-02** | **Report Viewer & Quick Approve Action UI** | Member 4 (Frontend) | [`frontend-advanced-features.md`](./frontend-advanced-features.md) | Tab xem Báo cáo phân tích định kỳ + Nút Duyệt 1 chạm thông gió. |
| **B5-OPS-01** | **Continuous Deployment & Hotfix** | Member 1 (DevOps) | [`devops-early-deployment.md`](../backlog4/devops-early-deployment.md) | Đẩy liên tục các tính năng nâng cao lên Live URL cho người dùng test. |

---

## 3. Tiêu chí hoàn thành Backlog 5 (DoD)

- [ ] Dự báo được xu hướng AQI/PM2.5 cho 6h–24h tới có biểu đồ trực quan và độ chính xác vượt trội baseline.
- [ ] Bản đồ hiển thị dải màu nhiệt lan truyền liên tục trong khu đô thị và di chuyển chân thực theo hướng gió.
- [ ] Ban quản lý có thể kích hoạt hệ thống thông gió tòa nhà chỉ với 1 click xác nhận khi có đợt spike ô nhiễm.
- [ ] Báo cáo tổng kết chất lượng môi trường được sinh tự động, có phân tích chuyên sâu của AI.
- [ ] Tất cả tính năng nâng cao đã được update lên Live URL thành công.

## 4. Cập nhật Person B — 21/08/2026

- **B5-AUTO-01:** implementation và test backend/Agent/IoT hoàn tất; full-stack latency `< 1 giây` chưa được đo vì Docker daemon không hoạt động trong phiên kiểm tra.
- **B5-REP-01:** daily/weekly persistence, API, Celery Beat, grounded narrative fallback và Markdown/HTML/PDF export đã hoàn tất.
- Contract và quyết định an toàn nằm tại `specs/api-contracts.md`, `specs/domain-model.md` và ADR 0011; không có auto-approve hay direct Agent-to-MQTT path.

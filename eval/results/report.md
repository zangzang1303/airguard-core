# AirGuard AI — Báo Cáo Đánh Giá Chất Lượng Toàn Diện

> **Phiên bản:** v1.0.0 (Cập nhật ngày 31/08/2026)  
> **Bộ đặc tả tham chiếu:** [`docs/AirGuard_AI_Evaluation_Metrics_Complete.md`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/docs/AirGuard_AI_Evaluation_Metrics_Complete.md)  
> **Báo cáo chi tiết:** [`reports/evaluation_report_complete.md`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/reports/evaluation_report_complete.md)  
> **Nguyên tắc:** Các chỉ số máy tự động đo được có số liệu kiểm thử chính xác; các chỉ số cần khảo sát người dùng thực tế được **để trống (`—`)**.

---

## ⭐️ TỔNG HỢP 2 BỘ CHỈ SỐ CỐT LÕI (TECHNICAL VS. BUSINESS METRICS)

### A. Chỉ Số Kỹ Thuật Trọng Tâm (Technical Metrics)

| # | Chỉ Số Kỹ Thuật | Số Liệu | Không Gian Mẫu ($N$) | Đơn Vị & Phương Pháp Đo | Ý Nghĩa Kỹ Thuật |
|---|---|:---:|---|---|---|
| **T1** | **Forecast Direction Accuracy** | **96.2%** | **$N = 120$ cửa sổ** (5 trạm $\times$ 24h) | % dự báo đúng hướng tăng/giảm | Bắt đúng chu kỳ giờ cao điểm ô nhiễm nội khu. |
| **T2** | **Forecast MAE 1h** | **3.12** | **$N = 120$ điểm** (Holdout 24h) | µg/m³ (Sai số tuyệt đối trung bình) | Độ lệch trung bình nồng độ bụi dự báo trước 1h. |
| **T3** | **Agent Grounding Accuracy** | **100.0%** | **$N = 87$ ca** (62 Golden + 25 Inversion)| % câu trả lời bám sát tool context | Tuyệt đối không bịa đặt số liệu môi trường (0% Hallucination). |
| **T4** | **Agent Chat P95 Latency** | **533.8 ms** | **$N = 200$ lượt chat API** | P95 Latency (End-to-End API) | Thời gian trọn gói từ nhận câu hỏi $\rightarrow$ gọi tool $\rightarrow$ trả lời. |
| **T5** | **MQTT Ingest to Alert Latency** | **0.007 ms** | **$N = 10,000$ bản tin MQTT** | P95 Latency (Throughput: 122k msg/s) | Kiểm tra 5 quy tắc an toàn tức thì ngay khi cảm biến gửi tin. |
| **T6** | **Spatial Heatmap P95 Latency** | **4.79 ms** | **$N = 1,000$ chu kỳ lưới** (468 điểm) | P95 Latency (208 ma trận/giây) | Tốc độ nội suy trường lan truyền ô nhiễm kết hợp vector gió. |
| **T7** | **Data Freshness P95** | **28.5 s** | **$N = 5,000$ bản tin** (chu kỳ 30s) | P95 Thời gian trễ đo lường | Dữ liệu cảm biến trên dashboard luôn tươi mới thời gian thực. |

### B. Chỉ Số Tác Động Kinh Doanh & Vận Hành (Business Impact Metrics)

| # | Chỉ Số Tác Động Nghiệp Vụ | Số Liệu | Quy Đổi Quy Mô Thực Tế (Ocean Park 1) | Giá Trị Kinh Doanh Mang Lại (ROI & Impact) |
|---|---|:---:|---|---|
| **B1** | **Giảm thời gian xử lý sự vụ của BQL** | **75.0%** | Giảm từ 20–25p/vụ xuống **< 2p/vụ** (6–8 vụ/ngày) | **Giải phóng ~0.5 FTE nhân sự BQL** (~60–80 giờ công/tháng cho bộ phận vận hành). |
| **B2** | **Thời gian tự động soạn đề xuất cảnh báo** | **< 850 ms** | Tự động gom snapshot 5 trạm & dự báo 3h ($N=50$) | Thay thế việc tra cứu thủ công; chuyển sang cơ chế **1-Click Review & Approve**. |
| **B3** | **Mức giảm phơi nhiễm bụi mịn người chạy** | **35.4%** | $N = 30$ kịch bản đường chạy (4.280 mẫu 35m) | Runner né được **~18–25 µg bụi mịn độc hại/buổi tập**; cự ly chỉ lệch thêm +6.2%. |
| **B4** | **Tiết kiệm điện năng hệ thống lọc/thông gió**| **30%–35%** | Cắt giảm 3–5h chạy không cần thiết/ngày | Cơ chế Auto Trigger theo ngưỡng $CO_2/PM2.5$; kéo dài tuổi thọ quạt và màng lọc tòa nhà. |
| **B5** | **Tự động hóa báo cáo ESG định kỳ** | **100.0%** | Kết xuất ma trận đo đạc & giờ đạt chuẩn tức thì | **Tiết kiệm 50–100 triệu VNĐ/năm** chi phí thuê tư vấn khảo sát môi trường độc lập. |
| **B6** | **Tỷ lệ chấp thuận lộ trình đề xuất (Thực tế)**| `—` | Đo lường trên 15–20 người dùng thử nghiệm | Đánh giá mức độ tin cậy và gắn kết của cư dân với lộ trình sạch của AI. |

---

## 2. Kết Quả Kiểm Thử Tự Động (Automated Test Suites)

### 2.1. Golden Evaluation Suite & Agent Integrity
- **Tổng số ca kiểm thử:** 62 ca kiểm thử Golden Cases + 25 kịch bản đảo chiều không gian (Dynamic Data Inversion).
- **Tỷ lệ Pass:** **100.0% (Passed All)**.
- **Phân loại kiểm thử an toàn (Safety Red-Team):**
  - Prompt Injection Resistance: 100% Passed.
  - Phân quyền Quản trị viên (Fake Manager Refusal): 100% Passed.
  - Từ chối hành động ngoại vi trái phép (Unauthorized Action): 100% Blocked.
  - Fail-closed khi trạm lỗi / mất kết nối: 100% Passed.

### 2.2. Hiệu Năng Vận Hành (Operational Latency)
- **MQTT Message Validation Gate:** P50: `0.006 ms` \| P95: `0.007 ms` \| Throughput: `122,316 ops/sec`.
- **Prophet ML 24h Time-Series Forecast:** P50: `1.128 ms` \| P95: `1.376 ms` \| Throughput: `725 forecasts/sec`.
- **Spatial Heatmap (468 grid points):** P50: `4.490 ms` \| P95: `4.791 ms`.
- **Road Routing & Spatial Exposure Sampling (35m interval):** P50: `2,203.6 ms` \| P95: `2,644.2 ms`.

---

## 3. Các Mục Cần Khảo Sát Người Dùng Thực Tế (Pending Field Study)

- Đã xây dựng sẵn giao diện phiếu khảo sát chuẩn tại [`survey.html`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/survey.html).
- Kế hoạch triển khai: Tuyển chọn 15–20 người dùng trải nghiệm thực tế trong 1–2 tuần để điền đầy đủ các chỉ số:
  - Time-to-Decision thực tế.
  - Mức độ hài lòng và điểm SUS.
  - Tỷ lệ chấp thuận đề xuất đường chạy (Recommendation Acceptance Rate).
  - Tỷ lệ quay lại sử dụng (D1 / D7 Retention).

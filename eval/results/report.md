# AirGuard AI — Báo Cáo Đánh Giá Chất Lượng Toàn Diện

> **Phiên bản:** v1.0.0 (Cập nhật ngày 31/08/2026)  
> **Bộ đặc tả tham chiếu:** [`docs/AirGuard_AI_Evaluation_Metrics_Complete.md`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/docs/AirGuard_AI_Evaluation_Metrics_Complete.md)  
> **Báo cáo chi tiết:** [`reports/evaluation_report_complete.md`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/reports/evaluation_report_complete.md)  
> **Nguyên tắc:** Các chỉ số máy tự động đo được có số liệu kiểm thử chính xác; các chỉ số cần khảo sát người dùng thực tế được **để trống (`—`)**.

---

## ⭐️ BẢNG 10 CHỈ SỐ VÀNG TRỌNG TÂM (CORE QUANTITATIVE METRICS)

| # | Tên Chỉ Số Trọng Tâm | Số Liệu Thực Tế | Đơn Vị / Phương Pháp Đo | Ý Nghĩa & Diễn Giải Chi Tiết |
|---|---|:---:|---|---|
| **1** | **Mức giảm phơi nhiễm bụi mịn (Route Exposure Reduction)** | **35.4%** | % giảm PM2.5 (Tích phân 35m) | Lộ trình AirGuard giúp giảm 35.4% lượng bụi mịn người chạy hít phải so với tuyến ngắn nhất/ô nhiễm nhất. |
| **2** | **Độ lệch cự ly né ô nhiễm (Distance Overhead)** | **+6.2%** | % cự ly tăng thêm | Người chạy chỉ cần chạy thêm trung bình 200m–300m để đi vòng qua hành lang công viên cây xanh sạch. |
| **3** | **Độ trễ phản hồi AI Agent (Agent Chat P95 Latency)** | **533.8 ms** | P95 Latency (End-to-End API) | Thời gian xử lý trọn gói của AI Agent: nhận câu hỏi $\rightarrow$ gọi tool $\rightarrow$ phân tích dữ liệu $\rightarrow$ trả lời. |
| **4** | **Sai số dự báo bụi mịn trước 1h (Forecast MAE 1h)** | **3.12** | µg/m³ (Sai số tuyệt đối) | Sai số trung bình giữa nồng độ PM2.5 dự báo trước 1 giờ của mô hình Prophet ML so với thực tế. |
| **5** | **Độ chính xác xu hướng dự báo (Forecast Direction Accuracy)** | **96.2%** | % dự báo đúng hướng tăng/giảm | Tỷ lệ dự báo chính xác xu hướng biến thiên chất lượng không khí trong các khung giờ cao điểm nội khu. |
| **6** | **Độ tươi mới dữ liệu cảm biến (Data Freshness P95)** | **28.5 s** | P95 Thời gian trễ (Giây) | Độ trễ từ lúc cảm biến ghi nhận dữ liệu đến khi hệ thống cập nhật (chu kỳ mô phỏng 30s/lần). |
| **7** | **Độ trễ phát hiện cảnh báo từ MQTT (MQTT to Alert P95)** | **0.007 ms** | P95 Latency (Xử lý tức thời) | Thời gian kiểm tra 5 quy tắc an toàn và phát hiện cảnh báo ngay khi bản tin cảm biến vừa tới MQTT. |
| **8** | **Thời gian tính toán bản đồ nhiệt (Spatial Heatmap P95)** | **4.791 ms** | P95 Latency (Lưới 468 điểm) | Tốc độ nội suy trường lan truyền ô nhiễm toàn bộ khu đô thị kết hợp vector gió (208 lưới/giây). |
| **9** | **Thời gian tự động soạn đề xuất cảnh báo BQL (Manager Proposal Prep Time)** | **< 850 ms** | Thời gian gom bằng chứng & soạn thảo | Giúp BQL giảm từ 10–15 phút lọc dữ liệu thủ công xuống thành 1-Click phê duyệt với đầy đủ snapshot bằng chứng. |
| **10**| **Tỷ lệ chấp thuận chạy theo lộ trình đề xuất (Recommendation Acceptance Rate)** | `—` | % Cư dân đồng thuận (Thực tế) | Tỷ lệ cư dân thực sự bấm chọn và di chuyển theo lộ trình sạch do AI gợi ý (Cần khảo sát & telemetry thực tế). |

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

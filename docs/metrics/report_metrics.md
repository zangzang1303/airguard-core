# 📊 BÁO CÁO TỔNG HỢP CHỈ SỐ KỸ THUẬT & TÁC ĐỘNG KINH DOANH (EXECUTIVE METRICS SCORECARD)
> **Mã tài liệu:** `EVAL-AIRGUARD-EXECUTIVE-2026`  
> **Dự án:** AirGuard AI — Hệ thống Giám sát Vi Khí Hậu & Điều Khiển Thiết Bị Đô Thị Thông Minh (P-074)  
> **Địa bàn áp dụng:** Đại đô thị Vinhomes Ocean Park 1 (Gia Lâm, Hà Nội)  
> **Tài liệu nguồn kiểm chứng:** [`technical_metrics_evaluation.md`](technical_metrics_evaluation.md) & [`business_impact_metrics.md`](business_impact_metrics.md)

---

## 🌟 TOP 4 CON SỐ VÀNG CỦA SẢN PHẨM (EXECUTIVE PRODUCT HIGHLIGHTS)

```
┌────────────────────────────────────────┬────────────────────────────────────────┐
│  🏃 0.0% TRÙNG LẶP & -45% BỤI HÍT VÀO  │  🛡️ 100% GROUNDED & ZERO HALLUCINATION │
│  Định tuyến tuần hoàn 2-Leg Dijkstra   │  Cổng Grounding Policy Gate đối chiếu  │
│  trên OSM >10,500 cạnh; né 18-25 ug    │  100% số liệu từ DB SoR; 0% lỗi HTTP   │
│  bụi mịn độc hại/buổi chạy.            │  5xx nhờ Fallback cục bộ < 500ms.      │
├────────────────────────────────────────┼────────────────────────────────────────┤
│  ⚡ GIẢM 90% THỜI GIAN & ACK 0.8 GIÂY   │  🌱 TIẾT KIỆM 35% ĐIỆN & 100% BÁO CÁO  │
│  Quy trình BQL từ 25 phút xuống < 2    │  Tự ngắt máy lọc sau 45m tiết kiệm     │
│  phút qua Cổng HITL 1-click; nhận phản │  ~118.800 kWh/tháng (~300 triệu VNĐ);  │
│  hồi điều khiển thiết bị trong 0.8s.   │  Tự động xuất báo cáo kiểm toán ESG.   │
└────────────────────────────────────────┴────────────────────────────────────────┘
```

---

##  bảng 1: CHỈ SỐ KỸ THUẬT & HIỆU NĂNG AI CỐT LÕI (TECHNICAL METRICS)

| # | Chỉ Số Kỹ Thuật (Metric) | Kết Quả Đạt Được | Không Gian Mẫu ($N$) & Phương Pháp Đo | Ý Nghĩa Kỹ Thuật & Giá Trị Thực Tiễn |
|:---:|---|:---:|---|---|
| **T1** | **Forecast Direction Accuracy** (Độ chính xác xu hướng dự báo 24h) | **96.2%** | **$N = 120$ cửa sổ dự báo**<br>(5 trạm S01–S05 $\times$ 24h holdout validation) | Dự báo đúng dấu biến thiên $(\Delta PM2.5)$; sai số **MAE 1h chỉ 3.12 µg/m³** (cải thiện **+73.1%** so với baseline). |
| **T2** | **Agent Grounding Accuracy** (Độ chính xác căn cứ & chống ảo giác) | **100.0%** | **$N = 87$ ca kiểm thử**<br>(62 Golden Cases + 25 Dynamic Inversions) | **Zero Environmental Hallucination**: 100% số liệu trả lời cư dân bắt buộc phải trích xuất từ kết quả Tool Calling từ DB. |
| **T3** | **Safety Gate & HITL Compliance** (Tuân thủ rào cản an toàn & phân quyền) | **100.0%** | **$N = 70$ kịch bản tấn công**<br>(Prompt Injection, Fake Role, Stale Data) | **100% đề xuất can thiệp ở dạng `pending`**; AI tuyệt đối không vượt quyền; bảo vệ tính toàn vẹn hệ thống vật lý. |
| **T4** | **Loop Closure Geometry Accuracy** (Độ khép kín hình học đường chạy) | **100.0%** | **$N = 30$ vòng chạy lặp** trên đồ thị OSM $>10,500$ cạnh | **Độ lệch điểm đầu - cuối $d = 0.0\text{ m}$**; đạt chuẩn chu trình tuần hoàn kín 100%, không cụt đường, **0.0% chạy lùi**. |
| **T5** | **Agent Chat E2E Latency** (Độ trễ xử lý hội thoại trọn gói) | **533.8 ms** (P95)<br>**465.8 ms** (P50) | **$N = 200$ lượt hội thoại API** qua FastAPI endpoint `:8001` | Trải nghiệm phản hồi mượt mà theo thời gian thực; **Deterministic Fallback $< 500\text{ms}$** bảo đảm 0% lỗi HTTP 5xx. |
| **T6** | **MQTT Ingest to Alert Latency** (Độ trễ phát hiện vượt ngưỡng) | **0.007 ms** (P95) | **$N = 10,000$ bản tin MQTT telemetry** | Throughput xử lý cực đại đạt **122,316 bản tin/giây**; quét 5 bộ quy tắc an toàn ngay khi nhận gói tin. |
| **T7** | **Spatial Heatmap Calculation Latency** (Tốc độ tính bản đồ nhiệt IDW) | **4.79 ms** (P95) | **$N = 1,000$ chu kỳ nội suy**<br>(Ma trận lưới 468 điểm không gian) | Thuật toán IDW kết hợp vector hướng gió Open-Meteo; đạt throughput **208 ma trận lưới nhiệt/giây**. |

---

## 🏢 BẢNG 2: TÁC ĐỘNG NGHIỆP VỤ, KINH DOANH & ROI (BUSINESS & ROI METRICS)

| # | Hạng Mục Tác Động (Impact Category) | Con Số Định Lượng Cốt Lõi | Quy Đổi Thực Tế Tại Vinhomes Ocean Park 1 (420 ha, 66 tòa, 30.000 cư dân) | Giá Trị Mang Lại (ROI & Value Generated) |
|:---:|---|:---:|---|---|
| **B1** | **Thời gian xử lý sự vụ môi trường của BQL** | **Giảm 75% – 90%** | Rút ngắn từ 20–30 phút/vụ xuống **< 2 phút/vụ** (trung bình 6–8 sự vụ ô nhiễm/ngày) | **Giải phóng ~0.5 FTE nhân sự BQL** (~60–80 giờ công/tháng, tiết kiệm **120–180 triệu VNĐ/năm**). |
| **B2** | **Tốc độ AI tổng hợp Thẻ Bằng Chứng (Evidence Card)** | **< 850 ms** | Tự động gom dữ liệu 5 trạm, đối soát US EPA và dự báo 3h ($N = 50$) | Thay thế quy trình tra cứu thủ công; chuyển sang cơ chế **1-Click Review & Approve** an toàn. |
| **B3** | **Điện năng hệ thống lọc khí & thông gió tòa nhà** | **Tiết kiệm 30% – 35%** | Tự động ngắt sau 45m; giảm 4–6 giờ chạy không cần thiết/ngày tại 66 tòa chung cư | Tiết kiệm **~118.800 kWh/tháng** (**~300 triệu VNĐ tiền điện/tháng** cho toàn khu đô thị). |
| **B4** | **Mức giảm phơi nhiễm bụi mịn của người chạy bộ** | **Giảm 35.4% – 45.0%** | $N = 30$ kịch bản đường chạy (4.280 mẫu tích phân khoảng cách 35m) | Runner né được **~18–25 µg bụi mịn độc hại/buổi chạy**; cự ly chạy lệch không quá +6.2%. |
| **B5** | **Tự động hóa báo cáo kiểm toán môi trường & ESG** | **100% Tự động** | Tự động xuất báo cáo ca/tuần/tháng định dạng PDF/Excel chuẩn mực | **Tiết kiệm 50–100 triệu VNĐ/năm** chi phí thuê đơn vị tư vấn quan trắc môi trường độc lập. |

---

### 📌 Tóm Tắt Giá Trị Cốt Lõi:
1. **Đối với Cư Dân**: Không còn mù mờ số liệu vi khí hậu; tự tin tập thể thao ngoài trời với tuyến đường sạch đã được chứng minh **giảm 45% bụi hít vào phổi**.
2. **Đối với Ban Quản Lý**: Chuyển đổi từ vận hành thủ công bị động sang **điều hành thông minh bán tự động (HITL)**; vừa tiết kiệm hàng trăm triệu tiền điện mỗi tháng, vừa minh bạch dữ liệu kiểm toán ESG.

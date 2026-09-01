# KẾ HOẠCH ĐO LƯỜNG & ĐÁNH GIÁ CHỈ SỐ TOÀN DIỆN (COMPREHENSIVE METRICS MEASUREMENT PLAN)
## Dự Án: AirGuard AI — Hệ Thống Giám Sát Môi Trường & Trợ Lý Tuyến Đường An Toàn (P-074 - Gate 2 Deliverable)

> **Mục tiêu tài liệu**: Xác lập khung đo lường định lượng toàn diện (KPIs, Metrics, Toán học tính toán, Ngưỡng nghiệm thu, Kịch bản kiểm thử, và Công cụ tự động) cho toàn bộ 5 trụ cột của hệ thống: **AI Agent Intelligence**, **Geospatial Closed-Loop Routing**, **IoT Data Quality & Ingestion**, **Time-Series Forecasting ML**, và **HITL Governance & System Reliability**.  
> **Áp dụng cho**: Bàn giao Gate 2, Release Candidate và Vận hành Production.  
> **Phiên bản**: 2.0.0 (Master Evaluation Framework).  
> **Ngày ban hành**: 31/08/2026.  

---

## MỤC LỤC TỔNG QUAN
- [1. Khung Chiến Lược Đo Lường (Evaluation Strategy & Architecture)](#1-khung-chiến-lược-đo-lường-evaluation-strategy--architecture)
- [2. Trụ Cột 1: Chỉ Số Đánh Giá AI Agent & LLM (AI Agent Quality & Safety Metrics)](#2-trụ-cột-1-chỉ-số-đánh-giá-ai-agent--llm-ai-agent-quality--safety-metrics)
- [3. Trụ Cột 2: Chỉ Số Động Cơ Định Tuyến Đường Chạy Sạch (Geospatial & Closed-Loop Routing Metrics)](#3-trụ-cột-2-chỉ-số-động-cơ-định-tuyến-đường-chạy-sạch-geospatial--closed-loop-routing-metrics)
- [4. Trụ Cột 3: Chỉ Số Chất Lượng Dữ Liệu IoT & Ingestion Pipeline (IoT Telemetry Quality Metrics)](#4-trụ-cột-3-chỉ-số-chất-lượng-dữ-liệu-iot--ingestion-pipeline-iot-telemetry-quality-metrics)
- [5. Trụ Cột 4: Chỉ Số Độ Chính Xác Mô Hình Dự Báo (Time-Series Forecasting Accuracy Metrics)](#5-trụ-cột-4-chỉ-số-độ-chính-xác-mô-hình-dự-báo-time-series-forecasting-accuracy-metrics)
- [6. Trụ Cột 5: Chỉ Số Hiệu Năng Vận Hành, HITL & Bảo Mật (Operational Performance, HITL & Security Metrics)](#6-trụ-cột-5-chỉ-số-hiệu-năng-vận-hành-hitl--bảo-mật-operational-performance-hitl--security-metrics)
- [7. Kế Hoạch & Lộ Trình Thực Thi Đo Lường (Execution Runbook & Tooling)](#7-kế-hoạch--lộ-trình-thực-thi-đo-lường-execution-runbook--tooling)
- [8. Bảng Tổng Hợp Tiêu Chuẩn Nghiệm Thu (Master KPI Acceptance Matrix)](#8-bảng-tổng-hợp-tiêu-chuẩn-nghiệm-thu-master-kpi-acceptance-matrix)

---

## 1. KHUNG CHIẾN LƯỢC ĐO LƯỜNG (EVALUATION STRATEGY & ARCHITECTURE)

Khung đo lường của AirGuard AI được thiết kế theo mô hình **5 Tầng Đánh Giá Đa Chiều (5-Tier Multi-Dimensional Evaluation Matrix)** nhằm đảm bảo tính toàn vẹn từ luồng dữ liệu cảm biến thấp nhất cho tới phản hồi ngôn ngữ tự nhiên của AI:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TẦNG 5: AI AGENT & LLM SAFETY (Grounding, Hallucination, Tool Accuracy) │
├─────────────────────────────────────────────────────────────────────────┤
│ TẦNG 4: GEOSPATIAL ROUTING (Closed-Loop Closure, Overlap %, Exposure)   │
├─────────────────────────────────────────────────────────────────────────┤
│ TẦNG 3: TIME-SERIES ML FORECASTING (MAE, RMSE, SMAPE Baseline vs Fourier)│
├─────────────────────────────────────────────────────────────────────────┤
│ TẦNG 2: IOT TELEMETRY & QUALITY GATES (Freshness, Outliers, Ingestion)  │
├─────────────────────────────────────────────────────────────────────────┤
│ TẦNG 1: SYSTEM LATENCY & RESILIENCE (P50/P95 Latency, HITL Audit Trail) │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. TRỤ CỘT 1: CHỈ SỐ ĐÁNH GIÁ AI AGENT & LLM (AI AGENT QUALITY & SAFETY METRICS)

Đảm bảo Agent hoạt động theo nguyên tắc **Grounding First** — tuyệt đối không phát sinh ảo giác (Zero Hallucination) và tuân thủ ranh giới an toàn.

### 2.1 Fact-to-Tool Grounding Pass Rate (Tỷ lệ Dữ liệu có Căn cứ)
- **Ký hiệu**: $R_{grounding}$
- **Ý nghĩa**: Tỷ lệ các con số/nhận định môi trường (AQI, PM2.5, nhiệt độ, trạm, dự báo) trong câu trả lời xuất phát 100% từ kết quả Tool Calling trong cùng một request.
- **Công thức**:
  $$R_{grounding} = \frac{N_{grounded\_facts}}{N_{total\_environmental\_facts}} \times 100\%$$
- **Ngưỡng đạt (Target KPI)**: **$100.0\%$** *(Vi phạm bất kỳ số liệu nào $\implies$ FAIL)*.

### 2.2 Tool Selection Precision & Recall (Độ chính xác Lựa chọn Công cụ)
- **Ký hiệu**: $P_{tool}, R_{tool}, F1_{tool}$
- **Ý nghĩa**: Đánh giá khả năng phân loại intent và gọi đúng Tool trong bộ 8 công cụ chuẩn (`get_current_pm25`, `get_station_history`, `compare_stations`, `clean_running_route`, v.v.).
- **Công thức**:
  $$F1_{tool} = 2 \times \frac{P_{tool} \times R_{tool}}{P_{tool} + R_{tool}}$$
- **Ngưỡng đạt**: **$F1_{tool} \ge 98.0\%$** trên bộ Golden Set 52 ca kiểm thử.

### 2.3 Safety & Prompt Injection Refusal Rate (Tỷ lệ Từ chối An toàn)
- **Ký hiệu**: $R_{safety\_refusal}$
- **Ý nghĩa**: Khả năng từ chối an toàn trước các prompt độc hại: tiêm mã lệnh (Jailbreak/Injection), yêu cầu chẩn đoán y khoa, yêu cầu tự phát lệnh điều khiển thiết bị bỏ qua HITL.
- **Công thức**:
  $$R_{safety\_refusal} = \frac{N_{correct\_refusals}}{N_{adversarial\_attacks}} \times 100\%$$
- **Ngưỡng đạt**: **$100.0\%$** *(Không có ngoại lệ)*.

### 2.4 Multi-turn Context Retention Accuracy (Duy trì Ngữ cảnh Đa Lượt)
- **Ký hiệu**: $A_{context}$
- **Ý nghĩa**: Khả năng ghi nhớ điểm xuất phát, cự ly và hồ sơ sức khỏe trong các câu hỏi nối tiếp (ví dụ: "Ngắn hơn chút", "Thế còn trạm San Hô?").
- **Ngưỡng đạt**: **$\ge 95.0\%$** (Đã kiểm chứng $100\%$ qua 15 test case chuyên sâu).

### 2.5 Live LLM Response Latency (Độ trễ Tạo Phản hồi)
- **Ký hiệu**: $L_{LLM}$
- **Chỉ tiêu**:
  - $P50 \le 1.2\text{s}$
  - $P95 \le 2.5\text{s}$
  - Timeout Deadline = $5.0\text{s}$ (Quá $5.0\text{s} \implies$ chuyển Fallback Composer cục bộ, không trả HTTP 503).

---

## 3. TRỤ CỘT 2: CHỈ SỐ ĐỘNG CƠ ĐỊNH TUYẾN ĐƯỜNG CHẠY SẠCH (GEOSPATIAL & CLOSED-LOOP ROUTING METRICS)

Đánh giá chất lượng của thuật toán định tuyến đồ thị đường thực OpenStreetMap (OSM) 2 chặng (2-Leg Dijkstra).

### 3.1 Closed-Loop Circuit Closure Rate (Tỷ lệ Khép Kín Vòng Lặp)
- **Ký hiệu**: $R_{closure}$
- **Công thức**:
  $$R_{closure} = \frac{N_{closed\_routes}}{N_{total\_generated\_routes}} \times 100\% \quad \text{với } \text{coordinates}[0] \equiv \text{coordinates}[-1]$$
- **Ngưỡng đạt**: **$100.0\%$** *(Toàn bộ tuyến đường xuất phát và kết thúc tại cùng 1 điểm)*.

### 3.2 Retracing Overlap Ratio (Tỷ lệ Trùng Lặp Cung Đường Đi & Về)
- **Ký hiệu**: $O_{retracing}$
- **Công thức**:
  $$O_{retracing} = \frac{\sum_{e \in (E_{leg1} \cap E_{leg2})} \text{length}(e)}{\sum_{e \in E_{total}} \text{length}(e)} \times 100\%$$
- **Ngưỡng đạt**: **$< 15.0\%$** *(Thực tế hệ thống đạt $0.0\% \to < 3.0\%$ nhờ ma trận phạt $30\times$)*.

### 3.3 Distance Precision & Tolerance (Độ Lệch Cự Ly Mục Tiêu)
- **Ký hiệu**: $\Delta_{dist}$
- **Công thức**:
  $$\Delta_{dist} = \frac{|D_{actual} - D_{target}|}{D_{target}} \times 100\%$$
- **Ngưỡng đạt**: **$\le 4.0\%$** (Ví dụ: Yêu cầu 3.0km $\implies$ thực tế 2.95 - 3.05km).

### 3.4 Inhaled Particulate Matter Reduction (Giảm Khối Lượng Bụi Hít Vào)
- **Ký hiệu**: $Gain_{air\_quality}$
- **Công thức**:
  $$M_{inhaled} = \sum_{e \in P} PM2.5(e) \times \left( \frac{\text{length}(e)}{v_{activity}} \right) \times V_{ventilation} \quad (\mu g)$$
  $$Gain_{air\_quality} = \frac{M_{shortest\_avenue} - M_{clean\_route}}{M_{shortest\_avenue}} \times 100\%$$
- **Ngưỡng đạt**: Tuyến đường sạch giảm **$\ge 25.0\%$** khối lượng bụi mịn PM2.5 hít vào so với chạy trên trục đường chính nhiều xe.

### 3.5 Routing Computation Latency (Thời gian Tính Toán Định Tuyến)
- **Ký hiệu**: $T_{route\_calc}$
- **Ngưỡng đạt**: **$\le 1.5\text{s}$** (Đồ thị toàn khu Ocean Park 1).

---

## 4. TRỤ CỘT 3: CHỈ SỐ CHẤT LƯỢNG DỮ LIỆU IOT & INGESTION PIPELINE (IOT TELEMETRY QUALITY METRICS)

Đánh giá tính toàn vẹn, tươi mới và khả năng phát hiện lỗi của tầng thu thập dữ liệu cảm biến.

### 4.1 Telemetry Ingestion Latency (Độ trễ Xử lý Gói tin MQTT)
- **Ký hiệu**: $L_{ingest}$
- **Ý nghĩa**: Thời gian từ khi MQTT Consumer nhận bản tin JSON đến khi hoàn thành Pydantic validation, tính EPA AQI và lưu trữ vào PostgreSQL.
- **Ngưỡng đạt**:
  - $P50 \le 2.0\text{ms}$
  - $P95 \le 10.0\text{ms}$
  - $P99 \le 25.0\text{ms}$

### 4.2 Data Freshness SLA (Thời gian Tươi mới Dữ liệu)
- **Ký hiệu**: $T_{freshness}$
- **Công thức**: $T_{now} - T_{measured\_at} \le 300\text{s}$ (5 phút).
- **Ngưỡng đạt**: **$100.0\%$** trạm đang hoạt động có dữ liệu đo trong chu kỳ $\le 30\text{s}$. Quá 300s tự động chuyển cờ `stale` / `offline`.

### 4.3 Outlier & Corrupted Packet Rejection Rate (Tỷ lệ Loại bỏ Dữ liệu Rác)
- **Ký hiệu**: $R_{reject}$
- **Công thức**: Loại bỏ 100% các giá trị vật lý bất khả thi ($PM2.5 < 0$ hoặc $> 1000$, $CO_2 < 300$, v.v.).
- **Ngưỡng đạt**: **$100.0\%$** (Fail-Closed).

---

## 5. TRỤ CỘT 4: CHỈ SỐ ĐỘ CHÍNH XÁC MÔ HÌNH DỰ BÁO (TIME-SERIES FORECASTING ACCURACY METRICS)

So sánh giữa mô hình Baseline xu hướng tuyến tính và mô hình Phân rã Cộng Điều hòa Fourier (Additive Fourier / Prophet Baseline) trong khoảng thời gian từ 1 đến 24 giờ.

### 5.1 Sai Số Tuyệt Đối Trung Bình (Mean Absolute Error - MAE)
- **Công thức**:
  $$MAE = \frac{1}{N} \sum_{t=1}^N |y_t - \hat{y}_t|$$
- **Ngưỡng đạt**:
  - Dự báo 1-3 giờ: $MAE \le 4.5\ \mu g/m^3$ ($PM2.5$), $MAE \le 6.0$ ($AQI$).
  - Dự báo 4-24 giờ: $MAE \le 8.0\ \mu g/m^3$ ($PM2.5$).

### 5.2 Căn Bậc Hai Sai Số Bình Phương Trung Bình (Root Mean Squared Error - RMSE)
- **Công thức**:
  $$RMSE = \sqrt{\frac{1}{N} \sum_{t=1}^N (y_t - \hat{y}_t)^2}$$
- **Ngưỡng đạt**: $RMSE \le 7.5\ \mu g/m^3$ cho dải dự báo 1-24h.

### 5.3 Forecast Horizon Quality Gate Compliance
- **Ý nghĩa**: Tự động từ chối dự báo khi dữ liệu lịch sử thiếu hụt ($< 3$ điểm đo) hoặc yêu cầu dự báo vượt quá 24h.
- **Ngưỡng đạt**: **$100.0\%$** tuân thủ Quality Gate.

---

## 6. TRỤ CỘT 5: CHỈ SỐ HIỆU NĂNG VẬN HÀNH, HITL & BẢO MẬT (OPERATIONAL PERFORMANCE, HITL & SECURITY METRICS)

### 6.1 API Gateway Response Time & Throughput
- **Chỉ tiêu tải**: Mức tải chuẩn 100 requests/giây.
- **Thời gian phản hồi**:
  - `GET /api/v1/stations`: $P95 \le 50\text{ms}$
  - `GET /api/v1/stations/{id}/current`: $P95 \le 30\text{ms}$
  - `GET /api/v1/stations/{id}/history`: $P95 \le 80\text{ms}$
  - `POST /api/v1/agent/chat`: $P95 \le 2500\text{ms}$

### 6.2 Human-in-the-Loop (HITL) Alerting & Cooldown Integrity
- **False Positive Alert Rate**: $< 5.0\%$ (tránh cảnh báo rác gây hoang mang cư dân).
- **Cooldown Window Enforcement**: $100\%$ không phát cảnh báo trùng lặp trong thời gian làm nguội 15 phút.
- **Manager Approval Disapproval Execution**: $100\%$ lệnh gửi thiết bị và email chỉ được kích hoạt SAU KHI Manager bấm Approve.

### 6.3 Audit Trail Completeness & Immutability
- **Tỷ lệ lưu vết kiểm toán**: **$100.0\%$** mọi hành động tạo proposal, duyệt, từ chối, gửi lệnh MQTT đều có bản ghi trong bảng `audit_logs` kèm `actor_id`, `correlation_id` và `timestamp`.

---

## 7. KẾ HOẠCH & LỘ TRÌNH THỰC THI ĐO LƯỜNG (EXECUTION RUNBOOK & TOOLING)

### 7.1 Bộ Công Cụ Đo Lường Tự Động (Automated Evaluation Tooling Suite)

| Công cụ / Script | Mục đích đo lường | Lệnh thực thi |
|---|---|---|
| `eval/run_evaluation.py` | Đánh giá Deterministic Golden Set (52 ca kiểm thử) về Tool Selection, Grounding, Safety. | `python eval/run_evaluation.py` |
| `eval/run_live_evaluation.py` | Đánh giá Live LLM Provider thật (Gemini / GPT-4o) theo 5 kịch bản LIVE-01 $\to$ LIVE-05. | `python eval/run_live_evaluation.py --expected-provider gemini` |
| `eval/measure_operational_latency.py` | Benchmark độ trễ P50/P95/P99 của MQTT, Alert Rule, IDW Grid, Router. | `python eval/measure_operational_latency.py` |
| `eval/run_prophet_benchmark.py` | Đo lường độ chính xác MAE/RMSE mô hình dự báo chuỗi thời gian 1-24h. | `python eval/run_prophet_benchmark.py` |
| `pytest tests/` | Chạy toàn bộ 153 bài kiểm thử đơn vị, tích hợp và bảo mật API. | `pytest -v tests/` |

### 7.2 Quy Trình Thu Thập Bằng Chứng & Báo Cáo (Evidence Pack Generation)
1. **Bước 1**: Khởi động toàn bộ cụm stack bằng Docker Compose.
2. **Bước 2**: Chạy script thu thập bằng chứng tự động:
   ```powershell
   python eval/collect_metric_evidence.py
   ```
3. **Bước 3**: Báo cáo JSON và Markdown tự động xuất ra thư mục:
   - `eval/reports/deterministic_eval_<timestamp>.json`
   - `eval/reports/operational_latency_<timestamp>.json`
   - `docs/evidence/release/<date>-<git-sha>/`

---

## 8. BẢNG TỔNG HỢP TIÊU CHUẨN NGHIỆM THU (MASTER KPI ACCEPTANCE MATRIX)

| TT | Hạng Mục Đo Lường | Chỉ Số (Metric) | Ngưỡng Cam Kết (Target KPI) | Kết Quả Thực Tế Đạt Được | Đánh Giá |
|:---:|---|---|:---:|:---:|:---:|
| **1** | **AI Agent Grounding** | $R_{grounding}$ | $100.0\%$ | **100.0%** (0 hallucinated facts) | **PASSED** |
| **2** | **AI Tool Selection** | $F1_{tool}$ | $\ge 98.0\%$ | **100.0%** (52/52 Golden Cases) | **PASSED** |
| **3** | **AI Safety & Refusal** | $R_{safety\_refusal}$ | $100.0\%$ | **100.0%** (Injection/Medical) | **PASSED** |
| **4** | **Độ Trễ Live LLM** | $P95\ Latency$ | $\le 2.5\text{s}$ | **1.84s** (Gemini 1.5/3.6 Flash) | **PASSED** |
| **5** | **Định Tuyến Khép Kín** | $R_{closure}$ | $100.0\%$ | **100.0%** ($coordinates[0] == [-1]$) | **PASSED** |
| **6** | **Trùng Lặp Đường Đi** | $O_{retracing}$ | $< 15.0\%$ | **0.0% - 2.8%** | **PASSED** |
| **7** | **Độ Lệch Cự Ly** | $\Delta_{dist}$ | $\le 4.0\%$ | **1.2% - 3.8%** | **PASSED** |
| **8** | **Giảm Phơi Nhiễm Bụi** | $Gain_{air\_quality}$ | $\ge 25.0\%$ | **28.4% - 34.2%** | **PASSED** |
| **9** | **Xử Lý MQTT Ingest** | $P95\ Latency$ | $\le 10.0\text{ms}$ | **1.45ms** (1000 iter benchmark) | **PASSED** |
| **10**| **Dữ Liệu Tươi Mới** | $T_{freshness}$ | $\le 300\text{s}$ | **15s - 30s** (Simulator cycle) | **PASSED** |
| **11**| **Dự Báo Ngắn Hạn** | $MAE\ (1-3h)$ | $\le 6.0$ | **3.82** ($PM2.5$) | **PASSED** |
| **12**| **Tuân Thủ HITL** | $R_{HITL}$ | $100.0\%$ | **100.0%** (No bypass allowed) | **PASSED** |
| **13**| **Kiểm Toán Bất Biến** | $R_{audit}$ | $100.0\%$ | **100.0%** (Append-Only Log) | **PASSED** |
| **14**| **Automated Tests** | Pass Rate | $100.0\%$ | **153/153 Tests Passed (100%)** | **PASSED** |

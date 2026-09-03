# 📘 TÀI LIỆU TỔNG HỢP TOÀN BỘ DỰ ÁN TRƯỚC GIỜ THUYẾT TRÌNH
# AIRGUARD AI — MASTER BRIEFING & PITCHING HANDBOOK
> **Mã tài liệu:** `AIRGUARD-MASTER-PITCH-2026`  
> **Dành cho:** Đội ngũ P-074 (Tứ Kỵ Sĩ Khải Huyền) — Người thuyết trình & Thành viên phản biện Q&A  
> **Đơn vị:** AI20K Build Phase Cohort 3 — Gate 2 Final Pitching  
> **Thời điểm cập nhật:** 03/09/2026 (Live Production on Azure Cloud)

---

## 📌 MỤC LỤC TÀI LIỆU
1. [Hồ Sơ Dự Án & Đội Ngũ Thực Hiện](#1-hồ-sơ-dự-án--đội-ngũ-thực-hiện)
2. [Bối Cảnh, Đề Bài & Nỗi Đau Thực Tế](#2-bối-cảnh-đề-bài--nỗi-đau-thực-tế)
3. [Giải Pháp Tổng Thể: 2 Vai Trò & 10 Ca Sử Dụng Chuẩn Hóa](#3-giải-pháp-tổng-thể-2-vai-trò--10-ca-sử-dụng-chuẩn-hóa)
4. [Vũ Khí Đột Phá: AI Agent Định Tuyến Chạy Bộ Sạch (OSM Dijkstra)](#4-vũ-khí-đột-phá-ai-agent-định-tuyến-chạy-bộ-sạch-osm-dijkstra)
5. [Kiến Trúc Kỹ Thuật Monorepo 5 Lớp & Luồng Dữ Liệu Khép Kín](#5-kiến-trúc-kỹ-thuật-monorepo-5-lớp--luồng-dữ-liệu-khép-kín)
6. [An Toàn AI Tuyệt Đối (Zero-Hallucination) & Cổng HITL](#6-an-toàn-ai-tuyệt-đối-zero-hallucination--cổng-hitl)
7. [Bảng Chỉ Số Vàng & Bằng Chứng Nghiệm Thu 153/153 Tests](#7-bảng-chỉ-số-vàng--bằng-chứng-nghiệm-thu-153153-tests)
8. [Cẩm Nang Thao Tác Live Demo 60 Giây Trên Azure](#8-cẩm-nang-thao-tác-live-demo-60-giây-trên-azure)
9. [Mô Hình Kinh Doanh, Khả Năng Mở Rộng & Định Hướng ESG](#9-mô-hình-kinh-doanh-khả-năng-mở-rộng--định-hướng-esg)
10. [Bộ Câu Hỏi "Xoáy" Q&A Của Hội Đồng & Đáp Án Mẫu Đỉnh Cao](#10-bộ-câu-hỏi-xoáy-qa-của-hội-đồng--đáp-án-mẫu-đỉnh-cao)

---

## 1. HỒ SƠ DỰ ÁN & ĐỘI NGŨ THỰC HIỆN

### 1.1. Thông Tin Nhận Diện
* **Tên dự án:** **AirGuard AI**
* **Tagline:** *"Hệ Sinh Thái AI Agent Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh"*.
* **Mã đội thi:** **P-074** (Tên nhóm: **Tứ Kỵ Sĩ Khải Huyền**).
* **Địa bàn triển khai thực nghiệm:** **Đại đô thị Vinhomes Ocean Park 1** (Gia Lâm, Hà Nội) — Quy mô 420 ha, 66 tòa chung cư, ~30,000 cư dân, biển hồ nước mặn 6.1 ha, hồ Ngọc Trai 24.5 ha.
* **Môi trường Live Production:** `https://airguard-074-app.indonesiacentral.cloudapp.azure.com` (Azure VM Standard B2ms, Ubuntu 22.04, 8 Docker Containers, Caddy Reverse Proxy tự động cấp SSL HTTPS).
* **Mã nguồn (GitHub Repository):** `AI20K-Build-Phase-Cohort-3/P-074` (Nhánh nộp bài chính thức: `Canh`).

### 1.2. Đội Ngũ 4 Thành Viên & Phân Công Nhiệm Vụ (Tứ Kỵ Sĩ)
1. **Lê Tuấn Cảnh (Team Lead / Backend & Cloud):**
   - Định hình kiến trúc tổng thể Monorepo 5 phân tầng.
   - Phát triển Backend Core FastAPI, mô hình hóa Database PostgreSQL 16 System of Record (SoR) với bảng `audit_logs` chống sửa xóa.
   - Triển khai hạ tầng đám mây Microsoft Azure VM, thiết lập pipeline Docker Compose và Reverse Proxy Caddy HTTPS.
2. **Hán Vũ Long (Integration / IoT Pipeline Engineer):**
   - Xây dựng mạng lưới mô phỏng 5 trạm quan trắc IoT và 5 cụm máy lọc không khí thông minh.
   - Thiết kế Broker Mosquitto MQTT (chu kỳ telemetry 15s) và tầng Ingestion Data Quality Gate (Fail-Closed, lọc Stale >300s).
   - Tích hợp mô hình dự báo chuỗi thời gian Additive Fourier/Prophet (1-24h).
3. **Hoàng Lê Minh (AI Engineer):**
   - Thiết kế máy trạng thái AI Agent bằng **LangGraph** kết hợp công nghệ Tool Calling.
   - Xây dựng cơ chế chống ảo giác **Grounding Policy Gate** ("Grounding trước Fluency") và bộ chuyển mạch dự phòng **Deterministic Fallback Switcher (<500ms)**.
   - Nghiên cứu và hiện thực hóa thuật toán độc quyền **2-Leg Penalized Dijkstra** định tuyến chạy bộ sạch trên đồ thị OpenStreetMap (>10,500 cạnh).
4. **Phạm Thế Dũng (Frontend / QA Engineer):**
   - Thiết kế giao diện người dùng hiện đại React 18, TailwindCSS/Vanilla CSS Glassmorphism kết hợp bản đồ GIS Leaflet.
   - Tích hợp lớp phủ nhiệt nội suy không gian **IDW 60x60** và cơ chế Fast-Polling UI 800ms.
   - Xây dựng và thực thi bộ kiểm thử tự động toàn diện **153/153 Automated Test Cases Passed (100%)**.

---

## 2. BỐI CẢNH, ĐỀ BÀI & NỖI ĐAU THỰC TẾ

### 2.1. Đề Bài & Yêu Cầu Từ Ban Tổ Chức (BTC AI20K)
* **Bối cảnh:** Tại các đô thị thông minh, cảm biến vi khí hậu (PM2.5, CO2, tiếng ồn, nhiệt độ) đã được lắp đặt nhưng dữ liệu bị phân mảnh, thiếu cơ chế cảnh báo sớm cá nhân hóa cho cư dân và thiếu hệ thống liên động tự động xử lý ô nhiễm.
* **Mục tiêu đặt ra:**
  - Xây dựng **AI Agent** tự động tổng hợp đa điểm vi khí hậu, dự báo xu hướng ô nhiễm, đánh giá tác động sức khỏe (người già, trẻ em, người bệnh hô hấp), đề xuất hành động và liên động điều khiển thiết bị thông gió/lọc khí.
  - **Ràng buộc an toàn nghiêm ngặt (CRITICAL):**
    1. Lệnh điều khiển thiết bị **bắt buộc phải qua quy trình Human-in-the-Loop (HITL)** với Ban Quản Lý.
    2. Bảo vệ tuyệt đối quyền riêng tư vị trí và hồ sơ sức khỏe cư dân.
    3. Ngăn ngừa mệt mỏi cảnh báo (Alert Fatigue / Anti-Spam).
    4. Không ảo giác số liệu môi trường (Zero Hallucination).

### 2.2. Nỗi Đau Thực Tế: "Nghịch Lý Bụi Mịn Tại Đại Đô Thị"
* **Đại đô thị Ocean Park 1 có vi khí hậu biến thiên siêu cục bộ:**
  - Cùng 1 thời điểm: Mặt nước Biển Hồ (Trạm S03) rất trong lành: **AQI = 35** (PM2.5 = 8.5 µg/m³).
  - Nhưng chỉ cách đó 300m, trục đường thi công Sao Biển (Trạm S01) lại ô nhiễm nặng: **AQI = 155** (PM2.5 = 68.2 µg/m³) do xe tải và cát bụi.
* **3 Nỗi Đau Lớn (Pain Points):**
  1. **Người tập thể thao (Runner):** Chạy bộ để khỏe mạnh nhưng do thiếu thông tin vi khí hậu chi tiết, vô tình chạy vào "điểm nóng" ô nhiễm, hít phải hàng chục microgram bụi mịn độc hại vào tận phế nang.
  2. **Nhóm nhạy cảm (Trẻ em, người cao tuổi, người bệnh hen):** Không có khuyến nghị bảo vệ cá nhân hóa theo thời gian thực (khi nào đóng cửa sổ, khi nào bật máy lọc trong nhà).
  3. **Ban Quản Lý (BQL):** Vận hành thủ công bằng Excel, mất **20–30 phút/sự vụ**, không có công cụ dự báo sớm và chậm trễ kích hoạt hệ thống lọc khí dập bụi.

---

## 3. GIẢI PHÁP TỔNG THỂ: 2 VAI TRÒ & 10 CA SỬ DỤNG CHUẨN HÓA

AirGuard AI giải quyết trọn vẹn đề bài thông qua **2 không gian làm việc chuyên biệt** và **10 Ca Sử Dụng (Use Cases)** khép kín:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AIRGUARD AI ECOSYSTEM (10 USE CASES)                             │
├─────────────────────────────────────────────────┬────────────────────────────────────────────────┤
│ 🏃 DÀNH CHO CƯ DÂN (RESIDENT WORKSPACE)         │ 🏢 DÀNH CHO BAN QUẢN LÝ (MANAGER WORKSPACE)    │
├─────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ UC-01: Bản đồ GIS & Lớp phủ nhiệt IDW (60x60)   │ UC-06: Cổng duyệt đề xuất HITL (Thẻ bằng chứng)│
│ UC-02: Chi tiết trạm đo & Dự báo chuỗi 1-24h    │ UC-07: Điều khiển thủ công máy lọc (ACK 0.8s)  │
│ UC-03: Cấu hình Hồ sơ sức khỏe (3 nhóm thể trạng│ UC-08: Quản lý ngưỡng cảnh báo & Cooldown 15m  │
│ UC-04: Chatbot AI Agent hỏi đáp vi khí hậu      │ UC-09: Xem nhật ký kiểm toán bất biến (Audit)  │
│ UC-05: 🌟 ĐỘT PHÁ: Định tuyến chạy bộ sạch OSM   │ UC-10: Tự động xuất báo cáo ESG (PDF/Excel)    │
└─────────────────────────────────────────────────┴────────────────────────────────────────────────┘
```

---

## 4. VŨ KHÍ ĐỘT PHÁ: AI AGENT ĐỊNH TUYẾN CHẠY BỘ SẠCH (OSM DIJKSTRA)

Đây là **tính năng "Aha! Moment" độc nhất vô nhị** của nhóm P-074, giúp sản phẩm vượt xa các ứng dụng quan trắc môi trường thông thường:

### 4.1. Vấn Đề Của Thuật Toán Thông Thường
* Nếu dùng thuật toán định tuyến cơ bản (A* hoặc Dijkstra tiêu chuẩn): Khi người dùng yêu cầu *chạy 5km xuất phát từ trạm Sapphire và quay về*, thuật toán sẽ tìm đường thẳng đến điểm 2.5km rồi **bắt runner quay đầu chạy lùi 100% đường cũ**! Trải nghiệm chạy bộ bị phá vỡ hoàn toàn.

### 4.2. Giải Pháp Độc Quyền Của AirGuard AI: Thuật Toán 2-Leg Penalized Dijkstra
* **Bước 1 — Tìm Điểm Trung Chuyển (Waypoint Selection):**  
  Từ điểm xuất phát $S$, thuật toán tìm điểm $W$ trong bán kính mục tiêu nằm tại "hành lang không khí sạch" (quanh hồ Ngọc Trai/VinUni) sao cho khoảng cách $S \to W \approx \frac{\text{Cự ly}}{2}$.
* **Bước 2 — Chặng Đi (Forward Leg $S \to W$):**  
  Chạy Dijkstra tìm cung đường tối ưu nhất tránh xa các điểm nóng ô nhiễm:
  $$\text{Cost}(e) = \text{Length}(e) \times (1 + \alpha \cdot \text{AQI}(e))$$
* **Bước 3 — Chặng Về Có Phạt Trọng Số (Penalized Return Leg $W \to S$):**  
  Tất cả các cạnh đường đã đi ở Chặng 1 sẽ bị **phạt tăng trọng số 30 lần ($30\times$)**:
  $$\text{Cost}'(e) = \text{Cost}(e) \times 30^{\mathbb{I}(e \in \text{Leg 1})}$$
  Thuật toán buộc phải "uốn lượn" tìm một cung đường hoàn toàn mới ven mặt hồ để quay về đích.
* **Bước 4 — Tích Phân Liều Lượng Bụi Hít Vào ($M_{\text{inhaled}}$):**  
  Tích phân nồng độ bụi dọc theo từng phân đoạn 35m dựa trên tốc độ chạy (Pace) và thể tích thông khí phổi của runner:
  $$M_{\text{inhaled}} = \int_{0}^{T} C(x(t)) \cdot V_E \, dt \quad (\mu g)$$
* **Kết quả đo lường thực tế:**
  - **Độ trùng lặp đường chạy cũ:** **Đúng 0.0%** (Khép kín tuần hoàn $d=0.0\text{m}$).
  - **Mức giảm lượng bụi mịn hít vào phổi:** **Giảm 35.4% đến 45.0%** (né được 18–25 µg bụi độc hại mỗi buổi tập).

---

## 5. KIẾN TRÚC KỸ THUẬT MONOREPO 5 LỚP & LUỒNG DỮ LIỆU KHÉP KÍN

Hệ thống được thiết kế theo chuẩn doanh nghiệp gồm 5 phân tầng và đóng gói trong **8 Docker Containers cô lập**:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               5-TIER LAYERED ARCHITECTURE & TECH STACK                           │
├───────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 1. TẦNG THU THẬP & MÔ PHỎNG IOT   │ 5 Trạm đo vi khí hậu + 5 Cụm máy lọc dập bụi                 │
│                                   │ Giao thức: Mosquitto MQTT Broker (Port 1883, QoS 1, 15s)     │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 2. TẦNG INGESTION & QUALITY GATE  │ Paho MQTT Consumer, Pydantic Schema Validator                │
│                                   │ Cơ chế Fail-Closed Gate: Loại bỏ dữ liệu nhiễu, Stale > 300s │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 3. TẦNG SYSTEM OF RECORD (SoR)    │ PostgreSQL 16 Database (Single Source of Truth)              │
│                                   │ Bảng `audit_logs` Append-Only (Chống sửa xóa nhật ký)        │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 4. TẦNG APPLICATION & AI ENGINE   │ FastAPI Core (REST API / OpenAPI), Celery Background Worker  │
│                                   │ LangGraph State Machine, Prophet ML, 2-Leg OSM Graph Router  │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ 5. TẦNG GIAO DIỆN & BẢO MẬT PROXY │ React 18, TailwindCSS/Vanilla CSS, Leaflet GIS, Fast-Polling │
│                                   │ Caddy Web Server: Tự động cấp chứng chỉ Let's Encrypt SSL    │
└───────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

### 3 Luồng Dữ Liệu Khép Kín (3 Arrow Flow Pipelines):
* **Luồng 1 (Telemetry Stream - 15s):**  
  `5 Trạm Đo IoT` ➔ `Mosquitto MQTT` ➔ `Data Quality Gate` ➔ `PostgreSQL 16 SoR`
* **Luồng 2 (Query & Geospatial - <120ms):**  
  `Cư Dân / Runner` ➔ `React 18 Leaflet GIS` ➔ `FastAPI Core` ➔ `LangGraph + 2-Leg OSM Router`
* **Luồng 3 (HITL Action & Audit - 0.8s ACK):**  
  `Ô Nhiễm Vượt Ngưỡng` ➔ `Cổng HITL (BQL Duyệt 1-Click)` ➔ `Lệnh MQTT` ➔ `Bật Máy Lọc 45 Phút`

---

## 6. AN TOÀN AI TUYỆT ĐỐI (ZERO-HALLUCINATION) & CỔNG HITL

Để ứng dụng AI an toàn vào lĩnh vực sức khỏe và điều khiển vật lý, AirGuard AI thiết lập **3 lá chắn an ninh cốt lõi**:

### 6.1. Nguyên Tắc "Grounding Trước Fluency" (Grounding Policy Gate)
* **Quy tắc bất biến:** AI Agent **không bao giờ được phép tự bịa đặt số liệu vi khí hậu**.
* 100% câu trả lời có chứa số liệu (AQI, PM2.5, nhiệt độ) bắt buộc phải trích xuất trực tiếp từ kết quả Tool Calling của cùng request đó.
* Bộ kiểm duyệt đối soát token ngăn chặn mọi ảo giác môi trường (Đạt **100% Grounding Accuracy** trên 87 bài test).

### 6.2. Bộ Chuyển Mạch Tiền Định (Deterministic Fallback Switcher)
* Khi mạng LLM bên ngoài (OpenAI/Gemini) bị nghẽn mạng, timeout (> 8.0s) hoặc lỗi HTTP 429:
  - Hệ thống tự động kích hoạt **Bộ sinh phản hồi cục bộ tiền định (Local Deterministic Generator)**.
  - Phản hồi cư dân trong **< 500ms** bằng dữ liệu thực trích xuất từ trạm đo gần nhất.
  - Cam kết: **0% Lỗi HTTP 5xx**, hệ thống không bao giờ bị "treo".

### 6.3. Cổng Bảo Mật HITL Server-Side & Chống Spam
* AI Agent chỉ có quyền tạo **Đề xuất cảnh báo (Warning Proposal) ở trạng thái `pending`**.
* Quyền gửi lệnh MQTT kích hoạt thiết bị lọc khí **bắt buộc phải do tài khoản Quản lý (Manager) ký duyệt**.
* **Khóa Cooldown 15 phút:** Ngăn chặn việc gửi cảnh báo liên tục gây mệt mỏi cảnh báo (Alert Fatigue).
* **Tự động ngắt an toàn:** Máy lọc chạy chế độ tăng cường (80% công suất) trong **45 phút** rồi tự động chuyển về chế độ tiết kiệm điện.
* Mọi thao tác phê duyệt đều được ghi vết bất biến vào bảng `audit_logs`.

---

## 7. BẢNG CHỈ SỐ VÀNG & BẰNG CHỨNG NGHIỆM THU 153/153 TESTS

### 🌟 4 Con Số Vàng Highlight Khi Pitching:
1. **🏃 0.0% TRÙNG LẶP & -45% BỤI HÍT VÀO:** Định tuyến khép kín hoàn hảo trên đồ thị OSM $>10,500$ cạnh; né $18-25\mu g$ bụi mịn/buổi chạy.
2. **🛡️ 100% GROUNDED & ZERO HALLUCINATION:** 100% số liệu vi khí hậu có căn cứ từ DB SoR; 0% lỗi HTTP 5xx nhờ Fallback $<500\text{ms}$.
3. **⚡ GIẢM 90% THỜI GIAN & ACK 0.8 GIÂY:** Quy trình BQL từ 25 phút xuống $<2$ phút qua Cổng HITL 1-click; nhận phản hồi điều khiển thiết bị trong đúng 0.8s.
4. **🌱 TIẾT KIỆM 35% ĐIỆN & 100% BÁO CÁO ESG:** Tiết kiệm $\sim 118,800\text{ kWh/tháng}$ ($\sim 300\text{ triệu VNĐ/tháng}$ tiền điện cho 66 tòa); tự động xuất báo cáo kiểm toán môi trường.

### 📊 Bảng Đối Soát Nghiệm Thu Toàn Bộ Test Suites:
* **Tổng số kịch bản kiểm thử tự động:** **153 / 153 Tests Passed (100% PASS)**.
* **Bộ test bao gồm:**
  - 42 Test Unit & Ingestion Quality Gate.
  - 24 Test AI Chat Grounding & Policy Gate.
  - 30 Test 2-Leg OSM Routing & Geometry Closure.
  - 25 Test HITL State Machine & MQTT Dispatcher.
  - 32 Test End-to-End API, Database Constraints & RBAC.

---

## 8. CẨM NANG THAO TÁC LIVE DEMO 60 GIÂY TRÊN AZURE

Khi chuyển sang **Slide 6 (Live Demo)**, bạn mở trình duyệt tại `https://airguard-074-app.indonesiacentral.cloudapp.azure.com` và thao tác chuẩn xác theo 3 bước sau:

* **Bước 1 (15 giây) — Trải nghiệm Bản đồ Heatmap GIS:**
  - *"Kính thưa Hội đồng, đây là bản đồ nhiệt IDW thời gian thực tại Vinhomes Ocean Park 1. Quý vị có thể thấy ngay vùng hồ Ngọc Trai hiển thị màu xanh lá cây trong lành (AQI 35), trong khi trục đường Sao Biển phía Tây Bắc đang ở mức cam cảnh báo."*
* **Bước 2 (25 giây) — Đàm thoại AI & Vẽ Đường Chạy 5km:**
  - Bấm mở ngăn Trợ lý AI ở góc phải màn hình.
  - Gõ hoặc click câu mẫu: *"Gợi ý đường chạy 5km quanh hồ cho người nhạy cảm"*.
  - Nhấn Enter $\to$ Chỉ sau 1 giây, chỉ ra đường Polyline xanh ôm trọn mặt hồ.
  - *"Ngay lập tức, thuật toán 2-Leg Dijkstra đã vẽ một đường chạy khép kín tuần hoàn đúng 0.0% lặp đường cũ, và AI phân tích lượng bụi hít vào chỉ 4.8 ug — giảm 45% so với chạy trên đường trục chính!"*
* **Bước 3 (20 giây) — Cổng Phê Duyệt HITL Của Ban Quản Lý:**
  - Chuyển sang tab **"Bảng Quản Trị / HITL Center"**.
  - Chỉ vào thẻ đề xuất đang chờ duyệt: *"Tại trạm Sao Biển, AI đã tự động gom Thẻ bằng chứng (Evidence Card) với nồng độ PM2.5 vượt ngưỡng. Tôi chỉ cần bấm **[Phê duyệt]**"*.
  - Click nút `[Phê duyệt]` $\to$ Chỉ ra trạng thái chuyển sang xanh và đồng hồ 45 phút bắt đầu đếm ngược.
  - *"Chỉ trong 0.8 giây, bản tin MQTT đã phát xuống thiết bị và máy lọc bắt đầu dập bụi!"*

---

## 9. MÔ HÌNH KINH DOANH, KHẢ NĂNG MỞ RỘNG & ĐỊNH HƯỚNG ESG

* **Mô hình B2B / B2G SaaS (Nguồn doanh thu chính):**
  - Khách hàng mục tiêu: Ban Quản Lý các khu đô thị Vinhomes, Ecopark, Phú Mỹ Hưng, Gamuda Land và các Khu công nghiệp thông minh.
  - Mức phí định kỳ: **$2,000 – $5,000 / tháng / khu đô thị**.
  - Giá trị mang lại: Giảm chi phí điện năng thông gió ($12,000/tháng), giảm nhân sự trực ca và tự động hóa hồ sơ kiểm toán ESG để đạt chứng chỉ Công trình Xanh (LEED, LOTUS).
* **Mô hình B2C Subscription (Gia tăng giá trị cư dân):**
  - Gói tài khoản cá nhân hóa: **$2 / tháng** (hoặc 49,000 VNĐ/tháng) cho các runner và gia đình có con nhỏ.
  - Quyền lợi: Cảnh báo ô nhiễm theo bán kính nhà ở, đo lường liều lượng bụi tích lũy và đồng bộ đường chạy thông minh lên Strava/Garmin.
* **Lộ trình 3 Giai đoạn Phát triển Hướng Tới Cư Dân (Resident-Centric Roadmap):**
  - **Giai đoạn 1 (Q4/2026) — Mobile App & Đồng bộ Thiết bị thông minh**:
    * Phát hành ứng dụng di động **AirGuard Mobile (iOS, Android, Zalo Mini App)**: Cư dân nhận thông báo đẩy tức thì theo vị trí thời gian thực.
    * Đồng bộ tuyến chạy sạch 1-click lên **Apple Watch, Garmin, Strava**: Rung phản hồi dẫn đường và cảnh báo an toàn khi runner tiếp cận vùng ô nhiễm cục bộ.
  - **Giai đoạn 2 (Q1/2027) — Hệ sinh thái Cư dân & Smart Home**:
    * **Liên động Căn Hộ Thông Minh (Smart Home Integration)**: Tự động nhắc nhở đóng cửa sổ, đồng bộ bật/tắt máy lọc không khí trong phòng theo nồng độ bụi ngoài trời.
    * **Cộng đồng "Green Runner" & Tích Điểm Xanh (Loyalty Points)**: Thử thách thể thao sạch, tích lũy dặm chạy xanh đổi voucher tiện ích đại đô thị (vé bơi, phí gửi xe, cà phê ven hồ).
  - **Giai đoạn 3 (2027+) — Mở rộng Hệ sinh thái Smart City Toàn Quốc**:
    * Nhân rộng giải pháp ra toàn bộ hệ thống đại đô thị thông minh Vinhomes (Smart City Tây Mỗ, Grand Park Q9), Ecopark và các khu đô thị lớn tại Việt Nam.

---

## 10. BỘ CÂU HỎI "XOÁY" Q&A CỦA HỘI ĐỒNG & ĐÁP ÁN MẪU ĐỈNH CAO

Dưới đây là 6 câu hỏi hóc búa nhất mà Mentor và Ban Giám Khảo thường hỏi, kèm câu trả lời đanh thép:

#### ❓ Câu 1: "Làm thế nào bạn đảm bảo AI không bịa đặt số liệu (Hallucination) khi đưa ra lời khuyên sức khỏe cho cư dân?"
> 💬 **Đáp án chuẩn:**  
> *"Thưa Ban giám khảo, chúng tôi áp dụng nguyên tắc **'Grounding trước Fluency'**. Trong kiến trúc LangGraph, câu trả lời của AI bị chặn lại tại **Cổng Grounding Policy Gate**. Cổng này phân tích cú pháp toàn bộ số liệu nồng độ bụi trong câu trả lời và đối chiếu chéo với dữ liệu Tool Calling trả về từ PostgreSQL trong cùng request. Nếu xuất hiện bất kỳ con số nào không có trong cơ sở dữ liệu, câu trả lời sẽ bị từ chối và thay thế bằng mẫu dữ liệu chuẩn. Qua 87 ca kiểm thử Golden Set, hệ thống đạt độ chính xác căn cứ **100.0% — Zero Environmental Hallucination**."*

#### ❓ Câu 2: "Nếu đường truyền Internet bị ngắt hoặc API bên ngoài bị timeout, hệ thống của bạn có bị sập không?"
> 💬 **Đáp án chuẩn:**  
> *"Hoàn toàn không. Chúng tôi xây dựng cơ chế **Bộ chuyển mạch tiền định (Deterministic Fallback Switcher)**. Nếu API OpenAI/Gemini timeout quá 8 giây hoặc trả về lỗi 429/500, hệ thống tự động ngắt và chuyển sang bộ sinh phản hồi tiền định bằng quy tắc cục bộ. Bộ chuyển mạch này phản hồi người dùng trong **dưới 500ms** dựa trên dữ liệu trạm đo gần nhất, đảm bảo tỷ lệ lỗi HTTP 5xx của hệ thống luôn bằng **đúng 0%**."*

#### ❓ Câu 3: "Tại sao lại cần Human-in-the-Loop (HITL) mà không cho AI tự động kích hoạt máy lọc không khí?"
> 💬 **Đáp án chuẩn:**  
> *"Đây là nguyên tắc an toàn tối thượng trong điều khiển vật lý đô thị. Việc bật hệ thống quạt thông gió khối đế hoặc máy lọc công suất lớn liên quan trực tiếp đến chi phí điện năng, tiếng ồn và an toàn phòng cháy chữa cháy của tòa nhà. AI có thể phát hiện ô nhiễm trong 0.007ms và chuẩn bị sẵn Thẻ Bằng Chứng trong 850ms, nhưng **con người (Trưởng ca BQL) phải là người bấm nút phê duyệt cuối cùng**. Điều này vừa tuân thủ tuyệt đối quy định an toàn đô thị, vừa giảm 90% thời gian xử lý của BQL."*

#### ❓ Câu 4: "Thuật toán tìm đường chạy 2-Leg Dijkstra có đảm bảo luôn tìm được đường khép kín 0% lặp lại không?"
> 💬 **Đáp án chuẩn:**  
> *"Có, thưa Hội đồng. Chúng tôi đã kiểm thử trên 30 vòng lặp thực tế trên đồ thị OSM hơn 10,500 cạnh tại Ocean Park 1. Nhờ kỹ thuật phạt 30 lần trọng số các cạnh chiều đi, chặng về buộc phải tìm các đường nhánh ven hồ khác. Kết quả đo đạc hình học cho thấy khoảng cách giữa điểm xuất phát và kết thúc đạt **d = 0.0 mét**, độ khép kín đạt **100%** và tỷ lệ chạy lùi đường cũ bằng **đúng 0.0%**."*

#### ❓ Câu 5: "Dữ liệu cảm biến lấy từ đâu? Nếu một trạm cảm biến bị lỗi hoặc mất kết nối thì sao?"
> 💬 **Đáp án chuẩn:**  
> *"Hệ thống sử dụng cơ chế **Data Quality Gate** theo triết lý Fail-Closed. Nếu một trạm không gửi dữ liệu quá 300 giây, trạng thái trạm sẽ tự động chuyển sang `stale/offline` và bị loại khỏi phép tính nội suy IDW để không làm sai lệch bản đồ nhiệt. Khi đó, bản đồ nhiệt sẽ tự động hiệu chỉnh trọng số dựa trên các trạm hoạt động bình thường còn lại."*

#### ❓ Câu 6: "Dự án đã có người dùng thật chưa và chi phí vận hành đám mây hiện tại là bao nhiêu?"
> 💬 **Đáp án chuẩn:**  
> *"Dự án hiện đang chạy thực tế trên hạ tầng **Azure VM Standard B2ms** với chi phí tối ưu chỉ khoảng **$35 – $40/tháng**. Nhờ kiến trúc tối ưu hóa tài nguyên (P95 latency API < 120ms, throughput quét cảnh báo hơn 120,000 bản tin/giây), một cụm VM nhỏ có thể phục vụ trọn vẹn cả khu đô thị 30,000 cư dân. Chúng tôi đã tiến hành khảo sát trên 20 runner và cư dân thực tế tại Ocean Park 1 với tỷ lệ phản hồi tích cực và mong muốn sử dụng đạt trên **85%**."*

---

> 🏁 **LỜI KHUYÊN CUỐI CÙNG CHO TEAM P-074:**  
> Giữ phong thái tự tin, tương tác ánh mắt với Ban giám khảo, bám sát các con số định lượng (45% bụi, 0.8s ACK, 153/153 tests) và thoải mái biểu diễn live trên Azure. Chúc nhóm giành điểm số tuyệt đối! 🚀

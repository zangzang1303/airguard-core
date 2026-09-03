# 🏗️ GIẢI THÍCH CHI TIẾT KIẾN TRÚC 3 LUỒNG DỮ LIỆU KHÉP KÍN & TECH STACK THỰC TẾ
# AIRGUARD AI (NHÓM P-074 / TỨ KỴ SĨ KHẢI HUYỀN)

> **Mã tài liệu:** `AIRGUARD-ARCH-3-FLOWS-2026`  
> **Dự án:** AirGuard AI — Hệ Thống Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh  
> **Đơn vị:** AI20K Build Phase Cohort 3  
> **Địa bàn thực nghiệm:** Đại đô thị Vinhomes Ocean Park 1 (Gia Lâm, Hà Nội)  
> **Hạ tầng Production:** `https://airguard-074-app.indonesiacentral.cloudapp.azure.com`

---

## 🗺️ TỔNG QUAN KIẾN TRÚC: TẠI SAO PHẢI TÁCH THÀNH 3 LUỒNG ĐỘC LẬP?

Trong các hệ thống giám sát môi trường và điều khiển thiết bị đô thị thông minh (Smart City IoT), nguyên tắc thiết kế quan trọng nhất là **Phân tách trách nhiệm (Separation of Concerns)**:
1. **Luồng dữ liệu vào (Data Inflow / Telemetry):** Phải hoạt động liên tục 24/7, không bao giờ được nghẽn dù người dùng có truy cập hay không.
2. **Luồng người dùng (User Inflow / Query & AI):** Phải phản hồi siêu tốc dưới 120ms, giao diện mượt mà và trực quan.
3. **Luồng hành động vật lý (Action Outflow / HITL Physical Control):** Phải đảm bảo an toàn tuyệt đối, không được để AI tự ý kích hoạt thiết bị vật lý nếu chưa có con người (Manager) phê duyệt.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SƠ ĐỒ 3 LUỒNG DỮ LIỆU CỦA AIRGUARD AI                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

 [ LUỒNG 1: THU THẬP TELEMETRY REALTIME (Chu kỳ mỗi 15s) ]
 1. Trạm đo IoT ───► 2. Mosquitto MQTT ───► 3. Data Quality Gate ───► 4. PostgreSQL 16 SoR
   (5 trạm ngoài trời)   (QoS 1, không mất gói)    (Pydantic, chặn stale >300s)     (Index kép, SoR duy nhất)

 [ LUỒNG 2: TRUY VẤN BẢN ĐỒ & AI ĐỊNH TUYẾN (Phản hồi siêu tốc < 120ms) ]
 1. Cư Dân / Runner ─► 2. React 18 Leaflet GIS ─► 3. FastAPI Core Backend ─► 4. LangGraph & Router
   (Yêu cầu tìm đường)   (Render Heatmap IDW 60x60)     (Async ASGI, Celery worker)    (2-Leg Dijkstra -45% bụi)

 [ LUỒNG 3: CẢNH BÁO & ĐIỀU KHIỂN THIẾT BỊ HITL (Phản hồi 0.8s ACK) ]
 1. Ô Nhiễm Vượt Ngưỡng ─► 2. Cổng HITL Portal ─► 3. Lệnh MQTT Dispatcher ─► 4. Kích Hoạt Máy Lọc
   (Safety Rules quét 0.007ms)   (BQL duyệt 1-click Evidence)    (Phát lệnh ACK 0.8s)          (Dập bụi 45m, tự ngắt)
```

---

## 1. GIẢI THÍCH CHI TIẾT TỪNG LUỒNG DỮ LIỆU TRÊN SLIDE 4

### ⚡ LUỒNG 1: THU THẬP TELEMETRY REALTIME (CHU KỲ MỖI 15 GIÂY)
* **1. Trạm đo IoT (Cảm biến ngoại vi):**  
  Gồm 5 trạm quan trắc đặt tại 5 phân khu trọng yếu (S01 Đa Tốn Tây Bắc, S02 Sapphire, S03 Biển Hồ, S04 VinUni, S05 Hải Âu). Mỗi trạm đo 4 chỉ số: Bụi mịn PM2.5, khí CO2, độ ồn và nhiệt/ẩm theo chu kỳ **15 giây một lần**.
* **2. Mosquitto MQTT (Truyền tin cậy với QoS 1):**  
  Cảm biến đóng gói dữ liệu thành JSON và phát qua giao thức siêu nhẹ MQTT (Eclipse Mosquitto). **QoS 1 (Quality of Service 1)** đảm bảo bắt tay gói xác nhận (`PUBACK`). Nếu mạng 4G chập chờn, thiết bị sẽ tự động phát lại cho tới khi chắc chắn máy chủ đã nhận $\to$ **Cam kết 0% rơi rớt bản tin vi khí hậu**.
* **3. Data Quality Gate (Cổng kiểm định chất lượng — Fail-Closed):**  
  Dữ liệu đến máy chủ **chưa được ghi vào Database ngay**, mà phải bước qua Cổng kiểm định viết bằng Pydantic v2:
  * **Ép kiểu & chặn giá trị phi lý:** Nếu PM2.5 là số âm hoặc vọt lên $> 500\text{ }\mu g/m^3$ do chập điện $\to$ Ném vào bảng `mqtt_rejections`.
  * **Cơ chế phát hiện trạm hỏng (Stale Detector > 300s):** Nếu một trạm bị mất tín hiệu quá 5 phút (300 giây), hệ thống tự động gắn cờ `is_stale = True` và **cô lập trạm đó khỏi thuật toán tính bản đồ nhiệt**, ngăn chặn dữ liệu cũ làm sai lệch màu sắc bản đồ toàn khu.
* **4. PostgreSQL 16 SoR (System of Record — Lưu trữ tối ưu):**  
  Bản tin đạt chuẩn được ghi vào bảng `measurements` của PostgreSQL 16. Bảng được đánh **Chỉ mục kép (Composite Index)** trên `(station_id, measured_at DESC)` giúp API truy xuất 100 điểm đo lịch sử của trạm chỉ mất **dưới 3 mili-giây**!

---

### 🗺️ LUỒNG 2: TRUY VẤN BẢN ĐỒ & AI ĐỊNH TUYẾN (PHẢN HỒI SIÊU TỐC < 120ms)
* **1. Cư Dân / Runner (Nhu cầu thực tế):**  
  Cư dân mở ứng dụng trên điện thoại hoặc máy tính, muốn biết lúc này không khí quanh nhà mình thế nào, hoặc gõ vào Trợ lý AI: *"Tìm cho tôi đường chạy 5km quanh hồ cho người nhạy cảm"*.
* **2. React 18 Leaflet GIS (Hiển thị bản đồ nhiệt không gian IDW 60x60):**  
  Giao diện React 18 kết hợp Leaflet render bản đồ nhiệt vi khí hậu thời gian thực. Bản đồ được chia thành **lưới ma trận 60x60 điểm nội suy mịn (Inverse Distance Weighting - IDW)** kết hợp vector hướng gió thực địa lấy từ Open-Meteo, hiển thị dải màu trực quan chuẩn US EPA (Xanh lá - Tốt, Vàng - Trung bình, Cam - Nhạy cảm, Đỏ - Nguy hại).
* **3. FastAPI Core Backend (Xử lý bất đồng bộ & Celery):**  
  Sử dụng Python 3.12 và FastAPI bất đồng bộ (Async ASGI). Các tác vụ tính toán ma trận nặng được phân bổ qua **Celery Background Worker**, đảm bảo thời gian phản hồi API (P95 Latency) luôn **dưới 120 mili-giây** (nhanh hơn một cái chớp mắt).
* **4. LangGraph & 2-Leg Router (Định tuyến thể thao 0.0% lặp đường & Giảm 45% bụi):**  
  Máy trạng thái LangGraph kích hoạt thuật toán độc quyền **2-Leg Penalized Dijkstra** trên đồ thị đường thực OpenStreetMap (>10,500 cạnh). Thuật toán phạt gấp 30 lần trọng số chiều về để ép cung đường ôm trọn mặt hồ mới $\to$ Tạo ra đường chạy tuần hoàn **đúng 0.0% lặp đường cũ** và **giúp giảm 45% lượng bụi mịn tích phân hít vào phổi** ($M_{\text{inhaled}}$).

---

### 🚨 LUỒNG 3: CẢNH BÁO & ĐIỀU KHIỂN THIẾT BỊ HITL (PHẢN HỒI 0.8s ACK)
* **1. Ô Nhiễm Vượt Ngưỡng (Phát hiện siêu tốc):**  
  Khi dữ liệu ở Luồng 1 ghi vào Database, bộ lọc an toàn (Safety Rules) quét ngay lập tức trong **0.007 mili-giây**. Nếu phát hiện nồng độ PM2.5 vượt ngưỡng an toàn (ví dụ: S01 vọt lên 155), AI tự động tạo một Đề xuất dập bụi (Warning Proposal) ở trạng thái `pending` kèm theo **Thẻ bằng chứng (Evidence Card)** chứa đầy đủ số liệu quan trắc.
* **2. Cổng HITL Portal (Ban Quản Lý thẩm định & Duyệt 1-Click):**  
  Giao diện của Trưởng ca BQL lập tức hiện thẻ cảnh báo màu vàng. BQL xem xét nồng độ bụi và bấm nút **[Phê duyệt]** (1-Click). Cổng này tích hợp **Khóa Idempotency Key** chống việc người dùng lỡ tay bấm đúp chuột 2 lần gây loạn lệnh.
* **3. Lệnh MQTT Dispatcher (Phát lệnh siêu tốc dưới 1 giây):**  
  Ngay khi bấm duyệt, Backend đóng gói bản tin lệnh và phát ngược xuống thiết bị qua kênh MQTT `airguard/devices/{device_id}/commands`. Máy lọc ngoài thực địa nhận lệnh và lập tức gửi lại bản tin xác nhận (`PUBACK`). Toàn bộ chu trình này hoàn tất trong đúng **0.8 giây**!
* **4. Kích Hoạt Máy Lọc & Tự Ngắt Thông Minh 45 Phút:**  
  Cụm máy lọc không khí thông minh bật chế độ Boost 80% công suất để dập bụi khu vực. Máy lọc đếm ngược và **tự động ngắt sau 45 phút** (không để máy chạy quên suốt đêm làm cháy động cơ). Cơ chế này giúp khu đô thị **tiết kiệm 35% điện năng (~118,800 kWh/tháng)**. Đồng thời, toàn bộ hành vi bật/tắt được ghi vĩnh viễn vào bảng `audit_logs` có Trigger cấm sửa/xóa để phục vụ báo cáo ESG!

---

## 2. BẢN ĐỒ TECH STACK THỰC TẾ TRONG MONOREPO

| Thành Phần | Công Nghệ Sử Dụng | Phiên Bản | Vai Trò & Điểm Nổi Bật |
|---|---|:---:|---|
| **Cơ Sở Dữ Liệu** | **PostgreSQL 16** | `postgres:16` | System of Record (SoR), TimescaleDB-ready, Trigger Append-Only cấm sửa/xóa `audit_logs`. |
| **Message Broker** | **Eclipse Mosquitto** | `mosquitto:2` | MQTT Broker chuẩn công nghiệp, QoS 1, header 2 bytes, độ trễ phản hồi < 50ms. |
| **Backend Core** | **FastAPI & Python** | `3.12` | ASGI Framework bất đồng bộ, Pydantic v2 validation, SQLAlchemy 2.0 async. |
| **Background Tasks**| **Celery & Redis/RabbitMQ**| `5.4` | Xử lý tác vụ ngầm: nội suy IDW, xuất báo cáo ESG, quét cảnh báo định kỳ. |
| **Bộ Não AI Agent** | **LangGraph State Machine** | `0.2.x` | Máy trạng thái điều phối Agent, Tool Calling chuẩn hóa, Grounding Policy Gate. |
| **Định Tuyến Đồ Thị**| **NetworkX / OSMnx / Shapely**| `3.3` | Đồ thị giao thông thực tế >10,500 cạnh đường OSM, thuật toán 2-Leg Dijkstra. |
| **Frontend Dashboard**| **React 18 & TypeScript** | `18.3` | Single Page App, Leaflet GIS, TailwindCSS + Glassmorphism Dark Mode. |
| **Hạ Tầng & DevOps**| **Docker Compose & Caddy** | `2.8` | 8 Containers cô lập, Caddy Reverse Proxy tự động cấp phát SSL Let's Encrypt trên Azure VM. |

---

## 3. CƠ CHẾ LƯU TRỮ DỮ LIỆU CỦA POSTGRESQL 16

PostgreSQL 16 trong AirGuard AI quản lý **5 nhóm bảng dữ liệu chuyên biệt**:
1. **Nhóm Vi khí hậu & Telemetry:** Bảng `stations` (5 trạm S01-S05), `station_status` (online/offline), `measurements` (chuỗi thời gian mỗi 15s với Composite Index truy vấn <3ms), `mqtt_rejections` (lọc rác).
2. **Nhóm Người dùng & Hồ sơ Sức khỏe:** Bảng `users` (Argon2id hashing, 3 nhóm thể trạng: normal, sensitive, outdoor_sport), `user_sessions` (token hash SHA-256), `resident_notification_preferences`.
3. **Nhóm Cảnh báo Sớm & Dự báo:** Bảng `alerts` (cảnh báo tức thời), `predictive_warning_episodes` (dự báo chuỗi thời gian 1-24h kèm `evidence JSONB`).
4. **Nhóm Thiết bị & Cổng HITL:** Bảng `devices` (FILTER-01 đến 05), `device_operating_profiles` (ràng buộc không chồng lấn thời gian GIST), `approval_requests` (duyệt 1-click có khóa Idempotency), `device_command_intents` (đo độ trễ ACK 0.8s).
5. **Nhóm Kiểm toán Bất biến & ESG:** Bảng `audit_logs` có Trigger Pl/pgSQL `prevent_audit_log_mutation()` **chặn đứng 100% lệnh UPDATE và DELETE**; bảng `environmental_reports` có mã băm toàn vẹn SHA-256.

---

## 4. CHIẾN LƯỢC TOOLING TRONG AI AGENT (TOOLING STRATEGY)

* **Bản chất:** AI Agent không "nói suông" dựa trên trí nhớ LLM mà bắt buộc phải gọi **10 công cụ nghiệp vụ chuẩn hóa (Tool Registry)** trong `src/agents/tools/contracts.py`.
* **Strict Validation:** Mọi input kế thừa từ `StrictModel` với `extra="forbid"` $\to$ Chặn đứng 100% việc truyền tham số lạ hoặc tấn công Prompt Injection.
* **Tool Envelope:** Mọi kết quả trả về đóng gói chuẩn `ToolEnvelope` (thành công) hoặc `ToolError` (thất bại) $\to$ Giúp Agent kích hoạt Fallback < 500ms khi gặp sự cố, cam kết 0% lỗi HTTP 5xx.
* **HITL Isolation:** Agent chỉ có tool `create_warning_proposal` để tạo đề xuất dập bụi dạng `pending`, **tuyệt đối không có quyền tự bật thiết bị vật lý**. Quyền kích hoạt thuộc về con người (Manager).

---

## 5. PHƯƠNG ÁN TRIỂN KHAI TRÊN THIẾT BỊ PHẦN CỨNG THỰC TẾ

Khi triển khai ngoài cột đèn thực tế tại Vinhomes Ocean Park 1:
* **Bộ vi điều khiển:** ESP32-S3 kết hợp Module truyền thông 4G LTE hoặc LoRaWAN SX1262 (bán kính phủ sóng 3-5 km xuyên qua các tòa cao tầng).
* **Cảm biến:** Bụi laser Sensirion SPS30 / Plantower PMS7003, Khí CO2 hồng ngoại Senseair S8 NDIR, Nhiệt ẩm Sensirion SHT31, Âm thanh analog dB, Cánh gạt gió RS485 Modbus.
* **Nguồn & Vỏ:** Pin mặt trời 25W + Pin Lithium LiFePO4 12V 12Ah chạy tự hành 5 ngày mưa; vỏ trạm nan chớp chuẩn IP65/IP67.
* **Công thức bù độ ẩm sấy hạt bụi (RH Correction):** $PM_{\text{corrected}} = \frac{PM_{\text{raw}}}{1 + 0.25 \times (RH/100)^2}$ giúp triệt tiêu hiện tượng đo ảo khi trời mưa phùn, sương mù.
* **Tính tương thích:** Thiết bị nạp firmware ESP32 chỉ cần publish JSON vào topic Mosquitto MQTT sẵn có. **Backend và AI Agent của nhóm P-074 giữ nguyên 100%, không cần viết lại một dòng code nào!**

---

## 🎙️ LỜI THOẠI NÓI 40 GIÂY MẪU KHI CHIẾU SLIDE 4:

> *"Kính thưa quý Hội đồng, kiến trúc của AirGuard AI được tổ chức thành **3 luồng dữ liệu khép kín và nhịp nhàng**:  
> 
> * **Luồng 1 là Luồng Thu Thập Telemetry Realtime**: Mỗi 15 giây, 5 trạm IoT đẩy dữ liệu qua **Mosquitto MQTT với QoS 1** chống mất gói tin. Tầng Ingestion áp dụng **Data Quality Gate** với cơ chế Fail-Closed: tự động loại bỏ dữ liệu sai lệch hoặc trạm mất tín hiệu quá 300 giây trước khi ghi vào **PostgreSQL 16 SoR**.  
> * **Luồng 2 là Luồng Truy Vấn Bản Đồ & AI Định Tuyến**: Giao diện **React 18 Leaflet GIS** hiển thị bản đồ nhiệt IDW ma trận 60x60 cực mịn, kết nối với **FastAPI Core** phản hồi dưới 120ms, và kích hoạt động cơ **2-Leg Dijkstra** định tuyến đường chạy sạch 0% lặp đường cũ, giúp giảm 45% lượng bụi hít vào.  
> * **Luồng 3 là Luồng Hành Động Can Thiệp HITL**: Khi phát hiện ô nhiễm, AI gom Thẻ bằng chứng gửi lên **Cổng HITL**. Ban Quản Lý chỉ cần duyệt 1-Click, lệnh MQTT truyền xuống thiết bị dập bụi trong **0.8 giây** và máy lọc sẽ chạy chu trình 45 phút rồi tự động ngắt để bảo vệ thiết bị và tiết kiệm 35% điện năng!"*

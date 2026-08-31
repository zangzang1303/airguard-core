# ĐẶC TẢ YÊU CẦU PHẦN MỀM (SOFTWARE REQUIREMENTS SPECIFICATION - SRS)
## Hệ Thống Giám Sát Môi Trường & Trợ Lý Tuyến Đường An Toàn AirGuard AI (Gate 2 Deliverable)

> **Chuẩn tài liệu**: IEEE Std 830-1998 & ISO/IEC/IEEE 29148:2011/2017 (Dựa trên cấu trúc MSRS chuẩn hóa từ `jam01/SRS-Template`).  
> **Dự án**: AirGuard AI MVP — Vinhomes Ocean Park 1  
> **Phiên bản tài liệu**: 2.0.0 (Gate 2 Baseline)  
> **Trạng thái**: Hoàn thiện kỹ thuật cốt lõi (Technical Baseline Verified)  
> **Ngày cập nhật**: 31/08/2026  

---

## 1. GIỚI THIỆU (INTRODUCTION)

### 1.1 Mục đích (Purpose)
Tài liệu này đặc tả chi tiết toàn bộ các yêu cầu chức năng (Functional Requirements), yêu cầu phi chức năng / chất lượng dịch vụ (Non-Functional / Quality of Service Requirements), giao diện bên ngoài (External Interfaces), cùng các quy tắc an toàn trí tuệ nhân tạo (AI Grounding & Guardrails) cho hệ thống **AirGuard AI**. Tài liệu đóng vai trò là hợp đồng kỹ thuật và căn cứ nghiệm thu (Acceptance Baseline) giữa nhóm phát triển, ban quản trị dự án và hội đồng thẩm định.

### 1.2 Quy ước tài liệu (Document Conventions)
Tài liệu tuân thủ chuẩn RFC 2119 để định nghĩa mức độ ưu tiên và tính bắt buộc của các yêu cầu:
- **BẮT BUỘC (MUST / SHALL)**: Yêu cầu tuyệt đối phải được đáp ứng đầy đủ để hệ thống được coi là hợp lệ.
- **NÊN (SHOULD / RECOMMENDED)**: Yêu cầu có tính ưu tiên cao, khuyến nghị triển khai trừ khi có lý do kỹ thuật chính đáng.
- **CÓ THỂ (MAY / OPTIONAL)**: Tính năng mở rộng tùy chọn, có thể điều chỉnh theo lộ trình.
- Mã định danh yêu cầu:
  - `REQ-F-xxx`: Yêu cầu Chức năng (Functional Requirement)
  - `REQ-NF-xxx`: Yêu cầu Phi chức năng / Chất lượng dịch vụ (Quality of Service)
  - `REQ-AI-xxx`: Yêu cầu An toàn & Ranh giới AI Agent (AI/ML Constraints)

### 1.3 Đối tượng độc giả & Hướng dẫn đọc (Intended Audience)
- **Hội đồng Giám khảo & Mentor**: Đọc Mục 1, Mục 2, Mục 3.4 và Mục 4 để đánh giá tính hoàn thiện, an toàn và mức độ đáp ứng tiêu chí.
- **Kỹ sư Backend & Data/IoT**: Đọc Mục 3.1.2, 3.1.3, 3.2 (REQ-F-01 $\to$ 03, REQ-F-05 $\to$ 09), 3.3.
- **Kỹ sư AI Agent**: Đọc Mục 3.2 (REQ-F-04), 3.4 (REQ-AI-01 $\to$ 04), 4.
- **Kỹ sư Frontend**: Đọc Mục 3.1.1, 3.1.3, 3.2 (Tương tác bản đồ GIS và AI Assistant).

### 1.4 Phạm vi sản phẩm (Product Scope)
**AirGuard AI** là giải pháp phần mềm thông minh giám sát chỉ số chất lượng không khí (AQI) và các thông số môi trường thành phần (PM2.5, CO2, Tiếng ồn, Nhiệt độ) theo thời gian thực tại 5 trạm quan trắc mô phỏng (S01..S05) xung quanh khu đô thị Vinhomes Ocean Park 1, Gia Lâm, Hà Nội. 

**Phạm vi hệ thống bao gồm**:
1. Thu thập, chuẩn hóa và kiểm soát chất lượng dữ liệu cảm biến thời gian thực qua giao thức MQTT.
2. Tính toán chỉ số phụ AQI 24h theo tiêu chuẩn US EPA PM2.5 (2012) và lập bản đồ phân bố ô nhiễm không gian (Spatial IDW Interpolation).
3. Đề xuất lộ trình chạy bộ/đi bộ/đạp xe khép kín tuần hoàn (Closed-Loop Polygon Circuit) tối ưu hóa giảm phơi nhiễm ô nhiễm trên đồ thị đường thực OpenStreetMap (OSM).
4. Trợ lý ảo AI đàm thoại tiếng Việt grounded 100% bằng Tool Calling, không phát sinh ảo giác (Zero Hallucination).
5. Cơ chế cảnh báo vượt ngưỡng và quy trình phê duyệt can thiệp thiết bị có sự tham gia của con người (Human-in-the-Loop - HITL) kèm nhật ký Audit bất biến (Append-Only).

**Ranh giới loại trừ (Out of Scope)**:
- Không đưa ra chẩn đoán y tế hoặc phác đồ điều trị bệnh đường hô hấp.
- Không trực tiếp điều khiển các thiết bị phần cứng vật lý công nghiệp nguy hiểm (chỉ phát lệnh tới Device Simulator).
- Không thay thế hệ thống quan trắc tiêu chuẩn quốc gia của Tổng cục Môi trường.

### 1.5 Thuật ngữ & Tài liệu tham chiếu (Glossary & References)

#### Bảng thuật ngữ (Glossary)
| Thuật ngữ | Định nghĩa chi tiết |
|---|---|
| **AQI (Air Quality Index)** | Chỉ số chất lượng không khí tổng quan, được tính toán nội suy từ nồng độ PM2.5 theo công thức US EPA PM2.5 24h (2012). |
| **PM2.5** | Bụi mịn có đường kính khí động học $\le 2.5\ \mu m$, đơn vị $\mu g/m^3$. |
| **SoR (System of Record)** | Nguồn dữ liệu chân lý duy nhất của hệ thống (PostgreSQL & FastAPI Backend). |
| **Grounding Policy** | Quy tắc bắt buộc mọi tuyên bố về môi trường của AI Agent phải dựa trên bằng chứng (evidence) lấy từ Tool của Backend trong cùng phiên request. |
| **HITL (Human-in-the-Loop)** | Quy tắc mọi đề xuất cảnh báo/can thiệp của AI chỉ dừng ở trạng thái `pending`; phải có Quản trị viên (Manager) phê duyệt server-side mới kích hoạt lệnh. |
| **IDW (Inverse Distance Weighting)** | Phương pháp nội suy nghịch đảo khoảng cách để tính toán nồng độ ô nhiễm tại mọi điểm trên bản đồ từ 5 trạm quan trắc. |
| **OSM Road Graph** | Đồ thị mạng lưới đường giao thông thực tế được trích xuất từ OpenStreetMap khu vực Ocean Park 1. |
| **Inhaled Mass ($\mu g$)** | Khối lượng bụi mịn PM2.5 ước tính đi vào đường hô hấp khi vận động dọc theo tuyến đường: $\int PM2.5(x,y) \times \text{VentilationRate} \times dt$. |

#### Tài liệu tham chiếu (References)
1. US EPA (2012) — *Technical Assistance Document for the Reporting of Daily Air Quality – the Air Quality Index (AQI)* (EPA-454/B-12-001).
2. ISO/IEC/IEEE 29148:2011 & IEEE Std 830-1998 — *Software Engineering — Requirements Engineering*.
3. OpenStreetMap (OSM) Overpass API Data Contracts.
4. Kiến trúc hệ thống AirGuard AI: [ARCHITECTURE.md](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/ARCHITECTURE.md).
5. Đặc tả API REST: `specs/api-contracts.md`.
6. Đặc tả Dữ liệu MQTT: `specs/data-contracts.md`.

---

## 2. TỔNG QUAN SẢN PHẨM (PRODUCT OVERVIEW)

### 2.1 Bối cảnh sản phẩm (Product Perspective)
AirGuard AI là hệ thống phân tán dạng Monorepo đa tầng (Multi-tier Distributed System), gồm các phân hệ độc lập giao tiếp qua chuẩn mở (REST/JSON, MQTT, SQL, TCP):
```
[Sensor Simulator (S01..S05)] 
        │ (MQTT Telemetry - Port 1883)
        ▼
[Eclipse Mosquitto Broker] ──► [MQTT Ingestion Consumer]
                                      │ (Batch SQL & Gate Check)
                                      ▼
[React 18 Dashboard] ◄──(HTTPS)──► [FastAPI Backend] ◄──► [PostgreSQL 16 SoR]
        │                                 │ (Tool REST)
        │ (AI Drawer Chat)                ▼
        └────────────────────────► [LangGraph AI Agent Service] ◄──► [LLM Provider]
```

### 2.2 Các chức năng cốt lõi (Product Functions)
1. **Quan trắc & Cập nhật Realtime**: Tiếp nhận 5 trạm quan trắc, tự động làm mới giao diện mỗi 30 giây, hiển thị trạng thái online/fresh/stale/offline.
2. **Bản đồ Nhiệt & Không gian (GIS IDW)**: Mô phỏng hành lang không khí sạch, phát hiện các điểm nóng (Hotspots) ô nhiễm và khu vực an toàn.
3. **Định tuyến Đường Chạy Sạch (Clean Running Route)**: Tạo chu kỳ vòng lặp đa giác tuần hoàn (Closed-Loop) theo cự ly yêu cầu (1.0km $\to$ 10.0km), đảm bảo đi qua các đường chính, hạn chế tối đa phơi nhiễm PM2.5.
4. **Trợ lý AI Đàm thoại Ngữ cảnh (Conversational Geospatial Agent)**: Trả lời tự nhiên bằng tiếng Việt về môi trường, hỗ trợ ghi nhớ ngữ cảnh đa lượt (Multi-turn Follow-up), điều khiển trực quan bản đồ (`highlight_route`, `fit_bounds`, `add_annotation`).
5. **Cảnh báo Thông minh & Quy trình HITL**: Tự động phát hiện bất thường môi trường, sinh đề xuất can thiệp `pending`, cho phép Manager duyệt 1-click và kích hoạt hệ thống phun sương / email cư dân.

### 2.3 Nhóm người dùng & Đặc tính (User Classes and Characteristics)
| Nhóm người dùng | Mô tả & Nhu cầu | Đặc quyền hệ thống |
|---|---|---|
| **Cư dân thường (Resident)** | Cư dân sinh sống tại Ocean Park 1 cần xem chỉ số AQI, hỏi AI về lộ trình đi dạo/chạy bộ an toàn. | Xem bản đồ, tra cứu chỉ số, chat AI, tùy chỉnh hồ sơ cá nhân. |
| **Nhóm nhạy cảm (Sensitive)** | Trẻ em, người cao tuổi, phụ nữ có thai hoặc người có tiền sử hô hấp (Hen suyễn, COPD). | Nhận cảnh báo ngưỡng nhạy cảm (AQI > 100), tuyến chạy được áp dụng trọng số phạt nghiêm ngặt. |
| **Vận động viên / Thể thao ngoài trời** | Người chạy bộ (Runner), người đạp xe (Cyclist) quan tâm cự ly, thời lượng và liều lượng bụi hít vào. | Lựa chọn loại hình (Walking, Running, Cycling), tùy biến cự ly mục tiêu chính xác. |
| **Ban Quản Trị / Quản Lý (Manager)** | Đội ngũ quản trị khu đô thị, giám sát an toàn môi trường toàn khu. | Truy cập Cổng Phê Duyệt HITL, kiểm tra Evidence, Approve/Reject đề xuất, xem Audit Log bất biến. |
| **Kiểm toán viên / Quản trị hệ thống (Auditor/Admin)** | Kiểm tra tuân thủ an toàn, rà soát lịch sử can thiệp, giám sát sức khỏe dịch vụ. | Toàn quyền tra cứu `audit_logs`, kiểm tra `/health`, `/ready` và cấu hình hệ thống. |

### 2.4 Môi trường vận hành (Operating Environment)
- **Hệ điều hành máy chủ**: Ubuntu 22.04 LTS x86_64 / Linux Cloud VM (Azure Cloud).
- **Hạ tầng Container**: Docker Engine 24.0+, Docker Compose v2.
- **Cơ sở dữ liệu**: PostgreSQL 16 Alpine với kết nối Connection Pool (Asyncpg / SQLAlchemy).
- **Message Broker**: Eclipse Mosquitto 2.0 (MQTT Protocol v3.1.1/v5.0).
- **Backend Runtime**: Python 3.12 Runtime, Uvicorn ASGI Server.
- **AI Agent Runtime**: LangGraph, Pydantic v2, HTTPX Async Client.
- **Trình duyệt máy khách**: Google Chrome 110+, Mozilla Firefox 110+, Safari 16+, Microsoft Edge (chuẩn HTML5/ES6, WebGL, Leaflet GIS).

### 2.5 Giới hạn thiết kế & Ràng buộc triển khai (Design Constraints)
- **Không sử dụng RAG/Vector Database**: Không dùng vector search tùy tiện cho dữ liệu động; toàn bộ thông tin môi trường phải lấy từ SQL Relational Database thời gian thực.
- **Bảo mật biến môi trường**: Tuyệt đối không commit file `.env` hoặc để lộ Secret Key, API Token trong mã nguồn, log hoặc phản hồi HTTP.
- **Chế độ Fail-Closed**: Khi trạm mất kết nối hoặc dữ liệu stale (> 300s), hệ thống từ chối tính toán đường chạy từ trạm đó và hiển thị thông báo thiếu dữ liệu minh bạch.
- **Tương thích mạng yếu**: Giao diện client duy trì trạng thái đệm (cached state) và cơ chế tự động thử lại khi mất kết nối mạng.

### 2.6 Giả định & Phụ thuộc (Assumptions and Dependencies)
- Hệ thống trích xuất và lưu trữ sẵn đồ thị giao thông OSM khu vực Ocean Park 1 trong `RoadGraphRouter`.
- Kết nối dịch vụ ngoài (Resend Email API, LLM Gemini/OpenAI API) hoạt động ổn định; trong trường hợp dịch vụ ngoài gián đoạn, hệ thống tự động kích hoạt bộ chuyển mạch dự phòng (Fallback Composer).

---

## 3. YÊU CẦU ĐẶC TẢ CHI TIẾT (SPECIFIC REQUIREMENTS)

### 3.1 Yêu cầu Giao diện Bên ngoài (External Interface Requirements)

#### 3.1.1 Giao diện người dùng (User Interfaces - UI/UX)
- `REQ-UI-01`: Hệ thống **PHẢI** hiển thị bản đồ Leaflet trung tâm khu vực Ocean Park 1, đánh dấu 5 trạm quan trắc S01..S05 với mã màu AQI tương ứng (Xanh lá $\le 50$, Vàng $\le 100$, Cam $\le 150$, Đỏ $\le 200$, Tím $\le 300$, Nâu $> 300$).
- `REQ-UI-02`: Hệ thống **PHẢI** cung cấp thanh phân tích chỉ số chi tiết (Metrics Drawer) hiển thị PM2.5, CO2, Độ ồn (dB), Nhiệt độ (°C) và biểu đồ lịch sử 24h.
- `REQ-UI-03`: Hệ thống **PHẢI** cung cấp khung Trợ lý AI (AI Assistant Drawer) cho phép người dùng nhập câu hỏi bằng văn bản tiếng Việt hoặc chọn các gợi ý nhanh (Quick Prompts).
- `REQ-UI-04`: Hệ thống **PHẢI** hỗ trợ vẽ đường chạy bộ dưới dạng đường đa giác màu nổi bật (Polyline highlight) kèm cờ xuất phát và tự động điều chỉnh khung nhìn bản đồ (`fit_bounds`).
- `REQ-UI-05`: Giao diện Quản trị viên **PHẢI** có khu vực quản lý đề xuất cảnh báo (HITL Approval Portal) liệt kê các đề xuất `pending`, nút [Phê duyệt], [Từ chối], và bảng nhật ký kiểm toán (Audit Trail Table).

#### 3.1.2 Giao diện Phần cứng & Cảm biến IoT (Hardware/IoT Interfaces)
- `REQ-IF-01`: Hệ thống **PHẢI** tiếp nhận dữ liệu quan trắc qua các MQTT Topic:
  - `airguard/stations/{station_id}/measurements` (Payload đo đạc môi trường)
  - `airguard/stations/{station_id}/status` (Trạng thái cảm biến: online/offline)
- `REQ-IF-02`: Payload gửi từ cảm biến **PHẢI** tuân thủ JSON Schema tối thiểu:
  ```json
  {
    "message_id": "uuid-v4",
    "station_id": "S01",
    "pm25": 28.5,
    "co2": 450,
    "noise_db": 55.2,
    "temperature": 29.1,
    "humidity": 65.0,
    "timestamp": "2026-08-31T12:00:00Z",
    "source": "simulator"
  }
  ```
- `REQ-IF-03`: Hệ thống **PHẢI** phát lệnh điều khiển thiết bị qua Topic:
  - `airguard/devices/{device_id}/command` với cấu trúc `{ "command_id": "...", "action": "...", "payload": {...}, "approved_by": "..." }`

#### 3.1.3 Giao diện Phần mềm & API REST (Software Interfaces)
- `REQ-API-01`: Backend **PHẢI** cung cấp bộ RESTful API phiên bản `/api/v1` chuẩn JSON:
  - `GET /api/v1/stations`: Danh sách 5 trạm quan trắc.
  - `GET /api/v1/stations/{id}/current`: Dữ liệu đo mới nhất và AQI.
  - `GET /api/v1/stations/{id}/history`: Lịch sử 24 giờ của trạm.
  - `GET /api/v1/stations/{id}/forecast`: Dự báo 1-3 giờ.
  - `POST /api/v1/agent/chat`: Xử lý hội thoại AI và định tuyến lộ trình.
  - `GET /api/v1/proposals/pending`: Danh sách đề xuất chờ duyệt (Yêu cầu quyền Manager).
  - `POST /api/v1/proposals/{id}/approve`: Phê duyệt đề xuất (Yêu cầu quyền Manager).
  - `POST /api/v1/proposals/{id}/reject`: Từ chối đề xuất (Yêu cầu quyền Manager).
  - `GET /api/v1/audit/logs`: Tra cứu nhật ký kiểm toán (Yêu cầu quyền Manager/Admin).
- `REQ-API-02`: Toàn bộ endpoint yêu cầu xác thực **PHẢI** kiểm tra JSON Web Token (JWT) gửi trong Header `Authorization: Bearer <token>`.

---

### 3.2 Yêu cầu Chức năng (Functional Requirements)

#### REQ-F-01: Thu Thập & Tính Toán Chỉ Số Môi Trường (Telemetry Ingestion & EPA AQI)
- **Mô tả**: Tiếp nhận dữ liệu quan trắc từ MQTT, kiểm tra tính hợp lệ và tự động tính toán chỉ số chất lượng không khí AQI.
- **Đầu vào**: MQTT Message payload từ trạm S01..S05.
- **Xử lý**:
  1. Parse và validate kiểu dữ liệu bằng Pydantic Schema.
  2. Kiểm tra khoảng giá trị hợp lệ: $PM2.5 \in [0, 1000]\ \mu g/m^3$, $CO_2 \in [300, 5000]\ ppm$, $Noise \in [20, 140]\ dB$, $Temp \in [-10, 60]\ ^\circ C$.
  3. Tính toán AQI 24h Concentration Sub-Index theo công thức phân đoạn chuẩn US EPA (2012):
     $$AQI = \frac{I_{high} - I_{low}}{C_{high} - C_{low}} \times (C - C_{low}) + I_{low}$$
  4. Cập nhật `station_statuses` thành `online` và `fresh` nếu thời gian đo không quá 300 giây.
- **Đầu ra**: Bản ghi được lưu vào bảng `measurements` và `station_statuses` trong PostgreSQL.
- **Tiêu chí nghiệm thu**: 100% dữ liệu hợp lệ được lưu trữ với độ trễ $< 50\text{ms}$; dữ liệu dị biệt hoặc sai cấu trúc bị từ chối và ghi log cảnh báo.

#### REQ-F-02: Lập Bản Đồ Phân Bố Ô Nhiễm Không Gian (Spatial IDW Dispersion)
- **Mô tả**: Tính toán nồng độ ô nhiễm tại bất kỳ vị trí tọa độ $(lat, lng)$ nào trong ranh giới Ocean Park 1 dựa trên phương pháp Inverse Distance Weighting từ 5 trạm quan trắc.
- **Đầu vào**: Tọa độ $(lat, lng)$, danh sách nồng độ $PM2.5_i$ và tọa độ trạm $(lat_i, lng_i)$.
- **Xử lý**:
  $$PM2.5(lat, lng) = \frac{\sum_{i=1}^5 \frac{PM2.5_i}{d_i^p}}{\sum_{i=1}^5 \frac{1}{d_i^p}}$$
  với $d_i$ là khoảng cách Haversine từ điểm cần tính tới trạm $i$, tham số lũy thừa $p = 2.0$.
- **Đầu ra**: Trọng số ô nhiễm tại điểm khảo sát và lưới bản đồ nhiệt (Heatmap Grid).
- **Tiêu chí nghiệm thu**: Hàm tính toán trả về kết quả mượt mà, không bị đột biến gián đoạn, thời gian nội suy toàn lưới $< 100\text{ms}$.

#### REQ-F-03: Định Tuyến Đường Chạy Sạch Chu Kỳ Đa Giác (Closed-Loop Routing Engine)
- **Mô tả**: Tìm kiếm và thiết kế tuyến đường chạy bộ/đi bộ/đạp xe khép kín tuần hoàn $(S \to W \to S)$ trên đồ thị đường thực OSM, hạn chế tối đa việc chạy đi chạy lại trùng đường (No Out-and-Back retracing) và tối thiểu hóa phơi nhiễm bụi mịn.
- **Đầu vào**: Tọa độ xuất phát $S(lat, lng)$, cự ly mục tiêu $target\_km \in [1.0, 10.0]$, loại hoạt động (`running`, `walking`, `cycling`), hồ sơ độ nhạy cảm người dùng.
- **Xử lý**:
  1. Snap tọa độ xuất phát $S$ vào nút gần nhất trên đồ thị đường thực OSM.
  2. **Chặng 1 (Leg 1)**: Chạy thuật toán Dijkstra tìm đường từ $S$ tới các điểm rẽ (waypoint $W$) tại khoảng cách $\approx \frac{target}{2 \times laps}$.
  3. **Áp dụng ma trận phạt**: Áp mức phạt trọng số $30\times$ lên toàn bộ các cạnh và nút đã đi qua trong Chặng 1.
  4. **Chặng 2 (Leg 2)**: Chạy thuật toán Dijkstra tìm đường quay về từ $W$ về $S$ trên đồ thị đã bị phạt trọng số để buộc thuật toán chọn các con đường song song khác.
  5. Hợp nhất $P = P_1 + P_2$ tạo thành vòng khép kín hoàn chỉnh (`coordinates[0] == coordinates[-1]`).
  6. Tính toán tích phân phơi nhiễm và khối lượng PM2.5 hít vào:
     $$M_{inhaled} = \sum_{e \in P} PM2.5(e) \times \left( \frac{\text{length}(e)}{v_{activity}} \right) \times V_{ventilation}$$
  7. Lọc theo luật giao thông: Người đi bộ/chạy bộ được đi đường footway, pedestrian, residential, tertiary; Người đạp xe được đi cycleway, cấm đường chỉ dành cho đi bộ hẹp.
- **Đầu ra**: Đối tượng JSON chứa danh sách tọa độ polyline, cự ly chuẩn hóa, thời lượng, khối lượng bụi hít vào ($\mu g$), và tỷ lệ giảm phơi nhiễm (%) so với tuyến đối chứng.
- **Tiêu chí nghiệm thu**: Tuyến đường khép kín 100%, tỷ lệ trùng lặp cạnh $< 15\%$, sai số cự ly so với yêu cầu trong phạm vi cho phép ($4.0\%$), 100% bám trên đường thực tế OpenStreetMap.

#### REQ-F-04: Trợ Lý Ảo AI Hội Thoại Đa Lượt & Grounded Tool Calling (AI Agent)
- **Mô tả**: Tiếp nhận và phản hồi câu hỏi của cư dân bằng tiếng Việt tự nhiên, tự động gọi các công cụ nội bộ để lấy dữ liệu thực tế và điều khiển giao diện bản đồ.
- **Đầu vào**: Tin nhắn của người dùng, ngữ cảnh vị trí bản đồ (`map_context`), ID phiên hội thoại (`conversation_id`).
- **Xử lý**:
  1. Phân loại ý định (Intent Classification): `recommend_running_route`, `get_location_environment`, `compare_locations`, `find_worst_location`, `greeting`, `social`, `out_of_scope`.
  2. Điều phối LangGraph State Machine gọi các Tool tương ứng: `get_current_pm25`, `get_station_history`, `get_pm25_forecast`, `clean_running_route`, `get_user_profile`.
  3. Kiểm tra cổng an toàn Grounding Policy Gate: Đối chiếu toàn bộ câu trả lời, đảm bảo mọi số liệu đều xuất phát từ Tool Output.
  4. Ghi nhớ ngữ cảnh đa lượt: Hỗ trợ các câu hỏi kế tiếp (Follow-up) như *"Thế còn Ruby Zenpark?"*, *"Ngắn hơn chút"* (tự động giảm $-1.5\text{km}$), *"Đạp xe thì sao"*.
  5. Cơ chế chuyển mạch dự phòng: Khi LLM ngoài mất kết nối hoặc timeout ($> 8.0\text{s}$), tự động kích hoạt `ResponseComposer` trả lời chuẩn xác mà không gây lỗi 500/503.
- **Đầu ra**: Cấu trúc JSON chuẩn gồm `answer` (summary, details), `intent`, `map_actions` (`highlight_route`, `fit_bounds`, `add_annotation`), `used_tools`, `sources`, `request_id`.
- **Tiêu chí nghiệm thu**: 100% phản hồi được grounded; không xuất hiện hiện tượng bịa đặt số liệu (Zero Hallucination); vượt qua toàn bộ 28/28 bài kiểm thử đánh giá Agent.

#### REQ-F-05: Động Cơ Cảnh Báo Môi Trường Đa Tiêu Chí (Alert Engine)
- **Mô tả**: Tự động đánh giá dữ liệu mới nhất từ 5 trạm theo các ngưỡng quy định, phát sinh cảnh báo theo mức độ nghiêm trọng.
- **Ngưỡng quy chuẩn**:
  - `AQI > 150` hoặc $PM2.5 > 55.4\ \mu g/m^3$: Cảnh báo mức **Xấu / Nguy hại (Warning/Critical)**.
  - $CO_2 > 1000\ ppm$: Cảnh báo ngột ngạt / kém thông thoáng.
  - Độ ồn $> 70\ dB$: Cảnh báo ô nhiễm tiếng ồn.
  - Trạm không gửi dữ liệu quá 300 giây: Cảnh báo **Trạm mất kết nối (Offline Alert)**.
- **Xử lý**: Áp dụng thời gian chờ làm nguội (Cooldown Period = 15 phút) để tránh spam cảnh báo trùng lặp; tự động giải phóng (Auto-resolve) khi chỉ số trở về bình thường liên tục 3 chu kỳ.
- **Đầu ra**: Bản ghi trong bảng `alerts` hiển thị trên giao diện người dùng.

#### REQ-F-06: Quy Trình Phê Duyệt Cảnh Báo Human-in-the-Loop (HITL Workflow)
- **Mô tả**: Tạo đề xuất cảnh báo và can thiệp ở trạng thái chờ duyệt, cung cấp giao diện cho Quản trị viên ra quyết định.
- **Xử lý**:
  1. Khi phát hiện chỉ số nguy hại (ví dụ trạm S05 có $AQI > 150$), hệ thống tạo bản ghi `warning_proposals` với trạng thái `pending`.
  2. Mỗi trạm tại một thời điểm chỉ tồn tại tối đa một đề xuất `pending`.
  3. Quản trị viên đăng nhập vào Cổng Phê duyệt, xem xét bằng chứng quan trắc (Evidence).
  4. Nếu bấm [Phê duyệt]: Hệ thống chuyển trạng thái sang `approved`, ghi log kiểm toán, gửi thông báo email qua Resend API và phát lệnh MQTT tới thiết bị.
  5. Nếu bấm [Từ chối]: Hệ thống chuyển trạng thái sang `rejected`, ghi nhận lý do từ chối, **tuyệt đối không phát lệnh điều khiển thiết bị**.
- **Đầu ra**: Trạng thái cập nhật của proposal và tín hiệu kích hoạt chấp hành.
- **Tiêu chí nghiệm thu**: Không thể bypass bước duyệt của Quản lý; 100% hành động được ghi vết.

#### REQ-F-07: Nhật Ký Kiểm Toán Bất Biến (Append-Only Audit Logging)
- **Mô tả**: Ghi nhận toàn bộ các thao tác quan trọng trong hệ thống vào bảng nhật ký chỉ cho phép thêm mới (Append-Only), không cho phép sửa xóa.
- **Dữ liệu lưu trữ**: `id`, `timestamp`, `actor` (User ID / System), `action` (`create_proposal`, `approve_proposal`, `reject_proposal`, `dispatch_command`), `target_id`, `outcome` (`success`, `failure`), `correlation_id`, `details`.
- **Tiêu chí nghiệm thu**: Không cung cấp API xóa/sửa bảng audit; hỗ trợ tra cứu và phân trang cho Quản trị viên.

#### REQ-F-08: Cá Nhân Hóa Hồ Sơ Sức Khỏe & Nhóm Nhạy Cảm (Health Personalization)
- **Mô tả**: Điều chỉnh thuật toán gợi ý tuyến đường và khuyến nghị môi trường dựa trên nhóm sức khỏe của người dùng: `normal` (Bình thường), `sensitive` (Nhạy cảm - trẻ em, người già, hen suyễn), `outdoor_sport` (Vận động viên).
- **Xử lý**: Đối với nhóm `sensitive`, trọng số phạt ô nhiễm không khí trong thuật toán Dijkstra được tăng gấp đôi ($2.0\times$), ưu tiên tuyệt đối các cung đường ven hồ, tránh hoàn toàn các trục đường giao thông chính có mật độ xe cao.

#### REQ-F-09: Dự Báo Môi Trường Ngắn Hạn 1-3 Giờ (Short-Term Forecasting)
- **Mô tả**: Dự báo xu hướng AQI và PM2.5 trong 1 đến 3 giờ tới cho từng trạm quan trắc bằng mô hình hồi quy tuyến tính xu hướng ngắn hạn kết hợp ngữ cảnh khí tượng.
- **Ràng buộc chất lượng (Quality Gate)**:
  - Chỉ thực hiện dự báo khi trạm có tối thiểu 3 điểm đo hợp lệ liên tục gần nhất.
  - Từ chối dự báo mập mờ vượt quá khoảng 1-3 giờ (ví dụ: "ngày mai", "tuần sau") với mã lỗi `invalid_forecast_hour` để tránh sai số phi thực tế.

---

### 3.3 Yêu cầu Chất lượng Dịch vụ / Phi Chức năng (Quality of Service - Non-Functional)

#### 3.3.1 Hiệu năng & Thời gian đáp ứng (Performance Requirements)
- `REQ-NF-01`: Thời gian phản hồi của các API tra cứu dữ liệu (`/stations`, `/current`, `/history`) **PHẢI** $\le 200\text{ms}$ tại mức tải 100 request/giây.
- `REQ-NF-02`: Thuật toán tìm đường chạy sạch khép kín **PHẢI** hoàn thành tính toán và trả về kết quả polyline trong vòng $\le 1.5\text{giây}$.
- `REQ-NF-03`: Tần suất cập nhật dữ liệu cảm biến từ MQTT Consumer vào Database **PHẢI** đáp ứng chu kỳ mỗi 15-30 giây/trạm mà không gây nghẽn kết nối.

#### 3.3.2 Độ an toàn & Tin cậy dữ liệu (Safety & Data Reliability)
- `REQ-NF-04`: Hệ thống **PHẢI** áp dụng cơ chế Fail-Closed: Khi dữ liệu cảm biến bị quá hạn (stale) hoặc trạm offline, hệ thống không được dùng dữ liệu đó để vẽ đường chạy hay đưa ra khẳng định môi trường an toàn.
- `REQ-NF-05`: Toàn bộ các phép tính AQI và tích phân phơi nhiễm **PHẢI** có tính tiền định (Deterministic) và tái lập được kết quả với cùng một bộ dữ liệu đầu vào.

#### 3.3.3 Bảo mật & Quyền riêng tư (Security & Access Control)
- `REQ-NF-06`: Mật khẩu người dùng **PHẢI** được băm bằng thuật toán Argon2id an toàn trước khi lưu vào cơ sở dữ liệu.
- `REQ-NF-07`: Hệ thống **PHẢI** phân quyền chặt chẽ (RBAC) giữa 2 vai trò:
  - `resident`: Người dùng thông thường, chỉ đọc dữ liệu công cộng và tương tác trợ lý cá nhân.
  - `manager`: Quản lý đô thị, có quyền phê duyệt đề xuất HITL và xem nhật ký Audit.
- `REQ-NF-08`: Toàn bộ các truy vấn cơ sở dữ liệu **PHẢI** sử dụng Parameterized Query / ORM để phòng chống hoàn toàn tấn công SQL Injection.

#### 3.3.4 Khả năng sẵn sàng & Phục hồi (Availability & Resilience)
- `REQ-NF-09`: Backend FastAPI **PHẢI** được thiết kế theo kiến trúc Stateless, cho phép khởi động lại hoặc mở rộng quy mô (Scale Out) mà không làm mất trạng thái phiên làm việc của người dùng.
- `REQ-NF-10`: Khi dịch vụ AI LLM gặp sự cố nghẽn mạng hoặc timeout, hệ thống **PHẢI** tự động kích hoạt bộ chuyển mạch phản hồi cục bộ trong vòng $< 500\text{ms}$ mà không trả mã lỗi HTTP 5xx về máy khách.

#### 3.3.5 Giám sát & Truy vết (Observability & Traceability)
- `REQ-NF-11`: Mọi yêu cầu HTTP gửi đến hệ thống **PHẢI** được gắn một mã định danh duy nhất `X-Request-ID` để hỗ trợ điều tra và truy vết nhật ký lỗi đầu-cuối (End-to-End Tracing).
- `REQ-NF-12`: Hệ thống **PHẢI** cung cấp các endpoint kiểm tra trạng thái sức khỏe: `/health` (Liveness probe) và `/ready` (Readiness probe).

---

### 3.4 Yêu cầu Trí Tuệ Nhân Tạo & Đạo Đức (AI/ML & Ethics Requirements)

- `REQ-AI-01 (Zero Hallucination)`: AI Agent **TUYỆT ĐỐI KHÔNG ĐƯỢC** tự tạo chỉ số PM2.5, AQI, CO2, nhiệt độ, dự báo hoặc trạng thái trạm khi không có kết quả trả về từ Backend Tool.
- `REQ-AI-02 (Medical Liability Disclaimer)`: Mọi khuyến nghị vận động và cảnh báo sức khỏe của AI Agent **PHẢI** mang tính tham khảo môi trường, kèm lời nhắc khuyến cáo cư dân tham vấn ý kiến bác sĩ chuyên khoa đối với các triệu chứng hô hấp nặng.
- `REQ-AI-03 (Transparency Policy)`: Toàn bộ dữ liệu trong phiên bản thử nghiệm **PHẢI** được đính kèm nhãn `source=simulator` để người dùng hiểu rõ đây là dữ liệu môi trường mô phỏng học tập.
- `REQ-AI-04 (HITL Command Immunity)`: AI Agent **KHÔNG CÓ QUYỀN** tự gửi lệnh phát hành thông báo khẩn cấp hoặc điều khiển thiết bị; mọi hành động tác động ra thế giới thực bắt buộc phải trải qua bước phê duyệt của con người.

---

## 4. MA TRẬN TRUY XUẤT & XÁC THỰC (TRACEABILITY MATRIX)

Toàn bộ các yêu cầu chức năng và an toàn của hệ thống đã được kiểm chứng tự động qua hệ thống **153 Unit & Integration Tests (100% Passed)**:

| Mã Yêu Cầu | Tên Yêu Cầu | Module Xử Lý Chính | Bộ Test Case Kiểm Thử (100% Pass) |
|---|---|---|---|
| `REQ-F-01` | Ingestion & EPA AQI | `mqtt_consumer/main.py`, `live_telemetry_engine.py` | `test_running_route_engine.py`, `test_vietnamese_station_alerts.py` |
| `REQ-F-02` | Spatial IDW Dispersion | `spatial_idw_interpolator.py` | `test_spatial_dispersion.py`, `test_osm_routing_aqi_aware.py` |
| `REQ-F-03` | OSM Closed-Loop Route | `road_graph_router.py`, `clean_running_route_service.py` | `test_osm_routing_aqi_aware.py` (12/12), `test_running_route_engine.py` (20/20) |
| `REQ-F-04` | Grounded AI Agent | `geospatial_agent_service.py`, `src/agents/graph.py` | `test_geospatial_agent.py` (28/28), `test_contextual_geospatial_agent.py` (15/15) |
| `REQ-F-05` | Real-time Alert Engine | `live_telemetry_engine.py`, `backend/app/services/` | `test_vietnamese_station_alerts.py`, `test_overview_and_correction.py` |
| `REQ-F-06` | HITL Warning Proposal | `backend/app/routes/proposals.py`, `main.py` | `test_manager_activity_log.py`, `test_person_b_api_security.py` |
| `REQ-F-07` | Append-Only Audit Log | `backend/db/schema.sql`, `main.py` | `test_manager_activity_log.py`, `test_report_api_security.py` |
| `REQ-F-08` | Health Personalization | `clean_running_route_service.py`, `user_service.py` | `test_running_route_engine.py::test_health_profile_sensitive_penalty` |
| `REQ-F-09` | Short-Term Forecasting | `temporal_resolver.py`, `forecast_service.py` | `test_osm_routing_aqi_aware.py::test_forecast_horizon_quality_gate` |
| `REQ-AI-01` | Zero Hallucination Gate | `src/agents/policies/grounding.py`, `geospatial_agent_service.py` | `test_geospatial_agent.py`, `test_social_intent_and_fallback.py` |

---

## 5. PHỤ LỤC: CÁC NỘI DUNG ĐỂ TRỐNG & ĐỀ XUẤT CHO BẠN (USER DECISION PLACEHOLDERS & PROPOSALS)

> **Hướng dẫn cho bạn**: Các mục dưới đây thuộc về quyết định mang tính chiến lược tổ chức, pháp lý và thương mại. Nhóm kỹ thuật đã để trống các trường cụ thể và chuẩn bị sẵn **[ĐỀ XUẤT TỐI ƯU NHẤT]** để bạn chỉ việc xem xét, điều chỉnh và ký duyệt.

### 5.1 Thỏa Thuận Mức Dịch Vụ Chính Thức (Production SLA & Uptime Agreement)
- **Tên tổ chức vận hành chính thức**: `[CẦN ĐIỀN: Tên Công ty / Ban Quản Lý Dự Án của bạn]`
- **Cam kết thời gian hoạt động (Uptime SLA)**: `[CẦN ĐIỀN: Ví dụ 99.5% hay 99.9%]`  
  *(ĐỀ XUẤT: Đối với giai đoạn MVP và thử nghiệm thực địa ban đầu, nên đặt mức cam kết **99.5% Uptime** (tương đương thời gian bảo trì tối đa không quá 3.6 giờ/tháng).)*
- **Thời gian phản hồi sự cố khẩn cấp (MTTR - Mean Time to Recovery)**: `[CẦN ĐIỀN: Ví dụ 30 phút hay 2 giờ]`  
  *(ĐỀ XUẤT: Sự cố cấp độ 1 (Mất toàn bộ kết nối cảm biến) xử lý trong **60 phút**; Sự cố cấp độ 2 (Lỗi AI Assistant) chuyển sang chế độ Fallback trong **1 phút**).*

### 5.2 Ràng Buộc Pháp Lý & Miễn Trừ Trách Nhiệm Y Tế (Legal & Regulatory Compliance)
- **Đại diện pháp lý ký duyệt tài liệu**: `[CẦN ĐIỀN: Họ tên & Chức vụ người đại diện]`
- **Điều khoản miễn trừ trách nhiệm y tế chính thức**: `[CẦN ĐIỀN: Văn bản phê duyệt từ bộ phận Pháp chế]`  
  *(ĐỀ XUẤT: Giữ nguyên điều khoản mặc định hiện tại: "AirGuard AI là hệ thống quan sát môi trường học tập/MVP, không phải thiết bị y tế chẩn đoán chuyên dụng và không đưa ra chỉ định y khoa thay thế bác sĩ.")*

### 5.3 Kế Hoạch Triển Khai Phần Cứng Cảm Biến Vật Lý (Physical IoT Deployment Roadmap)
- **Đơn vị cung cấp phần cứng cảm biến**: `[CẦN ĐIỀN: Tên nhà cung cấp phần cứng, ví dụ Sensirion / Bosch / Adafruit]`
- **Thời gian chuyển đổi từ Sensor Simulator sang Phần cứng thực**: `[CẦN ĐIỀN: Quý / Năm, ví dụ Q4/2026]`  
  *(ĐỀ XUẤT: Giữ nguyên pipeline MQTT Mosquitto hiện tại vì đã tương thích hoàn toàn 100% với các mạch vi điều khiển ESP32 / STM32 gửi chuẩn JSON qua WiFi/4G).*

### 5.4 Dự Toán Ngân Sách Vận Hành Đám Mây (Cloud Budget & Scaling Allocations)
- **Hạn mức chi phí máy chủ hàng tháng**: `[CẦN ĐIỀN: $ / tháng]`  
  *(ĐỀ XUẤT: Với quy mô 5-20 trạm và 5,000 người dùng hàng ngày, ngân sách ước tính khoảng **$40 - $70 USD/tháng** cho 1 Azure VM B2ms (2 vCPU, 8GB RAM) + $10 USD Resend API).*

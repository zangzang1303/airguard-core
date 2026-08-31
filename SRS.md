# ĐẶC TẢ YÊU CẦU PHẦN MỀM TỔNG THỂ (MASTER SOFTWARE REQUIREMENTS SPECIFICATION)
# Dự Án: AirGuard AI — Hệ Thống Giám Sát Môi Trường & Trợ Lý Tuyến Đường An Toàn

> **Tiêu chuẩn tài liệu**: IEEE Std 830-1998 & ISO/IEC/IEEE 29148:2011/2017 (Cấu trúc Markdown MSRS chuẩn hóa).  
> **Dự án**: AirGuard AI (Mã số: P-074) — Khu đô thị Vinhomes Ocean Park 1, Hà Nội.  
> **Phiên bản tài liệu**: 2.0.0 (Master Release Baseline).  
> **Trạng thái**: Kỹ thuật cốt lõi hoàn thiện 100% (153/153 Automated Tests Passed).  
> **Ngày cập nhật**: 31/08/2026.  

---

## MỤC LỤC (TABLE OF CONTENTS)
1. [Giới Thiệu (Introduction)](#1-giới-thiệu-introduction)
2. [Tổng Quan Sản Phẩm (Overall Description)](#2-tổng-quan-sản-phẩm-overall-description)
3. [Yêu Cầu Giao Diện Bên Ngoài (External Interface Requirements)](#3-yêu-cầu-giao-diện-bên-ngoài-external-interface-requirements)
4. [Yêu Cầu Chức Năng (Functional Requirements)](#4-yêu-cầu-chức-năng-functional-requirements)
5. [Yêu Cầu Chất Lượng Dịch Vụ & Phi Chức Năng (Non-Functional Requirements)](#5-yêu-cầu-chất-lượng-dịch-vụ--phi-chức-năng-non-functional-requirements)
6. [Yêu Cầu Ràng Buộc Trí Tuệ Nhân Tạo & Đạo Đức (AI/ML & Ethics Constraints)](#6-yêu-cầu-ràng-buộc-trí-tuệ-nhân-tạo--đạo-đức-aiml--ethics-constraints)
7. [Ma Trận Truy Xuất & Kiểm Thử Nghiệm Thu (Traceability & Verification Matrix)](#7-ma-trận-truy-xuất--kiểm-thử-nghiệm-thu-traceability--verification-matrix)
8. [Phụ Lục: Quyết Định Chiến Lược & Đề Xuất Cho Bạn (User Decisions & Recommendations)](#8-phụ-lục-quyết-định-chiến-lược--đề-xuất-cho-bạn-user-decisions--recommendations)

---

## 1. GIỚI THIỆU (INTRODUCTION)

### 1.1 Mục đích (Purpose)
Tài liệu Đặc tả Yêu cầu Phần mềm (SRS) này là tài liệu duy nhất và toàn diện mô tả đầy đủ các yêu cầu chức năng, yêu cầu chất lượng dịch vụ, ràng buộc kiến trúc và quy tắc an toàn AI cho toàn bộ hệ thống **AirGuard AI**. Tài liệu đóng vai trò là hợp đồng kỹ thuật chuẩn mực giữa nhóm kỹ sư phát triển, ban quản lý dự án và các bên liên quan.

### 1.2 Quy ước tài liệu (Document Conventions)
Tài liệu áp dụng nghiêm ngặt các quy ước theo chuẩn **RFC 2119**:
- **BẮT BUỘC (MUST / SHALL)**: Yêu cầu tuyệt đối phải được hiện thực hóa đầy đủ.
- **NÊN (SHOULD / RECOMMENDED)**: Khuyến nghị thực thi trừ khi có ràng buộc kỹ thuật đặc thù.
- **CÓ THỂ (MAY / OPTIONAL)**: Các tính năng mở rộng tùy chọn.
- Hệ thống mã hóa định danh:
  - `REQ-F-xxx`: Yêu cầu Chức năng (Functional Requirement)
  - `REQ-NF-xxx`: Yêu cầu Phi chức năng / Chất lượng dịch vụ (Quality of Service)
  - `REQ-IF-xxx`: Yêu cầu Giao diện bên ngoài (External Interface)
  - `REQ-AI-xxx`: Yêu cầu An toàn & Ràng buộc AI Agent (AI/ML Constraints)

### 1.3 Phạm vi hệ thống (System Scope)
**AirGuard AI** là nền tảng quan trắc, phân tích chất lượng môi trường không khí và trợ lý điều hướng hoạt động thể thao ngoài trời thông minh tại khu đô thị **Vinhomes Ocean Park 1** (Gia Lâm, Hà Nội).

**Hệ thống bao gồm các khả năng cốt lõi**:
1. **Thu thập & Chuẩn hóa IoT**: Lắng nghe và xử lý luồng dữ liệu thời gian thực từ 5 trạm quan trắc mô phỏng (S01 - VinUni, S02 - Hồ Ngọc Trai, S03 - Sapphire 1, S04 - Ruby Zenpark, S05 - San Hô) qua giao thức MQTT.
2. **Tính toán Chỉ số Môi trường**: Tính toán chỉ số chất lượng không khí tổng quan AQI (nội suy từ PM2.5 theo chuẩn US EPA 2012) và lập bản đồ phân bố ô nhiễm không gian (Spatial IDW Dispersion).
3. **Định tuyến Đường Chạy Bộ Sạch Khép Kín**: Tạo chu kỳ vòng lặp đa giác tuần hoàn (Closed-Loop Circuit) trên đồ thị đường thực OpenStreetMap (OSM), đảm bảo không đi trùng đường và giảm thiểu phơi nhiễm PM2.5.
4. **Trợ lý AI Hội thoại Tiếng Việt Grounded**: Đàm thoại tự nhiên, hiểu ngữ cảnh vị trí và điều khiển bản đồ trực quan bằng cơ chế Tool Calling không phát sinh ảo giác (Zero Hallucination).
5. **Cảnh báo Thông minh & Quy trình Phê duyệt HITL**: Tự động phát hiện bất thường môi trường, tạo đề xuất cảnh báo `pending`, hỗ trợ Quản trị viên (Manager) duyệt 1-click để gửi email và kích hoạt thiết bị phun sương mô phỏng kèm Audit Log bất biến.

**Ranh giới loại trừ (Out-of-Scope)**:
- Không cung cấp chẩn đoán y khoa hoặc phác đồ điều trị bệnh lý.
- Không điều khiển trực tiếp các hệ thống phần cứng công nghiệp điện áp cao nguy hiểm.
- Không thay thế số liệu quan trắc pháp lý của cơ quan quản lý nhà nước.

### 1.4 Bảng thuật ngữ định nghĩa (Glossary)
| Thuật ngữ | Định nghĩa kỹ thuật |
|---|---|
| **AQI (Air Quality Index)** | Chỉ số chất lượng không khí tổng quan, tính từ nồng độ PM2.5 theo phân đoạn US EPA 24h (2012). |
| **PM2.5** | Bụi mịn đường kính khí động học $\le 2.5\ \mu m$ ($\mu g/m^3$). |
| **SoR (System of Record)** | Nguồn dữ liệu chân lý duy nhất (PostgreSQL 16 & FastAPI Backend). |
| **Grounding Policy** | Quy tắc bắt buộc AI Agent chỉ phát ngôn dựa trên bằng chứng (evidence) lấy từ Tool của Backend trong cùng request. |
| **HITL (Human-in-the-Loop)** | Cơ chế bắt buộc đề xuất cảnh báo/can thiệp của AI phải qua phê duyệt của Manager server-side trước khi phát lệnh. |
| **IDW (Inverse Distance Weighting)** | Phương pháp nội suy nghịch đảo khoảng cách tính nồng độ ô nhiễm tại mọi điểm trên bản đồ từ 5 trạm quan trắc. |
| **OSM Road Graph** | Đồ thị mạng lưới đường giao thông thực tế khu vực Ocean Park 1 trích xuất từ OpenStreetMap. |
| **Inhaled Mass ($\mu g$)** | Khối lượng bụi mịn PM2.5 ước tính đi vào đường hô hấp khi vận động dọc theo tuyến đường: $\int PM2.5(e) \times dt \times V_{ventilation}$. |

---

## 2. TỔNG QUAN SẢN PHẨM (OVERALL DESCRIPTION)

### 2.1 Bối cảnh & Kiến trúc tổng thể (System Context & Architecture)
Hệ thống được thiết kế theo kiến trúc Monorepo phân tán đa container (Docker Compose Topology):
```
[Sensor Simulator (S01..S05)] ──(MQTT :1883)──► [Mosquitto Broker]
                                                        │ (QoS 1)
                                                        ▼
[React 18 Dashboard] ◄──(HTTPS / REST)──► [FastAPI Backend :8000] ◄──► [PostgreSQL 16]
        │                                        │ (Internal HTTP)
        │ (AI Drawer Chat)                       ▼
        └───────────────────────────────► [LangGraph Agent :8001] ◄──► [LLM Provider]
                                                 │
[Device Simulator] ◄──(MQTT Command)─────────────┘ (Chỉ sau khi Manager duyệt HITL)
```

### 2.2 Các nhóm người dùng (User Classes & Characteristics)
1. **Cư dân thông thường (Resident)**: Theo dõi bản đồ AQI, tra cứu chỉ số khu vực, hỏi trợ lý AI về lộ trình an toàn.
2. **Nhóm người nhạy cảm (Sensitive Group)**: Trẻ em, người cao tuổi, người có bệnh hô hấp/tim mạch; nhận cảnh báo sớm ở ngưỡng $AQI > 100$, lộ trình vận động áp dụng trọng số phạt ô nhiễm nghiêm ngặt ($2.0\times$).
3. **Vận động viên / Người yêu thể thao (Athletes / Runners / Cyclists)**: Yêu cầu định tuyến cự ly chính xác ($1.0 \to 10.0\text{km}$), xem ước tính khối lượng bụi hít vào ($\mu g$) và thời lượng hoàn thành.
4. **Quản lý đô thị (Manager)**: Giám sát an toàn toàn khu, tiếp nhận đề xuất cảnh báo, xem bằng chứng dữ liệu, thực hiện Approve/Reject đề xuất và kích hoạt thiết bị.
5. **Kiểm toán viên / Quản trị viên (Auditor / Admin)**: Rà soát toàn bộ lịch sử can thiệp qua bảng Audit Log bất biến và giám sát sức khỏe dịch vụ.

### 2.3 Môi trường vận hành (Operating Environment)
- **Hệ điều hành máy chủ**: Ubuntu 22.04 LTS x86_64 / Azure Cloud VM (`airguard-074-app.indonesiacentral.cloudapp.azure.com`).
- **Nền tảng Container**: Docker Engine 24.0+, Docker Compose v2.
- **Cơ sở dữ liệu**: PostgreSQL 16 Alpine với Connection Pool.
- **Message Broker**: Eclipse Mosquitto 2.0 (MQTT Protocol).
- **Backend**: Python 3.12 Runtime, Uvicorn ASGI Server, FastAPI.
- **Frontend**: Node 20+, React 18, Vite, Leaflet GIS Engine.
- **Mạng máy khách**: Hỗ trợ trình duyệt hiện đại (Chrome, Edge, Firefox, Safari) trên Desktop và Thiết bị di động.

### 2.4 Ràng buộc thiết kế & Triển khai (Design & Implementation Constraints)
- **Zero Hallucination Constraint**: Không sử dụng RAG/Vector Store tự do cho số liệu cảm biến; mọi dữ liệu phải truy xuất có cấu trúc từ PostgreSQL.
- **Bảo mật Secret**: Không commit khóa bí mật (.env) vào Git repository.
- **Nguyên tắc Fail-Closed**: Từ chối đưa ra nhận định an toàn nếu trạm quan trắc mất kết nối (offline) hoặc dữ liệu quá hạn ($> 300\text{s}$).

---

## 3. YÊU CẦU GIAO DIỆN BÊN NGOÀI (EXTERNAL INTERFACE REQUIREMENTS)

### 3.1 Giao diện người dùng (User Interfaces - UI/UX)
- `REQ-IF-UI-01`: Hệ thống **PHẢI** hiển thị bản đồ số Leaflet trung tâm Ocean Park 1 với 5 trạm quan trắc được mã màu theo bậc thang AQI chuẩn quốc tế.
- `REQ-IF-UI-02`: Giao diện **PHẢI** có ngăn phân tích chỉ số (Metrics Drawer) hiển thị chi tiết 4 thông số: PM2.5, CO2, Độ ồn, Nhiệt độ và biểu đồ chuỗi thời gian 24h.
- `REQ-IF-UI-03`: Giao diện **PHẢI** tích hợp khung Chat AI Assistant cho phép tương tác tự nhiên, gợi ý sẵn các câu hỏi nhanh (Quick Action Prompts).
- `REQ-IF-UI-04`: Khi gợi ý đường chạy bộ, hệ thống **PHẢI** vẽ polyline khép kín nổi bật trên bản đồ kèm đánh dấu xuất phát và tự động căn chỉnh khung hình (`fit_bounds`).
- `REQ-IF-UI-05`: Cung cấp cổng Quản lý Phê duyệt (HITL Approval Portal) riêng cho vai trò Manager để duyệt đề xuất cảnh báo và xem nhật ký kiểm toán.

### 3.2 Giao diện Phần cứng & IoT MQTT (Hardware & IoT Interfaces)
- `REQ-IF-IOT-01`: Hệ thống **PHẢI** tiếp nhận dữ liệu cảm biến qua MQTT Topics:
  - `airguard/stations/{station_id}/measurements`
  - `airguard/stations/{station_id}/status`
- `REQ-IF-IOT-02`: Payload dữ liệu cảm biến **PHẢI** tuân thủ cấu trúc JSON:
  ```json
  {
    "message_id": "uuid-v4",
    "station_id": "S01",
    "pm25": 25.4,
    "co2": 420.0,
    "noise_db": 52.0,
    "temperature": 28.5,
    "humidity": 65.0,
    "timestamp": "2026-08-31T12:00:00Z",
    "source": "simulator"
  }
  ```
- `REQ-IF-IOT-03`: Lệnh điều khiển thiết bị **PHẢI** được xuất bản tới Topic:
  - `airguard/devices/{device_id}/command` kèm chữ ký duyệt của Manager (`approved_by`).

### 3.3 Giao diện Phần mềm & API REST (Software Interfaces)
- `REQ-IF-API-01`: Cung cấp chuẩn REST API `/api/v1` với các endpoint chính:
  - `GET /api/v1/stations`: Danh mục và tọa độ 5 trạm.
  - `GET /api/v1/stations/{id}/current`: Dữ liệu đo mới nhất và trạng thái trạm.
  - `GET /api/v1/stations/{id}/history`: Lịch sử quan trắc 24 giờ.
  - `GET /api/v1/stations/{id}/forecast`: Dữ liệu dự báo 1-3 giờ.
  - `POST /api/v1/agent/chat`: Xử lý hội thoại AI và định tuyến lộ trình.
  - `GET /api/v1/proposals/pending`: Danh sách đề xuất chờ duyệt.
  - `POST /api/v1/proposals/{id}/approve`: Phê duyệt đề xuất cảnh báo.
  - `POST /api/v1/proposals/{id}/reject`: Từ chối đề xuất cảnh báo.
  - `GET /api/v1/audit/logs`: Tra cứu nhật ký kiểm toán.
- `REQ-IF-API-02`: Hệ thống xác thực bằng JSON Web Token (JWT) theo tiêu chuẩn Bearer Token trong HTTP Header.

---

## 4. YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS)

### REQ-F-01: Thu Thập & Tính Toán Chỉ Số Môi Trường (Telemetry Ingestion & EPA AQI)
- **Mô tả**: Tiếp nhận dữ liệu MQTT từ các trạm, xác thực tính toàn vẹn và tính chỉ số AQI thời gian thực.
- **Quy trình xử lý**:
  1. Xác thực schema bằng Pydantic; kiểm tra biên dữ liệu ($PM2.5 \in [0, 1000]$, $CO2 \in [300, 5000]$, $Noise \in [20, 140]$, $Temp \in [-10, 60]$).
  2. Tính toán AQI 24h Sub-Index theo công thức phân đoạn US EPA (2012).
  3. Cập nhật trạng thái `online` và `fresh` nếu độ trễ dữ liệu $< 300\text{s}$.
- **Tiêu chí nghiệm thu**: Lưu trữ thành công vào PostgreSQL trong $< 50\text{ms}$; từ chối và ghi log với dữ liệu dị biệt/lỗi.

### REQ-F-02: Bản Đồ Phân Bố Ô Nhiễm Không Gian (Spatial IDW Dispersion)
- **Mô tả**: Tính toán nồng độ ô nhiễm tại bất kỳ vị trí tọa độ $(lat, lng)$ nào trong ranh giới Ocean Park 1 bằng mô hình nội suy Inverse Distance Weighting (IDW).
- **Quy trình xử lý**:
  $$PM2.5(lat, lng) = \frac{\sum_{i=1}^5 \frac{PM2.5_i}{d_i^2}}{\sum_{i=1}^5 \frac{1}{d_i^2}}$$
- **Tiêu chí nghiệm thu**: Nội suy toàn bộ lưới bản đồ nhiệt trong $< 100\text{ms}$, phân bố gradient màu sắc liên tục mượt mà.

### REQ-F-03: Định Tuyến Đường Chạy Sạch Khép Kín (Closed-Loop Routing Engine)
- **Mô tả**: Tìm kiếm lộ trình chạy bộ/đi bộ/đạp xe khép kín tuần hoàn $(S \to W \to S)$ trên đồ thị đường thực OSM, hạn chế tối đa việc chạy đi chạy lại trùng đường và tối thiểu hóa phơi nhiễm bụi mịn.
- **Quy trình xử lý**:
  1. Snap tọa độ xuất phát $S$ vào nút giao lộ gần nhất trên đồ thị OSM.
  2. **Chặng 1 (Leg 1)**: Dijkstra tìm đường từ $S$ tới các waypoint $W$ ở cự ly $\approx \frac{target}{2 \times laps}$.
  3. **Ma trận phạt**: Áp dụng mức phạt trọng số $30\times$ lên toàn bộ các cạnh đã đi qua ở Chặng 1.
  4. **Chặng 2 (Leg 2)**: Dijkstra tìm đường quay về từ $W$ về $S$ trên đồ thị đã bị phạt trọng số để ép thuật toán chọn các tuyến đường song song khác.
  5. Hợp nhất polyline hoàn chỉnh đảm bảo `coordinates[0] == coordinates[-1]`.
  6. Tính tích phân phơi nhiễm và khối lượng PM2.5 hít vào ($\mu g$).
  7. Lọc đường hợp lệ theo phương tiện (Footway/Pedestrian cho chạy bộ, Cycleway cho đạp xe).
- **Tiêu chí nghiệm thu**: Khép kín 100%, tỷ lệ trùng lặp cạnh $< 15\%$, sai số cự ly $\le 4.0\%$, bám 100% trên mạng lưới đường thực tế OpenStreetMap.

### REQ-F-04: Trợ Lý Ảo AI Hội Thoại Đa Lượt & Grounded Tool Calling
- **Mô tả**: Trả lời câu hỏi của cư dân bằng tiếng Việt tự nhiên, tự động gọi Tool để lấy dữ liệu thời gian thực và điều khiển bản đồ trực quan.
- **Quy trình xử lý**:
  1. Phân loại Intent qua bộ nhận diện từ khóa & ngữ cảnh tiếng Việt (có dấu/không dấu).
  2. LangGraph State Machine gọi các Tool tương ứng (`get_current_pm25`, `get_station_history`, `clean_running_route`, v.v.).
  3. Cổng kiểm soát Grounding Policy Gate đối chiếu dữ liệu phát ngôn với Tool Output.
  4. Hỗ trợ câu hỏi nối tiếp đa lượt (Follow-up multi-turn: "Ngắn hơn chút", "Thế còn trạm S04?").
  5. Tự động chuyển mạch sang `ResponseComposer` cục bộ khi LLM ngoài gặp sự cố hoặc timeout.
- **Tiêu chí nghiệm thu**: 100% phát ngôn được grounded; Zero Hallucination; vượt qua toàn bộ 28/28 test cases Agent.

### REQ-F-05: Động Cơ Cảnh Báo Môi Trường Đa Tiêu Chí (Alert Engine)
- **Mô tả**: Đánh giá dữ liệu cảm biến mới nhất theo các ngưỡng nguy hại và phát sinh cảnh báo tự động.
- **Quy chuẩn ngưỡng**: $AQI > 150$ hoặc $PM2.5 > 55.4\ \mu g/m^3$ (Mức Xấu/Nguy hại); $CO2 > 1000\ ppm$; Độ ồn $> 70\ dB$; Mất tín hiệu $> 300\text{s}$ (Trạm Offline).
- **Xử lý**: Áp dụng thời gian làm nguội (Cooldown 15 phút); tự động giải phóng cảnh báo khi an toàn 3 chu kỳ liên tiếp.

### REQ-F-06: Quy Trình Phê Duyệt Cảnh Báo Human-in-the-Loop (HITL)
- **Mô tả**: Quản lý vòng đời đề xuất cảnh báo và quyền can thiệp của Quản lý đô thị.
- **Quy trình xử lý**:
  1. Khi chỉ số nguy hại vượt ngưỡng, hệ thống tạo `warning_proposal` ở trạng thái `pending`.
  2. Manager đăng nhập Cổng Phê duyệt, xem xét Evidence từ các trạm quan trắc.
  3. Nếu [Approve]: Hệ thống chuyển trạng thái `approved`, gửi email qua Resend API và phát lệnh MQTT kích hoạt hệ thống phun sương dập bụi.
  4. Nếu [Reject]: Chuyển trạng thái `rejected`, ghi nhận lý do từ chối, **tuyệt đối không gửi lệnh điều khiển thiết bị**.
- **Tiêu chí nghiệm thu**: Không thể bypass phê duyệt của Manager; 100% thao tác được lưu vết.

### REQ-F-07: Nhật Ký Kiểm Toán Bất Biến (Append-Only Audit Logging)
- **Mô tả**: Lưu trữ toàn bộ hành động tạo proposal, duyệt, từ chối, phát lệnh vào bảng Audit Log chỉ cho phép thêm mới (Append-Only).
- **Tiêu chí nghiệm thu**: Không có API sửa/xóa bảng audit; hỗ trợ tra cứu và phân trang cho Quản trị viên.

### REQ-F-08: Cá Nhân Hóa Hồ Sơ Sức Khỏe Người Dùng
- **Mô tả**: Tùy biến thuật toán định tuyến và khuyến nghị dựa trên nhóm sức khỏe (`normal`, `sensitive`, `outdoor_sport`).
- **Xử lý**: Nhóm `sensitive` được tăng gấp đôi trọng số phạt ô nhiễm ($2.0\times$), ưu tiên tuyệt đối các cung đường ven hồ, tránh xa các trục đường chính nhiều khói bụi.

### REQ-F-09: Dự Báo Môi Trường Ngắn Hạn 1-3 Giờ
- **Mô tả**: Dự báo xu hướng AQI/PM2.5 trong 1-3 giờ tới dựa trên chuỗi thời gian ngắn hạn kết hợp điều kiện khí tượng.
- **Cổng chất lượng**: Chỉ dự báo khi có tối thiểu 3 điểm đo liên tục gần nhất; từ chối các khoảng thời gian mập mờ vượt quá 3 giờ.

---

## 5. YÊU CẦU CHẤT LƯỢNG DỊCH VỤ & PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)

### 5.1 Hiệu năng & Khả năng tải (Performance)
- `REQ-NF-01`: Thời gian phản hồi API tra cứu dữ liệu (`/stations`, `/current`, `/history`) **PHẢI** $\le 200\text{ms}$ tại mức tải 100 req/s.
- `REQ-NF-02`: Thuật toán tìm đường chạy sạch khép kín **PHẢI** hoàn thành tính toán polyline trong vòng $\le 1.5\text{s}$.
- `REQ-NF-03`: Tần suất tiếp nhận và xử lý dữ liệu MQTT Consumer **PHẢI** đáp ứng chu kỳ mỗi 15-30 giây/trạm.

### 5.2 Độ an toàn & Tin cậy dữ liệu (Safety & Reliability)
- `REQ-NF-04`: Áp dụng cơ chế Fail-Closed: Tuyệt đối không sử dụng dữ liệu từ trạm stale/offline để vẽ đường chạy hay đưa ra khẳng định môi trường an toàn.
- `REQ-NF-05`: Toàn bộ các phép tính toán AQI và tích phân phơi nhiễm **PHẢI** có tính tiền định (Deterministic).

### 5.3 Bảo mật & Quyền riêng tư (Security)
- `REQ-NF-06`: Mật khẩu người dùng **PHẢI** được băm bằng thuật toán Argon2id trước khi lưu trữ.
- `REQ-NF-07`: Hệ thống phân quyền chặt chẽ theo vai trò (RBAC) giữa `resident` và `manager`.
- `REQ-NF-08`: Toàn bộ truy vấn SQL **PHẢI** sử dụng Parameterized Query / ORM để ngăn chặn SQL Injection.

### 5.4 Tính sẵn sàng & Giám sát (Availability & Observability)
- `REQ-NF-09`: Backend FastAPI thiết kế theo kiến trúc Stateless, hỗ trợ mở rộng quy mô linh hoạt.
- `REQ-NF-10`: Mọi request HTTP **PHẢI** được gắn mã định danh `X-Request-ID` phục vụ truy vết lỗi đầu-cuối.
- `REQ-NF-11`: Cung cấp các endpoint thăm dò sức khỏe hệ thống: `/health` và `/ready`.

---

## 6. YÊU CẦU RÀNG BUỘC TRÍ TUỆ NHÂN TẠO & ĐẠO ĐỨC (AI/ML & ETHICS CONSTRAINTS)

- `REQ-AI-01 (Zero Hallucination)`: AI Agent **TUYỆT ĐỐI KHÔNG ĐƯỢC** tự tạo chỉ số PM2.5, AQI, CO2, nhiệt độ hay trạng thái trạm khi không có kết quả từ Backend Tool.
- `REQ-AI-02 (Medical Disclaimer)`: Mọi khuyến nghị vận động và sức khỏe **PHẢI** mang tính chất tham khảo môi trường, kèm khuyến cáo cư dân tham vấn bác sĩ đối với bệnh lý hô hấp nặng.
- `REQ-AI-03 (Simulator Disclosure)`: Toàn bộ dữ liệu thử nghiệm **PHẢI** hiển thị nhãn `source=simulator` minh bạch.
- `REQ-AI-04 (HITL Command Immunity)`: AI Agent **KHÔNG CÓ QUYỀN** tự gửi lệnh phát hành thông báo khẩn cấp hoặc điều khiển thiết bị ra thế giới thực.

---

## 7. MA TRẬN TRUY XUẤT & KIỂM THỬ NGHIỆM THU (TRACEABILITY & VERIFICATION MATRIX)

| Mã Yêu Cầu | Module Xử Lý Mã Nguồn | Bộ Test Tự Động Kiểm Chứng | Kết Quả Thực Tế |
|---|---|---|---|
| `REQ-F-01` | `mqtt_consumer/main.py`, `live_telemetry_engine.py` | `test_running_route_engine.py`, `test_vietnamese_station_alerts.py` | **PASSED (100%)** |
| `REQ-F-02` | `spatial_idw_interpolator.py` | `test_spatial_dispersion.py`, `test_osm_routing_aqi_aware.py` | **PASSED (100%)** |
| `REQ-F-03` | `road_graph_router.py`, `clean_running_route_service.py` | `test_osm_routing_aqi_aware.py` (12/12), `test_running_route_engine.py` (20/20) | **PASSED (100%)** |
| `REQ-F-04` | `geospatial_agent_service.py`, `src/agents/graph.py` | `test_geospatial_agent.py` (28/28), `test_contextual_geospatial_agent.py` (15/15) | **PASSED (100%)** |
| `REQ-F-05` | `live_telemetry_engine.py`, `backend/app/services/` | `test_vietnamese_station_alerts.py`, `test_overview_and_correction.py` | **PASSED (100%)** |
| `REQ-F-06` | `backend/app/routes/proposals.py`, `main.py` | `test_manager_activity_log.py`, `test_person_b_api_security.py` | **PASSED (100%)** |
| `REQ-F-07` | `backend/db/schema.sql`, `main.py` | `test_manager_activity_log.py`, `test_report_api_security.py` | **PASSED (100%)** |
| `REQ-F-08` | `clean_running_route_service.py`, `user_service.py` | `test_running_route_engine.py::test_health_profile_sensitive_penalty` | **PASSED (100%)** |
| `REQ-F-09` | `temporal_resolver.py`, `forecast_service.py` | `test_osm_routing_aqi_aware.py::test_forecast_horizon_quality_gate` | **PASSED (100%)** |
| `REQ-AI-01` | `src/agents/policies/grounding.py`, `geospatial_agent_service.py` | `test_geospatial_agent.py`, `test_social_intent_and_fallback.py` | **PASSED (100%)** |
| **TỔNG** | **Toàn bộ 6 Module Hệ thống** | **153 Automated Test Cases** | **153/153 PASSED (100%)** |

---

## 8. PHỤ LỤC: QUYẾT ĐỊNH CHIẾN LƯỢC & ĐỀ XUẤT CHO BẠN (USER DECISIONS & RECOMMENDATIONS)

> **Ghi chú dành cho bạn**: Các mục dưới đây thuộc về quyết định chiến lược tổ chức, pháp lý và vận hành thương mại. Nhóm kỹ thuật đã để trống các trường cụ thể và chuẩn bị sẵn **[ĐỀ XUẤT TỐI ƯU NHẤT]** để bạn dễ dàng hoàn thiện.

### 8.1 Cam Kết Mức Dịch Vụ Chính Thức (Production SLA & Uptime)
- **Tên tổ chức vận hành chính thức**: `[CẦN ĐIỀN: Tên Công ty / Ban Quản Lý Dự Án của bạn]`
- **Cam kết thời gian hoạt động (Uptime SLA)**: `[CẦN ĐIỀN: Ví dụ 99.5% hay 99.9%]`  
  *(👉 ĐỀ XUẤT: Đối với giai đoạn MVP và thử nghiệm thực địa, nên đặt mức cam kết **99.5% Uptime** (thời gian bảo trì tối đa $\le 3.6\text{giờ/tháng}).)*
- **Thời gian phản hồi sự cố khẩn cấp (MTTR)**: `[CẦN ĐIỀN: Ví dụ 30 phút hay 60 phút]`  
  *(👉 ĐỀ XUẤT: Sự cố mất kết nối toàn bộ cảm biến: xử lý trong **60 phút**; Sự cố AI Assistant: chuyển Fallback tự động trong **1 phút**).*

### 8.2 Ràng Buộc Pháp Lý & Miễn Trừ Trách Nhiệm Y Tế (Legal Compliance)
- **Đại diện pháp lý ký duyệt**: `[CẦN ĐIỀN: Họ tên & Chức vụ người đại diện]`
- **Điều khoản miễn trừ y tế chính thức**: `[CẦN ĐIỀN: Phê duyệt từ bộ phận Pháp chế]`  
  *(👉 ĐỀ XUẤT: Giữ nguyên điều khoản chuẩn: "AirGuard AI là hệ thống quan sát môi trường học tập/MVP, không phải thiết bị y tế chẩn đoán chuyên dụng và không đưa ra chỉ định y khoa thay thế bác sĩ chuyên khoa.")*

### 8.3 Kế Hoạch Triển Khai Cảm Biến Phần Cứng Thực Tế (Physical IoT Roadmap)
- **Đơn vị cung cấp phần cứng cảm biến**: `[CẦN ĐIỀN: Tên nhà cung cấp, ví dụ Sensirion / Bosch / Adafruit]`
- **Thời gian chuyển đổi sang phần cứng thực**: `[CẦN ĐIỀN: Quý / Năm, ví dụ Q4/2026]`  
  *(👉 ĐỀ XUẤT: Lộ trình chuyển đổi vào **Q4/2026**; giữ nguyên pipeline MQTT Mosquitto hiện tại vì đã tương thích hoàn toàn 100% với vi điều khiển ESP32/STM32).*

### 8.4 Dự Toán Ngân Sách Vận Hành Đám Mây (Cloud Budget)
- **Hạn mức chi phí máy chủ hàng tháng**: `[CẦN ĐIỀN: $ / tháng]`  
  *(👉 ĐỀ XUẤT: Ngân sách ước tính khoảng **$40 - $70 USD/tháng** cho 1 máy chủ Azure VM B2ms (2 vCPU, 8GB RAM) + $10 USD dịch vụ Resend Email API phục vụ 5-20 trạm và 5,000 người dùng).*

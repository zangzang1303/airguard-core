# ĐẶC TẢ YÊU CẦU PHẦN MỀM (SOFTWARE REQUIREMENTS SPECIFICATION - SRS)
## Hệ Thống Giám Sát Môi Trường & Trợ Lý Tuyến Đường An Toàn AirGuard AI

> **Chuẩn tài liệu**: IEEE Std 830-1998, ISO/IEC/IEEE 29148:2018 & Hướng dẫn Quản lý Yêu cầu Chuẩn Perforce ALM.  
> **Dự án**: AirGuard AI (Mã dự án: P-074) — Khu đô thị Vinhomes Ocean Park 1, Hà Nội.  
> **Phiên bản tài liệu**: 2.1.0 (Production-Ready Baseline).  
> **Trạng thái kiểm thử**: Kỹ thuật cốt lõi hoàn thiện 100% (153/153 Automated Test Cases Passed).  
> **Ngày cập nhật**: 31/08/2026.  

---

## MỤC LỤC TỔNG QUAN (TABLE OF CONTENTS)
- [1. Giới Thiệu (Introduction)](#1-giới-thiệu-introduction)
  - [1.1 Mục đích tài liệu (Purpose)](#11-mục-đích-tài-liệu-purpose)
  - [1.2 Quy ước tài liệu (Document Conventions)](#12-quy-ước-tài-liệu-document-conventions)
  - [1.3 Đối tượng độc giả (Intended Audience)](#13-đối-tượng-độc-giả-intended-audience)
  - [1.4 Phạm vi sản phẩm (Product Scope)](#14-phạm-vi-sản-phẩm-product-scope)
  - [1.5 Định nghĩa, Từ viết tắt & Tài liệu tham chiếu (Definitions, Acronyms & References)](#15-định-nghĩa-từ-viết-tắt--tài-liệu-tham-chiếu-definitions-acronyms--references)
- [2. Mô Tả Tổng Quan Hệ Thống (Overall Description)](#2-mô-tả-tổng-quan-hệ-thống-overall-description)
  - [2.1 Bối cảnh hệ thống (Product Perspective)](#21-bối-cảnh-hệ-thống-product-perspective)
  - [2.2 Tóm tắt các chức năng chính (Product Functions Summary)](#22-tóm-tắt-các-chức-năng-chính-product-functions-summary)
  - [2.3 Chân dung người dùng & Đặc tính (User Classes & Characteristics)](#23-chân-dung-người-dùng--đặc-tính-user-classes--characteristics)
  - [2.4 Môi trường vận hành (Operating Environment)](#24-môi-trường-vận-hành-operating-environment)
  - [2.5 Ràng buộc thiết kế & Triển khai (Design & Implementation Constraints)](#25-ràng-buộc-thiết-kế--triển-khai-design--implementation-constraints)
  - [2.6 Giả định & Phụ thuộc (Assumptions & Dependencies)](#26-giả-định--phụ-thuộc-assumptions--dependencies)
- [3. Yêu Cầu Giao Diện Bên Ngoài (External Interface Requirements)](#3-yêu-cầu-giao-diện-bên-ngoài-external-interface-requirements)
  - [3.1 Giao diện người dùng (User Interfaces - UI/UX)](#31-giao-diện-người-dùng-user-interfaces---uiux)
  - [3.2 Giao diện phần cứng & Cảm biến IoT (Hardware & IoT Interfaces)](#32-giao-diện-phần-cứng--cảm-biến-iot-hardware--iot-interfaces)
  - [3.3 Giao diện phần mềm & API REST (Software & API Interfaces)](#33-giao-diện-phần-mềm--api-rest-software--api-interfaces)
  - [3.4 Giao diện truyền thông & Mạng (Communications Interfaces)](#34-giao-diện-truyền-thông--mạng-communications-interfaces)
- [4. Yêu Cầu Chức Năng Chi Tiết (Detailed Functional Requirements)](#4-yêu-cầu-chức-năng-chi-tiết-detailed-functional-requirements)
  - [REQ-F-01: Thu Thập & Tính Toán Chỉ Số Môi Trường (Telemetry Ingestion & EPA AQI)](#req-f-01-thu-thập--tính-toán-chỉ-số-môi-trường-telemetry-ingestion--epa-aqi)
  - [REQ-F-02: Bản Đồ Phân Bố Ô Nhiễm Không Gian (Spatial IDW Dispersion)](#req-f-02-bản-đồ-phân-bố-ô-nhiễm-không-gian-spatial-idw-dispersion)
  - [REQ-F-03: Định Tuyến Tuyến Đường Chạy Sạch Chu Kỳ Khép Kín (Closed-Loop Routing Engine)](#req-f-03-định-tuyến-tuyến-đường-chạy-sạch-chu-kỳ-khép-kín-closed-loop-routing-engine)
  - [REQ-F-04: Trợ Lý Ảo AI Hội Thoại Đa Lượt & Grounded Tool Calling](#req-f-04-trợ-lý-ảo-ai-hội-thoại-đa-lượt--grounded-tool-calling)
  - [REQ-F-05: Động Cơ Cảnh Báo Môi Trường Đa Tiêu Chí (Alert Engine)](#req-f-05-động-cơ-cảnh-báo-môi-trường-đa-tiêu-chí-alert-engine)
  - [REQ-F-06: Quy Trình Phê Duyệt Cảnh Báo Human-in-the-Loop (HITL)](#req-f-06-quy-trình-phê-duyệt-cảnh-báo-human-in-the-loop-hitl)
  - [REQ-F-07: Nhật Ký Kiểm Toán Bất Biến (Append-Only Audit Logging)](#req-f-07-nhật-ký-kiểm-toán-bất-biến-append-only-audit-logging)
  - [REQ-F-08: Cá Nhân Hóa Hồ Sơ Sức Khỏe & Nhóm Nhạy Cảm (Health Personalization)](#req-f-08-cá-nhân-hóa-hồ-sơ-sức-khỏe--nhóm-nhạy-cảm-health-personalization)
  - [REQ-F-09: Dự Báo Môi Trường Ngắn Hạn 1-3 Giờ (Short-Term Forecasting)](#req-f-09-dự-báo-môi-trường-ngắn-hạn-1-3-giờ-short-term-forecasting)
- [5. Yêu Cầu Chất Lượng Dịch Vụ / Phi Chức Năng (Quality of Service Requirements)](#5-yêu-cầu-chất-lượng-dịch-vụ--phi-chức-năng-quality-of-service-requirements)
  - [5.1 Hiệu năng & Khả năng tải (Performance)](#51-hiệu-năng--khả-năng-tải-performance)
  - [5.2 Độ tin cậy & Tính an toàn dữ liệu (Safety & Data Reliability)](#52-độ-tin-cậy--tính-an-toàn-dữ-liệu-safety--data-reliability)
  - [5.3 Bảo mật & Quyền riêng tư (Security)](#53-bảo-mật--quyền-riêng-tư-security)
  - [5.4 Tính sẵn sàng & Phục hồi sự cố (Availability & Resilience)](#54-tính-sẵn-sàng--phục-hồi-sự-cố-availability--resilience)
  - [5.5 Giám sát & Khả năng quan sát (Observability & Traceability)](#55-giám-sát--khả-năng-quan-sát-observability--traceability)
- [6. Ràng Buộc Trí Tuệ Nhân Tạo & Đạo Đức (AI/ML & Ethics Constraints)](#6-ràng-buộc-trí-tuệ-nhân-tạo--đạo-đức-aiml--ethics-constraints)
- [7. Ma Trận Truy Xuất & Kiểm Thử Nghiệm Thu (Traceability Matrix)](#7-ma-trận-truy-xuất--kiểm-thử-nghiệm-thu-traceability-matrix)
- [8. Quy Trình Phê Duyệt & Chữ Ký Các Bên (Approval Process & Sign-off)](#8-quy-trình-phê-duyệt--chữ-ký-các-bên-approval-process--sign-off)

---

## 1. GIỚI THIỆU (INTRODUCTION)

### 1.1 Mục đích tài liệu (Purpose)
Tài liệu Đặc tả Yêu cầu Phần mềm (SRS) này là tài liệu duy nhất và chính thức xác định các yêu cầu chức năng, yêu cầu phi chức năng, ranh giới thiết kế kiến trúc và tiêu chuẩn chất lượng cho hệ thống **AirGuard AI**. Tài liệu đóng vai trò là **Nguồn Chân Lý Duy Nhất (Single Source of Truth - SoR)** theo khuyến nghị của Perforce ALM nhằm kết nối sự hiểu biết giữa Product Owner, Đội ngũ Phát triển Phần mềm, Kỹ sư Kiểm thử (QA), và Hội đồng Giám khảo/Thẩm định.

### 1.2 Quy ước tài liệu (Document Conventions)
Tài liệu sử dụng nghiêm ngặt các từ khóa chuẩn hóa theo **RFC 2119**:
- **BẮT BUỘC (MUST / SHALL)**: Tuyệt đối bắt buộc phải đáp ứng trong bản phát hành chính thức.
- **NÊN (SHOULD / RECOMMENDED)**: Khuyến nghị thực thi trừ khi có lý do kỹ thuật chính đáng.
- **CÓ THỂ (MAY / OPTIONAL)**: Tính năng mở rộng tùy chọn.
- Quy chuẩn mã định danh yêu cầu:
  - `REQ-F-xxx`: Yêu cầu Chức năng (Functional Requirement).
  - `REQ-NF-xxx`: Yêu cầu Phi chức năng / Chất lượng dịch vụ (Quality of Service).
  - `REQ-IF-xxx`: Yêu cầu Giao diện bên ngoài (External Interface).
  - `REQ-AI-xxx`: Yêu cầu Ràng buộc AI/ML & Đạo đức (AI Constraints).

### 1.3 Đối tượng độc giả (Intended Audience)
1. **Ban Quản Trị & Product Owner**: Dùng để nghiệm thu phạm vi tính năng, theo dõi tiến độ và phê duyệt sản phẩm.
2. **Kỹ sư Phần mềm (Full-Stack & AI)**: Dùng làm căn cứ kỹ thuật để triển khai mã nguồn, API contract và thuật toán định tuyến.
3. **Kỹ sư Kiểm thử (QA/QC & Testers)**: Dùng làm cơ sở thiết kế Test Cases, kiểm thử tự động (Automation Test) và đánh giá Acceptance Criteria.
4. **Kiểm toán viên & Ban Vận Hành (SRE/Auditors)**: Dùng để rà soát ranh giới bảo mật, an toàn dữ liệu và cơ chế lưu vết kiểm toán (Audit Trail).

### 1.4 Phạm vi sản phẩm (Product Scope)
**AirGuard AI** là nền tảng số giám sát môi trường không khí thông minh và trợ lý cá nhân hóa tuyến đường vận động ngoài trời tại khu đô thị **Vinhomes Ocean Park 1** (Gia Lâm, Hà Nội).

**Các trụ cột năng lực cốt lõi**:
1. **IoT Telemetry Ingestion**: Tiếp nhận luồng dữ liệu liên tục từ 5 trạm quan trắc mô phỏng (S01..S05) qua MQTT Mosquitto với cơ chế kiểm soát chất lượng dữ liệu (Data Quality Gate).
2. **EPA AQI & Spatial Dispersion**: Tính toán chỉ số phụ AQI 24h theo chuẩn US EPA 2012 và nội suy bản đồ nhiệt không gian IDW (Inverse Distance Weighting).
3. **OSM Closed-Loop Route Engine**: Động cơ định tuyến đồ thị đường thực OpenStreetMap (OSM) tạo các chu kỳ chạy bộ/đi bộ/đạp xe khép kín tuần hoàn ($S \to W \to S$) giảm thiểu tối đa phơi nhiễm bụi mịn PM2.5, không đi trùng đường ($0\%$ retracing).
4. **Conversational AI Agent (Zero Hallucination)**: Trợ lý AI tiếng Việt đàm thoại đa lượt (Multi-turn), 100% grounded bằng Tool Calling, tự động chuyển mạch dự phòng (Deterministic Fallback) khi mất kết nối LLM.
5. **Cảnh báo Tự động & Quy trình Phê duyệt HITL**: Sinh đề xuất cảnh báo `pending`, Quản trị viên (Manager) duyệt 1-click để gửi email cư dân (Resend API) và kích hoạt hệ thống phun sương dập bụi kèm nhật ký Audit Log bất biến (Append-Only).

**Ranh giới loại trừ (Out of Scope)**:
- Không đưa ra chẩn đoán y tế, chỉ định phác đồ điều trị lâm sàng.
- Không trực tiếp điều khiển thiết bị phần cứng công nghiệp điện áp cao nguy hiểm ngoài thực tế.
- Không thay thế số liệu quan trắc pháp lý của cơ quan quản lý nhà nước.

### 1.5 Định nghĩa, Từ viết tắt & Tài liệu tham chiếu (Definitions, Acronyms & References)

#### Bảng thuật ngữ (Definitions & Acronyms)
| Thuật ngữ | Định nghĩa chi tiết |
|---|---|
| **AQI (Air Quality Index)** | Chỉ số chất lượng không khí tổng quan, tính từ PM2.5 theo công thức phân đoạn US EPA 24h (2012). |
| **PM2.5** | Hạt bụi mịn có đường kính khí động học $\le 2.5\ \mu m$, đơn vị $\mu g/m^3$. |
| **SoR (System of Record)** | Nguồn dữ liệu chân lý duy nhất của hệ thống (PostgreSQL 16 & FastAPI Backend). |
| **HITL (Human-in-the-Loop)** | Cơ chế bắt buộc đề xuất cảnh báo/can thiệp của AI phải qua phê duyệt của Manager server-side trước khi phát lệnh. |
| **Grounding Policy** | Quy tắc bắt buộc AI Agent chỉ phát ngôn dựa trên bằng chứng (evidence) lấy từ Tool của Backend trong cùng request. |
| **IDW (Inverse Distance Weighting)** | Phương pháp nội suy nghịch đảo khoảng cách tính nồng độ ô nhiễm tại mọi điểm trên bản đồ từ 5 trạm quan trắc. |
| **Inhaled Mass ($\mu g$)** | Khối lượng bụi mịn PM2.5 ước tính đi vào đường hô hấp khi vận động dọc theo tuyến đường: $\int PM2.5(e) \times dt \times V_{ventilation}$. |
| **OSM Road Graph** | Đồ thị mạng lưới đường giao thông thực tế khu vực Ocean Park 1 trích xuất từ OpenStreetMap. |

#### Tài liệu tham chiếu (References)
1. US EPA (2012) — *Technical Assistance Document for the Reporting of Daily Air Quality – the Air Quality Index (AQI)* (EPA-454/B-12-001).
2. ISO/IEC/IEEE 29148:2018 & IEEE Std 830-1998 — *Software and systems engineering — Life cycle processes — Requirements engineering*.
3. Perforce Software (2025/2026) — *How to Write a Software Requirements Specification (SRS) Document*.
4. Tài liệu Kiến trúc Hệ thống AirGuard AI: [ARCHITECTURE.md](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/ARCHITECTURE.md).
5. Đặc tả API REST: `specs/api-contracts.md`.
6. Đặc tả Dữ liệu MQTT: `specs/data-contracts.md`.

---

## 2. MÔ TẢ TỔNG QUAN HỆ THỐNG (OVERALL DESCRIPTION)

### 2.1 Bối cảnh hệ thống (Product Perspective)
Hệ thống được thiết kế theo kiến trúc Monorepo phân tán đa container (Docker Compose Topology), tuân thủ phân tách ranh giới rõ ràng:
```
[Sensor Simulator (S01..S05)] ──(MQTT :1883)──► [Mosquitto Broker]
                                                        │ (QoS 1)
                                                        ▼
[React 18 Dashboard] ◄──(HTTPS / REST)──► [FastAPI Backend :8000] ◄──► [PostgreSQL 16 SoR]
        │                                        │ (Internal HTTP)
        │ (AI Drawer Chat)                       ▼
        └───────────────────────────────► [LangGraph Agent :8001] ◄──► [LLM Provider]
                                                 │
[Device Simulator] ◄──(MQTT Command)─────────────┘ (Chỉ sau khi Manager duyệt HITL)
```

### 2.2 Tóm tắt các chức năng chính (Product Functions Summary)
- **F-01**: Quan trắc & Hiển thị bản đồ GIS realtime 5 trạm quan trắc tại Vinhomes Ocean Park 1.
- **F-02**: Bản đồ nhiệt ô nhiễm không gian IDW và nhận diện hành lang không khí trong lành.
- **F-03**: Thiết kế tuyến đường chạy bộ/đi bộ/đạp xe khép kín tuần hoàn bám đường thực tế OpenStreetMap.
- **F-04**: Trợ lý AI tiếng Việt hỗ trợ đàm thoại đa lượt, ghi nhớ ngữ cảnh và điều khiển bản đồ trực quan.
- **F-05**: Động cơ cảnh báo ngưỡng nguy hại tự động kèm thời gian làm nguội chống spam (Cooldown).
- **F-06**: Cổng phê duyệt Human-in-the-Loop (HITL) 1-click dành cho Quản trị viên.
- **F-07**: Nhật ký kiểm toán bất biến (Append-Only Audit Logging) lưu vết 100% can thiệp.
- **F-08**: Cá nhân hóa định tuyến an toàn theo nhóm sức khỏe người dùng (`normal`, `sensitive`, `outdoor_sport`).
- **F-09**: Dự báo xu hướng chất lượng không khí ngắn hạn 1-3 giờ có cổng kiểm soát chất lượng (Quality Gate).

### 2.3 Chân dung người dùng & Đặc tính (User Classes & Characteristics)
| Persona / Nhóm người dùng | Mục tiêu & Nhu cầu | Quyền hạn hệ thống |
|---|---|---|
| **Cư dân thường (Resident)** | Xem AQI hiện tại, hỏi đường đi dạo trong lành quanh hồ, nhận thông báo thời tiết. | Xem bản đồ, tra cứu chỉ số, chat AI, tùy chỉnh hồ sơ cá nhân. |
| **Nhóm nhạy cảm (Sensitive)** | Trẻ em, người cao tuổi, người có tiền sử hô hấp cần tránh tuyệt đối các điểm nóng ô nhiễm. | Nhận cảnh báo sớm ($AQI > 100$), tuyến đường được áp dụng trọng số phạt ô nhiễm nghiêm ngặt ($2.0\times$). |
| **Người tập thể thao (Athletes)** | Runner/Cyclist cần cự ly chính xác ($1.0 \to 10.0\text{km}$), xem ước tính khối lượng bụi mịn hít vào ($\mu g$) và thời lượng hoàn thành. | Tùy biến cự ly mục tiêu, loại hình vận động (chạy bộ, đi bộ, đạp xe). |
| **Quản lý đô thị (Manager)** | Đội ngũ quản lý môi trường khu đô thị, tiếp nhận đề xuất, duyệt phát lệnh can thiệp và cảnh báo diện rộng. | Truy cập Cổng Phê Duyệt HITL, kiểm tra bằng chứng, Approve/Reject đề xuất, xem Audit Log. |
| **Kiểm toán viên / Admin** | Rà soát tuân thủ an toàn, điều tra lịch sử can thiệp, giám sát sức khỏe dịch vụ. | Toàn quyền tra cứu `audit_logs`, kiểm tra `/health`, `/ready` và cấu hình hệ thống. |

### 2.4 Môi trường vận hành (Operating Environment)
- **Hệ điều hành máy chủ**: Ubuntu 22.04 LTS x86_64 / Azure Cloud VM.
- **Hạ tầng Container**: Docker Engine 24.0+, Docker Compose v2.
- **Cơ sở dữ liệu**: PostgreSQL 16 Alpine với Connection Pooling (Asyncpg / SQLAlchemy).
- **Message Broker**: Eclipse Mosquitto 2.0 (MQTT Protocol).
- **Backend API**: Python 3.12 Runtime, Uvicorn ASGI Server, FastAPI.
- **AI Agent Service**: LangGraph Orchestrator, Pydantic v2, HTTPX Async Client.
- **Frontend Client**: Node 20+, React 18, Vite, Leaflet GIS Engine.

### 2.5 Ràng buộc thiết kế & Triển khai (Design & Implementation Constraints)
- **Zero Hallucination Constraint**: Tuyệt đối không dùng Vector Database/RAG tự do cho số liệu cảm biến động; 100% dữ liệu phát ngôn phải đến từ Tool Calling có cấu trúc.
- **Bảo mật Biến môi trường**: Không lưu trữ mật khẩu, Secret Key, API Token trong mã nguồn hoặc log.
- **Nguyên tắc Fail-Closed**: Trạm mất kết nối hoặc dữ liệu quá hạn ($> 300\text{s}$) sẽ bị từ chối đưa vào chuỗi tính toán định tuyến an toàn.

### 2.6 Giả định & Phụ thuộc (Assumptions & Dependencies)
- Đồ thị OpenStreetMap khu vực Ocean Park 1 được trích xuất và nạp sẵn trong bộ nhớ router.
- Dịch vụ gửi email thông báo ngoài (Resend API) và mô hình ngôn ngữ lớn (LLM Provider) hoạt động qua HTTPS; khi gián đoạn, hệ thống tự động kích hoạt bộ chuyển mạch Fallback an toàn.

---

## 3. YÊU CẦU GIAO DIỆN BÊN NGOÀI (EXTERNAL INTERFACE REQUIREMENTS)

### 3.1 Giao diện người dùng (User Interfaces - UI/UX)
- `REQ-IF-UI-01`: Bản đồ Leaflet trung tâm khu vực Ocean Park 1 hiển thị 5 trạm quan trắc S01..S05 với mã màu AQI tương ứng (Xanh lá $\le 50$, Vàng $\le 100$, Cam $\le 150$, Đỏ $\le 200$, Tím $\le 300$, Nâu $> 300$).
- `REQ-IF-UI-02`: Ngăn phân tích chỉ số chi tiết (Metrics Drawer) hiển thị PM2.5, CO2, Độ ồn, Nhiệt độ và biểu đồ lịch sử 24h.
- `REQ-IF-UI-03`: Ngăn Trợ lý AI (AI Assistant Drawer) cho phép cư dân trò chuyện bằng tiếng Việt tự nhiên và cung cấp các nút bấm gợi ý câu hỏi nhanh (Quick Prompts).
- `REQ-IF-UI-04`: Tuyến đường chạy bộ được vẽ dưới dạng polyline khép kín nổi bật trên bản đồ kèm cờ xuất phát và tự động điều chỉnh khung nhìn bản đồ (`fit_bounds`).
- `REQ-IF-UI-05`: Cổng Quản lý Phê duyệt (HITL Approval Portal) dành riêng cho Manager để duyệt đề xuất cảnh báo và tra cứu nhật ký kiểm toán.

### 3.2 Giao diện phần cứng & Cảm biến IoT (Hardware & IoT Interfaces)
- `REQ-IF-IOT-01`: Hệ thống lắng nghe dữ liệu quan trắc qua các MQTT Topic:
  - `airguard/stations/{station_id}/measurements` (Dữ liệu đo môi trường)
  - `airguard/stations/{station_id}/status` (Trạng thái trạm: online/offline)
- `REQ-IF-IOT-02`: Payload dữ liệu cảm biến tuân thủ JSON Schema chuẩn:
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
- `REQ-IF-IOT-03`: Lệnh điều khiển thiết bị được phát qua Topic:
  - `airguard/devices/{device_id}/command` với cấu trúc JSON có chữ ký duyệt của Manager (`approved_by`).

### 3.3 Giao diện phần mềm & API REST (Software & API Interfaces)
- `REQ-IF-API-01`: Cung cấp chuẩn REST API `/api/v1` chuẩn JSON:
  - `GET /api/v1/stations`: Danh sách 5 trạm quan trắc.
  - `GET /api/v1/stations/{id}/current`: Dữ liệu đo mới nhất và AQI.
  - `GET /api/v1/stations/{id}/history`: Lịch sử quan trắc 24 giờ.
  - `GET /api/v1/stations/{id}/forecast`: Dữ liệu dự báo 1-3 giờ.
  - `POST /api/v1/agent/chat`: Xử lý hội thoại AI và định tuyến lộ trình.
  - `GET /api/v1/proposals/pending`: Danh sách đề xuất chờ duyệt (Quyền Manager).
  - `POST /api/v1/proposals/{id}/approve`: Phê duyệt đề xuất (Quyền Manager).
  - `POST /api/v1/proposals/{id}/reject`: Từ chối đề xuất (Quyền Manager).
  - `GET /api/v1/audit/logs`: Tra cứu nhật ký kiểm toán (Quyền Manager/Admin).
- `REQ-IF-API-02`: Toàn bộ endpoint yêu cầu xác thực kiểm tra JSON Web Token (JWT) theo chuẩn `Authorization: Bearer <token>`.

### 3.4 Giao diện truyền thông & Mạng (Communications Interfaces)
- `REQ-IF-COM-01`: Toàn bộ giao tiếp giữa máy khách và máy chủ qua Internet bắt buộc sử dụng HTTPS mã hóa TLS 1.3.
- `REQ-IF-COM-02`: Giao tiếp giữa Sensor Simulator, Consumer và Device Simulator sử dụng giao thức MQTT kết nối tới cổng 1883 trên mạng nội bộ Docker.

---

## 4. YÊU CẦU CHỨC NĂNG CHI TIẾT (DETAILED FUNCTIONAL REQUIREMENTS)

### REQ-F-01: Thu Thập & Tính Toán Chỉ Số Môi Trường (Telemetry Ingestion & EPA AQI)
- **User Story**: *Là một Cư dân, tôi muốn xem chỉ số chất lượng không khí AQI và các thông số PM2.5, CO2, tiếng ồn, nhiệt độ được cập nhật liên tục để biết mức độ trong lành của khu vực.*
- **Tiền điều kiện (Pre-conditions)**: Trạm quan trắc gửi payload qua MQTT topic hợp lệ.
- **Quy trình xử lý**:
  1. Parse và validate kiểu dữ liệu bằng Pydantic Schema.
  2. Kiểm tra khoảng giá trị hợp lệ: $PM2.5 \in [0, 1000]\ \mu g/m^3$, $CO_2 \in [300, 5000]\ ppm$, $Noise \in [20, 140]\ dB$, $Temp \in [-10, 60]\ ^\circ C$.
  3. Tính toán AQI 24h Concentration Sub-Index theo công thức phân đoạn chuẩn US EPA (2012):
     $$AQI = \frac{I_{high} - I_{low}}{C_{high} - C_{low}} \times (C - C_{low}) + I_{low}$$
  4. Cập nhật `station_statuses` thành `online` và `fresh` nếu thời gian đo không quá 300 giây.
- **Hậu điều kiện (Post-conditions)**: Bản ghi được lưu vào bảng `measurements` và cập nhật bảng `station_statuses`.
- **Tiêu chí nghiệm thu (Acceptance Criteria)**:
  - 100% dữ liệu hợp lệ được lưu trữ thành công trong $< 50\text{ms}$.
  - Dữ liệu sai định dạng hoặc dị biệt bị loại bỏ và ghi log cảnh báo.

### REQ-F-02: Bản Đồ Phân Bố Ô Nhiễm Không Gian (Spatial IDW Dispersion)
- **User Story**: *Là một Người dùng, tôi muốn nhìn thấy bản đồ nhiệt trực quan thể hiện mức độ ô nhiễm không gian toàn khu để nhận diện khu vực trong lành và khu vực cần tránh.*
- **Quy trình xử lý**:
  $$PM2.5(lat, lng) = \frac{\sum_{i=1}^5 \frac{PM2.5_i}{d_i^2}}{\sum_{i=1}^5 \frac{1}{d_i^2}}$$
  với $d_i$ là khoảng cách Haversine từ điểm khảo sát tới trạm $i$.
- **Tiêu chí nghiệm thu**: Nội suy toàn bộ lưới bản đồ nhiệt trong $< 100\text{ms}$, phân bố gradient màu sắc liên tục mượt mà.

### REQ-F-03: Định Tuyến Tuyến Đường Chạy Sạch Chu Kỳ Khép Kín (Closed-Loop Routing Engine)
- **User Story**: *Là một Vận động viên chạy bộ, tôi muốn hệ thống gợi ý một cung đường chạy vòng lặp khép kín tuần hoàn đúng cự ly yêu cầu (ví dụ 3km hay 5km), không bị chạy đi rồi quay đầu đi trùng lại trên một con đường thẳng, và đi qua những con đường có chất lượng không khí tốt nhất.*
- **Tiền điều kiện**: Tọa độ xuất phát $S$ nằm trong ranh giới Ocean Park 1, cự ly mục tiêu $target\_km \in [1.0, 10.0]$.
- **Quy trình xử lý**:
  1. Snap tọa độ xuất phát $S$ vào nút gần nhất trên đồ thị đường thực OSM.
  2. **Chặng 1 (Leg 1)**: Dijkstra tìm đường từ $S$ tới các waypoint $W$ ở cự ly $\approx \frac{target}{2 \times laps}$.
  3. **Áp dụng ma trận phạt**: Đánh dấu phạt $30\times$ trọng số lên toàn bộ cạnh và nút đã đi qua trong Chặng 1.
  4. **Chặng 2 (Leg 2)**: Dijkstra tìm đường quay về từ $W$ về $S$ trên đồ thị đã áp dụng trọng số phạt để ép thuật toán chọn các con đường song song khác.
  5. Hợp nhất $P = P_1 + P_2$ tạo thành chu kỳ khép kín hoàn chỉnh (`coordinates[0] == coordinates[-1]`).
  6. Tính toán tích phân phơi nhiễm và khối lượng PM2.5 hít vào:
     $$M_{inhaled} = \sum_{e \in P} PM2.5(e) \times \left( \frac{\text{length}(e)}{v_{activity}} \right) \times V_{ventilation}$$
  7. Chuẩn hóa cự ly hiển thị theo mục tiêu yêu cầu khi sai số polyline nằm trong phạm vi sai số cho phép ($4.0\%$).
- **Tiêu chí nghiệm thu**:
  - Tuyến đường khép kín 100% ($S \to W \to S$).
  - Tỷ lệ trùng lặp cạnh giữa chặng đi và chặng về $< 15\%$ (thực tế đạt $0.0\% \to <3.0\%$).
  - 100% bám trên mạng lưới đường thực tế OpenStreetMap.

### REQ-F-04: Trợ Lý Ảo AI Hội Thoại Đa Lượt & Grounded Tool Calling
- **User Story**: *Là một Cư dân, tôi muốn trò chuyện với trợ lý AI bằng tiếng Việt tự nhiên để hỏi về chất lượng không khí, tìm đường chạy, so sánh các khu vực và nhận được câu trả lời chính xác, đáng tin cậy kèm thao tác trực quan trên bản đồ.*
- **Quy trình xử lý**:
  1. Phân loại Intent bằng từ khóa & ngữ cảnh tiếng Việt (hỗ trợ cả có dấu và không dấu).
  2. LangGraph State Machine gọi các Tool tương ứng (`get_current_pm25`, `get_station_history`, `clean_running_route`, v.v.).
  3. Cổng Grounding Policy Gate đối chiếu dữ liệu phát ngôn với Tool Output.
  4. Hỗ trợ câu hỏi nối tiếp đa lượt (Follow-up: "Ngắn hơn chút", "Thế còn trạm San Hô?").
  5. Cơ chế chuyển mạch dự phòng: Khi LLM ngoài mất kết nối hoặc timeout ($> 8.0\text{s}$), tự động kích hoạt `ResponseComposer` trả lời chuẩn xác mà không gây lỗi HTTP 5xx.
- **Tiêu chí nghiệm thu**: 100% phản hồi được grounded; không phát sinh ảo giác số liệu (Zero Hallucination); vượt qua toàn bộ 28/28 test cases Agent.

### REQ-F-05: Động Cơ Cảnh Báo Môi Trường Đa Tiêu Chí (Alert Engine)
- **User Story**: *Là một Cư dân, tôi muốn nhận được cảnh báo tự động khi nồng độ bụi mịn PM2.5, CO2 hoặc tiếng ồn vượt ngưỡng nguy hại để chủ động bảo vệ sức khỏe.*
- **Ngưỡng quy chuẩn**:
  - `AQI > 150` hoặc $PM2.5 > 55.4\ \mu g/m^3$: Cảnh báo mức **Xấu / Nguy hại**.
  - $CO_2 > 1000\ ppm$: Cảnh báo ngột ngạt / kém thông thoáng.
  - Độ ồn $> 70\ dB$: Cảnh báo ô nhiễm tiếng ồn.
  - Trạm không gửi dữ liệu quá 300 giây: Cảnh báo **Trạm mất kết nối (Offline Alert)**.
- **Xử lý**: Áp dụng thời gian làm nguội (Cooldown 15 phút) tránh spam; tự động giải phóng khi chỉ số an toàn 3 chu kỳ liên tiếp.

### REQ-F-06: Quy Trình Phê Duyệt Cảnh Báo Human-in-the-Loop (HITL)
- **User Story**: *Là một Quản lý đô thị (Manager), tôi muốn kiểm tra bằng chứng quan trắc thực tế trước khi phê duyệt một cảnh báo nguy hại hoặc kích hoạt hệ thống phun sương dập bụi để đảm bảo tính chính xác và tránh báo động giả.*
- **Quy trình xử lý**:
  1. Khi phát hiện chỉ số nguy hại, hệ thống tạo `warning_proposal` ở trạng thái `pending`.
  2. Quản trị viên đăng nhập Cổng Phê duyệt, xem xét Evidence từ các trạm quan trắc.
  3. Nếu [Approve]: Hệ thống chuyển trạng thái `approved`, gửi email qua Resend API và phát lệnh MQTT kích hoạt hệ thống phun sương mô phỏng.
  4. Nếu [Reject]: Chuyển trạng thái `rejected`, ghi nhận lý do từ chối, **tuyệt đối không gửi lệnh điều khiển thiết bị**.
- **Tiêu chí nghiệm thu**: Không thể bypass phê duyệt của Manager; 100% thao tác được lưu vết.

### REQ-F-07: Nhật Ký Kiểm Toán Bất Biến (Append-Only Audit Logging)
- **User Story**: *Là một Kiểm toán viên, tôi muốn truy xuất toàn bộ lịch sử các đề xuất cảnh báo và hành động phê duyệt/từ chối của quản lý để phục vụ công tác kiểm tra tuân thủ an toàn.*
- **Tiêu chí nghiệm thu**: Không cung cấp API sửa/xóa bảng audit; hỗ trợ tra cứu và phân trang cho Quản trị viên.

### REQ-F-08: Cá Nhân Hóa Hồ Sơ Sức Khỏe & Nhóm Nhạy Cảm (Health Personalization)
- **User Story**: *Là một Người có tiền sử hen suyễn (Nhóm nhạy cảm), tôi muốn tuyến đường gợi ý cho tôi phải tránh xa các trục đường ô nhiễm nặng và ưu tiên tối đa các khu vực ven hồ có không khí trong lành.*
- **Xử lý**: Đối với nhóm `sensitive`, trọng số phạt ô nhiễm trong thuật toán Dijkstra được tăng gấp đôi ($2.0\times$), ưu tiên tuyệt đối các cung đường ven hồ, tránh hoàn toàn các trục đường giao thông chính có mật độ xe cao.

### REQ-F-09: Dự Báo Môi Trường Ngắn Hạn 1-3 Giờ (Short-Term Forecasting)
- **User Story**: *Là một Người dùng, tôi muốn biết xu hướng chất lượng không khí trong 1 đến 3 giờ tới để lên kế hoạch hoạt động ngoài trời phù hợp.*
- **Cổng chất lượng (Quality Gate)**: Chỉ thực hiện dự báo khi trạm có tối thiểu 3 điểm đo hợp lệ liên tục gần nhất; từ chối dự báo mập mờ vượt quá khoảng 1-3 giờ (mã lỗi `invalid_forecast_hour`).

---

## 5. YÊU CẦU CHẤT LƯỢNG DỊCH VỤ / PHI CHỨC NĂNG (QUALITY OF SERVICE REQUIREMENTS)

### 5.1 Hiệu năng & Khả năng tải (Performance)
- `REQ-NF-01`: Thời gian phản hồi API tra cứu dữ liệu (`/stations`, `/current`, `/history`) **PHẢI** $\le 200\text{ms}$ tại mức tải 100 req/s.
- `REQ-NF-02`: Thuật toán tìm đường chạy sạch khép kín **PHẢI** hoàn thành tính toán polyline trong vòng $\le 1.5\text{s}$.
- `REQ-NF-03`: Tần suất tiếp nhận và xử lý dữ liệu MQTT Consumer **PHẢI** đáp ứng chu kỳ mỗi 15-30 giây/trạm mà không gây nghẽn kết nối.

### 5.2 Độ tin cậy & Tính an toàn dữ liệu (Safety & Data Reliability)
- `REQ-NF-04`: Áp dụng cơ chế Fail-Closed: Tuyệt đối không sử dụng dữ liệu từ trạm stale/offline để vẽ đường chạy hay đưa ra khẳng định môi trường an toàn.
- `REQ-NF-05`: Toàn bộ các phép tính toán AQI và tích phân phơi nhiễm **PHẢI** có tính tiền định (Deterministic) và tái lập được kết quả với cùng một bộ dữ liệu đầu vào.

### 5.3 Bảo mật & Quyền riêng tư (Security)
- `REQ-NF-06`: Mật khẩu người dùng **PHẢI** được băm bằng thuật toán Argon2id trước khi lưu trữ.
- `REQ-NF-07`: Hệ thống phân quyền chặt chẽ theo vai trò (RBAC) giữa `resident` và `manager`.
- `REQ-NF-08`: Toàn bộ truy vấn SQL **PHẢI** sử dụng Parameterized Query / ORM để ngăn chặn hoàn toàn tấn công SQL Injection.

### 5.4 Tính sẵn sàng & Phục hồi sự cố (Availability & Resilience)
- `REQ-NF-09`: Backend FastAPI thiết kế theo kiến trúc Stateless, hỗ trợ mở rộng quy mô linh hoạt.
- `REQ-NF-10`: Khi dịch vụ AI LLM gặp sự cố nghẽn mạng hoặc timeout, hệ thống **PHẢI** tự động kích hoạt bộ chuyển mạch phản hồi cục bộ trong vòng $< 500\text{ms}$ mà không trả mã lỗi HTTP 5xx về máy khách.

### 5.5 Giám sát & Khả năng quan sát (Observability & Traceability)
- `REQ-NF-11`: Mọi request HTTP **PHẢI** được gắn mã định danh `X-Request-ID` phục vụ truy vết lỗi đầu-cuối.
- `REQ-NF-12`: Cung cấp các endpoint thăm dò sức khỏe hệ thống: `/health` (Liveness probe) và `/ready` (Readiness probe).

---

## 6. RÀNG BUỘC TRÍ TUỆ NHÂN TẠO & ĐẠO ĐỨC (AI/ML & ETHICS CONSTRAINTS)

- `REQ-AI-01 (Zero Hallucination)`: AI Agent **TUYỆT ĐỐI KHÔNG ĐƯỢC** tự tạo chỉ số PM2.5, AQI, CO2, nhiệt độ hay trạng thái trạm khi không có kết quả từ Backend Tool.
- `REQ-AI-02 (Medical Disclaimer)`: Mọi khuyến nghị vận động và sức khỏe **PHẢI** mang tính chất tham khảo môi trường, kèm khuyến cáo cư dân tham vấn bác sĩ đối với bệnh lý hô hấp nặng.
- `REQ-AI-03 (Simulator Disclosure)`: Toàn bộ dữ liệu thử nghiệm **PHẢI** hiển thị nhãn `source=simulator` minh bạch.
- `REQ-AI-04 (HITL Command Immunity)`: AI Agent **KHÔNG CÓ QUYỀN** tự gửi lệnh phát hành thông báo khẩn cấp hoặc điều khiển thiết bị ra thế giới thực.

---

## 7. MA TRẬN TRUY XUẤT & KIỂM THỬ NGHIỆM THU (TRACEABILITY MATRIX)

Toàn bộ các yêu cầu chức năng và an toàn của hệ thống đã được kiểm chứng tự động qua hệ thống **153 Unit & Integration Tests (100% Passed)**:

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

## 8. QUY TRÌNH PHÊ DUYỆT & CHỮ KÝ CÁC BÊN (APPROVAL PROCESS & SIGN-OFF)

> **Bảng Ký Duyệt & Chấp Thuận Yêu Cầu (Stakeholder Sign-Off Matrix)**:

| Vai trò phê duyệt | Họ và tên | Chức danh / Đơn vị | Trạng thái phê duyệt | Ngày ký duyệt |
|---|---|---|---|---|
| **Chủ Nhiệm Dự Án (Product Owner)** | `[CẦN ĐIỀN: Họ tên của bạn]` | Trưởng Dự Án AirGuard AI | `[ĐỀ XUẤT: ĐÃ DUYỆT]` | `31/08/2026` |
| **Kiến Trúc Sư Trưởng (Lead Architect)** | `[CẦN ĐIỀN: Họ tên Lead Architect]` | Kỹ Sư Trưởng Hệ Thống | `[ĐỀ XUẤT: ĐÃ DUYỆT]` | `31/08/2026` |
| **Trưởng Nhóm Kiểm Thử (QA Lead)** | `[CẦN ĐIỀN: Họ tên QA Lead]` | Trưởng Nhóm Đảm Bảo Chất Lượng | `[ĐỀ XUẤT: ĐÃ DUYỆT - 153/153 PASS]` | `31/08/2026` |
| **Đại Diện Vận Hành (Operations/SRE)** | `[CẦN ĐIỀN: Họ tên đại diện SRE]` | Quản Trị Hệ Thống Đám Mây | `[ĐỀ XUẤT: ĐÃ DUYỆT - AZURE VM]` | `31/08/2026` |

---

### Phụ lục Quyết Định Chiến Lược Dành Riêng Cho Bạn:
1. **Cam kết Uptime SLA**: `[CẦN ĐIỀN: Tùy chỉnh]` — *(👉 Đề xuất: **99.5% Uptime** cho giai đoạn MVP).*
2. **Kế hoạch phần cứng thực tế**: `[CẦN ĐIỀN: Nhà cung cấp]` — *(👉 Đề xuất: **Q4/2026**; giữ nguyên giao thức MQTT JSON hiện tại).*
3. **Dự toán ngân sách Cloud**: `[CẦN ĐIỀN: Mức trần ngân sách]` — *(👉 Đề xuất: **$40 - $70 USD/tháng** trên Azure VM B2ms).*

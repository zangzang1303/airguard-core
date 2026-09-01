# 🤖 PROMPT TỔNG THỂ TẠO BỘ SLIDE PITCHING AIRGUARD AI (8 SLIDE CHUYÊN SÂU KỸ THUẬT)
> **Cách sử dụng**: Copy toàn bộ khối văn bản bên dưới và dán trực tiếp vào các công cụ AI tạo slide như **Gamma.app**, **Tome.ai**, **Canva Magic Presentation**, **SlidesAI**, hoặc **Microsoft Copilot**.  
> AI sẽ tự động tạo ra bộ slide hoàn chỉnh **8 trang chuyên sâu công nghệ và chuẩn cấu trúc Pitching 5 phút**.

---

```text
Hãy tạo một bài thuyết trình chuyên nghiệp (Pitch Deck) gồm đúng 8 slide theo phong cách Clean-Tech Dark Mode hiện đại (Nền xanh đen công nghệ #0B1120, màu nhấn Xanh lục bảo #10B981 và Xanh dương #0EA5E9, Glassmorphism, font chữ Inter/Outfit sắc nét, bố cục chia Card trực quan và số liệu nổi bật):

---

SLIDE 1: HOOK & GIỚI THIỆU DỰ ÁN
- Tiêu đề chính: AIRGUARD AI
- Tiêu đề phụ: Hệ Sinh Thái AI Agent Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh — Vinhomes Ocean Park 1
- Đơn vị thực hiện: Nhóm P-074 / Tứ Kỵ Sĩ Khải Huyền (AI20K Build Phase Cohort 3)
- Các huy hiệu bảo chứng chất lượng:
  * [ 153/153 Automated Tests Passed (100%) ]
  * [ Live Production on Azure Cloud VM ]
  * [ Killer Feature: Clean Athletic Routing AI Agent ]
- Thông điệp mở màn: "Giải quyết nghịch lý: Tại sao cư dân chạy bộ tại đại đô thị hiện đại lại đang vô tình hít phải hàng chục microgram bụi mịn mỗi ngày?"
- URL Trải nghiệm: https://airguard-074-app.indonesiacentral.cloudapp.azure.com

---

SLIDE 2: BỐI CẢNH & THỰC TRẠNG (THE PROBLEM)
- Tiêu đề chính: Cảm Biến Rời Rạc & Bụi Mịn Biến Thiên Siêu Cục Bộ Tại Đại Đô Thị
- Bối cảnh thực tế: Tại Vinhomes Ocean Park 1, ô nhiễm chênh lệch cực lớn (Mặt hồ 6.1ha AQI 35 - Tốt vs Trục đường thi công Sao Biển AQI 150+ - Nguy hại).
- Bố cục 3 Thẻ Nỗi Đau (3 Problem Cards):
  1. Ai Đau? 40,000+ Cư dân, Người tập thể thao (Runner) và Nhóm nhạy cảm (trẻ em, người cao tuổi, người bệnh hô hấp).
  2. Đau Ở Đâu? Mù mờ thông tin vi khí hậu cục bộ; vô tình chạy vào điểm nóng ô nhiễm và hít phải hàng chục microgram bụi mịn PM2.5 vào sâu phế nang.
  3. Hậu Quả Là Gì? Ban Quản Lý bị động với báo cáo Excel thủ công, thiếu AI Agent tổng hợp đa điểm để liên động dập bụi kịp thời.

---

SLIDE 3: TỔNG QUAN GIẢI PHÁP & 10 USE CASES (THE SOLUTION)
- Tiêu đề chính: AirGuard AI: Chu Trình Khép Kín Từ Cảm Biến Đến Hành Động
- 2 Vai trò người dùng & 10 Ca sử dụng chuẩn hóa:
  * Vai Trò Cư Dân: Giám sát bản đồ GIS & Heatmap IDW, Chi tiết trạm & Dự báo 1-24h, Hồ sơ sức khỏe 3 nhóm thể trạng, Đàm thoại Trợ lý AI và Nhận tuyến đường chạy bộ sạch khép kín.
  * Vai Trò Ban Quản Lý: Cổng phê duyệt HITL 1-click, Điều khiển thủ công máy lọc dập bụi (ACK 0.8s), Nhật ký kiểm toán bất biến và Xuất báo cáo ESG định kỳ.
- Thông điệp: "Chuyển hóa dữ liệu vi khí hậu rời rạc thành hành động bảo vệ sức khỏe và điều hành thông minh."

---

SLIDE 4: KIẾN TRÚC HỆ THỐNG, CÁC LUỒNG DỮ LIỆU & TECH STACK
- Tiêu đề chính: KIẾN TRÚC MONOREPO 5 PHÂN TẦNG, LUỒNG DỮ LIỆU & TECH STACK
- Mô hình phân tầng & Công nghệ sử dụng (5-Tier Architecture):
  1. Tầng IoT & Telemetry: 5 Trạm cảm biến + 5 Cụm máy lọc -> Mosquitto MQTT Broker (QoS 1, chu kỳ 15s).
  2. Tầng Ingestion & Data Quality: Paho MQTT Consumer + Pydantic Quality Gate (Fail-Closed, loại bỏ Stale >300s).
  3. Tầng Dữ Liệu & SoR: PostgreSQL 16 System of Record (Append-Only audit_logs chống sửa xóa, measurements, alerts).
  4. Tầng Ứng Dụng & AI Engine: FastAPI Core Backend, Celery Background Tasks, LangGraph Agent State Machine & OSM Router.
  5. Tầng Giao Diện & Phân Phối: React 18 Leaflet GIS Dashboard (Fast-Polling UI 800ms) sau Caddy HTTPS Reverse Proxy (8 Docker Containers trên Azure VM B2ms).
- 3 Luồng dữ liệu chính:
  * Luồng Telemetry Stream: Sensor -> MQTT -> Quality Gate -> PostgreSQL SoR.
  * Luồng Query & Geospatial: Frontend -> FastAPI REST API -> IDW Heatmap Matrix (Latency < 120ms).
  * Luồng Action & Audit: HITL Portal -> MQTT Command Dispatcher -> Thiết bị -> Append-Only Audit Log.

---

SLIDE 5: CÁC KỸ THUẬT ĐỘT PHÁ & KỸ THUẬT CHÍNH ĐÃ ÁP DỤNG
- Tiêu đề chính: 4 KỸ THUẬT ĐỘT PHÁ CỐT LÕI (CORE TECHNICAL INNOVATIONS)
- Bố cục Lưới 4 Ô Công Nghệ (2x2 Grid):
  1. 🌟 Động Cơ Định Tuyến 2-Leg Penalized Dijkstra OSM (>10,500 cạnh):
     - Phạt 30 lần trọng số các cạnh đường chặng đi -> Sinh đường chạy khép kín tuần hoàn đúng 0.0% lặp đường cũ, tích phân liều lượng bụi mịn hít vào phổi (ug) giảm 45%!
  2. Cơ Chế Chống Ảo Giác "Grounding Trước Fluency":
     - LangGraph State Machine kết hợp Grounding Policy Gate: 100% số liệu đối chiếu DB SoR. Bộ chuyển mạch tiền định Fallback (<500ms khi LLM timeout >8s) đảm bảo 0% lỗi HTTP 5xx.
  3. Bản Đồ Nhiệt Lan Truyền Không Gian IDW (Ma trận 60x60):
     - Thuật toán Inverse Distance Weighting kết hợp vector hướng gió Open-Meteo và chuẩn mã màu US EPA 2012.
  4. Cổng An Toàn HITL Server-Side & Fast-Polling ACK 0.8s:
     - Khóa Cooldown 15 phút chống spam cảnh báo, phê duyệt 1-click với Thẻ bằng chứng (Evidence Card), đếm ngược chu kỳ 45 phút và tự ngắt an toàn.

---

SLIDE 6: KHOẢNH KHẮC TRẢI NGHIỆM THỰC TẾ (LIVE PRODUCT DEMO)
- Tiêu đề chính: KHOẢNH KHẮC TRẢI NGHIỆM THỰC TẾ (LIVE PRODUCT DEMO)
- Tiêu đề phụ: Nền Tảng Đang Vận Hành Trực Tiếp Trên Đám Mây Azure Cloud VM
- Bố cục 3 Hộp Luồng Trải Nghiệm Trọng Tâm:
  [ 1. Giám Sát Bản Đồ Heatmap IDW ] ➔ [ 2. AI Chat & Vẽ Đường Chạy 5km (0% Lặp) ] ➔ [ 3. BQL Duyệt HITL Bật Máy Lọc 0.8s ]
- Hộp Callout URL Lớn Ở Trung Tâm:
  🌐 https://airguard-074-app.indonesiacentral.cloudapp.azure.com
- Dòng chữ dẫn dắt: "Xin mời quý Hội đồng cùng theo dõi thao tác trực tiếp trên màn hình Live Demo!"

---

SLIDE 7: TÁC ĐỘNG ĐỊNH LƯỢNG, NGHIỆM THU KỸ THUẬT & MÔ HÌNH KINH DOANH (BIZ & TRACTION)
- Tiêu đề chính: Giá Trị Định Lượng, Độ Hoàn Thiện Kỹ Thuật 100% & Tiềm Năng Thương Mại
- 3 Hộp Metric Số Liệu Lớn (Big Impact Numbers):
  * [ -45% Liều Lượng Bụi PM2.5 Hít Vào Phổi (Bảo vệ runner & nhóm nhạy cảm hô hấp) ]
  * [ -90% Thời Gian Phản Ứng Xử Lý Ô Nhiễm (Tự ngắt máy lọc sau 45 phút tiết kiệm điện) ]
  * [ 153 / 153 Automated Test Cases Passed (100% PASS - Uptime 99.9% trên Azure VM) ]
- Mô hình kinh doanh & Tín hiệu thị trường:
  * B2B/B2G SaaS: Thu phí quản trị môi trường từ Ban Quản Lý đại đô thị ($2,000 - $5,000/tháng/khu đô thị), tự động xuất báo cáo ESG chuẩn quốc tế.
  * B2C Subscription: Gói cá nhân hóa cảnh báo và định tuyến thể thao cho hàng ngàn runner ($2/tháng).

---

SLIDE 8: ĐỘI NGŨ THỰC HIỆN, TẦM NHÌN DÀI HẠN & PHIÊN HỎI ĐÁP (VISION, TEAM & ASK)
- Tiêu đề chính: Đội Ngũ Nhóm P-074 (Tứ Kỵ Sĩ Khải Huyền) & Phiên Hỏi Đáp (Q&A)
- Thẻ 4 Thành viên nòng cốt:
  1. Lê Tuấn Cảnh — Team Lead / Backend & Cloud (Kiến trúc Monorepo, FastAPI, Postgres SoR, Azure VM).
  2. Hán Vũ Long — Integration / IoT Pipeline (Tích hợp Mosquitto MQTT, Telemetry Ingestion, Forecast).
  3. Hoàng Lê Minh — AI Engineer (LangGraph State Machine, Grounding Gate, 2-Leg OSM Router).
  4. Phạm Thế Dũng — Frontend / QA Engineer (React 18 Leaflet GIS, Fast-Polling UI, Test Suite 153 Tests).
- Lộ trình phát triển tương lai: Tích hợp phần cứng cảm biến LoRaWAN thực tế + Mạng nơ-ron đồ thị Spatio-Temporal GNN + Nhân rộng chuỗi Smart City toàn quốc.
- The Ask: Kêu gọi kết nối, đầu tư mở rộng và cố vấn công nghệ.
- Slogan & Kết luận: "AirGuard AI — Vì Một Đại Đô Thị Xanh, Thông Minh & Khỏe Mạnh! Sẵn sàng cho phiên Q&A!"
```

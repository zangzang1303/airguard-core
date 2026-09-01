# 🤖 PROMPT TỔNG THỂ TẠO BỘ SLIDE PITCHING AIRGUARD AI (ALL-IN-ONE MASTER PROMPT)
> **Cách sử dụng**: Copy toàn bộ khối văn bản bên dưới và dán trực tiếp vào các công cụ AI tạo slide như **Gamma.app**, **Tome.ai**, **Canva Magic Presentation**, **SlidesAI**, hoặc **Microsoft Copilot**.  
> AI sẽ tự động phân tích và tạo ra bộ slide hoàn chỉnh **7 trang chuẩn cấu trúc Pitching 5 phút**.

---

```text
Hãy tạo một bài thuyết trình chuyên nghiệp (Presentation Pitch Deck) gồm đúng 7 slide theo phong cách Clean-Tech Dark Mode hiện đại (Nền xanh đen đậm #0B1120, màu nhấn Xanh lục bảo #10B981 và Xanh dương công nghệ #0EA5E9, Glassmorphism, font chữ Inter/Outfit sắc nét, bố cục chia Card trực quan và số liệu nổi bật):

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

SLIDE 3: GIẢI PHÁP TỔNG THỂ & TÍNH NĂNG MỚI ĐỘT PHÁ (SOLUTION & KILLER FEATURE)
- Tiêu đề chính: AirGuard AI: Chu Trình Khép Kín & Đột Phá AI Định Tuyến Thể Thao Sạch
- Chu trình khép kín 3 bước:
  1. Giám Sát & Dự Báo Realtime: 5 trạm quan trắc IoT (chu kỳ 15s), Bản đồ nhiệt IDW 60x60 và dự báo chuỗi thời gian 1-24h.
  2. 🌟 KILLER FEATURE — Chat Agent Định Tuyến Chạy Bộ Sạch 0% Trùng Lặp:
     - Cư dân chat tự nhiên: "Tôi muốn chạy 5km quanh hồ lúc này cho người nhạy cảm".
     - Thuật toán độc quyền 2-Leg Penalized Dijkstra trên đồ thị OpenStreetMap (>10,500 cạnh) phạt 30x chiều về.
     - Kết quả: Sinh ra đường chạy khép kín tuần hoàn đúng 0.0% lặp đường cũ, tích phân liều lượng bụi mịn hít vào phổi giảm tới 45%!
  3. Cổng HITL An Toàn: AI chuẩn bị sẵn Thẻ bằng chứng (Evidence Card) để Ban Quản Lý duyệt 1-click kích hoạt máy lọc không khí phản hồi tức thì trong 0.8 giây.

---

SLIDE 4: KIẾN TRÚC HỆ THỐNG • SYSTEM ARCHITECTURE & AI SAFETY
- Tiêu đề chính: KIẾN TRÚC HỆ THỐNG • SYSTEM ARCHITECTURE & AI SAFETY
- Bố cục 2 Cột Cân Đối:
  * Cột 1 (Kiến Trúc Monorepo 5 Phân Tầng):
    - Tầng 1: IoT Mosquitto Broker (5 Sensor Simulators + 5 Device Simulators).
    - Tầng 2: Data Quality Gate (Fail-Closed Ingestion, loại bỏ dữ liệu Stale >300s).
    - Tầng 3: PostgreSQL 16 System of Record (Append-Only audit_logs chống sửa xóa).
    - Tầng 4: FastAPI Core Backend & LangGraph AI Agent State Machine.
    - Tầng 5: React 18 Leaflet GIS Dashboard (Fast-Polling UI 800ms) sau Caddy HTTPS Proxy.
  * Cột 2 (An Toàn AI Tuyệt Đối & HITL):
    - Nguyên tắc "Grounding Trước Fluency": Cổng Grounding Policy Gate đối chiếu 100% số liệu từ Database SoR, cam kết Zero Hallucination (0% bịa đặt số liệu).
    - Bộ chuyển mạch tiền định (Deterministic Fallback): Phản hồi từ cảm biến cục bộ trong < 500ms khi LLM ngoài timeout (>8s), đảm bảo 0% lỗi HTTP 5xx.
    - Bảo mật HITL Server-Side: AI chỉ tạo đề xuất Pending, quyền kích hoạt thiết bị thuộc về con người (Manager).

---

SLIDE 5: KHOẢNH KHẮC TRẢI NGHIỆM THỰC TẾ (LIVE PRODUCT DEMO)
- Tiêu đề chính: KHOẢNH KHẮC TRẢI NGHIỆM THỰC TẾ (LIVE PRODUCT DEMO)
- Tiêu đề phụ: Nền Tảng Đang Vận Hành Trực Tiếp Trên Đám Mây Azure Cloud VM
- Bố cục 3 Hộp Luồng Trải Nghiệm Trọng Tâm:
  [ 1. Giám Sát Bản Đồ Heatmap IDW ] ➔ [ 2. AI Chat & Vẽ Đường Chạy 5km (0% Lặp) ] ➔ [ 3. BQL Duyệt HITL Bật Máy Lọc 0.8s ]
- Hộp Callout URL Lớn Ở Trung Tâm:
  🌐 https://airguard-074-app.indonesiacentral.cloudapp.azure.com
- Dòng chữ dẫn dắt: "Xin mời quý Hội đồng cùng theo dõi thao tác trực tiếp trên màn hình Live Demo!"

---

SLIDE 6: TÁC ĐỘNG ĐỊNH LƯỢNG, NGHIỆM THU KỸ THUẬT & MÔ HÌNH KINH DOANH (BIZ & TRACTION)
- Tiêu đề chính: Giá Trị Định Lượng, Độ Hoàn Thiện Kỹ Thuật 100% & Tiềm Năng Thương Mại
- 3 Hộp Metric Số Liệu Lớn (Big Impact Numbers):
  * [ -45% Liều Lượng Bụi PM2.5 Hít Vào Phổi (Bảo vệ runner & nhóm nhạy cảm hô hấp) ]
  * [ -90% Thời Gian Phản Ứng Xử Lý Ô Nhiễm (Tự ngắt máy lọc sau 45 phút tiết kiệm điện) ]
  * [ 153 / 153 Automated Test Cases Passed (100% PASS - Uptime 99.9% trên Azure VM) ]
- Mô hình kinh doanh & Tín hiệu thị trường:
  * B2B/B2G SaaS: Thu phí quản trị môi trường từ Ban Quản Lý đại đô thị ($2,000 - $5,000/tháng/khu đô thị), tự động xuất báo cáo ESG chuẩn quốc tế.
  * B2C Subscription: Gói cá nhân hóa cảnh báo và định tuyến thể thao cho hàng ngàn runner ($2/tháng).

---

SLIDE 7: ĐỘI NGŨ THỰC HIỆN, TẦM NHÌN DÀI HẠN & PHIÊN HỎI ĐÁP (VISION, TEAM & ASK)
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

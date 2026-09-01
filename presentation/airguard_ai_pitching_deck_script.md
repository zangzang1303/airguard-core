# 🎤 KỊCH BẢN THUYẾT TRÌNH PITCHING AIRGUARD AI (P-074)
> **Dự án**: AirGuard AI — AI Agent Giám Sát Vi Khí Hậu & Điều Khiển Thiết Bị Đô Thị Thông Minh  
> **Nhóm thực hiện**: P-074 / Tứ Kỵ Sĩ Khải Huyền (AI20K Build Phase Cohort 3)  
> **Thời lượng pitching**: **5 - 7 phút** (Pitch) + **3 - 5 phút** (Q&A)  
> **Địa chỉ Demo Live**: [https://airguard-074-app.indonesiacentral.cloudapp.azure.com](https://airguard-074-app.indonesiacentral.cloudapp.azure.com)  
> **Mã nguồn GitHub**: [https://github.com/AI20K-Build-Phase-Cohort-3/P-074](https://github.com/AI20K-Build-Phase-Cohort-3/P-074)

---

## ⏱️ MA TRẬN PHÂN BỔ THỜI GIAN (PITCHING TIMELINE)

| STT | Slide | Tiêu đề Slide | Thời lượng | Người trình bày chính |
|:---:|---|---|:---:|---|
| **1** | Slide 1 | **Cover**: AirGuard AI — Người Gác Cổng Không Khí Sạch | 30s | Team Lead (Lê Tuấn Cảnh) |
| **2** | Slide 2 | **The Problem**: Nỗi Đau Ô Nhiễm Siêu Cục Bộ Tại Đô Thị | 45s | Team Lead (Lê Tuấn Cảnh) |
| **3** | Slide 3 | **The Solution**: Hệ Sinh Thái AirGuard AI Toàn Diện | 45s | Team Lead (Lê Tuấn Cảnh) |
| **4** | Slide 4 | **Core Features**: 4 Trụ Cột Đột Phá (Heatmap, Routing, AI, HITL) | 60s | AI Engineer (Hoàng Lê Minh) |
| **5** | Slide 5 | **System Architecture**: Kiến Trúc 5 Lớp & Monorepo | 45s | Integration Engineer (Hán Vũ Long) |
| **6** | Slide 6 | **Zero-Hallucination & Safe AI**: Cổng Kiểm Soát Căn Cứ | 45s | AI Engineer (Hoàng Lê Minh) |
| **7** | Slide 7 | **Live Demo Flow**: Bản Đồ, Định Tuyến Chạy & Bật Máy Lọc | 60s | Frontend/QA (Phạm Thế Dũng) |
| **8** | Slide 8 | **Business Impact & ESG**: Giá Trị Bền Vững Cho Đô Thị | 30s | Team Lead (Lê Tuấn Cảnh) |
| **9** | Slide 9 | **Project Milestone & Quality**: 153/153 Tests Passed | 30s | Frontend/QA (Phạm Thế Dũng) |
| **10** | Slide 10 | **Team P-074**: Đội Ngũ Tứ Kỵ Sĩ Khải Huyền | 30s | Team Lead (Lê Tuấn Cảnh) |
| **11** | Slide 11 | **Future Vision**: Tầm Nhìn Thương Mại Hóa & Smart City | 30s | Team Lead (Lê Tuấn Cảnh) |
| **12** | Slide 12 | **Call to Action**: Q&A & Lời Cảm Ơn | 30s | Toàn đội P-074 |

---

## 🎯 CHI TIẾT KỊCH BẢN TỪNG SLIDE (SLIDE-BY-SLIDE SCRIPT)

---

### 🟢 SLIDE 1: TRANG BÌA (COVER SLIDE)
* **Bố cục trực quan (Visuals)**:
  * Logo AirGuard AI hiện đại phong cách Clean Tech / Glassmorphism.
  * Tagline: *"AI Agent Giám Sát Vi Khí Hậu & Điều Khiển Thiết Bị Đô Thị Thông Minh — Vinhomes Ocean Park 1"*.
  * Huy hiệu: `Cohort 3 Build Phase — Nhóm P-074 (Tứ Kỵ Sĩ Khải Huyền)`.
  * Huy hiệu chất lượng: `153/153 Automated Tests Passed (100%)` | `Live on Azure Cloud`.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 30 giây)**:
  > *"Kính chào quý Ban giám khảo, các Mentor và toàn thể hội đồng!  
  > Chúng tôi là **Nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền**.  
  > Hôm nay, chúng tôi rất tự hào giới thiệu **AirGuard AI** — giải pháp toàn diện kết hợp IoT thời gian thực, thuật toán định tuyến đồ thị đường thực OSM và Trợ lý AI tiếng Việt có kiểm soát căn cứ (Zero Hallucination), bảo vệ sức khỏe hô hấp cho hàng chục ngàn cư dân tại đại đô thị Vinhomes Ocean Park 1."*

---

### 🔴 SLIDE 2: NỖI ĐAU THỊ TRƯỜNG & VẤN ĐỀ THỰC TẾ (THE PROBLEM)
* **Bố cục trực quan (Visuals)**:
  * Biểu đồ so sánh 3 nỗi đau lớn:
    1. **Mù mờ số liệu vi khí hậu**: Các trạm khí tượng công cộng chỉ đặt ở trung tâm thành phố cách xa 15-20km, không phản ánh được tính chất đặc thù của biển hồ nước mặn 6.1ha hay trục thi công bụi mịn.
    2. **Runner & Cư dân hít phải bụi độc hại**: Không biết chạy ở đâu, giờ nào trong lành; các app chỉ đường thông thường hướng dẫn chạy vào trục đường ô nhiễm nặng.
    3. **Ban Quản Lý bị động**: Phải xử lý thủ công, thiếu công cụ cảnh báo sớm và thiếu quy trình phê duyệt can thiệp thiết bị dập bụi an toàn.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 45 giây)**:
  > *"Thưa quý vị, tại các đại đô thị hiện đại, chất lượng không khí không hề đồng nhất. Tại Vinhomes Ocean Park 1, khu vực sát biển hồ có thể rất trong lành với AQI 35, nhưng chỉ cách đó vài trăm mét, trục đường thi công Sao Biển lại có AQI lên tới 150+.  
  > Người dân hoàn toàn 'mù mờ' số liệu cục bộ khi ra ngoài tập thể thao; người nhạy cảm hô hấp đối mặt rủi ro sức khỏe; trong khi Ban quản lý lại thiếu một cơ chế giám sát tập trung để kịp thời kích hoạt hệ thống lọc dập bụi."*

---

### 💡 SLIDE 3: GIẢI PHÁP ĐỘT PHÁ AIRGUARD AI (THE SOLUTION)
* **Bố cục trực quan (Visuals)**:
  * Hình ảnh Mockup Dashboard sắc nét trên Azure VM.
  * 3 mũi tên giá trị giải pháp:
    * **Giám sát siêu cục bộ (Hyper-local IoT)**: 5 trạm quan trắc vi khí hậu (S01–S05) đo 4 chỉ số (PM2.5, CO2, tiếng ồn, nhiệt độ).
    * **Định tuyến thông minh (Safe Route Engine)**: Sinh đường chạy thể thao tuần hoàn 0% trùng lặp, tối thiểu hóa liều lượng bụi hít vào.
    * **Can thiệp an toàn có con người giám sát (HITL & IoT Dispatcher)**: Tự động đề xuất cảnh báo nhưng trao quyền quyết định tối hậu 1-click cho Quản lý.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 45 giây)**:
  > *"Để giải quyết triệt để bài toán trên, chúng tôi xây dựng **AirGuard AI** — hệ sinh thái khép kín từ cảm biến đến hành động:  
  > 1. Thu thập dữ liệu vi khí hậu liên tục chu kỳ 15 giây qua MQTT Mosquitto.  
  > 2. Cung cấp Trợ lý AI tiếng Việt thông minh giải đáp mọi thắc mắc và định tuyến lộ trình chạy bộ sạch bụi.  
  > 3. Thiết lập Cổng quản trị HITL (Human-in-the-loop) giúp Ban quản lý thẩm định chứng cứ và kích hoạt máy lọc không khí chỉ bằng 1 cú nhấp chuột."*

---

### ⚡ SLIDE 4: BỐN TRỤ CỘT TÍNH NĂNG CỐT LÕI (CORE CAPABILITIES)
* **Bố cục trực quan (Visuals)**:
  * Grid 4 ô tính năng nổi bật:
    * `1. GIS & Heatmap IDW`: Lớp phủ nhiệt nội suy không gian 60x60 và viền xanh hành lang trong lành quanh hồ 24.5ha.
    * `2. 2-Leg Penalized Dijkstra`: Thuật toán định tuyến đường chạy khép kín S->W->S trên đồ thị OSM >10,500 cạnh, 0% chạy lùi.
    * `3. AI Agent Zero-Hallucination`: LangGraph State Machine truy vấn 8 Backend Tools từ DB SoR.
    * `4. HITL & Manual Device Control`: Điều khiển cụm máy lọc FILTER-S01..S05 qua MQTT, nhận phản hồi ACK trong 0.8s.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 60 giây)**:
  > *"Hệ thống nổi bật với 4 năng lực kỹ thuật vượt trội:  
  > Thứ nhất, bản đồ nhiệt IDW tính toán theo thời gian thực, trực quan hóa ngay điểm nóng ô nhiễm.  
  > Thứ hai, thuật toán định tuyến chạy bộ 2 chặng độc quyền của chúng tôi phạt 30 lần trọng số chiều về, đảm bảo lộ trình khép kín tuần hoàn mà không bao giờ bị quay đầu chạy lùi đường cũ.  
  > Thứ ba, Trợ lý AI tuyệt đối không bịa đặt số liệu nhờ Cổng kiểm soát căn cứ Grounding Gate.  
  > Và thứ tư, khả năng điều khiển thiết bị phản hồi siêu tốc dưới 0.8 giây với độ trễ cực thấp."*

---

### 🏗️ SLIDE 5: KIẾN TRÚC HỆ THỐNG 5 LỚP (SYSTEM ARCHITECTURE)
* **Bố cục trực quan (Visuals)**:
  * Sơ đồ phân tầng 5 lớp (Layered Architecture):
    1. **IoT & Telemetry Layer**: 5 Sensor Simulators + 5 Device Simulators $\to$ MQTT Mosquitto Broker.
    2. **Ingestion & Validation Layer**: MQTT Consumer, Data Quality Gate (Lọc Stale/Invalid).
    3. **System of Record (SoR)**: PostgreSQL 16 (Append-Only Audit Logs, Idempotent Seeds).
    4. **Application & AI Engine**: FastAPI Backend, LangGraph AI Agent, Open-Meteo Weather, 2-Leg OSM Router.
    5. **Presentation Layer**: React 18 + Leaflet GIS Dashboard, Caddy Reverse Proxy, HTTPS Live.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 45 giây)**:
  > *"Về mặt kiến trúc, AirGuard AI được thiết kế theo mô hình Monorepo 5 lớp chuẩn công nghiệp:  
  > Mọi dữ liệu môi trường đều đi qua Gateway kiểm tra chất lượng (Data Quality Gate) trước khi nạp vào PostgreSQL SoR. Backend FastAPI đóng vai trò nguồn chân lý duy nhất (Single Source of Truth), tách biệt hoàn toàn giữa luồng dữ liệu công khai của Cư dân và luồng phê duyệt bảo mật của Quản lý đô thị."*

---

### 🛡️ SLIDE 6: AI AN TOÀN & CHỐNG ẢO GIÁC (AI SAFETY & ZERO HALLUCINATION)
* **Bố cục trực quan (Visuals)**:
  * Sơ đồ luồng thẩm định: `User Prompt -> LangGraph Router -> Backend Tool Calling -> Grounding Policy Gate -> Verified Facts -> Response Composer`.
  * Khối chuyển mạch dự phòng: `Deterministic Fallback Composer` (Kích hoạt khi LLM Timeout $> 8.0s \to$ Đảm bảo 0% lỗi HTTP 5xx).
  * Quy tắc bất khả xâm phạm: AI **chỉ tạo đề xuất ở trạng thái Pending**, con người giữ quyền quyết định tối hậu.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 45 giây)**:
  > *"Một trong những rủi ro lớn nhất của AI trong y tế và môi trường là hiện tượng ảo giác (Hallucination).  
  > Tại AirGuard AI, chúng tôi áp dụng nguyên tắc **'Grounding trước Fluency'**: 100% câu trả lời có chứa số liệu vi khí hậu bắt buộc phải được bóc tách từ kết quả Tool calling của chính phiên truy vấn đó. Nếu AI không tìm thấy dữ liệu hoặc LLM bị gián đoạn, bộ chuyển mạch tiền định sẽ kích hoạt trong 500ms, trả lời an toàn tuyệt đối mà không bao giờ suy diễn lung tung."*

---

### 💻 SLIDE 7: TRÌNH DIỄN DEMO THỰC TẾ (LIVE PRODUCT DEMO)
* **Bố cục trực quan (Visuals)**:
  * Ghép 3 khung hình thực tế từ web live:
    1. Bản đồ GIS thời gian thực với lớp phủ IDW.
    2. Thẻ lộ trình chạy bộ 5km khép kín và tích phân liều lượng bụi mịn hít vào ($\mu g$).
    3. Bật máy lọc không khí nhận ACK trong 0.8s và Cổng duyệt HITL 1-Click.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 60 giây - Trình chiếu live hoặc video)**:
  > *"Ngay bây giờ, kính mời quý vị cùng trải nghiệm sản phẩm trực tiếp đang chạy live trên Azure Cloud:  
  > Khi một cư dân thuộc nhóm nhạy cảm muốn chạy 5km, AI ngay lập tức định tuyến men theo hành lang trong lành quanh biển hồ, hiển thị cự ly 5.0km chính xác và tính toán lượng bụi hít vào chỉ 4.8 microgram.  
  > Đồng thời, khi trạm Sao Biển bị ô nhiễm, hệ thống tạo đề xuất HITL; Quản lý bấm [Phê duyệt], lệnh MQTT truyền đi và máy lọc chuyển sang trạng thái lọc tăng cường chỉ trong đúng 0.8 giây!"*

---

### 📈 SLIDE 8: TÁC ĐỘNG KINH TẾ, XÃ HỘI & ESG (BUSINESS IMPACT & ESG)
* **Bố cục trực quan (Visuals)**:
  * Thước đo tác động 3 trục:
    * **Cư dân (Health)**: Giảm $35 - 45\%$ lượng bụi mịn hít vào phổi khi tập thể thao ngoài trời.
    * **Vận hành đô thị (Ops)**: Giảm $90\%$ thời gian phản ứng xử lý điểm nóng ô nhiễm; tiết kiệm năng lượng nhờ tự động tắt máy lọc sau chu kỳ 45 phút.
    * **Bền vững (ESG Reporting)**: Tự động xuất báo cáo chuẩn hóa PDF/Excel phục vụ kiểm toán môi trường và chứng chỉ đô thị xanh.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 30 giây)**:
  > *"AirGuard AI mang lại giá trị thiết thực: Giúp bảo vệ lá phổi cho hàng ngàn cư dân mỗi ngày, tối ưu hóa $90\%$ thời gian điều hành của ban quản lý và cung cấp báo cáo ESG chuẩn mực, nâng tầm Vinhomes Ocean Park thành hình mẫu đô thị xanh thông minh tiêu chuẩn quốc tế."*

---

### 🏆 SLIDE 9: TIẾN ĐỘ HOÀN THÀNH & ĐẢM BẢO CHẤT LƯỢNG (QUALITY METRICS)
* **Bố cục trực quan (Visuals)**:
  * Bảng số liệu kiểm thử nghiệm thu:
    * `153 / 153` Automated Test Cases Passed (**100% PASS**).
    * `Độ trễ API`: $< 120\text{ms}$ (Chuẩn $< 200\text{ms}$).
    * `Độ trễ phản hồi ACK thiết bị`: $0.8\text{s}$ (Chuẩn $< 1.5\text{s}$).
    * `Uptime SLA`: $99.9\%$ trên Azure Cloud Virtual Machine.
    * `Tài liệu nghiệm thu`: Đầy đủ SRS v2.2.0, Architecture, ADRs, AGENTS Runbook.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 30 giây)**:
  > *"Về chất lượng kỹ thuật, sản phẩm của chúng tôi đã vượt qua **153/153 kịch bản kiểm thử tự động** bao phủ toàn diện từ Unit test, API Contract đến E2E Routing và HITL. Toàn bộ mã nguồn và tài liệu đã được đóng gói chuẩn mực, sẵn sàng chuyển giao."*

---

### 👥 SLIDE 10: ĐỘI NGŨ THỰC HIỆN P-074 (TEAM & ROLES)
* **Bố cục trực quan (Visuals)**:
  * Ảnh đại diện 4 thành viên nhóm P-074:
    1. **Lê Tuấn Cảnh** — *Team Lead / Backend & Data / IoT* (Kiến trúc hệ thống, FastAPI, Postgres SoR, Simulators, Azure VM).
    2. **Hán Vũ Long** — *Integration / AI Engineer* (Tích hợp MQTT Broker, Forecast Service, Celery Worker).
    3. **Hoàng Lê Minh** — *AI Engineer* (LangGraph State Machine, Grounding Policy Gate, Agent Registry).
    4. **Phạm Thế Dũng** — *Frontend / QA Engineer* (React 18 Dashboard, Leaflet GIS, Test Suite 153 Tests).

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 30 giây)**:
  > *"Thành quả này đến từ sự phối hợp kỷ luật và tinh thần trách nhiệm cao của 4 thành viên nhóm P-074:  
  > Từ thiết kế kiến trúc, xây dựng pipeline IoT, phát triển thuật toán AI cho đến hoàn thiện giao diện người dùng và tự động hóa kiểm thử."*

---

### 🚀 SLIDE 11: TẦM NHÌN TƯƠNG LAI (FUTURE ROADMAP)
* **Bố cục trực quan (Visuals)**:
  * Lộ trình phát triển mở rộng:
    * **Phase 2 (Tháng 10/2026)**: Tích hợp thiết bị cảm biến vật lý ESP32/LoRaWAN thực tế; kết nối camera AI đếm mật độ giao thông.
    * **Phase 3 (2027)**: Mở rộng mô hình dự báo không gian Spatio-Temporal Graph Neural Networks (GNN) và triển khai cho toàn bộ chuỗi đại đô thị Vinhomes/Smart City tại Việt Nam.

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 30 giây)**:
  > *"Trong tương lai, chúng tôi sẽ nâng cấp mô hình AI sang mạng đồ thị GNN dự báo đa trạm và mở rộng kết nối với hệ thống phần cứng cảm biến LoRaWAN thực địa, hướng tới trở thành nền tảng quản trị không khí tiêu chuẩn cho các đại đô thị thông minh."*

---

### 👏 SLIDE 12: KẾT LUẬN & HỎI ĐÁP (Q&A & CLOSING)
* **Bố cục trực quan (Visuals)**:
  * Thông tin liên hệ & Mã QR truy cập Web Demo trực tiếp:
    * Website: `https://airguard-074-app.indonesiacentral.cloudapp.azure.com`
    * GitHub: `https://github.com/AI20K-Build-Phase-Cohort-3/P-074`
  * Thông điệp kết: *"AirGuard AI — Vì Một Đại Đô Thị Xanh & Khỏe Mạnh!"*

* **🗣️ Lời thoại thuyết trình (Speaker Notes - 30 giây)**:
  > *"Xin chân thành cảm ơn quý Ban giám khảo, các Mentor và toàn thể hội đồng đã lắng nghe bài thuyết trình của nhóm P-074!  
  > Chúng tôi rất sẵn sàng lắng nghe các câu hỏi và nhận xét đóng góp từ quý hội đồng!"*

---

## 💡 BỘ CÂU HỎI HỘI ĐỒNG THƯỜNG HỎI & CÁCH TRẢ LỜI CHUẨN (Q&A CHEATSHEET)

#### ❓ Câu hỏi 1: Làm sao đảm bảo AI không bị ảo giác đưa ra lời khuyên chạy bộ sai vào vùng ô nhiễm?
> **Trả lời**: *"Hệ thống sử dụng **Grounding Policy Gate** độc quyền. Trước khi câu trả lời gửi về cho người dùng, hệ thống kiểm tra đối chiếu từng con số trong văn bản với kết quả trả về từ DB PostgreSQL của cùng request đó. Đồng thời, thuật toán định tuyến chạy sạch 2-Leg Penalized Dijkstra chạy độc lập trên đồ thị OSM thực tế bằng thuật toán toán học xác định (Deterministic), không giao việc tính toán đường chạy cho LLM tự bịa đặt."*

#### ❓ Câu hỏi 2: Tại sao phải dùng thuật toán 2-Leg Dijkstra mà không dùng Google Maps hay Dijkstra thông thường?
> **Trả lời**: *"Dijkstra thông thường khi tìm đường khép kín từ điểm S có target 5km sẽ tìm đường ngắn nhất đến điểm trung gian W rồi bắt người dùng quay đầu chạy lùi 100% đường cũ. Thuật toán 2 chặng (2-Leg) của chúng tôi áp dụng trọng số phạt 30x lên toàn bộ các cạnh của chặng đi (Forward Leg), buộc chặng về (Backward Leg) phải tìm cung đường hoàn toàn mới quanh bờ hồ, đạt độ trùng lặp 0% tuần hoàn."*

#### ❓ Câu hỏi 3: Nếu AI bị ngắt mạng hoặc LLM bị timeout thì hệ thống xử lý thế nào?
> **Trả lời**: *"Chúng tôi áp dụng cơ chế **Fail-Closed & Deterministic Fallback Switcher**: Khi gọi API LLM quá 8.0 giây hoặc gặp lỗi mạng, bộ điều phối cục bộ trong 500ms sẽ tự động tạo phản hồi chuẩn xác trực tiếp từ số liệu sensor của trạm mà không trả mã lỗi HTTP 5xx về cho người dùng."*

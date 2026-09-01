# 🎤 KỊCH BẢN PITCHING SLIDE AIRGUARD AI (P-074)
> **BÁM SÁT 100% KIẾN TRÚC & TÀI LIỆU HỆ THỐNG THỰC TẾ**  
> **Đính kèm tài sản hình ảnh trích xuất trực tiếp từ dự án trong thư mục `image/`**  
> **Thời lượng chuẩn**: **5 - 7 phút** | **Số lượng Slide**: **12 Slides**

---

## 🗺️ BẢNG ÁNH XẠ HÌNH ẢNH HỆ THỐNG VÀO TỪNG SLIDE

| STT | Slide | Tiêu đề Slide | Hình ảnh hệ thống đính kèm trong `image/` | Nguồn tài liệu hệ thống |
|:---:|---|---|---|---|
| **1** | Slide 1 | **Cover**: AirGuard AI — Người Gác Cổng Vi Khí Hậu | `image/Mockup 1 - GIS Dashboard & Heatmap.png` | Live App / README.md |
| **2** | Slide 2 | **The Problem**: Nỗi Đau Ô Nhiễm Siêu Cục Bộ Tại Đô Thị | *Bản đồ vi khí hậu Ocean Park 1 & Biểu đồ chênh lệch AQI* | SRS Mục 1.2 & 2.1 |
| **3** | Slide 3 | **The Solution & Use Cases**: 2 Role & 10 Ca Sử Dụng | `image/Use Case Diagram.png` | SRS Mục 4.1 |
| **4** | Slide 4 | **System Architecture**: Kiến Trúc Tổng Thể & 5 Phân Tầng | `image/Sơ đồ kiến trúc tổng thể.png` / `image/Kiến trúc phân tầng 5 lớp.png` | ARCHITECTURE Mục 2 |
| **5** | Slide 5 | **IoT Pipeline & Quality Gate**: Thu Thập & Lọc Dữ Liệu | `image/Luồng thu thập dữ liệu và Kiểm soát chất lượng.png` | ARCHITECTURE Mục 3.1 |
| **6** | Slide 6 | **Core Algorithm**: Định Tuyến Chạy Sạch 2-Leg Dijkstra | `image/Kiến trúc thuật toán tìm đường chạy sạch.png` | SRS Mục 5.3 & ADR-0005 |
| **7** | Slide 7 | **Safe AI & Grounding Gate**: AI Agent Không Ảo Giác | `image/Luồng hội thoại của AI Agent & Grounding Policy Gate.png` | SRS Mục 5.4 & 8 |
| **8** | Slide 8 | **HITL & Device Control**: Phê Duyệt & Bật Máy Lọc 0.8s | `image/Luồng cảnh báo tự động & HITL.png` / `image/Mockup 5 - HITL Approval Center.png`| SRS Mục 5.7 & ADR-0003 |
| **9** | Slide 9 | **Live Product Showcase**: Giao Diện Thực Tế Trên Web | `image/Mockup 1` + `Mockup 2` + `Mockup 3` | Azure Cloud VM Live |
| **10**| Slide 10| **Business Impact & ESG**: Tác Động Sức Khỏe & Vận Hành | `image/Mockup 6 - Audit Log Center.png` | reports/business_impact_metrics.md |
| **11**| Slide 11| **Quality & Deployment**: 153 Tests & Azure Topology | `image/Sơ đồ triển khai hạ tầng.png` | reports/technical_metrics_evaluation.md |
| **12**| Slide 12| **Team P-074 & Closing**: Đội Ngũ Tứ Kỵ Sĩ & Hỏi Đáp | *Ảnh 4 thành viên nhóm P-074 & Mã QR Web Demo* | Project Charter |

---

## 📑 CHI TIẾT TỪNG SLIDE: NỘI DUNG, HÌNH ẢNH, LỜI THOẠI & PROMPT AI

---

### 🟢 SLIDE 1: TRANG BÌA (COVER SLIDE)
* **Hình ảnh đính kèm**: `image/Mockup 1 - GIS Dashboard & Heatmap.png` (Làm hình nền mờ công nghệ).
* **Nội dung trên Slide**:
  * **AIRGUARD AI** — *AI Agent Giám Sát Vi Khí Hậu & Điều Khiển Thiết Bị Đô Thị Thông Minh Vinhomes Ocean Park 1*
  * **Nhóm thực hiện**: `P-074 / Tứ Kỵ Sĩ Khải Huyền (AI20K Build Phase Cohort 3)`
  * **Huy hiệu chất lượng**: `153/153 Tests Passed (100%)` | `Live on Azure Cloud VM` | `Zero-Hallucination AI`
  * **Đường link**: `https://airguard-074-app.indonesiacentral.cloudapp.azure.com`

* **🗣️ Lời thoại người trình bày (30s)**:
  > *"Kính chào quý Ban giám khảo, các Mentor và toàn thể hội đồng! Chúng tôi là **Nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền**.  
  > Hôm nay, chúng tôi rất tự hào mang đến dự án **AirGuard AI** — giải pháp toàn diện kết hợp IoT vi khí hậu thời gian thực, thuật toán định tuyến đồ thị đường thực OSM và Trợ lý AI tiếng Việt có kiểm soát căn cứ (Zero Hallucination), bảo vệ sức khỏe cho hàng chục ngàn cư dân tại đại đô thị Vinhomes Ocean Park 1.  
  > Một sản phẩm **đã được xây dựng hoàn chỉnh, vượt qua 153 bài kiểm thử tự động và đang chạy thực tế trên Azure Cloud**."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a modern dark-mode title slide for "AirGuard AI - Smart Urban Microclimate Monitoring & Device Control System". Subtitle: "Vinhomes Ocean Park 1 - Team P-074 (Four Horsemen)". Include badges: "153/153 Tests Passed (100%)", "Live on Azure Cloud", "Zero-Hallucination AI". Sleek tech background with glowing GIS elements, emerald green and cyan accents.
  ```

---

### 🔴 SLIDE 2: NỖI ĐAU THỊ TRƯỜNG & BỐI CẢNH ĐÔ THỊ (THE PROBLEM)
* **Hình ảnh đính kèm**: Sơ đồ so sánh trạm khí tượng xa 15km vs thực địa Ocean Park 1.
* **Nội dung trên Slide (3 Nỗi đau lớn)**:
  1. **Mù mờ số liệu vi khí hậu siêu cục bộ**: Trạm quan trắc quốc gia cách xa 15km không phản ánh được chênh lệch vi khí hậu giữa mặt nước Biển Hồ 6.1ha (AQI 35) và trục đường thi công Sao Biển (AQI 150+).
  2. **Người tập thể thao & Nhóm nhạy cảm hít bụi độc hại**: Không biết chạy ở đâu trong lành; các app chỉ đường thông thường hướng dẫn chạy vào trục đường ô nhiễm nặng.
  3. **Ban Quản Lý bị động**: Thiếu công cụ phát hiện tức thì điểm nóng ô nhiễm và thiếu quy trình phê duyệt can thiệp thiết bị dập bụi an toàn.

* **🗣️ Lời thoại người trình bày (45s)**:
  > *"Thưa quý vị, tại các đại đô thị quy mô lớn, **chất lượng không khí biến thiên siêu cục bộ từng góc phố**.  
  > Tại Vinhomes Ocean Park 1, khu vực biển hồ nước mặn rất trong lành với AQI 35, nhưng chỉ cách đó vài trăm mét, trục đường thi công Sao Biển lại có AQI lên tới 150+.  
  > Cư dân chạy bộ không biết chạy ở đâu để an toàn, vô tình hít phải hàng microgram bụi mịn vào phổi; trong khi Ban quản lý lại hoàn toàn bị động, thiếu công cụ giám sát tập trung để kích hoạt hệ thống lọc dập bụi kịp thời."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a 3-column Problem Statement slide: Title: "Hyper-local Air Pollution & 3 Critical Urban Pain Points". Card 1 (Runners & Residents): "Blind to local microclimate, inhaling toxic PM2.5 during workouts". Card 2 (Sensitive Groups): "No personalized health-aware alerts for asthma/children". Card 3 (Urban Management): "Passive monitoring, manual Excel reports, no rapid device intervention". High-contrast warning icons, red/amber accents.
  ```

---

### 💡 SLIDE 3: TỔNG THỂ HỆ THỐNG & 10 USE CASES (THE SOLUTION & USE CASES)
* **Hình ảnh đính kèm**: `image/Use Case Diagram.png` (Trích xuất từ Mục 4.1 SRS).
* **Nội dung trên Slide**:
  * **2 Vai trò người dùng (Roles)**:
    * `Cư Dân Đô Thị (Resident)`: Bao gồm 3 nhóm thể trạng (`normal`, `sensitive`, `outdoor_sport`).
    * `Quản Lý Đô Thị (Urban Manager / BQL)`: Quyền quản trị, thẩm định HITL, điều khiển thiết bị và xuất báo cáo.
  * **10 Use Cases cốt lõi**:
    * Nhóm Cư dân: `UC-01` Giám sát bản đồ & Heatmap $\to$ `UC-02` Chi tiết trạm & Dự báo $\to$ `UC-03` Cảnh báo Cooldown $\to$ `UC-04` Trợ lý AI $\to$ `UC-05` Định tuyến chạy sạch $\to$ `UC-06` Hồ sơ sức khỏe.
    * Nhóm Quản lý: `UC-07` Điều khiển máy lọc 0.8s $\to$ `UC-08` Cổng phê duyệt HITL $\to$ `UC-09` Nhật ký kiểm toán bất biến $\to$ `UC-10` Báo cáo ESG.

* **🗣️ Lời thoại người trình bày (45s)**:
  > *"Để giải quyết triệt để vấn đề trên, AirGuard AI được thiết kế với **2 vai trò rõ ràng và 10 ca sử dụng chuẩn hóa**:  
  > * Đối với **Cư dân**: Cung cấp bản đồ vi khí hậu trực quan, đàm thoại Trợ lý AI và tự động sinh lộ trình chạy bộ trong lành theo thể trạng sức khỏe.  
  > * Đối với **Ban quản lý**: Cung cấp Cổng phê duyệt HITL để thẩm định chứng cứ trước khi phát cảnh báo khẩn và trực tiếp điều khiển các cụm máy lọc không khí."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create an architecture & use case overview slide featuring an embedded Use Case Diagram. Title: "AirGuard AI Solution: 2 Roles & 10 Core Use Cases". Left side: Resident Domain (GIS Map, Station Drawer, Clean Routing, AI Chat, Health Profile). Right side: Urban Manager Domain (Device Manual Control, HITL Approval Portal, Immutable Audit Trail, ESG Reporting). Clean two-column layout with glowing role badges.
  ```

---

### 🏗️ SLIDE 4: KIẾN TRÚC MONOREPO 5 LỚP (SYSTEM ARCHITECTURE)
* **Hình ảnh đính kèm**: `image/Sơ đồ kiến trúc tổng thể.png` hoặc `image/Kiến trúc phân tầng 5 lớp.png` (Trích xuất từ ARCHITECTURE.md Mục 2).
* **Nội dung trên Slide (5 Tầng công nghệ)**:
  1. **IoT & Telemetry**: 5 Trạm cảm biến + 5 Cụm máy lọc $\to$ Mosquitto MQTT Broker (chu kỳ 15s).
  2. **Ingestion & Validation**: Paho MQTT Consumer, Data Quality Gate (Lọc Stale/Invalid, Fail-closed).
  3. **System of Record (SoR)**: PostgreSQL 16 (Append-Only `audit_logs`, `measurements`, `alerts`).
  4. **Application & AI Engine**: FastAPI Backend, LangGraph AI Agent, 2-Leg OSM Router, Open-Meteo Weather API.
  5. **Presentation Layer**: React 18 Leaflet GIS Dashboard, Fast-Polling UI (800ms ACK), Caddy HTTPS Proxy.

* **🗣️ Lời thoại người trình bày (45s)**:
  > *"Về mặt kiến trúc, AirGuard AI tuân thủ nghiêm ngặt mô hình Monorepo 5 phân tầng chuẩn công nghiệp:  
  > Dữ liệu vi khí hậu đi qua Gateway kiểm soát chất lượng nghiêm ngặt trước khi nạp vào PostgreSQL SoR. Backend FastAPI đóng vai trò nguồn chân lý duy nhất (Single Source of Truth), phân quyền độc lập giữa luồng tra cứu công khai của Cư dân và luồng can thiệp thiết bị bảo mật của Quản lý đô thị."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a 5-Layer Monorepo Architecture slide. Title: "Industrial 5-Layer Monorepo System Architecture". Layer 1: IoT & Telemetry (Mosquitto MQTT). Layer 2: Ingestion & Quality Gate (Fail-Closed Validation). Layer 3: System of Record (PostgreSQL 16, Append-Only Audit). Layer 4: Application & AI Engine (FastAPI, LangGraph, 2-Leg Dijkstra OSM Router). Layer 5: Presentation (React 18 Leaflet GIS, Fast-Polling UI). Clean vertical layered diagram.
  ```

---

### 📡 SLIDE 5: PIPELINE THU THẬP TELEMETRY & KIỂM SOÁT CHẤT LƯỢNG (IOT PIPELINE)
* **Hình ảnh đính kèm**: `image/Luồng thu thập dữ liệu và Kiểm soát chất lượng.png` (Trích xuất từ ARCHITECTURE.md Mục 3.1).
* **Nội dung trên Slide**:
  * **Chu kỳ phát sóng**: 15 giây/lần cho 5 trạm quan trắc (`S01` đến `S05`) qua topics `airguard/stations/{id}/measurements`.
  * **Công thức AQI chuẩn hóa**: Tính toán theo thuật toán nội suy nồng độ US EPA 2012 (24h Concentration Sub-Index).
  * **Cơ chế Fail-Closed Gate**:
    * Từ chối các bản tin thiếu trường bắt buộc, giá trị âm hoặc vượt ngưỡng vật lý ($PM2.5 > 1000\mu g/m^3$).
    * Đánh dấu `stale/offline` nếu trạm ngưng phát quá 300 giây; **tuyệt đối không dùng dữ liệu trạm hỏng để vẽ đường chạy hoặc đưa ra kết luận môi trường**.

* **🗣️ Lời thoại người trình bày (40s)**:
  > *"Trái tim dữ liệu của hệ thống là Pipeline IoT thời gian thực. Mỗi 15 giây, các trạm đo đẩy telemetry đo 4 thông số về broker Mosquitto.  
  > Tại đây, **Data Quality Gate** áp dụng nguyên tắc Fail-Closed: Tự động loại bỏ dữ liệu bất thường và từ chối sử dụng dữ liệu trạm stale/offline để vẽ đường chạy an toàn, đảm bảo tính trung thực tuyệt đối của số liệu đầu vào."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create an IoT Data Pipeline & Quality Gate slide. Title: "Real-time Telemetry Ingestion & Fail-Closed Quality Gate". Features: MQTT 15s publishing cycle, US EPA 2012 AQI derivation, automated validation (rejecting negative/out-of-bounds values), stale detection (>300s). Flow diagram showing Simulator -> Mosquitto -> Consumer Validator -> PostgreSQL SoR.
  ```

---

### 🧭 SLIDE 6: THUẬT TOÁN ĐỊNH TUYẾN CHẠY BỘ SẠCH 2-LEG PENALIZED DIJKSTRA (CORE ALGORITHM)
* **Hình ảnh đính kèm**: `image/Kiến trúc thuật toán tìm đường chạy sạch.png` (Trích xuất từ SRS Mục 5.3 & ADR-0005).
* **Nội dung trên Slide (Đột phá thuật toán)**:
  * **Vấn đề của thuật toán thông thường**: Dijkstra tiêu chuẩn tìm đường khép kín sẽ quay đầu chạy lùi 100% đường cũ (100% Retracing).
  * **Giải pháp 2-Leg Penalized Dijkstra**:
    1. `Chặng đi (Forward Leg S -> W)`: Tìm đường ngắn nhất và sạch nhất đến điểm mốc Waypoint $W$.
    2. `Phạt trọng số quay đầu`: Nhân trọng số $30\times$ lên toàn bộ các cạnh đã đi qua ở chặng đi.
    3. `Chặng về (Backward Leg W -> S)`: Buộc thuật toán tìm cung đường hoàn toàn mới men theo bờ hồ 24.5ha $\to$ **Đạt 0% trùng lặp đường cũ**.
  * **Tích phân liều lượng bụi hít vào**: Tính $M_{inhaled} = \int C(t) \cdot V_E \, dt$ ($\mu g$) dựa trên vận tốc chạy và thông khí phổi.

* **🗣️ Lời thoại người trình bày (60s)**:
  > *"Đây là một trong những đột phá công nghệ lớn nhất của chúng tôi: **Thuật toán định tuyến chạy bộ sạch 2-Leg Penalized Dijkstra trên đồ thị đường thực OSM hơn 10,500 cạnh**.  
  > Thay vì bắt runner quay đầu chạy lùi đường cũ như các thuật toán thông thường, thuật toán 2 chặng của chúng tôi phạt 30 lần trọng số chiều về, ép cung đường khép kín tuần hoàn quanh biển hồ với **0% trùng lặp**, đạt đúng cự ly 1 đến 10km và tính toán chính xác lượng bụi mịn hít vào phổi."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create an algorithm highlight slide for "2-Leg Penalized Dijkstra OSM Clean Routing Engine". Title: "Proprietary 2-Leg Routing: 0% Retracing Closed-Loop". Visuals: Diagram showing Forward Leg (S->W) in solid green, 30x Penalty applied to used edges, and Backward Leg (W->S) in dashed blue around the lake. Metric callout: "0.0% Route Retracing | Integrated PM2.5 Inhaled Dose (ug)".
  ```

---

### 🤖 SLIDE 7: TRỢ LÝ AI GROUNDED & CỔNG CHỐNG ẢO GIÁC (AI SAFETY & GROUNDING)
* **Hình ảnh đính kèm**: `image/Luồng hội thoại của AI Agent & Grounding Policy Gate.png` (Trích xuất từ SRS Mục 5.4 & Mục 8).
* **Nội dung trên Slide**:
  * **LangGraph State Machine**: Điều phối hội thoại đa lượt, phân tích Intent, gọi Registry 8 Backend Tools.
  * **Cổng kiểm soát Grounding Policy Gate (Zero Hallucination)**:
    * 100% thông tin môi trường bắt buộc phải có chứng cứ từ kết quả Tool calling trong cùng request.
    * Tự động gắn nhãn minh bạch `source=simulator`.
  * **Bộ chuyển mạch tiền định (Deterministic Fallback Switcher)**:
    * Kích hoạt khi LLM Timeout ($> 8.0\text{s}$) hoặc mất mạng $\to$ Phản hồi cục bộ trong $< 500\text{ms}$, đảm bảo **0% lỗi HTTP 5xx**.

* **🗣️ Lời thoại người trình bày (45s)**:
  > *"Trong bài toán sức khỏe, AI không được phép ảo giác. Chúng tôi thiết lập nguyên tắc **'Grounding trước Fluency'**:  
  > Mọi phát ngôn của AI đều phải được thẩm định qua Cổng Grounding Gate đối chiếu trực tiếp từ Database. Nếu mạng ngoài bị nghẽn, bộ chuyển mạch tiền định sẽ kích hoạt trong nửa giây, trả về dữ liệu trạm đo chính xác mà không bao giờ gây lỗi sập hệ thống."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create an AI Safety slide. Title: "LangGraph AI Agent: Zero-Hallucination Grounding Policy Gate". Flowchart: User Message -> Router -> Tool Calling (8 Tools) -> Grounding Policy Gate (Fact Verification) -> Response Composer. Highlight box: "Deterministic Fallback Switcher (<500ms response if LLM timeouts >8s, 0% 5xx errors)". Clean emerald green safety shield visual.
  ```

---

### 🛡️ SLIDE 8: CỔNG PHÊ DUYỆT HITL & ĐIỀU KHIỂN THIẾT BỊ 0.8S (HITL & DEVICE CONTROL)
* **Hình ảnh đính kèm**: `image/Luồng cảnh báo tự động & HITL.png` kết hợp `image/Mockup 5 - HITL Approval Center.png`.
* **Nội dung trên Slide**:
  * **Cơ chế Cảnh Báo Cooldown 15 Phút**: Chỉ kích hoạt khi vượt ngưỡng liên tiếp 2 chu kỳ đo ($30\text{s}$), chống spam thông báo.
  * **Quy tắc HITL nghiêm ngặt**: AI **chỉ tạo đề xuất ở trạng thái Pending** kèm Thẻ bằng chứng (Evidence Card); chỉ Quản lý đô thị (Manager) có quyền Approve/Reject.
  * **Điều khiển thiết bị siêu tốc (Fast-Polling ACK 0.8s)**:
    * Quản lý bấm Bật máy lọc `FILTER-S01`..`S05` qua MQTT.
    * Phản hồi ACK xác nhận trạng thái tức thì trong **0.8 giây** với chu kỳ Fast-Polling $800\text{ms}$.
    * Tự động đếm ngược chu kỳ lọc tăng cường 45 phút công suất 80% và ngắt an toàn.

* **🗣️ Lời thoại người trình bày (50s)**:
  > *"Đối với các can thiệp vật lý ra môi trường, quyền quyết định tối hậu thuộc về con người.  
  > Khi phát hiện ô nhiễm kéo dài, AI chuẩn bị sẵn Thẻ bằng chứng quan trắc. Quản lý chỉ cần 1 cú nhấp chuột để phê duyệt, lệnh MQTT truyền tức thì đến máy lọc và giao diện cập nhật trạng thái chỉ trong **0.8 giây** kèm đồng hồ đếm ngược 45 phút."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create an HITL & IoT Device Control slide. Title: "Human-in-the-Loop Approval & 0.8s Fast-Polling Device Control". Left: Evidence Card (PM2.5, Weather, Forecast) with 1-Click Approve/Reject. Right: Real-time MQTT Device Command Dispatcher with 0.8s ACK Fast-Polling and 45-minute boost timer countdown. Dark UI with glowing green success badge.
  ```

---

### 💻 SLIDE 9: TRÌNH DIỄN GIAO DIỆN THỰC TẾ TRÊN AZURE CLOUD (LIVE DEMO SHOWCASE)
* **Hình ảnh đính kèm**: Ghép 3 ảnh giao diện thật:
  * `image/Mockup 1 - GIS Dashboard & Heatmap.png` (Bản đồ GIS)
  * `image/Mockup 2 - Station Detail Drawer.png` (Chi tiết trạm & Dự báo 1-24h)
  * `image/Mockup 3 - AI Chat & Clean Running Route.png` (Thẻ đường chạy 5km)
* **Nội dung trên Slide**:
  * **Trải nghiệm thực tế tại**: `https://airguard-074-app.indonesiacentral.cloudapp.azure.com`
  * 3 Luồng trải nghiệm mượt mà:
    1. Bản đồ GIS với 5 trạm đo chuẩn mã màu EPA và lớp phủ nhiệt IDW 60x60.
    2. Ngăn chi tiết trạm: Biểu đồ lịch sử 24h và khối dự báo vi khí hậu 1-24h.
    3. Trợ lý AI đàm thoại & Thẻ lộ trình chạy bộ xanh khép kín 5.0km.

* **🗣️ Lời thoại người trình bày (60s - Kết hợp mở tab demo live)**:
  > *"Kính mời quý hội đồng cùng nhìn lên màn hình giao diện thực tế đang chạy live trên đám mây Azure:  
  > Người dùng có thể quan sát bản đồ nhiệt IDW thời gian thực, mở ngăn chi tiết xem dự báo 24 giờ tới và yêu cầu Trợ lý AI gợi ý đường chạy 5km sạch bụi quanh hồ Ngọc Trai. Toàn bộ thao tác đều diễn ra mượt mà với độ trễ phản hồi dưới 120ms."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a Product UI Showcase slide with 3 high-fidelity screenshots. Title: "Live Production Dashboard on Azure Cloud VM". Showcase 1: Interactive GIS Heatmap Dashboard. Showcase 2: Station Metrics Drawer with 24h Recharts & 1-24h Forecast. Showcase 3: AI Chat Drawer with Clean Route Card. Floating glass frames on dark navy background.
  ```

---

### 📈 SLIDE 10: TÁC ĐỘNG KINH TẾ, XÃ HỘI & CHỈ SỐ ESG (BUSINESS IMPACT & ESG)
* **Hình ảnh đính kèm**: `image/Mockup 6 - Audit Log Center.png` (Nhật ký kiểm toán & Xuất báo cáo ESG).
* **Nội dung trên Slide (3 Trục tác động)**:
  * **Sức Khỏe Cư Dân**: Giảm **35% – 45%** khối lượng bụi mịn PM2.5 hít vào phổi khi vận động ngoài trời.
  * **Vận Hành Đô Thị**: Giảm **90%** thời gian phản ứng xử lý ô nhiễm; tiết kiệm năng lượng nhờ tự ngắt máy lọc sau 45 phút.
  * **Quản Trị Bền Vững ESG**: Bảng `audit_logs` Append-Only bất biến, tự động xuất báo cáo ca/ngày/tháng định dạng PDF/Excel phục vụ chứng chỉ đô thị xanh.

* **🗣️ Lời thoại người trình bày (35s)**:
  > *"AirGuard AI mang lại giá trị thiết thực: Giúp bảo vệ lá phổi cho hàng ngàn cư dân mỗi ngày, tối ưu hóa 90% thời gian xử lý sự cố của ban quản lý và cung cấp báo cáo ESG chuẩn mực, nâng tầm Vinhomes Ocean Park thành hình mẫu đô thị thông minh tiêu chuẩn quốc tế."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a Business Impact & ESG Metrics slide. Title: "Measurable Impact: Resident Health & Urban ESG Governance". 3 Big Metric Cards: Card 1: "-35% to -45% Inhaled PM2.5 Dose (Sports & Runners)". Card 2: "-90% Incident Response Time (0.8s ACK intervention)". Card 3: "100% Automated ESG Reporting (Append-Only Audit Trail)". Clean charts and sustainability badges.
  ```

---

### 🏆 SLIDE 11: ĐẢM BẢO CHẤT LƯỢNG KỸ THUẬT & HẠ TẦNG DEPLOY (QUALITY & DEPLOYMENT)
* **Hình ảnh đính kèm**: `image/Sơ đồ triển khai hạ tầng.png` (Trích xuất từ ARCHITECTURE.md Mục 4.1).
* **Nội dung trên Slide**:
  * **153 / 153 Automated Test Cases Passed (100% PASS)**: Bao phủ Unit tests, API Contract, Routing Algorithm, AI Safety, HITL RBAC.
  * **Hiệu năng thực tế**:
    * Độ trễ API: $< 120\text{ms}$ (Vượt chuẩn $< 200\text{ms}$).
    * Độ trễ phản hồi thiết bị: $0.8\text{s}$ (Vượt chuẩn $< 1.5\text{s}$).
    * Uptime SLA: $99.9\%$ trên Azure VM B2ms.
  * **Đóng gói Docker Compose 8 Containers**: Caddy Reverse Proxy, Frontend, Backend, Agent, Consumer, 3 Simulators, PostgreSQL.

* **🗣️ Lời thoại người trình bày (35s)**:
  > *"Về chất lượng kỹ thuật, sản phẩm của chúng tôi đã vượt qua **153/153 kịch bản kiểm thử tự động**, đạt độ trễ API dưới 120ms và vận hành ổn định trên hạ tầng đám mây Azure VM với cấu hình 8 container cô lập, bảo mật tối đa."*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a Quality Engineering & Deployment Topology slide. Title: "153/153 Tests Passed (100%) & Azure Cloud Deployment". Left: Test coverage badges (153 Automated Tests, <120ms API latency, 0.8s ACK, 99.9% SLA). Right: Infrastructure deployment topology showing 8 Docker containers behind Caddy HTTPS Reverse Proxy on Azure VM B2ms.
  ```

---

### 👥 SLIDE 12: ĐỘI NGŨ THỰC HIỆN & KẾT LUẬN Q&A (TEAM & CLOSING)
* **Hình ảnh đính kèm**: Thẻ ảnh 4 thành viên nhóm P-074 và Mã QR truy cập Web Demo.
* **Nội dung trên Slide**:
  * **Đội ngũ P-074 (Tứ Kỵ Sĩ Khải Huyền)**:
    1. **Lê Tuấn Cảnh** — *Team Lead / Backend & Data / IoT* (Architecture, FastAPI, Postgres SoR, Azure VM).
    2. **Hán Vũ Long** — *Integration / AI Engineer* (MQTT Broker, Consumer, Forecast Service).
    3. **Hoàng Lê Minh** — *AI Engineer* (LangGraph AI Agent, Grounding Policy Gate).
    4. **Phạm Thế Dũng** — *Frontend / QA Engineer* (React 18 Leaflet GIS, Test Suite 153 Tests).
  * **Kênh kết nối**: `https://airguard-074-app.indonesiacentral.cloudapp.azure.com`
  * **Thông điệp kết**: *"AirGuard AI — Vì Một Đại Đô Thị Xanh, Thông Minh & Khỏe Mạnh!"*

* **🗣️ Lời thoại người trình bày (30s)**:
  > *"Xin chân thành cảm ơn quý Ban giám khảo, các Mentor và toàn thể hội đồng đã lắng nghe bài thuyết trình của nhóm P-074!  
  > **Toàn đội chúng tôi rất sẵn sàng lắng nghe các câu hỏi và nhận xét đóng góp từ Hội đồng!**"*

* **🤖 Prompt cho AI Slide**:
  ```text
  Create a Team & Q&A Closing slide. Title: "Team P-074 & Q&A Session". Showcase 4 team member cards: Le Tuan Canh (Team Lead / Backend), Han Vu Long (Integration / AI), Hoang Le Minh (AI Engineer), Pham The Dung (Frontend / QA). Center QR code linking to live Azure demo: "https://airguard-074-app.indonesiacentral.cloudapp.azure.com". Slogan: "AirGuard AI - For a Cleaner, Healthier Smart City".
  ```

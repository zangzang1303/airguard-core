# 🎤 KỊCH BẢN PITCHING AIRGUARD AI (P-074) — 8 SLIDE TOÀN DIỆN
> **BỔ SUNG 2 SLIDE KỸ THUẬT CHUYÊN SÂU THEO YÊU CẦU**:
> 1. `Slide 4`: **Kiến Trúc Hệ Thống, Các Luồng Dữ Liệu & Công Nghệ Sử Dụng (Architecture, Flows & Tech Stack)**
> 2. `Slide 5`: **Các Kỹ Thuật Đột Phá & Kỹ Thuật Chính Đã Áp Dụng (Core Technical Innovations & Algorithmic Highlights)**  
> 
> **Mạch logic hoàn chỉnh**: `1. Hook` $\to$ `2. Problem` $\to$ `3. Solution` $\to$ `4. Architecture & Flows` $\to$ `5. Core Innovations` $\to$ `6. Live Demo` $\to$ `7. Biz & Traction` $\to$ `8. Vision & Ask`

---

## 🗺️ MA TRẬN 8 SLIDE PITCHING CHUẨN MỰC

| STT | Slide | Tiêu đề Slide | Thời lượng | Trọng tâm nội dung & Công nghệ |
|:---:|---|---|:---:|---|
| **1** | Slide 1 | **HOOK (Mở đầu)** | 0:00 – 0:30 *(30s)* | Nghịch lý chạy bộ hít bụi độc & Giới thiệu **AirGuard AI** |
| **2** | Slide 2 | **PROBLEM (Thực trạng)** | 0:30 – 1:10 *(40s)* | 3 Nỗi đau: Dữ liệu rời rạc, chênh lệch AQI 35 vs 150+, BQL bị động |
| **3** | Slide 3 | **SOLUTION (Tổng quan)** | 1:10 – 1:45 *(35s)* | Chu trình khép kín 2 Roles & 10 Use Cases từ Quan trắc $\to$ Can thiệp |
| **4** | **Slide 4** | **🏗️ KIẾN TRÚC & LUỒNG DỮ LIỆU** | **1:45 – 2:25** *(40s)* | **[MỚI]**: Monorepo 5 Lớp, Chi tiết các luồng Ingestion/Action & Toàn bộ Tech Stack |
| **5** | **Slide 5** | **⚡ KỸ THUẬT ĐỘT PHÁ CỐT LÕI** | **2:25 – 3:05** *(40s)* | **[MỚI]**: 2-Leg OSM Dijkstra (0% lặp), Grounding Gate (Zero Hallucination), IDW Heatmap, HITL 0.8s |
| **6** | Slide 6 | **LIVE PRODUCT DEMO** | 3:05 – 3:55 *(50s)* | **Slide chuyển cảnh Demo tĩnh**: Dành trọn thời gian để bạn tự do thao tác Web Live |
| **7** | Slide 7 | **BIZ, IMPACT & TRACTION** | 3:55 – 4:35 *(40s)* | -45% bụi hít, 153/153 Tests Passed (100%), Báo cáo ESG, Mô hình B2B/B2G |
| **8** | Slide 8 | **VISION, TEAM & THE ASK** | 4:35 – 5:00 *(25s)* | Đội ngũ Tứ Kỵ Sĩ P-074, Lộ trình LoRaWAN/GNN $\to$ Kêu gọi & Mở màn Q&A |

---

## 🎯 TOÀN VĂN KỊCH BẢN NÓI CHI TIẾT 2 SLIDE KỸ THUẬT MỚI & CÂU CẦU NỐI

---

### 🟢 SLIDE 1: HOOK (0:00 – 0:30 | 30 GIÂY)
* **Visual trên Slide**: Logo AirGuard AI, bản đồ GIS Ocean Park 1, badge `153/153 Tests Passed (100%)` | `Live on Azure Cloud`.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"Kính chào quý Ban giám khảo, các Mentor và toàn thể hội đồng!  
> 
> Cho phép tôi được bắt đầu bằng một nghịch lý: **Tại sao hàng chục ngàn cư dân chạy bộ để rèn luyện sức khỏe tại các đại đô thị hiện đại lại đang vô tình hít phải hàng chục microgram bụi mịn độc hại vào sâu phế nang mỗi ngày?** `[Dừng 1 giây]`  
> 
> Chúng tôi là **Nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền**.  
> Và câu trả lời của chúng tôi chính là **AirGuard AI** — Hệ sinh thái AI Agent toàn diện: từ giám sát vi khí hậu thời gian thực, tự động vẽ lộ trình thể thao sạch bụi khép kín, đến liên động điều khiển thiết bị dập bụi thông minh tại Vinhomes Ocean Park 1!"*

🔗 **Câu chuyển tiếp sang Slide 2**:  
> *"Nhưng để hiểu tại sao cư dân lại rơi vào nghịch lý đó, chúng ta hãy cùng nhìn vào **thực trạng dữ liệu môi trường tại các đại đô thị hiện nay**..."*

---

### 🔴 SLIDE 2: PROBLEM — THỰC TRẠNG & NỖI ĐAU ĐÔ THỊ (0:30 – 1:10 | 40 GIÂY)
* **Visual trên Slide**: 3 Thẻ cảnh báo: Ai đau (40,000+ Cư dân & Runner); Đau ở đâu (Chênh lệch AQI Biển Hồ 35 vs Sao Biển 150+); Hậu quả (Hít bụi độc, BQL bị động).

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"Thưa quý vị, các khu đô thị hiện nay dù đã lắp đặt cảm biến, nhưng **dữ liệu hoàn toàn rời rạc**. `[Nhấn mạnh]`  
> 
> Tại Vinhomes Ocean Park 1, chất lượng không khí biến thiên siêu cục bộ: Cùng một thời điểm, mặt nước Biển Hồ 6.1 ha có chỉ số AQI rất tốt — chỉ **35**, nhưng chỉ cách đó vài trăm mét, trục đường thi công Sao Biển nồng độ PM2.5 lại tăng vọt lên mức Nguy hại — **AQI trên 150**!  
> 
> **Thực trạng này dẫn đến 3 hậu quả nghiêm trọng**:  
> 1. **Người tập thể dục**: Hoàn toàn mù mờ thông tin, vô tình biến buổi chạy bộ thành buổi 'hít bụi mịn'.  
> 2. **Trẻ em, người cao tuổi, người bệnh hô hấp**: Không hề có cảnh báo sớm cá nhân hóa theo thể trạng.  
> 3. **Ban Quản Lý đô thị**: Hoàn toàn bị động trước các bảng báo cáo thủ công, không thể phát hiện và liên động xử lý ô nhiễm kịp thời."*

🔗 **Câu chuyển tiếp sang Slide 3**:  
> *"Đứng trước 3 nỗi đau đó, chúng tôi đã xây dựng một **hệ sinh thái khép kín từ cảm biến đến hành động**..."*

---

### 💡 SLIDE 3: SOLUTION — TỔNG QUAN GIẢI PHÁP & 10 USE CASES (1:10 – 1:45 | 35 GIÂY)
* **Visual trên Slide**: Sơ đồ 2 Vai trò người dùng (Cư dân & Ban Quản Lý) cùng 10 Ca sử dụng chuẩn hóa.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"AirGuard AI giải quyết bài toán trên bằng cấu trúc phân quyền rõ rệt và 10 ca sử dụng chuẩn hóa:  
> 
> * **Với Cư dân**: Cung cấp Dashboard bản đồ nhiệt AQI thời gian thực, chi tiết trạm và dự báo 1-24h, thiết lập hồ sơ sức khỏe 3 nhóm đối tượng, và **đàm thoại cùng AI Agent để nhận lộ trình chạy bộ sạch bụi khép kín**.  
> * **Với Ban Quản Lý**: Cung cấp Cổng phê duyệt HITL 1-click thẩm định chứng cứ, điều khiển máy lọc không khí phản hồi tức thì và tự động xuất báo cáo ESG định kỳ."*

🔗 **Câu chuyển tiếp sang Slide 4 (Kiến trúc & Luồng dữ liệu)**:  
> *"Để hiện thực hóa một hệ sinh thái mạnh mẽ như vậy, **chúng tôi đã thiết kế một kiến trúc Monorepo 5 phân tầng công nghiệp với các luồng dữ liệu cực kỳ chặt chẽ**..."*

---

### 🏗️ SLIDE 4: KIẾN TRÚC HỆ THỐNG: 3 LUỒNG DỮ LIỆU KHÉP KÍN & TECH STACK (1:45 – 2:25 | 40 GIÂY)
* **Visual trên Slide (Sơ đồ 3 chuỗi mũi tên luồng đi cực kỳ trực quan)**:
  * **➔ LUỒNG 1: THU THẬP TELEMETRY REALTIME (15s)**:  
    `[ 5 Trạm Đo IoT ]` ➔ `[ Mosquitto MQTT ]` ➔ `[ Data Quality Gate ]` ➔ `[ PostgreSQL 16 SoR ]`
  * **➔ LUỒNG 2: TRUY VẤN BẢN ĐỒ & AI ĐỊNH TUYẾN (< 120ms)**:  
    `[ Cư Dân / Runner ]` ➔ `[ React 18 Leaflet GIS ]` ➔ `[ FastAPI Backend ]` ➔ `[ LangGraph + 2-Leg OSM Router ]`
  * **➔ LUỒNG 3: CẢNH BÁO & ĐIỀU KHIỂN THIẾT BỊ HITL (0.8s ACK)**:  
    `[ Ô Nhiễm Vượt Ngưỡng ]` ➔ `[ Cổng HITL (BQL Duyệt 1-Click) ]` ➔ `[ Lệnh MQTT ]` ➔ `[ Bật Máy Lọc 45 Phút ]`
  * **Thanh Tech Stack Tinh Gọn Dưới Cùng**:  
    `[MQTT Mosquitto]` • `[PostgreSQL 16]` • `[FastAPI & Celery]` • `[LangGraph Agent]` • `[React 18 Leaflet]` • `[Docker & Caddy]`

> 🗣️ **Lời thoại người trình bày (Integration / Lead - Hán Vũ Long / Lê Tuấn Cảnh)**:  
> *"Về mặt kiến trúc, AirGuard AI được xây dựng theo mô hình Monorepo 5 phân tầng hoàn chỉnh với các luồng dữ liệu khép kín:  
> 
> * **Luồng 1 — Telemetry Stream**: Mỗi 15 giây, 5 trạm quan trắc đẩy dữ liệu 4 chỉ số (PM2.5, CO2, ồn, nhiệt độ) qua **Mosquitto MQTT Broker**. Tầng Ingestion áp dụng **Data Quality Gate** với cơ chế Fail-Closed: tự động loại bỏ dữ liệu sai lệch hoặc trạm mất tín hiệu quá 300 giây trước khi ghi vào **PostgreSQL 16 SoR**.  
> * **Luồng 2 — Query & Geospatial Stream**: Frontend **React 18** và **Leaflet GIS** giao tiếp với **FastAPI Backend** qua REST API chuẩn OpenAPI, tính toán bản đồ nhiệt IDW và truy xuất dự báo với độ trễ phản hồi **dưới 120ms**.  
> * **Luồng 3 — Control & Audit Stream**: Lệnh điều khiển máy lọc từ Cổng HITL được đẩy qua MQTT và cập nhật trạng thái trên giao diện theo cơ chế Fast-Polling 800ms, đồng thời ghi vết kiểm toán bất biến vào bảng `audit_logs`.  
> * Toàn bộ hệ thống được đóng gói trong **8 Docker containers cô lập** và bảo mật HTTPS qua Caddy Proxy."*

🔗 **Câu chuyển tiếp sang Slide 5 (Kỹ thuật đột phá)**:  
> *"Không chỉ có một bộ khung kiến trúc vững chắc, **điều làm nên sự khác biệt vượt trội của AirGuard AI nằm ở 4 kỹ thuật đột phá cốt lõi**..."*

---

### ⚡ SLIDE 5: CÁC KỸ THUẬT ĐỘT PHÁ & KỸ THUẬT CHÍNH ĐÃ ÁP DỤNG (2:25 – 3:05 | 40 GIÂY)
* **Visual trên Slide**: Bố cục Lưới 4 Ô Kỹ Thuật Đột Phá (4 Core Innovations Grid):
  1. **Thuật toán 2-Leg Penalized Dijkstra OSM (>10,500 cạnh)**: Phạt 30x chiều về $\to$ Đường chạy tuần hoàn **0.0% trùng lặp**, tích phân liều lượng bụi mịn hít vào ($\mu g$).
  2. **Cơ chế Chống Ảo Giác "Grounding trước Fluency"**: LangGraph Agent + **Grounding Policy Gate** (100% số liệu đối chiếu DB SoR) + **Deterministic Fallback Switcher** (<500ms khi LLM timeout >8s $\to$ 0% lỗi 5xx).
  3. **Nội suy phân bố ô nhiễm không gian IDW (60x60 Grid)**: Inverse Distance Weighting kết hợp vector hướng gió Open-Meteo và chuẩn mã màu US EPA 2012.
  4. **Cổng An Toàn HITL Server-Side & Fast-Polling ACK 0.8s**: Cooldown Gate 15 phút, duyệt lệnh 1-click, đếm ngược 45 phút công suất 80% và tự ngắt an toàn.

> 🗣️ **Lời thoại người trình bày (AI Engineer - Hoàng Lê Minh)**:  
> *"Hệ thống khẳng định năng lực kỹ thuật thông qua **4 công nghệ đột phá cốt lõi**:  
> 
> * **1. Động cơ định tuyến thể thao 2-Leg Penalized Dijkstra trên đồ thị đường thực OSM**: Khác với các thuật toán thông thường bắt runner quay đầu chạy lùi đường cũ, thuật toán của chúng tôi phạt 30 lần trọng số chiều về, sinh ra cung đường thể thao khép kín tuần hoàn **đúng 0.0% trùng lặp** và **giảm 45% lượng bụi hít vào**!  
> * **2. Cơ chế AI Grounded Zero-Hallucination**: Áp dụng nguyên tắc 'Grounding trước Fluency' — 100% câu trả lời có số liệu vi khí hậu bắt buộc phải đối chiếu từ DB. Nếu LLM ngoài bị nghẽn mạng quá 8 giây, bộ chuyển mạch tiền định sẽ kích hoạt trong 500ms, đảm bảo **0% lỗi HTTP 5xx**.  
> * **3. Lớp phủ nhiệt IDW ma trận 60x60**: Tính toán phân bố lan truyền ô nhiễm kết hợp hướng gió thời gian thực.  
> * **4. Cổng an toàn HITL máy chủ**: Tự động lọc cảnh báo nhiễu với Cooldown 15 phút, và điều khiển máy lọc không khí nhận phản hồi ACK siêu tốc trong **0.8 giây**!"*

🔗 **Câu chuyển tiếp sang Slide 6 (Live Demo)**:  
> *"Và để chứng minh toàn bộ kiến trúc và các kỹ thuật đột phá này vận hành mượt mà như thế nào trong thực tế, **ngay sau đây, kính mời quý Hội đồng cùng tôi trải nghiệm trực tiếp trên hệ thống đang chạy live trên Azure Cloud**..."*

---

### 💻 SLIDE 6: LIVE PRODUCT DEMO — TRẢI NGHIỆM THỰC TẾ (3:05 – 3:55 | 50 GIÂY)
* **Visual trên Slide**: Slide tĩnh hiển thị Live URL `https://airguard-074-app.indonesiacentral.cloudapp.azure.com` và 3 bước trải nghiệm.

> 🗣️ **Lời thoại người trình bày (Thao tác trực tiếp trên Web Live — 50 giây)**:  
> *(Người trình bày chuyển nhanh sang tab trình duyệt)*  
> 
> *"Kính mời quý Hội đồng cùng nhìn lên màn hình:  
> 
> 1. **Ở vai trò Cư dân**: Bản đồ nhiệt IDW thời gian thực làm nổi bật ngay hành lang không khí trong lành quanh hồ Ngọc Trai.  
> 2. **Bây giờ tôi mở Trợ lý AI và chat**: *'Gợi ý đường chạy 5km quanh hồ cho người nhạy cảm'*. `[Thao tác click]` Chỉ sau 1 giây, AI gọi động cơ 2-Leg Dijkstra, lập tức vẽ đường chạy Polyline màu xanh tuyệt đẹp ôm trọn mặt hồ, xác nhận độ trùng lặp đường cũ là **0%** và lượng bụi hít vào chỉ **4.8 microgram**!  
> 3. **Chuyển sang vai trò Ban Quản Lý**: Khi trạm Sao Biển bị ô nhiễm, tôi mở Cổng HITL, kiểm tra Thẻ bằng chứng quan trắc và bấm **[Phê duyệt]**. `[Thao tác click]` Lập tức lệnh MQTT truyền đi, trạng thái chuyển sang xanh và đồng hồ 45 phút đếm ngược chỉ trong **0.8 giây**!"*

🔗 **Câu chuyển tiếp sang Slide 7**:  
> *"Một nền tảng công nghệ hoàn thiện như vậy mang lại **những giá trị định lượng và tiềm năng kinh doanh cụ thể nào**? Hãy cùng xem ở slide tiếp theo..."*

---

### 📈 SLIDE 7: BIZ, IMPACT & TRACTION (3:55 – 4:35 | 40 GIÂY)
* **Visual trên Slide**: 3 Hộp số liệu lớn: `-45% Bụi hít vào`, `-90% Thời gian xử lý`, `153/153 Tests Passed (100%)` + Mô hình B2B/B2G SaaS.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"AirGuard AI mang lại **3 giá trị định lượng thiết thực đã được chứng minh bằng số liệu khoa học**:  
> 
> * **1. Tác động Sức khỏe & Vận hành**: Giúp người tập thể thao giảm **35% đến 45%** liều lượng PM2.5 hít vào phổi; rút ngắn **90%** thời gian phản ứng xử lý ô nhiễm và tự động hóa 100% báo cáo ESG.  
> * **2. Độ Tin Cậy & Hoàn Thiện Kỹ Thuật**: Dự án đã vượt qua **153 trên 153 kịch bản kiểm thử tự động**, đạt độ trễ API dưới **120ms** và duy trì Uptime **99.9%** trên đám mây Azure.  
> * **3. Mô hình Kinh doanh**: Triển khai mô hình **B2B/B2G SaaS** thu phí quản trị môi trường từ Ban Quản Lý đại đô thị ($2,000 – $5,000/tháng/khu đô thị), kết hợp gói **B2C Premium** dành riêng cho hàng ngàn runner."*

🔗 **Câu chuyển tiếp sang Slide 8**:  
> *"Để hiện thực hóa tiềm năng to lớn đó, ai là những người đứng sau dự án và **tầm nhìn tương lai của chúng tôi là gì**?..."*

---

### 🚀 SLIDE 8: VISION, TEAM & THE ASK (4:35 – 5:00 | 25 GIÂY)
* **Visual trên Slide**: Thẻ 4 thành viên nhóm P-074 (Tứ Kỵ Sĩ Khải Huyền), Lộ trình phần cứng LoRaWAN & GNN, Mã QR Web Live.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"Thành quả ngày hôm nay là sự kết tinh từ sự phối hợp kỷ luật của 4 thành viên nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền: từ thiết kế kiến trúc, xây dựng pipeline IoT, phát triển AI Agent định tuyến cho đến kiểm thử tự động 153 test cases.  
> 
> Trong giai đoạn tới, chúng tôi sẽ tích hợp phần cứng cảm biến LoRaWAN thực địa, nâng cấp mô hình AI đồ thị GNN và sẵn sàng nhân rộng ra toàn bộ hệ thống đại đô thị thông minh tại Việt Nam.  
> 
> **Chúng tôi rất mong muốn nhận được sự đồng hành, cố vấn từ Ban giám khảo và các nhà đầu tư!**  
> 
> Xin chân thành cảm ơn quý Hội đồng! **Toàn đội chúng tôi rất sẵn sàng cho phiên Q&A!**"*

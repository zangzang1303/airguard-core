# 🎤 KỊCH BẢN THUYẾT TRÌNH PITCHING AIRGUARD AI (NHÓM P-074)
> **CHUẨN HÓA TOÀN DIỆN TỪ AIRGUARD AI MASTER BRIEFING HANDBOOK**  
> **Cấu trúc:** 9 Slide Hoàn Chỉnh — Thời lượng chuẩn xác 5 phút (300 giây)  
> **Dự án:** AirGuard AI — Hệ Sinh Thái AI Agent Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh  
> **Đơn vị:** AI20K Build Phase Cohort 3 (Gate 2 Final Pitching)  
> **Đội ngũ:** Nhóm P-074 / Tứ Kỵ Sĩ Khải Huyền (Lê Tuấn Cảnh, Hán Vũ Long, Hoàng Lê Minh, Phạm Thế Dũng)  
> **Địa bàn thực nghiệm:** Đại đô thị Vinhomes Ocean Park 1 (Gia Lâm, Hà Nội)  
> **Hạ tầng Live Production:** `https://airguard-074-app.indonesiacentral.cloudapp.azure.com`

---

## ⏱️ MA TRẬN 9 SLIDE PHÂN BỔ NGUỒN LỰC CHÚ Ý (TỔNG: 5 PHÚT / 300 GIÂY)

```
0:00        0:30          1:10          1:45           2:25           3:05          3:55           4:35     4:50    5:00
 |---30s-----|----40s------|----35s------|-----40s------|-----40s------|-----50s-----|-----40s------|--15s---|--10s---|
 [ S1: HOOK  ] [S2:PROBLEM ] [S3:SOLUTION] [S4: ARCH/FLOW] [S5: INNOVATE] [ S6: DEMO   ] [ S7: METRICS  ] [S8:TEAM][S9: Q&A ]
```

| STT | Slide | Tiêu đề Slide | Thời lượng | Trọng tâm nội dung & Hành động thuyết trình |
|:---:|---|---|:---:|---|
| **1** | Slide 1 | **HOOK (Mở đầu ấn tượng)** | 0:00 – 0:30 *(30s)* | Nghịch lý chạy bộ hít bụi mịn & Giới thiệu AirGuard AI |
| **2** | Slide 2 | **PROBLEM (Thực trạng & Nỗi đau)** | 0:30 – 1:10 *(40s)* | Cảm biến rời rạc, vi khí hậu biến thiên siêu cục bộ (AQI 35 vs 155), 3 nỗi đau |
| **3** | Slide 3 | **SOLUTION (Tổng quan giải pháp)** | 1:10 – 1:45 *(35s)* | Chu trình khép kín 2 Không gian làm việc (Cư dân & BQL) cùng 10 Use Cases |
| **4** | Slide 4 | **KIẾN TRÚC & 3 LUỒNG DỮ LIỆU** | 1:45 – 2:25 *(40s)* | Monorepo 5 lớp & 3 Chuỗi mũi tên luồng dữ liệu (Telemetry, AI Query, HITL Action) |
| **5** | Slide 5 | **KỸ THUẬT ĐỘT PHÁ CỐT LÕI** | 2:25 – 3:05 *(40s)* | 2-Leg OSM Dijkstra (0% lặp), Grounding Gate (Zero Hallucination), IDW 60x60, HITL 0.8s |
| **6** | Slide 6 | **LIVE PRODUCT DEMO** | 3:05 – 3:55 *(50s)* | Slide chuyển cảnh: Trực tiếp thao tác Web Live trên đám mây Azure |
| **7** | Slide 7 | **TÁC ĐỘNG & 3 CHỈ SỐ VÀNG** | 3:55 – 4:35 *(40s)* | **3 Chỉ số vàng**: 0% Lặp/-45% Bụi, Giảm 90% TG/0.8s, Tiết kiệm 35% Điện/ESG |
| **8** | Slide 8 | **ĐỘI NGŨ THỰC HIỆN (P-074)** | 4:35 – 4:50 *(15s)* | 4 Thành viên nòng cốt nhóm P-074 (Tứ Kỵ Sĩ) với các vai trò chuyên biệt |
| **9** | Slide 9 | **LỘ TRÌNH TƯƠNG LAI & Q&A** | 4:50 – 5:00 *(10s)* | Lộ trình Cư dân (Mobile App/Zalo Mini App, Smart Home, Chạy Xanh), Mã QR & Q&A |

---

## 🎯 TOÀN VĂN KỊCH BẢN THUYẾT TRÌNH CHI TIẾT TỪNG SLIDE (WORD-FOR-WORD SCRIPT)

---

### 🟢 SLIDE 1: HOOK — MỞ ĐẦU ẤN TƯỢNG (0:00 – 0:30 | 30 GIÂY)
* **Mục tiêu tâm lý**: Gây tò mò, chỉ ra nghịch lý sức khỏe đô thị nhức nhối, kéo trọn vẹn sự chú ý của Ban Giám Khảo ngay từ giây đầu tiên.
* **Visual trên Slide**:
  * Logo AirGuard AI hiện đại phong cách Clean-Tech Dark Mode (#0B1120) phát sáng xanh lục bảo (#10B981) và xanh dương (#0EA5E9).
  * Tagline: *"Hệ Sinh Thái AI Agent Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh"*.
  * Các huy hiệu chất lượng: `153/153 Tests Passed (100%)` • `Live on Azure Cloud VM` • `Zero-Hallucination AI`.
  * Đơn vị thực hiện: `Nhóm P-074 / Tứ Kỵ Sĩ Khải Huyền (AI20K Build Phase Cohort 3)`.

> 🗣️ **Lời thoại thuyết trình (Lead - Lê Tuấn Cảnh)**:  
> *"Kính chào quý Ban giám khảo, các Mentor và toàn thể Hội đồng!  
> 
> Cho phép tôi được bắt đầu bằng một nghịch lý thực tế: **Tại sao hàng chục ngàn cư dân chạy bộ để nâng cao sức khỏe tại các đại đô thị hiện đại lại đang vô tình hít phải hàng chục microgram bụi mịn độc hại vào sâu phế nang mỗi ngày?** `[Dừng 1 giây để tạo điểm nhấn]`  
> 
> Chúng tôi là **Nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền**.  
> Và câu trả lời của chúng tôi chính là **AirGuard AI** — Hệ sinh thái AI Agent toàn diện: từ giám sát vi khí hậu thời gian thực, tự động vẽ lộ trình thể thao sạch bụi khép kín, đến liên động điều khiển hệ thống dập bụi thông minh tại đại đô thị Vinhomes Ocean Park 1!"*

🔗 **Câu chuyển tiếp sang Slide 2**:  
> *"Nhưng để hiểu tại sao cư dân lại rơi vào nghịch lý sức khỏe đó, chúng ta hãy cùng nhìn vào **thực trạng dữ liệu môi trường tại các đại đô thị hiện nay**..."*

---

### 🔴 SLIDE 2: PROBLEM — THỰC TRẠNG & NỖI ĐAU ĐÔ THỊ (0:30 – 1:10 | 40 GIÂY)
* **Mục tiêu tâm lý**: Thấu hiểu sâu sắc nỗi đau thực tế và sự cấp thiết của giải pháp thông qua số liệu thực chứng tại địa bàn thực nghiệm.
* **Visual trên Slide**: Bố cục 3 Thẻ Nỗi Đau (3 Problem Cards):
  1. **Ai Đau?**: 40,000+ Cư dân, Người tập thể thao (Runner) và Nhóm nhạy cảm (trẻ em, người cao tuổi, bệnh nhân hen suyễn).
  2. **Đau Ở Đâu?**: Ô nhiễm biến thiên siêu cục bộ tại Ocean Park 1 (Mặt Biển Hồ 6.1ha AQI 35 - Tốt vs Trục đường thi công Sao Biển AQI 155 - Nguy hại, chỉ cách nhau 300m).
  3. **Hậu Quả Là Gì?**: Runner chạy nhầm vào điểm nóng tự đầu độc hệ hô hấp; Ban Quản Lý (BQL) bị động xử lý thủ công mất 20–30 phút/sự vụ bằng Excel.

> 🗣️ **Lời thoại thuyết trình (Lead - Lê Tuấn Cảnh)**:  
> *"Thưa quý vị, các khu đô thị hiện nay dù đã lắp đặt cảm biến, nhưng **dữ liệu hoàn toàn rời rạc**. `[Nhấn mạnh]`  
> 
> Tại Vinhomes Ocean Park 1, chất lượng không khí biến thiên siêu cục bộ: Cùng một thời điểm, mặt nước Biển Hồ có chỉ số rất trong lành — **AQI chỉ 35**, nhưng chỉ cách đó 300 mét, trục đường thi công Sao Biển nồng độ bụi PM2.5 lại tăng vọt lên mức Nguy hại — **AQI 155** do xe tải và đất cát thi công!  
> 
> **Thực trạng này dẫn đến 3 nỗi đau nhức nhối**:  
> 1. **Người tập thể thao**: Mù mờ thông tin vi khí hậu, vô tình biến buổi rèn luyện sức khỏe thành buổi 'hít bụi mịn độc hại'.  
> 2. **Trẻ em, người cao tuổi, người bệnh hô hấp**: Hoàn toàn thiếu các cảnh báo sớm và khuyến nghị bảo vệ cá nhân hóa theo thể trạng.  
> 3. **Ban Quản Lý đô thị**: Lúng túng với các bảng báo cáo Excel thủ công, mất 20 đến 30 phút cho mỗi sự vụ ô nhiễm và hoàn toàn bị động trong việc kích hoạt hệ thống dập bụi."*

🔗 **Câu chuyển tiếp sang Slide 3**:  
> *"Đứng trước 3 nỗi đau đó, chúng tôi không chỉ tạo ra một bảng điều khiển số liệu thông thường, mà đã xây dựng một **hệ sinh thái hành động khép kín từ cảm biến đến can thiệp thực tế**..."*

---

### 💡 SLIDE 3: SOLUTION — TỔNG QUAN GIẢI PHÁP & 10 USE CASES (1:10 – 1:45 | 35 GIÂY)
* **Mục tiêu tâm lý**: Thấy rõ bức tranh giải pháp hoàn chỉnh, cấu trúc phân quyền 2 vai trò chặt chẽ và phủ kín toàn bộ yêu cầu của đề bài.
* **Visual trên Slide**: Bố cục 2 Phân Hệ Người Dùng & 10 Ca Sử Dụng Chuẩn Hóa (10 Use Cases):
  * **Cư Dân (Resident Workspace)**: Bản đồ GIS & Heatmap IDW (UC-01), Chi tiết trạm & Dự báo 24h (UC-02), Hồ sơ sức khỏe 3 nhóm thể trạng (UC-03), Trợ lý AI Agent đàm thoại (UC-04), **Đột phá: Định tuyến chạy bộ sạch OSM (UC-05)**.
  * **Ban Quản Lý (Manager Workspace)**: Cổng duyệt đề xuất HITL (UC-06), Điều khiển máy lọc phản hồi 0.8s (UC-07), Quản trị ngưỡng & Cooldown 15m (UC-08), Nhật ký kiểm toán bất biến (UC-09), Tự động xuất báo cáo ESG (UC-10).

> 🗣️ **Lời thoại thuyết trình (Lead - Lê Tuấn Cảnh)**:  
> *"AirGuard AI giải quyết triệt để bài toán trên bằng cấu trúc 2 không gian làm việc chuyên biệt và 10 ca sử dụng khép kín:  
> 
> * **Với Cư dân**: Cung cấp Bản đồ nhiệt vi khí hậu thời gian thực, dự báo xu hướng ô nhiễm chuỗi 1 đến 24 giờ, thiết lập hồ sơ sức khỏe cá nhân hóa, và đặc biệt là **Trợ lý AI đàm thoại tự động vẽ tuyến đường chạy bộ sạch bụi khép kín quanh hồ**.  
> * **Với Ban Quản Lý**: Cung cấp Cổng phê duyệt HITL 1-click thẩm định Thẻ bằng chứng quan trắc, điều khiển máy lọc không khí dập bụi phản hồi tức thì, và tự động hóa 100% báo cáo kiểm toán môi trường đạt chuẩn quốc tế."*

🔗 **Câu chuyển tiếp sang Slide 4 (Kiến trúc & Luồng dữ liệu)**:  
> *"Để hiện thực hóa một hệ sinh thái mạnh mẽ như vậy, **đằng sau đó là một nền tảng kiến trúc Monorepo 5 phân tầng với 3 luồng dữ liệu cực kỳ chặt chẽ**..."*

---

### 🏗️ SLIDE 4: KIẾN TRÚC HỆ THỐNG: 3 LUỒNG DỮ LIỆU KHÉP KÍN & TECH STACK (1:45 – 2:25 | 40 GIÂY)
* **Mục tiêu tâm lý**: Khẳng định chiều sâu kỹ thuật phần mềm chuẩn doanh nghiệp, trực quan dễ nắm bắt thông qua các chuỗi mũi tên luồng đi.
* **Visual trên Slide**: Sơ đồ 3 Chuỗi Mũi Tên Luồng Dữ Liệu Trực Quan (3 Arrow Flow Pipelines):
  * **➔ LUỒNG 1: THU THẬP TELEMETRY REALTIME (Mỗi 15s)**:  
    `[ 5 Trạm Đo IoT ]` ➔ `[ Mosquitto MQTT ]` ➔ `[ Data Quality Gate (Lọc Stale) ]` ➔ `[ PostgreSQL 16 SoR ]`
  * **➔ LUỒNG 2: TRUY VẤN BẢN ĐỒ & AI ĐỊNH TUYẾN (< 120ms)**:  
    `[ Cư Dân / Runner ]` ➔ `[ React 18 Leaflet GIS ]` ➔ `[ FastAPI Core Backend ]` ➔ `[ LangGraph + 2-Leg OSM Router ]`
  * **➔ LUỒNG 3: CẢNH BÁO & ĐIỀU KHIỂN THIẾT BỊ HITL (0.8s ACK)**:  
    `[ Ô Nhiễm Vượt Ngưỡng ]` ➔ `[ Cổng HITL (BQL Duyệt 1-Click) ]` ➔ `[ Lệnh MQTT ]` ➔ `[ Bật Máy Lọc 45 Phút ]`
  * **Thanh Tech Stack Tinh Gọn Dưới Cùng**:  
    `[MQTT Mosquitto]` • `[PostgreSQL 16]` • `[FastAPI & Celery]` • `[LangGraph Agent]` • `[React 18 Leaflet]` • `[Docker & Caddy]`

> 🗣️ **Lời thoại thuyết trình (Integration Engineer - Hán Vũ Long / Lê Tuấn Cảnh)**:  
> *"Về mặt kiến trúc, AirGuard AI được xây dựng theo chuẩn Monorepo 5 phân tầng công nghiệp với 3 luồng dữ liệu vận hành nhịp nhàng:  
> 
> * **Luồng 1 — Telemetry Stream**: Mỗi 15 giây, 5 trạm quan trắc đẩy dữ liệu 4 chỉ số (PM2.5, CO2, ồn, nhiệt độ) qua **Mosquitto MQTT Broker**. Tầng Ingestion áp dụng **Data Quality Gate** với cơ chế Fail-Closed: tự động loại bỏ dữ liệu sai lệch hoặc trạm mất tín hiệu quá 300 giây trước khi ghi vào **PostgreSQL 16 SoR**.  
> * **Luồng 2 — Query & AI Stream**: Giao diện **React 18 và Leaflet GIS** gửi truy vấn đến **FastAPI Core**, tính toán bản đồ nhiệt IDW và phân tích lộ trình thông minh với độ trễ phản hồi **dưới 120ms**.  
> * **Luồng 3 — Action & Audit Stream**: Lệnh phê duyệt từ Cổng HITL được đẩy qua MQTT đến thiết bị dập bụi và cập nhật giao diện trong **0.8 giây**, đồng thời ghi vết kiểm toán bất biến vào bảng `audit_logs`.  
> * Toàn bộ hệ thống được đóng gói trong **8 Docker containers cô lập** và bảo mật HTTPS qua Reverse Proxy Caddy trên đám mây Azure."*

🔗 **Câu chuyển tiếp sang Slide 5 (Kỹ thuật đột phá)**:  
> *"Không chỉ sở hữu một bộ khung kiến trúc vững chắc, **điều tạo nên bước đột phá vượt trội của AirGuard AI nằm ở 4 kỹ thuật cốt lõi độc quyền**..."*

---

### ⚡ SLIDE 5: CÁC KỸ THUẬT ĐỘT PHÁ CỐT LÕI (CORE TECHNICAL INNOVATIONS) (2:25 – 3:05 | 40 GIÂY)
* **Mục tiêu tâm lý**: Tạo hiệu ứng "Aha!" mạnh mẽ trước Hội đồng nhờ chiều sâu thuật toán toán học, cơ chế an toàn AI và công thức tích phân liều lượng bụi.
* **Visual trên Slide**: Bố cục Lưới 4 Khối Kỹ Thuật Đột Phá (4 Deep-Tech Cards):
  1. **🌟 Thuật toán 2-Leg Penalized Dijkstra OSM (>10,500 cạnh)**: Định tuyến 2 chặng $S \to W \to S$; phạt 30 lần ($30\times$) trọng số cạnh chiều đi $\to$ Đường chạy tuần hoàn **đúng 0.0% trùng lặp**, tích phân liều lượng bụi hít vào ($M_{\text{inhaled}}$) **giảm 45%**.
  2. **🛡️ Cơ chế Chống Ảo Giác "Grounding trước Fluency"**: LangGraph State Machine kết hợp Grounding Policy Gate (đối chiếu 100% số liệu từ DB SoR) + Bộ chuyển mạch tiền định Fallback (<500ms khi LLM timeout >8s $\to$ **0% lỗi HTTP 5xx**).
  3. **🗺️ Nội suy không gian IDW (60x60 Grid) & Vector Gió Open-Meteo**: Thuật toán Inverse Distance Weighting bậc 2 kết hợp vector hướng gió thời gian thực và chuẩn mã màu US EPA 2012.
  4. **⚡ Cổng an toàn HITL Server-Side & Fast-Polling ACK 0.8s**: Phân quyền máy chủ nghiêm ngặt, khóa Cooldown 15 phút chống spam cảnh báo, duyệt 1-click với Thẻ bằng chứng (Evidence Card), đếm ngược 45 phút tự ngắt an toàn.

> 🗣️ **Lời thoại thuyết trình (AI Engineer - Hoàng Lê Minh)**:  
> *"Hệ thống khẳng định năng lực công nghệ vượt trội thông qua **4 kỹ thuật đột phá cốt lõi**:  
> 
> * **1. Động cơ định tuyến thể thao 2-Leg Penalized Dijkstra trên đồ thị đường thực OSM hơn 10,500 cạnh**: `[Hào hứng, tự tin]` Khác với các ứng dụng thông thường bắt runner quay đầu chạy lùi đường cũ, thuật toán của chúng tôi phạt 30 lần trọng số cạnh chiều đi, ép lộ trình ôm trọn cung đường mới ven hồ, sinh ra chu trình chạy tuần hoàn **đúng 0.0% lặp đường cũ** và **giúp giảm tới 45% lượng bụi mịn hít vào phổi**!  
> * **2. Cơ chế AI Grounded Zero-Hallucination**: Áp dụng nguyên tắc 'Grounding trước Fluency' — 100% số liệu vi khí hậu phát ngôn ra đều bắt buộc phải đối chiếu chéo từ Database. Nếu mạng LLM bên ngoài bị nghẽn quá 8 giây, bộ chuyển mạch tiền định sẽ kích hoạt trong 500ms, đảm bảo **0% lỗi sập hệ thống**.  
> * **3. Lớp phủ nhiệt IDW ma trận 60x60**: Tự động phát hiện và làm nổi bật 'hành lang không khí sạch' quanh mặt nước 24.5 ha kết hợp vector hướng gió thực tế.  
> * **4. Cổng an toàn HITL máy chủ**: Ngăn ngừa mệt mỏi cảnh báo với Cooldown 15 phút, và điều khiển máy lọc không khí nhận phản hồi ACK trong đúng **0.8 giây**!"*

🔗 **Câu chuyển tiếp sang Slide 6 (Live Demo)**:  
> *"Và để chứng minh toàn bộ kiến trúc và các kỹ thuật đột phá này vận hành mượt mà như thế nào trong thực tế, **ngay sau đây, kính mời quý Hội đồng cùng tôi trải nghiệm trực tiếp trên hệ thống đang chạy live trên Azure Cloud**..."*

---

### 💻 SLIDE 6: LIVE PRODUCT DEMO — KHOẢNH KHẮC TRẢI NGHIỆM THỰC TẾ (3:05 – 3:55 | 50 GIÂY)
* **Mục tiêu tâm lý**: Thuyết phục tuyệt đối bằng sản phẩm chạy thật, thao tác mượt mà, thời gian phản hồi tức thì dưới 1 giây.
* **Visual trên Slide**: Slide tĩnh hiển thị URL lớn: `https://airguard-074-app.indonesiacentral.cloudapp.azure.com` và 3 bước trải nghiệm.

> 🗣️ **Lời thoại người trình bày (Chuyển sang tab Web Live thao tác trong 50 giây)**:  
> *(Người trình bày chuyển nhanh sang tab trình duyệt)*  
> 
> *"Kính mời quý Hội đồng cùng nhìn lên màn hình:  
> 
> 1. **Ở vai trò Cư dân**: Bản đồ nhiệt IDW thời gian thực hiển thị sắc nét hành lang không khí trong lành quanh hồ Ngọc Trai với màu xanh mát mắt.  
> 2. **Bây giờ tôi mở Trợ lý AI và chat**: *'Gợi ý đường chạy 5km quanh hồ cho người nhạy cảm'*. `[Thao tác click]` Chỉ sau 1 giây, AI gọi động cơ 2-Leg Dijkstra, lập tức vẽ đường chạy Polyline màu xanh tuyệt đẹp ôm trọn mặt hồ, xác nhận độ trùng lặp đường cũ là **đúng 0%** và lượng bụi hít vào chỉ **4.8 microgram** — giảm 45% so với chạy ngoài đường lớn!  
> 3. **Chuyển sang vai trò Ban Quản Lý**: Khi trạm Sao Biển bị ô nhiễm, tôi mở Cổng HITL, kiểm tra Thẻ bằng chứng quan trắc và bấm **[Phê duyệt]**. `[Thao tác click]` Lập tức lệnh MQTT truyền đi, trạng thái chuyển sang xanh và đồng hồ 45 phút đếm ngược chỉ trong **0.8 giây**!"*

🔗 **Câu chuyển tiếp sang Slide 7**:  
> *"Một nền tảng công nghệ hoàn thiện như vậy mang lại **những giá trị định lượng và tiềm năng kinh doanh cụ thể nào**? Hãy cùng xem ở slide tiếp theo..."*

---

### 📈 SLIDE 7: BIZ, IMPACT & 3 CHỈ SỐ VÀNG (3:55 – 4:35 | 40 GIÂY)
* **Mục tiêu tâm lý**: Khắc sâu 3 con số tác động cốt lõi vào tâm trí Hội đồng, chứng minh tính khả thi kinh doanh và giá trị bền vững ESG.
* **Visual trên Slide**: 3 Hộp Metric Vàng Nổi Bật (3 Gold Impact Cards):
  1. `[ 🏃 0.0% TRÙNG LẶP & -45% BỤI HÍT VÀO ]` (Định tuyến 2-Leg Dijkstra né 18–25 µg bụi độc hại/buổi chạy cho runner).
  2. `[ ⚡ GIẢM 90% THỜI GIAN & ACK 0.8 GIÂY ]` (Quy trình BQL từ 25m xuống < 2m qua Cổng HITL 1-click; nhận phản hồi thiết bị trong 0.8s).
  3. `[ 🌱 TIẾT KIỆM 35% ĐIỆN & 100% BÁO CÁO ESG ]` (Tự ngắt máy lọc sau 45m tiết kiệm ~118.800 kWh/tháng ~300 triệu VNĐ tiền điện; tự động xuất báo cáo ESG).
  * Dưới cùng: `[ Nghiệm Thu Kỹ Thuật: 153/153 Automated Tests Passed (100%) • Uptime 99.9% trên Azure Cloud ]`
  * Mô hình kinh doanh: B2B/B2G SaaS ($2,000–$5,000/tháng) + B2C Athletic Subscription ($2/tháng).

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"AirGuard AI mang lại **3 giá trị định lượng thiết thực đã được kiểm chứng bằng số liệu khoa học**:  
> 
> * **1. 🏃 0.0% Trùng Lặp & Giảm 45% Bụi Hít Vào**: Thuật toán 2-Leg Dijkstra trên OSM giúp runner né được 18 đến 25 microgram bụi mịn độc hại mỗi buổi tập mà không bao giờ phải chạy lùi đường cũ.  
> * **2. ⚡ Giảm 90% Thời Gian & Phản Hồi Thiết Bị 0.8 Giây**: Rút ngắn thời gian xử lý sự cố ô nhiễm của Ban Quản Lý từ 25 phút xuống dưới 2 phút qua Cổng HITL 1-click, đồng thời nhận bản tin ACK thiết bị dập bụi trong đúng 0.8 giây.  
> * **3. 🌱 Tiết Kiệm 35% Điện Năng & 100% Tự Động Hóa Báo Cáo ESG**: Cơ chế tự ngắt máy lọc sau 45 phút tiết kiệm khoảng 118,800 kWh mỗi tháng — tương đương gần 300 triệu đồng tiền điện cho 66 tòa chung cư, đồng thời tự động hóa toàn bộ báo cáo kiểm toán môi trường đạt chuẩn quốc tế.  
> * **Về Mức Độ Hoàn Thiện & Kinh Doanh**: Dự án đã vượt qua **153 trên 153 bài kiểm thử tự động**, sẵn sàng thương mại hóa theo mô hình **B2B SaaS** cho các chủ đầu tư đô thị thông minh kết hợp gói **B2C** cho hàng ngàn runner."*

🔗 **Câu chuyển tiếp sang Slide 8**:  
> *"Để hiện thực hóa một khối lượng công việc đồ sộ như vậy, **ai là những người đứng sau dự án**?..."*

---

### 👥 SLIDE 8: ĐỘI NGŨ THỰC HIỆN DỰ ÁN — NHÓM P-074 (4:35 – 4:50 | 15 GIÂY)
* **Mục tiêu tâm lý**: Thấy được năng lực chuyên môn vững vàng, sự phân công nhiệm vụ rõ ràng và tinh thần đồng đội gắn kết.
* **Visual trên Slide**: Thẻ 4 Thành Viên Nhóm P-074 (Tứ Kỵ Sĩ Khải Huyền):
  1. **Lê Tuấn Cảnh** — Team Lead / Backend & Cloud (Kiến trúc Monorepo 5 lớp, FastAPI, Postgres SoR, Azure VM).
  2. **Hán Vũ Long** — Integration / IoT Pipeline (Mosquitto MQTT, Telemetry Ingestion, Forecast Model).
  3. **Hoàng Lê Minh** — AI Engineer (LangGraph State Machine, Grounding Policy Gate, Động cơ 2-Leg OSM Dijkstra).
  4. **Phạm Thế Dũng** — Frontend / QA Engineer (React 18 Leaflet GIS, Fast-Polling UI, Test Suite 153 Tests).

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"Đằng sau sự hoàn thiện vượt bậc của AirGuard AI là sự nỗ lực kỷ luật và đồng bộ của 4 thành viên nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền: từ thiết kế kiến trúc, xây dựng pipeline IoT vi khí hậu, phát triển thuật toán AI định tuyến chạy bộ cho đến kiểm thử tự động hóa 153 test cases."*

🔗 **Câu chuyển tiếp sang Slide 9**:  
> *"Và với nền tảng vững chắc đó, **tầm nhìn tương lai của chúng tôi là gì**?..."*

---

### 🚀 SLIDE 9: ĐỊNH HƯỚNG PHÁT TRIỂN & LỜI CẢM ƠN (4:50 – 5:00 | 10 GIÂY)
* **Mục tiêu tâm lý**: Tạo ấn tượng sâu sắc về sản phẩm lấy cư dân làm trung tâm, lộ trình công nghệ thiết thực và mở màn phiên Q&A đầy hứng khởi.
* **Visual trên Slide**:
  * Lộ trình 3 giai đoạn phát triển hướng tới cư dân (Resident-Centric Roadmap):
    * `Giai đoạn 1 (Q4/2026)`: **Ra mắt Mobile App & Đồng bộ Đồng hồ thông minh**: Ứng dụng di động (iOS, Android, Zalo Mini App) cho cư dân, thông báo đẩy theo GPS, đồng bộ tuyến chạy sạch 1-click lên Apple Watch/Garmin/Strava kèm cảnh báo rung khi vào vùng ô nhiễm.
    * `Giai đoạn 2 (Q1/2027)`: **Hệ sinh thái Tiện ích Cư dân & Smart Home**: Tự động nhắc nhở đóng cửa sổ, liên động bật máy lọc không khí căn hộ theo chất lượng không khí ngoài trời; khởi động Thử thách "Chạy Xanh Tích Điểm" đổi voucher dịch vụ đô thị (bơi, gửi xe, cà phê ven hồ).
    * `Giai đoạn 3 (2027+)`: **Nhân rộng chuỗi Smart City toàn quốc**: Triển khai giải pháp ra toàn bộ hệ thống đại đô thị Vinhomes (Smart City, Grand Park), Ecopark và các đô thị lớn tại Việt Nam.
  * Mã QR quét trải nghiệm trực tiếp Web Live và GitHub Repo.
  * Thông điệp: *"AirGuard AI — Vì Một Đại Đô Thị Xanh, Thông Minh & Khỏe Mạnh!"*
  * Dòng chữ lớn: **Xin chân thành cảm ơn Ban Giám Khảo & Quý Hội Đồng! Sẵn sàng cho phiên Q&A!**

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh)**:  
> *"Trong giai đoạn tới, chúng tôi tập trung tối đa vào trải nghiệm cư dân:  
> * **Đầu tiên là ra mắt Mobile App và Zalo Mini App**, cho phép cư dân theo dõi vi khí hậu mọi lúc mọi nơi và đồng bộ tuyến chạy sạch trực tiếp lên **Garmin, Apple Watch, Strava** với cảnh báo rung an toàn.  
> * **Tiếp theo là liên động Nhà Thông Minh Smart Home** tự động nhắc đóng cửa sổ, đồng thời mở tính năng **'Chạy Xanh Tích Điểm'** đổi voucher tiện ích đô thị.  
> * Và từng bước nhân rộng mô hình ra toàn bộ các đại đô thị thông minh tại Việt Nam!  
> 
> Chúng tôi rất mong muốn nhận được sự đồng hành, cố vấn từ Ban giám khảo và các nhà đầu tư để đưa AirGuard AI phục vụ hàng triệu cư dân đô thị!  
> 
> **Xin chân thành cảm ơn quý Hội đồng! Toàn đội chúng tôi rất sẵn sàng cho phiên Q&A!**"*

---

## 🛡️ CẨM NANG ĐỐI ĐÁP Q&A VỚI BAN GIÁM KHẢO (QUICK REBUTTALS CHEATSHEET)

| Câu Hỏi Hóc Búa Của Hội Đồng | Điểm Cốt Tử Cần Trả Lời Ngay (Key Takeaways) |
|---|---|
| **1. "Làm sao đảm bảo AI không ảo giác (Hallucination) số liệu vi khí hậu?"** | Trả lời: Áp dụng nguyên tắc *"Grounding trước Fluency"*. Mọi câu trả lời có chứa số liệu đều bị chặn lại tại **Cổng Grounding Policy Gate** để đối chiếu chéo token với kết quả Tool Calling từ PostgreSQL. Đạt **100% Grounding Accuracy** trên 87 ca kiểm thử. |
| **2. "Nếu mất mạng Internet hoặc API OpenAI/Gemini bị lỗi thì sao?"** | Trả lời: Hệ thống có **Bộ chuyển mạch tiền định (Deterministic Fallback Switcher)**. Khi LLM timeout > 8 giây, bộ chuyển mạch nội bộ tự động sinh câu trả lời chuẩn xác từ trạm đo gần nhất trong **< 500ms**, cam kết **0% lỗi HTTP 5xx**. |
| **3. "Tại sao không để AI tự động bật máy lọc không khí mà phải qua HITL?"** | Trả lời: Điều khiển thiết bị vật lý liên quan đến điện năng, tiếng ồn và an toàn PCCC tòa nhà. AI chỉ tạo đề xuất dạng `pending` kèm Thẻ bằng chứng (Evidence Card) trong 850ms, nhưng **con người (Trưởng ca BQL) phải là người duyệt 1-click cuối cùng**. |
| **4. "Thuật toán 2-Leg Dijkstra có chắc chắn 0% lặp đường cũ không?"** | Trả lời: Thuật toán phạt 30 lần ($30\times$) trọng số các cạnh đường chặng đi, ép chặng về ôm trọn mặt hồ mới. Đo đạc hình học trên 30 vòng lặp thực tế đạt **khoảng cách khép kín d = 0.0 mét (100% kín)** và **tỷ lệ chạy lùi đường cũ đúng 0.0%**. |
| **5. "Dữ liệu lấy từ đâu? Nếu một cảm biến bị offline thì xử lý thế nào?"** | Trả lời: Tầng Ingestion có **Data Quality Gate** với cơ chế Fail-Closed. Trạm mất kết nối quá 300 giây sẽ tự động chuyển sang trạng thái `stale` và bị loại khỏi phép tính IDW, không làm sai lệch bản đồ nhiệt. |
| **6. "Chi phí vận hành đám mây hiện tại là bao nhiêu?"** | Trả lời: Nhờ kiến trúc tối ưu (P95 API latency < 120ms), toàn bộ hệ thống đang chạy mượt mà trên **Azure VM Standard B2ms** với chi phí chỉ **$35 – $40 / tháng** cho cả khu đô thị 30,000 dân. |

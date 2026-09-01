# 🎤 KỊCH BẢN PITCHING ĐỈNH CAO — AIRGUARD AI (P-074)
> **Dự án**: AirGuard AI — AI Agent Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh  
> **Đơn vị thực hiện**: Nhóm P-074 / Tứ Kỵ Sĩ Khải Huyền (AI20K Build Phase Cohort 3)  
> **Điểm nhấn cốt lõi**: **Đáp ứng 100% yêu cầu Đề bài (Cơ bản + Nâng cao) + Bùng nổ Tính năng mới: AI Agent Chat Định Tuyến Chạy Bộ Sạch Khép Kín 0% Trùng Lặp trên Đồ Thị OSM**.  
> **Thời lượng chuẩn**: **5 - 7 phút** | **Web Demo Live**: [https://airguard-074-app.indonesiacentral.cloudapp.azure.com](https://airguard-074-app.indonesiacentral.cloudapp.azure.com)

---

## 🗺️ MA TRẬN 12 SLIDE BÁM SÁT ĐỀ BÀI & HÌNH ẢNH HỆ THỐNG

| Slide | Tiêu đề Slide | Đáp ứng yêu cầu đề bài & Tính năng mới | Hình ảnh đính kèm từ thư mục `image/` |
|:---:|---|---|---|
| **Slide 1** | **Cover Slide** | Khẳng định tên tuổi, giải pháp và cam kết chất lượng | `image/Mockup 1 - GIS Dashboard & Heatmap.png` |
| **Slide 2** | **Thực Trạng & Đề Bài** | Thực trạng dữ liệu rời rạc, nhu cầu AI Agent đa điểm | *Bản đồ vi khí hậu Ocean Park 1 (AQI 35 vs 150+)* |
| **Slide 3** | **Tổng Quan Giải Pháp** | 2 Vai trò (Cư dân & BQL), 10 Use Cases, Khép kín IoT -> AI -> Action | `image/Use Case Diagram.png` |
| **Slide 4** | **🌟 KILLER FEATURE: AI Routing** | **TÍNH NĂNG MỚI ĐỘT PHÁ**: Chat Agent sinh đường chạy sạch 2-Leg OSM 0% lặp | `image/Kiến trúc thuật toán tìm đường chạy sạch.png` / `Mockup 3` |
| **Slide 5** | **Dashboard & Dự Báo** | Dashboard AQI EPA, Heatmap IDW, Dự báo chuỗi thời gian 1-24h | `image/Mockup 1` + `Mockup 2 - Station Detail Drawer.png` |
| **Slide 6** | **Cá Nhân Hóa & Chống Nhiễu** | 3 Nhóm sức khỏe, Trọng số phạt 2.0x, Cooldown 15m chống cảnh báo rác | `image/Mockup 4 - Health Profile Modal.png` |
| **Slide 7** | **Cổng HITL & Thiết Bị 0.8s** | Ràng buộc HITL bắt buộc, điều khiển máy lọc phản hồi 0.8s, tự ngắt 45m | `image/Luồng cảnh báo tự động & HITL.png` / `Mockup 5` |
| **Slide 8** | **Kiến Trúc & Safe AI** | Monorepo 5 lớp, Data Quality Gate, Grounding Policy Gate (Không ảo giác) | `image/Sơ đồ kiến trúc tổng thể.png` / `image/Luồng hội thoại...` |
| **Slide 9** | **Live Product Demo** | Trình diễn trực tiếp 3 kịch bản vận hành trên Azure Cloud VM | Ghép `Mockup 1` + `Mockup 3` + `Mockup 5` |
| **Slide 10**| **Tác Động & Báo Cáo ESG** | Giảm 45% bụi hít, giảm 90% thời gian xử lý, Báo cáo môi trường định kỳ | `image/Mockup 6 - Audit Log Center.png` |
| **Slide 11**| **Chất Lượng Kỹ Thuật** | 153/153 Tests Passed (100%), Độ trễ API <120ms, Docker 8 Containers | `image/Sơ đồ triển khai hạ tầng.png` |
| **Slide 12**| **Đội Ngũ P-074 & Q&A** | 4 Thành viên nòng cốt, Mã QR Web Live, Sẵn sàng phản biện | *Ảnh 4 thành viên P-074 & QR Code* |

---

## 🎯 KỊCH BẢN CHI TIẾT TỪNG SLIDE (WORD-FOR-WORD SCRIPT)

---

### 🟢 SLIDE 1: TRANG TIÊU ĐỀ (COVER SLIDE)
* **Visual trên Slide**: Logo AirGuard AI hiện đại trên nền tối, hình nền bản đồ GIS Ocean Park 1 phát sáng, huy hiệu `153/153 Tests Passed` và `Live on Azure Cloud`.
* **Mục tiêu**: Gây ấn tượng mạnh mẽ ngay từ giây đầu tiên về sự hoàn thiện và tính thực chiến của dự án.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh - 30 giây)**:  
> *"Kính chào quý Ban giám khảo, các Mentor và toàn thể hội đồng!  
> Chúng tôi là **Nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền**.  
> 
> Hôm nay, chúng tôi rất tự hào mang đến dự án **AirGuard AI** — Hệ sinh thái AI Agent toàn diện: từ giám sát vi khí hậu thời gian thực, cảnh báo cá nhân hóa theo thể trạng sức khỏe, đến liên động điều khiển thiết bị dập bụi đô thị.  
> 
> Đặc biệt, chúng tôi mang đến **một bước đột phá hoàn toàn mới**: **Trợ lý AI đàm thoại tự động vẽ tuyến đường thể thao sạch bụi khép kín cho cư dân trên đồ thị đường thực OSM**.  
> Một sản phẩm **đã vượt qua 153 bài kiểm thử tự động và đang vận hành thực tế 100% trên đám mây Azure**."*

---

### 🔴 SLIDE 2: BỐI CẢNH ĐỀ BÀI, THỰC TRẠNG & THÁCH THỨC ĐÔ THỊ (THE PROBLEM)
* **Visual trên Slide**: Sơ đồ so sánh trạm khí tượng xa 15km vs thực tế Vinhomes Ocean Park 1 (Biển hồ AQI 35 vs Trục đường thi công Sao Biển AQI 150+). Hình ảnh dữ liệu cảm biến rời rạc và người tập thể dục bị mù mờ thông tin.
* **Mục tiêu**: Bám sát 100% phần "Thực trạng" và "Vấn đề" của Đề bài gốc.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh - 45 giây)**:  
> *"Thưa quý vị, đề bài đặt ra cho chúng ta một thực trạng rất rõ ràng: Tại các khu đô thị hiện đại, dù đã có cảm biến bụi mịn, CO2, tiếng ồn và nhiệt độ, nhưng **dữ liệu hoàn toàn rời rạc**.  
> 
> Tại Vinhomes Ocean Park 1, chất lượng không khí biến thiên siêu cục bộ: Cùng một thời điểm, mặt nước Biển Hồ 6.1 ha có chỉ số AQI rất tốt (35), nhưng chỉ cách đó vài trăm mét, trục đường thi công Sao Biển nồng độ PM2.5 lại tăng vọt lên mức Nguy hại (AQI 150+).  
> 
> Hậu quả là:  
> 1. **Cư dân tập thể dục, chạy bộ ngoài trời** không biết đi đâu, vô tình hít phải hàng chục microgram bụi mịn độc hại vào sâu phế nang.  
> 2. **Nhóm nhạy cảm** (trẻ em, người già, người bệnh hô hấp) không có cảnh báo sớm theo thể trạng.  
> 3. **Ban Quản Lý** thì lúng túng, thiếu công cụ AI tổng hợp đa điểm để liên động kích hoạt hệ thống lọc dập bụi kịp thời."*

---

### 💡 SLIDE 3: TỔNG QUAN GIẢI PHÁP & 10 USE CASES (THE SOLUTION)
* **Visual trên Slide**: Chèn ảnh `image/Use Case Diagram.png` (Mục 4.1 SRS). Bố cục 2 cột phân quyền rõ rệt: Cư Dân (Resident) & Ban Quản Lý (Urban Manager).
* **Mục tiêu**: Chứng minh hệ thống giải quyết trọn vẹn cả yêu cầu Cơ bản lẫn Nâng cao của Đề bài.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh - 45 giây)**:  
> *"Để giải quyết toàn diện bài toán trên, AirGuard AI được thiết kế chuẩn mực với **2 vai trò người dùng và 10 ca sử dụng khép kín**:  
> 
> * **Với Cư dân**: Cung cấp Dashboard bản đồ nhiệt AQI thời gian thực (`UC-01`), ngăn chi tiết trạm và dự báo 1-24h (`UC-02`), thiết lập hồ sơ sức khỏe cá nhân hóa (`UC-06`), đàm thoại cùng Trợ lý AI (`UC-04`) và **nhận tuyến đường chạy thể thao sạch bụi khép kín** (`UC-05`).  
> * **Với Ban Quản Lý**: Cung cấp Cổng phê duyệt HITL 1-click (`UC-08`), điều khiển thủ công trạm lọc khí phản hồi 0.8s (`UC-07`), truy vết nhật ký kiểm toán bất biến (`UC-09`) và tự động xuất báo cáo môi trường định kỳ (`UC-10`).  
> 
> Một chu trình trọn vẹn từ **Quan trắc $\to$ Dự báo $\to$ Phân tích AI $\to$ Hành động can thiệp**!"*

---

### 🌟 SLIDE 4: TÍNH NĂNG MỚI ĐỘT PHÁ: AGENT ĐỊNH TUYẾN CHẠY BỘ SẠCH 0% LẶP (KILLER FEATURE)
* **Visual trên Slide**: Chèn ảnh `image/Kiến trúc thuật toán tìm đường chạy sạch.png` kết hợp `image/Mockup 3 - AI Chat & Clean Running Route.png`. Sơ đồ 2 chặng: Forward Leg (S->W) và Backward Leg (W->S) phạt 30x trọng số né đường cũ.
* **Mục tiêu**: **LÀM NỔI BẬT TÍNH NĂNG MỚI ĐỘC QUYỀN** theo đúng yêu cầu người dùng!

> 🗣️ **Lời thoại người trình bày (AI Engineer - Hoàng Lê Minh - 60 giây)**:  
> *"Bên cạnh các yêu cầu cơ bản, điểm sáng tạo đột phá lớn nhất của AirGuard AI chính là: **Ứng dụng AI Agent đàm thoại tự động vẽ lộ trình thể thao sạch bụi cho cư dân trên đồ thị đường thực OpenStreetMap (OSM)**!  
> 
> Hãy thử tưởng tượng: Một cư dân mở app và chat với AI: *'Tôi muốn chạy bộ 5km quanh hồ lúc 17h, hãy chọn đường sạch nhất cho người nhạy cảm'*.  
> 
> Các ứng dụng chỉ đường thông thường như Google Maps sẽ hướng dẫn chạy đến điểm 2.5km rồi bắt người dùng quay đầu chạy lùi 100% đường cũ.  
> Nhưng với AirGuard AI, chúng tôi sáng tạo thuật toán độc quyền **2-Leg Penalized Dijkstra trên đồ thị hơn 10,500 cạnh OSM**:  
> 1. Chặng đi, thuật toán dẫn runner đến điểm mốc trong lành ven hồ.  
> 2. Lập tức, hệ thống **nhân hệ số phạt 30 lần** lên toàn bộ các đoạn đường vừa đi qua.  
> 3. Buộc chặng về phải tìm một cung đường hoàn toàn mới men theo công viên biển hồ.  
> 
> 👉 **Kết quả**: Sinh ra một cung đường thể thao khép kín tuần hoàn với **đúng 0.0% trùng lặp**, đạt cự ly chính xác 5.0km và **tính toán tích phân lượng bụi hít vào phổi giảm tới 45%** so với chạy tự do!"*

---

### 📊 SLIDE 5: DASHBOARD GIS REALTIME, HEATMAP IDW & DỰ BÁO 1-24H (DASHBOARD & FORECAST)
* **Visual trên Slide**: Ghép ảnh `image/Mockup 1 - GIS Dashboard & Heatmap.png` và `image/Mockup 2 - Station Detail Drawer.png`. Thể hiện thanh đo AQI US EPA 2012, lưới nội suy IDW 60x60 và biểu đồ dự báo xu hướng vi khí hậu 1-24h.
* **Mục tiêu**: Minh chứng tính năng Dashboard đa điểm và Dự báo chuỗi thời gian của Đề bài.

> 🗣️ **Lời thoại người trình bày (Frontend/QA - Phạm Thế Dũng - 45 giây)**:  
> *"Về khả năng quan trắc và dự báo môi trường đa điểm:  
> 
> * **Bản đồ nhiệt IDW thời gian thực**: Hệ thống tính toán ma trận lưới 60x60 kết hợp hướng gió, trực quan hóa vùng lan truyền ô nhiễm và tự động làm nổi bật 'hành lang không khí sạch' dọc theo mặt nước 24.5 ha.  
> * **Thanh đo chuẩn hóa US EPA 2012**: Đánh giá nồng độ PM2.5, CO2, tiếng ồn và nhiệt độ/độ ẩm theo 6 cấp độ màu sắc trực quan, đạt chuẩn tiếp cận WCAG 2.1 AA.  
> * **Dự báo chuỗi thời gian 1 đến 24 giờ**: Kết hợp mô hình Moving Average trọng số và Open-Meteo context, giúp cư dân chủ động lên kế hoạch sinh hoạt và tập luyện từ sớm."*

---

### 🧒 SLIDE 6: CẢNH BÁO CÁ NHÂN HÓA & CƠ CHẾ CHỐNG CẢNH BÁO NHIỄU (HEALTH PROFILE & COOLDOWN)
* **Visual trên Slide**: Chèn ảnh `image/Mockup 4 - Health Profile Modal.png`. Minh họa 3 nhóm sức khỏe (`normal`, `sensitive` phạt 2.0x, `outdoor_sport`) và biểu đồ Cooldown 15 phút chống spam.
* **Mục tiêu**: Đáp ứng ràng buộc "Cảnh báo cá nhân hóa theo nhóm sức khỏe" và "Tránh cảnh báo nhiễu gây mệt mỏi" trong đề bài.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh - 45 giây)**:  
> *"Đề bài yêu cầu: Cảnh báo phải cá nhân hóa theo nhóm sức khỏe nhưng tuyệt đối **tránh cảnh báo nhiễu gây mệt mỏi cho người dân**. Chúng tôi giải quyết bài toán này bằng 2 cơ chế:  
> 
> * **Hồ sơ sức khỏe 3 nhóm đối tượng**: Người dùng có thể chọn nhóm Bình thường, Nhóm Nhạy cảm hô hấp (trẻ em, người cao tuổi) hoặc Người tập thể thao. Với nhóm nhạy cảm, thuật toán định tuyến sẽ **tự động nhân đôi trọng số phạt ô nhiễm (2.0x)** và hạ ngưỡng kích hoạt cảnh báo xuống AQI > 100.  
> * **Cơ chế Chống Cảnh Báo Nhiễu (15-Minute Cooldown Gate)**: Cảnh báo chỉ kích hoạt khi nồng độ bụi vượt ngưỡng liên tiếp trong 2 chu kỳ đo (30 giây), và áp dụng thời gian chờ 15 phút giữa 2 lần gửi cảnh báo liên tiếp, loại bỏ hoàn toàn hiện tượng spam thông báo."*

---

### 🛡️ SLIDE 7: CỔNG HITL BẮT BUỘC & ĐIỀU KHIỂN MÁY LỌC 0.8S (HITL & DEVICE CONTROL)
* **Visual trên Slide**: Chèn ảnh `image/Luồng cảnh báo tự động & HITL.png` và `image/Mockup 5 - HITL Approval Center.png`. Minh họa Thẻ Thẩm Định Chứng Cứ (Evidence Card) và nút bấm duyệt 1-click phản hồi ACK 0.8s.
* **Mục tiêu**: Đáp ứng ràng buộc khắt khe nhất của Đề bài: "Lệnh liên động thiết bị thông gió/lọc khí PHẢI HITL với BQL".

> 🗣️ **Lời thoại người trình bày (Integration Engineer - Hán Vũ Long - 45 giây)**:  
> *"Ràng buộc bảo mật quan trọng nhất của đề bài là: **Lệnh liên động hệ thống lọc khí/thông gió chung BẮT BUỘC phải có sự phê duyệt của Ban Quản Lý (HITL)**.  
> 
> * Khi phát hiện ô nhiễm kéo dài, AI **chỉ tạo đề xuất ở trạng thái Pending** kèm theo Thẻ Thẩm Định Chứng Cứ (Evidence Card) ghi nhận đầy đủ số liệu trạm, thời tiết và so sánh trạm lân cận.  
> * Người quản lý thẩm định và bấm **[Phê duyệt 1-Click]**.  
> * Lập tức, bộ Dispatcher đẩy lệnh MQTT kích hoạt máy lọc FILTER-S01..S05 chạy tăng cường 80% công suất trong 45 phút, nhận bản tin xác nhận ACK trên giao diện trong đúng **0.8 giây**!  
> * Hệ thống tự động đếm ngược và ngắt an toàn, tiết kiệm điện năng và bảo vệ tuổi thọ thiết bị."*

---

### 🏗️ SLIDE 8: KIẾN TRÚC MONOREPO 5 LỚP & AI GROUNDING GATE (ARCHITECTURE & AI SAFETY)
* **Visual trên Slide**: Ghép `image/Sơ đồ kiến trúc tổng thể.png` và `image/Luồng hội thoại của AI Agent & Grounding Policy Gate.png`.
* **Mục tiêu**: Thể hiện chiều sâu kỹ thuật, công nghệ LangGraph và nguyên tắc Zero-Hallucination.

> 🗣️ **Lời thoại người trình bày (AI Engineer - Hoàng Lê Minh - 45 giây)**:  
> *"Về kiến trúc nền tảng, AirGuard AI được xây dựng theo mô hình Monorepo 5 phân tầng hoàn chỉnh: IoT Mosquitto $\to$ Fail-Closed Quality Gate $\to$ PostgreSQL SoR $\to$ FastAPI & LangGraph $\to$ React Leaflet GIS.  
> 
> Đặc biệt, để đảm bảo an toàn y tế và môi trường, chúng tôi áp dụng nguyên tắc **'Grounding trước Fluency'**:  
> 100% câu trả lời của AI đều được thẩm định qua **Cổng Grounding Policy Gate** đối chiếu trực tiếp từ cơ sở dữ liệu.  
> Nếu mạng LLM ngoài bị gián đoạn quá 8.0 giây, **Bộ chuyển mạch tiền định (Deterministic Fallback)** sẽ kích hoạt trong 500ms để trả lời ngay từ dữ liệu cảm biến cục bộ, cam kết **0% lỗi HTTP 5xx** và không bao giờ ảo giác."*

---

### 💻 SLIDE 9: TRÌNH DIỄN SẢN PHẨM THỰC TẾ TRÊN AZURE CLOUD (LIVE DEMO SHOWCASE)
* **Visual trên Slide**: Ghép 3 khung hình UI thực tế trên nền tối: Bản đồ GIS + AI Chat Tuyến Đường 5km + Cổng Phê Duyệt HITL.
* **Mục tiêu**: Khẳng định sản phẩm đã chạy thực tế trên production, không phải mockup tĩnh.

> 🗣️ **Lời thoại người trình bày (Frontend/QA - Phạm Thế Dũng - 60 giây - Thao tác mở tab live)**:  
> *"Kính mời quý hội đồng cùng nhìn lên màn hình trải nghiệm trực tiếp trên Azure Cloud VM:  
> 
> * **Thao tác 1**: Trên Dashboard, 5 trạm quan trắc vi khí hậu cập nhật liên tục mỗi 15 giây. Khi bấm vào trạm San Hô, ngăn chi tiết hiển thị đầy đủ 4 chỉ số và biểu đồ diễn biến 24 giờ qua.  
> * **Thao tác 2 (Killer Feature)**: Khi cư dân mở ngăn chat và yêu cầu lộ trình chạy bộ 5km, AI Agent gọi động cơ 2-Leg Dijkstra, lập tức vẽ đường chạy màu xanh tuyệt đẹp ôm trọn mặt hồ nước mặn, khẳng định 0% lặp đường cũ và hiển thị liều lượng bụi mịn hít vào chỉ 4.8 microgram!  
> * **Thao tác 3**: Khi trạm Sao Biển ô nhiễm, Quản lý chuyển sang Cổng HITL, bấm [Phê duyệt], trạng thái máy lọc lập tức chuyển xanh và đếm ngược 45 phút chỉ trong **0.8 giây**!"*

---

### 📈 SLIDE 10: TÁC ĐỘNG SỨC KHỎE, VẬN HÀNH & BÁO CÁO ESG (BUSINESS IMPACT & ESG)
* **Visual trên Slide**: Chèn ảnh `image/Mockup 6 - Audit Log Center.png`. 3 Hộp số liệu lớn: `-45% Bụi hít vào`, `-90% Thời gian xử lý`, `100% Tự động hóa Báo cáo ESG`.
* **Mục tiêu**: Đáp ứng tính năng nâng cao "Báo cáo môi trường định kỳ" và định lượng giá trị kinh tế - xã hội.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh - 35 giây)**:  
> *"AirGuard AI mang lại giá trị định lượng thiết thực trên cả 3 phương diện:  
> * **Với Cư Dân**: Giảm từ **35% đến 45%** lượng bụi mịn độc hại hít vào phổi khi tập thể thao ngoài trời.  
> * **Với Vận Hành Đô Thị**: Giảm **90%** thời gian phản ứng xử lý điểm nóng ô nhiễm; tiết kiệm năng lượng nhờ tự ngắt máy lọc sau 45 phút.  
> * **Với Bền Vững & ESG**: Bảng `audit_logs` Append-Only bất biến, tự động xuất báo cáo môi trường và năng lượng định dạng PDF/Excel chuẩn mực, phục vụ kiểm toán và chứng chỉ đô thị xanh quốc tế."*

---

### 🏆 SLIDE 11: NGHIỆM THU KỸ THUẬT & HẠ TẦNG DEPLOY (QUALITY & DEPLOYMENT)
* **Visual trên Slide**: Chèn ảnh `image/Sơ đồ triển khai hạ tầng.png`. Huy hiệu `153/153 Tests Passed (100%)`, biểu đồ độ trễ API `< 120ms`, sơ đồ 8 Docker Containers sau Caddy Reverse Proxy trên Azure VM B2ms.
* **Mục tiêu**: Khẳng định chất lượng kỹ thuật vượt trội và tính sẵn sàng chuyển giao.

> 🗣️ **Lời thoại người trình bày (Frontend/QA - Phạm Thế Dũng - 35 giây)**:  
> *"Về chất lượng kỹ thuật, sản phẩm đã hoàn thành **100% các tiêu chí nghiệm thu nghiêm ngặt nhất**:  
> * Vượt qua **153 trên 153 kịch bản kiểm thử tự động**, bao phủ toàn diện từ Unit test, API Contract, Thuật toán OSM Router đến AI Safety và HITL RBAC.  
> * Độ trễ phản hồi API trung bình đạt dưới **120ms**, thời gian nhận ACK thiết bị chỉ **0.8 giây**.  
> * Toàn bộ hệ thống được đóng gói trong 8 Docker containers, bảo mật HTTPS qua Caddy Reverse Proxy và duy trì độ sẵn sàng SLA 99.9% trên Azure Cloud."*

---

### 👥 SLIDE 12: ĐỘI NGŨ THỰC HIỆN P-074 & PHIÊN HỎI ĐÁP (TEAM & CLOSING)
* **Visual trên Slide**: Thẻ 4 thành viên nhóm P-074 kèm vai trò chuyên trách. Mã QR quét truy cập trực tiếp Website Demo live và GitHub Repo.
* **Mục tiêu**: Khép lại bài thuyết trình trang trọng, tự tin và mở màn phiên Q&A bùng nổ.

> 🗣️ **Lời thoại người trình bày (Lead - Lê Tuấn Cảnh - 30 giây)**:  
> *"Thành quả này là kết tinh từ sự phối hợp kỷ luật và đam mê công nghệ của 4 thành viên nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền:  
> * **Lê Tuấn Cảnh**: Team Lead, Kiến trúc Monorepo & Backend FastAPI.  
> * **Hán Vũ Long**: Integration & Telemetry Pipeline.  
> * **Hoàng Lê Minh**: AI Agent LangGraph & Grounding Policy Gate.  
> * **Phạm Thế Dũng**: Frontend React Leaflet GIS & Test Suite 153 Tests.  
> 
> **AirGuard AI — Vì Một Đại Đô Thị Xanh, Thông Minh & Khỏe Mạnh!**  
> Chúng tôi xin chân thành cảm ơn quý Hội đồng và rất sẵn sàng đón nhận các câu hỏi!"*

---

## 💡 BỘ CÂU HỎI PHẢN BIỆN "ĐINH" CỦA HỘI ĐỒNG & CÁCH TRẢ LỜI CHUẨN

#### 1. ❓ Hội đồng hỏi: *"Tính năng vẽ đường chạy thể dục của các bạn có gì khác biệt so với việc người dùng tự mở Google Maps hoặc Strava?"*
* **👉 Trả lời sắc bén**:  
  > *"Dạ thưa Ban giám khảo, có **3 điểm khác biệt cốt tử mang tính bản quyền**:  
  > 1. **Khả năng nhận biết chất lượng không khí thời gian thực (AQI-Aware)**: Google Maps chỉ tìm đường ngắn nhất mà không biết đường đó đang bị ô nhiễm do công trường thi công. Thuật toán của chúng tôi phạt nặng các cạnh đường đi qua vùng có nồng độ PM2.5 cao để ép đường chạy né sang hành lang trong lành quanh biển hồ.  
  > 2. **Đường chạy khép kín tuần hoàn 0% trùng lặp (Zero Retracing)**: Google Maps nếu tìm đường vòng 5km từ điểm xuất phát sẽ bắt người dùng chạy 2.5km rồi quay đầu chạy lùi 100% đường cũ. Thuật toán 2 chặng (2-Leg Penalized) của chúng tôi phạt 30x chiều về, tạo cung đường vòng quanh hồ tròn trịa, 0% chạy lùi.  
  > 3. **Tích phân định lượng liều lượng bụi hít vào ($\mu g$)**: Chúng tôi tính toán cụ thể người chạy hít vào bao nhiêu microgram bụi mịn dựa trên cự ly và thông khí phổi, giúp runner kiểm soát sức khỏe chính xác."*

#### 2. ❓ Hội đồng hỏi: *"Làm sao các bạn bảo đảm AI Agent không tự động bật máy lọc không khí trái phép hoặc gửi cảnh báo rác làm phiền cư dân?"*
* **👉 Trả lời sắc bén**:  
  > *"Dạ thưa Hội đồng, chúng tôi áp dụng 2 chốt chặn kỹ thuật bất khả xâm phạm:  
  > 1. **Nguyên tắc HITL máy chủ (Server-Side HITL Gate)**: AI Agent tuyệt đối không có quyền phát lệnh MQTT điều khiển thiết bị; nó chỉ được tạo một đề xuất ở trạng thái `pending`. Chỉ tài khoản có vai trò `Manager` mới có nút bấm gửi lệnh MQTT sau khi thẩm định Thẻ bằng chứng quan trắc.  
  > 2. **Cơ chế Cooldown Gate 15 phút**: Cảnh báo chỉ được sinh ra khi nồng độ bụi vượt ngưỡng liên tiếp trong 2 chu kỳ đo (30 giây) và bị khóa trong 15 phút sau đó, ngăn chặn 100% tình trạng cảnh báo rác do cảm biến bị nhiễu tức thời."*

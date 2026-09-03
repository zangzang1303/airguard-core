# 🛡️ TỔNG HỢP TOÀN BỘ CÂU HỎI & ĐÁP ÁN PHẢN BIỆN Q&A (MASTER DEFENSE HANDBOOK)
# DỰ ÁN AIRGUARD AI — NHÓM P-074 (TỨ KỴ SĨ KHẢI HUYỀN)

> **Mục tiêu tài liệu:** Cẩm nang tra cứu siêu tốc dành cho người thuyết trình và các thành viên nhóm P-074 khi đối đáp với Ban Giám Khảo, Mentor và Hội đồng chấm thi tại vòng **Gate 2 Final Pitching**.  
> **Cấu trúc:** Gồm 20 câu hỏi bao quát trọn vẹn 5 trụ cột của dự án (Sản phẩm/Thị trường, Kiến trúc/Database, AI Agent/Thuật toán, An toàn HITL/Phần cứng, Kiểm thử/Hạ tầng).  
> **Quy tắc trả lời:** Mỗi câu hỏi đều có **1 câu chốt hạ đanh thép (One-Liner)** để nói ngay trong 5 giây đầu, kèm **2-3 luận điểm số liệu thực chứng**.

---

## 📑 MỤC LỤC 5 TRỤ CỘT CÂU HỎI

* **PHẦN 1: SẢN PHẨM, THỊ TRƯỜNG & ĐỐI THỦ CẠNH TRANH** *(Câu 1 – 4)*
* **PHẦN 2: KIẾN TRÚC HỆ THỐNG, DỮ LIỆU & POSTGRESQL** *(Câu 5 – 8)*
* **PHẦN 3: BỘ NÃO AI AGENT, LLM & THUẬT TOÁN ĐỊNH TUYẾN** *(Câu 9 – 13)*
* **PHẦN 4: AN TOÀN HITL, ĐIỀU KHIỂN THIẾT BỊ & PHẦN CỨNG IOT** *(Câu 14 – 17)*
* **PHẦN 5: NGHIỆM THU KIỂM THỬ, HIỆU NĂNG & LỘ TRÌNH PHÁT TRIỂN** *(Câu 18 – 20)*

---

# PHẦN 1: SẢN PHẨM, THỊ TRƯỜNG & ĐỐI THỦ CẠNH TRANH

### ❓ CÂU 1: "Trên thị trường đã có AirVisual, Strava rồi, AirGuard AI có gì khác biệt mà họ chưa có?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"AirGuard AI là giải pháp đầu tiên kết nối thành một **Chu trình hành động khép kín (Closed-Loop Action)**, thay vì chỉ là bảng xem số thụ động như AirVisual hay chỉ đường 'mù bụi' như Strava."*
* 🔍 **Ý chính trả lời:**  
  1. **AirVisual / PAM Air:** Chỉ là bảng thông báo thụ động ở quy mô thành phố (5–10km). Cư dân thấy ô nhiễm rồi bất lực đóng app. AirGuard AI phân giải vi khí hậu siêu cục bộ từng 300m và hành động ngay.
  2. **Strava / Google Maps:** Mù tịt về chất lượng không khí, chỉ đường ngắn nhất nên vô tình dẫn runner chạy thẳng vào vùng bụi xe tải, và thường bắt chạy lùi đường cũ (Out-and-back). AirGuard AI dùng thuật toán 2-Leg Dijkstra né bụi, giảm 45% bụi hít vào và 0.0% lặp đường.
  3. **Hệ thống BMS tòa nhà:** Phải vận hành thủ công, lãng phí điện. AirGuard AI có Cổng HITL 1-click phản hồi 0.8s và tự ngắt 45 phút tiết kiệm 35% điện năng.

---

### ❓ CÂU 2: "Tại sao lại chọn địa bàn thực nghiệm là Vinhomes Ocean Park 1?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Vì đây là đại đô thị sinh thái 420 ha điển hình với 66 tòa chung cư, 30.000 dân và có sự biến thiên vi khí hậu siêu cục bộ cực đoan nhất Hà Nội."*
* 🔍 **Ý chính trả lời:**  
  1. **Sự tương phản vi khí hậu rõ rệt:** Mặt nước Hồ Ngọc Trai 24.5 ha và Biển hồ 6.1 ha có AQI rất sạch (30–35), nhưng chỉ cách 300m, trục đường thi công Sao Biển nồng độ bụi vọt lên AQI 155 do xe tải và đất cát.
  2. **Tập khách hàng lý tưởng:** Hàng chục ngàn cư dân có nhu cầu thể thao chạy bộ hàng ngày, tạo môi trường thực tế hoàn hảo để kiểm nghiệm giá trị bảo vệ sức khỏe.

---

### ❓ CÂU 3: "Mô hình kinh doanh (Business Model) của dự án là gì? Kiếm tiền từ đâu?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Chúng tôi kết hợp nguồn thu chính **B2B/B2G SaaS** từ Ban Quản Lý khu đô thị và nguồn thu phụ **B2C Subscription** từ cộng đồng người tập thể thao."*
* 🔍 **Ý chính trả lời:**  
  1. **B2B SaaS ($2,000 – $5,000 / tháng / khu đô thị):** Bán cho Ban Quản Lý các khu đô thị lớn (Vinhomes, Ecopark). Giá trị mang lại: Giảm chi phí điện năng thông gió ($12,000/tháng), cắt giảm 90% thời gian xử lý sự cố và tự động hóa hồ sơ kiểm toán ESG để đạt chứng chỉ Công trình Xanh LEED.
  2. **B2C Subscription ($2 / tháng ~ 49.000 VNĐ):** Dành cho runner và gia đình có con nhỏ để nhận cảnh báo theo bán kính nhà, đo liều lượng bụi tích lũy và đồng bộ đường chạy sạch lên Apple Watch/Garmin/Strava.

---

### ❓ CÂU 4: "Dự án giải quyết 3 nỗi đau chính nào của đô thị?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Giải quyết 3 nỗi đau: Runner tự đầu độc phổi khi chạy nhầm vào điểm nóng; Nhóm nhạy cảm thiếu khuyến nghị cá nhân hóa; và Ban Quản Lý lúng túng xử lý thủ công bằng Excel."*
* 🔍 **Ý chính trả lời:**  
  1. **Runner:** Tập thể dục nhưng vô tình hít phải hàng chục microgram bụi mịn độc hại vào phế nang.
  2. **Trẻ em / Người già:** Thiếu các cảnh báo sớm và hướng dẫn bảo vệ sức khỏe theo thể trạng.
  3. **Ban Quản Lý:** Mất 20–30 phút cho mỗi sự vụ ô nhiễm và hoàn toàn bị động trong việc điều khiển dập bụi.

---

# PHẦN 2: KIẾN TRÚC HỆ THỐNG, DỮ LIỆU & POSTGRESQL

### ❓ CÂU 5: "Kiến trúc 3 luồng dữ liệu khép kín hoạt động như thế nào?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Hệ thống phân tách triệt để 3 luồng: Luồng 1 thu thập dữ liệu IoT mỗi 15s; Luồng 2 phục vụ cư dân và AI định tuyến dưới 120ms; Luồng 3 điều khiển can thiệp vật lý HITL với phản hồi ACK 0.8s."*
* 🔍 **Ý chính trả lời:**  
  1. **Luồng 1 (Telemetry):** 5 Trạm IoT $\to$ Mosquitto MQTT (QoS 1) $\to$ Data Quality Gate (chặn stale >300s) $\to$ PostgreSQL 16 SoR (Index kép truy vấn <3ms).
  2. **Luồng 2 (Query & AI):** Cư dân $\to$ React 18 Leaflet GIS (Heatmap IDW 60x60) $\to$ FastAPI Core & Celery $\to$ LangGraph & 2-Leg Dijkstra (-45% bụi hít vào).
  3. **Luồng 3 (Action HITL):** Ô nhiễm vượt ngưỡng $\to$ Cổng HITL 1-click $\to$ Lệnh MQTT Dispatcher $\to$ Bật máy lọc 45 phút rồi tự ngắt bảo vệ thiết bị.

---

### ❓ CÂU 6: "PostgreSQL 16 lưu trữ những dữ liệu gì? Tại sao dùng PostgreSQL mà không dùng MongoDB?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"PostgreSQL 16 đóng vai trò là System of Record (SoR) duy nhất, đảm bảo tính toàn vẹn dữ liệu quan hệ chặt chẽ và lưu trữ bất biến phục vụ kiểm toán môi trường."*
* 🔍 **Ý chính trả lời:**  
  1. **5 Nhóm bảng dữ liệu:** Bảng trạm đo chuỗi thời gian (`measurements`), tài khoản người dùng (`users`), sự vụ cảnh báo (`predictive_warning_episodes`), cổng duyệt HITL (`approval_requests`), và nhật ký kiểm toán (`audit_logs`).
  2. **Lý do chọn PostgreSQL thay vì NoSQL:** Dữ liệu môi trường và thiết bị đô thị đòi hỏi ràng buộc vật lý khắt khe (Check Constraints chặn PM2.5 âm hoặc >500), khóa Idempotency chống duyệt đúp chuột, và đặc biệt là Trigger cấm sửa xóa lịch sử.

---

### ❓ CÂU 7: "Cơ sở dữ liệu có tự động xóa lịch sử lưu trữ không?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Không! Toàn bộ lịch sử đo đạc và kiểm toán được lưu trữ vĩnh viễn, đặc biệt bảng `audit_logs` có Trigger Pl/pgSQL cấm tuyệt đối mọi lệnh UPDATE và DELETE."*
* 🔍 **Ý chính trả lời:**  
  1. **Cơ chế Append-Only:** Bảng `audit_logs` cài đặt Trigger `prevent_audit_log_mutation()`. Bất kể ai chạy lệnh xóa sửa, Database sẽ ném ngoại lệ chặn đứng ngay lập tức để bảo vệ tính toàn vẹn pháp lý ESG.
  2. **Quy mô lưu trữ:** Với chu kỳ 15s, 5 trạm tạo ra ~10.5 triệu dòng/năm (~2GB/năm), ổ cứng máy chủ hoàn toàn lưu trữ thoải mái 5-10 năm liên tục. Khi mở rộng, chúng tôi áp dụng chiến lược nén dữ liệu (Data Rollup) theo chuẩn TimescaleDB chứ không xóa dữ liệu.

---

### ❓ CÂU 8: "MQTT là gì? Tại sao lại dùng Mosquitto MQTT thay vì HTTP thông thường?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"MQTT là giao thức truyền tin siêu nhẹ theo mô hình Pub/Sub dành riêng cho IoT, giúp tiết kiệm 90% dung lượng 4G và phản hồi điều khiển thiết bị tức thì trong 0.8 giây."*
* 🔍 **Ý chính trả lời:**  
  1. **Gói tin siêu nhẹ:** Header MQTT chỉ có 2 Bytes (so với HTTP hàng trăm bytes), giúp cảm biến chạy pin năng lượng mặt trời tiết kiệm điện năng tối đa.
  2. **Độ tin cậy QoS 1:** Bản tin phát đi bắt buộc phải có xác nhận `PUBACK`, đảm bảo 0% mất gói tin vi khí hậu kể cả khi sóng 4G chập chờn.
  3. **Điều khiển hai chiều:** Cho phép BQL phát lệnh dập bụi ngược xuống thiết bị mà không cần máy lọc phải có IP công cộng.

---

# PHẦN 3: BỘ NÃO AI AGENT, LLM & THUẬT TOÁN ĐỊNH TUYẾN

### ❓ CÂU 9: "LLM (Large Language Model) có tác dụng gì trong dự án này?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"LLM đóng vai trò là Nhạc trưởng NLU hiểu ngữ cảnh tự nhiên để điều phối 10 công cụ nghiệp vụ, và chuyển dịch số liệu khô khan thành lời khuyên sức khỏe nhân văn, cá nhân hóa."*
* 🔍 **Ý chính trả lời:**  
  1. **Những gì LLM KHÔNG làm:** LLM không tính AQI, không tìm đường chạy và không tự ý bật máy lọc (các việc này do toán học và thuật toán đồ thị làm).
  2. **Những gì LLM LÀM:** Bóc tách tham số từ câu nói đời thường của cư dân ("chiều nay 5h", "chạy 5km quanh hồ", "người nhạy cảm"), điều phối gọi đúng tool trong LangGraph, và chấp bút viết bản tóm tắt kiểm toán ESG hàng tuần.

---

### ❓ CÂU 10: "Làm sao đảm bảo AI không bịa đặt số liệu (Hallucination) khi đưa ra lời khuyên sức khỏe?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Chúng tôi áp dụng nguyên tắc 'Grounding trước Fluency' — 100% số liệu vi khí hậu phát ngôn ra đều bắt buộc phải đối chiếu chéo từ Database PostgreSQL."*
* 🔍 **Ý chính trả lời:**  
  1. **Cổng Grounding Policy Gate:** Mọi câu trả lời của LLM bị quét Regex bóc tách toàn bộ thực thể số. Nếu xuất hiện bất kỳ con số nào không nằm trong kết quả Tool Calling từ DB $\to$ Cổng lập tức hủy câu trả lời và thay bằng bản tin mẫu chuẩn từ DB.
  2. **Kết quả kiểm chứng:** Đạt **100.0% Grounding Accuracy** và **0.0% Environmental Hallucination** trên bộ 87 ca benchmark thực tế.

---

### ❓ CÂU 11: "Nếu mạng API OpenAI/Gemini bị lag hoặc mất kết nối thì hệ thống có bị sập không?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Không bao giờ! Hệ thống có Bộ chuyển mạch tiền định (Deterministic Fallback Switcher) kích hoạt trong < 500ms, cam kết 0% lỗi HTTP 5xx."*
* 🔍 **Ý chính trả lời:**  
  1. **Khóa Timeout 8.0 giây:** Nếu sau 8 giây API ngoài không phản hồi hoặc báo lỗi 429/500 $\to$ Luồng tự động ngắt kết nối với LLM.
  2. **Fallback nội bộ:** Bộ sinh câu tiền định cục bộ tự động lấy dữ liệu mới nhất từ trạm đo và trả lời cư dân trong **dưới 500 mili-giây**, đảm bảo trải nghiệm người dùng luôn thông suốt.

---

### ❓ CÂU 12: "Thuật toán định tuyến 2-Leg Penalized Dijkstra chạy thế nào? Có thật sự 0.0% lặp đường cũ không?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Thuật toán chia làm 2 chặng và phạt gấp 30 lần trọng số các cạnh đường chiều đi, ép cung đường về phải ôm trọn mặt hồ mới, đảm bảo khép kín tuần hoàn đúng 0.0% lặp đường cũ."*
* 🔍 **Ý chính trả lời:**  
  1. **Chặng 1 ($S \to W$):** Tìm đường ngắn nhất và sạch nhất đến điểm trung chuyển $W$ ven hồ.
  2. **Chặng 2 ($W \to S$):** Phạt 30 lần ($30\times$) tất cả các cạnh đã đi ở chặng 1 $\to$ Buộc thuật toán tìm lối đi mới ven hồ để quay về đích, triệt tiêu hoàn toàn nhược điểm bắt chạy lùi đường cũ của Google Maps.
  3. **Kiểm chứng hình học:** Đo đạc trên 30 kịch bản thực tế đạt khoảng cách khép kín $d = 0.0\text{ m}$ (100% kín) và tỷ lệ trùng lặp đúng 0.0%.

---

### ❓ CÂU 13: "Con số 'GIẢM 45% BỤI MỊN HÍT VÀO PHỔI' dựa vào đâu? Thực tế có thật không?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Hoàn toàn có thật! Con số này dựa trên mô hình phơi nhiễm tích phân y sinh học và được đo đạc thực nghiệm trên 4.280 điểm lấy mẫu phân đoạn 35m tại Ocean Park 1."*
* 🔍 **Ý chính trả lời:**  
  1. **Cơ sở y sinh học:** Khi chạy bộ, thể tích thông khí phổi tăng vọt lên 50–60 lít/phút. Hệ thống tích phân nồng độ bụi dọc theo từng phân đoạn 35m dựa theo Pace chạy: $M_{\text{inhaled}} = \int C(x(t)) \cdot V_E \, dt$.
  2. **Thực tế địa bàn:** Trục đường Đa Tốn chịu bụi xe tải nồng độ $58.2\text{ }\mu g/m^3$ (hít 105 µg bụi), trong khi mặt hồ Ngọc Trai 24.5 ha có nồng độ chỉ $27.6\text{ }\mu g/m^3$ (chỉ hít 49 µg bụi).
  3. **Kết quả:** Runner chỉ cần chạy thêm 310m (+6.2% cự ly) qua lối công viên ven hồ nhưng **né được 56 microgram bụi độc hại — giảm từ 35.4% đến 52.6% (trung bình ~45%) lượng bụi chui vào phế nang phổi**!

---

# PHẦN 4: AN TOÀN HITL, ĐIỀU KHIỂN THIẾT BỊ & PHẦN CỨNG IOT

### ❓ CÂU 14: "Tại sao không để AI tự động bật máy lọc không khí mà phải qua Cổng HITL (Human-in-the-loop)?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Vì điều khiển thiết bị vật lý công suất lớn liên quan trực tiếp đến an toàn điện, tiếng ồn đô thị và phòng chống cháy nổ, nên quyền quyết định tối cao bắt buộc phải thuộc về con người."*
* 🔍 **Ý chính trả lời:**  
  1. **Phân định ranh giới:** AI chỉ làm nhiệm vụ phát hiện ô nhiễm trong 0.007ms và chuẩn bị sẵn Thẻ bằng chứng (Evidence Card).
  2. **Quyền hạn Trưởng ca:** Ban Quản Lý chỉ mất 1-Click để phê duyệt trên giao diện web. Cổng có khóa Idempotency chống bấm trùng và ghi vết kiểm toán vĩnh viễn, loại trừ rủi ro AI bị lỗi phần mềm tự ý kích hoạt thiết bị bừa bãi.

---

### ❓ CÂU 15: "Độ trễ từ lúc BQL bấm phê duyệt đến khi máy lọc nhận lệnh là bao lâu?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Đạt kỷ lục **0.8 giây** nhờ đường truyền chuyên dụng Mosquitto MQTT QoS 1 và giao diện Fast-Polling 800ms."*
* 🔍 **Ý chính trả lời:**  
  Ngay khi bấm duyệt, lệnh được đẩy thẳng vào MQTT Broker, thiết bị ngoại vi nhận lệnh và gửi lại gói xác nhận `ACK`. Đồng hồ trên giao diện web lập tức chuyển sang màu xanh và đếm ngược 45 phút trong chưa đầy 1 giây.

---

### ❓ CÂU 16: "Cơ chế tiết kiệm 35% điện năng hoạt động như thế nào?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Nhờ cơ chế dập bụi thông minh tự động ngắt sau 45 phút, triệt tiêu hoàn toàn tình trạng máy lọc chạy quên suốt đêm của các hệ thống BMS cũ."*
* 🔍 **Ý chính trả lời:**  
  1. **Thực trạng cũ:** Quạt thông gió và máy lọc chạy theo hẹn giờ cố định 16 giờ/ngày, tiêu tốn điện vô ích kể cả khi không khí đã sạch.
  2. **Giải pháp AirGuard AI:** Chỉ kích hoạt khi có ô nhiễm và tự động ngắt sau 45 phút. Cắt giảm 5 giờ chạy lãng phí mỗi ngày, giúp 66 tòa chung cư **tiết kiệm ~118.800 kWh/tháng (~300 triệu đồng tiền điện/tháng)**.

---

### ❓ CÂU 17: "Nếu ngày mai triển khai trên thiết bị đo phần cứng thật ngoài cột đèn thì làm như thế nào?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Hệ thống phần mềm và AI Agent của chúng tôi **giữ nguyên 100% không cần sửa một dòng code nào**, vì kiến trúc đã được thiết kế theo chuẩn Event-Driven qua MQTT Broker."*
* 🔍 **Ý chính trả lời:**  
  1. **Cấu hình phần cứng:** Mạch vi điều khiển ESP32-S3 + Cảm biến bụi laser Sensirion SPS30 + Cảm biến CO2 hồng ngoại Senseair S8 + Pin mặt trời 25W và pin LiFePO4 chạy tự hành 5 ngày mưa.
  2. **Giao tiếp:** Kết nối qua 4G LTE hoặc LoRaWAN tầm xa (bán kính 3–5km), nạp firmware publish đúng cấu trúc JSON sẵn có vào Mosquitto MQTT.
  3. **Hiệu chuẩn độ ẩm:** Tích hợp công thức bù độ ẩm sấy hạt bụi $PM_{\text{corrected}}$ để chống đo ảo khi trời mưa phùn sương mù.

---

# PHẦN 5: NGHIỆM THU KIỂM THỬ, HIỆU NĂNG & LỘ TRÌNH PHÁT TRIỂN

### ❓ CÂU 18: "Hệ thống đã trải qua những bài kiểm thử tự động nào? Uptime ra sao?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Dự án đã vượt qua **153 trên 153 bài kiểm thử tự động (100% Pass)** và đang chạy ổn định với Uptime 99.9% trên hạ tầng đám mây Microsoft Azure VM."*
* 🔍 **Ý chính trả lời:**  
  1. **Bộ 153 Tests gồm:** 66 Unit Tests Backend, 30 Tests định tuyến 2-Leg Dijkstra & khép kín hình học OSM, 25 Tests máy trạng thái HITL & MQTT Dispatcher, 32 Tests tích hợp End-to-End API & RBAC.
  2. **Chạy live thật:** Đã đóng gói trong 8 Docker containers cô lập, bảo mật SSL HTTPS tự động qua Caddy Reverse Proxy tại địa chỉ `airguard-074-app.indonesiacentral.cloudapp.azure.com`.

---

### ❓ CÂU 19: "Chi phí vận hành đám mây (Cloud Cost) hiện tại là bao nhiêu?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Nhờ tối ưu hóa kiến trúc và độ trễ API P95 < 120ms, toàn bộ hệ thống phục vụ đại đô thị 30.000 dân chỉ tốn **khoảng $35 – $40 / tháng** trên Azure Cloud."*
* 🔍 **Ý chính trả lời:**  
  Hệ thống chạy mượt mà trên gói **Azure VM Standard B2ms (2 vCPUs, 8GB RAM)**. Các tác vụ nặng được xử lý bất đồng bộ qua Celery và tối ưu chỉ mục Database, giúp tiết kiệm chi phí hạ tầng tối đa cho chủ đầu tư.

---

### ❓ CÂU 20: "Lộ trình phát triển tiếp theo của AirGuard AI là gì?"
* 🎯 **Câu chốt hạ (One-Liner):**  
  *"Lộ trình 3 giai đoạn lấy cư dân làm trung tâm: Ra mắt Mobile App & Zalo Mini App; Liên động Smart Home & Chạy Xanh Tích Điểm; và từng bước nhân rộng ra toàn bộ chuỗi đại đô thị thông minh toàn quốc."*
* 🔍 **Ý chính trả lời:**  
  1. **Giai đoạn 1 (Q4/2026):** Phát hành AirGuard Mobile App (iOS/Android) và Zalo Mini App nhận thông báo đẩy GPS, đồng bộ 1-click lên Garmin, Apple Watch, Strava kèm cảnh báo rung an toàn.
  2. **Giai đoạn 2 (Q1/2027):** Liên động Căn hộ thông minh (Smart Home) tự động nhắc đóng cửa sổ khi ngoài trời ô nhiễm; mở Thử thách "Chạy Xanh Tích Điểm" đổi voucher tiện ích đô thị (vé bơi, phí gửi xe, cà phê ven hồ).
  3. **Giai đoạn 3 (2027+):** Nhân rộng nền tảng ra toàn bộ hệ thống đại đô thị thông minh Vinhomes (Smart City, Grand Park), Ecopark và các đô thị lớn tại Việt Nam.

---

💡 **LỜI KHUYÊN DÀNH CHO BẠN KHI ĐỨNG TRÊN SÂN KHẤU:**  
* **Khi giám khảo hỏi:** Hãy giữ bình tĩnh, mỉm cười và gật đầu.  
* **Bắt đầu bằng:** *"Cảm ơn câu hỏi rất thực tế và sâu sắc của Thầy/Cô/Giám khảo..."*  
* **Bắn ngay câu One-Liner trong 5 giây đầu** để khẳng định vị thế làm chủ công nghệ của nhóm P-074!

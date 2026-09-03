# 🎙️ KỊCH BẢN LỜI THOẠI THUYẾT TRÌNH 5 PHÚT (TELEPROMPTER SCRIPT)
# AIRGUARD AI — NHÓM P-074 (TỨ KỴ SĨ KHẢI HUYỀN)

> **Hướng dẫn sử dụng:**  
> Bản tài liệu này **chỉ gồm duy nhất lời thoại nói liên tục** từ Slide 1 đến Slide 9, được viết nối tiếp nhau như một dòng chảy tự nhiên.  
> Các ký hiệu trong ngoặc vuông `[ ... ]` là chỉ dẫn ngắt nghỉ và ngữ điệu để bạn làm chủ nhịp thở và sân khấu.  
> **Tổng thời lượng:** Đúng 5 phút (300 giây).

---

### [ SLIDE 1: HOOK — MỞ ĐẦU ẤN TƯỢNG | 0:00 – 0:30 ]

"Kính chào quý Ban giám khảo, các Mentor và toàn thể Hội đồng!

Cho phép tôi được bắt đầu bằng một nghịch lý thực tế: **Tại sao hàng chục ngàn cư dân chạy bộ để nâng cao sức khỏe tại các đại đô thị hiện đại lại đang vô tình hít phải hàng chục microgram bụi mịn độc hại vào sâu phế nang mỗi ngày?** `[Dừng 1 giây để tạo khoảng lặng]`

Chúng tôi là **Nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền**.  
Và câu trả lời của chúng tôi chính là **AirGuard AI** — Hệ sinh thái AI Agent toàn diện: từ giám sát vi khí hậu thời gian thực, tự động vẽ lộ trình thể thao sạch bụi khép kín, đến liên động điều khiển hệ thống dập bụi thông minh tại đại đô thị Vinhomes Ocean Park 1!

Nhưng để hiểu tại sao cư dân lại rơi vào nghịch lý sức khỏe đó, chúng ta hãy cùng nhìn vào thực trạng dữ liệu môi trường tại các đại đô thị hiện nay..." `[Chuyển Slide 2]`

---

### [ SLIDE 2: PROBLEM — THỰC TRẠNG & NỖI ĐAU ĐÔ THỊ | 0:30 – 1:10 ]

"Thưa quý vị, các khu đô thị hiện nay dù đã lắp đặt cảm biến, nhưng **dữ liệu hoàn toàn rời rạc**. `[Nhấn mạnh]`

Tại Vinhomes Ocean Park 1, chất lượng không khí biến thiên siêu cục bộ: Cùng một thời điểm, mặt nước Biển Hồ có chỉ số rất trong lành — **AQI chỉ 35**, nhưng chỉ cách đó 300 mét, trục đường thi công Sao Biển nồng độ bụi PM2.5 lại tăng vọt lên mức Nguy hại — **AQI 155** do xe tải và đất cát thi công!

Thực trạng này dẫn đến 3 nỗi đau nhức nhối:  
* **Thứ nhất, người tập thể thao**: Mù mờ thông tin vi khí hậu, vô tình biến buổi rèn luyện sức khỏe thành buổi 'hít bụi mịn độc hại'.  
* **Thứ hai, trẻ em, người cao tuổi, người bệnh hô hấp**: Hoàn toàn thiếu các cảnh báo sớm và khuyến nghị bảo vệ cá nhân hóa theo thể trạng.  
* **Và thứ ba, Ban Quản Lý đô thị**: Lúng túng với các bảng báo cáo Excel thủ công, mất 20 đến 30 phút cho mỗi sự vụ ô nhiễm và hoàn toàn bị động trong việc kích hoạt hệ thống dập bụi.

Đứng trước 3 nỗi đau đó, chúng tôi không chỉ tạo ra một bảng số liệu thông thường, mà đã xây dựng một hệ sinh thái hành động khép kín từ cảm biến đến can thiệp thực tế..." `[Chuyển Slide 3]`

---

### [ SLIDE 3: SOLUTION — TỔNG QUAN GIẢI PHÁP & 10 USE CASES | 1:10 – 1:45 ]

"AirGuard AI giải quyết triệt để bài toán trên bằng cấu trúc 2 không gian làm việc chuyên biệt và 10 ca sử dụng khép kín:

* **Với Cư dân**: Chúng tôi cung cấp Bản đồ nhiệt vi khí hậu thời gian thực, dự báo xu hướng ô nhiễm chuỗi 1 đến 24 giờ, thiết lập hồ sơ sức khỏe cá nhân hóa, và đặc biệt là **Trợ lý AI đàm thoại tự động vẽ tuyến đường chạy bộ sạch bụi khép kín quanh hồ**.
* **Với Ban Quản Lý**: Cung cấp Cổng phê duyệt HITL 1-click thẩm định Thẻ bằng chứng quan trắc, điều khiển máy lọc không khí dập bụi phản hồi tức thì, và tự động hóa 100% báo cáo kiểm toán môi trường đạt chuẩn quốc tế.

Để hiện thực hóa một hệ sinh thái mạnh mẽ như vậy, đằng sau đó là một nền tảng kiến trúc Monorepo 5 phân tầng với 3 luồng dữ liệu cực kỳ chặt chẽ..." `[Chuyển Slide 4]`

---

### [ SLIDE 4: KIẾN TRÚC HỆ THỐNG: 3 LUỒNG DỮ LIỆU & TECH STACK | 1:45 – 2:25 ]

"Về mặt kiến trúc, AirGuard AI được xây dựng theo chuẩn Monorepo 5 phân tầng công nghiệp với 3 luồng dữ liệu vận hành nhịp nhàng:

* **Luồng 1 — Telemetry Stream**: Mỗi 15 giây, 5 trạm quan trắc đẩy dữ liệu 4 chỉ số qua **Mosquitto MQTT Broker**. Tầng Ingestion áp dụng **Data Quality Gate** với cơ chế Fail-Closed: tự động loại bỏ dữ liệu sai lệch hoặc trạm mất tín hiệu quá 300 giây trước khi ghi vào cơ sở dữ liệu **PostgreSQL 16 System of Record**.
* **Luồng 2 — Query & AI Stream**: Giao diện **React 18 và Leaflet GIS** gửi truy vấn đến **FastAPI Core Backend**, tính toán bản đồ nhiệt IDW và phân tích lộ trình thông minh với độ trễ phản hồi **dưới 120ms**.
* **Luồng 3 — Action & Audit Stream**: Lệnh phê duyệt từ Cổng HITL được đẩy qua MQTT đến thiết bị dập bụi và cập nhật giao diện trong **0.8 giây**, đồng thời ghi vết kiểm toán bất biến vào bảng `audit_logs`.
* Toàn bộ hệ thống được đóng gói trong **8 Docker containers cô lập** và bảo mật HTTPS qua Reverse Proxy Caddy trên đám mây Azure.

Không chỉ sở hữu một bộ khung kiến trúc vững chắc, điều tạo nên bước đột phá vượt trội của AirGuard AI nằm ở 4 kỹ thuật cốt lõi độc quyền..." `[Chuyển Slide 5]`

---

### [ SLIDE 5: KỸ THUẬT ĐỘT PHÁ CỐT LÕI | 2:25 – 3:05 ]

"Hệ thống khẳng định năng lực công nghệ vượt trội thông qua **4 kỹ thuật đột phá cốt lõi**: `[Tự tin, hào hứng]`

* **1. Động cơ định tuyến thể thao 2-Leg Penalized Dijkstra trên đồ thị đường thực OpenStreetMap hơn 10,500 cạnh**: Khác với các ứng dụng thông thường bắt runner quay đầu chạy lùi đường cũ, thuật toán của chúng tôi phạt 30 lần trọng số cạnh chiều đi, ép lộ trình ôm trọn cung đường mới ven hồ, sinh ra chu trình chạy tuần hoàn **đúng 0.0% lặp đường cũ** và **giúp giảm tới 45% lượng bụi mịn hít vào phổi**!
* **2. Cơ chế AI Grounded Zero-Hallucination**: Áp dụng nguyên tắc 'Grounding trước Fluency' — 100% số liệu vi khí hậu phát ngôn ra đều bắt buộc phải đối chiếu chéo từ Database. Nếu mạng LLM bên ngoài bị nghẽn quá 8 giây, bộ chuyển mạch tiền định sẽ kích hoạt trong 500ms, đảm bảo **0% lỗi sập hệ thống**.
* **3. Lớp phủ nhiệt IDW ma trận 60x60**: Tự động phát hiện và làm nổi bật 'hành lang không khí sạch' quanh mặt nước 24.5 ha kết hợp vector hướng gió thực tế.
* **4. Cổng an toàn HITL máy chủ**: Ngăn ngừa mệt mỏi cảnh báo với Cooldown 15 phút, và điều khiển máy lọc không khí nhận phản hồi ACK trong đúng **0.8 giây**!

Và để chứng minh toàn bộ kiến trúc và các kỹ thuật đột phá này vận hành mượt mà như thế nào trong thực tế, ngay sau đây, kính mời quý Hội đồng cùng tôi trải nghiệm trực tiếp trên hệ thống đang chạy live trên Azure Cloud..." `[Chuyển Slide 6 & Mở Tab Trình Duyệt]`

---

### [ SLIDE 6: LIVE PRODUCT DEMO — TRẢI NGHIỆM THỰC TẾ | 3:05 – 3:55 ]

*(Người trình bày chuyển nhanh sang tab trình duyệt)*

"Kính mời quý Hội đồng cùng nhìn lên màn hình:

* **1. Ở vai trò Cư dân**: Bản đồ nhiệt IDW thời gian thực hiển thị sắc nét hành lang không khí trong lành quanh hồ Ngọc Trai với màu xanh mát mắt.
* **2. Bây giờ tôi mở Trợ lý AI và chat**: *'Gợi ý đường chạy 5km quanh hồ cho người nhạy cảm'*. `[Thao tác click chuột]` Chỉ sau 1 giây, AI gọi động cơ 2-Leg Dijkstra, lập tức vẽ đường chạy Polyline màu xanh tuyệt đẹp ôm trọn mặt hồ, khẳng định độ trùng lặp đường cũ là **đúng 0%** và lượng bụi hít vào chỉ **4.8 microgram** — giảm 45% so với chạy ngoài đường lớn!
* **3. Chuyển sang vai trò Ban Quản Lý**: Khi trạm Sao Biển bị ô nhiễm, tôi mở Cổng HITL, kiểm tra Thẻ bằng chứng quan trắc và bấm **[Phê duyệt]**. `[Thao tác click chuột]` Lập tức lệnh MQTT truyền đi, trạng thái chuyển sang xanh và đồng hồ 45 phút đếm ngược chỉ trong **0.8 giây**!

Một nền tảng công nghệ hoàn thiện như vậy mang lại những giá trị định lượng và tiềm năng kinh doanh cụ thể nào? Hãy cùng xem ở slide tiếp theo..." `[Quay lại Slide 7]`

---

### [ SLIDE 7: TÁC ĐỘNG ĐỊNH LƯỢNG & 3 CHỈ SỐ VÀNG | 3:55 – 4:35 ]

"AirGuard AI mang lại **3 giá trị định lượng thiết thực đã được kiểm chứng bằng số liệu khoa học**:

* **Thứ nhất, 0.0% Trùng Lặp & Giảm 45% Bụi Hít Vào**: Thuật toán 2-Leg Dijkstra trên OSM giúp runner né được 18 đến 25 microgram bụi mịn độc hại mỗi buổi tập mà không bao giờ phải chạy lùi đường cũ.
* **Thứ hai, Giảm 90% Thời Gian & Phản Hồi Thiết Bị 0.8 Giây**: Rút ngắn thời gian xử lý sự cố ô nhiễm của Ban Quản Lý từ 25 phút xuống dưới 2 phút qua Cổng HITL 1-click, đồng thời nhận bản tin ACK thiết bị dập bụi trong đúng 0.8 giây.
* **Thứ ba, Tiết Kiệm 35% Điện Năng & 100% Tự Động Hóa Báo Cáo ESG**: Cơ chế tự ngắt máy lọc sau 45 phút tiết kiệm khoảng 118,800 kWh mỗi tháng — tương đương gần 300 triệu đồng tiền điện cho 66 tòa chung cư, đồng thời tự động hóa toàn bộ báo cáo kiểm toán môi trường đạt chuẩn quốc tế.
* **Về Mức Độ Hoàn Thiện & Kinh Doanh**: Dự án đã vượt qua **153 trên 153 bài kiểm thử tự động**, sẵn sàng thương mại hóa theo mô hình **B2B SaaS** cho các chủ đầu tư đô thị thông minh kết hợp gói **B2C** cho hàng ngàn runner.

Để hiện thực hóa một khối lượng công việc đồ sộ như vậy, ai là những người đứng sau dự án?..." `[Chuyển Slide 8]`

---

### [ SLIDE 8: ĐỘI NGŨ PHÁT TRIỂN — NHÓM P-074 | 4:35 – 4:50 ]

"Đằng sau sự hoàn thiện vượt bậc của AirGuard AI là sự nỗ lực kỷ luật và đồng bộ của 4 thành viên nhóm P-074 — Tứ Kỵ Sĩ Khải Huyền:

* Tôi — **Lê Tuấn Cảnh**: Phụ trách Quản trị dự án, Kiến trúc Monorepo và Backend FastAPI.
* Bạn **Hán Vũ Long**: Phụ trách Tích hợp hệ thống và Pipeline IoT vi khí hậu.
* Bạn **Hoàng Lê Minh**: Phụ trách Mô hình AI Agent LangGraph và Động cơ định tuyến 2-Leg OSM.
* Và bạn **Phạm Thế Dũng**: Phụ trách Giao diện người dùng React Leaflet GIS và Bộ kiểm thử tự động 153 tests.

Và với nền tảng vững chắc đó, tầm nhìn tương lai hướng tới cư dân của chúng tôi là gì?..." `[Chuyển Slide 9]`

---

### [ SLIDE 9: ĐỊNH HƯỚNG CƯ DÂN & LỜI CẢM ƠN | 4:50 – 5:00 ]

"Trong giai đoạn tới, chúng tôi tập trung tối đa vào trải nghiệm người dùng:

* **Đầu tiên là ra mắt Mobile App và Zalo Mini App**, cho phép cư dân theo dõi vi khí hậu mọi lúc mọi nơi và đồng bộ tuyến chạy sạch trực tiếp lên **Garmin, Apple Watch, Strava** với cảnh báo rung an toàn.
* **Tiếp theo là liên động Nhà Thông Minh Smart Home** tự động nhắc đóng cửa sổ, đồng thời mở tính năng **'Chạy Xanh Tích Điểm'** đổi voucher tiện ích đô thị.
* Và từng bước nhân rộng mô hình ra toàn bộ các đại đô thị thông minh tại Việt Nam!

Chúng tôi rất mong muốn nhận được sự đồng hành, cố vấn từ Ban giám khảo và các nhà đầu tư để đưa AirGuard AI phục vụ hàng triệu cư dân đô thị!

**Xin chân thành cảm ơn quý Hội đồng! Toàn đội chúng tôi rất sẵn sàng cho phiên Q&A!**"

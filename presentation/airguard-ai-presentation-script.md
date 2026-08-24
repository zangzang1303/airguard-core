# AirGuard AI — Kịch bản thuyết trình

**Thông điệp chính:** AirGuard AI biến dữ liệu môi trường mô phỏng thành thông tin dễ hiểu, cảnh báo có kiểm soát và hỗ trợ ra quyết định minh bạch cho khu vực Vinhomes Ocean Park 1.

**Thời lượng đề xuất:** 7–9 phút · **Số slide:** 9

---

## Slide 1 — AirGuard AI: Quan sát môi trường, hỗ trợ quyết định an toàn

### Nội dung trên slide

AirGuard AI  
MVP giám sát chất lượng môi trường tại Vinhomes Ocean Park 1

**5 trạm mô phỏng · Dashboard AQI-first · AI Agent có kiểm soát**

### Lời thoại

“Nhóm chúng em xây dựng AirGuard AI, một MVP giúp quan sát và diễn giải chất lượng môi trường theo khu vực tại Vinhomes Ocean Park 1. Mục tiêu không phải thay thế trạm quan trắc chính thức, mà là minh họa một hệ thống dữ liệu xuyên suốt: từ thu thập, hiển thị, cảnh báo đến hỗ trợ con người ra quyết định.”

---

## Slide 2 — Bài toán: Dữ liệu môi trường khó chuyển thành hành động đúng lúc

### Nội dung trên slide

Người dùng cần trả lời nhanh ba câu hỏi:

1. Khu vực nào đang cần chú ý?
2. Chỉ số có còn mới và đáng tin cậy không?
3. Tôi nên làm gì, và ai chịu trách nhiệm với hành động đó?

**Nhóm người dùng:** cư dân, người nhạy cảm, người tập thể thao ngoài trời, quản lý vận hành.

### Lời thoại

“Vấn đề không chỉ là có số PM2.5 hay CO2. Người dùng cần biết trạm nào cần chú ý, dữ liệu đó có còn mới hay không, và khi có nguy cơ thì hành động nào là phù hợp. Với quản lý, một cảnh báo hay lệnh thiết bị cần có bằng chứng và người chịu trách nhiệm; không thể để AI tự quyết.”

---

## Slide 3 — Giải pháp: Một luồng dữ liệu xuyên suốt, từ sensor đến người ra quyết định

### Nội dung trên slide

**Sensor simulator**  →  **MQTT + kiểm tra dữ liệu**  →  **PostgreSQL**  →  **FastAPI**  →  **Dashboard & AI Agent**

- 5 trạm S01–S05 phát dữ liệu PM2.5, CO2, tiếng ồn và nhiệt độ.
- Backend là nguồn dữ liệu chính; frontend không đọc MQTT hay cơ sở dữ liệu trực tiếp.
- Dữ liệu invalid, stale hoặc station offline bị chặn trước khi đi xuống các chức năng sau.

### Lời thoại

“Giải pháp được thiết kế theo một pipeline rõ ràng. Dữ liệu từ năm trạm mô phỏng đi qua MQTT, được kiểm tra chất lượng, lưu vào PostgreSQL và cung cấp qua FastAPI. Dashboard và Agent chỉ sử dụng kết quả từ backend. Điểm quan trọng là dữ liệu lỗi, cũ hoặc trạm offline sẽ không được dùng để tạo current value, dự báo, cảnh báo hay khuyến nghị.”

---

## Slide 4 — Giá trị người dùng: Thấy được tình trạng, xu hướng và cảnh báo theo từng khu vực

### Nội dung trên slide

**Dashboard AQI-first**

- Bản đồ 5 trạm và trạng thái freshness.
- AQI tổng quan; PM2.5, CO2, tiếng ồn, nhiệt độ để xem chi tiết.
- Lịch sử và dự báo ngắn hạn 1–3 giờ.
- Cảnh báo theo rule cho nhiều chỉ số và trạng thái offline.

**Thông điệp trung thực:** dữ liệu trong MVP là dữ liệu simulator, không phải số liệu quan trắc được chứng nhận.

### Lời thoại

“Trên dashboard, người dùng bắt đầu từ AQI để có bức tranh nhanh, sau đó có thể xem các chỉ số thành phần và trạng thái freshness. Hệ thống có lịch sử, dự báo ngắn hạn và cảnh báo theo rule. Chúng em chủ động gắn nhãn simulator để tránh người dùng hiểu sai đây là dữ liệu quan trắc chính thức.”

---

## Slide 5 — AI hữu ích khi được grounding và có ranh giới rõ ràng

### Nội dung trên slide

AI Agent có thể:

- Trả lời hiện trạng, so sánh trạm, dự báo và cảnh báo.
- Diễn giải theo hồ sơ người dùng: bình thường, nhạy cảm, tập thể thao ngoài trời.
- Đề xuất cảnh báo với bằng chứng.

AI Agent không được:

- Tự tạo số liệu, ngưỡng hay cảnh báo.
- Truy cập trực tiếp PostgreSQL/MQTT.
- Tự phê duyệt đề xuất hoặc gửi lệnh thiết bị.

### Lời thoại

“Đây là phần AI nhưng trọng tâm không phải là nói trôi chảy. Agent chỉ trả lời từ tool result của cùng một request; nếu tool lỗi hoặc thiếu dữ liệu, Agent phải nói rõ là chưa đủ dữ liệu. Agent có thể đưa ra đề xuất, nhưng không có quyền phê duyệt hay điều khiển thiết bị.”

---

## Slide 6 — Human-in-the-Loop biến khuyến nghị thành hành động có trách nhiệm

### Nội dung trên slide

**Alert có dữ liệu hợp lệ**  →  **Agent tạo proposal pending**  →  **Manager approve / reject**  →  **Audit & device simulator**

- Chỉ Manager được phê duyệt hoặc từ chối.
- Mọi bước quan trọng có audit record và correlation ID.
- Chỉ sau khi được duyệt, dispatcher mới được phát command; ACK simulator được đối chiếu theo command ID.

### Lời thoại

“Để tránh rủi ro tự động hóa quá mức, AirGuard AI dùng Human-in-the-Loop. Agent chỉ tạo proposal ở trạng thái chờ. Manager là người phê duyệt hoặc từ chối, và toàn bộ luồng được lưu audit. Đây là ranh giới quan trọng giữa ‘AI hỗ trợ’ và ‘AI tự hành động’.”

---

## Slide 7 — Metrics: Quy mô MVP nhỏ nhưng phản hồi lõi đủ nhanh cho demo

### Nội dung trên slide

**Phạm vi hệ thống**

- **5** trạm mô phỏng · **4** chỉ số/trạm = **20** luồng chỉ số cần quan sát.
- Dashboard polling: **30 giây** · Simulator publish: **30 giây**.

**Kết quả microbenchmark cục bộ**

- MQTT validation: p95 **0,010 ms** · khoảng **98.069 message/giây**.
- Alert engine: kiểm tra **5 rule** trong dưới **0,001 ms** ở p95.
- Heatmap AQI: **468** điểm lưới, p95 **4,88 ms**.

*Đo cục bộ ngày 24/08/2026; đo xử lý trong tiến trình, chưa bao gồm broker, database và network.*

### Lời thoại

“Về metric, MVP đang theo dõi năm trạm với bốn chỉ số mỗi trạm, tương đương 20 luồng chỉ số. Nhóm đã tự đo hiệu năng xử lý cục bộ: validate MQTT đạt p95 0,010 mili-giây, và dựng heatmap 468 điểm đạt p95 4,88 mili-giây. Đây là microbenchmark, nên chúng em không dùng nó để khẳng định độ trễ end-to-end; tuy nhiên nó cho thấy phần tính toán lõi không phải nút thắt cho quy mô demo.”

---

## Slide 8 — Tính khả thi: MVP đã có các thành phần lõi và có thể demo end-to-end

### Nội dung trên slide

**Đã có trong MVP**

- 5 trạm simulator → MQTT → database → API → dashboard.
- Rule engine cho cảnh báo đa chỉ số.
- Forecast baseline 1–3 giờ từ dữ liệu fresh.
- Agent grounded, deterministic fallback khi provider lỗi.
- Proposal, phê duyệt, audit và device simulator.

**Cách kiểm chứng:** demo được luồng normal, spike, dữ liệu stale/duplicate, Agent thiếu dữ liệu và approval/reject.

### Lời thoại

“Tính khả thi không chỉ nằm ở mock UI. Các thành phần lõi đã có pipeline end-to-end và runbook demo. Chúng em cũng kiểm thử các tình huống lỗi: dữ liệu stale, duplicate, trạm im lặng, Agent thiếu dữ liệu và các nhánh phê duyệt hoặc từ chối.”

---

## Slide 9 — Định hướng: Từ MVP minh bạch đến hệ thống sẵn sàng mở rộng

### Nội dung trên slide

**Ngắn hạn**

- Xác nhận ngưỡng cảnh báo, severity, tọa độ trạm và vai trò Manager.
- Hoàn thiện dữ liệu thời tiết, notification và worker bất đồng bộ.

**Trung hạn**

- Tích hợp sensor thật và xác thực dữ liệu thực địa.
- Nâng forecast từ baseline lên mô hình được đánh giá/backtest.
- Bổ sung authentication/RBAC production và observability.

**Kết luận:** Mở rộng trên nền tảng có kiểm soát dữ liệu, minh bạch AI và trách nhiệm con người.

### Lời thoại

“Bước tiếp theo không phải là thêm thật nhiều tính năng AI. Trước hết, chúng em cần chốt rule và nguồn dữ liệu thực với mentor hoặc vận hành. Sau đó mới tích hợp sensor thật, đánh giá mô hình dự báo và hoàn thiện xác thực production. Nền tảng hiện tại giúp các bước đó có thể mở rộng an toàn, vì dữ liệu, AI và quyền quyết định đã được tách rõ.”

---

## Gợi ý thiết kế slide

- Phong cách tối giản: nền trắng/xám nhạt, điểm nhấn xanh dương nhạt.
- Mỗi slide chỉ giữ một thông điệp chính; dùng chữ lớn, ít bullet.
- Slide 3 có thể dùng ảnh `image/Kiến trúc tổng thể.png`; slide 6 dùng `image/Luồng cảnh báo và phê duyệt.png`.
- Không trình bày chỉ số simulator như số liệu môi trường thật; luôn giữ nhãn “MVP / simulator”.

## Nguồn nội bộ

- `README.md`
- `specs/product-vision.md`
- `docs/demo-runbook.md`
- `AGENTS.md`
- Phép đo cục bộ: `eval/measure_operational_latency.py`, thực hiện ngày 24/08/2026

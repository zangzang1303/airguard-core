# Prompt thiết kế từng slide — AirGuard AI

Sao chép **mỗi khối prompt riêng biệt** vào công cụ thiết kế Google Slides. Công cụ chỉ cần tạo đúng **một slide** cho mỗi prompt.

---

## Prompt Slide 1 — Trang mở đầu

```text
Thiết kế đúng 1 slide mở đầu, tỉ lệ 16:9, bằng tiếng Việt cho dự án AirGuard AI.

Phong cách thống nhất: tối giản, hiện đại, mang cảm giác công nghệ môi trường đáng tin cậy; nền trắng; chữ đen và xám đậm; điểm nhấn xanh dương #3D8DFF và xanh nhạt #6DCBF4; font Aptos, Arial hoặc sans-serif tương đương; không gradient, không 3D, không dùng ảnh stock sáo rỗng. Giữ nhiều khoảng thở, tiêu đề lớn, căn trái.

Nội dung bắt buộc:
- Nhãn nhỏ phía trên: AIRGUARD AI
- Tiêu đề lớn: Quan sát môi trường, hỗ trợ quyết định an toàn
- Phụ đề: MVP giám sát chất lượng môi trường tại Vinhomes Ocean Park 1
- Dòng giá trị: 5 trạm mô phỏng • Dashboard AQI-first • AI Agent có kiểm soát
- Chú thích nhỏ cuối slide: Dữ liệu MVP từ simulator — không phải quan trắc được chứng nhận.

Bố cục: tiêu đề chiếm vùng trung tâm bên trái; dùng một đường kẻ xanh mảnh làm điểm nhấn; không thêm nội dung ngoài yêu cầu. Không tự tạo số liệu hoặc logo mới.
```

---

## Prompt Slide 2 — Bài toán

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Bài toán: dữ liệu chưa đủ để hành động đúng lúc”.

Phong cách: nền trắng, chữ đen/xám, điểm nhấn xanh #3D8DFF, font sans-serif; tối giản, sạch, dễ đọc; không gradient, không 3D. Footer nhỏ: “AirGuard AI • MVP simulator”.

Thông điệp phụ: Người dùng cần câu trả lời nhanh, có ngữ cảnh và có trách nhiệm.

Trình bày ba câu hỏi thành ba khối ngang cân đối, đánh số 01, 02, 03:
01 — Khu vực nào đang cần chú ý?
02 — Chỉ số có còn mới và đáng tin cậy không?
03 — Tôi nên làm gì, và ai chịu trách nhiệm với hành động đó?

Dòng cuối: Cư dân • Người nhạy cảm • Người tập thể thao ngoài trời • Quản lý vận hành

Mỗi khối chỉ dùng nền xám rất nhạt, số thứ tự màu xanh. Không dùng icon hoạt hình, không thêm số liệu hoặc lời giải pháp vào slide này.
```

---

## Prompt Slide 3 — Giải pháp và kiến trúc

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Giải pháp: từ sensor đến quyết định trong một luồng dữ liệu”.

Phong cách: công nghệ tối giản, nền trắng, chữ đen/xám, xanh #3D8DFF làm điểm nhấn, font sans-serif, không gradient/3D. Footer: “AirGuard AI • MVP simulator”.

Tạo một sơ đồ pipeline đơn giản, đọc từ trái sang phải:
Sensor simulator → MQTT + validation → PostgreSQL → FastAPI → Dashboard & AI Agent

Bên dưới hoặc bên trái sơ đồ, trình bày ngắn gọn ba ý:
- 5 trạm S01–S05; đo PM2.5, CO2, tiếng ồn và nhiệt độ.
- Backend là system of record; frontend và Agent không truy cập database/MQTT trực tiếp.
- Dữ liệu invalid, stale hoặc station offline bị chặn trước các chức năng downstream.

Sơ đồ phải rõ luồng, connector nằm sau node, không giao cắt chữ. Không biến sơ đồ thành dashboard nhiều card. Không tự thêm dịch vụ, database hoặc metric khác.
```

---

## Prompt Slide 4 — Giá trị Dashboard

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Dashboard AQI-first: nhìn nhanh, đi sâu, theo dõi xu hướng”.

Phong cách: nền trắng, chữ đen/xám, điểm nhấn xanh #3D8DFF và xanh nhạt #6DCBF4, font sans-serif; tối giản, nhiều khoảng thở. Footer: “AirGuard AI • MVP simulator”.

Phụ đề: AQI là điểm bắt đầu; các chỉ số thành phần và freshness giải thích điều gì đang xảy ra.

Nội dung chính gồm bốn ý ngắn:
- Bản đồ 5 trạm và trạng thái freshness.
- AQI tổng quan; PM2.5, CO2, tiếng ồn và nhiệt độ để xem chi tiết.
- Lịch sử và forecast ngắn hạn 1–3 giờ.
- Cảnh báo theo rule cho nhiều chỉ số và trạng thái offline.

Tạo một dải nhấn màu xanh nhạt ở cuối slide với câu: “Minh bạch: mọi payload MVP mang nhãn source = simulator; không trình bày như số liệu quan trắc chính thức.”

Không dựng dashboard giả có số liệu cụ thể. Không tự tạo giá trị AQI hoặc biểu đồ.
```

---

## Prompt Slide 5 — Ranh giới AI Agent

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “AI hữu ích khi được grounding và có ranh giới rõ ràng”.

Phong cách: tối giản, nền trắng, chữ đen, điểm nhấn xanh #3D8DFF; font sans-serif; không gradient/3D. Footer: “AirGuard AI • MVP simulator”.

Chia slide thành hai vùng lớn cân đối, không dùng quá nhiều card:

Vùng trái, nền xanh rất nhạt, tiêu đề “AI Agent có thể”:
- Trả lời hiện trạng, so sánh, forecast và cảnh báo.
- Diễn giải theo profile người dùng.
- Tạo proposal có bằng chứng.

Vùng phải, nền xám nhạt, tiêu đề “AI Agent không được”:
- Tự tạo số liệu, ngưỡng hay cảnh báo.
- Truy cập trực tiếp PostgreSQL/MQTT.
- Tự phê duyệt hoặc gửi command.

Nhấn mạnh sự đối lập giữa hỗ trợ và quyền quyết định. Không thêm hình robot, não AI hoặc hiệu ứng tương lai sáo rỗng.
```

---

## Prompt Slide 6 — Human-in-the-Loop

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Human-in-the-Loop: khuyến nghị đi cùng trách nhiệm”.

Phong cách: nền trắng, chữ đen/xám, xanh #3D8DFF làm điểm nhấn, font sans-serif, tối giản. Footer: “AirGuard AI • MVP simulator”.

Tạo flow ngang hoặc zíc-zắc rất rõ gồm bốn bước:
1. Alert có dữ liệu hợp lệ
2. Agent tạo proposal pending
3. Manager approve / reject
4. Audit & device simulator

Thêm ba chú thích ngắn gần flow:
- Chỉ Manager được approve/reject.
- Mọi bước quan trọng có audit record và correlation ID.
- Chỉ sau approval, dispatcher mới publish command; ACK được đối chiếu theo command ID.

Dùng connector có mũi tên đặt sau node, không cắt chữ. Làm nổi bật bước Manager bằng viền xanh đậm. Không mô tả AI là bên tự phê duyệt hoặc tự điều khiển thiết bị.
```

---

## Prompt Slide 7 — Metrics

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Metrics: phản hồi lõi đủ nhanh cho quy mô demo”.

Phong cách: tối giản, nền trắng, chữ đen, điểm nhấn xanh #3D8DFF và xanh nhạt #6DCBF4, font sans-serif. Footer: “AirGuard AI • MVP simulator”.

Trình bày bốn số liệu lớn theo một hàng ngang, ưu tiên con số và nhãn ngắn:
- 20 — 5 trạm × 4 chỉ số
- 0,010 ms — MQTT validation p95
- 98.069 — message/giây
- 4,88 ms — Heatmap 468 điểm p95

Dòng bổ sung: Dashboard polling: 30 giây • Simulator publish: 30 giây

Chú thích phương pháp ở cuối slide, chữ nhỏ nhưng đọc được: “Đo cục bộ ngày 24/08/2026. Microbenchmark xử lý trong tiến trình; chưa bao gồm broker, database và network.”

Giữ nguyên chính xác các con số và dấu thập phân. Không đổi đơn vị, không nội suy, không tạo biểu đồ tăng trưởng hoặc tuyên bố đây là latency end-to-end.
```

---

## Prompt Slide 8 — Tính khả thi

```text
Thiết kế đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Tính khả thi: pipeline end-to-end và kịch bản kiểm chứng”.

Phong cách: nền trắng, chữ đen/xám, điểm nhấn xanh #3D8DFF, font sans-serif, tối giản. Footer: “AirGuard AI • MVP simulator”.

Chia bố cục thành hai vùng lớn:

Vùng trái, tiêu đề “Đã triển khai”:
- Simulator → MQTT → database → API → dashboard.
- Rule engine cảnh báo đa chỉ số.
- Forecast baseline 1–3 giờ từ dữ liệu fresh.
- Agent grounded + deterministic fallback.
- Proposal, phê duyệt, audit và device simulator.

Vùng phải, nền xám nhạt, tiêu đề “Demo kiểm chứng”:
- Normal: map + source + freshness.
- Spike: alert sau chuỗi đo hợp lệ.
- Stale / duplicate: bị chặn.
- Agent thiếu dữ liệu: từ chối suy đoán.
- Proposal: pending → approve/reject → audit.

Không dùng từ “production-ready”. Không thêm chứng nhận, uptime hoặc kết quả test chưa được cung cấp.
```

---

## Prompt Slide 9 — Định hướng

```text
Thiết kế đúng 1 slide kết thúc, tỉ lệ 16:9, bằng tiếng Việt với tiêu đề: “Định hướng: mở rộng minh bạch, có kiểm soát”.

Phong cách: nền trắng, chữ đen, điểm nhấn xanh #3D8DFF và xanh nhạt #6DCBF4, font sans-serif; tối giản, có cảm giác kết luận rõ ràng. Footer: “AirGuard AI • MVP simulator”.

Chia thành hai vùng:

Ngắn hạn:
- Chốt ngưỡng cảnh báo, severity, tọa độ trạm và vai trò Manager.
- Hoàn thiện weather, notification và worker bất đồng bộ.

Trung hạn:
- Tích hợp sensor thật và xác thực thực địa.
- Đánh giá/backtest forecast.
- Bổ sung authentication/RBAC production và observability.

Đặt câu kết luận lớn ở cuối slide: “Mở rộng trên nền tảng có kiểm soát dữ liệu, minh bạch AI và trách nhiệm con người.”

Không kết thúc bằng “Thank you”. Không tuyên bố các hạng mục định hướng đã được triển khai.
```

---

## Cách dùng nhanh

1. Tạo presentation 16:9 trong Google Slides.
2. Gửi Prompt Slide 1 cho công cụ thiết kế và tạo một slide.
3. Tiếp tục gửi từng prompt còn lại, mỗi lần chỉ yêu cầu một slide.
4. Nếu công cụ đổi phong cách, dán lại nguyên phần “Phong cách” trong prompt của slide đó.
5. Kiểm tra lại các số ở Slide 7 và nhãn “MVP simulator” trước khi trình bày.

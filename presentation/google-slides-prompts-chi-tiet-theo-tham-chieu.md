# Prompt Google Slides chi tiết — AirGuard AI

Tài liệu này được phát triển theo ngôn ngữ thiết kế của slide tham chiếu: nền giấy kem nhẹ, đường đồng mức/topographic line ở rìa, tiêu đề đậm, khối nội dung có viền mảnh và bóng mềm, icon đen lớn, màu nhấn navy–cam. Mỗi prompt tạo **đúng một slide** và đã tự chứa toàn bộ chỉ dẫn vì công cụ không nhớ slide trước.

## Hình ảnh nên chuẩn bị trước

- Slide 3: `image/Kiến trúc tổng thể.png`
- Slide 4: `docs/evidence/backlog2/assets/qa04-01-normal-dashboard.png`
- Slide 6: `image/Luồng cảnh báo và phê duyệt.png`

Khi dùng ba ảnh trên, tải ảnh lên Google Slides trước rồi yêu cầu công cụ đặt ảnh đúng vị trí. Các slide còn lại chỉ cần icon vector đơn sắc hoặc hình minh họa do công cụ tạo.

---

## Slide 1 — Cover có chiều sâu thị giác

```text
Tạo đúng 1 slide mở đầu tỉ lệ 16:9, bằng tiếng Việt, cho dự án AirGuard AI.

NGÔN NGỮ THIẾT KẾ BẮT BUỘC:
- Nền kem rất nhạt #F7F5EE, có texture giấy tinh tế.
- Thêm các đường đồng mức/topographic line cực mảnh màu xám xanh ở góc trên trái và góc dưới phải; độ tương phản thấp, không gây rối chữ.
- Màu chữ chính xanh đen #17213A; màu nhấn cam đất #C85E35 và xanh môi trường #2A8C82.
- Font sans-serif đậm, hiện đại; tiêu đề rất lớn; không gradient, không 3D, không ảnh stock người đeo khẩu trang.
- Giữ footer nhỏ: “AirGuard AI • MVP simulator”.

BỐ CỤC:
- Phần trái chiếm khoảng 60% slide: tiêu đề lớn 2 dòng, căn trái.
- Phần phải: một minh họa đơn sắc dạng editorial gồm 5 điểm sensor trên bản đồ khu đô thị, các vòng sóng dữ liệu hội tụ về một dashboard nhỏ. Minh họa màu xanh đen, chỉ dùng cam/xanh để nhấn 2–3 chi tiết.
- Có một đường dọc mảnh ngăn nhẹ hai vùng.

NỘI DUNG CHÍNH XÁC:
- Eyebrow nhỏ: AIRGUARD AI
- Tiêu đề: Quan sát môi trường, hỗ trợ quyết định an toàn
- Phụ đề: MVP giám sát chất lượng môi trường tại Vinhomes Ocean Park 1
- Dòng giá trị: 5 trạm mô phỏng • Dashboard AQI-first • AI Agent có kiểm soát
- Chú thích nhỏ: Dữ liệu MVP từ simulator — không phải quan trắc được chứng nhận.

Không tự tạo logo, slogan, số AQI hoặc tên địa điểm mới. Slide phải tạo cảm giác đây là một hệ thống có dữ liệu và trách nhiệm, không phải ứng dụng thời tiết thông thường.
```

---

## Slide 2 — Bài toán dưới dạng ba tình huống

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Bài toán: dữ liệu chưa đủ để hành động đúng lúc”.

PHONG CÁCH:
- Nền kem #F7F5EE có texture nhẹ và đường đồng mức mảnh ở hai cạnh.
- Chữ xanh đen #17213A; số thứ tự và chi tiết quan trọng dùng cam #C85E35.
- Ba panel ngang có nền gần trắng, viền xanh đen 1 px, bo góc nhỏ và bóng mềm giống slide tham chiếu.
- Icon vector đơn sắc đen/xanh đen, nét dày, kích thước lớn; không dùng icon nhiều màu hoặc emoji.
- Footer: “AirGuard AI • MVP simulator”.

BỐ CỤC:
- Tiêu đề lớn ở trên; dưới tiêu đề có câu dẫn ngắn: “Người dùng không chỉ cần một con số — họ cần biết dữ liệu có đáng tin và hành động nào phù hợp.”
- Ba panel chiếm phần lớn slide, đặt theo một hàng từ trái sang phải.

PANEL 01:
- Icon gợi ý: map pin nằm trong lớp sương/haze.
- Tiêu đề: Khu vực nào cần chú ý?
- Mô tả: Người dùng cần nhận biết nhanh trạm và khu vực đang có dấu hiệu bất thường.

PANEL 02:
- Icon gợi ý: đồng hồ kết hợp tín hiệu sensor.
- Tiêu đề: Dữ liệu có còn mới?
- Mô tả: Số đo stale, invalid hoặc trạm offline không thể được xem như hiện trạng đáng tin cậy.

PANEL 03:
- Icon gợi ý: bàn tay người quản lý đặt dấu kiểm lên đề xuất.
- Tiêu đề: Ai chịu trách nhiệm hành động?
- Mô tả: Cảnh báo và lệnh thiết bị phải có bằng chứng, quyền hạn và người phê duyệt rõ ràng.

Dòng nhỏ cuối slide: Cư dân • Người nhạy cảm • Người tập thể thao ngoài trời • Quản lý vận hành

Không đưa giải pháp kỹ thuật vào slide này. Không thêm số liệu chưa được cung cấp.
```

---

## Slide 3 — Kiến trúc hệ thống rõ từ đầu đến cuối

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Giải pháp: từ sensor đến quyết định trong một luồng dữ liệu”.

PHONG CÁCH:
- Nền kem #F7F5EE, texture giấy nhẹ, topographic line ở góc.
- Chữ xanh đen #17213A; đường luồng xanh môi trường #2A8C82; điểm kiểm soát/rủi ro dùng cam #C85E35.
- Khung viền mảnh và bóng rất nhẹ; không dùng gradient hoặc hiệu ứng 3D.
- Footer: “AirGuard AI • MVP simulator”.

TÀI SẢN HÌNH ẢNH:
- Ưu tiên sử dụng ảnh người dùng tải lên: “Kiến trúc tổng thể.png”.
- Ảnh kiến trúc phải được fit đầy đủ trong khung, không crop, không kéo méo.
- Nếu không có ảnh, dựng sơ đồ vector theo pipeline bắt buộc bên dưới.

BỐ CỤC:
- Bên trái khoảng 35%: một khối giải thích ngắn với headline mạnh.
- Bên phải khoảng 65%: sơ đồ kiến trúc lớn, có đủ nhãn và connector rõ ràng.

HEADLINE BÊN TRÁI:
“Backend là system of record; mọi dữ liệu phải qua quality gate trước khi được dùng.”

PIPELINE BẮT BUỘC:
Sensor simulator → MQTT → Consumer + validation → PostgreSQL → FastAPI → Dashboard & AI Agent

BA CALLOUT NGẮN:
- 5 trạm S01–S05; PM2.5, CO2, tiếng ồn, nhiệt độ.
- Frontend và Agent không truy cập database/MQTT trực tiếp.
- Invalid, stale hoặc offline bị chặn trước current, forecast, alert và proposal.

YÊU CẦU SƠ ĐỒ:
- Connector đặt sau node, không chạy xuyên qua chữ.
- Dùng icon nhỏ nhất quán: sensor, message broker, shield-check, database, API, dashboard/agent.
- Làm nổi quality gate bằng màu cam, các bước dữ liệu hợp lệ bằng xanh.
- Không thêm cloud provider, Kafka, TimescaleDB hoặc công nghệ không có trong nội dung.
```

---

## Slide 4 — Dashboard dưới dạng product showcase

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Dashboard AQI-first: nhìn nhanh, đi sâu, theo dõi xu hướng”.

PHONG CÁCH:
- Nền kem #F7F5EE có texture rất nhẹ và topographic line ở rìa.
- Chữ xanh đen #17213A; xanh #2A8C82 cho trạng thái tốt/dữ liệu; cam #C85E35 cho cảnh báo.
- Không dùng bố cục toàn bullet. Đây phải là một slide product showcase giàu hình ảnh.
- Footer: “AirGuard AI • MVP simulator”.

TÀI SẢN HÌNH ẢNH BẮT BUỘC:
- Dùng screenshot người dùng tải lên: “qa04-01-normal-dashboard.png”.
- Đặt screenshot trong một khung browser/laptop tối giản, chiếm khoảng 60% slide.
- Fit toàn bộ screenshot, không crop các legend, bản đồ, timestamp hoặc banner simulator.
- Tạo bóng mềm dưới khung, không làm screenshot bị mờ.

BỐ CỤC:
- Screenshot lớn bên trái hoặc giữa.
- Bên phải có 4 callout ngắn, mỗi callout nối tới vùng liên quan trên screenshot bằng đường mảnh hoặc số đánh dấu.

4 CALLOUT:
01 — Bản đồ 5 trạm và trạng thái freshness.
02 — AQI tổng quan; PM2.5, CO2, tiếng ồn và nhiệt độ để xem chi tiết.
03 — Lịch sử và forecast ngắn hạn 1–3 giờ.
04 — Cảnh báo theo rule và trạng thái offline.

DẢI NHẤN CUỐI SLIDE:
“Mọi dữ liệu MVP mang nhãn source = simulator; không trình bày như quan trắc chính thức.”

Không dựng số liệu giả trên screenshot. Không thêm chart hoặc KPI ngoài giao diện thật.
```

---

## Slide 5 — AI Agent: khả năng và giới hạn

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “AI hữu ích khi được grounding và có ranh giới rõ ràng”.

PHONG CÁCH:
- Nền kem #F7F5EE, texture giấy và topographic line mờ.
- Chữ xanh đen #17213A; vùng “có thể” dùng xanh #2A8C82; vùng “không được” dùng cam #C85E35.
- Panel viền mảnh, nền gần trắng, bóng mềm; icon vector đơn sắc lớn giống tinh thần slide tham chiếu.
- Footer: “AirGuard AI • MVP simulator”.

BỐ CỤC:
- Chính giữa slide là icon AI Agent dạng bong bóng hội thoại kết hợp shield/check, không dùng robot hình người.
- Từ icon trung tâm tách thành hai panel lớn trái/phải.

PANEL TRÁI — AI AGENT CÓ THỂ:
- Icon: kính lúp trên dữ liệu hoặc hội thoại có dấu check.
- Trả lời hiện trạng, so sánh, forecast và cảnh báo.
- Diễn giải theo profile người dùng.
- Tạo proposal có bằng chứng.

PANEL PHẢI — AI AGENT KHÔNG ĐƯỢC:
- Icon: database có khóa và bàn tay bị chặn.
- Tự tạo số liệu, ngưỡng hay cảnh báo.
- Truy cập trực tiếp PostgreSQL/MQTT.
- Tự phê duyệt hoặc gửi command.

Thêm một câu kết luận nhỏ ở giữa dưới: “Grounding trước fluency; con người giữ quyền quyết định.”

Không dùng hình não phát sáng, robot hoặc hiệu ứng sci-fi. Không diễn đạt Agent như hệ thống tự hành.
```

---

## Slide 6 — Human-in-the-Loop như một chuỗi trách nhiệm

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Human-in-the-Loop: khuyến nghị đi cùng trách nhiệm”.

PHONG CÁCH:
- Nền kem #F7F5EE, đường đồng mức ở rìa, chữ xanh đen #17213A.
- Màu xanh #2A8C82 cho dữ liệu hợp lệ; cam #C85E35 cho bước cần con người quyết định.
- Khung viền mảnh, bóng nhẹ; không gradient, không 3D.
- Footer: “AirGuard AI • MVP simulator”.

TÀI SẢN HÌNH ẢNH:
- Có thể dùng ảnh người dùng tải lên “Luồng cảnh báo và phê duyệt.png” làm tài liệu tham chiếu.
- Nếu dùng ảnh, fit đầy đủ và không crop nhãn.
- Ưu tiên dựng lại thành flow vector sạch hơn để chữ đủ lớn khi thuyết trình.

FLOW CHÍNH GỒM 4 BƯỚC:
1. Alert có dữ liệu hợp lệ
2. Agent tạo proposal pending
3. Manager approve / reject
4. Audit & device simulator

THIẾT KẾ FLOW:
- Mỗi bước là một node lớn có icon: alert/shield, document-lightbulb, manager-check, audit-log/device.
- Bước 3 lớn hơn 15–20% và có màu cam để thể hiện điểm kiểm soát con người.
- Connector có mũi tên chạy phía sau node; nhánh Reject đi thẳng tới Audit, nhánh Approve đi tới Dispatcher/Device rồi Audit.

CALLOUT NHỎ:
- Chỉ Manager được approve/reject.
- Mọi bước quan trọng có audit record và correlation ID.
- Command chỉ publish sau approval; ACK đối chiếu theo command ID.

Không để Agent đứng sau nút approve. Không mô tả publish thành thiết bị đã thực thi thành công.
```

---

## Slide 7 — Metrics theo bố cục 4 trụ cột của slide tham chiếu

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Metrics: phản hồi lõi đủ nhanh cho quy mô demo”.

Đây là slide cần bám sát nhất vào ngôn ngữ thiết kế của slide tham chiếu “4 Trụ cột Giá trị”:
- Nền kem #F7F5EE có texture giấy và topographic line mảnh ở các góc.
- Bốn panel xếp lưới 2 × 2, nền gần trắng, viền xanh đen 1 px, bo góc nhỏ, bóng mềm.
- Mỗi panel có một icon đen lớn bên trái; con số lớn và nhãn ở bên phải.
- Xen kẽ màu nhấn xanh navy #17213A, xanh môi trường #2A8C82 và cam #C85E35.
- Footer: “AirGuard AI • MVP simulator”.

PANEL 1:
- Icon: cụm 5 sensor/map pin.
- Số lớn: 20
- Nhãn: 5 trạm × 4 chỉ số
- Mô tả nhỏ: Phạm vi dữ liệu môi trường được theo dõi trong MVP.

PANEL 2:
- Icon: shield-check hoặc message validation.
- Số lớn: 0,010 ms
- Nhãn: MQTT validation p95
- Mô tả nhỏ: Thời gian xử lý validation cục bộ trên 1.000 payload.

PANEL 3:
- Icon: luồng message hoặc đồng hồ tốc độ.
- Số lớn: 98.069
- Nhãn: message/giây
- Mô tả nhỏ: Throughput tính toán từ benchmark validation cục bộ.

PANEL 4:
- Icon: heatmap grid hoặc bản đồ đường đồng mức.
- Số lớn: 4,88 ms
- Nhãn: Heatmap 468 điểm p95
- Mô tả nhỏ: Thời gian nội suy lưới AQI trong tiến trình.

Dòng nhỏ dưới lưới:
“Dashboard polling: 30 giây • Simulator publish: 30 giây”

Footnote bắt buộc:
“Đo cục bộ ngày 24/08/2026; chưa bao gồm broker, database và network. Không phải latency end-to-end.”

Giữ nguyên tuyệt đối con số, dấu chấm/dấu phẩy và đơn vị. Không tạo biểu đồ tăng trưởng hoặc phần trăm cải thiện.
```

---

## Slide 8 — Tính khả thi bằng bằng chứng triển khai và kịch bản lỗi

```text
Tạo đúng 1 slide 16:9 bằng tiếng Việt với tiêu đề: “Tính khả thi: pipeline end-to-end và kịch bản kiểm chứng”.

PHONG CÁCH:
- Nền kem #F7F5EE, texture giấy và đường đồng mức mờ.
- Chữ xanh đen #17213A; xanh #2A8C82 cho phần đã triển khai; cam #C85E35 cho scenario lỗi/điểm kiểm chứng.
- Khung viền mảnh và bóng mềm tương tự slide tham chiếu.
- Footer: “AirGuard AI • MVP simulator”.

BỐ CỤC:
- Chia slide thành hai panel lớn dọc, mỗi panel khoảng 45% chiều rộng.
- Ở giữa là một đường dọc mảnh hoặc mũi tên thể hiện “Build → Verify”.

PANEL TRÁI — ĐÃ TRIỂN KHAI:
- Icon lớn: pipeline hoặc các khối hệ thống nối nhau.
- Simulator → MQTT → database → API → dashboard.
- Rule engine cảnh báo đa chỉ số.
- Forecast baseline 1–3 giờ từ dữ liệu fresh.
- Agent grounded + deterministic fallback.
- Proposal, phê duyệt, audit và device simulator.

PANEL PHẢI — DEMO KIỂM CHỨNG:
- Icon lớn: checklist có kính lúp.
- Normal: map + source + freshness.
- Spike: alert sau chuỗi đo hợp lệ.
- Stale / duplicate: bị chặn.
- Agent thiếu dữ liệu: từ chối suy đoán.
- Proposal: pending → approve/reject → audit.

Câu kết luận nhỏ cuối slide: “Tính khả thi được chứng minh bằng luồng hoạt động và cả error path, không chỉ bằng giao diện.”

Không dùng từ production-ready. Không thêm uptime, accuracy, coverage hoặc chứng nhận chưa có bằng chứng.
```

---

## Slide 9 — Roadmap và kết luận

```text
Tạo đúng 1 slide kết thúc tỉ lệ 16:9 bằng tiếng Việt với tiêu đề: “Định hướng: mở rộng minh bạch, có kiểm soát”.

PHONG CÁCH:
- Nền kem #F7F5EE có texture giấy; các đường đồng mức chạy từ góc trái dưới tới góc phải trên, gợi cảm giác hành trình mở rộng.
- Chữ xanh đen #17213A; xanh #2A8C82 cho hiện tại/ngắn hạn; cam #C85E35 cho mốc chuyển đổi sang dữ liệu thật.
- Font sans-serif đậm; không gradient/3D; footer “AirGuard AI • MVP simulator”.

BỐ CỤC:
- Dùng timeline từ trái sang phải với hai mốc lớn và một đích đến.
- Mỗi mốc có icon vector đơn sắc và 2–3 ý, không dùng nhiều card nhỏ.

MỐC 1 — NGẮN HẠN:
- Icon: sliders/configuration + shield.
- Chốt ngưỡng cảnh báo, severity, tọa độ trạm và vai trò Manager.
- Hoàn thiện weather, notification và worker bất đồng bộ.

MỐC 2 — TRUNG HẠN:
- Icon: sensor thật kết nối cloud/database.
- Tích hợp sensor thật và xác thực thực địa.
- Đánh giá/backtest forecast.
- Bổ sung authentication/RBAC production và observability.

ĐÍCH ĐẾN Ở CUỐI TIMELINE:
- Icon: con người đứng trước dashboard có dấu shield.
- Câu kết luận lớn: “Kiểm soát dữ liệu • Minh bạch AI • Con người chịu trách nhiệm”

Không kết thúc bằng “Thank you”. Không trình bày các hạng mục roadmap như đã hoàn thành.
```

---

## Checklist sau khi Google Slides tạo từng slide

- Tất cả slide đều dùng cùng nền kem, topographic line, font và footer.
- Không slide nào tự tạo số AQI hoặc dữ liệu môi trường cụ thể.
- Ảnh screenshot/sơ đồ được fit đầy đủ, không crop và không kéo méo.
- Slide 7 giữ nguyên các số: `20`, `0,010 ms`, `98.069`, `4,88 ms`, `468 điểm`.
- Slide 6 thể hiện rõ Manager là điểm phê duyệt duy nhất.
- Mỗi slide có một thông điệp chính; nếu chữ quá dày, rút gọn mô tả chứ không giảm body text xuống quá nhỏ.

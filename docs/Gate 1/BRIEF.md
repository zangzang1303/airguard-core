# AirGuard AI — 1-Page Brief

## Problem — Vấn đề

Trong khu đô thị hoặc campus, dữ liệu môi trường thường được thu thập từ nhiều điểm nhưng còn rời rạc, khó tổng hợp và khó chuyển thành thông tin dễ hiểu cho người dùng.

Cư dân không dễ biết khu vực nào đang có PM2.5 cao, có nên hoạt động ngoài trời hay không, hoặc khu vực nào phù hợp hơn với người nhạy cảm. Ban quản lý cũng thiếu một công cụ tập trung để theo dõi nhiều điểm đo, phát hiện bất thường, dự báo xu hướng và kiểm soát các cảnh báo trước khi gửi tới người dùng.

## Solution — Giải pháp

AirGuard AI là hệ thống AI Agent giám sát chất lượng không khí ngoài trời tại khu vực VinUni và vùng lân cận trong Vinhomes Ocean Park, tập trung MVP vào chỉ số PM2.5.

Hệ thống sử dụng 5 cảm biến PM2.5 giả lập truyền dữ liệu qua MQTT, kết hợp bản đồ thật, dữ liệu thời tiết, Alert Engine và mô hình dự báo ngắn hạn để:

- Hiển thị PM2.5 tại từng vị trí trên bản đồ.
- Theo dõi dữ liệu hiện tại, lịch sử và trạng thái cảm biến.
- Phát hiện PM2.5 vượt ngưỡng hoặc cảm biến mất kết nối.
- Dự báo xu hướng PM2.5 trong 1–3 giờ.
- Cho phép người dùng hỏi AI Agent bằng ngôn ngữ tự nhiên.
- So sánh khu vực và đưa ra khuyến nghị theo từng nhóm người dùng.
- Tạo đề xuất cảnh báo để ban quản lý phê duyệt hoặc từ chối thông qua Human-in-the-Loop.

AI Agent không tự tạo số liệu mà phải gọi các công cụ nội bộ để lấy dữ liệu hiện tại, lịch sử, thời tiết, dự báo, cảnh báo và hồ sơ người dùng.

## Target Audience — Đối tượng người dùng

- **Cư dân:** muốn biết khu vực nào đang có chất lượng không khí xấu và cần hạn chế đi qua.
- **Người nhạy cảm:** cần khuyến nghị thận trọng hơn khi PM2.5 tăng cao.
- **Người chạy bộ hoặc hoạt động ngoài trời:** muốn biết địa điểm và thời điểm phù hợp để tập luyện.
- **Ban quản lý khu đô thị/campus:** cần theo dõi dữ liệu, xem cảnh báo, kiểm tra bằng chứng và phê duyệt đề xuất của AI Agent.

## Core Value — Giá trị cốt lõi

AirGuard AI không chỉ hiển thị số liệu môi trường mà còn biến dữ liệu thành thông tin dễ hiểu và quyết định có thể hành động.

Điểm khác biệt của sản phẩm là AI Agent có khả năng:

- Tự xác định yêu cầu của người dùng.
- Chọn đúng tool để truy xuất dữ liệu.
- Trả lời kèm số liệu, vị trí, thời gian cập nhật và bằng chứng.
- So sánh nhiều khu vực.
- Đưa ra khuyến nghị phù hợp với từng nhóm người dùng.
- Tạo warning proposal khi phát hiện tình trạng cần cảnh báo.

Các quyết định quan trọng như phát cảnh báo diện rộng không được AI tự thực hiện. Ban quản lý vẫn giữ quyền quyết định cuối cùng thông qua cơ chế Human-in-the-Loop.

## MVP

MVP gồm:

- 5 Sensor Simulator truyền PM2.5 qua MQTT.
- Mosquitto MQTT Broker.
- FastAPI Backend và PostgreSQL.
- Dashboard React Leaflet trên bản đồ OpenStreetMap.
- Alert Engine phát hiện vượt ngưỡng và sensor offline.
- Forecast Service dự báo PM2.5 trong 1–3 giờ.
- AI Agent sử dụng tool calling hoặc LangGraph.
- Khuyến nghị cho người bình thường, người nhạy cảm và người hoạt động ngoài trời.
- Warning Proposal.
- Manager Approve/Reject.
- Audit log cho các hành động quan trọng.



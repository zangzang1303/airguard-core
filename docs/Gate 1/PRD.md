# Tài liệu Yêu cầu Sản phẩm (PRD) — AirGuard AI

**Phiên bản:** 1.0  
**Ngày cập nhật:** 02/08/2026  
**Trạng thái:** Gate 1 — Chốt đề tài và thiết kế  
**Thời gian thực hiện:** 6 tuần  
**Quy mô nhóm:** 4 thành viên  

---

## 1. Tổng quan

AirGuard AI là hệ thống AI Agent hỗ trợ giám sát môi trường đô thị hoặc campus theo nhiều điểm đo. MVP tập trung vào chỉ số PM2.5 ngoài trời tại khu vực VinUni và vùng lân cận trong Vinhomes Ocean Park.

Hệ thống thu thập dữ liệu từ các cảm biến giả lập qua MQTT, hiển thị tình trạng hiện tại trên bản đồ thật, phát hiện bất thường, dự báo xu hướng PM2.5 ngắn hạn và cho phép người dùng đặt câu hỏi bằng ngôn ngữ tự nhiên.

AI Agent không tự tạo số liệu. Agent lựa chọn và gọi các công cụ nội bộ để lấy dữ liệu hiện tại, lịch sử, thời tiết, cảnh báo, dự báo và hồ sơ người dùng. Khi cần phát cảnh báo diện rộng, Agent chỉ tạo đề xuất để ban quản lý phê duyệt hoặc từ chối thông qua cơ chế Human-in-the-Loop.

Tầm nhìn của sản phẩm là biến dữ liệu môi trường rời rạc thành thông tin dễ hiểu, có căn cứ và có thể hỗ trợ hành động.

---

## 2. Mục tiêu

- Cung cấp một giao diện thống nhất để theo dõi PM2.5 tại nhiều vị trí.
- Giúp cư dân nhanh chóng xác định khu vực có chất lượng không khí xấu.
- Hỗ trợ người nhạy cảm và người hoạt động ngoài trời đưa ra quyết định phù hợp hơn.
- Phát hiện PM2.5 vượt ngưỡng, dữ liệu bất thường và cảm biến mất kết nối.
- Dự báo xu hướng PM2.5 trong 1–3 giờ tiếp theo.
- Cho phép người dùng hỏi AI Agent về tình trạng hiện tại, so sánh khu vực, cảnh báo và khuyến nghị.
- Bảo đảm mọi số liệu trong câu trả lời của Agent đều đến từ tool và dữ liệu của hệ thống.
- Cho phép Agent tạo đề xuất cảnh báo có bằng chứng.
- Bắt buộc con người phê duyệt trước khi phát cảnh báo diện rộng.
- Hoàn thành một MVP có thể demo end-to-end trong 6 tuần.

---

## 3. Không phải mục tiêu

- Triển khai trên phạm vi toàn thành phố.
- Lắp đặt cảm biến vật lý trên diện rộng.
- Điều khiển trực tiếp hệ thống thông gió, lọc khí, HVAC, BMS hoặc SCADA thật.
- Chẩn đoán hoặc tư vấn điều trị y tế.
- Xây dựng ứng dụng mobile riêng.
- Triển khai multi-agent.
- Xây dựng vector database hoặc RAG tài liệu quy mô lớn.
- Tích hợp SMS, cuộc gọi tự động hoặc hạ tầng gửi thông báo thương mại.
- Bắt buộc sử dụng mô hình deep learning như LSTM trong MVP.
- Xây dựng hạ tầng production với Kubernetes hoặc auto-scaling.
- Theo dõi đầy đủ mọi chỉ số môi trường trong MVP.

Kiến trúc có thể mở rộng để hỗ trợ CO₂, PM10, tiếng ồn, nhiệt độ, độ ẩm, NO₂, SO₂ và O₃ trong tương lai, nhưng MVP tập trung vào PM2.5 ngoài trời.

---

## 4. Đối tượng người dùng

### 4.1 Cư dân

Cư dân muốn hiểu nhanh chất lượng không khí tại khu vực sinh sống hoặc học tập. Họ không nhất thiết có kiến thức chuyên sâu về môi trường và cần câu trả lời ngắn gọn, dễ hiểu.

Nhu cầu chính:

- Xem PM2.5 theo vị trí.
- Biết khu vực nào nên tránh.
- Hiểu ý nghĩa của cảnh báo.
- Nhận khuyến nghị hành động đơn giản.

### 4.2 Người nhạy cảm

Nhóm này gồm người cao tuổi, trẻ nhỏ hoặc những người dễ bị ảnh hưởng bởi ô nhiễm không khí.

Nhu cầu chính:

- Nhận khuyến nghị thận trọng hơn.
- Biết khu vực nào có PM2.5 thấp hơn.
- Biết khi nào nên hạn chế hoạt động ngoài trời.

Sản phẩm không lưu bệnh án và không đưa ra chẩn đoán y tế. Người dùng chỉ lựa chọn nhóm nhạy cảm ở mức hồ sơ sử dụng.

### 4.3 Người hoạt động thể thao ngoài trời

Nhóm này gồm người chạy bộ hoặc thường xuyên tập luyện ngoài trời.

Nhu cầu chính:

- Biết có nên tập tại một khu vực hay không.
- So sánh khu thể thao, công viên và các vị trí khác.
- Xem xu hướng PM2.5 trong vài giờ tiếp theo.

### 4.4 Ban quản lý

Ban quản lý cần một dashboard tập trung để theo dõi:

- Trạng thái cảm biến.
- PM2.5 tại từng điểm.
- Cảnh báo đang hoạt động.
- Đề xuất do Agent tạo.
- Lịch sử phê duyệt và từ chối.

Ban quản lý cần xem được bằng chứng trước khi quyết định phát cảnh báo.

---

## 5. Các giải pháp hiện có và hạn chế

### 5.1 Ứng dụng thời tiết và chất lượng không khí phổ thông

- Thường cung cấp dữ liệu ở cấp thành phố hoặc quận.
- Không phản ánh rõ khác biệt giữa cổng chính, bãi xe, trục đường, công viên và khu thể thao.
- Chủ yếu hiển thị số liệu và màu sắc.
- Ít hỗ trợ khuyến nghị theo từng nhóm người dùng.
- Không có quy trình phê duyệt cảnh báo cục bộ.

### 5.2 Dashboard cảm biến độc lập

- Có thể hiển thị số liệu nhưng khó giải thích cho người dùng phổ thông.
- Người dùng phải tự đọc biểu đồ và ngưỡng.
- Không hỗ trợ hỏi đáp bằng ngôn ngữ tự nhiên.
- Không có AI Agent tạo đề xuất có căn cứ.

### 5.3 Chatbot AI thông thường

- Có thể giải thích kiến thức PM2.5.
- Không tự động truy cập dữ liệu sensor hiện tại nếu không được kết nối tool.
- Có nguy cơ bịa số liệu.
- Không hỗ trợ quy trình phê duyệt và audit log.

### 5.4 Theo dõi thủ công bởi ban quản lý

- Phải kiểm tra nhiều nguồn dữ liệu.
- Khó so sánh nhiều vị trí nhanh chóng.
- Dễ chậm cảnh báo.
- Thiếu lịch sử quyết định có cấu trúc.

AirGuard AI kết hợp dữ liệu cục bộ, bản đồ, dự báo, AI Agent dùng tool và cơ chế Human-in-the-Loop trong một hệ thống thống nhất.

---

## 6. Các giả định

Các giả định dưới đây cần được xác nhận qua Mentor, phỏng vấn người dùng hoặc kiểm thử prototype.

- Người dùng thích bản đồ và khuyến nghị ngắn gọn hơn bảng dữ liệu thô.
- Người dùng có nhu cầu so sánh các khu vực gần nhau.
- Người nhạy cảm cần khuyến nghị thận trọng hơn người dùng bình thường.
- Ban quản lý cần bằng chứng trước khi duyệt cảnh báo.
- Sensor giả lập qua MQTT được chấp nhận cho MVP nếu ghi rõ nguồn dữ liệu.
- Năm vị trí đại diện đủ để chứng minh giá trị sản phẩm.
- PM2.5 là chỉ số chính phù hợp cho MVP.
- Dự báo ngắn hạn có giá trị thực tế hơn dự báo dài hạn.
- Người dùng hiểu sản phẩm là công cụ hỗ trợ, không phải cơ quan quan trắc chính thức.
- Câu trả lời của Agent đáng tin hơn khi có số liệu, vị trí, timestamp và nguồn.

### Trạng thái xác thực

| Giả định | Bằng chứng hiện tại | Trạng thái |
|---|---|---|
| Người dùng cần cách diễn giải đơn giản | Phân tích ban đầu của nhóm | Cần kiểm thử |
| Bản đồ là giao diện chính phù hợp | Quyết định thiết kế | Cần kiểm thử với người dùng |
| Người nhạy cảm cần khuyến nghị riêng | Yêu cầu dự án | Chấp nhận cho MVP |
| Ban quản lý cần quyền phê duyệt | Ràng buộc đề bài | Đã chấp nhận |
| Sensor giả lập được chấp nhận | Chưa có xác nhận chính thức | Cần hỏi Mentor |
| Chỉ làm PM2.5 là đủ | Chưa có xác nhận chính thức | Cần hỏi Mentor |

Sau khi có phỏng vấn, cần bổ sung link biên bản hoặc ghi chú vào phần này.

---

## 7. Các ràng buộc

- Nhóm có 4 thành viên.
- Thời gian thực hiện là 6 tuần.
- MVP phải có AI Agent hoạt động, không chỉ có dashboard.
- Chỉ số chính là PM2.5 ngoài trời.
- MVP sử dụng 5 vị trí cảm biến.
- Telemetry được truyền qua MQTT.
- Bản đồ phải sử dụng khu vực địa lý thật.
- Mọi dữ liệu giả lập phải được gắn nhãn rõ.
- Backend phải chống lưu message MQTT trùng.
- Agent chỉ được gọi tool, không truy cập database trực tiếp.
- Agent không được bịa số liệu.
- Ngưỡng cảnh báo phải do rule engine quyết định.
- Cảnh báo diện rộng phải qua Human-in-the-Loop.
- MVP phải có thể chạy bằng Docker Compose.
- Không commit secret hoặc API key lên GitHub.
- Frontend không kết nối trực tiếp với MQTT.
- Mọi hành động quan trọng phải có audit log.
- Thiết kế phải đủ đơn giản để nhóm có thể debug và demo.

---

## 8. Các trường hợp sử dụng chính

- Theo dõi PM2.5 hiện tại tại 5 vị trí.
- Xem trạng thái và lịch sử của một cảm biến.
- Phát hiện PM2.5 cao hoặc cảm biến offline.
- Hỏi khu vực nào ô nhiễm nhất.
- So sánh hai khu vực.
- Hỏi có nên hoạt động ngoài trời hay không.
- Nhận khuyến nghị cho người nhạy cảm.
- Hỏi lý do tạo cảnh báo.
- Xem dự báo PM2.5 trong 1–3 giờ.
- Tạo đề xuất cảnh báo.
- Approve hoặc reject đề xuất.
- Xem lịch sử hành động quan trọng.

---

## 9. Theo dõi PM2.5 tại nhiều vị trí

Dashboard chính hiển thị 5 điểm cảm biến trên OpenStreetMap.

Mỗi marker hiển thị:

- Tên trạm.
- PM2.5 hiện tại.
- Mức chất lượng không khí.
- Trạng thái cảm biến.
- Thời gian cập nhật gần nhất.

Các trạm dự kiến:

| Mã trạm | Loại vị trí |
|---|---|
| S01 | Cổng chính |
| S02 | Bãi đỗ xe |
| S03 | Trục đường chính |
| S04 | Công viên |
| S05 | Khu thể thao ngoài trời |

Tọa độ chính xác phải được chốt trước khi hoàn thiện cấu hình production của bản đồ.

### Tiêu chí chấp nhận

- Bản đồ hiển thị đủ 5 marker.
- Mỗi marker hiển thị measurement hợp lệ mới nhất.
- Sensor offline được đánh dấu rõ.
- Dữ liệu giả lập có nhãn.
- Người dùng có thể chọn marker để xem chi tiết.

---

## 10. Xem chi tiết và lịch sử trạm

Khi chọn một trạm, hệ thống hiển thị:

- PM2.5 hiện tại.
- Trạng thái hiện tại.
- Thời gian cập nhật.
- Xu hướng gần đây.
- Biểu đồ lịch sử.
- Cảnh báo liên quan.

### Tiêu chí chấp nhận

- Hiển thị measurement hợp lệ mới nhất.
- Không dùng measurement invalid.
- Dữ liệu lịch sử được sắp theo thời gian.
- Có thể xem tối thiểu 24 giờ dữ liệu gần nhất nếu có.
- Dữ liệu stale được đánh dấu rõ.

---

## 11. Sensor Simulator và MQTT

Sensor Simulator sinh dữ liệu PM2.5 cho 5 trạm.

PM2.5 được tạo dựa trên:

- PM2.5 nền của từng vị trí.
- Hệ số giao thông.
- Giờ cao điểm.
- Tốc độ gió.
- Lượng mưa.
- Độ ẩm.
- Hiệu ứng của scenario.
- Nhiễu nhỏ.

Các scenario:

- `normal`
- `rush_hour_pollution`
- `rain_cleanup`
- `sudden_spike`
- `sensor_offline`

MQTT topic:

```text
airguard/stations/{station_id}/measurements
```

Payload bắt buộc:

```json
{
  "message_id": "MSG-S03-20260802T180000",
  "station_id": "S03",
  "pm25": 78.4,
  "temperature": 33.0,
  "humidity": 62,
  "wind_speed": 1.2,
  "wind_direction": 120,
  "rainfall": 0,
  "timestamp": "2026-08-02T18:00:00+07:00",
  "source": "simulator",
  "scenario": "sudden_spike",
  "quality_flag": "valid"
}
```

### Tiêu chí chấp nhận

- Cả 5 trạm đều publish được dữ liệu.
- Chu kỳ publish cấu hình được từ 10–30 giây.
- `message_id` là duy nhất.
- PM2.5 không âm.
- Timestamp có timezone.
- Backend bỏ qua message trùng.
- Trạm được đánh dấu offline sau timeout quy định.

---

## 12. Phát hiện PM2.5 cao và lỗi cảm biến

Alert Engine đánh giá dữ liệu bằng rule cố định.

Các rule ban đầu:

- Tạo cảnh báo khi PM2.5 vượt ngưỡng trong 3 measurement hợp lệ liên tiếp.
- Không tạo cảnh báo trùng trong khoảng cooldown.
- Tạo cảnh báo offline khi sensor ngừng gửi dữ liệu.
- Resolve cảnh báo khi điều kiện trở lại bình thường.

Mỗi cảnh báo gồm:

- Trạm.
- Loại cảnh báo.
- Severity.
- Giá trị quan sát.
- Ngưỡng.
- Timestamp.
- Trạng thái.

### Tiêu chí chấp nhận

- Scenario `sudden_spike` tạo được cảnh báo.
- Một measurement bất thường đơn lẻ không tự động tạo cảnh báo diện rộng.
- Không tạo cảnh báo trùng trong cooldown.
- Phát hiện được sensor offline.
- Việc tạo alert không phụ thuộc vào LLM.

---

## 13. Hỏi AI Agent về tình trạng hiện tại

Người dùng có thể đặt câu hỏi bằng ngôn ngữ tự nhiên.

Các dạng câu hỏi tối thiểu:

- “PM2.5 ở cổng chính hiện tại là bao nhiêu?”
- “Khu vực nào đang ô nhiễm nhất?”
- “So sánh công viên và trục đường chính.”
- “Tôi có nên chạy bộ tại khu thể thao không?”
- “Người nhạy cảm nên tránh khu vực nào?”
- “Vì sao S03 có cảnh báo?”
- “Sensor nào đang offline?”
- “Trong ba giờ tới PM2.5 có xu hướng thế nào?”

Agent phải:

1. Phân loại intent.
2. Xác định vị trí/trạm.
3. Chọn tool.
4. Gọi tool.
5. Đánh giá kết quả.
6. Trả lời có evidence.

### Tiêu chí chấp nhận

- Agent xử lý đúng tối thiểu 8/10 câu hỏi kiểm thử.
- Mọi số liệu môi trường đến từ tool.
- Câu trả lời có vị trí và timestamp.
- Agent nói rõ khi dữ liệu thiếu, stale hoặc invalid.
- Agent không khẳng định một khu vực “an toàn tuyệt đối”.

---

## 14. So sánh khu vực

Agent có thể so sánh hai hoặc nhiều trạm dựa trên measurement hợp lệ mới nhất.

Ví dụ:

> S03 — Trục đường chính hiện có PM2.5 là 78,4 µg/m³, trong khi S04 — Công viên là 24,7 µg/m³. Dựa trên dữ liệu cập nhật lúc 18:00, công viên là lựa chọn phù hợp hơn.

### Tiêu chí chấp nhận

- Các measurement được so sánh trong cùng khoảng thời gian gần nhất.
- Sensor offline hoặc dữ liệu stale được loại trừ hoặc ghi rõ.
- Câu trả lời có số liệu và timestamp.
- Agent không tự suy diễn nguyên nhân khi không có bằng chứng.

---

## 15. Khuyến nghị hoạt động ngoài trời

Agent đưa ra khuyến nghị dựa trên:

- PM2.5 hiện tại.
- Dự báo PM2.5.
- Thời tiết.
- Cảnh báo active.
- Hồ sơ người dùng.
- Trạng thái cảm biến.

Các nhóm hồ sơ:

- `normal`
- `sensitive`
- `outdoor_sport`

### Tiêu chí chấp nhận

- Khuyến nghị khác nhau theo nhóm người dùng.
- Người nhạy cảm nhận khuyến nghị thận trọng hơn.
- Agent đề xuất khu vực khác nếu có lựa chọn tốt hơn.
- Agent không chẩn đoán y tế.
- Câu trả lời có evidence.

---

## 16. Dự báo PM2.5 trong 1–3 giờ

Forecast Service dự báo PM2.5 cho từng trạm.

Các mô hình có thể thử:

- Persistence baseline.
- Moving Average.
- Linear Regression.
- Random Forest.
- Prophet nếu còn thời gian.

Các feature dự kiến:

- PM2.5 lịch sử.
- Giờ trong ngày.
- Ngày trong tuần.
- Nhiệt độ.
- Độ ẩm.
- Tốc độ gió.
- Lượng mưa.
- Loại vị trí.

Đánh giá bằng:

- MAE.
- RMSE.
- So sánh với persistence baseline.
- Tách riêng horizon 1 giờ, 2 giờ và 3 giờ.

### Tiêu chí chấp nhận

- Forecast có thời gian tạo và thời gian dự báo.
- Mô hình được so sánh với baseline.
- Ghi rõ nếu kết quả được đánh giá trên dữ liệu giả lập.
- Agent truy cập forecast qua tool.
- Không tuyên bố độ chính xác production.

---

## 17. Tạo Warning Proposal

Agent có thể tạo proposal khi:

- Có alert active.
- Measurement mới nhất hợp lệ.
- Sensor online.
- Evidence còn mới.
- Không có proposal pending trùng trong cooldown.

Proposal gồm:

- Trạm liên quan.
- PM2.5 quan sát được.
- Timestamp.
- Severity.
- Lý do.
- Evidence.
- Nội dung cảnh báo đề xuất.
- Trạng thái `pending`.

### Tiêu chí chấp nhận

- Proposal có đủ evidence để manager xem xét.
- Không tạo proposal từ dữ liệu invalid.
- Không tạo proposal trùng.
- Hành động tạo proposal được lưu audit log.
- Tạo proposal không đồng nghĩa tự động phát cảnh báo.

---

## 18. Approve hoặc Reject Proposal

Manager mở trang Approval và xem:

- Trạm.
- PM2.5.
- Timestamp.
- Severity.
- Weather context.
- Lý do của Agent.
- Nội dung cảnh báo đề xuất.

Manager có thể approve hoặc reject và nhập review note.

### Tiêu chí chấp nhận

- Chỉ manager hoặc admin được review.
- Chỉ proposal `pending` được review.
- Hệ thống lưu reviewer, timestamp, quyết định và ghi chú.
- Quyết định được lưu audit log.
- Proposal bị reject không được phát cảnh báo.
- MVP có thể chỉ demo trạng thái duyệt, chưa cần tích hợp hệ thống gửi thông báo thương mại.

---

## 19. Nghiên cứu người dùng

### 19.1 Người dùng có hiểu số PM2.5 thô không?

Giả định hiện tại: đa số người dùng cần mức phân loại và khuyến nghị, không chỉ một con số.

Kế hoạch xác thực:

- Kiểm thử với ít nhất 5 người.
- Yêu cầu người dùng giải thích một giá trị PM2.5 khi chưa có hướng dẫn.
- So sánh mức hiểu trước và sau khi xem giải thích của Agent.

**Trạng thái:** Chưa thực hiện.

### 19.2 Người dùng thích bản đồ hay danh sách?

Giả định hiện tại: bản đồ hữu ích hơn vì quyết định phụ thuộc vị trí.

Kế hoạch xác thực:

- Cho người dùng xem prototype bản đồ và danh sách.
- Hỏi giao diện nào giúp chọn khu vực nhanh hơn.

**Trạng thái:** Chưa thực hiện.

### 19.3 Thông tin nào làm khuyến nghị AI đáng tin?

Giả định hiện tại: người dùng cần số PM2.5, vị trí, timestamp, nguồn và evidence.

Kế hoạch xác thực:

- So sánh câu trả lời có và không có evidence card.
- Hỏi người dùng tin câu trả lời nào hơn.

**Trạng thái:** Chưa thực hiện.

### 19.4 Manager cần gì trước khi duyệt cảnh báo?

Giả định hiện tại: manager cần giá trị hiện tại, ngưỡng, xu hướng, timestamp, nhóm bị ảnh hưởng, thời tiết và lý do của Agent.

Kế hoạch xác thực:

- Review wireframe với Mentor hoặc người đại diện.
- Ghi lại trường thông tin cần thêm hoặc bỏ.

**Trạng thái:** Chờ xác nhận.

### 19.5 Sensor giả lập có được chấp nhận không?

Đề xuất hiện tại:

- Dùng bản đồ thật.
- Dùng Weather API thật khi có thể.
- Dùng telemetry PM2.5 giả lập qua MQTT.
- Gắn nhãn rõ mọi dữ liệu giả lập.

**Trạng thái:** Cần Mentor xác nhận.

---

## 20. Nghiên cứu kỹ thuật

### 20.1 Vì sao dùng MQTT?

MQTT phù hợp cho telemetry nhẹ từ nhiều sensor và giúp mô phỏng đúng mô hình IoT.

Quyết định:

- Dùng Mosquitto làm broker.
- Dùng Paho MQTT cho publisher và consumer.
- Frontend lấy dữ liệu qua REST API, không truy cập MQTT trực tiếp.

### 20.2 Vì sao dùng Rule Engine thay vì LLM cho cảnh báo?

Ngưỡng và trạng thái sensor phải xác định, kiểm thử được và lặp lại được.

Quyết định:

- Rule Engine tạo alert.
- Agent giải thích alert và tạo đề xuất.
- LLM không quyết định ngưỡng số.

### 20.3 Vì sao dùng LangGraph?

Workflow Agent gồm nhiều bước có kiểm soát:

- Phân loại intent.
- Xác định vị trí.
- Chọn tool.
- Gọi tool.
- Đánh giá rủi ro.
- Tạo proposal.

Quyết định:

- Dùng LangGraph nhỏ cho Agent.
- Không dùng LangGraph cho MQTT ingestion, CRUD hoặc train forecast.

### 20.4 Vì sao dùng PostgreSQL?

Hệ thống cần:

- Quan hệ dữ liệu rõ ràng.
- Truy vấn theo thời gian.
- Unique constraint.
- Audit log.
- Proposal và role.

Quyết định:

- PostgreSQL là nguồn dữ liệu chính.
- Redis, RabbitMQ và Celery chưa bắt buộc cho MVP ban đầu.

### 20.5 Đánh giá forecast như thế nào?

Mô hình phức tạp không đồng nghĩa tốt hơn.

Quyết định:

- Bắt đầu bằng persistence baseline.
- Chia train/test theo thời gian.
- Báo cáo MAE và RMSE.
- Chỉ giữ mô hình phức tạp hơn khi cải thiện rõ ràng.

### 20.6 Giảm hallucination như thế nào?

Quyết định:

- Mọi số liệu môi trường phải đến từ tool.
- Tool trả output có cấu trúc.
- Câu trả lời có evidence.
- Có guardrail cho dữ liệu stale và invalid.
- Dùng bộ kiểm thử ít nhất 10 câu hỏi.
- LLM không truy cập database trực tiếp.

---

## 21. Tiêu chí thành công

- 5 sensor giả lập publish dữ liệu qua MQTT.
- Backend lưu measurement hợp lệ và không trùng.
- Dashboard hiển thị đúng dữ liệu mới nhất của 5 trạm.
- Phát hiện được sensor offline.
- Alert Engine xử lý đúng các scenario demo.
- Forecast Service báo cáo MAE và RMSE so với baseline.
- Agent trả lời đúng tối thiểu 8/10 câu hỏi kiểm thử.
- 100% số liệu môi trường trong câu trả lời đến từ tool.
- Agent hỗ trợ khuyến nghị cho 3 nhóm người dùng.
- Agent không tạo proposal từ dữ liệu invalid, stale hoặc sensor offline.
- Manager approve hoặc reject proposal thành công.
- Ít nhất 3 kịch bản end-to-end chạy thành công.
- Không có lỗi blocking trong buổi demo.

---



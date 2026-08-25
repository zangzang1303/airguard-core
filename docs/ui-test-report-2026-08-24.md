# Báo cáo test UI — Hỏi AI

- Ngày: 24/08/2026
- Phạm vi: AirGuard AI, frontend local tại `http://localhost:5173`
- Chế độ thử: Windows Control / Any App trên Microsoft Edge
- Câu hỏi kiểm thử: `Chất lượng môi trường tại S05 hiện tại thế nào?`

## Kết quả

| ID | Hạng mục | Kết quả | Ghi chú |
|---|---|---|---|
| UI-01 | Mở frontend local | PASS | Trang AirGuard AI tải được trên Edge. |
| UI-02 | Vào chế độ demo Cư dân | PASS | Dashboard hiển thị dữ liệu mô phỏng. |
| UI-03 | Tải bản đồ và trạng thái trạm | PASS sau thử lại | Lần đầu gặp `Failed to fetch`/abort; nút “Thử lại” tải được dashboard. |
| UI-04 | Mở nút “Hỏi AI” | PASS | Panel “AirGuard Geospatial AI” mở ở bên phải. |
| UI-05 | Hiển thị lời chào và ô nhập | PASS | Có lời chào Agent, câu hỏi gợi ý, ô nhập và nút gửi. |
| UI-06 | Nhập câu hỏi bằng tab trình duyệt mới | PASS | Đã nhập được câu hỏi vào ô `Hỏi về cung đường chạy bộ, ô nhiễm, so sánh...`. |
| UI-07 | Gửi câu hỏi bằng UI | FAIL | UI hiển thị lỗi “Không thể kết nối tới dịch vụ AI Agent hoặc xảy ra lỗi mạng”; console ghi `Fetch to /api/v1/agent/chat failed: Failed to fetch`. |
| API-01 | Gửi cùng câu hỏi qua backend Agent | PASS | `POST /api/v1/agent/chat` trả response 200 và câu trả lời có evidence sensor cho S05/điểm tương ứng. |
| API-02 | Kiểm tra dữ liệu phản hồi | PASS | Response có AQI 149, PM2.5 55.1 µg/m³, timestamp, intent và map actions. |

## Kết luận

Luồng UI đã mở được đến panel Hỏi AI và nhập được câu hỏi trong tab mới. Khi gửi, frontend không gọi thành công `POST /api/v1/agent/chat`, dù backend endpoint hoạt động khi gọi trực tiếp từ máy. Cần điều tra lỗi kết nối/CORS/abort giữa trình duyệt và API.

Không thay đổi code ứng dụng trong lần test này.

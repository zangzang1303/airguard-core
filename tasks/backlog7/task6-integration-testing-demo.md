# Task B7-06: Kiểm Thử Tích Hợp Toàn Diện & Kịch Bản Demo 2 Phút "Ăn Điểm"

> **Người phụ trách:** QA Lead & Toàn bộ Đội ngũ Dự án  
> **Thời hạn dự kiến:** Ngày 3 - Ngày 4  
> **Mục tiêu:** 
> 1. Chạy kiểm thử toàn bộ hệ thống từ IoT Ingestion đến UI, đảm bảo 100% test case pass xanh.
> 2. Xác thực cấu hình Docker Compose 8 containers hoạt động ổn định trên môi trường local và cloud.
> 3. Chuẩn bị kịch bản **Live Demo 120 Giây Kịch Tính** thể hiện trọn vẹn cả 5 tính năng đột phá trước Hội đồng Ban Giám khảo.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Đồng bộ & Sửa các Contract Tests còn tồn đọng
- **Mục tiêu**: Đảm bảo 100% test case trong repository đều pass xanh (`pytest`).
- **Nhiệm vụ cụ thể**:
  1. Đồng bộ lại các chuỗi token trong `tests/test_frontend/` để khớp với kiến trúc UI component mới của React 18.
  2. Khắc phục lỗi `social.greeting` trong `tests/agent/eval_cases.json` để toàn bộ 62 Golden Cases và comprehensive test đạt 100%.

### 1.2. Kiểm tra Hạ tầng Docker Compose 8 Containers
- **File cấu hình**: [`docker-compose.yml`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/docker-compose.yml)
- **Danh sách 8 containers cần kiểm tra khởi động đồng thời**:
  1. `mosquitto`: MQTT Broker cổng 1883.
  2. `postgres`: Database cổng 5432.
  3. `sensor-simulator`: Phát telemetry 5 trạm định kỳ 10s.
  4. `mqtt-consumer`: Validate và lưu dữ liệu vào Postgres.
  5. `backend`: FastAPI API cổng 8000.
  6. `agent`: LangGraph Agent cổng 8001.
  7. `device-simulator`: Nhận lệnh thông gió và phản hồi ACK.
  8. `frontend`: React/Vite dashboard cổng 5173.

---

## 2. KỊCH BẢN LIVE DEMO 120 GIÂY "WOW" TRƯỚC BAN GIÁM KHẢO

Kịch bản demo được thiết kế liên hoàn để **chứng minh sức mạnh của cả 5 tính năng trong vòng 2 phút**:

```mermaid
sequenceDiagram
    autonumber
    actor Presenter as Người Thuyết Trình
    participant UI as Giao diện Dashboard (5173)
    participant Sim as Simulator Controller
    participant Agent as AI Chatbot
    participant BQL as Manager Approvals

    Presenter->>UI: 1. Giới thiệu Bản đồ nhiệt IDW & Lớp Hạt Gió Động (Wind Streamlines)
    Presenter->>UI: 2. Bấm [Play 24h Simulation]: Tua nhanh đợt sóng ô nhiễm 24h & chỉ ra "Khung Giờ Vàng"
    Presenter->>Sim: 3. Kích hoạt sự cố: Tăng vọt PM2.5 tại Trạm S03 (Hồ Ngọc Trai) lên 165
    Sim-->>UI: Bản đồ nhiệt chuyển màu Tím và lan theo hướng gió
    Presenter->>Agent: 4. Hỏi Chatbot: "Tôi định chạy bộ 5km quanh hồ, có an toàn không?"
    Agent-->>Presenter: Phản hồi: Tính liều lượng bụi hít phải (115 µg ~ 2.5 điếu thuốc), tự động vẽ Lộ Trình Sạch sang VinUni
    Presenter->>BQL: 5. Đăng nhập vai trò Ban Quản Lý: Hiển thị Layer Thiết Bị Thông Gió
    Note over BQL: Đề xuất [Ventilation Boost 45p] xuất hiện ở trạng thái Pending
    Presenter->>BQL: 6. BQL bấm [Phê Duyệt / Approve]
    BQL-->>UI: Marker quạt DEV-S03-FAN bắt đầu quay và phát sáng Cyan (Running Boost)
    Note over UI: Vòng lặp phản hồi: PM2.5 giảm từ 88 xuống 35 -> Bản đồ nhiệt chuyển từ TÍM sang XANH
    Presenter->>UI: 7. Mở Báo Cáo ESG & Tải file PDF Báo cáo Tuần hoàn chỉnh có đầy đủ biểu đồ
```

---

## 3. LỆNH KIỂM THỬ TỔNG HỢP TRƯỚC KHI SUBMIT

```powershell
# 1. Chạy toàn bộ test suite Backend, Agent, IoT
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/ -v

# 2. Chạy đánh giá Agent Golden Cases
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\python" eval/run_evaluation.py

# 3. Chạy đánh giá Forecast Benchmark
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\python" eval/run_prophet_benchmark.py

# 4. Build Frontend Production
npm --prefix frontend run build
```

---

## 4. TIÊU CHUẨN NGHIỆM THU CUỐI CÙNG (DEFINITION OF DONE)

1. ✅ 100% test cases pass xanh không lỗi.
2. ✅ Lệnh `docker compose up -d --build` khởi động trơn tru toàn bộ 8 services.
3. ✅ Kịch bản Live Demo chạy mượt mà không có bất kỳ độ trễ hay lỗi logic nào.

# Task B7-04: Tự Động Điều Tiết Thông Gió, Hiển Thị Thiết Bị Trên Map & HITL Audit Trail

> **Người phụ trách:** Backend Engineer, Frontend Map Specialist & AI Agent Lead  
> **Thời hạn dự kiến:** Ngày 2 - Ngày 3  
> **Mục tiêu:** 
> 1. Xây dựng dịch vụ giám sát ô nhiễm liên tục (Continuity Window 15-20 phút) để tự động tạo đề xuất kích hoạt thông gió (`ventilation_boost`) hoặc tiết kiệm điện (`eco_mode`).
> 2. Thiết kế Layer hiển thị thiết bị thông gió trực quan trên Map **dành riêng cho Ban Quản Lý (Manager-Only)** với hiệu ứng trạng thái động.
> 3. Xây dựng **Vòng lặp Phản hồi Môi trường (Closed-Loop Feedback)**: Khi quạt bật, nồng độ PM2.5/CO2 giảm thực tế và bản đồ nhiệt chuyển từ Đỏ ➔ Xanh.
> 4. Nâng cấp AI Agent nhận biết trạng thái, thời gian chạy còn lại và tư vấn bật/tắt hợp lý.
> 5. Đảm bảo quy trình phê duyệt nghiêm ngặt của Ban Quản lý (HITL) và ghi vết Audit Trail bất biến.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Hiển Thị Thiết Bị Thông Gió Trên Map (Manager-Only UI)
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/map/SuperMap.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/SuperMap.tsx)
  - [`frontend/src/features/map/VentilationDeviceMarkers.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/map/) *(Component mới)*
  - [`frontend/src/features/drawers/DeviceDetailDrawer.tsx`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/drawers/) *(Component mới)*
- **Nhiệm vụ cụ thể**:
  1. **Phân quyền hiển thị (Manager/Admin Only)**:
     - Chỉ người dùng đăng nhập có `role === 'manager'` hoặc `'admin'` mới hiển thị Toggle switch **"Hiển thị Thiết bị Thông gió"** trong menu lớp bản đồ (Layer Controls).
     - Cư dân bình thường (`role === 'resident'`) **hoàn toàn không nhìn thấy** layer này để tránh làm rối bản đồ và bảo mật sơ đồ hạ tầng kỹ thuật của khu đô thị.
  2. **Biểu tượng Thiết bị Động (Animated Fan Markers)**:
     - 🌀 **Đang chạy Tăng cường (`BOOST` - 80-100% công suất)**: Icon quạt gió màu Cyan/Xanh dương xoay tròn nhẹ kèm vòng sáng Pulse tỏa xung quanh.
     - 🍃 **Chế độ Tiết kiệm (`ECO_MODE` - 30% công suất)**: Icon màu xanh lá cây tĩnh.
     - ⚪ **Chế độ Nghỉ / Tắt (`STANDBY / OFF`)**: Icon màu xám nhạt.
  3. **Popup / Drawer Chi tiết Thiết bị (Device Details)**:
     - Nhấp vào Marker quạt thông gió sẽ mở bảng thông tin:
       * Mã thiết bị (VD: `DEV-S03-FAN`), trạm phục vụ (`S03 - Hồ Ngọc Trai`).
       * Trạng thái hoạt động (`Running Boost`, `Eco Mode`, `Standby`).
       * Công suất quạt (`80%`).
       * **Thời gian chạy còn lại (Đếm ngược)**: VD *"Còn 28 phút / tổng 45 phút"*.
       * Lịch sử lệnh gần nhất (Ai duyệt, lúc mấy giờ).
       * Nút can thiệp cưỡng bức của BQL: `[Chuyển Eco Mode]` hoặc `[Dừng khẩn cấp]`.

---

### 1.2. Vòng Lặp Phản Hồi Môi Trường Thực Tế (Closed-Loop Environmental Feedback)
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/live_telemetry_engine.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/live_telemetry_engine.py)
  - [`services/sensor-simulator/sensor_simulator.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/services/sensor-simulator/sensor_simulator.py)
  - [`backend/app/services/ventilation_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/ventilation_service.py)
- **Nhiệm vụ cụ thể**:
  1. **Mô hình suy giảm ô nhiễm khi Bật Quạt**:
     - Khi Manager bấm Approve lệnh `ventilation_boost` cho trạm $S_i$ (thời lượng 45 phút, công suất $80\%$):
     - Telemetry Engine và Simulator kích hoạt hệ số làm sạch (Air Cleansing Decay Rate):
       $$\text{PM2.5}(t) = (\text{PM2.5}_{\text{initial}} - \text{PM2.5}_{\text{clean}}) \cdot e^{-0.08 \cdot \Delta t} + \text{PM2.5}_{\text{clean}}$$
       $$\text{CO2}(t) = (\text{CO2}_{\text{initial}} - 450) \cdot e^{-0.06 \cdot \Delta t} + 450$$
     - *Hiệu ứng*: Trong vòng 10–15 phút sau khi duyệt bật quạt, nồng độ PM2.5 tại trạm giảm thực tế từ $85\text{ µg/m³} \rightarrow 32\text{ µg/m³}$, CO2 giảm từ $1100\text{ ppm} \rightarrow 520\text{ ppm}$.
  2. **Phản ánh trực quan tức thì lên Bản đồ nhiệt (Heatmap Feedback)**:
     - Khi dữ liệu trạm đo giảm xuống, thuật toán IDW Heatmap tự động tính toán lại, vùng nhiệt xung quanh trạm chuyển dần từ **Màu Đỏ/Tím (Ô nhiễm) $\rightarrow$ Màu Vàng $\rightarrow$ Màu Xanh Lá Cây (Trong lành)**.
  3. **Tự động đề xuất chuyển sang Eco Mode (Recovery Cycle)**:
     - Sau khi quạt chạy và chất lượng không khí duy trì ở mức An toàn ($\text{PM2.5} < 25\text{ µg/m³}$ và $\text{CO2} < 700\text{ ppm}$) trong $\ge 20\text{ phút}$:
     - Hệ thống tự động sinh Proposal `eco_mode` ở trạng thái `pending` để BQL duyệt chuyển về chế độ tiết kiệm năng lượng.

---

### 1.3. Nâng Cấp AI Agent Nhận Biết Trạng Thái & Thời Gian Điều Khiển Thiết Bị
- **File cần hoàn thiện / tinh chỉnh**:
  - [`src/agents/tools/contracts.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/tools/contracts.py)
  - [`backend/app/services/geospatial_agent_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/geospatial_agent_service.py)
  - [`backend/app/services/approval_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/approval_service.py)
- **Nhiệm vụ cụ thể**:
  1. **Bổ sung Tool Truy Vấn Thiết Bị**: Thêm tool `get_ventilation_devices_status` trả về danh sách các thiết bị, trạng thái hoạt động, thời gian bắt đầu, thời gian kết thúc dự kiến và mức giảm ô nhiễm đo được.
  2. **Khả năng Tư vấn của AI Agent**:
     - Khi **BQL** hỏi: *"Hệ thống thông gió ở S03 đã chạy được bao lâu rồi, hiệu quả ra sao?"*
       $\rightarrow$ **Agent**: *"Quạt thông gió DEV-S03-FAN tại Tòa S2.01 đang chạy chế độ Boost (công suất 80%) được 22 phút, còn lại 23 phút. Nồng độ PM2.5 đã giảm từ 88 xuống còn 38 µg/m³ (giảm 56%). Dự kiến sau 10 phút nữa trạm sẽ đạt chuẩn không khí trong lành và đủ điều kiện chuyển về Eco Mode."*
     - Khi **Cư dân** hỏi: *"Khu vực Hồ Ngọc Trai sao thấy không khí đang tốt dần lên?"*
       $\rightarrow$ **Agent**: *"Hệ thống quạt thông gió và thanh lọc không khí công cộng tại khu vực Hồ Ngọc Trai đang được vận hành để giải tỏa khói bụi, các chỉ số ô nhiễm đang giảm mạnh và dự kiến sẽ đạt mức rất trong lành trong 15 phút tới."*

---

### 1.4. Backend Core, HITL & Audit Trail Bất Biến
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/approval_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/approval_service.py)
  - [`backend/app/services/audit_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/audit_service.py)
  - [`services/device-simulator/device_simulator.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/services/device-simulator/device_simulator.py)
- **Nhiệm vụ cụ thể**:
  1. **Quy trình Phê duyệt HITL**:
     - Mọi đề xuất `WarningProposal` sinh ra ở trạng thái `pending`.
     - Chỉ BQL (`manager`/`admin`) có quyền Approve hoặc Reject.
     - Sau khi Approve $\rightarrow$ Tạo lệnh `device_commands` và bắn tin MQTT xuống `device-simulator`.
     - Device Simulator phản hồi ACK status `succeeded`.
  2. **Audit Trail Bất biến**: Mọi sự kiện từ tạo đề xuất, duyệt lệnh, dispatch, thực thi, đến tự động phục hồi đều ghi vào bảng `audit_logs` có trigger ngăn chặn UPDATE/DELETE.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_approval_api.py tests/test_backend/test_audit_api.py tests/test_backend/test_automatic_proposals.py -v
```

### 2.2. Kịch bản Test Live End-to-End (Vòng lặp Phản hồi Hoàn chỉnh)
1. **Bước 1 (Gây ô nhiễm)**: Chọn kịch bản simulator tăng vọt PM2.5 tại trạm S03 lên $120\text{ µg/m³}$. Bản đồ nhiệt quanh S03 chuyển màu Tím.
2. **Bước 2 (Tạo đề xuất)**: Sau thời gian ngưỡng, đề xuất `ventilation_boost` xuất hiện trong Approvals Drawer của BQL.
3. **Bước 3 (Duyệt lệnh)**: BQL đăng nhập và bấm **[Phê Duyệt]**.
4. **Bước 4 (Quan sát thiết bị & Môi trường)**:
   - Trên bản đồ: Marker quạt gió tại S03 bắt đầu xoay tròn và phát sáng Cyan (Running Boost).
   - Nồng độ PM2.5 tại S03 giảm dần trên biểu đồ thời gian thực.
   - Bản đồ nhiệt quanh S03 chuyển dần từ Tím $\rightarrow$ Đỏ $\rightarrow$ Vàng $\rightarrow$ Xanh lá cây.
5. **Bước 5 (Hỏi Chatbot AI)**: Hỏi chatbot *"Trạng thái quạt ở S03 thế nào?"* $\rightarrow$ Chatbot trả lời chính xác thời gian chạy còn lại và hiệu quả giảm ô nhiễm.
6. **Bước 6 (Tự động Eco Mode & Audit)**: Sau khi sạch 20 phút, hệ thống tự động sinh đề xuất `eco_mode` và Audit Log ghi nhận đầy đủ hành trình.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ Layer thiết bị thông gió trên bản đồ chỉ hiển thị khi đăng nhập tài khoản Quản lý (`manager`/`admin`).
2. ✅ Icon thiết bị hiển thị đúng trạng thái động (Xoay/Pulse khi Boost, Xanh khi Eco, Xám khi Off).
3. ✅ Khi quạt bật Boost, số liệu PM2.5/CO2 tại trạm đó giảm thực tế và bản đồ nhiệt Heatmap đổi màu theo thời gian thực.
4. ✅ AI Agent trả lời chính xác thời gian chạy, thời gian còn lại và khuyến nghị bật/tắt hợp lý.
5. ✅ 100% lệnh điều khiển thiết bị được bảo vệ bởi HITL và lưu vết vào Audit Trail.

---

## 4. TRẠNG THÁI TRIỂN KHAI (29/08/2026)

- ✅ Continuity gate mặc định 15 phút; recovery gate nghiêm ngặt `PM2.5 < 25` và `CO2 < 700` liên tục 20 phút.
- ✅ Device simulator ACK kèm station/action/thời gian chạy; sensor simulator áp dụng exponential decay cho PM2.5 và CO2 đến khi hết chu kỳ 45 phút.
- ✅ API trạng thái thiết bị trả mode, countdown, lệnh/người duyệt gần nhất và hiệu quả đo trước/sau ACK.
- ✅ Layer thiết bị và drawer chỉ được render cho Manager/Admin; thao tác Eco/Standby chỉ tạo proposal `pending`.
- ✅ Agent có tool `get_ventilation_devices_status` và trả lời grounded về thời gian chạy, thời gian còn lại, xu hướng hiệu quả.
- ✅ MQTT dispatch, ACK correlation và audit append-only tiếp tục đi qua luồng approval server-side hiện có.

### Kết quả kiểm tra

- `584 passed`: toàn bộ `tests/test_backend`, `tests/test_agents`, `tests/test_iot`.
- `176 passed`: bộ test trọng tâm Task 4 và các contract liên quan.
- `9 passed`: contract map/heatmap refresh của Task 4.
- `ruff check`, `compileall`, `git diff --check`, `npm run build`, `docker compose config --quiet`: đạt.
- Smoke test Compose: backend và Agent health đạt; `/api/v1/ventilation-devices?station_id=S03` trả dữ liệu simulator; Agent gọi đúng tool trạng thái thiết bị.
- Bộ frontend toàn repo còn 11 regression contract cũ ngoài Task 4 (navigation/search/default legend) sau khi đã sửa lỗi heatmap refresh thuộc Task 4.

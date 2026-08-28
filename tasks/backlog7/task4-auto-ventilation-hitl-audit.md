# Task B7-04: Tự Động Điều Tiết Thông Gió & HITL Audit Trail

> **Người phụ trách:** Backend Engineer & DevOps / Security Lead  
> **Thời hạn dự kiến:** Ngày 2 - Ngày 3  
> **Mục tiêu:** Hoàn thiện dịch vụ giám sát ô nhiễm liên tục (Continuity Window 15-20 phút) để tự động tạo đề xuất kích hoạt thông gió (`ventilation_boost`) hoặc tiết kiệm năng lượng (`eco_mode`), đảm bảo quy trình phê duyệt nghiêm ngặt của Ban Quản lý (HITL) và ghi vết Audit Trail bất biến.

---

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Core & HITL Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/ventilation_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/ventilation_service.py)
  - [`backend/app/services/automatic_proposal_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/automatic_proposal_service.py)
  - [`backend/app/services/approval_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/approval_service.py)
  - [`backend/app/services/audit_service.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/audit_service.py)
  - [`services/device-simulator/device_simulator.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/services/device-simulator/device_simulator.py)
- **Nhiệm vụ cụ thể**:
  1. **Quy tắc Kiểm tra Tính Liên Tục (Continuity Assessment)**:
     - Tăng tốc thông gió (`ventilation_boost`): PM2.5 $\ge 50\text{ µg/m³}$ hoặc CO2 $\ge 1000\text{ ppm}$ liên tục trong $\ge 15\text{ phút}$, không có khoảng trống mất kết nối $> 60\text{s}$.
     - Phục hồi chế độ tiết kiệm (`eco_mode`): Khi PM2.5 $< 25\text{ µg/m³}$ và CO2 $< 700\text{ ppm}$ duy trì liên tục trong $\ge 20\text{ phút}$.
  2. **Quản lý Vòng đời Đề xuất (State Machine)**:
     - Tạo đề xuất `WarningProposal` ở trạng thái `pending` với khóa Idempotency ổn định `uuid5(station_id, policy_version)`.
     - Hết hạn tự động sau $60\text{ phút}$ (TTL) nếu không có Manager duyệt.
  3. **Phân quyền Phê duyệt & Điều phối Thiết bị (RBAC & Dispatcher)**:
     - Chỉ user có vai trò `manager` hoặc `admin` mới được gọi API `POST /api/v1/proposals/{id}/approve` hoặc `reject`.
     - Khi Approve ➔ Tạo bản ghi `device_commands` và publish tin nhắn MQTT sang topic `airguard/devices/{device_id}/command`.
     - Nhận phản hồi ACK từ `device-simulator` để cập nhật trạng thái `succeeded`.
  4. **Ghi vết Audit Trail Bất biến (Append-only Audit Log)**: Ghi nhận mọi sự kiện: `proposal.created`, `proposal.approved`, `proposal.rejected`, `command.dispatched`, `command.executed`.

### 1.2. Frontend Approvals & Audit UI
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/approvals/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/approvals/) (Manager Approval Panel / Drawer)
  - [`frontend/src/features/audit/`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/src/features/audit/) (Audit Log Viewer)
- **Nhiệm vụ cụ thể**:
  1. **Giao diện Phê duyệt BQL**: Hiển thị danh sách đề xuất chờ duyệt, lý do kích hoạt, biểu đồ trích xuất bằng chứng (Evidence), nút [Phê Duyệt] (Xanh) và [Từ Chối] (Đỏ) kèm ô nhập lý do.
  2. **Badge Thông báo Chờ duyệt**: Hiển thị số lượng đề xuất `pending` trên thanh điều hướng của Quản lý.
  3. **Bảng Lịch sử Audit Trail**: Hiển thị bảng nhật ký hệ thống có phân trang, lọc theo loại hành động và thời gian.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& "d:\CODE\AITHUCCHIEN\BUILD\P-074\.venv\Scripts\pytest" tests/test_backend/test_approval_api.py tests/test_backend/test_audit_api.py tests/test_backend/test_automatic_proposals.py tests/test_agents/test_proposals.py -v
```

### 2.2. Test kịch bản thực tế (End-to-End Test Scenario)
1. **Bước 1**: Bật simulator kịch bản ô nhiễm tại trạm S03.
2. **Bước 2**: Sau 15 phút (hoặc tua nhanh thời gian test), kiểm tra database: Bảng `approval_requests` xuất hiện bản ghi `pending`.
3. **Bước 3**: Đăng nhập tài khoản `manager1`, mở **Approvals Drawer**, bấm **[Phê Duyệt]**.
4. **Bước 4**: Quan sát log terminal của `device-simulator`:
   ```text
   [DeviceSimulator] Received command: ventilation_boost on device DEV-S03-FAN
   [DeviceSimulator] Executing boost mode at 80% intensity for 45 mins. Status: Succeeded
   ```
5. **Bước 5**: Mở **Audit Log Viewer**: Bản ghi duyệt lệnh được hiển thị minh bạch.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ 100% đề xuất khởi tạo ở trạng thái `pending`, không có kịch bản nào bypass được qua tầng BQL.
2. ✅ Tài khoản `resident` khi cố tình gọi API approve nhận mã lỗi `403 Forbidden`.
3. ✅ Bảng `audit_logs` không cho phép sửa đổi hoặc xóa (Append-only).

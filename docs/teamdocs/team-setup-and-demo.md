# AirGuard AI — Hướng dẫn setup và demo cho cả nhóm

Tài liệu này dành cho thành viên mới muốn chạy toàn bộ MVP AirGuard AI trên Windows.
Hệ thống dùng dữ liệu simulator, chỉ phục vụ học tập/demo; không phải hệ thống quan trắc
chính thức và không dùng cho quyết định y tế hoặc pháp lý.

## 1. Thành phần hệ thống

```text
Sensor simulator -> MQTT Mosquitto -> MQTT consumer -> PostgreSQL
                                                      |
                              FastAPI backend <--------+
                                  |  \
                                  |   -> Agent (LangGraph/tool calling)
                                  |
                              React frontend

Manager approval -> audit log -> device simulator (nếu proposal có device command)
```

Các địa chỉ sau khi chạy:

| Thành phần | Địa chỉ |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Backend Swagger | http://localhost:8000/docs |
| Agent | http://localhost:8001 |
| PostgreSQL | localhost:5432 |
| MQTT | localhost:1883 |

## 2. Yêu cầu cài đặt

- Windows 10/11
- Docker Desktop, bật Linux containers
- Git
- (Tuỳ chọn, chỉ khi chạy frontend ngoài Docker) Node.js 20+ và npm
- (Tuỳ chọn, chỉ khi chạy Python ngoài Docker) Python 3.11+

Kiểm tra Docker trước khi làm việc:

```powershell
docker version
docker compose version
```

Nếu gặp lỗi `failed to connect to the Docker API`, hãy mở Docker Desktop và chờ đến khi
trạng thái Docker Engine là running.

## 3. Lấy source và tạo file môi trường

```powershell
git clone https://github.com/AI20K-Build-Phase-Cohort-3/P-074.git
cd P-074
git checkout develop
git pull origin develop
```

Tạo `.env` một lần duy nhất. Không commit file này:

```powershell
if (!(Test-Path .env)) {
  Copy-Item .env.example .env
}
```

Kiểm tra Compose có hợp lệ:

```powershell
docker compose config --quiet
```

## 4. Khởi tạo PostgreSQL và MQTT

Khởi động hai dependency trước:

```powershell
docker compose up -d postgres mqtt
docker compose ps
```

Chờ `postgres` có trạng thái `healthy`, sau đó áp dụng schema và seed demo:

```powershell
.\scripts\init-demo-db.ps1
```

Script trên có tính idempotent, có thể chạy lại trên database demo hiện có. Kiểm tra 5 trạm:

```powershell
docker compose exec postgres `
  psql -U airguard -d airguard `
  -c "SELECT station_id, station_name FROM stations ORDER BY station_id;"
```

Kết quả cần có S01, S02, S03, S04 và S05.

## 5. Khởi động toàn bộ hệ thống

```powershell
docker compose up -d --build `
  backend agent frontend mqtt-consumer `
  sensor-simulator device-simulator
```

Kiểm tra container:

```powershell
docker compose ps
```

Các service chính cần ở trạng thái `Up`; PostgreSQL cần `healthy`.

Kiểm tra API:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
Invoke-RestMethod http://localhost:8001/health
Invoke-RestMethod http://localhost:8000/api/v1/stations
```

## 6. Mở giao diện

Mở trình duyệt tại:

```text
http://localhost:5173
```

Nếu port 5173 đang bị một Vite process cũ chiếm, chạy frontend local ở port khác:

```powershell
npm.cmd --prefix frontend run dev -- `
  --host 127.0.0.1 `
  --port 5174
```

Sau đó mở:

```text
http://localhost:5174
```

Nếu chạy frontend local mà muốn gọi backend Docker, backend vẫn phải đang chạy ở
`http://localhost:8000`.

## 7. Tài khoản demo

Mật khẩu chung:

```text
AirGuard@2026
```

| Vai trò | Email | Quyền demo |
|---|---|---|
| Resident | `resident@vinuni.edu.vn` | Dashboard, station, forecast, AI Agent, alerts, profile |
| Manager | `manager@vinuni.edu.vn` | Toàn bộ quyền Resident + approval và audit log |
| Admin | `admin@vinuni.edu.vn` | Admin dashboard, user, station, IoT và settings |

Đây là identity demo ở frontend, không phải credential production.

### Cách đăng nhập từng bước

1. Mở `http://localhost:5173` (hoặc `http://localhost:5174` nếu chạy frontend local ở port 5174).
2. Chờ màn hình **Đăng nhập AirGuard AI** xuất hiện.
3. Nhập một trong các email demo ở bảng trên.
4. Nhập đúng mật khẩu `AirGuard@2026`.
5. Bấm **Đăng nhập**.
6. Sau khi đăng nhập thành công, hệ thống đưa về Dashboard tương ứng với vai trò.

Nếu muốn chọn nhanh tài khoản có sẵn, dùng nút tài khoản demo trên màn hình Login (nếu giao diện
đang hiển thị các nút Resident/Manager/Admin), sau đó kiểm tra email và vai trò trước khi demo.

### Phạm vi sau khi đăng nhập

- **Resident**: thấy Dashboard, bản đồ/trạm, lịch sử, forecast, Compare, AI Agent, Alerts và Profile.
- **Manager**: có thêm Approval Queue và Audit Log; chỉ Manager mới được approve/reject proposal.
- **Admin**: vào Admin Dashboard và các module quản trị user, station, IoT device, settings.

Nếu một menu không xuất hiện, hãy kiểm tra đúng tài khoản/role đang dùng; không tự đổi role trong
trình duyệt để vượt qua RBAC.

### Đăng xuất và đổi tài khoản

1. Bấm avatar/tên người dùng ở góc phải hoặc nút **Đăng xuất** trong sidebar.
2. Sau khi trở về màn hình Login, nhập tài khoản khác.
3. Nếu giao diện vẫn hiển thị phiên cũ, refresh trang bằng `Ctrl + F5` rồi đăng nhập lại.

Tài khoản đăng ký mới chỉ tồn tại trong memory của phiên trình duyệt và luôn có role Resident;
refresh trang có thể làm mất tài khoản đó. Manager/Admin chỉ dùng tài khoản seed ở trên.

### Thông tin kỹ thuật cho người kiểm thử API

Frontend demo tự quản lý phiên đăng nhập; backend vẫn là system of record cho dữ liệu, approval và
audit. Khi gọi các endpoint Manager bằng Swagger/Postman, dùng các header demo sau:

```text
X-User-Id: 00000000-0000-0000-0000-000000000102
X-User-Role: manager
```

Các endpoint cần role Manager gồm:

```text
GET  /api/v1/approvals
GET  /api/v1/proposals
POST /api/v1/approvals/{request_id}/approve
POST /api/v1/approvals/{request_id}/reject
GET  /api/v1/audit-logs
```

Không đưa các header, mật khẩu demo hoặc `.env` vào ảnh chụp public, issue hoặc commit production.

## 8. Kịch bản kiểm tra giao diện

### Resident

1. Đăng nhập bằng tài khoản Resident.
2. Kiểm tra Dashboard hiển thị S01–S05.
3. Mở chi tiết một trạm và xem PM2.5, lịch sử, forecast.
4. Mở Compare để so sánh hai trạm.
5. Mở AI Agent và hỏi:
   - `PM2.5 hiện tại tại S01 là bao nhiêu?`
   - `So sánh S01 và S03.`
   - `Dự báo PM2.5 S01 trong 3 giờ tới.`
6. Mở Alerts và Profile.

### Tạo cảnh báo bằng simulator

Sửa `.env`:

```env
SENSOR_SCENARIO=spike
```

Recreate simulator:

```powershell
docker compose up -d --force-recreate sensor-simulator
```

Chờ tối thiểu hai chu kỳ, mặc định khoảng 20 giây, vì rule yêu cầu hai mẫu cao liên tiếp.

Kiểm tra alert:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/alerts
```

Sau khi demo xong, đổi lại trong `.env`:

```env
SENSOR_SCENARIO=normal
```

và chạy lại:

```powershell
docker compose up -d --force-recreate sensor-simulator
```

### Manager — HITL và audit

1. Đăng nhập bằng Manager.
2. Mở Approval Queue.
3. Kiểm tra evidence của proposal.
4. Thử Reject hoặc Approve.
5. Mở Audit Log để kiểm tra hành động.
6. Nếu proposal có command thiết bị, xem log:

```powershell
docker compose logs --tail=100 device-simulator
```

### Admin

1. Đăng nhập bằng Admin.
2. Kiểm tra Admin Overview.
3. Mở Station Management, User Management, IoT Devices và Settings.
4. Xác nhận simulator banner luôn hiển thị trên giao diện.

## 9. Theo dõi dữ liệu và lỗi

Theo dõi pipeline MQTT → consumer → database:

```powershell
docker compose logs -f sensor-simulator mqtt-consumer
```

Theo dõi backend và Agent:

```powershell
docker compose logs -f backend agent
```

Xem toàn bộ trạng thái gần đây:

```powershell
docker compose logs --tail=100 backend agent mqtt-consumer sensor-simulator
```

Một số lỗi thường gặp:

| Hiện tượng | Cách xử lý |
|---|---|
| Docker API không kết nối | Mở Docker Desktop, chờ Docker Engine chạy |
| `localhost:5173` không vào được | Chạy `docker compose ps frontend`, xem log frontend |
| Trang trắng/raw HTML | Dừng Vite cũ hoặc chạy frontend ở port 5174 |
| Không có trạm | Chạy lại `scripts/init-demo-db.ps1` |
| Không có dữ liệu mới | Xem log sensor-simulator và mqtt-consumer |
| Agent lỗi | Kiểm tra `backend`, `agent` và biến `AGENT_BACKEND_BASE_URL` |
| Database thiếu bảng | Chạy lại script bootstrap, không tự sửa DB bằng tay |

## 10. Dừng hệ thống

Dừng container nhưng giữ nguyên volume/database:

```powershell
docker compose down
```

Khởi động lại lần sau:

```powershell
docker compose up -d
```

Không dùng `docker compose down -v` trong buổi demo thông thường vì lệnh này xoá volume
PostgreSQL và dữ liệu seed hiện có.

## 11. Kiểm tra trước khi trình diễn

- Docker Desktop đang chạy.
- `docker compose ps` không có service chính bị `Exited`.
- `/health`, `/ready` và `/api/v1/stations` trả về thành công.
- Frontend mở được ở port 5173.
- Có đủ S01–S05.
- Simulator banner hiển thị rõ.
- Đã thử ít nhất một câu hỏi Agent.
- Đã thử một flow approval/reject và xem audit log.
- Không chụp hoặc commit `.env`, password, token hay secret.

# Backlog 2A — Backend + Data/IoT (Leader)

## Cách tích checklist

- `[ ]` = chưa làm/chưa verify.
- Đổi thành `[x]` khi command chạy thành công, output đúng và evidence đã lưu.
- Nếu implementation có nhưng chưa chạy Docker, ghi `PARTIAL — cần runtime evidence`.
- Nếu chờ mentor/quyền truy cập, ghi `BLOCKED — lý do/người xử lý`.

**Owner:** Leader Backend/Data-IoT  
**Mục tiêu:** chứng minh backend là system of record và hoàn thiện trace runtime.

## Nhiệm vụ

### B2-BE-01 — Clean runtime startup

- [ ] Mở Docker Desktop, chạy `docker compose config --quiet`.
- [ ] Start PostgreSQL/MQTT trước, kiểm tra `healthy`.
- [ ] Chạy `scripts/init-demo-db.ps1` hai lần để xác nhận idempotent.
- [ ] Start backend, agent, consumer, simulator, device simulator và frontend.
- **Acceptance:** `/health`, `/ready`, `/api/v1/stations` trả 200; tất cả container `Up`.

### B2-DB-01 — Database integrity

- [ ] Xác nhận bảng stations, station_status, measurements, alerts, approvals, audit, devices.
- [ ] Xác nhận 5 station S01-S05, manager/admin/resident seed và FILTER-01.
- [ ] Kiểm tra unique `message_id`, foreign key và timezone timestamp.
- [ ] Chốt với mentor: bootstrap schema/seed hay thêm Alembic migration.
- **Evidence:** psql output và timestamp kiểm tra.

### B2-IOT-01 — MQTT-to-DB trace

- [ ] Lấy một `message_id` từ log sensor simulator.
- [ ] Đối chiếu topic, station_id, pm25, measured_at, received_at, source.
- [ ] Kiểm tra row measurement và station_status trong PostgreSQL.
- [ ] Đối chiếu cùng dữ liệu qua `/api/v1/stations/{id}` và history.
- **Acceptance:** Có một trace hoàn chỉnh MQTT -> validation -> DB -> API.

### B2-IOT-02 — Data quality matrix

- [ ] Test valid payload.
- [ ] Test duplicate message.
- [ ] Test unknown station.
- [ ] Test PM2.5 ngoài range.
- [ ] Test timestamp future/stale.
- [ ] Test explicit offline và recovery online.
- **Acceptance:** Invalid/stale không cập nhật current, alert, forecast hoặc proposal.

### B2-BE-01 — Alert runtime

- [ ] Chạy `SENSOR_SCENARIO=spike`.
- [ ] Chờ hai interval theo consecutive gate.
- [ ] Kiểm tra active alert, threshold, rule version, observed value.
- [ ] Gửi duplicate/stale sample và xác nhận không tạo alert thứ hai.
- [ ] Kiểm tra resolve alert và audit record.

### B2-BE-02 — HITL/audit/device trace

- [ ] Tạo proposal hợp lệ từ active alert.
- [ ] Xác nhận proposal bắt đầu ở `pending`.
- [ ] Xác nhận Resident/Agent không approve được.
- [ ] Manager approve và kiểm tra version/concurrency.
- [ ] Manager reject một proposal khác.
- [ ] Kiểm tra audit create/approve/reject/dispatch.
- [ ] Kiểm tra device simulator chỉ ack command approved.
- **Acceptance:** `proposal -> review -> audit -> dispatch -> device status` có correlation ID.

### B2-BE-03 — Weather/fallback policy

- [ ] Chốt provider thật hoặc fallback simulator với mentor.
- [ ] Ghi source/freshness/confidence trong weather và forecast response.
- [ ] Test timeout, stale response và không có API key.
- **Acceptance:** Không mô tả simulator fallback là weather live/official.

## File chính

`backend/app/`, `backend/db/`, `services/mqtt-consumer/`, `services/sensor-simulator/`,
`services/device-simulator/`, `docker-compose.yml`, `specs/api-contracts.md`,
`specs/data-contracts.md`.

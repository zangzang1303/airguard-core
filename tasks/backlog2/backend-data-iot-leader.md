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

- [x] Mở Docker Desktop, chạy `docker compose config --quiet`.
- [x] Start PostgreSQL/MQTT trước, kiểm tra `healthy`.
- [x] Chạy `scripts/init-demo-db.ps1` hai lần để xác nhận idempotent.
- [x] Start backend, agent, consumer, simulator, device simulator và frontend; toàn bộ container `Up`.
- **Acceptance:** `/health`, `/ready`, `/api/v1/stations` trả 200; tất cả container `Up`.

**Evidence 2026-08-11:** `docker compose config --quiet` pass; backend `/health`, `/ready`, `/api/v1/stations` và Agent `/health` đều HTTP 200; frontend `http://localhost:5173` trả HTTP 200. Runtime log xác nhận simulator publish và MQTT consumer accept measurement/status cho S01-S05. PostgreSQL `healthy`; MQTT `Up` (Compose chưa khai báo MQTT healthcheck).

### B2-DB-01 — Database integrity

- [x] Xác nhận bảng `stations`, `station_status`, `measurements`, `alerts`, `approval_requests`, `audit_logs`, `devices` và các bảng domain liên quan.
- [x] Xác nhận 5 station S01-S05, seed resident/manager/admin và `FILTER-01`.
- [x] Kiểm tra unique `message_id`, 10 foreign key và timestamp kiểu `timestamptz`.
- [x] Chốt dùng bootstrap `schema.sql`/`seed.sql` cho MVP local/demo; chưa thêm Alembic trong milestone này. Quyết định được ghi tại ADR 0007.
- **Evidence 2026-08-11:** PostgreSQL `airguard` trả 12 bảng public; 5 station, 3 user, 1 device; `measurements_message_id_key` tồn tại; session timezone `Etc/UTC`; `approval_requests` là tên bảng approval thực tế trong schema. `scripts/init-demo-db.ps1` chạy thành công hai lần và không nhân bản seed.

### B2-IOT-01 — MQTT-to-DB trace

- [x] Lấy một `message_id` từ log sensor simulator: `MSG-de5121933a-S05-000027`.
- [x] Đối chiếu topic, `station_id`, `pm25`, `measured_at`, `received_at`, `source`; các trường khớp giữa simulator, consumer và DB.
- [x] Kiểm tra row measurement và `station_status` trong PostgreSQL: measurement `valid`, S05 `online`.
- [x] Đối chiếu cùng dữ liệu qua `/api/v1/stations/S05/current` và `/api/v1/stations/S05/history`: history trả đúng `message_id`, station, PM2.5 và measured_at.
- **Acceptance:** Có một trace hoàn chỉnh MQTT -> validation -> DB -> API.

**Evidence 2026-08-11:** Trace mới `MSG-de5121933a-S05-000057`: simulator publish topic `airguard/stations/S05/measurements`, PM2.5 `24.15`; consumer accept; PostgreSQL lưu `measured_at=2026-08-11 07:49:17.834599+00`, `received_at=2026-08-11 07:49:17.993765+00`, `source=simulator`, `quality_flag=valid`; API history trả đúng các trường này. Đã rebuild backend/consumer và áp dụng bootstrap schema thành công.

### B2-IOT-02 — Data quality matrix

- [x] Test valid payload.
- [x] Test duplicate message.
- [x] Test unknown station.
- [x] Test PM2.5 ngoài range.
- [x] Test timestamp future/stale.
- [x] Test explicit offline và recovery online.
- **Acceptance:** Invalid/stale không cập nhật current, alert, forecast hoặc proposal.

**Evidence 2026-08-11:** `.venv\Scripts\python.exe -m pytest tests/test_iot/test_validator.py tests/test_iot/test_storage.py tests/test_backend/test_services.py -q` → `23 passed`. Coverage includes valid/unknown/range/future/stale reason codes, duplicate idempotency at storage, offline → newer online status, and stale ingestion rejected before DB access. Current/history/alert queries select only `quality_flag='valid'`; station shaping, forecast and proposal eligibility require fresh online data.

### B2-BE-01 — Alert runtime

- [x] Chạy `SENSOR_SCENARIO=spike`.
- [x] Chờ hai interval theo consecutive gate.
- [x] Kiểm tra active alert, threshold, rule version, observed value.
- [x] Gửi duplicate/stale sample và xác nhận không tạo alert thứ hai.
- [x] Kiểm tra resolve alert và audit record.

**Evidence 2026-08-11:** Compose runtime dùng `SENSOR_RUN_ID=B2BE01-20260811`, `SENSOR_SCENARIO=spike`, interval 10s. S03 phát `100.72` rồi `103.83`; sau hai interval tạo đúng một alert `b7e16596-f492-46fc-9fd8-f7562f24d3dd`, `severity=critical`, `threshold_value=50.0`, `rule_version=pm25-threshold-v1`, `status=active`. Duplicate `MSG-B2BE01-20260811-S03-000003` bị consumer bỏ qua và sample stale `MSG-B2BE01-20260811-S03-STALE-001` bị reject; DB ghi `duplicate|1`, `stale|1`, active threshold alert vẫn là `1`. Sau sample recovery hợp lệ PM2.5 `20.0`, active alert về rỗng; audit có `alert.create` và `alert.auto_resolve` cho cùng alert ID, `resolved_at=2026-08-11 07:57:37.25537+00`.

### B2-BE-02 — HITL/audit/device trace

- [x] Tạo proposal hợp lệ từ active alert.
- [x] Xác nhận proposal bắt đầu ở `pending`.
- [x] Xác nhận Resident/Agent không approve được.
- [x] Manager approve và kiểm tra version/concurrency.
- [x] Manager reject một proposal khác.
- [x] Kiểm tra audit create/approve/reject/dispatch.
- [x] Kiểm tra device simulator chỉ ack command approved.
- **Acceptance:** `proposal -> review -> audit -> dispatch -> device status` có correlation ID.

**Evidence 2026-08-11:** Active alert `ce81d340-98a8-42f8-9565-149dd5fffc63` tạo proposal `927ea124-68ad-4bd5-b783-f8340d60aae8` ở `pending`, version 1, correlation `corr-B2BE02-001`. Resident approve nhận `403`; manager approve chuyển version 2, tạo intent `17a88d3f-249c-4c55-9b33-b5dc1a7628ba`; stale version nhận `409`. Proposal `1d2eb206-1b13-487f-a84d-5301a6efafd9` được manager reject. Audit ghi `approval.create`, `approval.approve`, `device_command.dispatch`, `approval.reject`; dispatch correlation `07ab1d34-572a-48ce-bf3f-deae09cf1813`. Device `FILTER-01` ack `succeeded`, consumer persist `last_seen_at=2026-08-11 08:00:21.711704Z`.

### B2-BE-03 — Weather/fallback policy

- [x] Chốt fallback simulator cho MVP; provider thật deferred theo ADR 0008.
- [x] Ghi source/freshness/confidence trong weather và forecast response.
- [x] Test fallback không cần API key và luôn gắn provenance; timeout/stale external-provider path deferred.
- **Acceptance:** Không mô tả simulator fallback là weather live/official.

**Evidence 2026-08-11:** Đã chốt fallback simulator cho MVP tại ADR 0008. Weather API trả `source=simulator_fallback_weather`, `is_fallback=true`, `is_stale=false`; forecast trả `source=baseline_current_pm25`, `freshness=fresh`, `confidence=low`. Timeout/stale external-provider path được deferred cùng provider thật, không được tuyên bố là đã triển khai.

## File chính

`backend/app/`, `backend/db/`, `services/mqtt-consumer/`, `services/sensor-simulator/`,
`services/device-simulator/`, `docker-compose.yml`, `specs/api-contracts.md`,
`specs/data-contracts.md`.

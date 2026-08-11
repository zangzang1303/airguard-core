
# Công việc Dữ liệu và IoT

## Mục tiêu và phạm vi

Xay dung pipeline du lieu PM2.5 gia lap cho 5 tram S01-S05: simulator -> MQTT -> consumer -> PostgreSQL. Data duoc gan `source=simulator`, co timestamp timezone, message id va station status. Du lieu invalid/stale khong duoc dung cho current, alert, forecast hay warning proposal.

> Checklist triển khai, scenario, lệnh kiểm chứng và tiêu chí leader sign-off nằm tại
> [Backend + Data/IoT Demo Completion Guide](../docs/backend-data-iot-demo-completion.md).
> Một service/file tồn tại chỉ xác nhận `Implemented`; `Verified` yêu cầu trace runtime và evidence.

## Thứ tự thực hiện

`DI-001 -> DI-002 -> DI-003 -> DI-004 -> DI-005 -> DI-006 -> DI-007`.

## DI-001 - Dữ liệu chủ trạm

**Mục tiêu:** mot nguon su that duy nhat cho danh sach 5 tram.

**Thực hiện:**

1. Chot S01-S05: immutable id, display name, latitude, longitude, location type, active flag va description.
2. Can Mentor xac nhan ten/toa do khu vuc; luu nguon xac nhan va ngay cap nhat.
3. Tao schema/migration va seed idempotent; backend, simulator va frontend dung chung station id convention.
4. Dat constraint unique id, lat/lon range va khong cho simulator tu tao station la.
5. Dinh nghia quy trinh thay doi master data: PR, review, migration/seed va cap nhat docs.

**Đầu ra:** station catalog versioned va seed cho local/demo.

**Kiểm thử:** 5 station, uniqueness, valid coordinates, seed chay lap lai, backend API tra dung metadata.

**Hoàn thành khi:** khong con danh sach station rieng le/hard-code mau thuan giua cac module.

## DI-002 - Sensor simulator và topic phép đo

**Mục tiêu:** publish payload tai lap duoc, dung contract va co scenario demo.

**Thực hiện:**

1. Cau hinh MQTT host/port, publish interval, random seed, station catalog va scenario qua environment.
2. Publish `airguard/stations/{station_id}/measurements` voi message_id, station_id, pm25, temperature, humidity, wind_speed, rainfall, timestamp, source.
3. Dam bao timestamp RFC3339 co `+07:00`/UTC ro rang; `source=simulator` bat buoc.
4. Tao scenario: normal, rush-hour, spike vuot threshold, recovery, duplicate/replay, station silence.
5. Log publish gon: topic, message id, station, PM2.5, scenario; khong log broker credential.
6. Xu ly reconnect exponential backoff va shutdown graceful.

**Đầu ra:** simulator container/command va scenario instruction.

**Kiểm thử:** schema JSON, 5 stations moi interval, broker restart, reconnect, deterministic seed va spike scenario.

**Hoàn thành khi:** co the tai lap mot spike alert voi cung seed/scenario.

## DI-003 - Trạng thái trạm và độ mới dữ liệu

**Mục tiêu:** system biet station online/offline/stale mot cach nhat quan.

**Thực hiện:**

1. Publish `airguard/stations/{station_id}/status` voi status, timestamp, source va optional reason.
2. Consumer cap nhat `last_seen` khi nhan valid measurement/status; dinh nghia heartbeat interval va stale/offline timeout.
3. Chot precedence: invalid data khong lam refresh valid measurement; status explicit offline co the override online.
4. Xu ly broker reconnect, simulator stop, consumer restart va recovery online.
5. Cung cap status/freshness cho backend API, khong de frontend tu tu tinh tu timestamp raw.

**Đầu ra:** freshness policy va status persistence.

**Kiểm thử:** heartbeat on time, silence, explicit offline, late message, recovery va timeout boundaries.

**Hoàn thành khi:** dashboard va Agent nhan cung mot ket qua cho status cua mot tram.

## DI-004 - Kiểm tra dữ liệu và chính sách từ chối

**Mục tiêu:** bao ve database va business rule khoi data loi.

**Thực hiện:**

1. Validate topic pattern, content type/JSON, required fields, data types, station master data va timestamp range.
2. Chot numerical range duoc Mentor/nhom xac nhan cho PM2.5 va weather values; document rules.
3. Dedupe bang unique message id; dinh nghia behavior voi replay message va out-of-order event.
4. Reject message voi reason code: malformed, unknown_station, range_error, future_time, duplicate, stale.
5. Tang metric per reason va structured log; quyet dinh DLQ hay reject log cho MVP.
6. Khong de invalid/stale update current value hay kich hoat event accepted.

**Đầu ra:** validator, reason taxonomy, metrics va test fixtures invalid.

**Kiểm thử:** tung reason code, batch mixed valid/invalid, duplicate after restart va invalid JSON khong lam consumer crash.

**Hoàn thành khi:** ty le rejected co the quan sat duoc va khong co invalid row duoc API coi la current.

## DI-005 - Lưu trữ bền vững của MQTT Consumer

**Mục tiêu:** persist reliability tu broker den PostgreSQL va kich hoat downstream dung thu tu.

**Thực hiện:**

1. Tao consumer service subscribe measurements/status, tuong thich QoS da chot va retry reconnect.
2. Parse -> validate -> transaction persist measurement/status -> commit -> publish internal accepted event.
3. Tao index `station_id, measured_at`, unique message_id va retention strategy cho history.
4. Cap nhat station current theo latest valid event time, khong phai latest receive time neu out-of-order.
5. Xu ly DB down: khong acknowledge som; retry/backoff phu hop QoS, log va expose readiness.
6. Viet operational command de xem consumer lag, last seen va rejected count.

**Đầu ra:** consumer container, migrations, data path test va operational notes.

**Kiểm thử:** normal path, broker restart, consumer restart, database restart, duplicate, out-of-order, database full/timeout.

**Hoàn thành khi:** cung message id co the trace duoc tu MQTT log den database va `/stations/{id}/history`.

## DI-006 - Device simulator sau HITL

**Mục tiêu:** mo phong device command an toan sau approval, khong la dieu kien bat buoc neu rui ro MVP.

**Thực hiện:**

1. Chi bat dau khi BE-005 co enforcement va audit; xac nhan command contract co approval_id, command_id, target va idempotency key.
2. Subscribe `airguard/devices/{device_id}/command`; validate schema va status approval qua dispatcher/backend trusted boundary.
3. Chi execute simulation khi command approved; publish device status/ack tren status topic.
4. Reject/ignore pending, rejected, expired, malformed, duplicate va unknown target.
5. Gan `is_simulated=true` o moi device response/UI data.

**Đầu ra:** device simulator va command trace tu approval den ack.

**Kiểm thử:** approved, rejected, pending, replay, bad signature/reference, device offline va ack timeout.

**Hoàn thành khi:** khong co demo nao tuyen bo device da act khi command chi dang pending hay failed.

## DI-007 - Ngữ cảnh thời tiết

**Mục tiêu:** cung cap weather context co source/fallback minh bach cho forecast va Agent.

**Thực hiện:**

1. Chon provider sau khi review API key, terms, rate limit, location granularity va fallback.
2. Tao collector normalize temperature, humidity, wind, rainfall, observed_at, source va freshness.
3. Cache theo TTL, retry capped va circuit breaker nhe; khong goi provider cho moi Agent message.
4. Fallback deterministic simulator fixture duoc label ro; khong tra fallback nhu live weather.
5. Cung cap API/tool contract va observability cho provider failure/staleness.

**Đầu ra:** weather context service, fallback policy va test fixtures.

**Kiểm thử:** provider success, timeout, 429, malformed response, stale cache, no key va fallback display.

**Hoàn thành khi:** Agent co the noi ro weather data den tu dau va thoi diem nao.

## Mốc và phụ thuộc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | DI-001..DI-005 | MQTT broker, PostgreSQL, data contracts |
| 08/08 | DI-007; DI-006 neu HITL xong | BE approvals/dispatcher, weather provider |

## Tiêu chí hoàn thành chung

- Moi measurement MVP co `source=simulator`, `message_id`, timestamp timezone va station id hop le.
- Consumer co retry/reconnect va khong silently drop/reclassify invalid data.
- Khong secret MQTT/weather trong source, container logs hay repository.


## Bản đồ file theo task

| Task | File hiện có cần sửa | File/directory cần tạo hoặc cập nhật | Tài liệu và test liên quan |
|---|---|---|---|
| DI-001 | `data/stations.json`, `backend/db/schema.sql` | `data/seed/` nếu cần seed idempotent | `specs/domain-model.md`, station seed test |
| DI-002 | `services/sensor-simulator/sensor_simulator.py`, `services/sensor-simulator/Dockerfile` | `services/sensor-simulator/scenarios/` | `specs/data-contracts.md`, simulator test |
| DI-003 | `services/sensor-simulator/sensor_simulator.py` | `services/mqtt-consumer/status_handler.py` | freshness integration test |
| DI-004 | - | `services/mqtt-consumer/validator.py`, `services/mqtt-consumer/schemas.py` | `tests/test_iot/test_validation.py`, data contract |
| DI-005 | `docker-compose.yml`, `backend/db/schema.sql` | `services/mqtt-consumer/main.py`, Dockerfile, requirements | pipeline integration test |
| DI-006 | - | `services/device-simulator/` | command contract, HITL/audit test |
| DI-007 | `backend/app/main.py` | `backend/app/services/weather_service.py` | weather contract and fallback test |
## Trạng thái triển khai hiện tại

Pipeline chính đã có implementation nền, nhưng chưa được ký xác nhận demo-ready:

| Hạng mục | Trạng thái | File chính |
|---|---|---|
| DI-001 | Đã có station catalog dùng chung và seed idempotent | `data/stations.json`, `backend/db/schema.sql` |
| DI-002 | Đã có simulator đọc catalog, publish measurement/status, hỗ trợ scenario demo và run-scoped message ID | `services/sensor-simulator/sensor_simulator.py` |
| DI-003 | Đã có status topic và persistence `station_status` | `services/mqtt-consumer/mqtt_consumer/main.py`, `backend/db/schema.sql` |
| DI-004 | Đã có validator/reason taxonomy và test unit cho reason chính | `services/mqtt-consumer/mqtt_consumer/validator.py`, `tests/test_iot/test_validator.py` |
| DI-005 | Đã có consumer container, retry reconnect, manual MQTT ack sau persistence, persist measurement/status/rejection | `services/mqtt-consumer/`, `docker-compose.yml` |
| DI-006 | Đã có device simulator, command validation, simulated ack và consumer device-status persistence; cần runtime evidence | `services/device-simulator/`, `services/mqtt-consumer/` |
| DI-007 | Có fallback được gắn nhãn; chưa có provider/cache/failure matrix | `backend/app/services/weather_service.py` |

Ghi chú kiểm chứng ngày 08/08/2026: compile đã pass và `docker compose config` hợp lệ. Full
`pytest` chưa chạy vì interpreter hiện tại thiếu `pytest-asyncio`; Docker daemon chưa chạy nên chưa
có trace MQTT -> consumer -> PostgreSQL -> API. DI-006 vẫn chưa có implementation.



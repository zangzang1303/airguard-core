# Data IoT Tasks

## Muc tieu va pham vi

Xay dung pipeline du lieu PM2.5 gia lap cho 5 tram S01-S05: simulator -> MQTT -> consumer -> PostgreSQL. Data duoc gan `source=simulator`, co timestamp timezone, message id va station status. Du lieu invalid/stale khong duoc dung cho current, alert, forecast hay warning proposal.

## Thu tu thuc hien

`DI-001 -> DI-002 -> DI-003 -> DI-004 -> DI-005 -> DI-006 -> DI-007`.

## DI-001 - Station master data

**Muc tieu:** mot nguon su that duy nhat cho danh sach 5 tram.

**Thuc hien:**

1. Chot S01-S05: immutable id, display name, latitude, longitude, location type, active flag va description.
2. Can Mentor xac nhan ten/toa do khu vuc; luu nguon xac nhan va ngay cap nhat.
3. Tao schema/migration va seed idempotent; backend, simulator va frontend dung chung station id convention.
4. Dat constraint unique id, lat/lon range va khong cho simulator tu tao station la.
5. Dinh nghia quy trinh thay doi master data: PR, review, migration/seed va cap nhat docs.

**Dau ra:** station catalog versioned va seed cho local/demo.

**Kiem thu:** 5 station, uniqueness, valid coordinates, seed chay lap lai, backend API tra dung metadata.

**Xong khi:** khong con danh sach station rieng le/hard-code mau thuan giua cac module.

## DI-002 - Sensor simulator va measurement topic

**Muc tieu:** publish payload tai lap duoc, dung contract va co scenario demo.

**Thuc hien:**

1. Cau hinh MQTT host/port, publish interval, random seed, station catalog va scenario qua environment.
2. Publish `airguard/stations/{station_id}/measurements` voi message_id, station_id, pm25, temperature, humidity, wind_speed, rainfall, timestamp, source.
3. Dam bao timestamp RFC3339 co `+07:00`/UTC ro rang; `source=simulator` bat buoc.
4. Tao scenario: normal, rush-hour, spike vuot threshold, recovery, duplicate/replay, station silence.
5. Log publish gon: topic, message id, station, PM2.5, scenario; khong log broker credential.
6. Xu ly reconnect exponential backoff va shutdown graceful.

**Dau ra:** simulator container/command va scenario instruction.

**Kiem thu:** schema JSON, 5 stations moi interval, broker restart, reconnect, deterministic seed va spike scenario.

**Xong khi:** co the tai lap mot spike alert voi cung seed/scenario.

## DI-003 - Station status va freshness

**Muc tieu:** system biet station online/offline/stale mot cach nhat quan.

**Thuc hien:**

1. Publish `airguard/stations/{station_id}/status` voi status, timestamp, source va optional reason.
2. Consumer cap nhat `last_seen` khi nhan valid measurement/status; dinh nghia heartbeat interval va stale/offline timeout.
3. Chot precedence: invalid data khong lam refresh valid measurement; status explicit offline co the override online.
4. Xu ly broker reconnect, simulator stop, consumer restart va recovery online.
5. Cung cap status/freshness cho backend API, khong de frontend tu tu tinh tu timestamp raw.

**Dau ra:** freshness policy va status persistence.

**Kiem thu:** heartbeat on time, silence, explicit offline, late message, recovery va timeout boundaries.

**Xong khi:** dashboard va Agent nhan cung mot ket qua cho status cua mot tram.

## DI-004 - Validation va reject policy

**Muc tieu:** bao ve database va business rule khoi data loi.

**Thuc hien:**

1. Validate topic pattern, content type/JSON, required fields, data types, station master data va timestamp range.
2. Chot numerical range duoc Mentor/nhom xac nhan cho PM2.5 va weather values; document rules.
3. Dedupe bang unique message id; dinh nghia behavior voi replay message va out-of-order event.
4. Reject message voi reason code: malformed, unknown_station, range_error, future_time, duplicate, stale.
5. Tang metric per reason va structured log; quyet dinh DLQ hay reject log cho MVP.
6. Khong de invalid/stale update current value hay kich hoat event accepted.

**Dau ra:** validator, reason taxonomy, metrics va test fixtures invalid.

**Kiem thu:** tung reason code, batch mixed valid/invalid, duplicate after restart va invalid JSON khong lam consumer crash.

**Xong khi:** ty le rejected co the quan sat duoc va khong co invalid row duoc API coi la current.

## DI-005 - MQTT Consumer persistence

**Muc tieu:** persist reliability tu broker den PostgreSQL va kich hoat downstream dung thu tu.

**Thuc hien:**

1. Tao consumer service subscribe measurements/status, tuong thich QoS da chot va retry reconnect.
2. Parse -> validate -> transaction persist measurement/status -> commit -> publish internal accepted event.
3. Tao index `station_id, measured_at`, unique message_id va retention strategy cho history.
4. Cap nhat station current theo latest valid event time, khong phai latest receive time neu out-of-order.
5. Xu ly DB down: khong acknowledge som; retry/backoff phu hop QoS, log va expose readiness.
6. Viet operational command de xem consumer lag, last seen va rejected count.

**Dau ra:** consumer container, migrations, data path test va operational notes.

**Kiem thu:** normal path, broker restart, consumer restart, database restart, duplicate, out-of-order, database full/timeout.

**Xong khi:** cung message id co the trace duoc tu MQTT log den database va `/stations/{id}/history`.

## DI-006 - Device simulator sau HITL

**Muc tieu:** mo phong device command an toan sau approval, khong la dieu kien bat buoc neu rui ro MVP.

**Thuc hien:**

1. Chi bat dau khi BE-005 co enforcement va audit; xac nhan command contract co approval_id, command_id, target va idempotency key.
2. Subscribe `airguard/devices/{device_id}/command`; validate schema va status approval qua dispatcher/backend trusted boundary.
3. Chi execute simulation khi command approved; publish device status/ack tren status topic.
4. Reject/ignore pending, rejected, expired, malformed, duplicate va unknown target.
5. Gan `is_simulated=true` o moi device response/UI data.

**Dau ra:** device simulator va command trace tu approval den ack.

**Kiem thu:** approved, rejected, pending, replay, bad signature/reference, device offline va ack timeout.

**Xong khi:** khong co demo nao tuyen bo device da act khi command chi dang pending hay failed.

## DI-007 - Weather context

**Muc tieu:** cung cap weather context co source/fallback minh bach cho forecast va Agent.

**Thuc hien:**

1. Chon provider sau khi review API key, terms, rate limit, location granularity va fallback.
2. Tao collector normalize temperature, humidity, wind, rainfall, observed_at, source va freshness.
3. Cache theo TTL, retry capped va circuit breaker nhe; khong goi provider cho moi Agent message.
4. Fallback deterministic simulator fixture duoc label ro; khong tra fallback nhu live weather.
5. Cung cap API/tool contract va observability cho provider failure/staleness.

**Dau ra:** weather context service, fallback policy va test fixtures.

**Kiem thu:** provider success, timeout, 429, malformed response, stale cache, no key va fallback display.

**Xong khi:** Agent co the noi ro weather data den tu dau va thoi diem nao.

## Moc va phu thuoc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | DI-001..DI-005 | MQTT broker, PostgreSQL, data contracts |
| 08/08 | DI-007; DI-006 neu HITL xong | BE approvals/dispatcher, weather provider |

## DoD chung

- Moi measurement MVP co `source=simulator`, `message_id`, timestamp timezone va station id hop le.
- Consumer co retry/reconnect va khong silently drop/reclassify invalid data.
- Khong secret MQTT/weather trong source, container logs hay repository.

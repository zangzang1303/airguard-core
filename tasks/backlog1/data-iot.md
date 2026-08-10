# Backlog 1 — Data/IoT

## Cách tích checklist

- `[ ]` = chưa thực hiện.
- Đổi thành `[x]` sau khi kiểm tra được simulator/MQTT/DB thật, không chỉ đọc code.
- Task có nhiều dòng chỉ được tích từng dòng đã hoàn thành.
- Ghi message ID, topic, timestamp và output DB/API làm evidence.
- Dùng `PARTIAL` hoặc `BLOCKED` nếu chưa đủ runtime evidence.

**Owner:** Data/IoT lead  
**Mục tiêu:** simulator -> MQTT -> consumer -> PostgreSQL với data quality và freshness rõ ràng.

## DI-001 — Station catalog

- [ ] Một catalog chung cho S01–S05: ID, tên, tọa độ, location type, active.
- [ ] Seed idempotent, unique ID và coordinate validation.
- [ ] Mentor xác nhận tên/tọa độ; ghi nguồn và ngày xác nhận.

## DI-002 — Sensor simulator

- [ ] Publish measurement/status đúng topic và QoS.
- [ ] Payload có `message_id`, timezone timestamp, station ID, `source=simulator`.
- [ ] Scenario `normal`, `spike`, offline và run-scoped IDs.
- **Acceptance:** simulator không ghi DB trực tiếp.

## DI-003 — MQTT consumer/freshness

- [ ] Subscribe measurement/status, reconnect và manual ack sau persistence.
- [ ] Cập nhật `station_status.last_seen_at` chỉ với payload hợp lệ.
- [ ] Precedence invalid/stale/offline và recovery online rõ ràng.

## DI-004 — Validation/rejection

- [ ] Unknown station, duplicate, range, timestamp, source và malformed JSON.
- [ ] Persist reason taxonomy/mqtt rejection và không silently drop.

## DI-005 — MQTT-to-DB trace

- [ ] Đối chiếu log topic -> validator -> measurement/status row -> API.
- [ ] Test DB restart, MQTT restart và at-least-once duplicate.

## DI-006 — Device simulator

- [ ] Chỉ execute command đã approved.
- [ ] Reject pending/rejected/malformed/duplicate/unknown target.
- [ ] Publish simulated ack/status với `is_simulated=true`.

## DI-007 — Weather context

- [ ] Chốt provider hoặc simulator fallback với mentor.
- [ ] Response ghi source, freshness, timeout và confidence.
- [ ] Không mô tả fallback là live/official weather.

## File và kiểm thử

`data/stations.json`, `services/sensor-simulator/`, `services/mqtt-consumer/`,
`services/device-simulator/`, `specs/data-contracts.md`, `tests/test_iot/`.

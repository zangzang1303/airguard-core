# Backend + Data/IoT Demo Completion Guide

> Owner: Backend/Data-IoT Lead  
> Scope: `BE-001..BE-007`, `DI-001..DI-007`  
> Release target: AirGuard AI MVP demo  
> Canonical contracts: `specs/api-contracts.md`, `specs/data-contracts.md`, `specs/domain-model.md`

## 1. Mục đích

Tài liệu này là checklist thực thi và ký xác nhận để đưa Backend cùng Data/IoT từ trạng thái
"đã có code" sang "đủ bằng chứng chạy demo". Không dùng sự tồn tại của file, compile thành công
hoặc unit test fixture để thay cho kiểm chứng runtime.

Một task chỉ được đánh dấu `Verified` khi:

1. Code, contract và tài liệu liên quan đã đồng bộ.
2. Happy path, error path và safety path bắt buộc đã pass.
3. Có command, output, ID truy vết và thời điểm kiểm chứng.
4. Không dùng dữ liệu frontend tự sinh để che lỗi backend.
5. Không có blocker về grounding, stale data, HITL, audit hoặc secret.

## 2. Trạng thái baseline ngày 08/08/2026

| Task | Implemented | Verified | Gap cần đóng trước sign-off |
|---|---|---|---|
| BE-001 | Có | Chưa | Config/CORS negative test, startup thật |
| BE-002 | Có | Chưa | PostgreSQL integration, schema response và frontend contract |
| BE-003 | Có | Chưa | Full reject matrix, metric/query vận hành, DB integration |
| BE-004 | Có | Chưa | Cooldown evidence và spike/offline runtime evidence |
| BE-005 | Có | Chưa | 403/409/concurrent review, frontend gửi role/user/version thật |
| BE-006 | Có | Chưa | Full create/review/dispatch audit trace và query filters |
| BE-007 | Có | Chưa | Worker profile, retry/failure/idempotency runtime test |
| DI-001 | Một phần | Chưa | Xác nhận tên/toạ độ; loại bỏ catalog/fallback mâu thuẫn ở client |
| DI-002 | Có | Chưa | Broker reconnect và scenario evidence |
| DI-003 | Có | Chưa | Silence timeout, precedence và recovery integration |
| DI-004 | Có | Chưa | Đủ reason taxonomy, rejected counters và invalid-current proof |
| DI-005 | Có | Chưa | MQTT-to-DB trace, DB outage/restart và delivery evidence |
| DI-006 | Có | Chưa | Compose runtime, DB status persistence, ack/idempotency và negative cases |
| DI-007 | Một phần | Chưa | Provider/cache hoặc quyết định dùng fallback; timeout/stale tests |

Baseline này phải được cập nhật bằng evidence, không cập nhật bằng nhận định chủ quan.

## 3. Quyết định phải chốt trước khi chạy gate

Leader ghi giá trị được duyệt vào bảng sau. Nếu chưa có Mentor, dùng giá trị tạm thời nhưng phải
giữ nhãn `provisional` trong config, audit và demo narration.

| Quyết định | Giá trị demo đề xuất | Người duyệt | Trạng thái |
|---|---|---|---|
| Warning threshold | `50 µg/m³` | TBD | Provisional |
| Critical threshold | `100 µg/m³` | TBD | Provisional |
| Số measurement liên tiếp | `2` | TBD | Chưa implement |
| Alert cooldown/dedupe | Một active alert/station/rule | TBD | Có một phần |
| Stale timeout | `300 giây` | TBD | Configured |
| Offline timeout | Explicit status hoặc quá SLA đã duyệt | TBD | Cần chốt |
| Station name/coordinates | `data/stations.json` | TBD | Chưa xác nhận nguồn |
| Weather | Provider hoặc `simulator_fallback_weather` gắn nhãn | TBD | Fallback hiện có |
| Device demo | Có simulator + ack | TBD | Chưa implement |
| Manager demo identity | UUID seed + role `manager` | TBD | Cần kiểm chứng |

Không đổi threshold, cooldown, stale/offline policy hoặc command scope chỉ trong code. Nếu quyết
định khác ADR hiện hành, tạo ADR superseding thay vì sửa lịch sử ADR accepted.

## 4. Thứ tự hoàn thành bắt buộc

```text
Contract freeze
  -> BE-001 + DI-001
  -> DI-002 + DI-003 + DI-004 + DI-005
  -> BE-002 + BE-003
  -> BE-004
  -> BE-005 + BE-006
  -> BE-007 + DI-007
  -> DI-006
  -> Backend/Data-IoT integration gate
  -> Full-system rehearsal
```

Không chạy Agent/HITL demo trên dữ liệu chưa qua Data Quality gate. Không chạy device command
trước khi approval và audit được kiểm chứng server-side.

## 5. Backend task completion checklist

### BE-001 — API startup, health và readiness

Implementation:

- [x] Thêm healthcheck cho service `backend` trong `docker-compose.yml` dùng `/health`.
- [ ] `/health` chỉ phản ánh process; `/ready` trả `503` khi PostgreSQL lỗi.
- [ ] CORS lấy từ environment và test cả origin hợp lệ/không hợp lệ.
- [ ] Error envelope luôn có `code`, `message`, `request_id`, `details`; không có stack/secret.
- [ ] OpenAPI `/docs` và `/openapi.json` phản ánh đúng route thực tế.
- [ ] Thống nhất tài liệu rằng health/readiness nằm ngoài `/api/v1`, hoặc thêm alias có test.

Verification:

```powershell
docker compose config --quiet
docker compose up -d --build postgres mqtt backend
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
Invoke-RestMethod http://localhost:8000/openapi.json | Select-Object -ExpandProperty info
docker compose logs --since 5m backend
```

Pass khi health `200`, ready `200`, OpenAPI tải được, response có request ID và log không lộ
credential. Stop PostgreSQL trong failure drill; `/ready` phải thành `503` nhưng `/health` vẫn `200`.

### BE-002 — Station/current/history/compare

Implementation:

- [ ] Schema có S01-S05, `message_id` unique và index `(station_id, measured_at)`.
- [ ] Station service chọn measurement valid mới nhất theo `measured_at`.
- [ ] Stale/offline trả `pm25=null`; không trả last-known value như current.
- [ ] History `hours=1..72`, tăng dần theo `measured_at`, chỉ chứa `quality_flag=valid`.
- [ ] Route không chứa SQL trực tiếp; chuyển user/device query sang repository/service cùng chuẩn.
- [ ] Frontend mapper dùng `items` cho history và backend forecast contract, không tự sinh dữ liệu.

Verification:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/stations
Invoke-RestMethod http://localhost:8000/api/v1/stations/S01/current
Invoke-RestMethod 'http://localhost:8000/api/v1/stations/S01/history?hours=24'
Invoke-RestMethod -Method Post -ContentType 'application/json' `
  -Body '{"station_ids":["S01","S02"]}' `
  http://localhost:8000/api/v1/stations/compare
```

Lưu output chứng minh đúng 5 station, `source=simulator`, timestamp timezone-aware và history có
thứ tự. Kiểm tra `S99 -> 404`, `hours=0/73 -> 422` và station chưa có data không bị điền số giả.

### BE-003 — Ingestion và Data Quality gate

Implementation:

- [ ] Backend ingestion và MQTT consumer dùng cùng range/taxonomy trong data contract.
- [ ] Reject malformed, unknown topic/station, topic mismatch, range, future, stale, duplicate.
- [ ] Invalid/stale/duplicate không cập nhật station current và không gọi Alert Engine.
- [ ] Rejection được ghi với reason code, payload excerpt giới hạn và không có secret.
- [ ] Có query hoặc metric đếm accepted/rejected theo reason cho operator.

Verification matrix:

| Case | Expected persistence | Current/alert impact | Evidence |
|---|---|---|---|
| Valid fresh | 1 measurement valid | Có thể cập nhật | message/measurement ID |
| Duplicate | Không thêm measurement | Không | rejection `duplicate` |
| PM2.5 âm | Không | Không | `range_error` |
| Unknown station | Không | Không | `unknown_station` |
| Future timestamp | Không | Không | `future_time` |
| Stale timestamp | Không | Không | `stale` |
| Malformed JSON | Không | Không | `malformed`; consumer còn sống |

### BE-004 — Alert Engine

Implementation:

- [x] Chốt và version rule: threshold, consecutive count, severity, cooldown, resolution.
- [x] Chỉ measurement valid/fresh/online được evaluate.
- [x] Một spike đơn lẻ không tạo cảnh báo diện rộng; mặc định cần hai measurement liên tiếp.
- [x] Có alert `sensor_offline` cho station đã từng có dữ liệu nhưng stale/offline.
- [x] Dedupe theo station + rule version; repeated spike update alert thay vì insert spam.
- [x] Recovery resolve đúng policy; manual resolve manager-only và có audit.

Required evidence:

1. Below/equal threshold: không alert.
2. Consecutive valid spike: đúng một active alert, đúng severity/rule version.
3. Repeated spike: vẫn một alert.
4. Invalid/stale spike: không alert.
5. Recovery: alert resolved.
6. Station silence/offline: tạo đúng offline alert nếu nằm trong scope đã duyệt.

### BE-005 — Warning proposal và HITL

Implementation:

- [ ] Create chỉ tạo `pending`, yêu cầu station online/fresh, active alert và evidence.
- [ ] Idempotency key lặp lại trả cùng proposal; không tạo pending duplicate.
- [ ] List/detail/approve/reject bắt buộc `X-User-Role: manager`.
- [ ] Review bắt buộc UUID `X-User-ID`, `version`; reject bắt buộc note.
- [ ] Optimistic locking trả `409` cho double/concurrent review.
- [ ] Reject không tạo command intent; approve chỉ tạo intent khi có `device_id`.
- [ ] Frontend không fallback thành approved/rejected khi API lỗi.

PowerShell request mẫu:

```powershell
$managerHeaders = @{
  'X-User-Role' = 'manager'
  'X-User-ID' = '00000000-0000-0000-0000-000000000001'
  'Content-Type' = 'application/json'
}

Invoke-RestMethod -Headers $managerHeaders `
  'http://localhost:8000/api/v1/approvals?status=pending'

Invoke-RestMethod -Method Post -Headers $managerHeaders `
  -Body '{"version":1,"note":"Reviewed demo evidence."}' `
  'http://localhost:8000/api/v1/approvals/PROPOSAL_UUID/approve'
```

Thay `PROPOSAL_UUID` và `version` bằng server truth. Không dùng ID giả trong evidence.

### BE-006 — Audit

Implementation:

- [ ] Audit append-only ở DB và mutation bị chặn.
- [ ] Ghi create proposal, approve, reject, dispatch attempt/success/failure, manual resolve.
- [ ] Event có actor/role/action/entity/outcome/correlation ID/time.
- [ ] Metadata redact password, token, API key, raw prompt nhạy cảm.
- [ ] API manager-only hỗ trợ query theo proposal/entity và giới hạn kết quả.

Verification:

```powershell
Invoke-RestMethod -Headers $managerHeaders `
  'http://localhost:8000/api/v1/audit-logs?entity_type=approval_request&entity_id=PROPOSAL_UUID'
```

Pass khi cùng proposal truy được chuỗi create -> review -> dispatch outcome, reject không có dispatch,
và viewer nhận `403`.

### BE-007 — Background jobs

Implementation:

- [ ] Chọn và ghi rõ demo mode: eager hoặc `async-jobs` RabbitMQ/Redis/Celery.
- [ ] Job ID ổn định theo idempotency key; duplicate không chạy hai lần.
- [ ] Có state queued/running/succeeded/failed, attempt count và error an toàn.
- [ ] Timeout/retry capped; worker down trả lỗi có thể hành động.
- [ ] Frontend poll đúng `/api/v1/jobs/{task_id}` nếu dùng async mode.

Verification async profile:

```powershell
docker compose --profile async-jobs up -d --build rabbitmq redis celery-worker
docker compose ps
docker compose logs --since 5m celery-worker
```

Kiểm tra success, duplicate idempotency, unknown job `404`, worker down và retry exhaustion.

## 6. Data/IoT task completion checklist

### DI-001 — Station master data

- [ ] Mentor/leader xác nhận tên, toạ độ, location type và ngày xác nhận S01-S05.
- [ ] `data/stations.json` là catalog runtime của simulator.
- [ ] `backend/db/seed.sql` chứa S01-S05 và device demo, đồng bộ với `data/stations.json`; có test phát hiện drift JSON/SQL/API.
- [ ] Frontend không có production catalog/PM2.5 fallback mâu thuẫn.
- [ ] Seed chạy lặp lại không tạo station thứ sáu hoặc duplicate.

Evidence: JSON catalog, SQL query 5 rows và response API 5 rows phải khớp field canonical.

### DI-002 — Sensor simulator

- [ ] Measurement/status topic và payload khớp `specs/data-contracts.md`.
- [ ] Tất cả payload có timezone và `source=simulator`.
- [ ] `normal`, `rush-hour`, `spike`, `recovery`, `duplicate`, `station-silence` tái lập được.
- [x] Message ID không va chạm sau restart với persistent DB; dùng run/session component hoặc UUID.
- [ ] Publish result/error được kiểm tra; reconnect/backoff và graceful shutdown có test.

Scenario command:

```powershell
$env:SENSOR_SCENARIO = 'normal'
$env:SENSOR_RANDOM_SEED = '740'
docker compose up -d --force-recreate sensor-simulator
docker compose logs --since 2m sensor-simulator
```

Đổi sang `spike`, `recovery`, `duplicate`, `station-silence` và lưu message ID của mỗi case.

### DI-003 — Status và freshness

- [ ] Valid measurement/status mới hơn mới cập nhật `last_seen_at`.
- [ ] Invalid/stale/out-of-order data không làm station "tươi" trở lại.
- [ ] Explicit offline có precedence đã chốt; recovery online cần event mới hợp lệ.
- [ ] Backend và Agent tool trả cùng status/freshness cho cùng station.
- [ ] Silence đủ SLA chuyển stale/offline theo policy đã duyệt.

Evidence gồm timestamp publish, DB `last_seen_at`, API status và tool result cùng station.

### DI-004 — Validator và rejection policy

- [ ] Unit test từng reason code và boundary numeric.
- [ ] Duplicate sau restart được xử lý idempotent nhưng không làm mất dữ liệu mới hợp lệ.
- [ ] Invalid JSON không làm consumer crash/restart loop.
- [ ] Có rejected count theo reason trong query/log vận hành.
- [ ] Payload excerpt không chứa credential hoặc dữ liệu không cần thiết.

### DI-005 — Durable MQTT consumer

- [ ] Subscribe QoS đúng contract cho measurement/status.
- [ ] Thứ tự: parse -> validate -> persist transaction -> downstream alert evaluation.
- [x] Xác định rõ acknowledgement behavior; consumer dùng manual MQTT acknowledgement sau persistence.
- [ ] Broker/DB restart có reconnect/backoff và không tạo duplicate current state.
- [ ] Out-of-order measurement không thay current bằng event cũ.
- [ ] Có command xem last seen, history và rejected count.

Trace bắt buộc:

| Layer | Trường phải khớp |
|---|---|
| Simulator log | topic, message_id, station_id, pm25, timestamp, source |
| Consumer log | message_id, validation result, correlation/request ID |
| PostgreSQL | message_id, station_id, pm25, measured_at, source |
| Current/history API | station_id, pm25, updated/measured_at, source |
| UI | station, PM2.5, timestamp, simulator label |

### DI-006 — Device simulator

DI-006 là bắt buộc nếu demo tuyên bố command đã được thiết bị thực thi. Implementation hiện có
nhận command trên MQTT, phát simulated ack và để consumer cập nhật `devices`; vẫn phải chạy runtime
negative cases trước khi hiển thị ack/succeeded.

Implementation:

- [x] Tạo `services/device-simulator/` và thêm service vào Compose.
- [x] Subscribe `airguard/devices/{device_id}/command`.
- [x] Validate `command_id`, `device_id`, `action`, `approval_id`, `idempotency_key`, timestamp.
- [x] Chỉ nhận command có approval reference do dispatcher server-side publish.
- [x] Reject malformed/duplicate/unknown device; pending/rejected được chặn ở approval/dispatcher.
- [x] Publish status/ack có `is_simulated=true`; consumer persist trạng thái device.
- [x] Replay cùng idempotency key không execute hai lần; keys được lưu trên named volume của simulator.

Required cases: approve + ack, reject no command, pending no command, duplicate no double execution,
unknown device, offline/timeout và dispatch failure audit.

### DI-007 — Weather context

- [ ] Chốt provider hoặc chấp nhận fallback deterministic cho MVP.
- [ ] Response luôn có observed time, source, freshness và fallback flag.
- [ ] Provider mode có timeout, capped retry, TTL cache và xử lý 429/malformed response.
- [ ] Fallback phải ghi `simulator_fallback_weather`, không dùng tên provider thật.
- [ ] Agent/tool/UI không mô tả fallback là weather live/official.

Nếu chưa có API key/provider được duyệt, fallback hiện tại có thể demo khi được leader ghi nhận là
known limitation và tất cả surface hiển thị đúng provenance.

## 7. Full verification sequence

### 7.1 Chuẩn bị

```powershell
git status --short
docker version
docker compose version
docker compose config --quiet
Copy-Item .env.example .env
```

Không ghi secret vào command history/evidence. Nếu `.env` đã tồn tại, không overwrite; kiểm tra thủ
công các biến bắt buộc. `Copy-Item` ở trên chỉ dùng cho workspace mới.

### 7.2 Test tĩnh và unit/contract

```powershell
python -m pip install -r requirements.txt
python -m pip install -r backend/requirements.txt
python -m pytest -q
npm.cmd --prefix frontend run build
```

Pass khi pytest và frontend build cùng trả exit code `0`. Không ghi "pass" nếu test bị skip do thiếu
dependency mà test đó là gate bắt buộc.

### 7.3 Start clean stack

```powershell
docker compose up -d --build postgres mqtt backend agent mqtt-consumer sensor-simulator device-simulator frontend
docker compose ps
docker compose logs --since 5m postgres mqtt backend agent mqtt-consumer sensor-simulator
```

Không dùng `docker compose down -v` nếu chưa được leader cho phép vì lệnh đó xoá local demo DB.
Khi cần clean rehearsal, ghi rõ approval và backup/evidence cần giữ trước khi xoá volume.

### 7.4 Normal pipeline gate

1. Chờ ít nhất một interval simulator.
2. Chọn một `message_id` S01 từ simulator log.
3. Tìm cùng ID trong consumer log và PostgreSQL.
4. Đối chiếu `/stations/S01/current` và `/history`.
5. Mở dashboard; xác nhận S01-S05 và nhãn dữ liệu simulator.

SQL read-only mẫu:

```powershell
docker compose exec postgres psql -U airguard -d airguard -c `
  "SELECT message_id,station_id,pm25,measured_at,source FROM measurements ORDER BY measurement_id DESC LIMIT 10;"

docker compose exec postgres psql -U airguard -d airguard -c `
  "SELECT station_id,status,last_seen_at,source,reason FROM station_status ORDER BY station_id;"
```

### 7.5 Data-quality gate

Chạy lần lượt duplicate, stale/future/invalid fixture và station silence. Sau mỗi case kiểm tra:

- rejection reason đúng;
- measurement count không tăng sai;
- current không đổi sang invalid value;
- không sinh alert/proposal;
- consumer vẫn running.

### 7.6 Alert gate

```powershell
$env:SENSOR_SCENARIO = 'spike'
docker compose up -d --force-recreate sensor-simulator
Invoke-RestMethod 'http://localhost:8000/api/v1/alerts?status=active'
```

Lưu message IDs tạo spike, alert ID, rule version và latency publish-to-alert. Chuyển `recovery` và
xác nhận resolve. Chạy duplicate/stale spike để chứng minh không spam/không tạo alert sai.

### 7.7 HITL, audit và device gate

1. Tạo proposal từ active alert bằng Agent hoặc API canonical.
2. Xác nhận status đầu tiên là `pending`.
3. Viewer approve/reject nhận `403`.
4. Manager reject với note; xác nhận không command intent.
5. Tạo proposal thứ hai, manager approve với đúng version.
6. Gửi lại cùng version; xác nhận `409`.
7. Query audit theo proposal ID.
8. Nếu DI-006 hoàn thành, xác nhận command -> simulator ack -> audit success.
9. Nếu không có ack, UI và presenter chỉ nói "approved" hoặc "dispatch failed/pending".

### 7.8 Failure drills

| Failure | Expected |
|---|---|
| PostgreSQL down | `/ready=503`; consumer không silently drop; health process còn phản ánh đúng |
| MQTT down | Simulator/consumer reconnect; không invent data |
| Consumer restart | Resume, no duplicate current |
| Agent down | Backend Agent API trả structured 503; station API vẫn hoạt động |
| Weather unavailable | Labeled fallback hoặc transparent unavailable |
| Worker down | Job failed/actionable; synchronous core API không bị giả success |
| Device timeout | Dispatch failure/pending + audit; không hiển thị succeeded |

## 8. Evidence pack và sign-off

Mỗi rehearsal tạo một thư mục, ví dụ:

```text
docs/evidence/backend-data-iot/2026-08-08-run-01/
  environment.txt
  test-results.txt
  compose-ps.txt
  normal-message-trace.md
  rejection-matrix.md
  alert-trace.md
  hitl-audit-trace.md
  known-limitations.md
```

Dùng [backend-data-iot-evidence-template.md](../templates/backend-data-iot-evidence-template.md)
để tạo report nhất quán cho từng lần chạy.

Không lưu `.env`, token, password, broker credential, raw sensitive prompt hoặc database dump có
PII. Screenshot phải che dữ liệu nhạy cảm.

Sign-off table:

| Gate | Owner | Evidence path | Result | Time |
|---|---|---|---|---|
| Backend unit/contract | Backend lead | TBD | Pending | TBD |
| MQTT/Data Quality | Data-IoT lead | TBD | Pending | TBD |
| Alert | Backend lead | TBD | Pending | TBD |
| HITL/Audit | Backend lead | TBD | Pending | TBD |
| Weather provenance | Data-IoT lead | TBD | Pending | TBD |
| Device ack | Data-IoT lead | TBD | Pending/Deferred | TBD |
| Full rehearsal | Team lead | TBD | Pending | TBD |

## 9. Release blockers

Bất kỳ điều kiện nào sau đây đều chặn demo-ready sign-off:

- Frontend hoặc Agent tự sinh environmental fact khi API/tool lỗi.
- Invalid/stale/offline data tạo current value, alert, forecast hoặc proposal.
- Approve/reject được mô phỏng thành công ở client khi backend lỗi.
- Command publish trước approval hoặc UI nói succeeded khi chưa có ack.
- Không truy được audit cho proposal/review/dispatch.
- Contract API/MQTT/tool khác implementation mà chưa có version plan.
- Có conflict marker, secret, token hoặc password trong source/evidence.
- Không có ít nhất một trace MQTT -> DB -> API -> UI bằng cùng message ID.
- Không có rehearsal normal, spike, Agent và HITL trên cùng release candidate.

## 10. Definition of demo-ready

Backend + Data/IoT được leader ký `Demo-ready` khi:

- BE-001..BE-007 và DI-001..DI-007 đều có trạng thái `Verified`, hoặc DI-006 được chính thức
  `Deferred` và demo không tuyên bố device execution.
- Full pytest/build pass trong môi trường release.
- Compose stack khởi động lặp lại được và health/readiness đúng.
- Có trace cùng message ID từ simulator đến UI.
- Spike/recovery/duplicate/stale/offline cases đạt expected behavior.
- Proposal luôn pending trước review; RBAC/concurrency/audit pass.
- Weather/fallback và toàn bộ simulator data được gắn provenance rõ.
- Evidence pack và known limitations đã được leader review.

# Backend Tasks

## Muc tieu va pham vi

Xay dung FastAPI la system of record cho station, measurement, alert, approval va audit. Backend la cua vao duy nhat cho Frontend va AI Agent; MQTT Consumer dung service ingestion noi bo. Agent khong truy cap PostgreSQL truc tiep va khong co quyen publish MQTT.

## Thu tu thuc hien

`BE-001 -> BE-002 -> BE-003 -> BE-004 -> BE-005 -> BE-006 -> BE-007`.

## BE-001 - Khoi tao API va health check

**Muc tieu:** dich vu khoi dong duoc trong Docker Compose va bao cao dung tinh trang dependency.

**Thuc hien:**

1. Tao FastAPI app, prefix `/api/v1`, CORS tu environment va OpenAPI tai `/docs`.
2. Tao config typed cho database URL, broker URL, allowed origins, log level va stale threshold; config sai phai fail fast khi startup.
3. Them `GET /health` va `GET /ready`. Health chi kiem tra process; readiness kiem tra PostgreSQL va dependency bat buoc.
4. Tao middleware gan `request_id`, structured log va exception handler chung.
5. Chot error envelope: `code`, `message`, `request_id`, `details`; khong tra stack trace cho client.

**Dau ra:** service backend, Docker healthcheck, OpenAPI, va huong dan cac status `200/503`.

**Kiem thu:** app startup, config thieu, database down, CORS origin hop le/khong hop le, va error response schema.

**Xong khi:** `/health` tra 200 khi process song; `/ready` tra 503 khi DB down va logs co request id ma khong lo secret.

## BE-002 - Station va measurement read API

**Muc tieu:** frontend va tools doc duoc du lieu cua S01-S05 tu PostgreSQL.

**Thuc hien:**

1. Tao migration/schema cho `stations`, `measurements`, `station_status`; `station_id` bat bien, `message_id` unique, timestamp co timezone.
2. Tao seed idempotent cho S01-S05: name, latitude, longitude, location type, active flag.
3. Viet repository/service tach khoi route; route khong chua SQL va khong tu tinh current PM2.5 neu database co du lieu.
4. Implement `GET /stations`, `GET /stations/{station_id}/current`, `GET /stations/{station_id}/history?hours=1..72`.
5. Response phai co `source`, `updated_at`, `status`, `is_stale`; history sap xep tang dan theo `measured_at`.
6. Dinh nghia 404 station khong ton tai, 422 filter sai, va `items: []` cho station chua co measurement.

**Dau ra:** API contract dung `specs/api-contracts.md`; index `(station_id, measured_at)` phuc vu history.

**Kiem thu:** 5 tram seed, current co/khong co data, history boundary 1/72 gio, 404, pagination neu co, va schema snapshot.

**Xong khi:** map co the render 5 tram tu API, khong can fallback hard-code o client.

## BE-003 - Ingestion validation boundary

**Muc tieu:** chi measurement hop le moi duoc persist va duoc phep anh huong den current/alert/forecast.

**Thuc hien:**

1. Dinh nghia Pydantic schema cho measurement va status MQTT theo `specs/data-contracts.md`.
2. Validate topic/station id, `message_id`, PM2.5 khong am, numerical fields, timestamp RFC3339 timezone, source va max future skew.
3. Xac dinh stale bang config; invalid/stale phai duoc gan ly do ro rang.
4. Dung unique `message_id` va transaction idempotent de xu ly at-least-once delivery.
5. Luu reject metric/log co `reason`, topic, station neu co; khong log raw payload co secret.
6. Chi phat event `measurement.accepted` sau khi transaction persist thanh cong.

**Dau ra:** `MeasurementIngestionService` co contract noi bo va dashboard metrics accept/reject.

**Kiem thu:** JSON loi, missing field, PM2.5 am, station la, duplicate, late event, timestamp tuong lai va stale boundary.

**Xong khi:** du lieu invalid/stale khong xuat hien trong current API, Alert Engine hay Agent tools.

## BE-004 - Alert Engine PM2.5

**Muc tieu:** tao alert nhat quan tu measurement valid, fresh va co kha nang truy vet rule.

**Thuc hien:**

1. Can Mentor xac nhan threshold/severity/cooldown; tam thoi de bang rule trong config versioned, khong hard-code trong route.
2. Tao entity `alerts`: station, rule id/version, observed/threshold value, severity, status, created/resolved time.
3. Goi engine sau accepted measurement; evaluate theo station va gia tri moi nhat.
4. Dedupe active alert cung station+rule; update observed value thay vi tao spam alert.
5. Dinh nghia resolve policy khi gia tri ha thap hon nguong hoac manager resolve thu cong.
6. Implement `GET /alerts?status=&station_id=` va action resolve co RBAC.

**Dau ra:** active/resolved alerts va event log cho create/update/resolve.

**Kiem thu:** duoi/bang/tren threshold, repeated spike, cooldown, stale measurement, manual resolve va authorization.

**Xong khi:** spike tu simulator tao dung mot alert tren API va co the hien thi o frontend.

## BE-005 - HITL approvals API

**Muc tieu:** manager la nguoi duy nhat chap thuan/tuchoi warning proposal; Agent khong the bypass luong nay.

**Thuc hien:**

1. Tao `approval_requests` voi proposal content, evidence, requester, status, version va timestamps.
2. Implement list/detail pending va `POST approve`, `POST reject`; reject note la bat buoc neu policy yeu cau.
3. Enforce role manager o backend; UI an nut khong thay the cho authorization.
4. Dung optimistic locking/version de chan double review va tra `409` khi request da doi.
5. Approve tao dispatch intent; chi dispatcher moi duoc publish command, reject tuyet doi khong tao intent.
6. Tra response co trang thai moi, reviewer, audit reference va command outcome neu co.

**Dau ra:** API HITL versioned va state machine `pending -> approved|rejected`.

**Kiem thu:** 401/403, approve, reject, double-click, two reviewers, transition sai va dispatch failure.

**Xong khi:** khong co endpoint nao cho Agent hoac normal user tu approve/reject.

## BE-006 - Audit log service

**Muc tieu:** truy vet duoc ai da de xuat, review va dispatch gi trong demo.

**Thuc hien:**

1. Tao append-only `audit_logs` voi actor, role, action, target type/id, outcome, correlation id, created_at va metadata da redact.
2. Ghi event cho proposal create, approve, reject, dispatch attempt/success/failure va manual alert resolution.
3. Dua audit write vao transaction hoac outbox phu hop de failure khong bi mat dau vet.
4. Cung cap query theo proposal, station, action va time range cho manager/debug.
5. Dat retention va cam luu API key, password, raw prompt nhay cam.

**Dau ra:** audit service, API read-only co RBAC va evidence cho runbook.

**Kiem thu:** moi HITL action co event; dispatch failure van co audit; pagination, permission va redaction.

**Xong khi:** co the trace `proposal_id -> reviewer action -> dispatch outcome` bang audit log.

## BE-007 - Background jobs va status

**Muc tieu:** forecast va agent work khong block HTTP request va co kha nang theo doi.

**Thuc hien:**

1. Chot Celery/Redis hoac co che queue da duoc nhom duyet; tach worker khoi API process.
2. Tao POST bat dong bo cho forecast/agent dung idempotency key va task id on dinh.
3. Luu job states `queued/running/succeeded/failed`, progress, result pointer, error code va retry count.
4. Implement `GET /jobs/{task_id}`; khong tra raw exception/model response nhay cam.
5. Dat timeout, retry capped va dead-letter/failed state ro rang.

**Dau ra:** worker, job registry va status API.

**Kiem thu:** worker down, duplicate idempotency key, timeout, retry exhaustion, job khong ton tai.

**Xong khi:** frontend co the poll job status va user nhan duoc loi co the hanh dong.

## Moc va phu thuoc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | BE-001..BE-004 | PostgreSQL schema, DI-001..DI-005 |
| 08/08 | BE-005..BE-007 | AI-005, frontend manager UI, worker/queue |

## DoD chung

- Route co OpenAPI, unit test service va integration test API cho happy/error path.
- Khong route truy cap DB truc tiep; khong secret trong response/log/audit.
- API contract thay doi phai cap nhat `specs/api-contracts.md` va co test regression.

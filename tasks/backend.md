# Công việc Backend

## Mục tiêu và phạm vi

Xay dung FastAPI la system of record cho station, measurement, alert, approval va audit. Backend la cua vao duy nhat cho Frontend va AI Agent; MQTT Consumer dung service ingestion noi bo. Agent khong truy cap PostgreSQL truc tiep va khong co quyen publish MQTT.

## Thứ tự thực hiện

`BE-001 -> BE-002 -> BE-003 -> BE-004 -> BE-005 -> BE-006 -> BE-007`.

## BE-001 - Khởi tạo API và kiểm tra sức khỏe

**Mục tiêu:** dich vu khoi dong duoc trong Docker Compose va bao cao dung tinh trang dependency.

**Thực hiện:**

1. Tao FastAPI app, prefix `/api/v1`, CORS tu environment va OpenAPI tai `/docs`.
2. Tao config typed cho database URL, broker URL, allowed origins, log level va stale threshold; config sai phai fail fast khi startup.
3. Them `GET /health` va `GET /ready`. Health chi kiem tra process; readiness kiem tra PostgreSQL va dependency bat buoc.
4. Tao middleware gan `request_id`, structured log va exception handler chung.
5. Chot error envelope: `code`, `message`, `request_id`, `details`; khong tra stack trace cho client.

**Đầu ra:** service backend, Docker healthcheck, OpenAPI, va huong dan cac status `200/503`.

**Kiểm thử:** app startup, config thieu, database down, CORS origin hop le/khong hop le, va error response schema.

**Hoàn thành khi:** `/health` tra 200 khi process song; `/ready` tra 503 khi DB down va logs co request id ma khong lo secret.

## BE-002 - API đọc trạm và phép đo

**Mục tiêu:** frontend va tools doc duoc du lieu cua S01-S05 tu PostgreSQL.

**Thực hiện:**

1. Tao migration/schema cho `stations`, `measurements`, `station_status`; `station_id` bat bien, `message_id` unique, timestamp co timezone.
2. Tao seed idempotent cho S01-S05: name, latitude, longitude, location type, active flag.
3. Viet repository/service tach khoi route; route khong chua SQL va khong tu tinh current PM2.5 neu database co du lieu.
4. Implement `GET /stations`, `GET /stations/{station_id}/current`, `GET /stations/{station_id}/history?hours=1..72`.
5. Response phai co `source`, `updated_at`, `status`, `is_stale`; history sap xep tang dan theo `measured_at`.
6. Dinh nghia 404 station khong ton tai, 422 filter sai, va `items: []` cho station chua co measurement.

**Đầu ra:** API contract dung `specs/api-contracts.md`; index `(station_id, measured_at)` phuc vu history.

**Kiểm thử:** 5 tram seed, current co/khong co data, history boundary 1/72 gio, 404, pagination neu co, va schema snapshot.

**Hoàn thành khi:** map co the render 5 tram tu API, khong can fallback hard-code o client.

## BE-003 - Biên kiểm tra dữ liệu đầu vào

**Mục tiêu:** chi measurement hop le moi duoc persist va duoc phep anh huong den current/alert/forecast.

**Thực hiện:**

1. Dinh nghia Pydantic schema cho measurement va status MQTT theo `specs/data-contracts.md`.
2. Validate topic/station id, `message_id`, PM2.5 khong am, numerical fields, timestamp RFC3339 timezone, source va max future skew.
3. Xac dinh stale bang config; invalid/stale phai duoc gan ly do ro rang.
4. Dung unique `message_id` va transaction idempotent de xu ly at-least-once delivery.
5. Luu reject metric/log co `reason`, topic, station neu co; khong log raw payload co secret.
6. Chi phat event `measurement.accepted` sau khi transaction persist thanh cong.

**Đầu ra:** `MeasurementIngestionService` co contract noi bo va dashboard metrics accept/reject.

**Kiểm thử:** JSON loi, missing field, PM2.5 am, station la, duplicate, late event, timestamp tuong lai va stale boundary.

**Hoàn thành khi:** du lieu invalid/stale khong xuat hien trong current API, Alert Engine hay Agent tools.

## BE-004 - Bộ máy cảnh báo PM2.5

**Mục tiêu:** tao alert nhat quan tu measurement valid, fresh va co kha nang truy vet rule.

**Thực hiện:**

1. Can Mentor xac nhan threshold/severity/cooldown; tam thoi de bang rule trong config versioned, khong hard-code trong route.
2. Tao entity `alerts`: station, rule id/version, observed/threshold value, severity, status, created/resolved time.
3. Goi engine sau accepted measurement; evaluate theo station va gia tri moi nhat.
4. Dedupe active alert cung station+rule; update observed value thay vi tao spam alert.
5. Dinh nghia resolve policy khi gia tri ha thap hon nguong hoac manager resolve thu cong.
6. Implement `GET /alerts?status=&station_id=` va action resolve co RBAC.

**Đầu ra:** active/resolved alerts va event log cho create/update/resolve.

**Kiểm thử:** duoi/bang/tren threshold, repeated spike, cooldown, stale measurement, manual resolve va authorization.

**Hoàn thành khi:** spike tu simulator tao dung mot alert tren API va co the hien thi o frontend.

## BE-005 - API phê duyệt HITL

**Mục tiêu:** manager la nguoi duy nhat chap thuan/tuchoi warning proposal; Agent khong the bypass luong nay.

**Thực hiện:**

1. Tao `approval_requests` voi proposal content, evidence, requester, status, version va timestamps.
2. Implement list/detail pending va `POST approve`, `POST reject`; reject note la bat buoc neu policy yeu cau.
3. Enforce role manager o backend; UI an nut khong thay the cho authorization.
4. Dung optimistic locking/version de chan double review va tra `409` khi request da doi.
5. Approve tao dispatch intent; chi dispatcher moi duoc publish command, reject tuyet doi khong tao intent.
6. Tra response co trang thai moi, reviewer, audit reference va command outcome neu co.

**Đầu ra:** API HITL versioned va state machine `pending -> approved|rejected`.

**Kiểm thử:** 401/403, approve, reject, double-click, two reviewers, transition sai va dispatch failure.

**Hoàn thành khi:** khong co endpoint nao cho Agent hoac normal user tu approve/reject.

## BE-006 - Dịch vụ nhật ký kiểm toán

**Mục tiêu:** truy vet duoc ai da de xuat, review va dispatch gi trong demo.

**Thực hiện:**

1. Tao append-only `audit_logs` voi actor, role, action, target type/id, outcome, correlation id, created_at va metadata da redact.
2. Ghi event cho proposal create, approve, reject, dispatch attempt/success/failure va manual alert resolution.
3. Dua audit write vao transaction hoac outbox phu hop de failure khong bi mat dau vet.
4. Cung cap query theo proposal, station, action va time range cho manager/debug.
5. Dat retention va cam luu API key, password, raw prompt nhay cam.

**Đầu ra:** audit service, API read-only co RBAC va evidence cho runbook.

**Kiểm thử:** moi HITL action co event; dispatch failure van co audit; pagination, permission va redaction.

**Hoàn thành khi:** co the trace `proposal_id -> reviewer action -> dispatch outcome` bang audit log.

## BE-007 - Tác vụ nền và trạng thái

**Mục tiêu:** forecast va agent work khong block HTTP request va co kha nang theo doi.

**Thực hiện:**

1. Chot Celery/Redis hoac co che queue da duoc nhom duyet; tach worker khoi API process.
2. Tao POST bat dong bo cho forecast/agent dung idempotency key va task id on dinh.
3. Luu job states `queued/running/succeeded/failed`, progress, result pointer, error code va retry count.
4. Implement `GET /jobs/{task_id}`; khong tra raw exception/model response nhay cam.
5. Dat timeout, retry capped va dead-letter/failed state ro rang.

**Đầu ra:** worker, job registry va status API.

**Kiểm thử:** worker down, duplicate idempotency key, timeout, retry exhaustion, job khong ton tai.

**Hoàn thành khi:** frontend co the poll job status va user nhan duoc loi co the hanh dong.

## Mốc và phụ thuộc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | BE-001..BE-004 | PostgreSQL schema, DI-001..DI-005 |
| 08/08 | BE-005..BE-007 | AI-005, frontend manager UI, worker/queue |

## Tiêu chí hoàn thành chung

- Route co OpenAPI, unit test service va integration test API cho happy/error path.
- Khong route truy cap DB truc tiep; khong secret trong response/log/audit.
- API contract thay doi phai cap nhat `specs/api-contracts.md` va co test regression.


## Bản đồ file theo task

| Task | File hiện có cần sửa | File/directory cần tạo hoặc cập nhật | Tài liệu và test liên quan |
|---|---|---|---|
| BE-001 | `backend/app/main.py`, `docker-compose.yml` | `backend/app/core/config.py`, `backend/app/core/logging.py`, `backend/app/api/errors.py` | `tests/test_api/test_health.py`, `specs/api-contracts.md` |
| BE-002 | `backend/app/main.py`, `backend/db/schema.sql`, `data/stations.json` | `backend/app/repositories/stations.py`, `backend/app/services/station_service.py` | `tests/test_api/test_stations.py`, `specs/domain-model.md` |
| BE-003 | `backend/db/schema.sql` | `backend/app/schemas/measurements.py`, `backend/app/services/ingestion_service.py` | `tests/test_services/test_ingestion.py`, `specs/data-contracts.md` |
| BE-004 | `backend/app/main.py` | `backend/app/services/alert_engine.py`, `backend/app/repositories/alerts.py` | `tests/test_services/test_alert_engine.py`, `adrs/0003-alert-and-hitl.md` |
| BE-005 | `backend/app/services/approval_service.py` | `backend/app/api/approvals.py`, `backend/app/repositories/approvals.py` | `tests/test_api/test_approvals.py`, `specs/api-contracts.md` |
| BE-006 | `backend/db/schema.sql` | `backend/app/services/audit_service.py`, `backend/app/repositories/audit_logs.py` | `tests/test_services/test_audit.py`, `docs/observability.md` |
| BE-007 | `backend/app/celery_app.py`, `backend/app/tasks/*.py` | `backend/app/services/job_service.py` | `tests/test_api/test_jobs.py`, `docs/test-plan.md` |

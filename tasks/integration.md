# Công việc Tích hợp

## Mục tiêu và phạm vi

Ket noi va chung minh duoc luong AirGuard AI end-to-end, co kha nang lap lai tren moi truong demo:

```text
Sensor Simulator -> MQTT -> Consumer -> PostgreSQL -> FastAPI -> Frontend
                                                |
                                                v
                                     Alert -> Forecast -> Agent -> HITL -> Audit
```

Integration khong duoc che dau loi bang mock khong gan nhan. Moi fallback duoc su dung trong demo phai hien source va gioi han ro rang.

## Thứ tự thực hiện

`INT-001 -> INT-002 -> INT-003 -> INT-004 -> INT-005 -> INT-006`.

## INT-001 - Docker Compose và contract môi trường

**Mục tiêu:** toan bo dependency chay bang mot quy trinh khoi dong co the tai lap.

**Thực hiện:**

1. Liet ke service: PostgreSQL, Mosquitto, backend API, MQTT Consumer, sensor simulator, frontend, worker/queue neu dung.
2. Chot ten service, network, port expose, persistent volumes, dependencies va healthchecks.
3. Tao `.env.example` day du: DB, MQTT, CORS, stale threshold, simulator interval, weather/LLM optional; khong them gia tri secret that.
4. Xac dinh startup order: DB/broker healthy -> migrations/seed -> consumer/API/worker -> simulator -> frontend.
5. Viet lenh start, stop, logs, health check va reset demo data an toan trong runbook.
6. Kiem tra container khong chay root neu co the, logs stdout, va restart policy phu hop.

**Đầu ra:** Compose topology, environment matrix va troubleshooting notes.

**Kiểm thử:** clean startup, restart tung service, broker/DB unavailable, port conflict va environment missing.

**Hoàn thành khi:** thanh vien khac co the chay stack tu README ma khong can sua source.

## INT-002 - Xác nhận data path end-to-end

**Mục tiêu:** chung minh measurement tu simulator hien dung tren dashboard va truy vet duoc.

**Thực hiện:**

1. Start normal scenario va chon mot message S01 lam trace sample.
2. Kiem tra topic/payload tren MQTT log, validator result, row PostgreSQL, station current, history API va marker/detail UI.
3. Doi chieu `message_id`, station id, PM2.5, timestamp, source va status tai moi hop.
4. Kiem tra 5 stations deu publish/persist; station list/map cap nhat theo polling/refresh policy.
5. Chay scenario duplicate, invalid, stale/offline va ghi expected behavior o tung layer.
6. Luu evidence: request id, query/log command, screenshot UI va ket qua API phuc vu rehearsal.

**Đầu ra:** integration test matrix va trace table `message_id -> database -> API -> UI`.

**Kiểm thử:** happy path, duplicate dedupe, malformed payload, stop simulator, restart consumer va database transient failure.

**Hoàn thành khi:** khong co gap gia tri/timestamp/source giua DB, API va UI cho message valid.

## INT-003 - Luồng cảnh báo

**Mục tiêu:** alert duoc sinh boi rule, hien dung va khong spam.

**Thực hiện:**

1. Chot threshold, severity va cooldown voi Mentor; ghi rule version cho demo.
2. Chay simulator spike deterministically tai mot station va luu message ids lien quan.
3. Xac minh consumer persist -> Alert Engine evaluate -> active alert create/update -> `/alerts` -> frontend panel/focus marker.
4. Chay repeated spike de kiem dedupe; chay recovery de kiem resolve policy.
5. Chay stale/invalid spike de xac minh khong tao alert.
6. Do latency tu publish den UI va dat budget demo; neu qua budget, tim diem nghen truoc rehearsal.

**Đầu ra:** ba evidence cases create, dedupe, resolve; bang threshold duoc duyet.

**Kiểm thử:** below/equal/above threshold, multi-station, repeated messages, stale/invalid, manual resolve va UI refresh.

**Hoàn thành khi:** spike scenario tao expected alert trong mot time window da chot va no hien thi dung tram/severity.

## INT-004 - Luồng công cụ Agent

**Mục tiêu:** chung minh Agent chi dung backend tools va xu ly failure an toan.

**Thực hiện:**

1. Cau hinh Agent endpoint chi tro ve backend integration environment; kiem tra Agent khong co DB/MQTT variables.
2. Chay golden prompts da duyet: current PM2.5, history, compare, weather, forecast, active alerts, user group, no-data.
3. Kiem tra trace `request_id`, intent, `used_tools`, tool result status va source/time trong answer.
4. Inject loi co kiem soat: backend timeout, 404, weather unavailable, station stale; xac nhan Agent noi thieu du lieu thay vi hallucinate.
5. Chay prompt injection/safety prompts; xac nhan Agent khong bo qua tools, khong chan doan y te, khong approve/reject.
6. Chon 3-5 prompts ngan, on dinh, co expected result lam script demo.

**Đầu ra:** Agent smoke report, prompt script va trace evidence.

**Kiểm thử:** tool routing, factual assertions, timeout, tool error, stale data, injection va latency p95.

**Hoàn thành khi:** moi prompt demo co expected tool trace va khong co fact moi truong khong truy ve duoc.

## INT-005 - Luồng HITL, dispatch và kiểm toán

**Mục tiêu:** chung minh warning proposal khong the di qua manager va audit.

**Thực hiện:**

1. Tao proposal bang Agent hoac fixture hop le, co evidence/current alert va proposal id.
2. Kiem tra frontend manager queue lay duoc pending proposal va detail evidence.
3. Chay reject case: manager note -> state rejected -> audit event -> khong co dispatch intent/MQTT command.
4. Chay approve case: state approved -> audit event -> dispatcher intent -> device ack neu DI-006 san sang.
5. Chay concurrent/double review va dispatch failure; UI/log phai phan anh server truth.
6. Query audit theo proposal id de in/ghi bang evidence: create, review, dispatch outcome.

**Đầu ra:** trace `proposal -> review -> audit -> dispatch -> device status` va known limitation neu device simulator chua co.

**Kiểm thử:** RBAC 403, pending no dispatch, reject no dispatch, approve success/fail, 409 concurrency va idempotency.

**Hoàn thành khi:** demo khong bao gio tuyen bo device da thuc thi khi command khong duoc approved va acknowledged.

## INT-006 - Diễn tập demo và điều kiện phát hành

**Mục tiêu:** demo MVP lap lai duoc trong khung thoi gian, co fallback minh bach.

**Thực hiện:**

1. Cap nhat `docs/demo-runbook.md` voi prerequisite, startup order, roles, commands, expected evidence va rollback.
2. Chuan bi 4 scenario: A normal dashboard, B spike -> alert, C Agent grounded, D proposal -> approve/reject -> audit.
3. Phan cong: presenter, nguoi dieu khien stack, nguoi theo doi logs, nguoi quyet dinh fallback.
4. Chay rehearsal tren may/moi truong gan demo; tinh toan thoi gian tung scenario va loai bo thao tac de loi.
5. Test failure drills: restart frontend, broker down, weather/LLM unavailable; chi dung fixture da gan nhan, khong gia so lieu live.
6. Luu screenshot/API output/log request ids va danh sach known limitations sau rehearsal.
7. Chi release khi tat ca critical gate pass; ghi nguoi chap thuan va thoi diem.

**Đầu ra:** runbook da duyet, rehearsal evidence, release checklist va fallback decisions.

**Kiểm thử:** full flow tu clean stack, mot service restart, browser refresh, loai bo stale data va manual recovery.

**Hoàn thành khi:** rehearsal thanh cong it nhat mot lan va team co the lap lai demo theo runbook ma khong can nho thu tu ngam dinh.

## Lịch thực hiện

| Ngay | Muc tieu integration | Bang chung can luu |
|---|---|---|
| 02/08 | INT-001 topology/env | healthchecks va startup log |
| 03/08 | INT-001 readiness | clean Compose startup |
| 04/08 | INT-002 normal data path | S01 message trace |
| 05/08 | INT-002 + INT-003 basic | 5 stations va spike alert prototype |
| 06/08 | INT-003 + INT-004 | alert evidence, Agent tool trace |
| 07/08 | INT-005 + INT-006 rehearsal 1 | approval/audit trace, screenshots |
| 08/08 | release rehearsal | full MVP evidence va known limitations |

## Điều kiện phát hành 08/08

- Simulator -> MQTT -> Consumer -> PostgreSQL -> FastAPI -> Frontend chay voi S01-S05.
- Spike valid/fresh tao alert co severity dung, duplicate khong spam, stale/invalid khong tao alert.
- Agent dung backend tool, hien source/trace, refusal dung khi tool/data loi.
- Proposal can manager approve/reject; moi action quan trong co audit event.
- Khong co secret trong repository, logs, response, screenshot hay runbook.
- Known limitations va fallback da duoc ghi ro; khong dien giai data simulator thanh quan trac chinh thuc.

## Phụ thuộc và leo thang rủi ro

| Rủi ro | Trigger | Hanh dong |
|---|---|---|
| Threshold chua chot | Truoc test spike 05/08 | Dung config tam thoi, yeu cau Mentor chot trong ngay |
| Consumer chua san sang | API van mock sau 04/08 | Uu tien DI-005, dong bang feature Agent/proposal phu thuoc data that |
| LLM/weather external loi | Rehearsal timeout/429 | Dung fallback fixture gan nhan ro, khong bo qua grounding |
| HITL chua on dinh | Approve/reject khong audit duoc | Khong demo device command; chi demo pending/review an toan |


## Bản đồ file theo task

| Task | File hiện có cần sửa | File/directory cần tạo hoặc cập nhật | Tài liệu và test liên quan |
|---|---|---|---|
| INT-001 | `docker-compose.yml`, `.env.example` | healthcheck/run scripts nếu cần | `docs/environment-setup.md`, Compose validation |
| INT-002 | `docker-compose.yml`, backend/API và frontend client | `tests/integration/test_data_path.py` | `docs/demo-runbook.md`, message trace |
| INT-003 | alert service, simulator scenario, frontend alerts | `tests/integration/test_alert_path.py` | ADR 0003, threshold matrix |
| INT-004 | `src/agents/`, backend Agent endpoints | `eval/golden_cases/` | `docs/agent-evaluation.md` |
| INT-005 | approvals/audit services, frontend approvals | `tests/integration/test_hitl_path.py` | audit trace/runbook |
| INT-006 | `docs/demo-runbook.md`, `presentation/` | rehearsal evidence folder | screenshots, known limitations |

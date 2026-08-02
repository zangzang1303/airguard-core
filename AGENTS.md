# AirGuard AI - Agent Handoff Guide

> Doc file nay truoc khi phan tich, sua code, chay service, thay doi contract hoac tao pull request. Day la handoff pack cho mot agent/may moi; no mo ta muc tieu, ranh gioi, hien trang can xac minh va quy trinh tiep tuc cong viec an toan.

## 1. North star

AirGuard AI la MVP quan sat PM2.5 ngoai troi quanh VinUni/Vinhomes Ocean Park. He thong dung 5 sensor gia lap (S01-S05), MQTT, PostgreSQL, FastAPI, React va AI Agent dung tool calling. San pham giup nguoi dung xem data, alert, forecast ngan han va gui warning proposal qua Human-in-the-Loop (HITL).

Day la demo hoc tap/MVP, **khong phai he thong quan trac chinh thuc**, khong dua ra chan doan y te va khong dieu khien thiet bi that.

Moc bat buoc:

| Moc | Ket qua |
|---|---|
| Thu Tu 05/08/2026 | Core modules chay doc lap, data/API contracts ro rang, 5 tram hien thi duoc |
| Thu Bay 08/08/2026 | MVP end-to-end: simulator -> MQTT -> DB -> API -> dashboard -> alert/forecast/Agent/HITL/audit |

## 2. Nguyen tac bat buoc

1. **Grounding truoc fluency.** Agent khong duoc tu tao PM2.5, forecast, weather, alert, timestamp, station status hay chi tiet user. Moi environmental fact phai den tu backend tool result cua cung request.
2. **Backend la system of record.** Frontend khong ket noi MQTT truc tiep va khong tu tinh business alert. Agent khong truy cap PostgreSQL truc tiep.
3. **HITL khong duoc bypass.** Agent chi tao proposal `pending`; chi manager role duoc approve/reject. Command device chi duoc dispatcher publish sau approval server-side.
4. **Data quality la gate.** Data invalid, stale hoac station offline khong duoc dung cho current value, alert, forecast hoac warning proposal.
5. **Minh bach simulator.** Moi payload MVP co `source=simulator`; UI/Agent khong duoc dien dat no nhu quan trac chinh thuc/live certified.
6. **Audit hanh dong quan trong.** Proposal create, approve, reject, dispatch va failure phai co audit record.
7. **Khong secret.** Khong commit `.env`, API key, password, token; khong in secret trong log, response, screenshot hay issue.
8. **Contract first.** Thay doi API, MQTT payload, data schema, rule hay tool schema phai cap nhat specs va tests trong cung thay doi.

## 3. Kien truc muc tieu

```text
Sensor Simulator
  -> MQTT Mosquitto topics
  -> MQTT Consumer / validation
  -> PostgreSQL (stations, measurements, alerts, approvals, audit)
  -> FastAPI /api/v1
  -> React dashboard

FastAPI tool endpoints -> AI Agent (LangGraph/tool calling)
AI Agent -> warning proposal -> manager HITL -> audit -> optional device dispatcher/simulator

Weather provider/fallback -> weather context -> forecast + Agent
```

### Bien gioi ownership

| Thanh phan | Duoc lam | Khong duoc lam |
|---|---|---|
| Simulator | publish payload gia lap/status | gia danh data official, tu sua DB |
| MQTT Consumer | validate, persist, status/freshness | tu tao recommendation |
| Backend | API, alert rules, RBAC, approval, audit | expose DB credential cho Agent/client |
| Frontend | render API state, interaction UI | MQTT direct, bypass HITL, suy dien alert |
| Agent | tool call, explain, recommend, propose | invent facts, approve/reject, direct DB/MQTT |
| Manager | approve/reject proposal | sua audit history |

## 4. Domain nhanh

- `Station`: S01-S05, immutable id, name, lat/lon, location type, active status.
- `Measurement`: `message_id`, station, PM2.5, weather fields, `measured_at`, `received_at`, source, validation state.
- `StationStatus`: online/offline/stale/invalid, `last_seen`.
- `Alert`: rule version, severity, observed/threshold value, `active/resolved`.
- `Forecast`: station, horizon 1-3h, values/range, model/source/confidence/freshness.
- `WarningProposal`: evidence, target/action, rationale, policy version, `pending/approved/rejected`.
- `AuditLog`: append-only actor/action/target/outcome/correlation id/time.
- User groups: `normal`, `sensitive`, `outdoor_sport`.

Dinh nghia day du nam o [specs/domain-model.md](specs/domain-model.md) va [docs/glossary.md](docs/glossary.md).

## 5. Contracts khong duoc pha vo

### MQTT topics

```text
airguard/stations/{station_id}/measurements
airguard/stations/{station_id}/status
airguard/devices/{device_id}/command
airguard/devices/{device_id}/status
```

Measurement toi thieu: `message_id`, `station_id`, `pm25`, `timestamp` timezone-aware, `source=simulator`. Dung schema chinh thuc trong [specs/data-contracts.md](specs/data-contracts.md).

### REST va Agent tools

REST contract o [specs/api-contracts.md](specs/api-contracts.md). Tool registry bat buoc:

- `get_current_pm25`
- `get_station_history`
- `compare_stations`
- `get_weather_context`
- `get_pm25_forecast`
- `get_active_alerts`
- `get_user_profile`
- `create_warning_proposal`

Neu tool loi: tra structured error, Agent noi khong du du lieu. Khong co fallback hallucination.

## 6. Hien trang va cach lam viec voi repo

Repo co the chua o trang thai MVP hoan chinh. Khong gia dinh mock endpoint la pipeline that; doc code va test truoc khi tuyen bo mot capability da san sang. Khi bat dau mot task:

1. Doc `README.md`, file task lien quan trong `tasks/`, specs va ADR lien quan.
2. Kiem tra `git status --short`; bao ton thay doi nguoi dung/co agent khac tao ra.
3. Tim code bang `rg` truoc khi sua; xac dinh owner module va contract phu thuoc.
4. Chot acceptance criteria va test plan truoc implementation.
5. Implement scope nho nhat phu hop codebase; khong refactor vo can.
6. Chay test/lint/build phu hop; neu khong chay duoc, ghi ro ly do va risk.
7. Cap nhat docs, task status va ai-log neu quyet dinh/experiment quan trong thay doi.

Khong reset/revert/xoa thay doi khong phai cua minh. Khong dung destructive git command neu chua duoc yeu cau ro rang.

## 7. Runbook cho may moi

### Yeu cau

- Docker Desktop/Compose
- Python va Node.js theo version duoc xac nhan trong `README.md`/container files
- Copy `.env.example` thanh `.env`, dien secret local neu can; `.env` khong bao gio commit

### Thu tu khoi dong muc tieu

1. Start PostgreSQL va Mosquitto; cho healthy.
2. Chay migration/seed S01-S05.
3. Start backend, consumer va worker (neu feature can queue).
4. Start sensor simulator.
5. Start frontend.
6. Kiem tra health, stations API, MQTT logs, database row va map.

Lenh chinh xac va troubleshooting: [docs/environment-setup.md](docs/environment-setup.md), [docs/demo-runbook.md](docs/demo-runbook.md). Neu code hien tai chua ho tro mot buoc, ghi no vao known limitation thay vi tao ket qua gia.

## 8. Quality gates

Truoc merge/demo, xac minh:

- Unit tests cho logic moi va integration test cho API/pipeline contract bi anh huong.
- Happy path va error path: invalid, stale, offline, duplicate, timeout, permission denial.
- API/MQTT/tool schema khop specs; migration an toan va seed idempotent neu co data change.
- Agent tests bao gom grounding, tool failure, injection, safety, proposal eligibility.
- UI co loading/empty/error state; khong coi fixture la live data.
- Logs/audit co request/correlation id, khong lo secret/PII.

Chi tiet: [docs/test-plan.md](docs/test-plan.md), [docs/definition-of-done.md](docs/definition-of-done.md), [docs/agent-evaluation.md](docs/agent-evaluation.md).

## 9. Quy tac thay doi

| Thay doi | Bat buoc cap nhat |
|---|---|
| API request/response/status code | `specs/api-contracts.md`, tests, frontend/tool adapter |
| MQTT field/topic/QoS | `specs/data-contracts.md`, simulator, consumer, tests |
| Entity/migration | `specs/domain-model.md`, migration, repository tests |
| Alert threshold/HITL | ADR 0003, acceptance criteria, config/test matrix |
| Agent graph/tool/policy | ADR 0004, `docs/agent-evaluation.md`, golden cases |
| Forecast method | ADR 0006, API/tool contract, evaluation |
| Architecture/technology decision | ADR moi hoac cap nhat ADR, README, dependencies/risks |

Khong sua ADR da accepted de doi lich su; tao ADR moi de supersede no.

## 10. Tai lieu can doc theo vai tro

| Vai tro | Doc truoc |
|---|---|
| Backend | `tasks/backend.md`, specs API/data/domain, ADR 0001-0003, test plan |
| Frontend | `tasks/frontend.md`, API contracts, user stories, acceptance criteria |
| AI Agent | `tasks/ai-agent.md`, ADR 0004/0006, agent evaluation, security guidelines |
| Data/IoT | `tasks/data-iot.md`, data contracts, ADR 0005, observability |
| Integrator/demo | `tasks/integration.md`, roadmap, dependencies, risks, demo runbook |
| Product/PM | product vision, features, backlog, user stories, acceptance criteria |

## 11. Quyet dinh can xac nhan voi Mentor/nhom

- PM2.5 threshold, severity labels, cooldown va alert resolution policy.
- Toa do/ten chinh thuc cua S01-S05.
- Nguon Weather API, key ownership, rate limit va fallback policy.
- Authentication/RBAC provider va danh sach manager demo.
- Device command scope: co demo device simulator hay chi demo HITL/audit.
- Forecast model, confidence presentation va success metric sau MVP.

Danh sach song: [planning/dependencies.md](planning/dependencies.md), [planning/risks.md](planning/risks.md).

## 12. Khi bi block

- Contract chua ro: de xuat option va cap nhat open question, khong tu y pha contract.
- External service loi: dung fixture/fallback chi khi duoc gan nhan ro; ghi impact vao runbook.
- Data quality loi: dung downstream action, bao cao reason code, khong "sua" bang cach bo qua validation.
- Co thay doi song song: doc diff, preserve no, va chi hoi khi conflict khong the tu giai quyet.

## 13. Navigation

- [README.md](README.md): tong quan, quick start, links.
- [specs/](specs): product va contracts.
- [adrs/](adrs): cac quyet dinh kien truc.
- [planning/](planning): milestone, backlog, dependency, risk, sprint.
- [tasks/](tasks): execution plan theo workstream.
- [docs/](docs): workflow, test, security, observability, demo.
- [templates/](templates): format task/ADR/PR/bug/AI log.

## 14. Handoff note template

Truoc khi dung mot phien lam viec dang do, cap nhat `.ai-log/` theo `templates/ai-log-template.md` voi: muc tieu, file da sua, decisions, tests da chay/khong chay, blockers, next command/next step. Handoff tot la nguoi ke tiep co the tiep tuc ma khong can doan y dinh cua nguoi truoc.

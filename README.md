# AirGuard AI

AirGuard AI la MVP theo doi PM2.5 ngoai troi quanh VinUni/Vinhomes Ocean Park. He thong dung sensor simulator, MQTT, PostgreSQL, FastAPI, React va AI Agent co tool calling de hien thi data, canh bao, forecast ngan han va warning proposal co Human-in-the-Loop.

> Du lieu trong MVP la gia lap (`source=simulator`), khong phai quan trac chinh thuc va khong phuc vu chan doan y te.

## Muc tieu MVP

- Quan sat PM2.5 tai 5 tram S01-S05 tren ban do.
- Dua data tu simulator qua MQTT, validation, PostgreSQL, REST API va dashboard.
- Tao alert bang Rule Engine khi PM2.5 vuot nguong duoc duyet.
- Forecast ngan han 1-3 gio co source/freshness ro rang.
- Agent tra loi dua tren backend tools, khong phat minh du lieu.
- Agent chi tao warning proposal; manager approve/reject va moi action quan trong co audit log.

## Kien truc

```text
Simulator -> MQTT -> Consumer -> PostgreSQL -> FastAPI -> React
                                  |                 |
                                  +-> Alert/Forecast +-> Agent tools -> HITL -> Audit
```

## Moc

| Ngay | Cam ket |
|---|---|
| 05/08/2026 | Core modules chay doc lap, contracts va dashboard 5 tram co ban |
| 08/08/2026 | MVP end-to-end co data path, alert, Agent grounded, HITL va audit |

## Quick start

1. Doc [AGENTS.md](AGENTS.md) neu ban la contributor/agent moi.
2. Copy `.env.example` thanh `.env`; khong commit `.env`.
3. Khoi dong stack bang Docker Compose theo [docs/environment-setup.md](docs/environment-setup.md).
4. Kiem tra `/health`, `/api/v1/stations`, logs simulator/consumer va dashboard.
5. Chay scenario demo theo [docs/demo-runbook.md](docs/demo-runbook.md).

Lenh chinh xac phu thuoc vao compose/scripts hien co trong repo; khong tuyen bo pipeline da complete neu chi mock endpoint dang chay.

## Tai lieu chinh

| Nhu cau | Tai lieu |
|---|---|
| Handoff va quy tac agent | [AGENTS.md](AGENTS.md) |
| Product, users, features | [specs/](specs) |
| Frontend screens, flows, validation, states va roles | [specs/frontend-screen-spec.md](specs/frontend-screen-spec.md) |
| API, MQTT, data contracts | [specs/api-contracts.md](specs/api-contracts.md), [specs/data-contracts.md](specs/data-contracts.md) |
| Architecture decisions | [adrs/](adrs) |
| Roadmap va backlog | [planning/](planning) |
| Work plans | [tasks/](tasks) |
| Run/test/security/ops | [docs/](docs) |

## Non-negotiables

- Frontend khong ket noi MQTT truc tiep.
- Agent khong truy cap database truc tiep, khong bịa environmental facts, khong approve/reject.
- Data invalid/stale/offline khong duoc kich hoat alert, forecast hay proposal.
- Device command chi sau server-side approval; device demo luon la simulated.
- Khong commit secret hay log secret/PII.

## Team work

Dung conventional commits, PR co test evidence, va cap nhat docs/contracts khi thay doi interface. Chi tiet tai [docs/development-workflow.md](docs/development-workflow.md) va [docs/git-conventions.md](docs/git-conventions.md).

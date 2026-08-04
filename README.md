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
| API, MQTT, data contracts | [specs/api-contracts.md](specs/api-contracts.md), [specs/data-contracts.md](specs/data-contracts.md) |
| Architecture decisions | [adrs/](adrs) |
| Roadmap va backlog | [planning/](planning) |
| Work plans | [tasks/](tasks) |
| Run/test/security/ops | [docs/](docs) |

## 🛠 Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| AI Agent | LangGraph + LangChain | Latest |
| Backend | FastAPI + Uvicorn | 0.100+ |
| LLM | OpenAI GPT-4o-mini | API |
| Frontend | Next.js / Streamlit | 14+ / 1.30+ |
| Database | SQLite (dev) / PostgreSQL (prod) | — |
| DevOps | Docker + GitHub Actions | — |
| Testing | pytest + pytest-asyncio | 8+ |

## 📊 AI Usage Logging

Template đã tích hợp sẵn auto-logging hooks cho 6 AI tools:

| Tool | Cơ chế | Config |
|------|--------|--------|
| Claude Code | `.claude/settings.json` hooks | Tự động |
| Cursor | `.cursor/hooks.json` | Tự động |
| OpenAI Codex CLI | `.codex/hooks.json` | Tự động |
| Gemini CLI | `.gemini/settings.json` | Tự động |
| GitHub Copilot | `.github/hooks/hooks.json` | Tự động |
| Antigravity IDE | Pre-push scan transcript | Tự động trên `git push` |

Tất cả prompts và tool calls được log vào `.ai-log/session.jsonl` và tự động submit lên grading server mỗi khi `git push`.

**ChatGPT / web tools khác** — log thủ công:
```bash
bash scripts/_pyrun.sh scripts/log_manual.py --tool chatgpt --prompt "What you asked"
```

> ⚠️ Chạy `bash scripts/setup_hooks.sh` một lần sau khi clone để cài pre-push hook.

## Team work

Dung conventional commits, PR co test evidence, va cap nhat docs/contracts khi thay doi interface. Chi tiet tai [docs/development-workflow.md](docs/development-workflow.md) va [docs/git-conventions.md](docs/git-conventions.md).

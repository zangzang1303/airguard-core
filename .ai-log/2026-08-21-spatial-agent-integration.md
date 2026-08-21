# AI Work Log

## Date / agent / machine

- Date: 21/08/2026
- Agent: Codex, Người A workstream
- Workspace: `E:\Vinproject\P-074`

## Goal

Hoàn thiện luồng Agent sử dụng `get_spatial_air_quality` cho câu hỏi so sánh POI và phân tích hướng gió, đồng thời giữ grounding/fail-closed.

## Context read

- `AGENTS.md`
- `tasks/ai-agent.md`
- `tasks/backlog5/spatial-heatmap-dispersion.md`
- `tasks/backlog5/parallel-work-coordination.md`
- ADR 0004, 0006, 0007, 0008
- `docs/agent-evaluation.md`, `docs/security-guidelines.md`

## Files changed

- `backend/app/services/station_service.py`
- `backend/app/services/spatial_dispersion_service.py`
- `src/agents/policies/spatial_response.py`
- `src/agents/policies/grounding.py`
- `src/agents/response_composer.py`
- Spatial schemas/adapters in `src/agents/tools/`
- `tests/test_agents/test_grounding.py`, `tests/test_agents/test_tools.py`
- `tests/test_backend/test_spatial_dispersion.py`
- Spatial golden cases and Agent evaluation docs
- Spatial/Agent task status docs

## Decisions and rationale

- Thêm deterministic `spatial` intent trước compare/weather để hai câu mẫu không còn rơi vào `out_of_scope`.
- Dùng catalog tọa độ tĩnh allow-list; mọi giá trị môi trường vẫn lấy từ grid của tool cùng request.
- So sánh POI dùng điểm grid gần nhất và nói rõ không phải trạm đo tại POI.
- Phân tích gió chỉ là suy luận hình học theo quy ước vector của model; không xác nhận nguồn phát thải hoặc mô hình vật lý.
- Typed output giữ `model`, `extent`, `station_inputs` để adapter không làm mất provenance.
- Giữ fallback mặc định của `StationService` cho caller cũ, nhưng buộc Spatial dùng `allow_fallback=False`; dữ liệu DB rỗng/stale/offline fail với `insufficient_spatial_data`, còn lỗi DB được chuẩn hóa thành `spatial_station_data_unavailable`.
- Đồng bộ Agent fixture với typed contracts: history được trả theo thứ tự tăng dần và đúng station; alert dùng ổn định `alert-S02-001`, `fixture_alert_rule` và rule version để grounding/proposal idempotency dùng cùng evidence.

## Commands/tests run and results

- Spatial/backend/tool suite: `54 passed`, gồm test giữ/require typed provenance, DB rỗng, DB lỗi, toàn bộ trạm stale/offline và tương thích fallback mặc định.
- Agent Spatial routing/composer: `6 passed`.
- Hai golden case Spatial: pass.
- Integration `Agent graph -> HTTP adapter -> FastAPI -> Spatial service`: pass.
- Ruff trên toàn bộ file liên quan: pass.
- Agent grounding/proposal/evaluation/tool suite: `84 passed`.
- Full regression: `232 passed`, không còn lỗi; Ruff pass.
- `git diff --check`: không có whitespace error; chỉ có cảnh báo LF/CRLF của working tree Windows.

## Contracts/risks changed

- Tool registry version: `2026-08-21.ai-spatial-003`.
- Integrator vẫn cần cập nhật API specs và shared frontend types theo coordination contract.
- Integrator cần bổ sung error code additive `spatial_station_data_unavailable` vào API spec khi đồng bộ Spatial contract.

## Blockers/open questions

- Cần Integrator áp dụng shared API/frontend contract fields.

## Next exact step

Integrator cập nhật `specs/api-contracts.md` và `frontend/src/types/index.ts`, sau đó chạy full integration suite.

## Handoff IDs (request/message/proposal/job)

- Không có external request/proposal/job ID.

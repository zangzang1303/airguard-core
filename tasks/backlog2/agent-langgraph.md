# Backlog 2C — Agent/LangGraph

## Cách tích checklist

- `[ ]` = chưa kiểm thử.
- Đổi thành `[x]` khi tool trace/golden case pass và không có hallucination.
- Proposal chỉ được tích khi bắt đầu `pending` và có evidence/permission đúng.
- Ghi input, tool result, response, error code và proposal/correlation ID.

**Owner:** Thành viên Agent/AI  
**Mục tiêu:** bảo đảm Agent grounded, an toàn và tạo proposal đúng HITL.

## Nhiệm vụ

### B2-AI-01 — Tool contract audit

- [x] Kiểm tra 8 tools: current, history, compare, weather, forecast, alerts, profile, proposal.
- [x] Đối chiếu input/output với `specs/api-contracts.md` và `docs/agent-tool-registry.md`.
- [x] Backend/tool failure phải trả structured error.
- [x] Agent không có DB credential, MQTT credential hoặc approve/reject tool.

### B2-AI-02 — Grounding tests

- [x] Current PM2.5 lấy từ backend result.
- [x] History/forecast có station, source, freshness, confidence.
- [x] Station stale/offline/invalid thì Agent từ chối dùng dữ liệu.
- [x] Weather fallback phải được gắn nhãn.
- [x] Không tự suy đoán user group hoặc dữ liệu người dùng.

### B2-AI-03 — Proposal workflow

- [x] Proposal chỉ tạo khi station fresh/online, có active alert và evidence đủ.
- [x] Proposal luôn bắt đầu `pending`.
- [x] Response nói rõ manager cần review.
- [x] Tool timeout/failed không được nói là proposal đã gửi thành công.
- [x] Kiểm tra `proposal_id`, policy version và correlation ID.

### B2-AI-04 — Safety/evaluation

- [x] Tool timeout.
- [x] Backend 403/404/503.
- [x] Prompt injection yêu cầu bỏ qua tool.
- [x] Yêu cầu Agent tự approve/reject.
- [x] Yêu cầu chẩn đoán y tế hoặc khẳng định live certified data.
- [x] Chạy golden cases trong `docs/agent-evaluation.md` và lưu kết quả.

## Kết quả kiểm chứng 11/08/2026

- B2-AI-01: `tests/test_agents/test_tools.py` — 20 passed; registry đủ 8 tool, structured error, active-alert backend filter và credential boundary pass.
- B2-AI-02: grounding/forecast/recommendation suite — 50 passed; stale/offline/invalid và weather fallback đều fail closed hoặc được gắn nhãn.
- B2-AI-03: Agent proposal + backend contract/service suite — 29 passed; fixture trả `proposal-001`, trạng thái `pending`, policy `2026-08-08.ai-005`, correlation ID khớp request trace.
- B2-AI-04: focused safety/evaluation suite — 69 passed; golden set 39/39, grounding/safety/proposal/error transparency đều 100%.
- Docker live recheck: MQTT→DB, 5/5 stations và các health endpoint pass trên 8000/8001/5173; `get_active_alerts` trả success với active-only filter; yêu cầu tiếng Việt “tự phê duyệt” trả `hitl_bypass/refused`, không gọi tool và không tạo proposal.
- Full repository: 131 passed; hai regression trong `tests/test_scripts/test_log_hook.py` đã được sửa và focused gate pass 2/2.

## Acceptance

- Không hallucinate environmental fact.
- Không bypass HITL.
- Không truy cập DB/MQTT trực tiếp.
- Có structured refusal khi thiếu hoặc stale data.

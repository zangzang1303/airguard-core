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

- [ ] Kiểm tra 8 tools: current, history, compare, weather, forecast, alerts, profile, proposal.
- [ ] Đối chiếu input/output với `specs/api-contracts.md` và `docs/agent-tool-registry.md`.
- [ ] Backend/tool failure phải trả structured error.
- [ ] Agent không có DB credential, MQTT credential hoặc approve/reject tool.

### B2-AI-02 — Grounding tests

- [ ] Current PM2.5 lấy từ backend result.
- [ ] History/forecast có station, source, freshness, confidence.
- [ ] Station stale/offline/invalid thì Agent từ chối dùng dữ liệu.
- [ ] Weather fallback phải được gắn nhãn.
- [ ] Không tự suy đoán user group hoặc dữ liệu người dùng.

### B2-AI-03 — Proposal workflow

- [ ] Proposal chỉ tạo khi station fresh/online, có active alert và evidence đủ.
- [ ] Proposal luôn bắt đầu `pending`.
- [ ] Response nói rõ manager cần review.
- [ ] Tool timeout/failed không được nói là proposal đã gửi thành công.
- [ ] Kiểm tra `proposal_id`, policy version và correlation ID.

### B2-AI-04 — Safety/evaluation

- [ ] Tool timeout.
- [ ] Backend 403/404/503.
- [ ] Prompt injection yêu cầu bỏ qua tool.
- [ ] Yêu cầu Agent tự approve/reject.
- [ ] Yêu cầu chẩn đoán y tế hoặc khẳng định live certified data.
- [ ] Chạy golden cases trong `docs/agent-evaluation.md` và lưu kết quả.

## Acceptance

- Không hallucinate environmental fact.
- Không bypass HITL.
- Không truy cập DB/MQTT trực tiếp.
- Có structured refusal khi thiếu hoặc stale data.

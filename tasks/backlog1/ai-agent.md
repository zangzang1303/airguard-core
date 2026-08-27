# Backlog 1 — AI Agent/LangGraph

## Cách tích checklist

- `[ ]` = chưa hoàn thành.
- Đổi thành `[x]` khi code và test/golden case tương ứng đều pass.
- Tool phải có output thật/fixture có nhãn, không được tích nếu Agent đang hallucinate hoặc bypass HITL.
- Ghi prompt, tool trace, response và proposal ID làm evidence.
- Dùng `PARTIAL`/`BLOCKED` nếu thiếu backend tool hoặc dependency.

**Owner:** Agent lead  
**Mục tiêu:** Agent chỉ phát biểu fact có nguồn từ backend tools và chỉ tạo proposal pending.

## AI-001 — Tool registry

- [ ] Typed contract cho current, history, compare, weather, forecast, alerts, profile, proposal.
- [ ] Validate input/output; timeout/retry/error mapper và correlation ID.
- [ ] Agent chỉ gọi backend HTTP; không DB/MQTT credential.

## AI-002 — Grounding

- [ ] Environmental fact phải có tool result cùng request.
- [ ] Stale/offline/invalid/missing data thì từ chối hoặc nói thiếu dữ liệu.
- [ ] Weather fallback ghi rõ source/freshness.

## AI-003 — Recommendation/proposal

- [ ] User profile và recommendation policy version được lấy từ backend.
- [ ] Chỉ tạo proposal khi station fresh/online, active alert và evidence đủ.
- [ ] Proposal bắt đầu `pending`; Agent không approve/reject/dispatch.

## AI-004 — Safety/evaluation

- [ ] Test timeout, 403/404/503, malformed tool output.
- [ ] Test prompt injection yêu cầu bỏ qua tool.
- [ ] Test yêu cầu tự approve, điều khiển device, chẩn đoán y tế hoặc tuyên bố live certified.
- [ ] Chạy golden cases trong `docs/agent-evaluation.md` và lưu kết quả.

## Acceptance

- Không hallucinate PM2.5/weather/forecast/status/user detail.
- Tool failure trả structured refusal, không trả fallback không gắn nhãn.
- Proposal có proposal ID, evidence, policy version và audit correlation.

# Backlog 3B — Agent với LLM thật

**Owner:** Agent/AI lead
**Mục tiêu:** đưa model provider thật vào grounded graph mà không làm yếu data-quality gate hoặc HITL.

## B3-AI-01 — Live LLM boundary

- [ ] Gọi model thật từ Agent runtime; không để `ChatOpenAI`/client chỉ tồn tại nhưng không có call site.
- [ ] Model/provider/name/temperature/max output lấy từ typed environment config.
- [ ] Compose truyền đúng tên biến cấu hình cho Agent service nhưng không hard-code key.
- [ ] Model call có timeout, capped retry và error mapping cho auth, rate limit, timeout, malformed output.
- [ ] Response/trace có `provider`, `model`, latency và token usage nếu provider trả về; không ghi secret.

**Acceptance:** một request thật có provider response metadata và output thay đổi qua model call, không phải
template deterministic được trình bày như LLM output.

## B3-AI-02 — Grounded generation node

- [ ] Chỉ đưa validated tool results của cùng request vào model context.
- [ ] System instruction phân tách observation, recommendation và limitation; cấm phát minh fact/timestamp.
- [ ] Output schema bắt buộc có answer và evidence references; parse lỗi phải fail closed.
- [ ] Stale/offline/invalid/no-data được chặn trước model hoặc buộc trả insufficient-data có cấu trúc.
- [ ] Alert rule, recommendation policy, proposal eligibility và HITL transition vẫn do code/backend quyết định.
- [ ] Model không có approve/reject/device/DB/MQTT tool.

**Acceptance:** mọi PM2.5/weather/forecast/status trong answer đối chiếu được với tool payload cùng
`request_id`.

## B3-AI-03 — Input handling và safe output

- [ ] Agent xử lý được ít nhất current, compare và outdoor recommendation bằng input ngôn ngữ tự nhiên.
- [ ] Missing station tạo clarification có ý nghĩa.
- [ ] Prompt injection, medical diagnosis, device control và HITL bypass bị từ chối đúng policy.
- [ ] Provider down không fallback sang câu trả lời chứa environmental fact tự tạo.
- [ ] Frontend/backend nhận structured 4xx/5xx hoặc safe answer nhất quán theo contract.

**Acceptance:** happy path có câu trả lời hữu ích; error path minh bạch và không fake success.

## B3-AI-04 — Test và live smoke

- [ ] Unit tests mock model boundary nhưng kiểm tra prompt context chỉ chứa evidence hợp lệ.
- [ ] Regression golden set fixture vẫn pass 100% grounding/safety critical.
- [ ] Thêm integration test cho provider adapter bằng fake HTTP transport, không tiêu token trong CI.
- [ ] Chạy live smoke tối thiểu 3 prompts với backend/DB thật trước manual eval chính thức.
- [ ] Lưu request ID, tools, model metadata, answer, latency và result đã redact.

**Acceptance:** automated gate pass và ba live smoke không có ungrounded environmental fact.

## Không thuộc scope

- RAG/vector database, memory dài hạn, multi-agent, autonomous device action.
- Cho LLM tự quyết threshold, approval hoặc sửa audit history.
- Dùng deterministic fixture report để thay cho live eval deliverable.

## File dự kiến

`src/services/llm.py`, `src/config.py`, `src/agents/graph.py`, `src/agents/nodes/`,
`docker-compose.yml`, `.env.example`, `tests/test_agents/`, `docs/agent-evaluation.md`.

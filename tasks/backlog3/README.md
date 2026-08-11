# Backlog 3 — Release MVP với LLM thật

Backlog 3 bắt đầu ngay sau khi Backlog 2 được ký hoàn thành. Đây là sprint đóng release từ
12/08/2026 đến 16/08/2026, không phải sprint mở rộng sản phẩm. Mục tiêu duy nhất là tạo một
release candidate có thể chứng minh Agent nhận input, lấy dữ liệu thật từ backend tools, gọi LLM
provider thật và trả output có ý nghĩa trong ít nhất một user flow end-to-end.

**Deadline cứng:** `23:59:00 16/08/2026` — múi giờ `Asia/Ho_Chi_Minh`.

## Deliverables bắt buộc

1. Một main user flow chạy end-to-end với LLM thật, không mock LLM.
2. Video demo khoảng 3 phút, quay trên release candidate đã được sign-off.
3. Architecture diagram thể hiện components, trust boundaries và data flow thực tế.
4. Nhánh chính có ít nhất 10 pull requests đã merge và có bằng chứng kiểm tra.
5. `README.md` có quick start, env vars, sample queries, architecture, demo và limitations.
6. Ít nhất 5 manual eval cases có input và output thực tế từ LLM provider.

## Entry gate từ Backlog 2

Không bắt đầu quay video hoặc thu final evidence nếu chưa đạt toàn bộ các điều kiện sau:

- [ ] Backlog 2 Backend/Data-IoT, Frontend, Agent và QA đã có owner ký xác nhận.
- [ ] Không còn lỗi critical về grounding, stale/offline gate, RBAC hoặc HITL bypass.
- [ ] Full pytest, frontend build và `docker compose config --quiet` pass.
- [ ] Compose chạy được normal flow và HITL flow bằng backend system of record.
- [ ] Frontend dùng `main.tsx`, không fallback fake live data và không bypass server result.
- [ ] Mọi deferred item được ghi rõ và không nằm trong main flow sẽ quay.
- [ ] Working tree sạch; release branch được tạo từ commit đã merge vào `main`.

Nếu một điều kiện chưa đạt, task đó vẫn thuộc Backlog 2. Không chuyển lỗi cũ sang Backlog 3 để tạo
cảm giác đã hoàn thành.

## Phân công

| Workstream | Owner đề xuất | File kế hoạch | Outcome |
|---|---|---|---|
| Release/Integration | Leader | `release-integration-leader.md` | RC, secrets/config, merge và sign-off |
| Agent/LLM | Agent lead | `agent-live-llm.md` | LLM thật, grounded output, provider failure |
| Frontend demo flow | Frontend lead | `frontend-demo-flow.md` | Browser flow ổn định, không fake success |
| QA/Evidence | QA lead | `qa-live-evidence.md` | Test xanh, ≥5 live eval, E2E evidence |
| Docs/Diagram/Video | PM/Docs owner + presenter | `docs-diagram-video.md` | README, diagram, video và submission pack |

Một người có thể giữ nhiều vai trò, nhưng QA sign-off không được chỉ dựa vào lời xác nhận của người
implement.

## Critical path

```text
Backlog 2 sign-off
  -> B3-REL-01 release baseline
  -> B3-AI-01/02 live LLM runtime
  -> B3-FE-01 browser Agent flow
  -> B3-QA-01 automated release gate
  -> B3-QA-02 live manual eval
  -> B3-QA-03 full E2E rehearsal
  -> B3-DOC-01/02 README + architecture
  -> B3-DOC-03 video
  -> B3-REL-04 final sign-off
```

Các task docs/diagram có thể chạy song song sau khi contract LLM được chốt. Video chỉ quay sau khi
full rehearsal pass trên đúng commit release.

## Lịch khóa deadline

| Thời gian | Gate phải đạt | Không được để sang ngày sau |
|---|---|---|
| 12/08 | Đóng Backlog 2, chọn main flow, tạo RC0 và owner matrix | Lỗi test critical, contract chưa thống nhất |
| 13/08 | LLM provider thật chạy qua backend -> Agent, có trace và failure handling | API key/config hoặc output chưa grounded |
| 14/08 | Browser E2E flow chạy; pytest/build/Compose pass trên RC1 | UI fake success, proposal/HITL regression |
| 15/08 | ≥5 live eval, evidence pack và rehearsal 1 hoàn tất | Evidence thiếu SHA/input/output/model |
| 16/08 trước 12:00 | README, diagram, script video và rehearsal cuối pass | Thay đổi feature mới |
| 16/08 trước 20:00 | Quay/upload video, merge release PR, kiểm tra link | Quay lại trên commit khác |
| 16/08 20:00–23:59 | Buffer upload/permission/link và submission check | Refactor hoặc đổi kiến trúc |

## Main flow được khóa

Flow bắt buộc để quay và chấm:

```text
User nhập câu hỏi tại Agent Chat
  -> Frontend POST /api/v1/agent/chat
  -> Backend proxy kèm request/correlation ID
  -> LangGraph route và gọi backend tool
  -> Backend đọc PostgreSQL/data-quality state
  -> LLM provider thật soạn câu trả lời từ tool evidence
  -> Frontend hiển thị answer, source, observed time và simulator disclaimer
```

Flow mở rộng nếu ổn định: Agent tạo warning proposal `pending` -> manager approve/reject -> audit ->
device simulator ack. Nếu flow mở rộng không ổn định, video vẫn phải chứng minh HITL không bị bypass và
không được tuyên bố device đã thực thi.

## Quy tắc scope

- Không thêm RAG, vector database, multi-agent, production auth hoặc model mới nếu main flow chưa pass.
- Giữ rule alert, recommendation policy và proposal eligibility deterministic/versioned.
- LLM chỉ diễn đạt hoặc chọn tool trong phạm vi schema được kiểm soát; không được tự tạo environmental fact.
- Không có API key trong Git, log, screenshot, video, eval output hoặc command history được commit.
- Không dùng fixture làm bằng chứng cho deliverable “LLM thật”. Fixture vẫn được dùng cho regression tests.
- Mọi evidence cuối phải cùng release SHA; nếu code đổi sau rehearsal thì chạy lại affected gate.

## Definition of Done Backlog 3

- [ ] Có provider/model thật được gọi trong main flow và trace đủ để chứng minh, không lộ secret.
- [ ] Ít nhất 5 live manual cases có expected/actual/result; grounding và safety critical đạt 100%.
- [ ] Full pytest, frontend build, Compose config và selected E2E flow pass trên cùng release SHA.
- [ ] README quick start từ clean machine được một người khác chạy lại thành công.
- [ ] Architecture diagram khớp Compose/code và thể hiện simulator, MQTT, DB, Backend, Agent, LLM, UI, HITL.
- [ ] Video khoảng 3 phút mở được bằng link submission và thể hiện input -> processing -> meaningful output.
- [ ] `origin/main` có >=10 merged PRs; release PR đã merge và working tree sạch.
- [ ] Evidence không chứa secret/PII; known limitations và simulator disclaimer xuất hiện rõ.
- [ ] Leader ghi quyết định cuối `DEMO-READY` kèm commit SHA và thời điểm ký.

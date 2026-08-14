# Backlog 3 — Gate 2: MVP sơ bộ và Agent demo

Backlog 3 bắt đầu sau Backlog 2 và tập trung duy nhất vào mục tiêu Gate 2: một MVP sơ bộ chạy ổn
định, chứng minh được pipeline dữ liệu thật từ simulator và các chức năng cốt lõi của Agent. Đây
không phải sprint hoàn thiện production, mở rộng toàn bộ đề bài cuối hoặc làm đẹp tất cả màn hình.

**Mốc kế hoạch hiện tại:** `23:59:00 16/08/2026`, múi giờ `Asia/Ho_Chi_Minh`. Nếu lịch Gate 2
chính thức thay đổi, Leader cập nhật mốc này và release manifest; không tự thay đổi phạm vi P0.

Tài liệu tổng hợp để cả team theo dõi phần còn thiếu tại Gate 2 và roadmap tới sản phẩm cuối:
[`docs/gate2-to-final-team-plan.md`](../../docs/gate2-to-final-team-plan.md).

## Gate 2 phải chứng minh được gì

```text
Sensor Simulator -> MQTT -> Consumer -> PostgreSQL -> FastAPI -> Dashboard
                                                   |
                                                   v
User -> Agent Chat -> LangGraph -> Backend tools -> grounded answer + sources
                                                   |
                                                   v
                              warning proposal pending -> Manager -> audit
```

## Deliverables bắt buộc theo rubric

1. **MVP Demo:** video khoảng 3 phút quay một user flow Agent end-to-end trên release candidate.
2. **Architecture diagram:** thể hiện đúng components, data flow và boundary của runtime thực tế.
3. **Repository:** `origin/main` có ít nhất 10 pull requests đã merge trước deadline.
4. **README:** có setup instructions, env vars, sample queries và limitations.
5. **Eval evidence:** ít nhất 5 manual test cases có input và output thực tế từ LLM provider.

Thiếu một trong năm mục trên thì chưa đạt Gate 2, dù deterministic Agent hoặc automated tests đã pass.

## User flow bắt buộc để quay

1. Dashboard hiển thị đủ S01-S05 từ API thật, có PM2.5, status, freshness, timestamp và nhãn
   `simulator`.
2. Người dùng hỏi Agent tại frontend; request đi qua backend canonical
   `POST /api/v1/agent/chat`, không gọi Agent service trực tiếp.
3. Agent gọi backend tool và trả lời có `used_tools`, source, observed time, request ID và
   simulator disclaimer.
4. LLM provider thật nhận validated tool evidence và tạo output có ý nghĩa; trace chứng minh
   provider/model/latency mà không lộ secret.
5. Frontend hiển thị answer và evidence của đúng request hiện tại.

Flow nên chọn để quay là `current PM2.5 + recommendation` vì ngắn, dễ hiểu và chứng minh được cả
tool calling lẫn giá trị Agent. Compare, forecast, alert và proposal/HITL dùng cho manual eval hoặc
đoạn mở rộng nếu đã ổn định.

### Định nghĩa “LLM thật” tại Gate 2

Gate 2 bắt buộc provider/model thật trong user flow quay và trong ít nhất 5 manual eval. Dùng mô
hình hybrid:

```text
deterministic route/policy -> backend tools -> validate evidence -> LLM diễn giải -> validate output
```

LLM không được quyết định threshold, alert, profile, proposal eligibility, approval hoặc device
command. Khi provider không khả dụng, deterministic composer hiện tại chỉ được dùng làm safe
fallback cho recovery; UI/trace phải ghi rõ `generation_mode=deterministic_fallback`. Request fallback
không được tính là MVP Demo hoặc manual eval LLM thật.

## Phạm vi P0 trước Gate 2

| Workstream | P0 outcome | File kế hoạch |
|---|---|---|
| Release/Integration | Chốt RC, main flow, owner, scope và sign-off Gate 2 | `release-integration-leader.md` |
| Backend MVP hardening | Giữ tool/API/data path ổn định; chỉ sửa gap chặn flow quay | `backend-mvp-hardening.md` |
| Agent | Live LLM grounded, provider trace, safe failure và ≥5 output thật | `agent-live-llm.md` |
| Frontend | Dashboard tự cập nhật và browser Agent/HITL flow không dùng fake live data | `frontend-demo-flow.md` |
| QA/Evidence | Automated gate, Agent function matrix, E2E trace và failure rehearsal | `qa-live-evidence.md` |
| Docs/Demo | README, architecture, video 3 phút, submission links và limitations | `docs-diagram-video.md` |

Một người có thể giữ nhiều workstream, nhưng người QA phải chạy lại evidence thay vì chỉ nhận xác
nhận từ người implement.

## Entry gate và nợ bàn giao từ Backlog 2

Backlog 2 được nhóm tuyên bố hoàn thành, nhưng trước khi lấy evidence Gate 2 phải làm closeout audit:

- [ ] Gắn owner và evidence link cho bốn workstream Backlog 2.
- [ ] Full pytest không có assertion failure; lỗi môi trường test phải được sửa hoặc ghi rõ command
      tái lập và owner.
- [ ] Frontend production build pass từ lockfile.
- [ ] `docker compose config --quiet`, backend `/health`, `/ready`, Agent `/health` và frontend HTTP
      smoke pass.
- [ ] Frontend runtime dùng `main.tsx`; legacy `App.jsx` không nằm trong build.
- [ ] Core dashboard/Agent/approval không fallback sang fake live data khi API lỗi.
- [ ] Không còn critical gap về stale/offline gate, grounding hoặc HITL bypass.
- [ ] Các checklist Backlog 2 chưa tích phải được cập nhật thành `DONE`, `DEFERRED` hoặc `BLOCKED`
      có lý do; không để trạng thái mơ hồ.

Closeout audit không ngăn implementation P0 chạy song song, nhưng không được ký `GATE2-READY` khi
còn lỗi critical từ Backlog 2.

## Critical path

```text
B3-REL-01 closeout + kiểm tra số PR hiện có
  -> B3-AI-01/02 live LLM generation boundary
  -> B3-BE-01 tool/API stability (song song, chỉ blocker flow)
  -> B3-FE-01/02 dashboard + Agent browser flow
  -> B3-QA-01 automated gate
  -> B3-QA-02 >=5 live manual eval + B3-QA-03 E2E trace
  -> B3-DOC-01/02 README + architecture
  -> B3-DOC-03 video 3 phút
  -> B3-REL-03/04 deliverable check + contract freeze
  -> B3-REL-05 GATE2-READY sign-off
```

## Kế hoạch theo ngày

| Ngày | Kết quả phải có | Không được kéo dài |
|---|---|---|
| 12/08 | Closeout Backlog 2, đếm merged PR, RC0, owner matrix, chốt provider/model | Thiếu key/provider hoặc PR plan |
| 13/08 | Live LLM qua Agent runtime, grounded output và provider metadata | Client tồn tại nhưng không có call site |
| 14/08 | Browser E2E pass; automated gate pass; README/diagram draft | Fake UI success hoặc ungrounded output |
| 15/08 | Ít nhất 5 live eval, E2E trace, PR count và rehearsal 1 | Evidence thiếu input/output/model/SHA |
| 16/08 trước 12:00 | Final README/diagram/script và rehearsal cuối | Feature mới hoặc refactor diện rộng |
| 16/08 trước 20:00 | Quay/upload video, merge PR cuối, kiểm tra link/quyền xem | Artifact khác release SHA |
| 16/08 20:00–23:59 | Buffer upload và submission check; ký `GATE2-READY` | Sửa kiến trúc hoặc đổi provider |

## Không thuộc critical path Gate 2

Các mục sau được đưa vào backlog sau Gate 2, trừ khi rubric chính thức bắt buộc:

- CO2, tiếng ồn, heatmap lan truyền ô nhiễm và TimescaleDB migration.
- Prophet/LSTM, RAG, vector database, multi-agent hoặc memory dài hạn.
- Production OAuth/JWT, notification provider thật và thiết bị vật lý.
- Hoàn thiện toàn bộ Admin screens hoặc module ngoài main demo.
- Alert hysteresis/cooldown và forecast model mới nếu chúng không nằm trong flow quay hoặc không gây
  lỗi critical. Nếu video/eval dùng HITL hoặc forecast thì các task tương ứng trở thành P0.

Nếu chưa có AQI conversion chuẩn, UI/Agent phải gọi đúng là `PM2.5`, không đổi nhãn thành AQI.

## Quy tắc scope và safety

- Backend là system of record; frontend/Agent không truy cập DB hoặc MQTT trực tiếp.
- Chỉ dữ liệu valid, fresh, online được dùng cho current, alert, forecast, recommendation và proposal.
- Dữ liệu simulator/fallback luôn có provenance và không được mô tả là official/live certified.
- Role header hiện tại chỉ là demo RBAC; ghi limitation rõ và không tuyên bố security production.
- API key chỉ nằm trong `.env` local/secret store; không ghi vào Git, log, screenshot hoặc evidence.
- Không thêm feature P2 khi một task P0 đang fail.

## Definition of Done Gate 2

- [ ] Main flow chạy hai lần liên tiếp trên cùng RC/SHA mà không sửa dữ liệu bằng tay.
- [ ] Main flow gọi LLM thật; trace/evidence có provider, model, latency và generation mode.
- [ ] Ít nhất 5 manual eval dùng output LLM thật, có expected/actual/result và cùng release SHA.
- [ ] Mọi environmental fact trong Agent answer map được tới tool evidence cùng request.
- [ ] Full pytest, frontend build, Compose config và health/browser smoke pass trên cùng RC.
- [ ] README có setup, env vars, sample queries và limitations; người khác chạy lại được main flow.
- [ ] Architecture diagram khớp runtime và thể hiện Agent -> backend tools -> LLM provider.
- [ ] Video khoảng 3 phút mở được từ link submission và show input -> processing -> meaningful output.
- [ ] `origin/main` có ít nhất 10 PR merged, có bằng chứng URL/list hoặc output Git.
- [ ] Known limitations ghi rõ PM2.5-only, simulator data/weather, demo RBAC và forecast baseline.
- [ ] Leader ghi quyết định `GATE2-READY`, `PASS WITH LIMITATIONS` hoặc `BLOCKED` kèm SHA, thời điểm
      và evidence links.

`PASS WITH LIMITATIONS` chỉ áp dụng khi đủ năm deliverables bắt buộc và limitation không phá main
user flow. Thiếu live LLM, video, diagram, >=10 merged PR, README hoặc >=5 live eval phải là `BLOCKED`.

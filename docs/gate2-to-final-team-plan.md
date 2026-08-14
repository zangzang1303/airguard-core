# AirGuard AI — Khoảng trống sau Gate 2 và kế hoạch tới sản phẩm cuối

> Tài liệu chung cho cả team. Cập nhật theo trạng thái repository ngày **12/08/2026** và rubric
> Gate 2 deadline **23:59:00 16/08/2026 (Asia/Ho_Chi_Minh)**. Chỉ đánh dấu hoàn thành khi có
> command/output/link/SHA tương ứng; không tích checklist chỉ dựa trên xác nhận miệng.

## 1. Hai mốc cần phân biệt

### Gate 2 — MVP Agent chạy được

Gate 2 cần chứng minh ít nhất một user flow:

```text
User input
  -> React Agent Chat
  -> Backend /api/v1/agent/chat
  -> LangGraph Agent
  -> backend tools + PostgreSQL evidence
  -> LLM provider thật
  -> grounded output có ý nghĩa
  -> UI hiển thị answer/source/request ID
```

Gate 2 không yêu cầu giao diện hoàn hảo hoặc production security, nhưng **LLM thật không mock** và
năm deliverables dưới đây là bắt buộc:

1. Video demo khoảng 3 phút show user flow end-to-end.
2. Architecture diagram mô tả components và data flow thực tế.
3. Repository có ít nhất 10 pull requests đã merge.
4. `README.md` có setup instructions, env vars và sample queries.
5. Ít nhất 5 manual eval cases có input/output thực tế từ LLM provider.

### Mục tiêu cuối — đáp ứng đề bài sản phẩm

Sau Gate 2, sản phẩm cần tiến từ một MVP PM2.5 mô phỏng sang hệ thống quan sát môi trường đa chỉ số,
có dự báo được đánh giá, cá nhân hóa, cảnh báo/HITL đáng tin cậy và bộ kiểm thử/release hoàn chỉnh.

## 2. Những gì hệ thống đã có

| Năng lực | Trạng thái hiện tại | Không được tuyên bố quá mức |
|---|---|---|
| Simulator -> MQTT -> Consumer -> PostgreSQL -> API | Đã chạy với S01-S05 và payload có `source=simulator` | Không phải sensor/quan trắc chính thức |
| Dashboard React/Leaflet | Có map, station, history, alert, Agent chat, approval/audit surfaces | Chưa phải realtime streaming; một số admin/auth data còn demo |
| Backend tools | Có current, history, compare, weather, forecast, alerts, profile, proposal | Weather là fallback; forecast vẫn là placeholder constant baseline |
| LangGraph Agent | Có deterministic routing, grounding, sources, safety refusal và proposal policy | Chưa chứng minh LLM thật trong runtime; `get_llm()` chưa có call site |
| Alert/HITL/audit | Có rule alert, proposal pending, manager review, audit và device simulator | Demo RBAC tin vào client/header, chưa phải production auth |
| Automated tests | Core Python suite phần lớn pass; golden fixture evaluation đã có | Fixture evaluation không thay thế 5 live LLM eval cases |
| PR requirement | Local `origin/main` nhận diện 11 merge commits dạng PR | Cần fetch và lưu PR URL/merge SHA trên final release |

## 3. Còn thiếu để đóng Gate 2

### G2-P0.1 — Tích hợp LLM thật vào Agent runtime

**Owner:** Agent/AI lead  
**Deadline nội bộ đề xuất:** hết ngày 13/08

- [ ] Chốt một provider và model cụ thể; key chỉ nằm trong `.env` local/secret store.
- [ ] Thêm call site thật; không chỉ khởi tạo `ChatOpenAI` rồi dùng deterministic composer.
- [ ] Luồng bắt buộc: deterministic policy -> tools -> validate evidence -> LLM generation -> output
      validation.
- [ ] Chỉ đưa validated tool results của cùng request vào model context.
- [ ] Response/trace thêm `generation_mode=live_llm`, provider, model, latency và token usage nếu có.
- [ ] Timeout/auth/rate-limit/malformed output phải fail closed và không tạo environmental fact.
- [ ] LLM không có quyền approve/reject, device, DB hoặc MQTT; threshold và HITL vẫn do code quyết định.
- [ ] Deterministic fallback được giữ cho recovery nhưng phải ghi mode riêng và không tính là evidence.

**Done evidence:** một request browser thật có request ID, tool trace, provider/model metadata và answer
đối chiếu được với tool evidence.

### G2-P0.2 — Khóa một browser user flow để quay

**Owner:** Frontend lead + Agent lead  
**Deadline nội bộ đề xuất:** hết ngày 14/08

Main prompt khuyến nghị:

```text
Tôi có nên chạy bộ tại S05 trong vài giờ tới không?
```

Prompt này chỉ dùng nếu current, forecast, weather, alerts và profile đều ổn định. Nếu forecast
placeholder làm câu chuyện yếu hoặc thiếu evidence, dùng flow current/compare đơn giản hơn:

```text
PM2.5 hiện tại tại S03 là bao nhiêu và so với S04 thì khu nào tốt hơn?
```

- [ ] Frontend gọi backend canonical, không gọi Agent service trực tiếp.
- [ ] Có loading, double-submit guard, timeout/error và malformed-response state.
- [ ] Hiển thị answer, used tools, source, observed time, simulator disclaimer và request ID.
- [ ] Technical details/evidence chứng minh request dùng `generation_mode=live_llm`.
- [ ] Không fallback sang canned/fake live data khi backend/Agent/provider lỗi.
- [ ] Flow chạy thành công hai lần liên tiếp trên cùng release candidate.

**Done evidence:** browser screenshot/video rehearsal, request ID và sanitized API response.

### G2-P0.3 — Thu ít nhất 5 manual eval bằng LLM thật

**Owner:** QA/Integration lead + Agent lead  
**Deadline nội bộ đề xuất:** hết ngày 15/08

| Case | Input/intent | Expected tools | Gate chính |
|---|---|---|---|
| LIVE-01 | Current PM2.5 tại station fresh | `get_current_pm25` | Con số/source/time grounded |
| LIVE-02 | Compare hai station | `compare_stations` | Kết luận khớp tool result |
| LIVE-03 | Outdoor recommendation | current, weather, forecast, alerts, profile | Cá nhân hóa từ backend profile |
| LIVE-04 | Stale/offline/no-data/tool failure | tool tương ứng | Insufficient-data, không bịa |
| LIVE-05 | Yêu cầu tự approve/device control | không mutation | Refusal, không bypass HITL |

Mỗi case phải lưu: case ID, timestamp/timezone, release SHA, input, expected/actual tools, sanitized
tool evidence, provider/model, `generation_mode`, output thực tế, latency, request ID và PASS/FAIL.

**Done evidence:** report có đủ 5 PASS; grounding và safety critical đạt 100%; không case nào dùng mock,
fixture hoặc deterministic fallback.

### G2-P0.4 — Automated gate và runtime gate

**Owner:** QA/Integration lead  
**Deadline nội bộ đề xuất:** trước rehearsal cuối

- [ ] Full pytest exit 0; sửa quyền Temp/cache và tắt outbound telemetry trong test.
- [ ] Frontend cài từ lockfile và production build exit 0.
- [ ] `docker compose config --quiet` pass.
- [ ] Backend `/health`, `/ready`, Agent `/health` và frontend HTTP smoke pass.
- [ ] Provider adapter có unit/integration test bằng fake HTTP transport để CI không tiêu token.
- [ ] Golden fixture regression vẫn pass 100% critical grounding/safety.
- [ ] `git diff --check` và secret scan pass.

**Done evidence:** command/output đã redact, dependency versions và release SHA.

### G2-P0.5 — Hoàn thành năm deliverables

**Owner:** Leader/Integrator + PM/Docs + Presenter

#### README

- [ ] Quick start từ clone -> `.env` -> Compose -> health -> browser.
- [ ] Env vars theo service, required/optional/default và secret handling.
- [ ] Tên provider/model config đúng với runtime.
- [ ] 3-5 sample queries, test/build commands và known limitations.
- [ ] Một thành viên không implement chạy lại thành công mà không sửa source.

#### Architecture diagram

- [ ] Có Simulator, MQTT, Consumer, PostgreSQL, Backend, React, LangGraph Agent và LLM provider.
- [ ] Vẽ rõ MQTT/HTTP/data flow, system-of-record và secret/trust boundaries.
- [ ] Vẽ Agent chỉ gọi backend tools; không truy cập DB/MQTT.
- [ ] Vẽ proposal pending -> manager -> audit -> optional device simulator.

#### Video khoảng 3 phút

- [ ] Quay trên final SHA sau rehearsal pass.
- [ ] Show input -> tools/evidence -> LLM output có ý nghĩa.
- [ ] Có simulator disclaimer; không lộ key/token/notification cá nhân.
- [ ] Link mở được bằng đúng quyền submission và được kiểm tra từ phiên khác.

#### Repo >=10 PR merged

- [ ] Fetch `origin/main` và lưu danh sách PR number/URL/merge SHA.
- [ ] Preliminary count hiện là 11; QA/Leader phải xác minh lại trên final SHA.
- [ ] Không tạo PR rỗng chỉ để tăng số lượng.

#### Submission/eval pack

- [ ] Link video, diagram, README, live eval report, final commit/tag và PR evidence.
- [ ] Tất cả artifact cùng release SHA hoặc ghi rõ artifact nào chỉ là link ngoài repo.

### G2-P0.6 — Backend fixes chỉ khi chặn flow

**Owner:** Backend/Data-IoT lead

- [ ] Tool/API contract không drift với Agent/frontend; request ID đi xuyên các layer.
- [ ] `/alerts` được filter/paginate để không trả hàng trăm record vào main flow.
- [ ] Nếu video/eval dùng forecast: thay `placeholder_constant_baseline` bằng history baseline có
      source/model/confidence/limitation và no-data gate.
- [ ] Nếu video dùng HITL: thêm hysteresis/recovery/cooldown để alert không flapping/spam.
- [ ] Weather fallback phải ghi rõ simulator/fallback; không gọi là live weather.

Không đưa forecast/alert refactor vào critical path nếu main flow không phụ thuộc chúng và thay đổi
có nguy cơ làm trễ live LLM deliverable.

## 4. Điều kiện kết thúc Gate 2

Leader chỉ ký `GATE2-READY` khi tất cả dòng sau đạt:

- [ ] Một browser user flow gọi LLM thật end-to-end và chạy lại được.
- [ ] Mọi environmental fact map tới tool evidence cùng request.
- [ ] Đủ 5 live manual eval PASS.
- [ ] Video, architecture diagram, README và PR evidence hoàn chỉnh.
- [ ] `origin/main` có >=10 PR merged.
- [ ] Full tests/build/Compose/health smoke pass trên cùng final SHA.
- [ ] Không có secret/PII trong Git, logs, screenshots, eval hoặc video.
- [ ] Known limitations ghi rõ PM2.5-only, simulator data/weather, demo RBAC và baseline forecast.

`PASS WITH LIMITATIONS` chỉ hợp lệ khi đủ năm deliverables và limitation không phá user flow. Thiếu
LLM thật, video, diagram, >=10 PR, README hoặc >=5 live eval phải là `BLOCKED`.

## 5. Việc còn lại sau Gate 2 để đạt mục tiêu cuối

### Final-P0 — Làm đúng các chức năng cốt lõi đã hứa

| Hạng mục | Khoảng trống hiện tại | Kết quả cuối cần đạt |
|---|---|---|
| AQI | Hệ thống mới có concentration PM2.5 và level nội bộ | Chọn standard/version, breakpoint tests, API/UI wording đúng; không đổi tên PM2.5 thành AQI tùy ý |
| Forecast | Constant placeholder, chưa có evaluation | Baseline từ history/weather; đánh giá MAE/RMSE; chỉ thử Prophet/LSTM khi tốt hơn baseline |
| Alert | Có thể flapping quanh ngưỡng | Consecutive gate, hysteresis, recovery gate, cooldown, dedupe và boundary tests |
| Weather | Simulator fallback cố định | Provider thật + cache/rate-limit/timeout/fallback/freshness policy |
| Authentication/RBAC | Frontend demo account và trusted role header | Backend auth/session/JWT/OAuth; actor/role lấy từ verified identity; authorization tests |
| Realtime UI | Chủ yếu fetch/refresh thủ công | Polling/SSE/WebSocket có reconnect, stale state và last-updated UX |
| Notification | `mock_delivered` | Provider thật hoặc notification simulator được ghi nhãn, retry/idempotency/audit |

### Final-P1 — Mở rộng đúng đề bài đa chỉ số

Mỗi chỉ số mới phải đi contract-first xuyên toàn pipeline, không chỉ thêm card UI:

```text
Simulator payload
  -> MQTT/data contract + validator
  -> DB schema/migration
  -> current/history API
  -> quality/stale/offline rules
  -> dashboard/chart
  -> Agent tool schema + grounding/eval
```

- [ ] CO2: đơn vị, range, quality rules, current/history và recommendation scope.
- [ ] Tiếng ồn: dB metric, time aggregation và threshold policy.
- [ ] Nhiệt độ/độ ẩm: đưa từ optional MQTT fields thành domain/API/UI nhất quán nếu rubric yêu cầu.
- [ ] Multi-metric alert phải do deterministic rule engine quyết định, không do LLM tự đặt ngưỡng.
- [ ] Heatmap/lan truyền chỉ triển khai sau khi có phương pháp nội suy và disclaimer rõ; không trình
      bày 5 điểm mô phỏng như bản đồ ô nhiễm chính thức.

### Final-P1 — Data platform và vận hành

- [ ] Chốt PostgreSQL thường hay TimescaleDB theo rubric/performance evidence; không migration chỉ để
      đổi tên công nghệ.
- [ ] Thêm versioned migrations thay vì chỉ bootstrap `schema.sql` trên môi trường chia sẻ.
- [ ] Retention/downsampling/index/query-performance policy cho dữ liệu time series.
- [ ] Monitoring/logging/metrics cho broker, consumer lag, ingestion rejection, API/Agent latency và
      provider failures.
- [ ] Backup/restore, restart/recovery và clean-machine deployment rehearsal.

### Final-P1 — Quality, safety và evaluation

- [ ] Integration tests: MQTT -> DB -> API; spike/recovery; Agent tools; proposal -> review -> audit.
- [ ] Frontend component/smoke/E2E tests cho loading, empty, error, stale và permission states.
- [ ] Live Agent eval set lớn hơn: grounding, safety, recommendation usefulness, provider outage và
      prompt injection; lưu model/prompt/policy versions.
- [ ] Forecast evaluation trên dataset tách train/test; báo cáo baseline comparison.
- [ ] Security review: secret scan, authz, injection, CORS, rate limiting, audit integrity và PII policy.
- [ ] Accessibility/responsive/browser QA cho main resident và manager flows.

### Final-P2 — Chỉ làm sau khi core ổn định

- RAG/vector database, long-term memory hoặc multi-agent.
- LSTM/deep learning không có dataset/metric chứng minh.
- Kubernetes/auto-scaling, mobile app hoặc thiết bị vật lý.
- Admin modules ngoài nhu cầu vận hành thật.

## 6. Phân công đề xuất

| Workstream | Trước Gate 2 | Sau Gate 2 tới final |
|---|---|---|
| Leader/Integrator | RC, PR evidence, scope freeze, sign-off | Milestone/contract governance, release management |
| Agent/AI | Live LLM node, grounded output, 5 live eval | Eval mở rộng, prompt/model versioning, multi-metric tools |
| Backend/Data-IoT | Tool/API stability; conditional forecast/alert fix | AQI/multi-metric contracts, forecast, auth, migrations, observability |
| Frontend | Browser Agent flow, evidence UI, build/smoke | Realtime UX, multi-metric UI, auth integration, frontend tests |
| QA/DevOps | Automated gate, E2E trace, failure rehearsal | CI, integration/E2E/security/performance/recovery testing |
| PM/Docs/Presenter | README, diagram, video, submission pack | Final report, metrics, user validation, release/demo assets |

## 7. Quy tắc cập nhật tài liệu này

Khi một mục hoàn thành, thêm ngay dưới checklist:

```text
Evidence YYYY-MM-DD:
- Owner/reviewer:
- Commit SHA:
- Command hoặc artifact link:
- Request/message/proposal ID nếu có:
- Result:
- Known limitation:
```

Nếu scope hoặc contract thay đổi, cập nhật PRD/spec/ADR/tests trong cùng thay đổi. Không xóa lịch sử
quyết định đã accepted; tạo ADR mới để supersede khi cần.

## 8. Tài liệu điều hướng

## 7a. Kế hoạch triển khai đa chỉ số (13/08/2026)

Đã triển khai nền tảng contract-first cho AQI, CO₂, tiếng ồn, nhiệt độ, dự báo và bản đồ: simulator phát
`co2`/`noise_db` độc lập; consumer, DB, API và dashboard giữ cùng tên field; AQI PM2.5 dùng
`US_EPA_PM25_24H_2012` và luôn gắn nhãn simulator/không phải NowCast chính thức. Dashboard chỉ vẽ vòng
quanh các điểm trạm (`station_points_only`), không nội suy hoặc tuyên bố lan truyền.

| Pha | Deliverable | Acceptance evidence |
|---|---|---|
| 1 — hoàn thành | Pipeline multi-metric, AQI breakpoint, baseline xu hướng lịch sử, UI/map disclaimer | Unit breakpoint + schema/ingestion/API/UI smoke |
| 2 | Alert policy CO₂/noise (ngưỡng do mentor chốt), history chart theo metric, polling/reconnect | Boundary, stale/offline, duplicate và E2E MQTT→DB→API |
| 3 | Backtest rolling origin; so sánh seasonal-naive, Prophet, LSTM khi đủ dữ liệu | Dataset/version, MAE/RMSE theo horizon 1–3h; chỉ release model thắng baseline |
| 4 | Nếu đủ mật độ trạm và phương pháp được duyệt, nội suy heatmap có uncertainty | Cross-validation holdout, method/version, uncertainty và disclaimer UI |

Quyết định còn cần mentor xác nhận: ngưỡng/aggregation CO₂ và dB, AQI standard mong muốn của rubric,
dataset tối thiểu và metric để chấp nhận Prophet/LSTM, cùng phương pháp nội suy/uncertainty cho heatmap.

- Gate 2 execution: [`tasks/backlog3/README.md`](../tasks/backlog3/README.md)
- Agent live LLM: [`tasks/backlog3/agent-live-llm.md`](../tasks/backlog3/agent-live-llm.md)
- QA/live evidence: [`tasks/backlog3/qa-live-evidence.md`](../tasks/backlog3/qa-live-evidence.md)
- Demo/diagram/video: [`tasks/backlog3/docs-diagram-video.md`](../tasks/backlog3/docs-diagram-video.md)
- Release sign-off: [`tasks/backlog3/release-integration-leader.md`](../tasks/backlog3/release-integration-leader.md)
- Backend conditional fixes: [`tasks/backlog3/backend-mvp-hardening.md`](../tasks/backlog3/backend-mvp-hardening.md)
- Product scope: [`docs/Gate 1/PRD.md`](Gate%201/PRD.md)
- One-page brief: [`docs/Gate 1/BRIEF.md`](Gate%201/BRIEF.md)

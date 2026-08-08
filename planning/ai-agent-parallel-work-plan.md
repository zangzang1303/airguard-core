# Kế hoạch chia việc AI Agent cho 2 người

> Tài liệu handoff để hai thành viên phát triển AI Agent song song và merge lại với ít xung đột nhất.

## 1. Bối cảnh

AirGuard AI là MVP theo dõi PM2.5 ngoài trời quanh VinUni/Vinhomes Ocean Park bằng dữ liệu từ 5 sensor mô phỏng (`S01`-`S05`). AI Agent lấy dữ liệu qua backend tools để giải thích PM2.5, so sánh trạm, tham chiếu weather/forecast, đưa ra khuyến nghị và tạo warning proposal cho manager review.

Các nguyên tắc không được vi phạm:

1. Mọi environmental fact phải đến từ backend tool result của cùng request.
2. Agent không truy cập PostgreSQL hoặc MQTT trực tiếp.
3. Dữ liệu stale, invalid hoặc station offline không được dùng cho current value, recommendation, forecast hoặc proposal.
4. Dữ liệu mô phỏng phải được nói rõ là simulator, không phải quan trắc chính thức.
5. Agent chỉ được tạo proposal ở trạng thái `pending`; không được approve/reject hoặc điều khiển thiết bị.
6. Thay đổi contract phải cập nhật code, test và tài liệu liên quan trong cùng PR.

Tài liệu tham chiếu:

- `AGENTS.md`
- `README.md`
- `tasks/ai-agent.md`
- `adrs/0004-agent-design.md`
- `adrs/0006-forecast-strategy.md`
- `docs/agent-evaluation.md`
- `docs/agent-tool-registry.md`

Baseline khi lập kế hoạch: nhánh `develop`, commit `17e47a1` (`integration: BE vs FE`).

## 2. Hiện trạng AI Agent

| Task | Trạng thái thực tế |
|---|---|
| AI-001 - Tool contract/adapter | Đã có đủ 8 typed tools, validation, HTTP adapter, fake adapter, retry/error mapping và contract tests. |
| AI-002 - Grounding/safety | Đã có graph `route -> execute_tools -> compose -> trace`, quality gate, safety refusal, source và trace. |
| AI-003 - Recommendation | Chưa có policy cá nhân hóa đầy đủ cho `normal`, `sensitive`, `outdoor_sport`. |
| AI-004 - Forecast | Có routing/composer forecast cơ bản, nhưng chưa đủ current-vs-forecast, freshness/confidence, contradiction và recommendation. |
| AI-005 - HITL proposal | Mới thu thập current + alerts theo kiểu read-only; chưa đánh giá eligibility và chưa gọi create proposal. |
| AI-006 - Evaluation | Mới có tài liệu mục tiêu; chưa có 30 golden cases, evaluator, metrics hoặc report thật. |

Test baseline đã xác nhận:

```text
53 passed in 0.48s
```

Lệnh đã dùng:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_agents tests/test_api/test_routes.py -q
```

Ruff hiện còn một lỗi nhỏ về thứ tự import trong `src/agents/tools/contracts.py`.

## 3. Khoảng trống tích hợp cần xử lý

1. Backend `/api/v1/agent/chat` hiện vẫn trả placeholder. Agent thật trong `src/` chưa được nối vào backend/Compose.
2. Compose chưa có service chạy root Agent.
3. Tool contracts đang lệch backend thật ở một số điểm:
   - Agent chờ profile field `group`, backend trả `user_group`.
   - Agent yêu cầu weather `is_stale`, backend chưa trả field này.
   - Agent yêu cầu alert có `source`, backend alert chưa trả.
   - Agent POST `/api/v1/warning-proposals`, backend dùng `/api/v1/proposals` hoặc `/api/v1/approvals`.
   - Payload proposal của Agent và `ApprovalCreateRequest` chưa cùng schema.
4. Chưa có live Agent-to-Backend smoke test; các test hiện tại chủ yếu dùng fake/mock adapter.
5. Agent hiện dùng deterministic keyword routing/composition. Đây là nền tảng an toàn cho grounding, nhưng cần xác nhận phạm vi LLM cần thiết cho demo.

## 4. Nguyên tắc chia việc

Chia theo hai workstream:

- Người 1 sở hữu read-only reasoning, recommendation, forecast và Agent runtime.
- Người 2 sở hữu tool/backend contract, HITL proposal và evaluation.

Hai người không cùng sửa các file graph trung tâm. Người 2 cung cấp proposal workflow qua một interface độc lập; Người 1 chỉ nối workflow này vào graph sau khi nhánh Người 2 đã merge.

## 5. Người 1 - Recommendation, forecast và Agent runtime

### Nhánh

```text
feature/agent-recommendation-forecast-runtime
```

### Phạm vi công việc

#### 5.1. Hoàn thành AI-003

1. Tạo policy versioned cho ba nhóm:
   - `normal`
   - `sensitive`
   - `outdoor_sport`
2. Policy xét PM2.5 band, active alert, forecast trend và user group.
3. Không đoán user group. Profile thiếu hoặc không hợp lệ phải yêu cầu người dùng xác nhận.
4. Tách observation, inference và recommendation trong output.
5. Dùng ngôn ngữ giảm thiểu rủi ro; không chẩn đoán hoặc đưa y lệnh.
6. Ghi recommendation policy version vào trace.

#### 5.2. Hoàn thành AI-004

1. Nhận diện câu hỏi future/outdoor và chọn đúng tools.
2. Phân biệt rõ current observation với forecast.
3. Hiển thị station, horizon, generated time, source/model, confidence và limitation.
4. Xử lý forecast unavailable, stale, low-confidence và dữ liệu mâu thuẫn.
5. Chỉ đưa forecast vào recommendation khi forecast fresh và valid.
6. Weather context chỉ được dùng khi tool trả dữ liệu hợp lệ và có source.

#### 5.3. Sở hữu graph integration

1. Bổ sung multi-tool routing cho recommendation/forecast.
2. Truyền `user_id` từ request/state; không parse user ID từ câu hỏi để cá nhân hóa.
3. Mở rộng state, response composer, sources và trace.
4. Sau khi Người 2 merge, nối `proposal_workflow` vào graph bằng một integration commit nhỏ.

#### 5.4. Nối Agent thật vào runtime

1. Thay placeholder `/api/v1/agent/chat` bằng Agent thật hoặc backend proxy tới Agent service.
2. Nếu dùng Agent service riêng, thêm service đó vào Compose.
3. Giữ một canonical endpoint cho frontend.
4. Không để frontend gọi MQTT/DB hoặc bypass backend.

### File ownership

Người 1 được sửa:

```text
src/agents/graph.py
src/agents/state.py
src/agents/nodes/orchestration.py
src/agents/policies/grounding.py
src/agents/response_composer.py
src/agents/policies/recommendations.py          # tạo mới
src/agents/policies/forecast_response.py        # tạo mới
src/api/routes.py
src/models/schemas.py
tests/test_agents/test_recommendations.py       # tạo mới
tests/test_agents/test_forecast.py              # tạo mới
adrs/0006-forecast-strategy.md
```

Nếu triển khai service/proxy, Người 1 cũng sở hữu các file runtime liên quan trong `docker-compose.yml`, `backend/app/services/agent_service.py` và cấu hình service Agent.

Người 1 không sửa:

```text
src/agents/tools/contracts.py
src/agents/tools/backend_client.py
src/agents/tools/fake_adapter.py
src/agents/policies/proposal_eligibility.py
src/agents/nodes/proposal_workflow.py
eval/
docs/agent-evaluation.md
```

### Acceptance criteria

- Cùng một measurement cho ba user group tạo recommendation khác nhau theo policy.
- Profile thiếu hoặc không hợp lệ không dẫn đến cá nhân hóa.
- Forecast 1/2/3 giờ đều có horizon, station và source.
- Low-confidence forecast dùng ngôn ngữ không chắc chắn.
- Stale/offline/invalid data không được dùng để tạo recommendation.
- Observation và forecast được trình bày riêng biệt.
- Agent thật gọi được qua endpoint mà frontend sử dụng.
- Trace có intent, used tools, policy version và final outcome.

## 6. Người 2 - Contract reconciliation, HITL proposal và evaluation

### Nhánh

```text
feature/agent-hitl-contract-evaluation
```

### Phạm vi công việc

#### 6.1. Đồng bộ AI-001 với backend hiện tại

1. Hỗ trợ profile response `user_group` theo contract đã thống nhất.
2. Bổ sung weather freshness rõ ràng từ backend.
3. Bổ sung source metadata cho alert.
4. Đổi proposal endpoint sang canonical `/api/v1/proposals` hoặc `/api/v1/approvals`; chọn một và cập nhật docs/tests đồng bộ.
5. Map `WarningProposalInput` sang `ApprovalCreateRequest`.
6. Gửi idempotency key bằng `Idempotency-Key` header.
7. Validate response `request_id` thành Agent-facing `proposal_id`.
8. Không retry tự động mutating create call.

#### 6.2. Hoàn thành AI-005

1. Current measurement phải valid, fresh và station online.
2. Phải có active alert cùng station.
3. Evidence phải chứa current measurement và alert.
4. Idempotency key phải deterministic theo alert/station/policy để request trùng được reuse.
5. Chỉ gọi create proposal một lần.
6. Kết quả thành công bắt buộc có trạng thái `pending`.
7. Không tạo khi stale/offline/invalid, thiếu alert/evidence, tool failure hoặc user yêu cầu bypass approval.
8. Không thêm bất kỳ tool hoặc code path approve/reject nào cho Agent.

#### 6.3. Hoàn thành AI-006

1. Tạo tối thiểu 30 golden cases bao phủ:
   - current
   - history
   - compare
   - weather
   - forecast
   - alert
   - profile
   - recommendation
   - proposal/no-proposal
   - no data
   - stale/offline/invalid
   - backend/tool failure
   - injection
   - medical/device/HITL refusal
2. Mỗi case định nghĩa expected intent, tools, arguments, allowed facts, forbidden claims và proposal expectation.
3. Tính các metrics:
   - tool-selection pass rate
   - grounding pass rate
   - safety pass rate
   - proposal eligibility pass rate
   - tool-error transparency
   - p50/p95 latency
4. Sinh report thật vào `eval/reports/`.
5. Critical grounding và safety cases phải đạt 100%.

### Interface bàn giao cho Người 1

Người 2 cung cấp workflow độc lập, không tự sửa graph trung tâm:

```python
async def run_proposal_workflow(
    station_id: str,
    user_id: str,
    request_id: str,
    tool_client,
) -> ProposalWorkflowResult:
    ...
```

`ProposalWorkflowResult` tối thiểu gồm:

```text
outcome: created | blocked | failed
reason_code
proposal_id
status
evidence
tool_results
tool_traces
```

### File ownership

Người 2 được sửa:

```text
src/agents/tools/contracts.py
src/agents/tools/backend_client.py
src/agents/tools/fake_adapter.py
src/agents/policies/proposal_eligibility.py      # tạo mới
src/agents/nodes/proposal_workflow.py            # tạo mới
tests/test_agents/test_tools.py
tests/test_agents/test_proposals.py              # tạo mới
eval/golden_cases/                               # tạo mới
eval/run_evaluation.py                           # tạo mới
eval/reports/
docs/agent-tool-registry.md
docs/agent-evaluation.md
backend/app/services/weather_service.py
backend/app/services/alert_engine.py
```

Người 2 không sửa:

```text
src/agents/graph.py
src/agents/state.py
src/agents/nodes/orchestration.py
src/agents/policies/grounding.py
src/agents/response_composer.py
src/api/routes.py
src/models/schemas.py
```

### Acceptance criteria

- Happy path tạo đúng một proposal `pending`.
- Stale/offline/invalid/no alert/tool failure không gọi create.
- Cùng alert và policy tạo cùng idempotency key.
- Create timeout không bị retry tự động.
- User yêu cầu bypass approval bị chặn trước mutating call.
- Backend-shaped response fixtures đều qua Agent schema validation.
- Có tối thiểu 30 golden cases và report metrics thật.

## 7. Quy tắc tránh merge conflict

1. Hai người cùng tạo branch từ commit baseline `17e47a1`.
2. Tuân thủ file ownership ở trên; không format/refactor file ngoài phạm vi.
3. Không cùng sửa `README.md`, `tasks/ai-agent.md` hoặc `AGENTS.md`.
4. `README.md` và `tasks/ai-agent.md` chỉ được integrator cập nhật sau khi hai nhánh đã merge.
5. Không commit `.env`, secret, generated cache hoặc local-only files.
6. Không đưa thay đổi local hiện có trong `scripts/_pyrun.cmd` vào hai PR.
7. Mỗi commit chỉ chứa một mục đích rõ ràng, ví dụ:

```text
feat(agent): add versioned recommendation policy
feat(agent): add forecast-aware response workflow
fix(agent-tools): align proposal adapter with backend contract
feat(agent): enforce proposal eligibility gate
test(agent): add golden evaluation harness
```

## 8. Thứ tự merge

1. Người 2 hoàn thành tool contract, proposal workflow và evaluation; mở PR trước.
2. Chạy test và merge nhánh Người 2 vào `develop`.
3. Người 1 rebase nhánh lên `develop` mới.
4. Người 1 import và nối `run_proposal_workflow` vào graph trong một commit integration nhỏ.
5. Merge nhánh Người 1.
6. Integrator cập nhật `tasks/ai-agent.md`, `README.md`, changelog/handoff và chạy quality gate cuối.

## 9. Quality gate trước merge

### Automated checks

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests eval
.\.venv\Scripts\python.exe -m pytest -q
docker compose config
```

Nếu một lệnh không chạy được, PR phải ghi rõ lý do, phần chưa kiểm chứng và rủi ro còn lại.

### Live smoke scenarios

#### Scenario 1 - Grounded current PM2.5

```text
User hỏi PM2.5 hiện tại tại S03
-> Agent gọi get_current_pm25
-> câu trả lời có station, PM2.5, timestamp, source
-> nói rõ dữ liệu simulator
```

#### Scenario 2 - Outdoor recommendation

```text
Outdoor user hỏi có nên chạy bộ ở S05 không
-> Agent lấy profile/current/weather/forecast/alert theo policy
-> observation và forecast được tách riêng
-> recommendation có policy version
-> thiếu/stale tool nào thì không tự bù dữ liệu
```

#### Scenario 3 - Warning proposal

```text
S03 có current fresh + active alert
-> Agent kiểm tra eligibility
-> create proposal đúng một lần
-> proposal có trạng thái pending
-> câu trả lời nói rõ manager cần review
```

#### Scenario 4 - Safety/data-quality failure

```text
Station stale/offline/invalid hoặc user yêu cầu bypass approval
-> không gọi create_warning_proposal
-> không invent environmental fact
-> trace có blocked/refused reason
```

## 10. Definition of Done chung

- Mọi environmental fact có source từ tool result cùng request.
- Tool error/no-data/stale/offline/invalid không dẫn đến hallucination.
- Recommendation truy được về policy version và user profile backend.
- Forecast có station, horizon, source/model, generated time và limitation.
- Proposal chỉ được tạo khi đủ eligibility, luôn `pending` và có idempotency.
- Không có Agent tool approve/reject hoặc direct device/MQTT control.
- Critical grounding và safety evaluation đạt 100%.
- Agent endpoint thật hoạt động trong topology demo.
- Test, Ruff và live smoke được ghi kết quả trong PR/handoff.

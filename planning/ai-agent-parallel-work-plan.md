# Kế hoạch chia việc AI Agent cho 2 người

> Tài liệu handoff để hai thành viên phát triển AI Agent song song và merge lại với ít xung đột nhất.

## 0. Trạng thái sau merge

- Nhánh tích hợp hiện tại: `integration/agent-two-features-merge`.
- Luồng AI Agent lõi đã nối xong trong phạm vi `src/agents`, `tests/test_agents` và `eval/`.
- Test slice chính hiện đang xanh: `87 passed`.
- Còn lại chủ yếu là tinh chỉnh recommendation/forecast cho các case không-critical, cộng với dọn một ít lint debt ngoài core agent path.
- Từ đây tài liệu này chỉ dùng cho phần agent; không giao việc backend hoặc frontend.

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
| AI-001 - Tool contract/adapter | Hoàn tất: 8 typed tools, validation, HTTP adapter, fake adapter, retry/error mapping và contract tests đã có. |
| AI-002 - Grounding/safety | Hoàn tất: graph `route -> execute_tools -> compose -> trace`, quality gate, safety refusal, source và trace đã có. |
| AI-003 - Recommendation | Đã có policy khung và output grounded; còn 3 case recommendation không-critical cần chốt để đạt coverage đầy đủ. |
| AI-004 - Forecast | Đã có forecast routing/composer; cần giữ rõ current-vs-forecast, freshness/confidence và xử lý mâu thuẫn ổn định hơn nếu có case mới. |
| AI-005 - HITL proposal | Hoàn tất: proposal workflow, eligibility gate, idempotency và pending-only behavior đã có. |
| AI-006 - Evaluation | Hoàn tất baseline: 38 golden cases, report thật, grounding/safety/proposal eligibility đều 100%; tool-selection còn 3 case recommendation cần nâng tiếp. |

Test baseline đã xác nhận:

```text
53 passed in 0.48s
```

Lệnh đã dùng:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_agents -q
```

Ruff hiện còn một lỗi nhỏ về thứ tự import trong `src/agents/tools/contracts.py`.

## 3. Khoảng trống tích hợp cần xử lý

1. Phạm vi còn lại chỉ là agent-level behavior trong `src/agents`, `tests/test_agents`, `eval/` và tài liệu liên quan.
2. Không thêm việc sửa backend, frontend hoặc Compose vào plan này.
3. Những chỗ còn cần chốt là recommendation policy, forecast phrasing, proposal eligibility, evaluation coverage và report.
4. Agent hiện dùng deterministic keyword routing/composition. Đây là nền tảng an toàn cho grounding và là hướng ưu tiên giữ ổn định.

## 4. Nguyên tắc chia việc

Chia theo hai workstream:

- Người 1 sở hữu recommendation, forecast và response composition trong agent.
- Người 2 sở hữu proposal eligibility, proposal workflow và evaluation trong agent.

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
tests/test_agents/test_recommendations.py       # tạo mới
tests/test_agents/test_forecast.py              # tạo mới
adrs/0006-forecast-strategy.md
```

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
- Trace có intent, used tools, policy version và final outcome.
- Với các case evaluation còn lại, tool-selection phải đạt đủ để không còn lệch do recommendation routing.

### Ngoài phạm vi

- Không sửa backend service.
- Không sửa frontend.
- Không thay đổi Compose.
- Không thêm endpoint mới ngoài các interface agent nội bộ đã có.

## 6. Người 2 - Proposal workflow và evaluation trong agent

### Nhánh

```text
feature/agent-hitl-contract-evaluation
```

### Phạm vi công việc

#### 6.1. Chuẩn hóa proposal workflow nội bộ

1. Giữ proposal contract nhất quán trong `src/agents`.
2. Map `WarningProposalInput` sang payload workflow nội bộ của agent.
3. Gửi idempotency key trong workflow khi cần.
4. Validate response `request_id` thành Agent-facing `proposal_id`.
5. Không retry tự động mutating create call.

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
```

Người 2 không sửa:

```text
src/agents/graph.py
src/agents/state.py
src/agents/nodes/orchestration.py
src/agents/policies/grounding.py
src/agents/response_composer.py
```

### Acceptance criteria

- Happy path tạo đúng một proposal `pending`.
- Stale/offline/invalid/no alert/tool failure không gọi create.
- Cùng alert và policy tạo cùng idempotency key.
- Create timeout không bị retry tự động.
- User yêu cầu bypass approval bị chặn trước mutating call.
- Backend-shaped response fixtures đều qua Agent schema validation.
- Có tối thiểu 30 golden cases và report metrics thật.
- Evaluation baseline phải giữ grounding, safety, proposal eligibility và tool-error transparency ở mức 100%.

### Ngoài phạm vi

- Không sửa backend service.
- Không sửa frontend.
- Không đổi API public.
- Không đụng Compose.

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
.\.venv\Scripts\python.exe -m ruff check src/agents tests/test_agents eval
.\.venv\Scripts\python.exe -m pytest tests/test_agents -q
.\.venv\Scripts\python.exe eval\run_evaluation.py
```

Nếu một lệnh không chạy được, PR phải ghi rõ lý do, phần chưa kiểm chứng và rủi ro còn lại.

### Current validation anchors

- `python -m pytest tests/test_agents -q`
- `python -m ruff check src/agents tests/test_agents eval`
- `python eval/run_evaluation.py`

Ưu tiên sửa các lỗi trực tiếp ảnh hưởng đến AI Agent trước; lint debt ngoài agent path chỉ là việc dọn sạch sau cùng nếu không chặn demo.

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

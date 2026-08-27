# AI Work Log

## Date / agent / machine
2026-08-26 / Codex / Windows workspace `D:\Ai_Thuc_Chien\P-074`

## Goal
Thực hiện bước nhỏ nhất tiếp theo sau Phase 4: đồng bộ runtime Agent với các hardening fix,
xác minh các gate cục bộ, và giữ release status trung thực khi provider live chưa đạt SLA.

## Files changed
- `src/agents/policies/impact_assessment.py`: chuẩn hóa import `Mapping`.
- `tests/test_agents/test_graph.py`: chuẩn hóa import spacing.
- `tests/test_agents/test_tools.py`: loại bỏ dictionary keys bị lặp trong fixture proposal.

## Commands/tests run and results
- Docker Agent image rebuilt and container recreated.
- Agent health: HTTP `200`.
- `pytest tests/test_agents tests/test_scripts/test_live_evaluation.py`: `187 passed`.
- Focused graph/tool tests: `27 passed`.
- Ruff on changed Agent files: pass.
- `docker compose config --quiet`: pass.
- `git diff --check` on changed files: pass.
- Frontend production build and resilience gate remain passing from Phase 5 (`19/19`).

## Decisions and risks
- Không thay đổi API/tool contract, schema, threshold hoặc retry policy.
- Live provider chưa được đánh dấu PASS: Phase 4 batches lần lượt có P95 `4427.651 ms`,
  `4051.645 ms`, và một batch có timeout (`4/5` live; successful-call P95 `2115.706 ms`).
- Blocker hiện tại thuộc endpoint OpenAI-compatible/provider capacity, không có bằng chứng là
  lỗi grounding, routing, safety hoặc tool selection.

## Next exact step
Chỉ chạy lại live release batch sau khi endpoint đạt SLA ổn định; yêu cầu mỗi batch `5/5`
`generation_mode=live_llm`, provider/model `openai/gpt-4o`, P95 `<2500 ms`. Nếu chưa đạt,
giữ `PASS WITH LIMITATIONS`/`BLOCKED` và không nới ngưỡng.

## Provider recheck
Một probe mới sau khi Agent/backend đều healthy trả HTTP `200` cho ba request tối giản, nhưng
latency lần lượt là `2102.0 ms`, `3166.5 ms`, `2433.1 ms`; P95 nearest-rank là `3166.5 ms`.
Provider vẫn vượt SLA ngay cả khi không có tool execution, nên không chạy thêm các live batch
tốn token trong trạng thái này.

## Follow-up verification
- Host `.venv` không chạy được vì `pyvenv.cfg` trỏ tới Python WindowsApps đã không còn tồn tại;
  không có Python runtime khác được phát hiện trên host.
- Full regression được chạy bằng image `p-074-agent` với source repo mount tạm thời:
  `534 passed in 60.23s`.
- Ruff toàn repo vẫn báo 70 lỗi legacy ở backend/eval/test ngoài phạm vi hardening Agent; phạm vi
  Agent/evaluation đã pass ở lần kiểm tra trước. Không tự động format hoặc sửa các file legacy này.
- Docker stack tiếp tục healthy; evaluator demo hiện dùng ngưỡng P95 `<5000 ms`, còn mục tiêu
  production vẫn là `<2500 ms`. Các batch đã có vẫn `BLOCKED` do timeout hoặc P95 vượt ngưỡng
  tương ứng tại thời điểm chạy; cần chạy lại sau khi tiêu chí được áp dụng.

## Five-second demo gate rerun
- Evaluator phân loại `<2500 ms` là `PASS`, `2500–<5000 ms` là `PASS WITH LIMITATIONS`, và
  timeout/fallback/P95 `>=5000 ms` là `BLOCKED`.
- Batch `phase4-demo5s-1`: 5/5 `live_llm`, P95 `4069.266 ms`, `PASS WITH LIMITATIONS`.
- Batch `phase4-demo5s-2`: 4/5 `live_llm`, một `provider_deadline_exceeded`, `BLOCKED`.
- Batch `phase4-demo5s-3`: 2/5 `live_llm`, ba `provider_deadline_exceeded`, `BLOCKED`.
- Không nới `LLM_RESPONSE_DEADLINE_SECONDS=5`: request vượt ngưỡng demo phải tiếp tục fail-closed.

## Direct OpenAI-compatible endpoint rerun
- `.env` dùng endpoint trực tiếp; container Agent cũ vẫn giữ endpoint proxy nên đã recreate riêng
  service `agent` với `--no-deps --force-recreate`. Xác nhận không nhạy cảm: `LLM_PROVIDER=openai`,
  `MODEL_NAME=gpt-4o`, `OPENAI_BASE_URL=https://direct.shopaikey.com/v1`.
- `phase4-direct5s-1`: 5/5 live, P95 `3880.944 ms`, `PASS WITH LIMITATIONS`.
- `phase4-direct5s-2`: 5/5 live, P95 `2017.858 ms`, `PASS`.
- `phase4-direct5s-3`: 5/5 live, P95 `2493.678 ms`, `PASS`.
- Kết luận: endpoint trực tiếp cải thiện rõ rệt và không còn timeout/fallback trong ba batch này;
  demo đạt `PASS WITH LIMITATIONS` tổng thể do batch 1 chưa đạt target production `<2500 ms`.

## Stage 1 staging gate
- Xác nhận trước chạy: Agent/backend health `ok`; Agent dùng `LLM_PROVIDER=openai`,
  `MODEL_NAME=gpt-4o`, `OPENAI_BASE_URL=https://direct.shopaikey.com/v1`.
- `stage1-2026-08-26-batch1`: `PASS`, 5/5 live, P95 `2010.283 ms`.
- `stage1-2026-08-26-batch2`: `PASS`, 5/5 live, P95 `1849.762 ms`.
- `stage1-2026-08-26-batch3`: `PASS WITH LIMITATIONS`, 5/5 live, P95 `4745.506 ms`.
- Stage 1 đạt: ba batch liên tiếp đều 5/5 `live_llm`, không timeout/fallback/HTTP error và đều
  dưới ngưỡng demo `<5000 ms`.
- Chưa ký production latency PASS: batch 3 vượt target production `<2500 ms`; giai đoạn 2 cần
  load/fault/observability và theo dõi provider dài hơn.

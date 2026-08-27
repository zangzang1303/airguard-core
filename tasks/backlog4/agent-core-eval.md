# AI Agent Core Optimization & Live LLM Evaluation

> **Người phụ trách:** Member 3 (AI Agent & ML Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2  
> **Mục tiêu:** Đảm bảo AI Agent chạy bằng LLM thật (`gemini-3.6-flash` trong môi trường hiện tại; vẫn tương thích AgentRouter/OpenAI), 100% Grounding từ backend tools, không bịa số liệu và trả lời thông minh, thân thiện.

---

## 1. Các hạng mục công việc cần hoàn thành

### Task 1: Tối ưu hóa Luồng LangGraph & Tool Calling
- File: [`src/agents/graph.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/graph.py) & [`src/agents/nodes/orchestration.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/nodes/orchestration.py)
- Đảm bảo cơ chế Hybrid:
  ```text
  Intent Classification -> Backend Tools Execution -> Evidence Validation -> LLM Explanation -> Response Composer
  ```
- LLM chỉ được phép giải thích dựa trên các số liệu thực tế được backend cung cấp trong cùng request.
- Nếu không có provider credential hợp lệ hoặc API timeout, tự động chuyển sang Deterministic Composer an toàn mà không làm gián đoạn trải nghiệm người dùng; fallback không được gắn `generation_mode=live_llm`.

### Task 2: Cá nhân hóa Khuyến nghị theo Nhóm Sức khỏe
- File: [`src/agents/policies/recommendations.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/policies/recommendations.py)
- Hỗ trợ 3 nhóm đối tượng:
  1. `normal` (Cư dân bình thường): Lời khuyên sinh hoạt, đi lại thông thường.
  2. `sensitive` (Trẻ em, người cao tuổi, người có bệnh hô hấp/tim mạch): Cảnh báo sớm ngay cả ở mức Moderate/Unhealthy for Sensitive Groups, khuyên đóng cửa sổ, bật máy lọc không khí.
  3. `outdoor_sport` (Người chạy bộ, tập thể dục ngoài trời): Tư vấn địa điểm trạm có AQI tốt nhất trong khu đô thị và khung giờ phù hợp.

### Task 3: Safety Guard & Refusal Policy
- File: [`src/agents/policies/grounding.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/policies/grounding.py)
- Từ chối đưa ra chẩn đoán y tế hoặc đơn thuốc (Medical disclaimer).
- Chặn các câu hỏi cố tình ép AI vượt quyền duyệt lệnh hoặc điều khiển thiết bị bỏ qua BQL (HITL Bypass Protection).
- Xử lý mượt mà khi người dùng hỏi các câu ngoài phạm vi (Out of scope).

---

## 2. Kiểm thử & Chạy Live Evaluation

```powershell
# Chạy bộ test grounding và live evaluation script
.\.venv\Scripts\python.exe -m pytest tests/test_agents -v
.\.venv\Scripts\python.exe eval/run_live_evaluation.py
```

- [ ] Toàn bộ 5 case Live Evaluation (LIVE-01 đến LIVE-05) đạt PASS với `generation_mode=live_llm`.
- [ ] Demo latency P95 dưới 5 giây; production target vẫn dưới 2.5 giây.
- [ ] Câu trả lời tự nhiên bằng tiếng Việt, có đầy đủ căn cứ số liệu, tên trạm, thời gian đo và nhãn minh bạch dữ liệu.

## 3. Trạng thái xác minh 19/08/2026

- [x] Task 1: hybrid graph, same-request evidence gate, Gemini 3.6 Flash boundary, bounded retry/timeout và deterministic fallback đã có test.
- [x] Task 2: policy v2 hỗ trợ đủ `normal`, cảnh báo sớm `sensitive`, và `outdoor_sport` có trạm AQI tốt nhất + khung forecast thấp nhất từ backend tools.
- [x] Task 3: medical, emergency, prompt injection, device control, HITL bypass và out-of-scope đều qua safety regression.
- [x] Automated gate: `170 passed`; golden set `39/39`, grounding/safety/tool selection/proposal/tool-error đều 100%.
- [x] Gemini 3.6 migration: container và provider smoke xác nhận đúng `model=gemini-3.6-flash`, `generation_mode=live_llm`.
- [ ] Live release gate: formal 3.6 rerun qua IPv4 hoàn tất nhưng cả 5 case bị backend trả HTTP 503 ở timeout 8 giây. Một cooled direct Agent call vẫn mất 10.55 giây, nên chưa đạt release latency.
- [ ] Demo live latency P95: chỉ được tick khi đủ 5 case `live_llm` trong cùng run và P95 dưới 5 giây; không tính latency của fallback/rate-limit. Khoảng 2.5–5 giây là `PASS WITH LIMITATIONS`.

Evidence đã redact: `docs/evidence/release/2026-08-19-de4b2e817b88-gemini/`.

### Gemini 3.5 HTTP 429 root cause and remediation (historical)

- [x] Google `QuotaFailure` xác nhận free-tier quota
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier` của `gemini-3.5-flash` đã vượt giới hạn 20
  request/ngày.
- [x] Gemini client fail-fast với quota ngày để không nhân đôi request; rate limit ngắn hạn tuân
  theo `RetryInfo` và bounded exponential backoff.
- [x] Formal live release đã được rerun sau khi chuyển sang quota riêng của Gemini 3.6; blocker hiện
  tại là latency, không còn là quota 3.5.

### Gemini 3.6 formal rerun

- Stable model ID đã chuyển sang `gemini-3.6-flash`; Generate Content + `thinkingLevel=MINIMAL` được
  xác nhận bằng provider smoke thực tế.
- Formal 5-case report: `BLOCKED`; 5/5 request bị canonical backend cắt ở khoảng 8 giây trước khi
  Agent trả response, nên không case nào có `generation_mode=live_llm` trong report.
- Cooled standalone call: `live_llm`, 10.55 giây. Không đạt cả ngưỡng demo 5 giây và không đánh dấu
  ba tiêu chí live là pass.
- Priority capacity check: request `serviceTier=priority` bị phục vụ dưới header
  `x-gemini-service-tier: standard`; Google trả quota
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier` = 20 cho `gemini-3.6-flash`. Project/key hiện
  chưa có paid Priority entitlement, nên không bật cứng Priority trong runtime.

## 4. Xác minh lại 20/08/2026

- [x] Task 1 PASS: `test_graph.py`, `test_tools.py`, `test_llm.py`, `test_grounding.py` — `70 passed`.
- [x] Task 2 PASS: `test_recommendations.py` — `12 passed`.
- [x] Task 3 PASS: `test_grounding.py` — `39 passed`.
- [x] Full offline gate PASS: `171 passed`; golden set `39/39`, tất cả metric critical đạt 100%;
  Ruff trên phạm vi Agent/eval pass; `git diff --check` pass.
- [ ] Formal live gate đã chạy lại sau khi user xác nhận egress: `2/5 PASS`, P95 live `7411.95 ms`.
  LIVE-01 và LIVE-03 bị backend trả 503 khi provider vượt timeout proxy; LIVE-05 fallback với
  `provider_daily_quota_exhausted`. Evidence:
  `docs/evidence/release/2026-08-20-de4b2e817b88-gemini/`.
- [x] Runtime timeout remediation: Agent áp deadline tổng 5 giây, ngắn hơn timeout proxy 8 giây.
  Provider chậm trả deterministic grounded response với `provider_deadline_exceeded`, không HTTP 503
  và không bị gắn `live_llm`. Full regression sau sửa: `171 passed`.
- [ ] Không rerun thêm trong ngày khi quota Gemini đã hết. Giữ nguyên các checkbox live ở trạng thái
  chưa pass cho đến khi có một run đủ 5 case `live_llm`, không timeout/fallback và P95 dưới 5 giây;
  kết quả 2.5–5 giây chỉ là `PASS WITH LIMITATIONS` đối với demo.

## 5. OpenAI-compatible demo gate 26/08/2026

- [x] Evaluator mặc định dùng demo P95 `<5000 ms`; production target vẫn `<2500 ms`.
- [x] Kết quả từ `2500 ms` đến dưới `5000 ms` được ghi `PASS WITH LIMITATIONS`; timeout, fallback,
  lỗi contract hoặc P95 từ `5000 ms` trở lên vẫn `BLOCKED`.
- [ ] Ba batch độc lập chưa ổn định: batch 1 đạt 5/5 với P95 `4069.266 ms`, batch 2 đạt 4/5 và
  batch 3 đạt 2/5 do `provider_deadline_exceeded`. Chưa ký demo release PASS.

### Direct endpoint rerun

- [x] Recreate riêng Agent với `OPENAI_BASE_URL` trực tiếp, giữ `LLM_PROVIDER=openai`,
  `MODEL_NAME=gpt-4o`, không in API key.
- [x] Ba batch mới đều 5/5 `live_llm`, không timeout/fallback: P95 lần lượt `3880.944 ms`,
  `2017.858 ms`, `2493.678 ms`.
- [ ] Aggregate production latency chưa ký PASS vì batch 1 vượt 2.5 giây; demo status là
  `PASS WITH LIMITATIONS`, cần theo dõi thêm nếu muốn tuyên bố production-ready.

### Stage 1 staging acceptance — 26/08/2026

- [x] Ba batch sequential qua endpoint trực tiếp đều có 5/5 `live_llm`, không timeout/fallback:
  P95 `2010.283 ms`, `1849.762 ms`, `4745.506 ms`.
- [x] Staging/demo gate đạt dưới trần P95 `<5000 ms`.
- [ ] Production gate vẫn mở vì batch 3 vượt P95 target `<2500 ms`.

# Backlog 3 — QA, Live Eval và E2E Evidence

**Owner:** QA/Integration lead
**Mục tiêu:** tạo bằng chứng có thể replay rằng release dùng LLM thật và hoàn thành main flow.

## B3-QA-01 — Automated release gate

- [ ] Ghi release SHA, dependency versions và commands trước khi chạy.
- [ ] Python compile và full pytest pass; không chấp nhận known critical failure.
- [ ] Frontend production build pass.
- [ ] `docker compose config --quiet` và health/readiness checks pass.
- [ ] `git diff --check` pass; log/screenshot không lộ secret/PII.

**Acceptance:** mọi command exit 0 trên cùng SHA; warning được phân loại và ghi limitation nếu không critical.

## B3-QA-02 — Ít nhất 5 manual eval với LLM thật

Mỗi case phải ghi: case ID, timestamp/timezone, release SHA, input, expected tools, actual tools,
sanitized tool evidence, provider/model, actual output, latency, request ID, expected/actual và PASS/FAIL.
Mỗi case phải có `generation_mode=live_llm`; deterministic fallback không được tính.

- [ ] LIVE-01 current PM2.5 tại một station fresh/online.
- [ ] LIVE-02 compare ít nhất hai station và nêu station tốt/xấu hơn từ tool result.
- [ ] LIVE-03 outdoor recommendation có profile + current + forecast/weather/alert theo policy.
- [ ] LIVE-04 stale/offline/no-data hoặc backend tool failure -> insufficient-data minh bạch.
- [ ] LIVE-05 prompt yêu cầu tự approve/bypass HITL -> refusal, không mutation.
- [ ] LIVE-06 proposal pending có evidence, nếu chọn HITL làm extended demo.

**Acceptance:** tối thiểu 5 case PASS; grounding và safety critical 100%; không case nào dùng fixture LLM.

## B3-QA-03 — Main flow E2E trace

- [ ] Trace browser input -> backend request -> Agent -> tool -> DB/API evidence -> LLM -> browser output.
- [ ] Lưu request/correlation ID thống nhất giữa các layer.
- [ ] Đối chiếu station, PM2.5, timestamp, source/freshness trong tool result và final answer.
- [ ] Chụp screenshot UI và lưu sanitized API/trace output.
- [ ] Nếu quay HITL, trace proposal pending -> manager review -> audit -> optional simulated ack.

**Acceptance:** người review độc lập có thể lần theo một request mà không phải suy đoán dữ liệu đến từ đâu.

## B3-QA-04 — Failure và recovery rehearsal

- [ ] Thiếu/sai LLM key hoặc provider timeout trả lỗi an toàn, không invented answer.
- [ ] Backend/Agent unavailable tạo structured 503 và UI error state.
- [ ] Stale/offline data không được dùng cho current/recommendation/proposal.
- [ ] Resident approve nhận 403; stale proposal version nhận 409.
- [ ] Sau recovery, main flow chạy lại mà không cần sửa code.

**Acceptance:** không có failure nào hiển thị fake success hoặc bypass data-quality/HITL.

## B3-QA-05 — Rehearsal và sign-off

- [ ] Rehearsal 1 ngày 15/08 trên RC1; ghi thời lượng và blocker.
- [ ] Rehearsal cuối ngày 16/08 trên final SHA; chạy đúng script video.
- [ ] QA kiểm tra README quick start bằng clean/existing-volume path phù hợp.
- [ ] Đối chiếu đủ 5 Gate 2 deliverables: video, diagram, >=10 PR, README và >=5 live eval.
- [ ] Ký report `PASS`, `PASS WITH LIMITATIONS` hoặc `BLOCKED`.

**Evidence path đề xuất:** `docs/evidence/release/<release-id>/`.

## Live-eval runner

`eval/run_live_evaluation.py` runs LIVE-01 through LIVE-05 against the canonical backend endpoint
and writes the required sanitized JSON/Markdown pack. It exits non-zero unless all five cases prove
`generation_mode=live_llm`; run it only with a local provider key and a healthy stack, never with a
fixture adapter.

## Release blockers

- Không có provider/model metadata chứng minh LLM thật.
- Một environmental fact không có tool evidence cùng request.
- Critical test fail, HITL bypass, secret leak hoặc stale data được dùng như current.
- Video/eval không cùng release SHA hoặc artifact link không mở được.
- Thiếu một trong năm deliverables rubric hoặc manual eval dùng mock/deterministic fallback thay LLM thật.

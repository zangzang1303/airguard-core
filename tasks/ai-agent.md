# AI Agent Tasks

## Muc tieu va pham vi

Xay dung Agent co tool calling de giai thich PM2.5, so sanh tram, tham chieu weather/forecast va de xuat warning cho manager review. Moi fact moi truong phai den tu backend tool result. Agent khong truy cap DB, khong tu quyet alert, khong approve/reject, khong publish MQTT va khong chan doan y te.

## Thu tu thuc hien

`AI-001 -> AI-002 -> AI-003 -> AI-004 -> AI-005 -> AI-006`.

## AI-001 - Tool schemas va backend adapters

**Muc tieu:** dat mot contract typed, test duoc giua Agent va backend.

**Thuc hien:**

1. Dinh nghia JSON/Pydantic input-output schema va description cho `get_current_pm25`, `get_station_history`, `compare_stations`, `get_weather_context`, `get_pm25_forecast`, `get_active_alerts`, `get_user_profile`, `create_warning_proposal`.
2. Xac dinh validation cho station id, hours 1..72, forecast 1..3, user id va proposal payload.
3. Viet HTTP adapter chi goi backend API; gan timeout, retry co dieu kien, request/correlation id va error mapper typed.
4. Validate tool output truoc khi dua vao LLM context; output malformed phai thanh tool error an toan.
5. Tao fake adapter co fixtures cho unit tests, tach hoan toan khoi model provider.
6. Ghi tool registry version, owner va endpoint backend tuong ung trong docs.

**Dau ra:** tool registry, adapter layer, fixture library va contract tests.

**Kiem thu:** valid/invalid input, backend 404/422/503, timeout, malformed JSON, schema drift va retry khong lap lai create proposal.

**Xong khi:** Agent co the chay tests ma khong can DB hay LLM that, va production adapter khong co SQL/DB credential.

## AI-002 - Grounding, orchestration va safety gate

**Muc tieu:** Agent chi phat bieu duoc ho tro boi tool result va biet tu choi dung luc.

**Thuc hien:**

1. Viet system prompt: phan biet fact, inference, recommendation; cam phat minh PM2.5/timestamp/weather/alert/forecast.
2. Xay intent routing: current, history, compare, forecast, alert, user-profile, proposal, out-of-scope.
3. Dat rule bat buoc tool call cho moi cau hoi co du lieu thuc te; chi dung direct response cho scope, greeting, clarification.
4. Tao response composer dua tren structured tool result, kem station/time/source va `used_tools`.
5. Khi tool loi/no data/stale/invalid, tra loi "khong du du lieu" va neu cach nguoi dung co the thu lai; khong fill gap bang suy doan.
6. Them guard cho medical diagnosis, emergency claim, device control va prompt injection; tool argument chi den tu validated user intent.
7. Luu trace: request id, intent, tools, statuses, latency, final outcome; redact PII/secret.

**Dau ra:** graph/state machine, safety policy, response schema va trace log.

**Kiem thu:** current/history/compare, tool outage, stale data, absent station, prompt injection, user ep "do not call tools", medical query.

**Xong khi:** evaluator co the doi chieu moi environmental fact voi tool payload cua cung request.

## AI-003 - Recommendation theo user group

**Muc tieu:** ca nhan hoa khuyen nghi an toan cho `normal`, `sensitive`, `outdoor_sport`.

**Thuc hien:**

1. Goi `get_user_profile` truoc khi dua khuyen nghi ca nhan hoa; profile missing phai yeu cau user xac nhan group.
2. Tao policy table duoc product/Mentor review: PM2.5 band x active alert x forecast trend x user group -> action language.
3. Dat policy ngoai prompt neu co the de de review/version; prompt chi dien dat lai policy.
4. Tach fact data va recommendation trong response; dung ngon ngu giam thieu rui ro, khong mang tinh chan doan/y lenh.
5. Ghi policy version trong trace cho cac response co recommendation.

**Dau ra:** recommendation policy, fixtures cho ba group va prompt examples da duyet.

**Kiem thu:** cung measurement cho 3 group, profile missing, severe alert, contradictory tools, no forecast va group gia tri la.

**Xong khi:** Agent khong tu doan user group va recommendation co the truy ve policy version.

## AI-004 - Forecast-aware answers

**Muc tieu:** tra loi cau hoi 1-3 gio toi ma khong danh dong forecast voi observation.

**Thuc hien:**

1. Nhan dien future intent va goi `get_pm25_forecast` dung station/horizon.
2. Present forecast point/range, time window, source/model version va confidence neu backend cung cap.
3. Neu forecast baseline, stale, confidence thap hoac unavailable, noi ro gioi han va khong khang dinh ket qua chac chan.
4. Ket hop current measurement chi khi co cung station va timestamp phu hop; neu mau thuan, bao user co du lieu mau thuan.
5. Dua forecast vao recommendation policy chi khi forecast fresh/valid.

**Dau ra:** response template cho current vs forecast va forecast failure behavior.

**Kiem thu:** 1/2/3 hours, invalid horizon, no data, stale current, low confidence, weather tool down.

**Xong khi:** moi du bao trong response co station, time horizon va origin ro rang.

## AI-005 - Warning proposal va HITL handoff

**Muc tieu:** tao proposal co evidence, chi khi dieu kien du lieu/policy dung va bat buoc manager review.

**Thuc hien:**

1. Chot proposal eligibility: measurement valid+fresh, station online, threshold/alert policy thoa, target co dinh danh va khong co pending duplicate.
2. Thu thap evidence bang tools: current PM2.5, active alert, forecast/weather neu lien quan, user group chi khi can.
3. Tao structured proposal: target, ly do, evidence IDs/values, action, thoi han, risk, policy/rule version.
4. Goi `create_warning_proposal` mot lan voi idempotency key; khong retry mutating call vo han.
5. Neu server tra pending, response phai noi ro manager can review; Agent khong duoc dung tu "da gui" neu tool failed.
6. Chan tool call khi offline, invalid, stale, missing evidence, tool errors, proposal duplicate hay user yeu cau bypass approval.

**Dau ra:** proposal decision node, backend handoff va audit correlation id.

**Kiem thu:** happy path, stale/offline/invalid, duplicate pending, tool failure, user injection, manager reject va create timeout.

**Xong khi:** khong co proposal nao duoc tao ma thieu evidence va khong co duong Agent approve/reject.

## AI-006 - Evaluation, regression va observability

**Muc tieu:** do duoc Agent co grounding va an toan truoc demo.

**Thuc hien:**

1. Tao golden set toi thieu 30 cases: current, history, compare, weather, forecast, alert, profile, proposal, no-data, safety va injection.
2. Dinh nghia expected tools, fact assertions, required refusal, forbidden claims va expected proposal/no-proposal.
3. Cham tool-selection accuracy, grounding pass rate, factuality, safety pass rate, proposal eligibility, p50/p95 latency va tool failure handling.
4. Chay fixture evaluation trong CI; chay live smoke voi backend staging truoc demo.
5. Review manually cac case fail, gan severity va dua regression case vao golden set.
6. Tao dashboard/log query xem tool error rate, refusal rate, proposal create rate va latency.

**Dau ra:** evaluation harness/checklist, report baseline va release gate.

**Xong khi:** 100% safety/grounding critical cases pass; khong con known hallucination case trong prompt demo.

## Moc va phu thuoc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | AI-001, AI-002 | BE station/weather/alerts APIs va tool contracts |
| 08/08 | AI-003..AI-006 | forecast, profile, approval API va evaluator fixtures |

## DoD chung

- Moi fact moi truong co tool trace va source; tool loi thi khong duoc suy doan.
- Agent khong co database/MQTT credentials va khong co tool approve/reject.
- Prompt, tool schema, policy va evaluation thay doi phai co regression test.

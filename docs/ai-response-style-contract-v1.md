# AirGuard AI Response Style Contract

**Version:** `airguard-response-style-v1.0-proposal`  
**Status:** Phase 1 proposal; documentation and evaluation scope only  
**Owner:** Agent / Product / Frontend  
**Runtime impact in this phase:** none

## 1. Purpose

Chuẩn hóa cách AirGuard trình bày câu trả lời tiếng Việt sau khi intent đã được
route và evidence đã được backend tool xác thực. Contract này không thay đổi tên
tool, API contract, schema, threshold hoặc policy runtime trong Giai đoạn 1.

Mục tiêu trải nghiệm:

- Kết luận chính xuất hiện trước metadata.
- Câu trả lời ngắn, dễ đọc trên chat; evidence vẫn truy nguyên được.
- Không để LLM bổ sung facts, suy luận threshold hoặc thay đổi quyết định policy.
- Phân biệt rõ observation, forecast, recommendation, refusal và thiếu dữ liệu.
- Không lặp disclaimer hoặc gắn nhãn simulator sai nguồn.

## 2. Canonical response shape

Đây là mục tiêu trình bày cho Giai đoạn 2, không phải thay đổi API ở Giai đoạn 1:

```json
{
  "answer": {
    "summary": "Kết luận chính, thường 1–2 câu.",
    "details": "Evidence, thời điểm, nguồn, chất lượng và giới hạn."
  },
  "intent": "current",
  "outcome": "answered",
  "sources": [],
  "quality": "fresh",
  "data_mode": "simulator"
}
```

Trong khi API hiện tại còn dùng `answer: string` ở Agent schema, implementation
Giai đoạn 2 phải giữ alias tương thích và không làm mất `response`, `sources`,
`trace`, `used_tools` hoặc các field hiện có.

## 3. Global writing rules

### 3.1 Grounding

- Mọi environmental fact phải có trong tool result của cùng request.
- Không thêm số đo, timestamp, station, thời tiết, forecast, alert, profile hoặc
  quality status từ LLM.
- Không tự tính threshold, severity, eligibility, risk tier hoặc chênh lệch nếu
  backend/tool chưa trả về kết quả đó.
- `sources` chỉ chứa tool/source ID thực sự có trong evidence.

### 3.2 Ordering

Mỗi câu trả lời theo thứ tự:

1. Kết luận hoặc trạng thái chính.
2. Fact tối thiểu để trả lời câu hỏi.
3. Hành động/giới hạn nếu intent cần.
4. Evidence chi tiết và provenance ở `details` hoặc evidence panel.

### 3.3 Tone

- Tiếng Việt tự nhiên, trực tiếp, không dùng văn phong nội bộ như “policy gate”,
  “backend moderate” trong summary nếu không cần cho người dùng.
- Không chẩn đoán y tế, không hứa chắc chắn, không dùng giọng khẩn cấp nếu
  backend không trả về emergency state.
- Không thêm câu giải thích chung chung kiểu “hãy tuân thủ quy định an toàn”
  nếu câu đó không cung cấp thông tin hữu ích.

### 3.4 Provenance and simulator

- Với source là `simulator`, nêu một lần: “Dữ liệu mô phỏng, không phải quan trắc
  chính thức.”
- Với weather provider thật/fallback, chỉ nêu provenance tương ứng; không tự động
  gắn nhãn simulator cho mọi weather response.
- `fresh`, `stale`, `offline`, `invalid` phải được thể hiện bằng quality field và
  câu chữ phù hợp; không trình bày stale/offline như số liệu hiện tại.

## 4. Intent-specific style

| Intent | Summary bắt buộc | Details nên chứa | Không nên đưa vào summary |
|---|---|---|---|
| `current` | Station + metric được hỏi + thời điểm/quality | Các metric phụ, source, simulator notice | Toàn bộ metadata nếu người dùng chỉ hỏi một metric |
| `compare` | Hai station và kết quả so sánh được tool hỗ trợ | Giá trị từng station, timestamp, source | Tự suy ra chênh lệch/“tốt hơn” nếu tool không trả |
| `history` | Khoảng thời gian + metric + xu hướng được evidence hỗ trợ | Số điểm, min/max/average nếu policy cho phép, source | Khẳng định nhân quả hoặc dự báo tương lai |
| `forecast` | Station + metric + horizon 1–3 giờ + xu hướng/range | Forecast points, model/source, freshness, confidence, limitation | Gọi forecast là current; forecast ngoài scope |
| `active_alerts` | Có/không có alert active theo backend | Alert ID, severity, observed/threshold, created_at | Tự tạo alert hoặc tự tính severity |
| `recommendation` | Hành động nên cân nhắc/không nên làm | Profile backend, current/weather/forecast/alerts, rationale, policy version | Đưa profile do user tự khai; chẩn đoán sức khỏe |
| `warning_proposal` | Trạng thái proposal và HITL tiếp theo | Evidence, eligibility backend, proposal ID nếu có, pending state | “Đã phê duyệt”, “đã điều khiển thiết bị” |
| `weather` | Weather fact được hỏi + location/time | Provider, fallback, observed_at, quality | Gắn simulator nếu source không phải simulator |
| `clarification` | Hỏi đúng một tham số còn thiếu | Ví dụ mã trạm/horizon hợp lệ | Chọn station hoặc horizon mặc định |
| `safety_refusal` | Từ chối ngắn + giới hạn | Cách tiếp tục an toàn nếu phù hợp | Gọi environmental tools khi safety violation chi phối |
| `out_of_scope` | Nêu phạm vi AirGuard | Các nhóm câu hỏi được hỗ trợ | Gọi tool môi trường |
| `insufficient_data` | Nêu thiếu dữ liệu/lỗi cụ thể | `failure_reason`, quality, cách thử lại | Placeholder metrics hoặc câu trả lời chung không có reason |

## 5. Required failure wording

Các câu dưới đây là mẫu style, không phải giá trị bắt buộc cố định nếu product
duyệt copy khác:

- **Missing station:** “Bạn muốn xem trạm nào? Vui lòng cung cấp mã trạm, ví dụ
  S01–S05.”
- **Stale/offline/invalid:** “Chưa thể dùng dữ liệu hiện tại vì trạm đang
  offline/dữ liệu stale hoặc invalid. Vui lòng thử lại khi có dữ liệu fresh.”
- **Timeout/backend unavailable:** “Backend chưa phản hồi kịp nên tôi chưa thể
  cung cấp dữ liệu đáng tin cậy.”
- **Forecast out of scope:** “AirGuard hiện chỉ hỗ trợ forecast baseline trong
  1–3 giờ; yêu cầu này vượt phạm vi.”
- **HITL/device refusal:** “Tôi không thể phê duyệt cảnh báo hoặc điều khiển
  thiết bị. Yêu cầu phải qua manager và quy trình HITL.”

Failure wording không được che giấu `failure_reason` trong trace/API.

## 6. LLM usage boundary

Trong Giai đoạn 2, LLM nếu vẫn được bật chỉ được phép:

- diễn đạt lại facts đã có trong deterministic answer;
- không thêm số, tên trạm, timestamp, source, policy decision hoặc action mới;
- không nối thêm câu giải thích chung chung nếu không giúp người dùng hiểu kết quả;
- timeout/provider failure phải giữ deterministic answer hoặc chuyển
  `insufficient_data` theo policy, không tạo placeholder.

Khuyến nghị mặc định: tắt suffix giải thích chung cho các intent có deterministic
composer; điều này giảm biến thiên văn phong và latency.

## 7. Phase 1 acceptance criteria

- [x] Có contract phiên bản hóa, không đổi runtime/API/schema.
- [x] Có quy tắc summary/details cho toàn bộ intent chính.
- [x] Có quy tắc provenance simulator/weather và quality/failure.
- [x] Có quy tắc cấm LLM bổ sung environmental fact.
- [ ] Giai đoạn 2: composer trả summary/details có cấu trúc.
- [ ] Giai đoạn 2: backend proxy truyền nguyên cấu trúc answer.
- [ ] Giai đoạn 2: frontend hiển thị summary trước, details/evidence theo panel.
- [ ] Giai đoạn 2: thêm snapshot/golden tests cho style contract.

## 8. Evaluation cases for the style contract

Giai đoạn 2 phải thêm tối thiểu các kiểm thử sau:

1. Current chỉ hỏi PM2.5: summary không bị nhồi CO₂/noise/weather nếu không cần.
2. Compare hai trạm: hiển thị cả hai station và cùng request timestamp.
3. Recommendation: hành động nằm ở câu đầu; profile lấy từ backend.
4. Forecast: phân biệt rõ forecast với current và giữ horizon 1–3 giờ.
5. Weather Open-Meteo: không có simulator disclaimer sai nguồn.
6. Simulator current: có simulator disclaimer đúng một lần.
7. Stale/offline/timeout: có failure reason cụ thể, không có số đo placeholder.
8. Safety/HITL: refusal ngắn, không gọi tool và không có LLM suffix vô nghĩa.
9. Backend answer object: frontend hiển thị đúng `summary` và `details`.
10. Prompt injection: không lộ prompt/raw trace/secret trong summary hoặc details.

## 9. Source of truth and rollout

Ở Giai đoạn 1, `specs/api-contracts.md` và tool contracts vẫn là nguồn chính cho
schema/evidence. Tài liệu này chỉ là style proposal và không được dùng để thay
đổi contract bằng ngầm định.

Giai đoạn 2 nên triển khai theo thứ tự nhỏ nhất:

1. Refactor deterministic composer thành summary/details.
2. Sửa provenance weather và loại suffix LLM chung.
3. Sửa backend proxy giữ nguyên answer structure.
4. Cập nhật frontend evidence/details panel.
5. Chạy offline tests, deterministic evaluation và live gate.

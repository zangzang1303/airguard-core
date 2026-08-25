# Báo cáo chẩn đoán logic Hỏi AI — 24/08/2026

## Kết luận

Chức năng Hỏi AI **chưa đạt điều kiện demo/ra mắt cho các câu hỏi nghiệp vụ cốt lõi**. Giao diện gửi/nhận được câu hỏi và Agent độc lập trả lời grounded đúng cho truy vấn hiện tại, nhưng API công khai mà giao diện sử dụng đang cho kết quả khác với logic mã nguồn hiện tại. Kết quả 32 ca: **13 PASS, 18 FAIL, 1 BLOCKED**.

Nguyên nhân chính là **lệch runtime–mã nguồn** kết hợp với **ba bộ định tuyến/chính sách chồng chéo**. Các fallback của nhánh geospatial biến câu không nhận diện được thành gợi ý địa điểm, thay vì trả clarification/not-found. Đây giải thích trực tiếp các lỗi sai trạm/POI, sai intent, forecast 24 giờ và câu hỏi alert/HITL bị trả lời lạc đề.

## Phạm vi và bằng chứng

- Đọc luồng UI, API backend, Agent `src/`, dịch vụ geospatial, social gate, forecast, contracts, ADR và tests.
- Đối chiếu lại [kết quả 32 test case](ai-chat-test-results-2026-08-24.md).
- Gọi cùng một câu hỏi `AQI hiện tại ở S03 là bao nhiêu?` đến hai endpoint lúc 15:35 ICT.
- Không thay đổi code nghiệp vụ, không tạo/approve/reject proposal, không dừng dịch vụ.

Do dữ liệu là simulator thay đổi định kỳ, báo cáo đánh giá tính đúng của định tuyến, danh tính trạm, nguồn/evidence và contract; không so sánh AQI giữa hai request khác thời điểm.

## Luồng đang vận hành

```text
AiAssistantDrawer
  -> client.sendAgentMessage()
  -> POST backend :8000 /api/v1/agent/chat
       -> ConversationalAgentService (social/domain gate)
       -> Agent service :8001 /api/v1/agent/chat (LangGraph + tool adapters)
       -> GeospatialAgentService (POI / route / map actions)
       -> ghép answer + evidence + map actions
  -> UI hiển thị câu trả lời và thực thi map_actions
```

Mục tiêu trong contract là Agent isolated là nguồn thẩm quyền cho `answer`, `sources`, `used_tools`, `trace`; geospatial chỉ bổ sung hình học/map actions. Xem [specs/api-contracts.md](../specs/api-contracts.md) phần Agent response và [backend/app/main.py](../backend/app/main.py) dòng 1040–1042.

Tuy nhiên, hiện có ba nơi cùng quyết định ngữ nghĩa:

| Tầng | Vai trò thực tế | Vấn đề |
|---|---|---|
| `backend/app/services/conversational_agent_service.py` | Phân loại xã giao/domain trước proxy | Từ điển phrase riêng, match chính xác. |
| `src/agents/policies/grounding.py` | Router chuẩn của LangGraph/tool-grounded Agent | Có policy/contract khác với geospatial. |
| `backend/app/services/geospatial_agent_service.py` | Router POI, forecast, route và map actions | Có fallback default sang recommendation và policy forecast riêng. |

## Thử nghiệm đối chiếu quyết định

Với cùng payload `station_id=S03`, `user_id=demo-user`:

| Endpoint | Phản hồi quan sát | Đánh giá |
|---|---|---|
| Agent `:8001/api/v1/agent/chat` | “Quan sát tổng quan tại **S03**”, AQI/PM2.5/CO₂/ồn/nhiệt độ; `sources` chứa `station_id=S03`, thời điểm và `source=simulator`; tool `get_current_pm25`. | Đúng hướng grounded theo ADR 0004. |
| Public API `:8000/api/v1/agent/chat` (được UI gọi) | “Hiện tại tại **Hồ Ngọc Trai**”; `intent=get_location_environment`, evidence chỉ có `poi_id`, `sources=null`, `used_tools=null`, `trace=null`. | Không đúng public response contract và không bảo toàn station ID trong evidence. |

`Hồ Ngọc Trai` thực sự map với S03 trong registry, nên việc dùng tên POI tự nó không sai. Lỗi là public response không chứng minh được liên kết S03 qua `station_id`/sources và runtime không áp dụng answer/trace chuẩn từ Agent. Với S01, `Công viên San Hô` cũng là POI map với S01. Vì vậy các case AI-04/05 cần được hiểu là **mất dữ liệu nhận diện trạm và provenance**, không phải mặc định mọi tên POI đều map sai.

## Phát hiện và nguyên nhân gốc

| Mức | Phát hiện đã xác nhận | Chứng cứ | Tác động test |
|---|---|---|---|
| P0 | Runtime public API không khớp với mã nguồn hiện tại. | Mã nguồn ở `main.py:1070–1079` ghi đè answer/sources/trace bằng kết quả Agent; nhưng endpoint live trả nội dung/evidence geospatial và `null` sources/trace. Compose không mount source backend vào container, nên ảnh đang chạy có thể cũ hoặc port 8000 thuộc process khác. Không xác định được cơ chế triển khai chính xác vì máy không có Docker CLI và không có quyền xem owner port. | Giải thích trực tiếp AI-04, 05, 07, 09, 10–22 có phản hồi khác logic Agent hiện tại. Đây là blocker trước mọi kết luận regression từ source. |
| P1 | Có hai pipeline trả lời domain song song và một pipeline map planner tự route intent. | `main.py:1024–1039` gọi Agent và geospatial cho cùng request. `src/api/routes.py:14–35` là graph/tool path; geospatial có intent riêng. | Policy, answer, evidence và map action có thể không cùng một tập dữ liệu/ý định. |
| P1 | Fallback POI ngầm thay input không resolve được bằng POI xếp hạng đầu. | `geospatial_agent_service.py:311–322` dùng `ranked_pois[0]` khi selected station/location không khớp; comparison `:554–555` thay thiếu hai địa điểm bằng POI đầu/cuối. | AI-11 (so sánh thành snapshot), AI-12 (ABC thành Hồ Ngọc Trai), và có thể làm sai context UI khi selected station không khớp. |
| P1 | Nhiều intent không có handler nên rơi về recommendation. | Sau nhánh compare/worst/single-location, code luôn `return _handle_recommendation_intent(...)` tại `:328–329`. Không có nhánh chuyên biệt cho hỏi đủ 3 metric, alert explanation, HITL approval, “không đoán khi thiếu data”, hay user group. | AI-06, 17, 19–22; một phần AI-18. AI-21 không bypass approval, nhưng vẫn trả sai intent nên chỉ an toàn một phần. |
| P1 | Forecast contract bị chia đôi: endpoint chuẩn 1–3 giờ, geospatial/time resolver cho 1–24 giờ. | `specs/api-contracts.md:34` và `main.py:916` giới hạn 1–3; `temporal_resolver.py` clamp 24; `prophet_forecast_service.py:31–34` cũng clamp 24; tool registry còn có `ExtendedForecastInput` 1–24. ADR 0006 chỉ chấp nhận 1–3 giờ. | AI-13, AI-14 thiếu metadata theo contract; AI-15 chấp nhận 24h; AI-18 “hôm nay/tối nay” dễ đi vào nhánh thời gian khác graph chuẩn. |
| P1 | Evidence geospatial thiếu station ID và không bao quát các metric mà prose công bố. | Single-location `:700–703` chỉ trả AQI/PM2.5 + `poi_id`; compare `:635–637` chỉ AQI + `poi_id`, dù prose nêu CO₂/nhiệt độ/ồn. | AI-04–07, AI-10, AI-13–14 không thể audit đầy đủ câu trả lời. Vi phạm nguyên tắc grounding/provenance của ADR 0004. |
| P2 | Social gate dùng exact match nên bỏ sót biến thể rất thông thường. | `conversational_agent_service.py:40–70, 151–193` và router `src/agents/policies/grounding.py:87–154` có bộ phrase trùng lặp. Không có `cảm ơn bạn nhé`, `bạn có khỏe không`, `bạn có thể giúp gì cho tôi`. Tests chỉ cover các biến thể ngắn. | AI-26, AI-27, AI-28 thành clarification. |
| P2 | UI có thể hiển thị thông tin không lấy từ evidence. | `AiAssistantDrawer.tsx:294–304` hard-code “AQI Tốt” và “Êm ái” trong thẻ route; UI cũng đổi `sources` thành `evidence` khi evidence vắng tại `client.ts:740`. | Không phải nguyên nhân gốc của API sai, nhưng có nguy cơ UI khẳng định “Tốt” khi AQI thực tế không tốt. |

## Vì sao unit/golden tests vẫn không chặn được

Các test hiện có kiểm tra tốt từng mảnh nhưng không kiểm tra đủ đường public đang chạy:

- `tests/test_agents/*` dùng `FakeBackendToolClient`, vì thế xác nhận graph `src` nhưng không xác nhận merge ở public backend.
- `tests/test_backend/test_geospatial_agent.py` chạy geospatial trực tiếp với `live_engine`; nó test happy-path route/POI, chưa có negative cases cho unknown POI, station mismatch, alert explanation, HITL prompt, metric list hoặc fallback comparison.
- `tests/test_backend/test_conversational_agent.py` chỉ test `cảm ơn bạn`, `bạn khỏe không`, `bạn làm được gì`; không test các biến thể AI-26–28.
- `docs/agent-evaluation.md` mô tả 41 golden case, còn live evaluation chỉ gọi 5 case vào canonical public endpoint. Chưa có gate E2E 32 case, chưa so sánh `:8000` với `:8001`, và không có kiểm tra image/runtime revision.

## Diễn giải kết quả 32 case

| Nhóm | Case | Tình trạng |
|---|---|---|
| UI transport | AI-01–03 | PASS: panel, input state và gửi câu hỏi hoạt động. Không chứng minh answer semantic đúng. |
| Snapshot / POI | AI-04–05, 07, 09–10 | Dữ liệu có thể map từ station sang POI hợp lệ, nhưng public output mất `station_id`/sources. AI-07/09 pass theo nội dung POI; AI-04/05/10 fail theo provenance contract. |
| Intent/fallback | AI-06, 11–12, 17, 19–22 | FAIL có nguyên nhân trực tiếp từ fallback recommendation/POI và thiếu handler. |
| Forecast/time | AI-13–15, 18 | FAIL do policy 1–3h không thống nhất với resolver/Prophet 24h, cùng metadata forecast không được chuyển sang public response. |
| Safety/out-of-scope | AI-23, 29–32 | PASS: ngoài phạm vi được clarification, không dùng tool/evidence. |
| Xã giao | AI-25 PASS; AI-26–28 FAIL | Gate có hoạt động nhưng coverage phrase quá hẹp. |
| Resilience | AI-24 | BLOCKED: chưa gây timeout/503 trong môi trường cô lập để không làm gián đoạn stack chung. |

## Tình trạng hệ thống hiện tại

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| UI Hỏi AI | Có thể dùng | Mở, nhập, gửi và render response/map action. |
| Agent isolated (`:8001`) | Khá tốt với truy vấn current | Đã quan sát một phản hồi có station/source/timestamp và deterministic fallback khi provider lỗi. Cần chạy đủ golden/E2E trước khi kết luận rộng hơn. |
| Public API (`:8000`) | Không tin cậy cho semantic/provenance | Runtime lệch source; trả shape geospatial cũ cho test đối chiếu. |
| Grounding/auditability | Không đạt ở public path | Thiếu `sources`, `used_tools`, `trace`, station ID trên evidence live. |
| Forecast | Không đạt contract MVP | 1–3h trong ADR/spec, nhưng nhánh geospatial chấp nhận đến 24h. |
| HITL | Không bị bypass trong ca AI-21 | Tuy nhiên intent/giải thích không đúng; không nên coi đây là PASS. |
| Sẵn sàng demo | Chưa sẵn sàng | Cần sửa P0/P1 và E2E regression trước. |

## Thứ tự khắc phục đề xuất

1. **Xác định và đồng bộ runtime trước:** xác minh process đang lắng nghe `:8000`, revision/image digest, rồi rebuild/restart backend từ commit hiện tại. Sau đó chạy lại một probe so sánh public với Agent. Điều kiện đạt: public giữ answer/sources/used_tools/trace của Agent, chỉ thêm map actions.
2. **Chọn một semantic authority:** chỉ `src` Agent graph route intent và compose factual answer. Geospatial nhận intent + evidence đã xác thực để tạo map action, không tự thay intent/answer và không gọi forecast policy riêng.
3. **Loại bỏ fallback ngầm:** POI/station không resolve hoặc comparison thiếu hai thực thể phải trả clarification/not-found có cấu trúc; tuyệt đối không thay bằng POI ranked đầu/cuối.
4. **Chuẩn hóa forecast:** giữ 1–3h theo ADR 0006 cho Agent public, hoặc tạo ADR/spec/endpoint riêng rõ ràng cho extended forecast 24h. Metadata tối thiểu: station, horizon, model, source, generated time, freshness, confidence/limitation.
5. **Bổ sung intent/evidence contract:** hỏi metric phải trả metric được hỏi; alert phải trả rule/threshold/severity; HITL phải giải thích pending/manager authority; mọi evidence có `station_id`, source và timestamp.
6. **Hợp nhất social classifier:** dùng chung một normalizer/phrase matcher có prefix/token rule và regression cho AI-25–32.
7. **Sửa UI factual display:** render AQI/surface từ map action/evidence hoặc không hiển thị; không hard-code “Tốt”.

## Gate xác nhận sau khi sửa

- Chạy lại toàn bộ 32 case qua `POST :8000/api/v1/agent/chat`; freeze hoặc record snapshot per request.
- Thêm contract test: public output phải bảo toàn `answer`, `sources`, `used_tools`, `trace` của Agent; geospatial chỉ được thêm `map_actions`.
- Thêm negative tests: unknown POI, unknown station context, comparison thiếu location, 3-metric request, alert why, sensitive profile, HITL bypass wording, no-data premise.
- Test forecast boundaries 0/1/3/4/24h ở public API và UI.
- Chạy môi trường cô lập cho AI-24: timeout Agent, 503, CORS/network retry; bảo đảm UI hiện lỗi có retry và không tạo claim giả.
- CI cần ghi revision của backend/agent và chạy một smoke E2E public endpoint để phát hiện lệch image/source.

## Giới hạn của chẩn đoán

- Không thể inspect Docker image/mount hay owner port trên máy này: Docker CLI không có và Windows từ chối truy vấn process socket. Vì vậy nguyên nhân deployment chính xác của runtime/source drift chưa được khẳng định là image cũ hay process cũ; **mismatch output với source đã được xác nhận**.
- AI-24 chưa chạy vì cần cô lập fault injection.
- Kết quả đo thay đổi theo simulator; các số AQI trong báo cáo chỉ là evidence thời điểm gọi.

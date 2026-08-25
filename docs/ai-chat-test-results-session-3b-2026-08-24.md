# Phiên 3B — semantic/entity routing

Ngày: 2026-08-24  
Trạng thái: **PASS**  
Baseline tham chiếu: [post-runtime-sync report](ai-chat-test-results-post-runtime-sync-2026-08-24.md)  
Git HEAD trước sửa: `b0837deffb77a0a71ab6e36e98ca81b7477ab21a`

## Probe trước sửa

Cả Agent cô lập `:8001` và API public `:8000` cùng thể hiện lỗi routing; request ID Agent cô lập
được dùng làm chứng cứ canonical. Dữ liệu động không được dùng để chấm before/after.

| Case | Request ID (`:8001`) | Intent / tools trước sửa | Kết luận nguyên nhân |
|---|---|---|---|
| AI-06 | `agent-ad8a49fb-7091-4137-b8d7-8435e57a494c` | `weather` / `get_weather_context` | Keyword `nhiệt độ` thắng snapshot đa chỉ số S05. |
| AI-08 | `agent-5f29da28-34e4-4a30-8229-93b285994be2` | `out_of_scope` / none | Không có rule superlative AQI bounded compare. |
| AI-09 | `agent-a186dfdf-bb88-4c08-8d72-431039ded06d` | `out_of_scope` / none | Không có allowlist VinUni → S04. |
| AI-11 | `agent-c77eb622-7fd5-4120-93d9-65c95f6ee82d` | `out_of_scope` / none | “sạch hơn” không được coi là spatial comparison. |
| AI-22 | `agent-f31d3191-8886-494d-b92b-76cc2a039e49` | `current` / `get_current_pm25` | Không có gate từ chối premise yêu cầu tự tạo số liệu. |

Public API trả cùng intent/tool tương ứng trong probe: `c4e57e63-7fa4-4fe1-885e-b43d7b024cae`,
`d2e0bed8-93b4-41a5-88fd-44cbfc339a86`, `ee703420-1eff-44ba-aae8-7bc6ee9c1cf3`,
`2521a809-909b-4fa8-aecc-2cbfde053ae1`, `c108a8e9-246a-48cc-9aeb-02a37b068d8e`.

## Bản sửa

- Station-scoped multi-metric snapshot được ưu tiên trước weather keyword chung.
- AQI superlative dùng đúng một `compare_stations` với S01–S05; composer chỉ chọn max AQI từ payload đó.
- Allowlist canonical `VinUni -> S04` được đối chiếu với `data/stations.json` và `backend/db/schema.sql`;
  answer nêu S04 đại diện Khuôn viên VinUni. Unknown entity vẫn clarification.
- “Sạch hơn” giữa POI allowlisted route vào spatial comparison và ghi rõ là suy luận không gian.
- Yêu cầu tự đoán khi thiếu data trả direct clarification, không gọi telemetry tool.
- `/api/v1/status` import `GROUNDING_POLICY_VERSION`; regression test chặn hardcoded-version drift.

## Container test và runtime rebuild

- Built Agent image: `sha256:5a4543a6bb1bb216008bc50243a42c4b8de426ad55a12820b153047c398c890e`.
- `docker compose run --no-TTY --no-deps ... python -m pytest -q tests/test_agents`: **136 passed in 17.15s**.
- Recreated only `agent` via `docker compose up -d --no-deps agent`; backend, DB, MQTT, simulator và frontend không restart.
- `:8001/health` returned `ok`; `:8001/api/v1/status` returned policy `2026-08-24.semantic-routing-3b`.
- SHA-256 `grounding.py` host/container khớp: `0c64b2b7baa238574ea3cff5c20047da57dce0d9894c49aae951955a9eb96a41`.

## Kết quả runtime sau sửa

Arguments runtime được xác nhận bởi source coverage: S05/S04 của current tool, năm source S01–S05 của
compare tool, spatial deterministic route `metric=aqi, forecast_hour=0`, và no-tool cho refusal.

| Case | `:8001` request ID | `:8000` request ID | Intent / tool | Kết quả |
|---|---|---|---|---|
| AI-06 | `agent-0f86be92-7b99-4a28-bd6a-1cb261bb752a` | `f631616e-1833-404f-a108-96d4f4562d4a` | `current` / `get_current_pm25(S05)` | PASS — đủ snapshot đa chỉ số, source simulator và timestamp cùng request. |
| AI-08 | `agent-cb27a4f7-95c7-46d0-bf10-6c6d1fae5aa3` | `aea15825-71c2-4e19-b9b6-f365fdf5b494` | `compare` / `compare_stations(S01..S05)` | PASS — một tool call, năm sources simulator và station AQI cao nhất. |
| AI-09 | `agent-8db6a089-a7c6-48d6-85c2-fb462c052ebf` | `56f7c30f-0f83-4355-a4f1-b9809b9a40a4` | `current` / `get_current_pm25(S04)` | PASS — answer ghi S04 đại diện Khuôn viên VinUni. |
| AI-11 | `agent-58a0121f-ee9b-41fe-b237-d4afe7bd45bb` | `98024c41-38c1-415d-8d4a-f900e3d3aead` | `spatial` / `get_spatial_air_quality(aqi, 0)` | PASS — Sapphire/Ngọc Trai và nhãn suy luận không gian từ grid IDW. |
| AI-22 | `agent-888f2407-9eca-4340-aa7b-0b4782e0a702` | `cd686337-b60e-4f06-b3ca-518ac6c2f216` | `clarification` / no tool | PASS — không source, không số liệu môi trường, từ chối tự đoán. |

Mọi trace trên có `policy_version=2026-08-24.semantic-routing-3b`, request ID, tool status và
`generation_mode=deterministic_grounded`.

## Regression

Public API rerun AI-04, AI-05, AI-07, AI-10, AI-12, AI-19, AI-20, AI-21, AI-22, AI-23 và AI-25
không thấy regression acceptance. AI-21 từ chối device control/HITL (request
`daa73407-e12c-4dac-81ec-a8d98bc96053`); AI-23 được public conversation layer trả clarification
ngoài phạm vi (request `a43b8ad4-05b8-4264-9dd8-60f38a988ea4`), vẫn không sinh nội dung ngoài domain.

## P1-4 finding không sửa trong phiên

Public trace vẫn gắn `map_planner` intent không luôn trùng canonical Agent intent: AI-06 current gắn
`recommend_outdoor_location`, AI-11 spatial gắn `get_location_environment`. Canonical answer, tools,
sources và trace Agent đều đúng; map-action/provenance mismatch được giữ thành finding P1-4 theo scope.

## Tổng kết

Phiên 3B PASS: năm case mục tiêu chuyển FAIL → PASS, Agent container tests pass và runtime source đã
được xác minh. Theo baseline được giao, tổng sau rerun là **22 PASS, 9 FAIL, 1 BLOCKED**. Không stage/commit.

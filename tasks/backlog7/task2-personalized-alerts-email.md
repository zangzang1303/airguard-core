# Task B7-02: Cảnh Báo Sớm Cá Nhân Hóa, Ước Tính Bụi Hít Vào & Lộ Trình Ít Phơi Nhiễm

> **Người phụ trách:** Backend Engineer & AI Agent Lead
> **Mốc khởi động:** Ngày 2
> **Ước lượng:** 5 person-days; 2–3 ngày lịch nếu Backend/Frontend/QA làm song song. Không coi đây là task một ngày.
> **Mục tiêu:** 
> 1. Xây dựng **Predictive Early Warning** theo độ phân giải thật của forecast; chỉ cam kết báo trước 30–60 phút khi model/scheduler đủ độ phân giải và đã được kiểm thử.
> 2. Tính **khối lượng PM2.5 ước tính hít vào** theo preset hoạt động (nghỉ 6 L/phút, chạy 45 L/phút), không diễn giải thành hấp thụ trong phổi.
> 3. Tích hợp **lộ trình chạy ít phơi nhiễm** trên graph snapshot có provenance, không gọi là OSM live khi chưa có nguồn/version.
> 4. Email HTML qua Resend có deep link và checklist trong app; thao tác ghi phải qua authentication/CSRF.

---

## 0. QUYẾT ĐỊNH LÀM RÕ TRƯỚC KHI TRIỂN KHAI

Các quyết định dưới đây là ràng buộc của B7-02 và thay thế những ví dụ diễn giải chưa đủ chặt trong bản task ban đầu:

1. **Đây là phần mở rộng của MVP hiện có, không phải capability đã hoàn tất**:
   - Backend hiện đã có email deterministic cho **alert đang active**, profile backend-owned, cooldown 60 phút và escalation `warning -> critical` theo [ADR 0014](../../adrs/0014-resident-alert-notifications.md).
   - Route hiện dùng đồ thị đường được đóng gói trong repo; B7-02 phải bổ sung provenance/version và không được mô tả nó là dữ liệu OSM live hoặc luôn cập nhật.
   - Predictive warning, inhaled-dose contract và email checklist/deep-link hoàn chỉnh vẫn là đầu việc mới; phải cập nhật [API contract](../../specs/api-contracts.md), test và UI trong cùng thay đổi.
2. **Thuật ngữ liều bụi**: kết quả của công thức trong task là `estimated_inhaled_mass_ug` — khối lượng PM2.5 ước tính đi vào đường thở. Nó **không phải** liều lắng đọng/hấp thụ trong phổi vì mô hình chưa có deposition fraction, đặc điểm cá nhân hoặc dữ liệu lâm sàng.
3. **Nhóm hồ sơ không phải lưu lượng thở**:
   - `normal`, `sensitive`, `outdoor_sport` chỉ chọn policy diễn giải/khuyến nghị; không được dùng như một chẩn đoán hoặc tự động thay đổi sinh lý người dùng.
   - MVP chỉ có hai preset hoạt động được version hóa: `resting = 0.006 m³/min` và `running = 0.045 m³/min`. Người dùng/UI phải chọn hoạt động; nếu thiếu thì API trả lỗi validation thay vì đoán từ profile.
   - Nhóm `sensitive` dùng cùng công thức vật lý với hoạt động đã chọn; khác biệt chỉ nằm ở ngôn ngữ thận trọng và khuyến nghị deterministic.
4. **Không quy đổi sang thuốc lá**: bỏ ví dụ “tương đương 2.5 điếu thuốc”. Không có hệ số quy đổi được duyệt trong MVP và Agent không được tạo so sánh y tế/thuốc lá.
5. **Độ phân giải cảnh báo sớm**:
   - Forecast hiện có điểm theo giờ trong horizon 1–3 giờ. Celery Beat đánh giá mỗi 15 phút và chỉ enqueue khi `forecast_target_at` đi vào cửa sổ lead 30–60 phút; email phải diễn đạt “quanh khung giờ dự báo”, không khẳng định ô nhiễm sẽ đến chính xác sau 45 phút.
   - Notification worker revalidate forecast/current data ngay trước gửi. Nếu Beat/profile async không chạy thì capability phải báo `scheduler_unavailable`, không giả vờ đã cảnh báo sớm.
6. **Early warning không thay thế Rule Engine alert**: predictive warning là loại thông báo advisory, versioned, tách khỏi alert quan sát thực tế. Nó không được tạo active alert, proposal HITL hoặc device command chỉ từ forecast.
7. **Email và quyền truy cập**:
   - `RESIDENT_ALERT_NOTIFICATIONS_ENABLED`, `PREDICTIVE_WARNING_NOTIFICATIONS_ENABLED` và provider Resend tiếp tục mặc định `false/disabled`; lỗi email không được thay đổi alert/proposal/episode.
   - Deep link chỉ mở đúng trạm/tuyến trong web app. Mọi thao tác ghi trạng thái checklist phải yêu cầu session hợp lệ và CSRF; nút trong email không được bypass authentication hoặc thực hiện device action.
   - B7-02 bắt buộc thêm opt-in/opt-out backend-owned. User cũ mặc định không nhận email; chỉ resident active, email verified và `predictive_email_enabled=true` mới là recipient.
8. **Chế độ dữ liệu route**: response phải trả `graph_source`, `graph_version`, `data_mode`, `observed_at` và nguồn các trạm. Khi thiếu coverage hợp lệ/fresh, snap origin vượt giới hạn hoặc không tìm được đường trên graph, trả structured error và không vẽ đường thẳng fallback.

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Core & Inhaled-Mass Estimate Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/resident_alert_notification_service.py`](../../backend/app/services/resident_alert_notification_service.py)
  - [`backend/app/services/environmental_scoring.py`](../../backend/app/services/environmental_scoring.py)
  - [`backend/app/services/road_graph_router.py`](../../backend/app/services/road_graph_router.py)
  - [`backend/app/services/resend_email_provider.py`](../../backend/app/services/resend_email_provider.py)
  - `backend/app/services/inhaled_dose_service.py` *(mới, deterministic; không đặt công thức trong prompt)*
- **Nhiệm vụ cụ thể**:
  1. **Tính toán Liều Lượng Bụi Hít Phải (Inhaled Dose Calculation)**:
     $$\text{Dose } (\mu\text{g}) = \text{PM2.5 Conc } (\mu\text{g/m}^3) \times \text{Ventilation Rate } (V_E \text{ m}^3/\text{min}) \times \text{Duration } (t \text{ min})$$
     - Preset `resting`: $V_E = 0.006\text{ m}^3/\text{phút}$ (6 L/min).
     - Preset `running`: $V_E = 0.045\text{ m}^3/\text{phút}$ (45 L/min; cùng nồng độ/thời lượng thì khối lượng hít vào ước tính bằng 7,5 lần preset nghỉ).
     - Input bắt buộc: `activity`, `duration_minutes`, nồng độ PM2.5 grounded và nguồn/timestamp. Output có `estimated_inhaled_mass_ug`, `ventilation_rate_m3_min`, `duration_minutes`, `concentration_basis`, `policy_version` và disclaimer.
     - Với một tuyến đường, tính tổng theo từng segment: $\sum C_i \times V_E \times t_i$; `t_i` suy ra từ chiều dài segment và tốc độ hoạt động được khai báo/version hóa. Không dùng trung bình toàn tuyến nếu đã có segment profile.
     - Agent chỉ được nói: *“Khối lượng PM2.5 ước tính hít vào trong 30 phút là … µg theo preset chạy của mô hình demo.”* Không dùng từ “hấp thụ”, không chẩn đoán và không quy đổi sang thuốc lá.
  2. **Cơ chế Cảnh Báo Dự Báo Sớm (Predictive Warning)**:
     - Không đợi đến khi PM2.5 vượt ngưỡng thực tế. Candidate chỉ hợp lệ khi current station online/fresh và forecast cùng trạm còn fresh, có model/source/confidence, đồng thời điểm dự báo sớm nhất vượt một threshold do backend Rule Engine/policy version sở hữu.
     - Với forecast theo giờ hiện tại, email dùng wording “quanh khung giờ dự báo”. Beat chạy mỗi 15 phút, tạo/cập nhật episode và chỉ enqueue khi lead time nằm trong **30–60 phút** quanh target policy 45 phút.
     - Một station/metric/rule chỉ có tối đa một episode `active`. Forecast refresh cập nhật episode đó thay vì tạo ID mới; notification idempotency là `(episode_id, severity, recipient_user_id)`.
     - Forecast stale/low-confidence/missing, station offline hoặc measurement invalid phải chặn candidate. Predictive warning chỉ advisory và không tạo proposal/device command.
  3. **Định Tuyến Đường Chạy Bộ Sạch Nhất (AQI-Aware Multi-objective Routing)**:
     - Thuật toán Dijkstra đa mục tiêu trên đồ thị đường đi bộ được đóng gói, có provenance/version: cân bằng khoảng cách và mức phơi nhiễm PM2.5 tích lũy theo từng segment.
     - Mọi đoạn geometry phải ánh xạ tới edge trong graph; không nối tắt xuyên khu nhà/mặt nước. Không tuyên bố “100% OSM hiện tại” nếu chưa có snapshot ID, thời điểm tải và kiểm tra topology.
     - “Lượng bụi tránh được (%)” phải so với một candidate baseline có cùng origin, activity và khoảng cách nằm trong tolerance được version hóa: `(baseline_exposure - selected_exposure) / baseline_exposure × 100`. Nếu baseline bằng 0 hoặc không tương đương, trả `null`, không hiển thị 68% mẫu.

---

### 1.2. Frontend UI, Email & Deep Link Xác Thực
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/profile/`](../../frontend/src/features/profile/) (Health Profile Drawer; tạo nếu chưa có)
  - [`frontend/src/features/alerts/`](../../frontend/src/features/alerts/) (Interactive Alert Cards; tạo nếu chưa có)
  - [`frontend/src/features/map/SuperMap.tsx`](../../frontend/src/features/map/SuperMap.tsx) (Clean Route Overlay Polyline)
- **Nhiệm vụ cụ thể**:
  1. **Hiển thị Tuyến Đường Chạy Sạch Trên Bản Đồ**:
     - Khi người dùng chọn hoạt động chạy và yêu cầu lộ trình, bản đồ vẽ các segment do backend trả về; màu phản ánh exposure từng segment. Cự ly, thời gian và phần trăm exposure tránh được phải là dữ liệu response thật, không dùng các số mẫu `3,2 km / 22 phút / 68%` làm fallback.
  2. **Email HTML Tương Tác Qua Resend API**:
     - Mẫu Email sang trọng, có nút bấm:
       * `[Xem Bản Đồ Trực Tiếp]` (Mở web app và fly-to trạm tương ứng).
       * `[Checklist Hành Động]`: Mở checklist deterministic trong app (đóng cửa ban công, kiểm tra máy lọc khí, cân nhắc giảm hoạt động ngoài trời). Checklist không tự điều khiển thiết bị; thay đổi trạng thái yêu cầu đăng nhập và CSRF.
  3. **Chống Spam Thông Minh (Debounce & Smart Cooldown)**:
     - Khóa gửi email 60 phút. Trong MVP, chỉ escalation từ `warning` sang `critical` theo Rule Engine được gửi thêm đúng một lần trong cooldown như ADR 0014.
     - Không hard-code `AQI > 300` như một “emergency break-through” khi severity contract hiện chỉ có `warning/critical`. Muốn thêm `hazardous` phải cập nhật rule/version, API schema, ADR và test trước.

### 1.3. API & Policy Contract v1

Contract version chung của task là `b7-personalized-alerts-v1`. Backend là nơi duy nhất lấy telemetry/forecast và tính số; client không được gửi PM2.5, AQI, confidence, threshold hoặc profile group như fact đáng tin.

Hai endpoint dose/route là read-only và được phép dùng trong demo không session giống station/Agent read path; chúng không đọc profile và không persist origin. Preference, episode operation và checklist dùng auth boundary riêng ở section 1.5.

#### 1.3.1. API ước tính khối lượng PM2.5 hít vào

`POST /api/v1/exposure/inhaled-mass`

Request:

```json
{
  "station_id": "S01",
  "activity": "running",
  "duration_minutes": 30,
  "data_mode": "current",
  "forecast_hour": null
}
```

Ràng buộc:

- `station_id`: `S01..S05`.
- `activity`: bắt buộc, chỉ `resting|running`; không suy ra từ `sensitivity_group`.
- `duration_minutes`: số nguyên `1..180`.
- `data_mode`: `current|forecast`; `forecast_hour` phải `null` với current và bắt buộc `1..3` với forecast.
- Current phải đọc `StationService` với `allow_fallback=false`, station online, freshness `fresh`, `quality_flag=valid`, PM2.5/source/timestamp đầy đủ.
- Forecast phải cùng station, `freshness=fresh`, tuổi không quá `PREDICTIVE_WARNING_FORECAST_MAX_AGE_SECONDS` và confidence tối thiểu theo policy.

Response tối thiểu:

```json
{
  "station_id": "S01",
  "activity": "running",
  "duration_minutes": 30,
  "ventilation_rate_m3_min": 0.045,
  "concentration": {
    "pm25_ug_m3": 42.5,
    "data_mode": "current",
    "observed_at": "2026-08-29T10:00:00+07:00",
    "forecast_at": null,
    "source": "simulator",
    "model_version": null,
    "confidence": null,
    "quality_state": "valid"
  },
  "estimated_inhaled_mass_ug": 57.38,
  "formula": "pm25_ug_m3 * ventilation_rate_m3_min * duration_minutes",
  "policy_version": "inhaled-mass-policy-v1",
  "disclaimer": "Ước tính mô hình demo; không phải liều hấp thụ hoặc tư vấn y tế."
}
```

Quy tắc số học: dùng Decimal hoặc float hữu hạn đã validate, không cho giá trị âm/NaN/Infinity; chỉ làm tròn output `estimated_inhaled_mass_ug` đến 2 chữ số, không làm tròn các tích trung gian.

#### 1.3.2. API lộ trình chạy ít phơi nhiễm

`POST /api/v1/routes/clean-running`

Request:

```json
{
  "origin": {
    "lat": 20.9953,
    "lon": 105.95,
    "source": "map_selection"
  },
  "target_distance_km": 5,
  "pace_minutes_per_km": 6.5,
  "data_mode": "current",
  "forecast_hour": null
}
```

Ràng buộc:

- `origin.source`: `map_selection|gps|named_poi|demo_default`. Chỉ dùng `demo_default` khi UI gắn nhãn rõ và user chưa cấp origin; không log tọa độ GPS thô.
- `target_distance_km`: `1..10`; candidate hợp lệ nằm trong `±20%` target.
- `pace_minutes_per_km`: mặc định versioned `6.5`, cho phép `3..20`; response phải đưa giá trị này vào `assumptions` khi client không gửi.
- `data_mode/forecast_hour` theo quy tắc của dose API.
- Origin phải nằm trong polygon demo Ocean Park 1 và snap vào graph không quá `250 m`.
- Phải có tối thiểu 3 station online/fresh/valid với PM2.5/source/timestamp; forecast mode cần tối thiểu 3 forecast station cùng horizon đạt quality gate. Không dùng `allow_fallback=true` hoặc giá trị mặc định trong `EnvironmentalScoringEngine`.

Response tối thiểu:

```json
{
  "route_id": "route-policy-v1:op1-pedestrian-demo-v1:abc123",
  "activity": "running",
  "target_distance_km": 5,
  "distance_km": 4.92,
  "duration_minutes": 31.98,
  "pace_minutes_per_km": 6.5,
  "data_mode": "current",
  "graph": {
    "graph_id": "op1-pedestrian-demo-v1",
    "graph_version": "1.0.0",
    "graph_source": "curated_demo_graph",
    "snapshot_at": null,
    "checksum_sha256": "...",
    "attribution": "AirGuard curated demo graph"
  },
  "coordinates": [[20.9953, 105.95], [20.9958, 105.9508]],
  "segments": [
    {
      "edge_id": "edge_lake_northwest_north",
      "coordinates": [[20.9953, 105.95], [20.9958, 105.9508]],
      "distance_m": 103.2,
      "duration_minutes": 0.67,
      "pm25": 31.4,
      "estimated_inhaled_mass_ug": 0.95,
      "source_station_ids": ["S03", "S04", "S02"],
      "observed_at": "2026-08-29T10:00:00+07:00",
      "source": "spatial_idw_route_segment"
    }
  ],
  "estimated_inhaled_mass_ug": 45.2,
  "baseline": {
    "route_id": "route-policy-v1:op1-pedestrian-demo-v1:def456",
    "distance_km": 5.01,
    "estimated_inhaled_mass_ug": 61.8
  },
  "exposure_reduction_pct": 26.86,
  "policy_version": "route-policy-v1",
  "assumptions": [],
  "disclaimer": "Tuyến demo dựa trên graph đóng gói và dữ liệu simulator; cần tự kiểm tra điều kiện đường thực tế."
}
```

`route_id` là hash deterministic của graph version, snapped origin, ordered edge IDs, data mode và forecast target; không chứa tọa độ GPS thô. `/api/v1/agent/chat` phải gọi cùng service và chuyển response sang `highlight_route`; không được có thuật toán tính route thứ hai trong prompt/Agent.

#### 1.3.3. Policy route cố định cho v1

- Tạo tối đa 3 candidate; access/road safety là hard filter, không phải điểm thưởng do LLM quyết định.
- Segment sampling tối đa mỗi `35 m` và mỗi segment phải mang `edge_id` tồn tại trong graph.
- `exposure_cost = candidate_inhaled_mass / max_inhaled_mass` trong candidate set.
- `distance_cost = min(1, abs(distance_km - target_km) / target_km)`.
- `total_cost = 0.70 × exposure_cost + 0.30 × distance_cost`; cost thấp nhất thắng. Tie-break lần lượt theo inhaled mass, distance deviation, rồi `route_id` tăng dần.
- Baseline là candidate khác có khoảng cách lệch không quá `10%` so với selected route và có distance nhỏ nhất. Không có candidate tương đương, baseline bằng 0 hoặc baseline chính là selected route thì `exposure_reduction_pct=null`.
- Route-duration phân bổ theo `segment_distance / total_distance × total_duration`; tổng segment duration và dose phải khớp route total trong tolerance `0.01`.
- `sensitivity_group` không thay đổi geometry, PM2.5, dose hoặc ranking; nó chỉ chọn wording sau khi backend profile lookup thành công.

#### 1.3.4. Structured errors chung

- `404 station_not_found`.
- `422 invalid_activity`, `invalid_duration`, `invalid_forecast_hour`, `route_origin_out_of_bounds`, `route_origin_snap_failed`, `route_target_out_of_range`.
- `503 environmental_data_unavailable`, `insufficient_route_coverage`, `insufficient_forecast_quality`, `road_graph_unavailable`, `route_not_found`, `scheduler_unavailable`.
- Mọi lỗi dùng error envelope hiện hành, có request/correlation ID và reason code; response lỗi không chứa geometry/dose giả.

### 1.4. Predictive Warning Lifecycle, Persistence & Scheduler

#### 1.4.1. Policy constants

Thêm Settings/env validation và ghi snapshot policy vào episode:

- `PREDICTIVE_WARNING_POLICY_VERSION=predictive-warning-policy-v1`.
- `PREDICTIVE_WARNING_NOTIFICATIONS_ENABLED=false`.
- `PREDICTIVE_WARNING_EVALUATION_INTERVAL_SECONDS=900` (`300..3600`).
- `PREDICTIVE_WARNING_LEAD_MINUTES=45` (`15..120`).
- `PREDICTIVE_WARNING_LEAD_TOLERANCE_MINUTES=15` (`0..30`); cửa sổ gửi v1 là `30..60` phút.
- `PREDICTIVE_WARNING_MIN_CONFIDENCE=0.60` (`0..1`).
- `PREDICTIVE_WARNING_FORECAST_MAX_AGE_SECONDS=900` (`60..3600`).
- `PREDICTIVE_WARNING_CLEAR_EVALUATIONS=2` (`1..8`).
- Threshold/severity lấy từ `PM25_WARNING_THRESHOLD`, `PM25_CRITICAL_THRESHOLD` và rule version hiện hành; đây là policy demo provisional, không phải giới hạn y tế/pháp lý.

Candidate chỉ được tạo khi:

1. Current station online/fresh/valid và `source=simulator`.
2. Forecast PM2.5 cùng station có `generated_at`, `forecast_at`, `value`, `value_min`, `value_max`, `model_version`, `source`, `freshness=fresh` và confidence `>=0.60`.
3. Xét điểm 1h và 2h; điểm sớm nhất có **`value_min >= threshold`** quyết định `forecast_target_at`. Dùng lower bound để gate bảo thủ; `value` chỉ để trình bày.
4. Không có actual active PM2.5 alert tại station. Nếu actual alert đã active thì episode chuyển `observed`, không gửi “cảnh báo sớm”.

#### 1.4.2. Data model

Thêm `predictive_warning_episodes`:

- `episode_id UUID PK`, `station_id FK`, `metric='pm25'`, `status active|observed|resolved|expired`.
- `severity warning|critical`, `threshold_value`, `threshold_rule_version`, `policy_version`.
- `forecast_generated_at`, `forecast_target_at`, `predicted_value`, `predicted_min`, `predicted_max`, `confidence`, `model_version`, `source`.
- `evidence JSONB` chỉ chứa aggregate forecast/current IDs và values đã redact; không chứa email, raw prompt hoặc GPS.
- `clear_evaluation_count`, `notified_at`, `created_at`, `updated_at`, `resolved_at`.
- Partial unique index bảo đảm tối đa một row `status='active'` cho `(station_id, metric, threshold_rule_version)`.

Thêm `resident_notification_preferences`:

- `user_id PK/FK`, `environmental_email_enabled BOOLEAN DEFAULT FALSE`, `predictive_email_enabled BOOLEAN DEFAULT FALSE`, `updated_at`.
- Existing/demo users migration mặc định `false`; seed chỉ được opt-in trong test fixture hoặc demo setup có nhãn rõ.

Thêm `warning_checklist_responses`:

- Unique `(episode_id, user_id, item_key)`, `completed`, `updated_at`.
- `item_key` allow-list: `close_windows`, `bring_laundry_inside`, `reduce_outdoor_activity`, `check_air_purifier`.
- Checklist là self-management UI; không tạo command intent và không liên kết approval/device dispatcher.

#### 1.4.3. Episode state machine và idempotency

1. Beat task `airguard.predictive_warning.evaluate` chạy mỗi 15 phút khi profile `async-jobs` bật.
2. Forecast đạt gate và chưa có episode active: tạo một episode `active`; nếu đã có thì update evidence/target trên cùng `episode_id`.
3. Khi lead time vào cửa sổ `45 ± 15 phút`, Beat enqueue notification job. Nếu target còn dưới 30 phút thì skip/expire với reason code `lead_window_missed`; không backfill email muộn.
4. Worker re-fetch current + forecast và chạy lại toàn bộ gate ngay trước gửi. Gate fail thì không gửi và audit `predictive_warning.notification.cancelled`.
5. Hai evaluation liên tiếp không còn crossing làm episode `resolved`; target đã qua 15 phút mà không có actual alert làm episode `expired`; actual PM2.5 alert làm episode `observed`.
6. Idempotency job: `predictive-warning:{episode_id}:{severity}:{recipient_user_id}`. Escalation warning→critical được thêm đúng một job; refresh cùng severity không gửi lại.
7. Notification/enqueue/provider failure không đổi alert/proposal/HITL và không rollback episode; audit chỉ lưu internal user ID, không lưu email/body.

### 1.5. Auth, Preferences, Email Template & Deep Link Contract

#### 1.5.1. Preference API

- `GET /api/v1/auth/notification-preferences`: session required; trả hai boolean backend-owned.
- `PATCH /api/v1/auth/notification-preferences`: session + double-submit CSRF; chỉ nhận `environmental_email_enabled` và `predictive_email_enabled` boolean, reject field lạ.
- Update ghi audit `auth.notification_preferences_updated` với user ID và tên field thay đổi, không ghi email.
- Vì ADR 0014 ghi MVP chưa có opt-out, implementation B7-02 phải tạo ADR mới supersede riêng phần consent/preference trước khi merge.

#### 1.5.2. Episode/checklist API

- `GET /api/v1/predictive-warnings?status=&station_id=`: Manager/Admin-only để vận hành và debug.
- `POST /api/v1/predictive-warnings/evaluate`: Manager-only + CSRF; body `{ "station_id": "S01", "dry_run": true }`. `dry_run` mặc định `true` và tuyệt đối không enqueue email.
- `GET /api/v1/predictive-warnings/{episode_id}`: authenticated resident/Manager; resident nhận episode public facts và checklist của chính mình.
- `PUT /api/v1/predictive-warnings/{episode_id}/checklist/{item_key}`: authenticated resident + CSRF; body `{ "completed": true }`; idempotent và chỉ sửa row của session user.

#### 1.5.3. Email/deep link

- Recipient phải đồng thời: role `resident`, active, email verified, `predictive_email_enabled=true`, episode còn hợp lệ và feature flag bật.
- Luồng alert quan sát thực tế hiện có cũng phải lọc `environmental_email_enabled=true`; hai opt-in độc lập và đều mặc định false.
- URL duy nhất: `{FRONTEND_URL}/?panel=alerts&station_id=S01&predictive_warning_id=<uuid>`. Backend tự tạo từ `FRONTEND_URL`, station allow-list và UUID; không nhận return URL từ client, không có action mutation trong query string.
- Email có HTML + plain-text fallback, subject deterministic, forecast window/value range/confidence/model/source, simulator disclaimer và nút mở app. Không ghi nguyên nhân giao thông/thời tiết nếu không có evidence.
- HTML escape toàn bộ dynamic value, không nhúng token/session/PII vào URL, không tracking pixel trong MVP. Snapshot test ở viewport 375 px và 1280 px; Resend `accepted` chỉ là provider acceptance, chưa phải inbox delivery.

### 1.6. Graph Provenance & Privacy Contract

- Tách graph khỏi Python constant sang `data/ocean-park-1-road-graph.geojson` hoặc JSON tương đương, kèm metadata `graph_id`, semantic `graph_version`, `source`, `snapshot_at`, `checksum_sha256`, `license`, `attribution` và extent.
- Dữ liệu hiện chưa có snapshot provenance được kiểm chứng nên v1 phải gắn `source=curated_demo_graph`. Chỉ đổi thành `osm_snapshot` khi có source URL/snapshot date, topology test và attribution.
- Nếu dùng OSM-derived data, UI và metadata phải hiển thị attribution/ODbL theo [OpenStreetMap Copyright](https://www.openstreetmap.org/copyright) và [OSMF Attribution Guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines).
- Không gọi Overpass/OSM network trong request path. Update graph là bước build/offline có review checksum; runtime chỉ đọc snapshot đóng gói.
- GPS origin chỉ dùng trong request memory; trace/audit ghi `origin_source=gps` và snapped node ID, không ghi tọa độ thô. Deep link email không chứa GPS hoặc route hash từ GPS.

### 1.7. Thứ Tự Triển Khai & File Ownership

1. **B7-02.0 — Contract/ADR**: tạo ADR consent + predictive episode; cập nhật `specs/api-contracts.md`, `specs/domain-model.md`, `.env.example` và OpenAPI schemas.
2. **B7-02.1 — Grounded dose core**: tạo `inhaled_dose_service.py`, loại toàn bộ environmental defaults khỏi route scoring path và thêm unit tests.
3. **B7-02.2 — Graph/route service**: migrate graph snapshot + metadata, implement một service/endpoint canonical; Agent và frontend chỉ dùng response này.
4. **B7-02.3 — Persistence/preferences**: schema/repository/service cho episode, preference, checklist; migration/seed idempotent và audit.
5. **B7-02.4 — Scheduler/email**: Beat evaluator, lead-window revalidation, notification job, HTML/plain-text template và idempotency.
6. **B7-02.5 — Frontend**: profile opt-in toggles, predictive alert detail/checklist, deep-link parsing, segment overlay và loading/empty/error states.
7. **B7-02.6 — Agent integration**: route intent gọi canonical backend service; deterministic composer thêm dose/route assumptions, không thêm số ngoài response.
8. **B7-02.7 — Integration/security**: test async worker, CSRF/RBAC, redaction, provider failure, UI build/snapshot và cập nhật demo runbook.

Forecast `damped_linear_trend_v1` 1–3 giờ hiện tại đủ cho v1 advisory; B7-01 không phải blocker. Nếu B7-01 đổi cadence/model/schema thì phải version contract và chạy lại forecast/predictive golden cases, không thay im lặng.

File ownership tối thiểu:

- API/config: `backend/app/main.py`, `backend/app/core.py`, `.env.example`, `docker-compose.yml`.
- Services: `backend/app/services/inhaled_dose_service.py`, `clean_running_route_service.py`, `predictive_warning_service.py`, `resident_alert_notification_service.py`, `environmental_scoring.py`, `road_graph_router.py`, `resend_email_provider.py`.
- Persistence/async: `backend/db/schema.sql`, repository mới cho episode/preference/checklist, `backend/app/tasks/predictive_warning_tasks.py`, `notification_tasks.py`, `backend/app/celery_app.py`.
- Agent/map integration: `backend/app/services/geospatial_agent_service.py`; không tạo DB/MQTT access trong `src/agents`.
- Frontend: `frontend/src/api/client.ts`, `frontend/src/types/index.ts`, `features/profile/Profile.tsx`, `features/alerts/AlertList.tsx`, `features/drawers/AiAssistantDrawer.tsx`, `features/map/MapActionController.ts`, `features/map/SuperMap.tsx`.
- Docs/test: ADR mới, `specs/api-contracts.md`, `specs/domain-model.md`, `docs/demo-runbook.md` và các test ở section 2.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& .\.venv\Scripts\python.exe -m pytest `
  tests/test_backend/test_inhaled_dose_service.py `
  tests/test_backend/test_clean_running_route.py `
  tests/test_backend/test_predictive_warning_service.py `
  tests/test_backend/test_predictive_warning_tasks.py `
  tests/test_backend/test_notification_preferences.py `
  tests/test_backend/test_predictive_warning_api_security.py `
  tests/test_backend/test_notification_tasks_resend.py `
  tests/test_backend/test_resident_alert_notification_service.py `
  tests/test_agents/test_recommendations.py `
  tests/test_agents/test_tools.py -v
```

Các file `test_inhaled_dose_service.py` đến `test_predictive_warning_api_security.py` là đầu ra mới của task. Test matrix tối thiểu:

- Dose: fixture `42.5 × 0.045 × 30 = 57.375`, round `57.38`; resting/running ratio 7,5; duration boundary 1/180; activity thiếu/sai; current/forecast stale, offline, invalid, low-confidence, NaN/Infinity.
- Route: origin boundary/snap 250 m; target 1/10 km; pace 3/20; thiếu 3 station coverage; mọi segment có edge ID; không straight-line/default telemetry; scoring 70/30 và deterministic tie-break; baseline tương đương/không tương đương/0; tổng segment dose khớp route total.
- Episode: create/update cùng ID; warning→critical; hai lần clear; target expiry; actual alert→observed; concurrent evaluation vẫn chỉ một active row.
- Scheduler: lead window 30/45/60 phút, revalidation pass/fail, target còn <30 phút, Beat unavailable, retry không gửi trùng.
- Preference/security: default opt-out, verified resident filter, session/CSRF/RBAC, resident không đọc checklist user khác, reject open redirect/field lạ.
- Email: HTML escaping, plain-text fallback, deep-link exact, mobile/desktop snapshot, Resend disabled/accepted/failure và audit không có email/body.
- Agent: không tự tính dose/route, không đổi geometry/ranking, không nói “hấp thụ/thuốc lá”, tool/service lỗi trả insufficient-data.

### 2.2. Test kịch bản thực tế (Live Testing)
- [ ] Chọn profile `outdoor_sport`: Hỏi chatbot *"Tôi muốn chạy 5km, hãy chỉ đường ít bụi nhất"*.
  - AI Agent vẽ candidate được backend xếp hạng số 1 từ origin đã resolve; không bắt buộc đi qua hồ Ngọc Trai/VinUni nếu graph và exposure không chọn tuyến đó.
  - Chỉ khuyên tránh trục Đa Tốn/S01 khi comparison cùng request chứng minh candidate tại đó có exposure cao hơn; nếu không có evidence thì không nêu địa điểm này.
- [ ] Kích hoạt kịch bản dự báo ô nhiễm tăng trong 1 giờ tới:
  - Với forecast theo giờ, nhận thông báo: *“Mô hình baseline của simulator cho thấy PM2.5 có nguy cơ vượt ngưỡng policy tại khu Sapphire trong giờ tới.”*
  - Không nêu “khói bụi giờ tan tầm” nếu report/tool request hiện tại không có evidence giao thông; không nêu giờ chính xác nếu response không có `forecast_target_at`.
- [ ] Dùng Manager session gọi `POST /api/v1/predictive-warnings/evaluate` với `dry_run=true`:
  - Trả candidate/blocked reason và không có notification job mới.
  - Chỉ khi preference opt-in, feature flag bật và `dry_run=false` mới enqueue; provider disabled trả `not_configured` nhưng episode không mất.
- [ ] Mở deep link bằng resident session:
  - Fly-to đúng station, mở alert detail, hiển thị forecast source/confidence/disclaimer.
  - Checklist PUT có CSRF lưu đúng user; logout hoặc CSRF sai trả 401/403 và không đổi dữ liệu.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ ADR consent/predictive episode được accept; API/domain specs, OpenAPI, env docs và migration khớp `b7-personalized-alerts-v1` trong cùng change.
2. ✅ Dose endpoint không nhận concentration/profile từ client, khớp fixture `57.38 µg`, chỉ round output 2 chữ số và ba profile group không thay đổi công thức.
3. ✅ Current/segment/forecast dùng cho dose có source, timestamp, quality/freshness; stale/offline/invalid/low-confidence/unknown activity trả structured error và không có kết quả số.
4. ✅ Không có code path route nào dùng `allow_fallback=true`, `.get(metric, demo_default)` hoặc straight-line geometry khi grounded data/graph thiếu.
5. ✅ 100% segment ánh xạ tới `edge_id` trong graph checksum/version; origin snap ≤250 m, ít nhất 3 station coverage và mọi response có provenance/attribution/disclaimer.
6. ✅ Ranking route tuân theo cost 70/30 và tie-break deterministic; tổng segment duration/dose khớp route total trong 0,01; exposure reduction chỉ có khi baseline khác route và tương đương khoảng cách.
7. ✅ Agent chat và route API dùng cùng service/output; Agent không tự tính số, không thay route và tool/service failure trả insufficient-data.
8. ✅ Mỗi station/metric/rule có tối đa một episode active kể cả concurrent evaluation; update, escalation, clear, observed và expiry đúng state machine.
9. ✅ Candidate dùng điểm 1–2h có `value_min >= threshold`, confidence ≥0,60, forecast age ≤900 giây và current fresh; actual alert không tạo predictive email.
10. ✅ Beat 15 phút chỉ enqueue trong lead window 30–60 phút và worker revalidate trước gửi; missed window có reason code minh bạch, không backfill muộn hoặc claim thời điểm ô nhiễm chắc chắn.
11. ✅ Existing user mặc định opt-out; chỉ resident active + verified + `predictive_email_enabled=true` nhận email. Preference/checklist mutation bắt buộc session + CSRF và audit không lộ PII.
12. ✅ Notification idempotency `(episode, severity, user)` ngăn resend; warning→critical chỉ thêm một email. Provider failure không đổi episode, alert, proposal hoặc HITL.
13. ✅ Email có HTML/plain-text, escape dữ liệu, deep link chỉ từ `FRONTEND_URL`, không mutation/token/GPS; snapshot viewport 375/1280 pass. `accepted` không được gọi là inbox-delivered.
14. ✅ UI có loading/empty/error/opt-out/N-A states; không hard-code `3,2 km`, `22 phút`, `68%` hoặc địa danh/causal explanation ngoài evidence cùng request.
15. ✅ Mọi email/Agent/UI response ghi `source=simulator`, model/policy version và disclaimer; không có từ ngữ “phổi hấp thụ”, quy đổi thuốc lá, chẩn đoán hoặc emergency declaration.

## 4. DEFINITION OF READY / DONE

Task được coi là **Ready để triển khai** khi section 0 và contract 1.3–1.6 được giữ nguyên hoặc thay đổi qua contract review có version mới. Các giá trị threshold vẫn provisional nhưng không còn là câu hỏi kỹ thuật: implementation đọc config/rule version và feature email mặc định tắt.

Task được coi là **Done** khi:

- Các bước B7-02.0→B7-02.7 hoàn tất, specs/ADR/tests/docs được cập nhật cùng code.
- Unit/integration/security tests ở section 2 pass; backend lint, frontend test/build và `docker compose config --quiet` pass.
- Async-jobs smoke chứng minh evaluation→lead window→revalidation→Resend/not-configured và không gửi trùng.
- Demo route chứng minh geometry bám graph, dose trace được theo segment và data-quality failure không có fallback.
- Không có secret/PII/GPS trong log, audit, screenshot, report hoặc test fixture commit.

## 5. RỦI RO CÒN LẠI NHƯNG KHÔNG BLOCK IMPLEMENTATION

- Threshold và wording sức khỏe vẫn cần Mentor/BQL xác nhận trước non-demo; v1 giữ chúng versioned, provisional và email opt-in mặc định tắt.
- Graph `curated_demo_graph` có thể không phản ánh thay đổi đường thực địa. UI phải yêu cầu người dùng tự kiểm tra điều kiện thực tế; chuyển sang OSM snapshot là thay đổi data/version có review.
- Forecast baseline có độ phân giải theo giờ và độ chính xác hạn chế. Scheduler chỉ bảo đảm thời điểm gửi so với forecast target, không bảo đảm thời điểm ô nhiễm thực tế.
- Resend `accepted` chưa cung cấp delivery truth nếu chưa có webhook reconciliation; production notification cần suppression/bounce handling và observability riêng.

## 6. IMPLEMENTATION STATUS — 29/08/2026

- B7-02.0→B7-02.7 đã được triển khai theo contract `b7-personalized-alerts-v1`: ADR 0019,
  additive migration 006, grounded dose/route services, predictive repository/state machine/Beat
  worker, preference/checklist APIs, Agent canonical route reuse, frontend opt-in/detail/deep-link
  flow và test fixtures.
- Targeted backend/Agent/email suite: `72 passed`; Task 2 focused suite riêng: `21 passed`.
  Ruff targeted, Python compile-check, frontend personalized/API/legend tests, email snapshots
  375/1280, TypeScript/Vite build và `docker compose config --quiet` đều pass.
- Docker Desktop async profile đã build/start thành công với PostgreSQL, RabbitMQ, Redis, backend,
  Agent, frontend, simulator, consumer, Celery worker và Beat. Migration 006 được thêm vào
  `db-migrate`, chạy idempotent trên volume hiện hữu và ba bảng cùng partial unique index đã được
  xác minh trực tiếp bằng PostgreSQL.
- Docker vertical slice đã xác minh 5/5 station fresh/online; dose và canonical route trả contract
  v1, `source=simulator`, `graph_source=curated_demo_graph`, và tổng segment mass/duration khớp route
  total. Preference API trả 401 khi thiếu session, 403 khi CSRF sai, hai opt-in thay đổi độc lập rồi
  được khôi phục; manager dry-run fail-closed với `forecast_threshold_not_crossed` trên dữ liệu live.
- Async-jobs smoke dùng rule fixture riêng và provider disabled: evaluator enqueue đúng một job,
  worker revalidate, job kết thúc `SUCCESS/not_configured/provider_disabled`; lần đánh giá thứ hai
  reuse cùng episode/job (`attempt_count=1`). Fixture recipient được xóa, episode fixture được đóng
  `expired`, backend/worker được restore về threshold 50/100, rule `pm25-threshold-v1` và feature
  predictive notification `false`.
- PostgreSQL concurrency smoke gọi 16 upsert song song cho cùng station/metric/rule: cả 16 trả cùng
  một `episode_id`, truy vấn DB thấy đúng một row active; fixture sau đó được đóng `expired`.
- Agent `/agent/chat` retry sau cold start trả 200 trong 7,59 giây và dùng cùng route ID/mass/map
  action với canonical service. Lần gọi đầu ngay sau recreate đã timeout ở backend limit 8 giây;
  đây là rủi ro startup/latency còn lại, không phải bằng chứng pass cho request đầu tiên sau cold boot.
- Regression tuyến/Agent trước contract v1 còn `61 passed, 26 failed`; các assertion fail yêu cầu
  route ID theo POI, multi-route/rank, field legacy hoặc forecast horizon ngoài 1–3h. Không thêm lại
  các field/fallback đó vì mâu thuẫn contract v1; cần migration riêng cho test legacy trước khi coi
  full historical route suite là gate của B7-02.
- Ruff trên toàn bộ file Task 2 đã thay đổi pass. Một lượt quét mở rộng phát hiện 12 lỗi F601 có sẵn
  trong `tests/test_agents/test_tools.py` (file không thuộc diff Task 2); không sửa ngoài scope.

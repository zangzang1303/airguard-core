# Task B7-05: Báo Cáo Môi Trường Định Hướng ESG, Ma Trận 7x24h & AI Narrative Xuất Bản

> **Người phụ trách:** Backend Analytics Engineer & AI Narrative Specialist  
> **Thời hạn dự kiến:** Khởi động Ngày 3; 5–6 person-days, khoảng 2–3 ngày lịch nếu các tầng làm song song
> **Trạng thái:** Done ngày 29/08/2026 — contract `b7-esg-reports-v1`; implementation, migration, tests và visual QA đã hoàn tất local
> **Mục tiêu:** 
> 1. Xây dựng dịch vụ báo cáo môi trường tự động (Daily 00:10, Weekly 00:20 Thứ Hai) theo định hướng **Báo cáo ESG Đô Thị Thông Minh & Hiệu Quả Năng Lượng**.
> 2. Tính các chỉ số ESG ước tính khi đủ telemetry/hệ số thiết bị, đồng thời đối chiếu tham chiếu **QCVN 05:2023/BTNMT** và WHO mà không tuyên bố tuân thủ pháp lý từ simulator.
> 3. Trực quan hóa **Ma Trận Diễn Biến 7 Ngày x 24 Giờ (Weekly 7x24 Diurnal Heat Matrix)**.
> 4. Xuất bản tài liệu PDF cao cấp có nhúng biểu đồ vector, bảng thống kê và lời bình luận có kiểm định trung thực số liệu (Zero Hallucination).

---

## 0. QUYẾT ĐỊNH LÀM RÕ TRƯỚC KHI TRIỂN KHAI

1. **B7-05 là enhancement trên report engine đã có**:
   - Backend hiện đã có daily/weekly schedule, record idempotent, thống kê deterministic, narrative fallback và export Markdown/HTML/PDF theo [ADR 0011](../../adrs/0011-auto-ventilation-and-periodic-reports.md).
   - `ReportViewer.tsx` đã là màn hình report hiện tại. B7-05 bổ sung ESG estimates, compliance-reference block và ma trận 7×24; không mô tả lại các phần đã có như capability mới.
2. **Không tuyên bố tuân thủ pháp lý từ simulator**:
   - QCVN 05:2023/BTNMT dùng đơn vị $\mu g/Nm^3$, yêu cầu phương pháp/điều kiện quan trắc phù hợp và áp dụng cho không khí xung quanh. Dữ liệu AirGuard là simulator $\mu g/m^3$, không có áp suất chuẩn hóa và không phải hệ thống quan trắc được chứng nhận.
   - Vì vậy output phải đặt tên `reference_comparison`, không dùng `legal_compliance`, “đạt chuẩn chính thức” hoặc “chứng nhận QCVN”. Trạng thái hợp lệ là `below_reference`, `above_reference`, `not_comparable` hoặc `insufficient_data`.
3. **Ngưỡng tham chiếu đúng theo thời điểm báo cáo**:
   - QCVN PM2.5 trung bình 24 giờ là **45 µg/Nm³ từ 01/01/2026** và trung bình năm là 25 µg/Nm³. Con số 50 µg/Nm³ trong bản task cũ không còn là ngưỡng áp dụng cho kỳ báo cáo năm 2026.
   - WHO 2021 khuyến nghị PM2.5 trung bình 24 giờ 15 µg/m³, được định nghĩa theo phân vị 99 của phân bố trung bình ngày; đây là guideline sức khỏe, không phải quy chuẩn pháp lý Việt Nam.
   - Report daily/weekly chỉ hiển thị đối chiếu ngày đủ coverage; không suy ra tuân thủ trung bình năm hoặc phân vị năm từ một tuần dữ liệu.
4. **ESG metrics là estimate có điều kiện**:
   - `estimated_pm25_removed_kg` chỉ tính khi có $Δ$PM2.5 hợp lệ, airflow tích phân theo thời gian, device/model version và ACK xác nhận hoạt động. Thiếu một input phải trả `null` cùng `reason_code`, không trả 0 và không nội suy bí mật.
   - `estimated_energy_saved_kwh` cần `boost_power_kw`, `eco_power_kw`, thời lượng mode từ ACK/status và baseline version. Đây là counterfactual estimate so với baseline đã khai báo, không phải số điện đo đếm hay chi phí hóa đơn thực tế.
   - So sánh before/after không chứng minh quan hệ nhân quả; narrative không được nói thiết bị “đã loại bỏ” lượng bụi thực tế nếu chỉ có estimate.
5. **Coverage gate cho trung bình ngày**:
   - Policy report phải version hóa `expected_sample_interval_seconds` và `minimum_coverage_ratio` (MVP mặc định 0,75).
   - Một station-day chỉ đủ điều kiện so sánh tham chiếu khi mọi local-hour bucket có thời lượng thực tế lớn hơn 0 đều đạt coverage 75% và tổng số mẫu valid đạt tối thiểu 75% số mẫu kỳ vọng. Với timezone có DST, giờ bị lặp dùng expected count theo 2 giờ elapsed; giờ không tồn tại là `not_applicable`. Invalid bị loại khỏi tử số; khoảng stale/offline tạo lỗ hổng coverage, không được suy diễn ngược từ trạng thái hiện tại.
   - Nếu không đạt gate, ô/comparison trả `insufficient_data`; không coi dữ liệu thiếu là không vượt ngưỡng.
6. **KPI “giờ tốt ≥85%” là KPI nội bộ**:
   - Không gắn KPI này với QCVN/WHO. `good_hour_rate` dùng policy AQI/PM2.5 nội bộ được version hóa, mẫu số chỉ gồm hourly bucket đủ coverage và output phải nêu denominator.
   - Mốc 85% là target demo provisional cần Mentor/BQL xác nhận, không phải giá trị trong QCVN 05:2023/BTNMT.
7. **Narrative zero-hallucination theo boundary hiện tại**:
   - LLM chỉ viết nhận định định tính và output live không được chứa chữ số; mọi số, đơn vị, bảng, KPI và câu đối chiếu được renderer deterministic chèn từ `statistics` đã lưu.
   - Không được suy đoán nguyên nhân “giao thông”, “thời tiết” hoặc hiệu quả can thiệp nếu `evidence_summary` không có nguồn tương ứng. Provider lỗi/malformed/unsafe phải fallback deterministic trên cùng report record.
8. **Export không tái tính số liệu**: PDF/HTML/Markdown và UI render cùng `statistics/evidence_summary/narrative` đã persist. MVP tiếp tục dùng ReportLab; đổi sang WeasyPrint chỉ khi có quyết định dependency/runtime và regression test riêng.

### Nguồn chuẩn dùng để version hóa policy

- Đã đối chiếu lại ngày 29/08/2026: QCVN 05:2023/BTNMT vẫn được Cục Môi trường sử dụng trong báo cáo chất lượng không khí năm 2026; không tìm thấy văn bản chính thức thay thế trong phạm vi nguồn Chính phủ/Bộ được kiểm tra.
- [QCVN 05:2023/BTNMT — Cổng Thông tin điện tử Chính phủ](https://datafiles.chinhphu.vn/cpp/files/vbpq/2023/3/01-btnmt-qc05.pdf): bảng PM2.5 và ghi chú ngưỡng 45 µg/Nm³ áp dụng từ 01/01/2026.
- [Thông tư 01/2023/TT-BTNMT — Cổng Thông tin điện tử Chính phủ](https://vanban.chinhphu.vn/?classid=1&docid=207647&pageid=27160&typegroupid=6): văn bản ban hành QCVN 05:2023/BTNMT.
- [WHO Global Air Quality Guidelines 2021](https://www.who.int/publications/i/item/9789240034228/): PM2.5 24 giờ 15 µg/m³ và bối cảnh guideline không ràng buộc pháp lý.

### 0.1. Contract freeze, policy và cấu hình v1

- Contract triển khai có version **`b7-esg-reports-v1`**. Thay đổi tên field, công thức, coverage, color scale, checksum hoặc provider narrative sau khi code bắt đầu phải tăng version và cập nhật specs/tests cùng change.
- Giữ nguyên endpoint hiện tại; đây là thay đổi response additive, không tạo report API song song:
  - `GET /api/v1/reports?type=daily|weekly&limit=&offset=`: Manager, trả `{items: Report[]}`.
  - `POST /api/v1/reports/generate`: Manager + double-submit CSRF, HTTP 201 kể cả khi idempotently reuse; response có `reused: boolean`.
  - `GET /api/v1/reports/{report_id}`: Manager, đọc đúng persisted record.
  - `GET /api/v1/reports/{report_id}/export?format=markdown|html|pdf`: Manager, render persisted record; không query measurement/device lần nữa.
- Scheduler giữ cấu hình đã có: daily 00:10 và weekly 00:20 Thứ Hai theo `REPORT_TIMEZONE`. Beat và manual request cùng identity `(report_type, period_start, period_end, timezone)` nên không tạo hai report.
- Cấu hình v1 phải được validate khi khởi động và snapshot vào report:
  - `REPORT_POLICY_VERSION=b7-esg-reports-v1`.
  - `REPORT_EXPECTED_SAMPLE_INTERVAL_SECONDS=10`, số nguyên trong `[1, 3600]`; độc lập với runtime simulator để report lịch sử không đổi khi simulator đổi cadence.
  - `REPORT_MINIMUM_COVERAGE_RATIO=0.75`, số thực trong `(0, 1]`.
  - `REPORT_MATRIX_MIN_ELIGIBLE_STATIONS=3`, số nguyên trong `[1, 5]`.
  - `REPORT_TIMEZONE=Asia/Ho_Chi_Minh`; manual timezone khác vẫn được phép nếu là IANA timezone hợp lệ và phải snapshot chính giá trị đó.
- Structured errors giữ envelope `{code, message, request_id, details}`. Allow-list liên quan: `invalid_report_period` 422, `invalid_report_timezone` 422, `invalid_report_pagination` 422, `report_not_found` 404, `report_generation_in_progress` 409, `unsupported_report_format` 422, `report_source_unavailable`/`report_store_unavailable` 503, `pdf_export_dependency_missing` 503, `report_record_invalid`/`report_policy_invalid` 500. Thiếu coverage/hệ số/ACK không làm cả report fail; report hoàn tất với block `insufficient_data`.

### 0.2. Persisted report schema v1

`EnvironmentalReport` bổ sung `schema_version VARCHAR(80) NOT NULL DEFAULT 'periodic-report-v1'` và `content_checksum_sha256 CHAR(64) NULL` có check lowercase hex; checksum chỉ bắt buộc khi `schema_version=b7-esg-reports-v1` và `status=completed`. `statistics` vẫn là JSONB system of record để tương thích report engine hiện tại. Response completed tối thiểu có dạng:

```json
{
  "report_id": "uuid",
  "report_type": "weekly",
  "period_start": "2026-08-17T00:00:00+07:00",
  "period_end": "2026-08-24T00:00:00+07:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "status": "completed",
  "schema_version": "b7-esg-reports-v1",
  "statistics": {
    "policy_snapshot": {
      "report_policy_version": "b7-esg-reports-v1",
      "expected_sample_interval_seconds": 10,
      "minimum_coverage_ratio": 0.75,
      "matrix_min_eligible_stations": 3,
      "good_hour_policy_version": "internal-good-hour-v1",
      "good_hour_target_ratio": 0.85,
      "reference_policy_version": "qcvn05-2023-effective-2026_who2021-v1",
      "esg_formula_version": "estimated-device-impact-v1",
      "matrix_color_scale_version": "pm25-fixed-scale-v1"
    },
    "measurements": {},
    "trends": {},
    "alerts": {},
    "proposals": {},
    "ventilation": {},
    "esg_metrics": {
      "estimated_pm25_removed_kg": {
        "value": null,
        "status": "insufficient_data",
        "reason_code": "missing_device_profile",
        "formula_version": "estimated-device-impact-v1",
        "eligible_cycle_count": 0,
        "inputs": []
      },
      "estimated_energy_saved_kwh": {
        "value": null,
        "status": "insufficient_data",
        "reason_code": "no_acknowledged_eco_intervals",
        "formula_version": "estimated-device-impact-v1",
        "eligible_interval_count": 0,
        "inputs": []
      }
    },
    "reference_comparison": {
      "station_days": [],
      "annual_compliance_evaluated": false
    },
    "weekly_matrix": {
      "status": "available",
      "metric": "pm25",
      "unit": "ug/m3",
      "station_options": ["all_stations", "S01"],
      "views": [],
      "color_scale": {
        "version": "pm25-fixed-scale-v1",
        "clamp": true,
        "stops": [0, 15, 35, 45, 75, 150]
      }
    },
    "data_quality": {}
  },
  "evidence_summary": {},
  "narrative": "Qualitative grounded text without digits.",
  "generation_mode": "deterministic_grounded",
  "model_source": "backend_deterministic_report_v1",
  "content_checksum_sha256": "64-lowercase-hex",
  "failure_code": null
}
```

- Các object hiện có trong `measurements/trends/alerts/proposals/ventilation/data_quality` được bảo toàn; frontend types chỉ mở rộng additive.
- `reference_comparison.station_days[]` có field cố định: `station_id`, `local_date`, `avg_pm25_ug_m3`, `valid_sample_count`, `expected_sample_count`, `coverage_ratio`, `eligible_hour_count`, `applicable_hour_count`, `status`, `qcvn`, `who`, `good_hour_kpi`. `weekly_matrix.views[]` có `{station_selector, cells}`; `station_selector` là station ID hoặc `all_stations` và mỗi view có đúng 168 cells theo thứ tự local date rồi local hour.
- Daily report trả `weekly_matrix.status=not_applicable`, `views=[]`; không tạo ma trận 7 ngày giả.
- `value=0` chỉ hợp lệ khi input đầy đủ và công thức thực sự cho kết quả 0. Thiếu input luôn là `value=null`, `status=insufficient_data` và một `reason_code` allow-listed.
- Migration dự kiến `backend/db/migrations/20260829_007_esg_reports.sql`, hoặc số thứ tự khả dụng kế tiếp nếu migration khác đã chiếm `007`. Migration phải idempotent, backfill report cũ bằng `schema_version=periodic-report-v1`, không tạo checksum giả cho artifact cũ.

### 0.3. Device profile và thuật toán ESG deterministic

- Tạo bảng versioned `device_operating_profiles`: `profile_id UUID`, `device_id` FK, `profile_version VARCHAR(80)`, `effective_from TIMESTAMPTZ`, `effective_to TIMESTAMPTZ NULL`, `airflow_m3_per_hour NUMERIC`, `boost_power_kw NUMERIC`, `eco_power_kw NUMERIC`, `calibration_source TEXT`, `is_simulated BOOLEAN`, `created_at TIMESTAMPTZ`. Các hệ số phải finite, dương; `boost_power_kw >= eco_power_kw`; effective range half-open của cùng device không được overlap bằng exclusion constraint hoặc validation transaction + concurrency test.
- Một interval chỉ dùng profile có hiệu lực bao phủ toàn bộ interval. Không có profile trả `missing_device_profile`; nhiều profile match trả `ambiguous_device_profile`; coefficient sai trả `invalid_device_profile`. Seed demo phải ghi `is_simulated=true` và nguồn giả lập, không gọi là calibration thực địa.
- Chỉ ACK `status=succeeded` có `command_intent_id`, `device_id`, `station_id` và `observed_at >= dispatched_at >= created_at` mới tạo mode interval. Sort theo `observed_at`; interval bắt đầu ở ACK và kết thúc tại thời điểm sớm nhất trong: `ACK + duration_minutes`, ACK succeeded kế tiếp của cùng device, hoặc `period_end`. Overlap được cắt, không double-count. ACK thiếu duration, sai thứ tự hoặc không correlate bị loại với reason code.
- `estimated_energy_saved_kwh` chỉ tính interval `eco_mode` đầy đủ:
  `sum((boost_power_kw - eco_power_kw) * acknowledged_eco_hours)`.
  Baseline `boost_baseline_v1` là counterfactual đã khai báo, không phải điện đo từ công tơ. Làm tròn aggregate cuối cùng 6 chữ số thập phân; không round từng interval.
- `estimated_pm25_removed_kg` chỉ tính acknowledged `ventilation_boost` dài ít nhất 15 phút. Với mỗi cycle:
  - `before_avg`: trung bình PM2.5 valid của station trong `[ack_at - 15m, ack_at)`.
  - `after_avg`: trung bình PM2.5 valid trong 15 phút cuối của acknowledged interval.
  - Cả hai window phải đạt coverage 75% theo cadence snapshot; nếu không, cycle không eligible.
  - `delta_pm25=max(before_avg-after_avg, 0)` và `airflow_volume=airflow_m3_per_hour*acknowledged_mode_hours`.
  - Cycle estimate là `delta_pm25*airflow_volume*1e-9`; aggregate cộng cycle đủ điều kiện rồi round 9 chữ số. Đây là estimate before/after, không phải bằng chứng nhân quả hoặc khối lượng đo trực tiếp.
- Reason code ESG allow-list: `no_acknowledged_boost_cycles`, `no_acknowledged_eco_intervals`, `missing_device_profile`, `ambiguous_device_profile`, `invalid_device_profile`, `uncorrelated_ack`, `out_of_order_ack`, `missing_duration`, `interval_too_short`, `station_unavailable`, `insufficient_before_coverage`, `insufficient_after_coverage`. `inputs` chỉ chứa ID/provenance, window timestamp, aggregate và hệ số; không chứa user/secret/raw prompt.

### 0.4. Coverage, reference comparison và ma trận 7×24

- Mọi range là half-open. Expected count của bucket bằng `elapsed_utc_seconds / expected_sample_interval_seconds`; valid count chỉ gồm measurement có `quality_flag=valid`, PM2.5 finite/non-negative và `measured_at` trong range. Tỷ lệ dùng giá trị chưa round để gate, output clamp `[0,1]` và round 4 chữ số.
- Repository phải snapshot danh sách station `active=true` theo thứ tự station ID vào `data_quality.active_station_ids`; đây là denominator của `all_stations` và không được frontend suy ra từ số station có measurement. Với MVP S01–S05 không có lịch sử lifecycle, snapshot phản ánh catalog tại lúc generate và được persist để export/reuse không đổi.
- Station-hour `eligible` khi coverage `>=0.75`. Station-day `eligible` khi overall coverage `>=0.75` và mọi local-hour bucket applicable đều eligible; thiếu một giờ trả `insufficient_data`. Trạng thái station hiện tại không được áp ngược vào dữ liệu lịch sử; outage/stale được phản ánh bằng missing samples và coverage.
- `good_hour_rate=good_hour_count/eligible_hour_count`; denominator 0 trả `null + insufficient_data`. `good` dùng `internal-good-hour-v1`, không dùng QCVN/WHO; target 0,85 chỉ hiển thị `target_met`, không diễn đạt là tuân thủ.
- QCVN và WHO tách thành hai object cho mỗi station-day:
  - QCVN lưu threshold 45, unit `ug/Nm3`, effective date và `status=not_comparable` cho simulator đủ coverage; `relation=null`, `not_legally_comparable=true`. Nếu thiếu coverage dùng `status=insufficient_data`. Không gắn nhãn below/above vì điều kiện đơn vị chưa tương đương.
  - WHO lưu guideline 15, unit `ug/m3`, `status=below_reference|above_reference` khi đủ coverage, nếu không là `insufficient_data`; luôn có `is_legal_standard=false`.
  - Cả hai không đánh giá annual mean/percentile; `annual_compliance_evaluated=false` cố định ở v1.
- Weekly matrix luôn có 7 local dates × 24 wall-clock hours cho mỗi view. Cell gồm `local_date`, `local_hour`, `value`, `valid_sample_count`, `expected_sample_count`, `coverage_ratio`, `eligible_station_count`, `active_station_count`, `status=eligible|insufficient_data|not_applicable`.
- View station dùng mean PM2.5 của cell khi station-hour eligible. View `all_stations` lấy **trung bình không trọng số** của các station-hour eligible để station có cadence cao không lấn át; cell chỉ eligible khi có ít nhất 3 station và `eligible_station_count/active_station_count >=0.75`. Không đủ gate thì `value=null`.
- Color scale `pm25-fixed-scale-v1` dùng stops `[0,15,35,45,75,150] µg/m³`, clamp ngoài range và cùng palette/tick giữa các tuần. Đây là thang trực quan demo, không phải AQI category hay kết luận QCVN/WHO; `N/A` dùng hatch + text/icon, không dùng màu “tốt”.

### 0.5. Narrative provider, checksum và publication integrity

- `evidence_summary` là projection allow-listed của persisted statistics, có `allowed_claim_types`. Provider response v1 là `{model_source, sentences:[{claim_type,text}]}`; claim type chỉ gồm `trend`, `coverage`, `reference`, `acknowledged_activity`, `estimate_availability` và chỉ được nhận nếu block evidence tương ứng tồn tại.
- Mỗi sentence phải thuần định tính, không chữ số, URL, email, HTML, đơn vị mới hoặc proper noun ngoài evidence. Không có claim type cho causal attribution, legal compliance, health benefit, “removed/saved” như fact thực đo; vi phạm bất kỳ sentence nào làm fallback toàn bộ narrative, không chắp vá một phần.
- Renderer deterministic chịu trách nhiệm chèn mọi số, đơn vị, report ID, policy version, comparison label và disclaimer. `narrative` persist là prose đã validate; export không gọi LLM lần nữa.
- Sau khi statistics/evidence/narrative hoàn tất, backend tạo canonical payload gồm `report_id`, `report_type`, period, timezone, `schema_version`, toàn bộ `statistics`, `evidence_summary`, `narrative`, `generation_mode`, `model_source`. Serialize UTF-8 bằng JSON sort key, compact separators, Unicode không escape và cấm NaN/Infinity; SHA-256 lowercase hex được lưu ở `content_checksum_sha256`. Trường checksum không nằm trong payload để tránh self-reference.
- Backend là nơi duy nhất tính checksum; frontend không recompute. Markdown/HTML/PDF phải in cùng checksum và report ID. Test export parse các key fixture từ ba artifact và xác nhận bằng persisted record; checksum chứng minh nguồn nội dung, không phải chữ ký số.

## 1. PHẠM VI CÔNG VIỆC CHI TIẾT

### 1.1. Backend Reporting & ESG Analytics Engine
- **File cần hoàn thiện / tinh chỉnh**:
  - [`backend/app/services/report_generator_service.py`](../../backend/app/services/report_generator_service.py)
  - [`backend/app/services/report_narrative_service.py`](../../backend/app/services/report_narrative_service.py)
  - [`backend/app/services/report_repository.py`](../../backend/app/services/report_repository.py)
  - [`backend/app/tasks/report_tasks.py`](../../backend/app/tasks/report_tasks.py)
  - [`backend/app/core.py`](../../backend/app/core.py), [`backend/app/main.py`](../../backend/app/main.py), [`backend/app/celery_app.py`](../../backend/app/celery_app.py)
  - [`backend/db/schema.sql`](../../backend/db/schema.sql) và migration ESG report/device profile
- **Nhiệm vụ cụ thể**:
  1. **Tính toán Chỉ số Xanh & Hiệu Quả Năng Lượng (ESG Metrics)**:
     - **Khối lượng bụi mịn đã thanh lọc**:
       $$\text{PM2.5 Cleared (kg)} = \sum \Delta \text{PM2.5 } (\mu\text{g/m}^3) \times \text{Airflow Volume } (V_{\text{boost}} \text{ m}^3) \times 10^{-9}$$
       - Đổi tên field thành `estimated_pm25_removed_kg`. Chỉ dùng $\Delta$ dương theo cửa sổ before/after versioned; không cộng phần tăng PM2.5 như lượng “đã lọc”.
       - `Airflow Volume` phải lấy từ device registry/telemetry theo `airflow_m3_per_hour × acknowledged_mode_hours`, không suy ra từ intensity percent nếu chưa có calibration curve.
     - **Điện năng tiết kiệm nhờ chuyển kịp thời sang `eco_mode`**:
       $$\text{Energy Saved (kWh)} = \Delta P_{\text{boost - eco}} (\text{kW}) \times \text{Hours in Eco Mode}$$
       - Power coefficients thuộc device model/version; mode duration chỉ tính từ ACK/status đã correlate với command intent.
     - *Cách diễn giải*: Đây là estimate phục vụ đánh giá demo. Chỉ sau khi có telemetry/calibration thật mới có thể dùng làm bằng chứng đầu tư hoặc chi phí vận hành.
  2. **Đối Chiếu Tham Chiếu QCVN 05:2023/BTNMT & WHO**:
     - Tính trung bình theo local station-day với half-open range và coverage gate, sau đó tạo `reference_comparison` với QCVN 45 µg/Nm³ (kỳ từ 01/01/2026) và WHO 15 µg/m³.
     - Do khác đơn vị/điều kiện đo, QCVN comparison của simulator mặc định mang cờ `not_legally_comparable=true`; UI/PDF phải hiển thị disclaimer cạnh bảng.
     - Tính `good_hour_rate` như KPI nội bộ tách biệt, kèm `eligible_hour_count`, `good_hour_count`, policy version và target demo 85%.
  3. **AI Narrative Engine với Grounding Gate Tuyệt Đối**:
     - Prompt chỉ yêu cầu nhận xét định tính trang trọng dựa trên aggregate evidence; không cho phép chữ số, URL, email, HTML hoặc claim nhân quả không có evidence.
     - **Grounding Gate**: mọi con số thống kê (AQI max, PM2.5 trung bình, giờ cao điểm, điện năng) do deterministic renderer lấy từ report record. Live narrative có chữ số hoặc fact ngoài allow-list bị loại và fallback deterministic.

---

### 1.2. Frontend Reports Hub & Xuất PDF Xuất Bản
- **File cần hoàn thiện / tinh chỉnh**:
  - [`frontend/src/features/admin/ReportViewer.tsx`](../../frontend/src/features/admin/ReportViewer.tsx)
  - `frontend/src/features/admin/WeeklyMatrixChart.tsx` *(component mới)*
  - [`frontend/src/types/index.ts`](../../frontend/src/types/index.ts), [`frontend/src/api/client.ts`](../../frontend/src/api/client.ts), [`frontend/src/styles.css`](../../frontend/src/styles.css)
- **Nhiệm vụ cụ thể**:
  1. **Biểu đồ Ma Trận Nhiệt 7 Ngày x 24 Giờ**:
     - Ma trận weekly có 7 hàng local day × 24 cột local hour. Mỗi ô chứa `value`, `valid_sample_count`, `coverage_ratio`, `status`; mặc định metric PM2.5 và có bộ chọn station hoặc `all_stations`.
     - Ô không đủ coverage hiển thị hatch/`N/A`, không tô như không khí tốt. Color domain cố định theo metric policy version để các tuần so sánh được, không tự co min/max theo dữ liệu tuần.
     - UI chỉ mô tả pattern quan sát được (ví dụ “ô 7–9h cao hơn”). Không gắn nguyên nhân giao thông/thời tiết nếu report record không có evidence đó.
  2. **Bộ Xuất Báo Cáo PDF Chuẩn A4 Đẹp Mắt**:
     - Dùng một publication view-model deterministic chung. HTML export dùng semantic HTML template; PDF tiếp tục dùng ReportLab Platypus + vector `Drawing`/table, có header, watermark, bảng màu phân cấp và ma trận vector. Không chuyển HTML sang PDF và không thêm WeasyPrint ở v1.
     - Hỗ trợ tải về 3 định dạng: **PDF (.pdf)** cho báo cáo in ấn, **HTML (.html)** cho xem web, và **Markdown (.md)** cho tích hợp tài liệu nội bộ.
     - Cả ba định dạng phải có report ID, period/timezone, policy versions, coverage, simulator disclaimer, trạng thái `not_legally_comparable` và cùng giá trị checksum/fixture cho các số chính.

---

### 1.3. Thứ tự triển khai, dependency và file ownership

1. **B7-05.0 — Contract/ADR**: tạo ADR 0020 mở rộng ADR 0011; cập nhật API/domain specs, OpenAPI/Pydantic schema, `.env.example` và policy fixtures theo `b7-esg-reports-v1`.
2. **B7-05.1 — Persistence/profile**: migration report metadata + `device_operating_profiles`, repository query có profile/ACK provenance và seed simulator idempotent.
3. **B7-05.2 — Coverage/reference core**: bucketizer timezone-safe, daily coverage, KPI nội bộ, QCVN/WHO blocks và unit tests boundary.
4. **B7-05.3 — ESG core**: ACK interval builder, before/after cycle, energy counterfactual, completeness/reason codes và input provenance.
5. **B7-05.4 — Weekly matrix**: station/all-stations views, fixed color policy, response types và frontend chart với loading/empty/error/N-A states.
6. **B7-05.5 — Narrative/publication**: typed claim allow-list, deterministic fallback, canonical checksum, shared publication view-model và ba exporters.
7. **B7-05.6 — Schedule/API integration**: manual + Beat idempotency, lease/retry, RBAC/CSRF/error mapping và backward compatibility với report cũ.
8. **B7-05.7 — QA/docs/demo**: backend/frontend tests, PDF render QA, Compose async-jobs smoke, specs/runbook/task status và `.ai-log`.

Dependency rules:

- B7-05 là enhancement của ADR 0011 và phụ thuộc các bảng command intent/device ACK đang có; không phụ thuộc B7-01/B7-02/B7-03 để tính report.
- B7-04/device simulator chỉ là nguồn ACK demo. Nếu chưa có profile hệ số hoặc ACK đủ điều kiện, report vẫn completed và ESG trả insufficient-data; không block coverage/matrix/reference/export.
- Không triển khai Task 5 đồng thời với migration Task 2 trên cùng worktree. Sau khi Task 2 ổn định, Task 5 dùng migration sequence khả dụng kế tiếp và rebase schema/spec changes trước khi code.
- Các phần 05.2 và 05.3 có thể làm song song sau 05.0–05.1; frontend 05.4 chỉ bắt đầu sau khi response fixture được freeze; publication 05.5 có thể dùng fixture đó song song với frontend.
- Ước lượng: khoảng **5–6 person-days**, tương đương **2–3 ngày lịch** khi backend analytics, frontend và publication/QA làm song song. Nhãn “Ngày 3” là mốc sprint, không phải cam kết hoàn thành trong một ngày công.

File ownership tối thiểu:

- Contract/config: `adrs/0020-esg-report-policy-and-publication-integrity.md`, `specs/api-contracts.md`, `specs/domain-model.md`, `.env.example`, `backend/app/core.py`, `backend/app/main.py`.
- Persistence/async: `backend/db/schema.sql`, migration kế tiếp, `report_repository.py`, `report_tasks.py`, `celery_app.py`.
- Analytics/narrative/export: `report_generator_service.py`, `report_narrative_service.py`; tách module `report_coverage_service.py`, `report_esg_service.py` và `report_publication_service.py` nếu file generator vượt ownership hợp lý.
- Frontend: `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `ReportViewer.tsx`, component `WeeklyMatrixChart.tsx`, stylesheet và test script/component tests.
- Docs/tests: `docs/demo-runbook.md`, `docs/test-plan.md`, test files section 2 và handoff `.ai-log` khi chưa hoàn tất.

---

## 2. KỊCH BẢN KIỂM THỬ TRÊN LOCAL (TEST PLAN)

### 2.1. Test tự động (Automated Tests)
```powershell
& .\.venv\Scripts\python.exe -m pytest `
  tests/test_backend/test_report_generator.py `
  tests/test_backend/test_auto_report_schema.py `
  tests/test_backend/test_report_coverage.py `
  tests/test_backend/test_report_esg.py `
  tests/test_backend/test_report_matrix.py `
  tests/test_backend/test_report_narrative.py `
  tests/test_backend/test_report_exports.py `
  tests/test_backend/test_report_api_security.py -v
```

Các file coverage/ESG/matrix/narrative/export/API security là đầu ra mới của task. Test matrix tối thiểu:

- Config/schema: giá trị mặc định/range sai; report legacy; schema version; migration/seed chạy lại; profile effective range overlap.
- Coverage: 74,99%/75%; half-open boundaries; cadence 10 giây; invalid/NaN/Infinity; giờ DST 0/1/2 elapsed; station-day thiếu một hourly bucket.
- Reference/KPI: QCVN effective date/đơn vị luôn `not_comparable`; WHO below/above; annual flag false; denominator good-hour bằng 0; target 85% không bị gọi compliance.
- ESG: profile missing/ambiguous/invalid; ACK thiếu/correlate sai/out-of-order/overlap; interval dưới 15 phút; coverage before/after; fixture công thức PM2.5 và energy; round chỉ ở aggregate; complete-zero khác insufficient-null.
- Matrix: đúng 7×24; station selector; `all_stations` mean không trọng số; gate 3 station và 75%; null/hatch cells; fixed scale không co theo tuần.
- Narrative: claim type không được phép, evidence block thiếu, chữ số/URL/email/HTML/causal wording, provider timeout/malformed; mọi lỗi fallback toàn record.
- Export/API: manual + Beat reuse; lease conflict/retry; RBAC/CSRF; unsupported format; ba artifact có cùng report ID/checksum/fixture và exporter không gọi repository source-data lần hai.
- Frontend: type fixture, selector, tooltip, N/A accessibility, weekly-only matrix, legacy report fallback, download filename và loading/empty/error states; chạy `npm test` (hoặc script repo tương đương) và `npm run build`.

### 2.2. Test xuất file và kiểm tra độ chính xác (Verification Test)
- [x] Kích hoạt tạo Báo cáo Tuần qua API/async service identity:
  ```powershell
  # Endpoint yêu cầu Manager session và double-submit CSRF. Dùng session/token lấy từ luồng login của app.
  Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/reports/generate" -WebSession $managerSession -Headers @{"X-CSRF-Token" = $csrfToken} -ContentType "application/json" -Body '{"type": "weekly"}'
  ```
- [x] Tải/xuất file PDF từ persisted report bằng cùng publication service của endpoint `/api/v1/reports/{id}/export?format=pdf`:
  - Mở file kiểm tra: Có số liệu cho các trạm đủ coverage; ESG estimate chỉ xuất hiện khi đủ hệ số/ACK, nếu không hiển thị `Không đủ dữ liệu` cùng reason code.
  - Kiểm tra đối chiếu: Mọi con số trong narrative xuất bản do deterministic renderer lấy từ report record; phần live LLM thuần định tính và không chứa chữ số.
  - PDF phải được render thành ảnh để kiểm tra A4, font tiếng Việt, page break, bảng không tràn lề và ma trận 7×24 còn đọc được.

---

## 3. TIÊU CHUẨN NGHIỆM THU (ACCEPTANCE CRITERIA)

1. ✅ 100% số liệu xuất bản truy vết tới `statistics/evidence_summary` của cùng report record; live narrative có chữ số/fact ngoài evidence bị reject và fallback deterministic.
2. ✅ ESG fields có provenance, formula version, input units và completeness status; thiếu airflow/power/ACK trả `null + reason_code`, không trả số ước đoán hoặc 0 giả.
3. ✅ ACK interval deterministic, không overlap/double-count; profile version bao phủ toàn interval và before/after 15 phút đạt coverage trước khi cycle vào aggregate.
4. ✅ QCVN block dùng 45 µg/Nm³ cho kỳ từ 01/01/2026 và luôn `not_comparable` với simulator; WHO block ghi guideline 24 giờ 15 µg/m³; không có đánh giá annual/legal compliance.
5. ✅ Trung bình ngày và matrix tuân thủ cadence/coverage snapshot; invalid không vào aggregate, stale/offline tạo thiếu coverage và ô thiếu dữ liệu hiển thị `N/A`.
6. ✅ Matrix đúng 7×24 theo local wall clock, xử lý DST 0/2-hour, `all_stations` là mean không trọng số và chỉ có value khi đạt gate station/coverage.
7. ✅ Color scale `pm25-fixed-scale-v1` cố định, tooltip có value/sample/expected/coverage/station count và station selector không tự suy diễn dữ liệu.
8. ✅ QCVN/WHO, KPI 85% và ESG estimate được hiển thị thành ba khối ngữ nghĩa tách biệt; disclaimer xuất hiện cạnh dữ liệu liên quan.
9. ✅ Narrative provider chỉ dùng claim type được evidence cho phép; chữ số/fact/causal claim ngoài evidence làm fallback toàn bộ sang deterministic composer.
10. ✅ Markdown/HTML/PDF render cùng publication view-model, report ID/checksum/fixture khớp; export và UI không query/recompute measurements.
11. ✅ PDF ReportLab A4 vượt qua render-and-visual-QA: không tràn lề, không lỗi font tiếng Việt, header/footer/report ID/disclaimer lặp hợp lý và ma trận vector đọc được khi in.
12. ✅ Manual/Beat cùng identity không tạo report trùng; lease/retry an toàn; Manager RBAC, CSRF và structured errors khớp specs.
13. ✅ Report legacy vẫn xem/tải được bằng UI/export compatibility path; report v1 có schema/policy/formula/color versions và checksum hợp lệ.
14. ✅ Không có secret, session, email/user profile, raw prompt hoặc claim nguyên nhân giao thông/thời tiết/hiệu quả nhân quả trong persisted report và artifact.

## 4. DEFINITION OF READY / DONE

Task được coi là **Ready để triển khai** khi section 0–1.3 được giữ nguyên hoặc thay đổi qua contract review có version mới. Hệ số seed demo có thể còn provisional nhưng không còn là blocker kỹ thuật: profile bắt buộc version/source/simulator flag, còn thiếu profile thì trả insufficient-data.

Task được coi là **Done** khi:

- B7-05.0→B7-05.7 hoàn tất; ADR 0020, API/domain specs, migration, env docs, frontend types và test fixtures khớp `b7-esg-reports-v1`.
- Unit/integration/security/frontend tests section 2 pass; backend lint, frontend build và `docker compose config --quiet` pass.
- Async-jobs smoke chứng minh daily/weekly/manual idempotency, lease/retry và report completed dù narrative provider hoặc ESG input không khả dụng.
- PDF được render thành ảnh và visual-QA; Markdown/HTML/PDF cùng checksum và không có export recomputation.
- Mọi acceptance criterion có test hoặc bằng chứng manual được ghi; không commit secret/PII/raw prompt.

## 5. RỦI RO CÒN LẠI NHƯNG KHÔNG BLOCK IMPLEMENTATION

- Hệ số airflow/power seed là dữ liệu mô phỏng; trước khi dùng cho quyết định đầu tư phải thay bằng profile được hiệu chuẩn và tăng version.
- Before/after không chứng minh quan hệ nhân quả và có thể bị ảnh hưởng bởi thời tiết/nguồn phát thải ngoài hệ thống; renderer luôn dùng từ “ước tính”.
- QCVN comparison không legally comparable vì simulator không chuẩn hóa µg/Nm³ và không phải quan trắc chứng nhận; v1 cố ý không đưa kết luận below/above cho QCVN.
- ReportLab đáp ứng MVP nhưng ma trận dày có thể cần điều chỉnh typography; nếu chuyển WeasyPrint hoặc engine khác phải có ADR/dependency/image regression riêng.
- `content_checksum_sha256` là integrity marker của nội dung persisted, không phải chữ ký số hoặc bằng chứng chống sửa đổi ngoài hệ thống.

## 6. IMPLEMENTATION EVIDENCE — 29/08/2026

- B7-05.0: ADR 0020, API/domain specs, OpenAPI response models và bốn report policy env vars đã đồng bộ.
- B7-05.1: migration `20260829_007_esg_reports.sql`, checksum/schema metadata,
  `device_operating_profiles`, no-overlap constraint và simulator seed versioned đã chạy lặp lại thành công.
- B7-05.2: coverage half-open/cadence/local timezone/DST, station-day, QCVN/WHO và KPI nội bộ đã có targeted tests.
- B7-05.3: successful correlated ACK intervals, profile coverage, before/final-after windows,
  `boost_baseline_v1`, complete-zero và null/reason-code behavior đã có targeted tests.
- B7-05.4: weekly station/all-stations views đúng 168 cells, unweighted mean, station/coverage gate,
  fixed scale và React N/A hatch/tooltip/selector states đã triển khai.
- B7-05.5: typed claim allow-list, all-or-nothing fallback, canonical SHA-256 và shared publication
  view-model cho Markdown/HTML/PDF/UI đã triển khai; exporter không đọc source data.
- B7-05.6: endpoint/RBAC/CSRF/lease/retry/idempotent identity giữ nguyên; report legacy có compatibility path.
- B7-05.7: report pytest suite 46 tests pass trong container; `npm run test:reports`, frontend build,
  Compose config, migration hai lần, RabbitMQ/Celery worker/Beat smoke và identity reuse pass. PDF A4 ba
  trang đã render 144 DPI và kiểm tra font tiếng Việt, watermark, table split/header, page number,
  clipping, disclaimer và ma trận vector.
- Frontend live QA bằng Manager session đã pass cho cả Daily/Weekly: reports hub truy cập được từ thanh
  công cụ Manager và deep link `/reports`, schema/SHA-256 và weekly matrix hiển thị từ persisted record;
  breakpoint 390x844 không tràn ngang. `npm run test:reports` pass 15 checks và production build pass.

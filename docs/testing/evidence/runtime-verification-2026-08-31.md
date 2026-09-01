# Runtime verification — 31/08/2026

## Metadata

| Trường | Giá trị |
|---|---|
| Branch / commit | `test-report` / `202037e` |
| Môi trường | Docker Desktop, local stack |
| Backend | `http://localhost:8000` |
| Agent | `http://localhost:8001` |
| Frontend | `http://localhost:5173` |
| Dữ liệu | `source=simulator`; không phải quan trắc chính thức |
| Người chạy | Codex automated/runtime verification |

Lưu ý build: `docker compose up -d --build` build được backend/frontend nhưng Agent image mới bị chặn
bởi timeout khi tải `pydantic_core` từ PyPI. Để tiếp tục xác minh chức năng, mã `src/` tại commit trên được
copy vào Agent container dùng dependency image cache ngày 29/08 rồi container được restart. Vì vậy runtime
checks dưới đây là evidence hợp lệ cho mã Agent hiện tại, nhưng **không** thay thế clean-image build gate.

## Stack, pipeline và forecast

- Backend `/health`: HTTP 200, service `airguard-api`, version `0.3.0`.
- Backend `/ready`: HTTP 200, database `ok`.
- Agent `/health`: HTTP 200.
- Frontend: HTTP 200.
- `/api/v1/stations`: đủ S01–S05, online/fresh và `source=simulator` trong scenario normal.
- Trace history S03 có message ID `MSG-cae2219e1f-S03-000003`, `measured_at`, `received_at` và bốn metric đo.
- Forecast S03 24 giờ: 24 horizon, model `extended_additive_fourier_v3`, confidence `0.72`.
- Golden Window trả best/worst window; spatial heatmap hiện tại và +6 giờ đều trả source
  `spatial_idw_dispersion_model`.

## Agent và trình duyệt

- Current, compare và forecast chat: HTTP 200; tool lần lượt gồm `get_current_pm25`,
  `compare_stations`, `get_pm25_forecast`; mỗi response có grounded evidence.
- Prompt yêu cầu bỏ qua Manager và tự bật thiết bị: Agent từ chối, không gọi mutation tool.
- `npm run test:ai-resilience`: 19/19 PASS.
- `npm run test:ai-browser-e2e`: 6/6 PASS, gồm lỗi 503/timeout/network và recovery tương ứng.
- Browser evidence: [`../../../evidence/session-3f/browser_e2e_evidence.json`](../../../evidence/session-3f/browser_e2e_evidence.json)
  và sáu screenshot cùng thư mục.

## Alert, recovery và data-quality gate

1. Scenario `spike` tạo alert thật cho S03:
   - AQI alert `3da1420c-6f05-41f1-9901-f194ba25abf8`.
   - PM2.5 alert `e57cee26-dd01-427f-924b-1502cee9e150`.
2. Scenario `recovery` hạ S03 xuống PM2.5 `27.26`, AQI `83`; active alert S03 về `0`.
3. Scenario `station-silence` đưa S05 về `offline`, `stale`, current PM2.5/AQI là `null` và Agent không
   dùng trạm đó.
4. Phát hiện lỗi release-blocking: forecast S05 vẫn trả HTTP 200, `freshness=fresh` và ba giá trị dự báo
   khi S05 đang offline/stale. Theo data-quality gate, forecast phải bị chặn. Xem `BUG-005`.
5. Bốn test duplicate/stale-forecast cấp validator/storage/Agent PASS. Sau kiểm thử, simulator đã được
   trả về `normal`; S05 trở lại online/fresh.

## HITL, thiết bị và audit

### Reject path

- Proposal `dc90419b-d284-4d93-9a17-cfe24d4ca57a` bắt đầu `pending`, version 1.
- Resident gọi approve nhận HTTP 403.
- Manager reject; proposal thành `rejected`, version 2.
- `latest_command.command_intent_id` trước và sau reject không đổi: không dispatch.

### Approve/ACK path

- Proposal `06458c80-20da-4236-aeab-4a3abfd3be3a` bắt đầu `pending`.
- Manager quick-approve; proposal thành `approved`, version 2.
- Command intent `17178030-7bc3-484f-9d11-f3773bd4da8e`, command `standby`.
- Device command `796b7f54-5a26-50af-a73c-5ea0df23025c`: status và ACK đều `succeeded`.
- Audit có 7 records, gồm `approval.create`, `approval.quick_approve`,
  `device_command.dispatch.prepare`, `device_command.dispatch`, `device_command.ack`.

## Automated regression snapshot

- Fail-fast full suite: 14 PASS rồi FAIL tại dataset TC-16.
- Full suite không hoàn tất: lần chạy tiếp theo bị treo sau khoảng 63% và đã được dừng; không dùng số
  liệu cũ `763 PASS / 20 FAIL` làm kết quả của commit này.
- Scoped route/context/report/frontend group: 122 PASS, 3 FAIL.
- Scoped HITL/device/alert/report group: 103 PASS, 2 FAIL.
- Có 7 failures đã xác nhận tại thời điểm chạy; xem báo cáo hiện hành ở [`../03-test-report.md`](../03-test-report.md#4-defect-và-rủi-ro-còn-mở). Các scoped run có thể
  chồng test; không cộng số PASS thành tổng regression suite.
- `npm run test:reports`: 22 PASS.
- `npm run test:email-snapshots`: PASS tại viewport 375/1280.
- `npm run build`: PASS, 2323 modules.

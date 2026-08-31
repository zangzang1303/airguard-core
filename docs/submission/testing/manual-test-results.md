# Manual Test Results — Runtime Run 31/08/2026

## Run metadata

| Trường | Giá trị |
|---|---|
| Commit | `202037e` |
| Tester | Codex automated/runtime verification; human visual sign-off còn thiếu |
| Ngày/giờ | 31/08/2026, Asia/Bangkok |
| Local URL | Frontend `:5173`, backend `:8000`, Agent `:8001` |
| Browser | Chrome headless qua browser E2E; responsive 375/1280 qua snapshot script |
| `SENSOR_SCENARIO` | `normal` → `spike` → `recovery` → `station-silence` → `normal` |
| Kết luận | **FAIL — còn lỗi data-quality forecast và regression failures** |

Evidence chi tiết, ID và giới hạn môi trường nằm tại
[`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md).
Tài liệu này không thay checklist đầy đủ tại [`../../manual-test-checklist.md`](../../manual-test-checklist.md).

## P0 release checklist

| ID | Luồng bắt buộc | Trạng thái | Evidence/ghi chú |
|---|---|---|---|
| M-01 | Compose startup, health/readiness và frontend access | PASS | Backend health/ready, Agent health và frontend đều HTTP 200. Clean Agent image build vẫn bị PyPI timeout; runtime dùng current source trên cached dependency image. |
| M-02 | S01–S05 simulator → MQTT → DB → API → UI | PASS | API có đủ 5 trạm online/fresh; trace S03 `MSG-cae2219e1f-S03-000003`; browser E2E tải live dashboard. |
| M-03 | Dashboard current/history đa metric | NOT_RUN | API current/history đa metric PASS; chưa thao tác thủ công đủ metric/range trên UI và chưa có screenshot riêng. |
| M-04 | Forecast 1–24h, bounds, Golden Window | NOT_RUN | API 24 horizon, bounds/model/confidence và Golden Window PASS; chưa đối chiếu toàn bộ giá trị trên UI. |
| M-05 | Timeline Play/Pause và spatial heatmap | NOT_RUN | Heatmap API hiện tại/+6 giờ PASS; chưa xác minh trực quan Play/Pause 0→24h. |
| M-06 | Multi-metric alert sau đủ consecutive samples | PASS | Spike tạo AQI/PM2.5 alert S03; recovery đóng toàn bộ alert S03. |
| M-07 | Agent current/compare/forecast có grounding | PASS | Ba prompt HTTP 200, đúng tool và có evidence; browser E2E 6/6 PASS. |
| M-08 | Personalized route và indoor fallback | NOT_RUN | Chưa sign-off live; còn 3 route failures đã xác nhận trong regression. |
| M-09 | Agent/backend fail closed khi stale/offline/outage | FAIL | Current và Agent chặn S05 offline, resilience 19/19 PASS; forecast vẫn trả dữ liệu fresh cho S05 offline (`BUG-005`). |
| M-10 | Proposal bắt đầu pending, Resident nhận 403 | PASS | Proposal `dc90419b-...` pending v1; Resident approve nhận 403. |
| M-11 | Reject không dispatch | PASS | Proposal trên rejected v2; latest command intent trước/sau không đổi. |
| M-12 | Approve → dispatch → ACK đúng command ID | PASS | Proposal `06458c80-...`; intent `17178030-...`; command `796b7f54-...` ACK succeeded. |
| M-13 | Agent từ chối bypass HITL | PASS | Agent từ chối tự approve/bật thiết bị; không mutation tool. |
| M-14 | Audit create/review/dispatch/failure đầy đủ | PASS | Chuỗi approve có 7 audit records từ create đến ACK; không ghi secret trong evidence. |
| M-15 | Report daily/weekly và Markdown/HTML/PDF | FAIL | Export/report scoped tests phần lớn PASS nhưng còn 2 report contract failures (`BUG-002`). |
| M-16 | Duplicate, station-silence và recovery | PASS | 4 duplicate/stale unit tests PASS; live S05 offline/stale rồi trở lại online/fresh; recovery alert PASS. |
| M-17 | Retest Agent chat UI failure ngày 24/08 | PASS | Browser E2E 6/6; 503/timeout/network và recovery đều render đúng, có screenshots. |

## P1 checklist

| ID | Luồng nâng cao | Trạng thái | Evidence/ghi chú |
|---|---|---|---|
| M-18 | Ba nhóm user nhận khuyến nghị đúng policy | NOT_RUN | Chưa so sánh live normal/sensitive/outdoor_sport. |
| M-19 | Notification disabled và provider configured | NOT_RUN | Automated notification cases PASS; chưa có quyền/provider thật để chứng minh inbox delivery. |
| M-20 | PDF tiếng Việt, watermark, matrix và page break | NOT_RUN | Email snapshots 375/1280 PASS; chưa render/soát thủ công mọi trang PDF. |
| M-21 | Responsive UI/mobile | NOT_RUN | Email snapshot 375/1280 PASS; chưa duyệt thủ công tất cả major views. |
| M-22 | Public URL incognito, HTTPS/CORS | NOT_RUN | Chưa có final public URL. |

## Evidence còn cần người kiểm tra

- [ ] Chụp dashboard current/history khi đổi metric và time range.
- [ ] Chụp forecast/Golden Window/timeline; thao tác Play/Pause.
- [ ] Chạy personalized route và indoor fallback sau khi sửa `BUG-001`.
- [ ] Render và soát PDF tiếng Việt sau khi sửa `BUG-002`.
- [ ] Kiểm tra toàn bộ major views ở 375px/1280px.
- [ ] Kiểm tra public URL incognito, HTTPS và CORS khi URL đã freeze.

## Final sign-off

- [ ] Sửa/retest `BUG-001`, `BUG-002`, `BUG-003` và `BUG-005`.
- [ ] Full pytest hoàn tất, không treo và không còn failure chưa disposition.
- [ ] Hoàn thành các mục UI/public URL còn `NOT_RUN`.
- [ ] QA Lead, Technical Lead và Product/Team Lead ký duyệt trên final commit.

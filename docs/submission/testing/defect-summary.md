# Defect and Blocker Summary — 31/08/2026

## Tổng quan

Full command `.\.venv\Scripts\python.exe -m pytest tests -q` trên commit `a939966` cho kết quả:

- 763 passed.
- 20 failed.
- 2 warnings.
- 35.95 giây.

Các mục dưới đây là kết quả quan sát, chưa khẳng định nguyên nhân gốc cho đến khi owner điều tra.

## Automated failure groups

| Nhóm | Số failure | Quan sát | Owner/next step |
|---|---:|---|---|
| Comprehensive Agent dataset | 1 | TC-16 expected route intent nhưng nhận `insufficient_data`. | Agent/route owner kiểm tra fixture và data-quality gate. |
| Contextual geospatial Agent | 5 | Route/follow-up/forecast cases thiếu usable grounded station data hoặc sai intent. | Backend Agent owner điều tra snapshot/history contract. |
| Deep conversation context | 6 | Offer/slot/modify/social-resume flows thất bại, một số đường đi gọi DB chưa cấu hình. | Conversation + route owner kiểm tra request-scoped dependencies. |
| Geospatial Agent | 4 | Dynamic ranking/route intent/distance follow-up và 3 km precision không khớp. | Route owner retest data injection và distance synthesis. |
| Report generator | 2 | Fallback narrative assertion và stored-record export assertion không khớp. | Report owner xác nhận contract/ngôn ngữ/escaping. |
| Running route engine | 1 | Distance/detour precision nhận `insufficient_data`. | Route owner điều tra cùng nhóm geospatial. |
| Ventilation frontend contract | 1 | Test còn kỳ vọng `requestProposal("eco_mode")` trong drawer. | Frontend/HITL owner xác nhận UI mới hay regression. |

## Environment blockers

| ID | Blocker | Trạng thái | Cách gỡ |
|---|---|---|---|
| ENV-01 | Docker Compose không có container đang chạy. | OPEN | Start final stack rồi chạy health/manual/browser E2E. |
| ENV-02 | `test:ai-resilience` live pass-through nhận 503. | BLOCKED BY ENV-01 | Retest khi backend/Agent healthy. |
| ENV-03 | `test:email-snapshots` yêu cầu runtime container đang chạy. | BLOCKED BY ENV-01 | Khởi động dependency/container theo script rồi retest. |
| ENV-04 | `test:ai-browser-e2e` chưa chạy. | BLOCKED BY ENV-01 | Chạy trên final live stack. |
| ENV-05 | `npm ci` báo 1 high severity advisory. | OPEN | Chạy audit review; không auto-fix khi chưa đánh giá breaking change. |

## Historical issue requiring retest

[`../../ui-test-report-2026-08-24.md`](../../ui-test-report-2026-08-24.md) ghi UI Agent request thất bại trong
khi backend API trực tiếp PASS. Vì code đã thay đổi sau ngày đó, trạng thái phù hợp là **NEEDS RETEST**, không
được tự coi là fixed hoặc vẫn-failing nếu chưa có lần chạy mới.

## Release-blocking policy

Không sign-off nếu còn một trong các lỗi sau:

- Agent bịa số liệu hoặc dùng dữ liệu ngoài backend evidence cùng request.
- Dữ liệu invalid/stale/offline vẫn dùng cho current/forecast/alert/proposal.
- Resident approve/reject hoặc device dispatch trước Manager approval.
- Report/export tính lại thành số liệu khác persisted record.
- Secret, token, email người nhận hoặc raw prompt xuất hiện trong evidence/audit.

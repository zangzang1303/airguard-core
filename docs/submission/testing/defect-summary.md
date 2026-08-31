# Defect and Blocker Summary — 31/08/2026

## Tổng quan hiện tại

Code được kiểm tra tại branch `test-report`, commit `202037e`.

- Full `pytest tests -q` chưa hoàn tất: tiến trình bị treo sau khoảng 63% và được dừng.
- Fail-fast run: 14 PASS, sau đó FAIL tại Phase31 dataset TC-16.
- Scoped route/context/report/frontend: 122 PASS, 3 FAIL.
- Scoped HITL/device/alert/report: 103 PASS, 2 FAIL.
- Hai scoped run có phần test chồng nhau; không cộng số PASS thành tổng suite.
- Có 7 failures đã xác nhận trong Sheet, nhưng chưa coi đây là tổng cuối cho đến khi full suite chạy xong.

## Confirmed failure groups

| Nhóm | Số failure | Quan sát | Owner/next step |
|---|---:|---|---|
| Agent route contract | 3 | TC-16 sai intent; validation thiếu `activity`; route-service failure không fail closed | Agent/route owner đồng bộ signature, injection và insufficient-data contract |
| Report generator/export | 2 | Fallback narrative assertion và stored export marker không khớp | Report owner chốt ngôn ngữ/escaping contract rồi sửa/retest |
| Ventilation frontend contract | 1 | Drawer thiếu eco-mode proposal action mà test yêu cầu | Frontend/HITL owner xác nhận UI mới hay regression |
| Offline forecast gate | 1 | Forecast trả dữ liệu fresh cho S05 offline/stale | Backend forecast owner thêm station-quality gate; P0 release blocker |

## Resolved/retested groups

- 15 route/context cases `PY-002`–`PY-016` và route precision `PY-019`: PASS sau merge `main`.
- AI resilience: 19/19 PASS trên live stack.
- Browser Agent E2E: 6/6 PASS; historical UI issue ngày 24/08 được đóng.
- Email snapshots: 375/1280 PASS.
- Compose runtime: backend ready, Agent healthy, frontend HTTP 200.
- Alert spike/recovery và HITL pending → reject/approve → dispatch → ACK/audit: PASS.

## Environment blocker còn lại

| ID | Blocker | Trạng thái | Cách gỡ |
|---|---|---|---|
| ENV-004 | Clean Agent image build timeout khi tải `pydantic_core` từ PyPI | BLOCKED | Rerun build khi PyPI/network ổn định; không dùng cached-image runtime để ký clean-build gate |
| SEC-001 | Một npm high-severity advisory chưa disposition | OPEN | Review `npm audit`, fix hoặc ghi risk acceptance có owner |

## Release-blocking policy

Không sign-off nếu còn một trong các lỗi sau:

- Agent bịa số liệu hoặc không fail closed khi route/tool lỗi.
- Data invalid/stale/offline vẫn dùng cho current, forecast, alert hoặc proposal.
- Resident approve/reject hoặc device dispatch trước Manager approval.
- Report/export không giữ cùng persisted record và checksum.
- Secret, token, email người nhận hoặc raw prompt xuất hiện trong evidence/audit.

Evidence runtime: [`evidence/runtime-verification-2026-08-31.md`](evidence/runtime-verification-2026-08-31.md).

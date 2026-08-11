# Backlog 1 — Frontend

## Cách tích checklist

- `[ ]` = chưa làm hoặc chưa kiểm thử.
- Đổi thành `[x]` khi component đã nối API thật, có loading/error/empty state và build pass.
- Với task Figma, chỉ tích sau khi đã kiểm tra màn hình trên trình duyệt và lưu screenshot.
- Nếu chỉ hoàn thành giao diện nhưng chưa nối API, ghi `PARTIAL`, không tích `[x]`.

**Owner:** Frontend lead  
**Mục tiêu:** React dashboard hiển thị dữ liệu API thật, không truy cập MQTT/DB trực tiếp.

## FE-001 — Auth và shell

- [ ] Login/register demo, role visibility Resident/Manager/Admin.
- [ ] AppShell/AdminShell, simulator banner, navigation và responsive drawer.
- [ ] Không tự tuyên bố production authentication khi provider chưa chốt.

## FE-002 — Dashboard/stations

- [ ] Map/list S01–S05 từ API.
- [ ] Current PM2.5, status, source, freshness và popup/detail.
- [ ] History/forecast/compare dùng response backend, không fixture live.

## FE-003 — Alerts/Agent

- [ ] Alert list/filter/severity/active-resolved.
- [ ] Agent chat hiển thị tool/source/freshness và structured error.
- [ ] Proposal detail hiển thị evidence, rationale, policy và pending state.

## FE-004 — Manager/Admin

- [ ] Approval queue/detail; gửi đúng user/role/version; dùng server result.
- [ ] Audit log read-only.
- [ ] Admin dashboard, station, user, IoT và settings theo RBAC.

## FE-005 — Figma conversion

- [ ] Map từng frame Figma vào component hiện có.
- [ ] Không copy đè API client hoặc bypass HITL.
- [ ] Căn layout, typography, colors, spacing; chụp screenshot so sánh.

## FE-006 — UX quality

- [ ] Loading, empty, error 401/403/409/503/network.
- [ ] Keyboard focus, contrast, mobile/tablet/1280px.
- [ ] Simulator/source disclaimer luôn hiển thị.

## Kiểm thử

```powershell
npm.cmd --prefix frontend run build
```

Evidence gồm screenshot Dashboard, Alert, Approval, Audit và Admin Overview khi API live.

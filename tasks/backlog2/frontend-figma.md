# Backlog 2B — Frontend + Figma

## Cách tích checklist

- `[ ]` = chưa chuyển/chưa kiểm tra.
- Đổi thành `[x]` khi frame Figma đã thành component React, nối API thật và build pass.
- Mỗi màn hình cần kiểm tra loading/empty/error và screenshot ở viewport phù hợp.
- Chuyển giao diện nhưng không được tự tạo dữ liệu live hoặc bypass HITL.

**Owner:** Thành viên Frontend  
**Mục tiêu:** chuyển dần toàn bộ Figma sang React hiện có nhưng giữ API thật và RBAC server-side.

## Nhiệm vụ

### B2-FE-01 — Foundation/shell

- [ ] Giữ `frontend/src/main.tsx` làm entrypoint; không dùng legacy `App.jsx`.
- [ ] Hoàn thiện AppShell/AdminShell theo design token Figma.
- [ ] Căn sidebar, header, simulator banner, typography, spacing và colors.
- [ ] Test 1280px, tablet và mobile.

### B2-FE-02 — Resident screens

- [ ] Dashboard: map 5 station, KPI, freshness/source.
- [ ] Station Detail: current, history, forecast, status.
- [ ] Compare Stations: so sánh API thật.
- [ ] AI Chat: hiển thị tool/source/freshness và proposal state.
- [ ] Alert List: filter, severity, active/resolved, error/empty state.
- [ ] Proposal Detail: evidence, rationale, pending state.
- [ ] Profile: user profile API, role và group.
- [ ] Error states: loading, 401, 403, 409, 503, network error.

### B2-FE-03 — Admin screens

- [ ] Admin Overview.
- [ ] Station Management.
- [ ] Station Detail.
- [ ] Alert Management.
- [ ] HITL Approval Queue/Detail.
- [ ] User and Role Management.
- [ ] Audit Logs.
- [ ] System Settings.

### B2-FE-04 — API and safety

- [ ] Không fallback sang fake live data khi API lỗi.
- [ ] Không tự tính business alert ở client.
- [ ] Không gọi MQTT hoặc PostgreSQL từ frontend.
- [ ] Approval request gửi đúng role/user/version và hiển thị server result.
- [ ] Audit chỉ read-only.

### B2-FE-05 — Visual evidence

- [ ] Chụp screenshot Dashboard, Alert, Approval, Audit và Admin Overview.
- [ ] So sánh với frame Figma tương ứng.
- [ ] Ghi sai lệch còn lại vào `docs/` hoặc `.ai-log/`.
- [ ] Chạy `npm.cmd --prefix frontend run build`.

## Acceptance

- Không còn placeholder trong các màn hình thuộc MVP scope.
- Mọi màn hình có loading/empty/error state.
- UI hiển thị rõ `[SIMULATOR]`, source và freshness.
- Responsive không làm mất action quan trọng hoặc bypass HITL.

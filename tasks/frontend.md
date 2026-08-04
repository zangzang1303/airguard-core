# Công việc Frontend

## Mục tiêu và phạm vi

Xay dung dashboard React + TypeScript cho nguoi dung xem PM2.5 5 tram, alerts, Trò chuyện với Agent va manager review proposal. Frontend chi giao tiep qua backend REST/job APIs; tuyet doi khong subscribe MQTT va khong tu suy dien alert o client.

## Thứ tự thực hiện

`FE-001 -> FE-002 -> FE-003 -> FE-004 -> FE-005 -> FE-006 -> FE-007`.

## Đặc tả màn hình

Dung [specs/frontend-screen-spec.md](../specs/frontend-screen-spec.md) lam tai lieu handoff canonical cho danh sach man hinh, route, user flow, field/button/table, validation, loading/empty/error states, role visibility va Figma checklist. Neu tai lieu nay yeu cau API/schema chua co trong [specs/api-contracts.md](../specs/api-contracts.md), phai chot contract truoc khi implement production UI.

## Demo auth UI (implemented, production contract pending)

- Login va Resident registration da co de review luong va responsive theo Figma S01/S01B.
- Ba identity Resident/Manager/Admin duoc seed trong frontend; role read-only va dieu khien navigation demo.
- Tai khoan dang ky moi chi ton tai in-memory va luon la Resident.
- Chua co production session, password storage, email verification hay server-side RBAC; khong duoc tuyen bo auth da production-ready truoc khi API/provider contract duoc chot.

## FE-001 - Bản đồ dashboard 5 trạm

**Mục tiêu:** render ban do va station list tu API chinh thuc.

**Thực hiện:**

1. Khoi tao structure: routes, feature folders, typed API client, environment `VITE_API_BASE_URL`, error boundary.
2. Dinh nghia TypeScript types theo API: Station, Measurement, Alert, Approval, AgentResponse.
3. Tich hop React Leaflet + OSM; dat center/zoom phu hop khu VinUni/Vinhomes Ocean Park.
4. Goi `GET /api/v1/stations`, render marker va station list tu cung mot state.
5. Tao loading skeleton, empty state va failure state co retry; fallback demo chi duoc dung khi gan nhan ro la fixture.
6. Khong hard-code toa do/PM2.5 trong component production.

**Đầu ra:** map 5 marker, list dong bo va API client co typing.

**Kiểm thử:** response thanh cong, 0 items, network error, toa do missing/sai va marker selection.

**Hoàn thành khi:** chay voi backend sach va thay du 5 tram seed tren map.

## FE-002 - Chi tiết trạm và độ mới dữ liệu

**Mục tiêu:** nguoi dung biet gia tri, thoi diem va do tin cay cua data.

**Thực hiện:**

1. Them popup/side panel: station name/id, PM2.5, unit, level, status, source va updated_at.
2. Quy uoc time format theo `Asia/Ho_Chi_Minh`; khong hien "now" neu timestamp la fixture.
3. Hien badge `online`, `offline`, `stale`, `invalid`; stale/offline co thong diep de hieu.
4. Them label co dinh "Du lieu gia lap cho MVP - khong phai quan trac chinh thuc".
5. Tu station click goi current/history khi can; cancel request cu khi doi station nhanh.

**Đầu ra:** detail panel minh bach ve freshness va source.

**Kiểm thử:** timestamp moi/cu, timezone, data null, station offline, stale, invalid va API error.

**Hoàn thành khi:** khong co UI state nao trinh bay data cu hoac fixture nhu live official data.

## FE-003 - Mức độ nghiêm trọng và trạng thái marker

**Mục tiêu:** mau sac nhat quan voi Rule Engine va de hieu tren map/list.

**Thực hiện:**

1. Lay `severity/level` tu backend hoac dung shared threshold config da duoc chot, khong viet lai rule thu cong.
2. Tao color tokens va legend cho good/moderate/warning/critical.
3. Uu tien visual state: invalid > offline > stale > PM2.5 severity.
4. Dung icon/pattern/text de khong phu thuoc mau duy nhat; dam bao contrast.
5. Cap nhat marker, list, popup va alert link bang mot display mapper dung chung.

**Đầu ra:** design token va component hien thi status dung chung.

**Kiểm thử:** cac boundary threshold, high contrast, color blindness, keyboard focus va screenshot regression.

**Hoàn thành khi:** map/list/popup khong mau thuan mau hoac severity cho cung station.

## FE-004 - Khu vực cảnh báo

**Mục tiêu:** theo doi va dieu huong active alerts ma khong tao logic alert o client.

**Thực hiện:**

1. Goi `GET /alerts` voi filter status/station/severity, them loading/error/empty states.
2. Hien severity, title, station, observed value, threshold, created time, status.
3. Click alert focus marker va mo station detail; cho phep loc/sort theo severity va moi nhat.
4. Chon polling interval duoc nhom xac nhan; hien `last refreshed` va manual refresh icon button.
5. Chi manager role moi thay action resolve neu backend cung cap.

**Đầu ra:** alert panel co trace den station va accessible filter controls.

**Kiểm thử:** duplicate API records, empty, service 503, filter combinations, active/resolved va refresh race.

**Hoàn thành khi:** alert spike co the duoc tim thay va mo tu dashboard trong toi da ba thao tac.

## FE-005 - Trò chuyện với Agent

**Mục tiêu:** gui cau hoi ve moi truong qua backend va trinh bay answer co grounding.

**Thực hiện:**

1. Tao chat composer, message list, loading/sending state, cancel/retry va input validation.
2. Goi agent synchronous/job endpoint; poll job status neu API tra 202.
3. Render text an toan, khong dung `dangerouslySetInnerHTML`; support copy va focus management.
4. Hien source/time/used tools o panel debug duoc bat bang environment flag, khong phoi ra noi dung noi bo cho end user.
5. Hien ro khi Agent thieu data, tool loi, data stale hoac cau hoi nam ngoai scope.
6. Khong tu chen PM2.5, forecast hay recommendation vao response o client.

**Đầu ra:** chat flow co request id, retry va UI cho grounded response.

**Kiểm thử:** empty input, long message, 4xx/5xx, timeout, malformed response, tool failure va mobile keyboard.

**Hoàn thành khi:** 3 prompt demo dung tool response thanh cong va 1 prompt thieu data refusal dung.

## FE-006 - Phê duyệt của quản lý

**Mục tiêu:** manager review proposal minh bach va khong the vo tinh dispatch command.

**Thực hiện:**

1. Tao pending queue, filter status, detail drawer/page: rationale, evidence, target, requested action, created by/time.
2. Goi approvals API; approve/reject phai co confirmation modal va loading state.
3. Reject note bat buoc khi policy yeu cau; validate truoc submit.
4. Disable action sau submit, xu ly `409` bang reload current server state.
5. An/redirect theo role nhung van dua vao backend RBAC; hien audit history read-only.
6. Neu command outcome failed, hien dung failure state, khong bao "da thuc thi".

**Đầu ra:** manager workspace va state transitions phan anh server.

**Kiểm thử:** approve, reject, 403, 409, network error, double click, pending empty va audit unavailable.

**Hoàn thành khi:** pending proposal khong the tu nhien bien thanh approved tren client.

## FE-007 - Responsive, khả năng truy cập và hoàn thiện demo

**Mục tiêu:** luong demo on dinh tren desktop va mobile, khong co thong tin gay hieu nham.

**Thực hiện:**

1. Kiem tra 1440x900, 1024x768, 768x1024 va 375x812; map/list/chat/approval khong overlap.
2. Kiem tra keyboard tab order, focus trap modal, aria labels, contrast, screen-reader labels cho marker/actions.
3. Them skeleton/no data/error cho moi screen; khong de blank screen khi API loi.
4. Viet Playwright smoke: load dashboard, open station, see alert, send chat stub, approve/reject fixture.
5. Chay screenshot review truoc rehearsal va chot known limitations.
6. Dung Page Header duy nhat cho moi route; chuan hoa Lucide icon va button hierarchy, khong dung emoji lam icon UI.

**Đầu ra:** test checklist, screenshots va demo-ready UI.

**Hoàn thành khi:** cac man hinh chinh khong co overflow/overlap va luong demo hoan thanh tren browser muc tieu.

## Mốc và phụ thuộc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | FE-001..FE-003 | BE-001..BE-003, station seed |
| 08/08 | FE-004..FE-007 | Alert, Agent, Approvals APIs |

## Tiêu chí hoàn thành chung

- Khong co MQTT client, broker credential hay business rule alert trong frontend.
- Moi API screen co loading, empty, error va retry state.
- Copy UI phan biet data simulator va khong dua ra chan doan y te.


## Bản đồ file theo task

| Task | File hiện có cần sửa | File/directory cần tạo hoặc cập nhật | Tài liệu và test liên quan |
|---|---|---|---|
| FE-001 | `frontend/src/App.jsx`, `frontend/src/main.jsx` | `frontend/src/api/client.js`, `frontend/src/features/stations/` | `frontend/src/**/*.test.*`, `specs/api-contracts.md`, `specs/frontend-screen-spec.md` |
| FE-002 | `frontend/src/App.jsx`, `frontend/src/styles.css` | `frontend/src/features/stations/StationDetail.jsx` | `tasks/frontend.md`, `specs/frontend-screen-spec.md`, screenshot test |
| FE-003 | `frontend/src/App.jsx` | `frontend/src/features/stations/statusDisplay.js` | `specs/acceptance-criteria.md`, `specs/frontend-screen-spec.md` |
| FE-004 | `frontend/src/App.jsx` | `frontend/src/features/alerts/` | `specs/api-contracts.md`, `specs/frontend-screen-spec.md`, UI smoke test |
| FE-005 | `frontend/src/App.jsx` | `frontend/src/features/agent/`, `frontend/src/api/agent.js` | `docs/agent-evaluation.md`, `specs/frontend-screen-spec.md` |
| FE-006 | `frontend/src/App.jsx` | `frontend/src/features/approvals/` | `specs/api-contracts.md`, `specs/frontend-screen-spec.md`, approval UI test |
| FE-007 | `frontend/src/styles.css` | `frontend/e2e/`, Playwright config nếu được chọn | `docs/test-plan.md`, `docs/demo-runbook.md`, `specs/frontend-screen-spec.md` |

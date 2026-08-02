# Frontend Tasks

## Muc tieu va pham vi

Xay dung dashboard React + TypeScript cho nguoi dung xem PM2.5 5 tram, alerts, Agent chat va manager review proposal. Frontend chi giao tiep qua backend REST/job APIs; tuyet doi khong subscribe MQTT va khong tu suy dien alert o client.

## Thu tu thuc hien

`FE-001 -> FE-002 -> FE-003 -> FE-004 -> FE-005 -> FE-006 -> FE-007`.

## FE-001 - Dashboard map 5 tram

**Muc tieu:** render ban do va station list tu API chinh thuc.

**Thuc hien:**

1. Khoi tao structure: routes, feature folders, typed API client, environment `VITE_API_BASE_URL`, error boundary.
2. Dinh nghia TypeScript types theo API: Station, Measurement, Alert, Approval, AgentResponse.
3. Tich hop React Leaflet + OSM; dat center/zoom phu hop khu VinUni/Vinhomes Ocean Park.
4. Goi `GET /api/v1/stations`, render marker va station list tu cung mot state.
5. Tao loading skeleton, empty state va failure state co retry; fallback demo chi duoc dung khi gan nhan ro la fixture.
6. Khong hard-code toa do/PM2.5 trong component production.

**Dau ra:** map 5 marker, list dong bo va API client co typing.

**Kiem thu:** response thanh cong, 0 items, network error, toa do missing/sai va marker selection.

**Xong khi:** chay voi backend sach va thay du 5 tram seed tren map.

## FE-002 - Station detail va freshness

**Muc tieu:** nguoi dung biet gia tri, thoi diem va do tin cay cua data.

**Thuc hien:**

1. Them popup/side panel: station name/id, PM2.5, unit, level, status, source va updated_at.
2. Quy uoc time format theo `Asia/Ho_Chi_Minh`; khong hien "now" neu timestamp la fixture.
3. Hien badge `online`, `offline`, `stale`, `invalid`; stale/offline co thong diep de hieu.
4. Them label co dinh "Du lieu gia lap cho MVP - khong phai quan trac chinh thuc".
5. Tu station click goi current/history khi can; cancel request cu khi doi station nhanh.

**Dau ra:** detail panel minh bach ve freshness va source.

**Kiem thu:** timestamp moi/cu, timezone, data null, station offline, stale, invalid va API error.

**Xong khi:** khong co UI state nao trinh bay data cu hoac fixture nhu live official data.

## FE-003 - Severity va marker states

**Muc tieu:** mau sac nhat quan voi Rule Engine va de hieu tren map/list.

**Thuc hien:**

1. Lay `severity/level` tu backend hoac dung shared threshold config da duoc chot, khong viet lai rule thu cong.
2. Tao color tokens va legend cho good/moderate/warning/critical.
3. Uu tien visual state: invalid > offline > stale > PM2.5 severity.
4. Dung icon/pattern/text de khong phu thuoc mau duy nhat; dam bao contrast.
5. Cap nhat marker, list, popup va alert link bang mot display mapper dung chung.

**Dau ra:** design token va component hien thi status dung chung.

**Kiem thu:** cac boundary threshold, high contrast, color blindness, keyboard focus va screenshot regression.

**Xong khi:** map/list/popup khong mau thuan mau hoac severity cho cung station.

## FE-004 - Alerts workspace

**Muc tieu:** theo doi va dieu huong active alerts ma khong tao logic alert o client.

**Thuc hien:**

1. Goi `GET /alerts` voi filter status/station/severity, them loading/error/empty states.
2. Hien severity, title, station, observed value, threshold, created time, status.
3. Click alert focus marker va mo station detail; cho phep loc/sort theo severity va moi nhat.
4. Chon polling interval duoc nhom xac nhan; hien `last refreshed` va manual refresh icon button.
5. Chi manager role moi thay action resolve neu backend cung cap.

**Dau ra:** alert panel co trace den station va accessible filter controls.

**Kiem thu:** duplicate API records, empty, service 503, filter combinations, active/resolved va refresh race.

**Xong khi:** alert spike co the duoc tim thay va mo tu dashboard trong toi da ba thao tac.

## FE-005 - Agent chat

**Muc tieu:** gui cau hoi ve moi truong qua backend va trinh bay answer co grounding.

**Thuc hien:**

1. Tao chat composer, message list, loading/sending state, cancel/retry va input validation.
2. Goi agent synchronous/job endpoint; poll job status neu API tra 202.
3. Render text an toan, khong dung `dangerouslySetInnerHTML`; support copy va focus management.
4. Hien source/time/used tools o panel debug duoc bat bang environment flag, khong phoi ra noi dung noi bo cho end user.
5. Hien ro khi Agent thieu data, tool loi, data stale hoac cau hoi nam ngoai scope.
6. Khong tu chen PM2.5, forecast hay recommendation vao response o client.

**Dau ra:** chat flow co request id, retry va UI cho grounded response.

**Kiem thu:** empty input, long message, 4xx/5xx, timeout, malformed response, tool failure va mobile keyboard.

**Xong khi:** 3 prompt demo dung tool response thanh cong va 1 prompt thieu data refusal dung.

## FE-006 - Manager approvals

**Muc tieu:** manager review proposal minh bach va khong the vo tinh dispatch command.

**Thuc hien:**

1. Tao pending queue, filter status, detail drawer/page: rationale, evidence, target, requested action, created by/time.
2. Goi approvals API; approve/reject phai co confirmation modal va loading state.
3. Reject note bat buoc khi policy yeu cau; validate truoc submit.
4. Disable action sau submit, xu ly `409` bang reload current server state.
5. An/redirect theo role nhung van dua vao backend RBAC; hien audit history read-only.
6. Neu command outcome failed, hien dung failure state, khong bao "da thuc thi".

**Dau ra:** manager workspace va state transitions phan anh server.

**Kiem thu:** approve, reject, 403, 409, network error, double click, pending empty va audit unavailable.

**Xong khi:** pending proposal khong the tu nhien bien thanh approved tren client.

## FE-007 - Responsive, a11y va demo hardening

**Muc tieu:** luong demo on dinh tren desktop va mobile, khong co thong tin gay hieu nham.

**Thuc hien:**

1. Kiem tra 1440x900, 1024x768, 768x1024 va 375x812; map/list/chat/approval khong overlap.
2. Kiem tra keyboard tab order, focus trap modal, aria labels, contrast, screen-reader labels cho marker/actions.
3. Them skeleton/no data/error cho moi screen; khong de blank screen khi API loi.
4. Viet Playwright smoke: load dashboard, open station, see alert, send chat stub, approve/reject fixture.
5. Chay screenshot review truoc rehearsal va chot known limitations.

**Dau ra:** test checklist, screenshots va demo-ready UI.

**Xong khi:** cac man hinh chinh khong co overflow/overlap va luong demo hoan thanh tren browser muc tieu.

## Moc va phu thuoc

| Moc | Bat buoc | Phu thuoc chinh |
|---|---|---|
| 05/08 | FE-001..FE-003 | BE-001..BE-003, station seed |
| 08/08 | FE-004..FE-007 | Alert, Agent, Approvals APIs |

## DoD chung

- Khong co MQTT client, broker credential hay business rule alert trong frontend.
- Moi API screen co loading, empty, error va retry state.
- Copy UI phan biet data simulator va khong dua ra chan doan y te.

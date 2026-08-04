# Frontend Screen Specification

## 1. Muc dich va pham vi

Tai lieu nay la dac ta tap trung de ban giao giua Product, Design, Frontend va Backend cho AirGuard AI. No tra loi cho moi man hinh: ai duoc xem, muc dich, du lieu, truong nhap, nut bam, validation, trang thai va API phu thuoc.

Thu tu uu tien:

- `P0` (Gate 05/08/2026): Dashboard, danh sach/chi tiet tram, source/freshness/data-quality states.
- `P1` (Gate 08/08/2026): Alerts, Agent, forecast, warning proposal, approval/rejection va audit.
- `P2` (sau MVP hoac khi Mentor/nhom xac nhan): dang ky tai khoan, auth provider production, notification preference, device-dispatch UX nang cao.

Tai lieu nay khong tu tao backend capability. Neu mot man hinh chua co endpoint/schema trong [api-contracts.md](api-contracts.md), UI phai duoc danh dau `contract pending` va khong duoc mo phong nhu capability da hoat dong.

## 2. Nguyen tac UI bat buoc

1. Moi man hinh co environmental data phai hien nhan co dinh: **"Du lieu gia lap cho MVP - khong phai quan trac chinh thuc."**
2. PM2.5, weather, forecast, alert, timestamp va recommendation chi render tu response cua backend trong cung request/job. Frontend khong tu dien gia tri.
3. Frontend khong subscribe MQTT va khong tu tinh alert rule. `level`/`severity` den tu backend hoac shared policy da duoc duyet.
4. Uu tien hien thi data quality: `invalid > offline > stale > severity`.
5. PM2.5 co the `null`; UI hien ly do khong kha dung, khong thay bang `0` va khong tinh vao aggregate.
6. Timestamp hien theo `Asia/Ho_Chi_Minh`, co timezone trong detail/debug. Phan biet `measured/updated time` voi `last refreshed` cua UI.
7. Source simulator/fixture phai luon nhin thay. Khong dung cac copy "official", "certified" hoac "live monitoring".
8. Action phan quyen chi an/hien de cai thien UX; backend RBAC van la quyet dinh cuoi cung.
9. Moi API surface co `loading`, `empty`, `error` va `retry`; action mutation co `submitting`, `success`, `conflict` va `failure` khi phu hop.
10. Khong render Agent answer bang `dangerouslySetInnerHTML`; content, link va markdown phai duoc sanitize/allowlist.
11. Moi route chi co mot Page Header ben duoi breadcrumb, gom H1, mo ta ngan va page action ben phai; khong dung eyebrow/tag de lap lai section name.
12. Emoji khong duoc dung lam UI icon. Dung Lucide icon voi accessible label; button theo hierarchy `primary`, `outline`, `ghost/icon`, `destructive`.

## 3. Vai tro va navigation

### 3.1 Access matrix

| Surface/action | Resident | Manager | Admin |
|---|---:|---:|---:|
| Dashboard, station current/history | Yes | Yes | Yes |
| Compare stations | Yes | Yes | Yes |
| Agent chat va grounded evidence | Yes | Yes | Yes |
| Alert list/detail | Yes | Yes | Yes |
| Resolve alert | No | Chi khi backend policy cho phep | Yes |
| Proposal queue/detail | No | Yes | Yes |
| Approve/reject pending proposal | No | Yes | Yes |
| Audit log | No | Limited scope | Full scope |
| Edit own user group | Yes | Yes | Yes |
| User/system administration | No | No | P2/not in current MVP UI |

### 3.2 App shell variants

**Resident navigation:** Dashboard, AI Agent, Canh bao, Ho so, Dang xuat.

**Manager/Admin navigation:** Dashboard, AI Agent, Canh bao, Phe duyet, Audit Log, Ho so, Dang xuat. `Phe duyet` co pending-count badge neu backend tra du lieu.

Khong render action approve/reject, audit hoac resolve cho Resident. Truy cap URL truc tiep phai nhan `403`/redirect theo auth contract, khong chi dua vao hidden navigation.

## 4. Danh sach man hinh va route de xuat

| ID | Man hinh | Route de xuat | Role | Priority |
|---|---|---|---|---|
| S00 | UI Flow/Design index | Figma only | Team | Documentation |
| S01 | Login/Demo access | `/login` | Public | P1 dependency |
| S01B | Dang ky cu dan | `/register` | Public | P2/optional |
| S02 | Dashboard | `/dashboard` | All authenticated | P0 |
| S03 | Chi tiet tram | `/stations/:stationId` | All authenticated | P0 |
| S04 | So sanh khu vuc | `/compare` | All authenticated | P1 |
| S05 | AI Agent Chat | `/agent` | All authenticated | P1 |
| S06 | Danh sach canh bao | `/alerts` | All authenticated | P1 |
| S07 | Chi tiet Proposal | `/approvals/:proposalId` | Manager/Admin | P1 |
| S08 | Danh sach phe duyet | `/approvals` | Manager/Admin | P1 |
| S09A/B | Ket qua phe duyet | `/approvals/:proposalId/result` hoac state cua S07 | Manager/Admin | P1 |
| S10 | Audit Log | `/audit` | Manager/Admin | P1 |
| S11 | Ho so nguoi dung | `/profile` | All authenticated | P1 |
| S12 | Error/Empty State Inventory | Khong nam trong production nav | Team | Documentation |
| E401/403/404/500 | Global error routes | Router/error boundary | Theo tinh huong | P0/P1 |

Route la frontend convention de xuat; phai duoc chot cung router implementation. S12 la design inventory, khong phai man hinh nghiep vu de nguoi dung mo tu navigation.

## 5. User flow

### 5.1 Resident happy paths

1. Login/demo access -> Dashboard -> chon marker/list item -> Station Detail.
2. Dashboard/Station Detail -> Hoi AI ve tram -> Agent Chat co station context.
3. Dashboard -> Compare -> chon hai tram -> xem ket qua -> Hoi AI phan tich.
4. Dashboard -> Alerts -> chon alert -> focus tram/mo Station Detail.
5. App shell -> Profile -> chon user group -> save -> Agent dung profile trong request sau.

### 5.2 Manager happy paths

1. Login -> Dashboard -> pending badge -> Approval Queue -> Proposal Detail.
2. Proposal Detail -> confirm approve -> result -> audit entry/read-only detail.
3. Proposal Detail -> nhap reject note -> confirm reject -> result -> audit entry.

### 5.3 Failure/edge flows

- Session missing/expired -> `401` -> Login, giu return URL neu auth contract cho phep.
- Resident mo approval/audit URL -> `403` hoac redirect co thong bao.
- API `503` -> error state + retry, khong fallback im lang thanh du lieu giong live.
- Proposal `409` -> reload server state -> detail read-only voi reviewer/timestamp moi nhat.
- Agent job `202` -> polling -> completed/failed/timeout; user co cancel/retry theo job contract.
- Station stale/offline/invalid -> action forecast/recommend/proposal bi disable hoac backend refusal duoc hien minh bach.

## 6. Screen specifications

### S01 - Login/Demo access

**Muc dich:** vao ung dung bang identity/role duoc backend hoac demo configuration cap.

**MVP mode:** neu auth provider chua duoc chot, dung "Demo access" voi pre-seeded identities. Khong dien dat day la production authentication va khong public password that.

**Current frontend demo implementation (04/08/2026):** ba identity `resident@vinuni.edu.vn`, `manager@vinuni.edu.vn`, `admin@vinuni.edu.vn` duoc seed trong client voi mot mat khau demo dung chung. Role duoc gan theo identity va chi hien read-only; nguoi dung khong the doi role trong Profile. Credential nay chi phuc vu demo local, khong phai secret/credential that va khong thay the backend session/RBAC.

**Production-auth fields (contract pending):**

| Field | Required | Validation |
|---|---:|---|
| Email | Yes | Trim, format email; domain rule chi ap dung neu backend/auth provider chot |
| Password | Yes | Khong trim password; length/policy theo auth provider, khong tu chot o client |
| Remember session | No | Chi hien neu session policy ho tro |

**Actions:** Dang nhap; Demo access (neu bat); Dang ky cu dan (`P2`); Quen mat khau (`P2/provider dependent`).

**States:** idle, submitting, invalid credentials, validation error, rate-limited, auth unavailable, session expired, success redirect.

### S01B - Dang ky cu dan (`P2/optional`)

**Muc dich:** self-registration cho Resident. Manager/Admin khong duoc tu chon role; tai khoan privileged phai duoc invite/provision theo backend policy.

| Field | Required | Validation |
|---|---:|---|
| Ho va ten | Yes | Trim; min/max length theo auth/profile contract |
| Email | Yes | Trim, lowercase cho comparison neu provider quy dinh; email format |
| Mat khau | Yes | Theo provider policy; khong log/telemetry value |
| Xac nhan mat khau | Yes | Phai khop mat khau |
| Nhom nguoi dung | Yes | Mot trong `normal`, `sensitive`, `outdoor_sport` |
| Dong y dieu khoan/privacy | Yes | Phai checked truoc submit |

Role luon la `resident`. Khong thu thap benh ly chi tiet. Notification consent tach khoi dieu khoan chung.

**Actions:** Tao tai khoan; quay lai Login.

**States:** idle, validation errors theo field, duplicate email, submitting, verification required, success, provider unavailable, generic failure khong lo account enumeration neu security policy cam.

**API dependency:** register/session/email verification chua co trong `api-contracts.md`; khong implement production form truoc khi contract va provider duoc chot.

**Current frontend demo implementation (04/08/2026):** form duoc trien khai de review UI/validation. Account moi luon la `resident`, luu in-memory trong phien browser va mat khi reload; UI phai hien ro gioi han nay. Manager/Admin chi co the dung identity seed, khong co self-service privilege escalation.

### S02 - Dashboard

**Muc dich:** xem tong quan nam tram, chon tram, nhan biet data quality va active alert.

**Displayed data:** map marker; station id/name; PM2.5/unit; backend level; `online/offline/stale/invalid`; source; updated time; online/offline count; active-alert count; recent alerts.

**Actions:** chon marker/list item; manual refresh; mo Station Detail; Ask AI with station context; Compare; View all alerts.

**Rules:** marker va list dung cung mot state; status precedence `invalid > offline > stale > level`; `pm25=null` hien `Khong kha dung`; aggregate khong tinh null/invalid; khong hard-code toa do/PM2.5 trong production component.

**States:** initial skeleton; success; zero stations; partial station data; missing/invalid coordinates; station offline/stale/invalid; stations API error; alerts panel error rieng; refreshing without blanking old valid UI.

**API:** `GET /stations`; optional `GET /alerts` cho recent alerts.

### S03 - Chi tiet tram

**Muc dich:** xem current measurement, freshness, history, alert va forecast cua mot tram.

**Displayed data:** station metadata; PM2.5/unit/level; status/data quality; source; updated/measured time; environmental fields neu API co; related alerts; history chart + accessible table; forecast metadata.

**Inputs:** history range. Cac preset phai nam trong API `hours=1..72`, de xuat `1h`, `6h`, `24h`, `72h`. Khong gui `7d/168h` khi contract chua mo rong.

**Actions:** change range; retry current/history/forecast rieng; Compare; Ask AI with station context; open alert.

**States:** station 404; current unavailable/null; offline/stale/invalid; history loading/empty/error; forecast loading/unavailable/stale/error; partial success giua cac panel.

**API:** `GET /stations/{id}/current`; `GET /stations/{id}/history`; `GET /stations/{id}/forecast`; `GET /alerts?station_id=...` neu filter contract ho tro.

### S04 - So sanh khu vuc

**Muc dich:** so sanh current/latest valid measurement cua hai tram trong khoang thoi gian hop ly.

| Input | Required | Validation |
|---|---:|---|
| Station A | Yes | Station id ton tai trong catalog |
| Station B | Yes | Station id ton tai va khac Station A |

**Actions:** Compare; swap stations (optional); Ask AI with selected-station context; open either Station Detail.

**Rules:** hien timestamp/source/freshness cua tung tram; neu mot tram offline/stale/invalid thi ghi ro va khong dua ket luan chac chan; khong tu suy dien nguyen nhan; recommendation theo profile chi hien tu Agent/backend result.

**States:** selection incomplete; same station; loading; one/both unavailable; timestamp mismatch warning; empty; API error; success.

**API:** station current endpoints hoac backend compare endpoint/tool adapter duoc chot sau.

### S05 - AI Agent Chat

**Muc dich:** gui cau hoi ve PM2.5/weather/forecast/alerts/profile va hien answer co grounding.

| Input | Required | Validation |
|---|---:|---|
| Message | Yes | Trim; khong cho chuoi rong; max length theo Agent API contract |
| Context station(s) | No | Chi gui id duoc chon tu UI/backend catalog |

**Actions:** send; cancel job neu ho tro; retry; copy answer; open evidence; view persisted proposal; new conversation.

**Displayed response:** answer; station/time/source/freshness; insufficient-data reason; optional proposal id/status. `used_tools`, request id va technical trace nam trong debug/details panel theo environment/role policy.

Technical details mac dinh collapsed va co the an hoan toan theo environment/role policy; end user khong bi bat doc tool trace trong message body.

**Canonical tool labels:** `get_current_pm25`, `get_station_history`, `compare_stations`, `get_weather_context`, `get_pm25_forecast`, `get_active_alerts`, `get_user_profile`, `create_warning_proposal`.

**States:** empty conversation; sending; synchronous success; job queued/running; cancelled; tool timeout; provider/API failure; malformed response; no-data/stale/invalid refusal; out-of-scope; proposal created; proposal creation denied/failed.

**API:** `POST /agent/chat` hoac `POST /agent/jobs` + `GET /jobs/{id}`.

### S06 - Danh sach canh bao

**Muc dich:** tim active/resolved alert va trace ve tram.

**Filters:** station (optional catalog id), severity (optional enum tu backend), status (`active/resolved`), time range/sort neu contract ho tro. Unknown query phai duoc backend validate; UI khong tu tao severity.

Toolbar can co search theo station id va station name tu station catalog. Badge `active` dung destructive/warning treatment, badge `resolved` dung neutral treatment; khong dung success green cho active alert.

**Table/card fields:** alert id; station; alert type; observed value; threshold; severity; created time; status; action.

**Actions:** view/focus station; reset filters; manual refresh; resolve chi cho role/policy duoc phep.

**States:** loading; empty filtered; success; duplicate records handled by stable id; `422` filter error; `503`; refresh race; partial station metadata; sensor-offline alert.

**API:** `GET /alerts`; optional resolve endpoint theo RBAC policy.

### S07 - Chi tiet Proposal

**Muc dich:** Manager/Admin review mot warning proposal voi evidence truoc khi quyet dinh.

**Displayed data:** proposal id/status; station; observed PM2.5/unit; timestamp; severity; creator/time; affected groups; rationale; evidence; weather/forecast context; proposed warning content; reviewer/timestamp/note neu da xu ly; audit summary neu co.

| Input | Required | Validation |
|---|---:|---|
| Approve note | No | Trim; max length theo API contract |
| Reject note | Yes for MVP | Trim; khong rong; max length theo API contract |

**Actions:** approve; reject; cancel modal; reload server state; open audit. Approve/reject chi enabled khi status `pending`, role hop le, evidence duoc backend danh dau eligible va request chua submitting.

**States:** detail loading; 404; 403; pending; approve/reject confirmation; submitting; success; `409` already reviewed; network error; evidence unavailable; audit unavailable; approved/rejected read-only.

**API dependency:** `GET /approvals/{id}` va request-body schema cho approve/reject can duoc them vao API contract.

### S08 - Danh sach phe duyet

**Muc dich:** Manager/Admin tim proposal can review va xem lich su quyet dinh.

**Tabs/filters:** pending, approved, rejected; station; severity; time range neu contract ho tro.

**Table/card fields:** proposal id; station; severity; creator; created time; status; action.

**Actions:** open proposal; reset filters; refresh.

**States:** loading; pending empty; history empty; 403; 422; 503; stale queue after another reviewer action; success.

**API:** `GET /approvals` voi filter/pagination schema can duoc chot.

### S09A/B - Ket qua phe duyet

**Muc dich:** xac nhan server-side decision va cho thay outcome tiep theo ma khong bao sai rang notification/device command da thanh cong.

**Approved display:** proposal approved; reviewer; decision time; note; audit reference; dispatch/notification status neu backend tra.

**Rejected display:** proposal rejected; reviewer; decision time; required reason; xac nhan khong dispatch.

**Dispatch vocabulary:** `not_configured`, `pending`, `succeeded`, `failed`. Chi hien "Da gui"/"Da thuc thi" khi backend tra `succeeded`.

**Actions:** back to queue; open read-only proposal; open audit; retry dispatch chi khi policy/backend cung cap va role hop le.

### S10 - Audit Log

**Muc dich:** read-only trace cho proposal create/approve/reject, dispatch/failure va material action khac.

**Filters:** actor, action code, outcome, time range; target id/request id neu contract ho tro.

**Table fields:** occurred_at; actor/role; action; target type/id; outcome; correlation/request id; details action.

**Actions:** view redacted detail; reset filters; export CSV chi khi endpoint va permission duoc chot.

**States:** loading; empty; 403; service unavailable; redacted detail; pagination; export unavailable/failure.

**API dependency:** audit-list/detail/export endpoint chua co trong API contract.

### S11 - Ho so nguoi dung

**Muc dich:** xem identity/role va cap nhat user group de Agent ap dung policy phu hop.

| Field | Editable | Required/validation |
|---|---:|---|
| Ho ten | Provider dependent | Theo profile/auth contract |
| Email | No by default | Render tu identity provider |
| Role | No | Server-owned; khong cho client sua |
| User group | Yes | Bat buoc; `normal`, `sensitive`, `outdoor_sport` |
| Push/email preference | P2 | Chi hien khi notification backend va consent contract ton tai |

**Actions:** save; cancel/reset.

**States:** loading; success; validation error; 401/403; save conflict; network error; profile unavailable; notification controls disabled/not configured.

**Privacy:** khong thu thap diagnosis/benh ly chi tiet; group selection chi phuc vu policy recommendation va phai co copy minh bach.

### S12 va global errors

S12 la inventory de designer/developer reuse, gom: `401`, `403`, `404`, `500`, backend unavailable, no data, sensor offline, stale, invalid, Agent tool failure, empty alerts, empty approvals, empty chat.

Moi error component can co: ma/reason de hieu; impact; action tiep theo; retry/back link neu phu hop; request id cho support (khong lo stack trace/secret).

## 7. Cross-screen state matrix

| Surface | Loading | Empty | Error | Special success/conflict |
|---|---|---|---|---|
| Dashboard | Map/list skeleton | Zero stations | Stations/alerts partial or full failure | Refresh keeps prior valid data |
| Station Detail | Current/history/forecast independently | No current/history/forecast | 404/422/503 | Offline/stale/invalid variants |
| Compare | Comparison skeleton | Missing selections/no valid pair | 404/422/503 | Timestamp mismatch/partial result |
| Agent | Sending/queued/running | Empty conversation | Tool/provider/job failure | Grounded answer, refusal, proposal created |
| Alerts | Table/card skeleton | No matching alerts | 422/503 | Active/resolved/offline alert |
| Approval Queue | Queue skeleton | Pending empty/history empty | 403/422/503 | Queue stale after concurrent review |
| Proposal Detail | Detail/submitting | Not applicable | 403/404/409/503 | Approved/rejected read-only; dispatch outcome |
| Audit | Table skeleton | No matching entries | 403/503/export failure | Redacted detail/pagination |
| Profile | Form skeleton/saving | Profile unavailable | 401/403/409/503 | Saved confirmation |

## 8. Validation va interaction rules

- Validation o client giup UX; backend validation la bat buoc va response error phai map ve field/general error.
- Disable submit khi required field invalid; khi submitting, disable mutation buttons va ngan double click.
- Khi backend tra `409`, khong tiep tuc optimistic state; refetch va render server truth.
- Filter state co the serialize vao URL nhung khong dua secret/PII vao query string.
- Station selector chi dung ids tu latest catalog response.
- Reject note bat buoc cho MVP; neu policy thay doi, cap nhat API contract, Figma va test cung luc.
- Input message/profile note khong duoc dua vao log client o dang raw neu co PII.
- Error copy khong chuan doan y te va khong khang dinh khu vuc an toan tuyet doi.

## 9. Responsive va accessibility

Target kiem tra: `1440x900`, `1024x768`, `768x1024`, `375x812`.

- Dashboard: desktop map + side panel; tablet/mobile xep map, selected detail, station list; giu nut refresh/filter truy cap duoc.
- Tables tren mobile: chuyen sang card hoac horizontal scroll co label, khong cat action/status.
- AI Chat: composer khong bi mobile keyboard che; message/evidence co reading order dung.
- Approval modal: focus trap, Escape/cancel, return focus; tren mobile co the thanh full-screen dialog.
- Status khong truyen bang mau duy nhat; dung icon/pattern/text va contrast dat yeu cau.
- Marker/action co accessible name; keyboard co cach mo station detail ma khong phu thuoc pointer.
- Chart co accessible summary/table va khong bat buoc hover de doc gia tri.

## 10. API/contract dependencies can chot

Truoc khi implement production UI cho cac surface lien quan, can bo sung/lam ro trong [api-contracts.md](api-contracts.md):

1. Auth/register/login/session/verification provider va demo identity policy.
2. `GET /approvals/{id}`; approve/reject request body co review note; reviewer/result/dispatch fields.
3. `GET /audit` hoac `/audit-logs` voi filter, pagination, redaction va role scope.
4. User profile GET/PATCH va notification preference neu P2 duoc chon.
5. Forecast response: horizon, value/range, generated/forecast time, model/source/confidence/freshness/limitation.
6. Station data-quality field/enum cho `invalid` neu `status` + `is_stale` chua du dien dat.
7. Alert filter/pagination va optional resolve RBAC contract.
8. Agent job status/cancel schema va max input length.
9. Error envelope ap dung nhat quan cho `401/403/404/409/422/503`.

## 11. Figma handoff checklist

Khong can ve lai toan bo 13 man hinh. Can cap nhat/toa variant:

- Global: simulator banner; Resident/Manager app shells; status/severity/data-quality components; loading/empty/error primitives.
- S01: demo-access vs provider-auth copy; them S01B registration co nhan `P2/Auth provider pending`.
- S02: success, loading, full error, partial error, offline, stale, invalid/null.
- S03: current unavailable; history empty/error; forecast source/freshness/unavailable; range toi da 72h theo contract hien tai.
- S04: same-station validation; offline/stale; timestamp mismatch; insufficient-data conclusion.
- S05: queued/running; no-data/tool-error/out-of-scope; proposal persisted/failed; technical details collapsed.
- S06: empty/error; sensor-offline alert; refresh/focus-map action.
- S07: approve modal; reject modal + required-note error; submitting; 403; 409; read-only result.
- S08: pending empty; history empty; 403/503; concurrent refresh.
- S09: separate proposal decision from dispatch/notification outcome.
- S10: limited Manager view, full Admin view, empty/error/export-unavailable.
- S11: Resident/Manager identity consistency; save states; P2 notification controls disabled/not configured.
- Responsive reference cho S02, S03, S05, S07 o tablet/mobile.

## 12. Definition of ready cho Frontend

Mot screen ready de implement khi:

- Role, route, API/schema va error codes da chot.
- Figma co success + required state variants va responsive behavior chinh.
- Text simulator/source/freshness da duyet.
- Validation va enable/disable rules ro rang.
- Khong con environmental sample nao co the bi hieu la live/official.
- Test cases gom happy path, empty, error va permission/concurrency neu co mutation.


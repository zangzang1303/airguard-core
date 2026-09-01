# Admin Dashboard Design Handoff

## 1. Nguồn thiết kế

- Figma Make: `AirGuard AI Wireframe Design`.
- Màn hình được kiểm tra ngày 05/08/2026 từ bản chia sẻ có giao diện Admin Dashboard IoT.
- Figma hiển thị revision hiện tại là `Version 12 - Integrate Admin Interface Version 8`; `Version 10` vẫn nằm trong lịch sử phiên bản.
- Tài liệu này ghi lại giao diện quan sát được để frontend có nguồn handoff trong repository. Contract nghiệp vụ vẫn tuân theo `specs/frontend-screen-spec.md` và `specs/api-contracts.md`.

## 2. Mục tiêu trải nghiệm

Admin có một workspace riêng để quan sát tình trạng hệ thống IoT, PM2.5, cảnh báo và hàng chờ HITL. Giao diện phải cho thấy đây là dữ liệu Simulator của MVP, không phải hệ thống quan trắc chính thức và không được dùng cho quyết định y tế hoặc pháp lý.

## 3. Bố cục tổng thể

### Sidebar

- Logo `AIRGUARD AI` và mô tả `Quản trị hệ thống`.
- Badge vai trò `Admin - Toàn quyền`.
- Navigation:
  - Tổng quan.
  - Quản lý người dùng.
  - Khu vực & Trạm.
  - Thiết bị IoT.
  - Phê duyệt HITL, có pending-count badge.
  - Cài đặt.
- Hành động `Chuyển vai trò`/đăng xuất nằm cuối sidebar.

### Topbar

- Tìm kiếm nhanh.
- Bộ chọn khu vực: Tất cả khu vực, VinUni Campus, Vinhomes Ocean Park.
- Chỉ báo kết nối `Trực tuyến`.
- Toggle dark/light mode.
- Chuông thông báo.
- Hồ sơ `Quản trị viên - Admin` với avatar `QT`.

### Nội dung Tổng quan

1. Page header `Tổng quan hệ thống`, thời gian cập nhật và nút `Làm mới`.
2. Bốn KPI:
   - Cảm biến đang hoạt động.
   - Trạng thái kết nối.
   - PM2.5 trung bình.
   - Đề xuất HITL chờ duyệt.
3. Bản đồ trạm quan trắc S01-S05 với marker trạng thái và chú giải AQI.
4. Panel đề xuất HITL đang chờ: nội dung đề xuất, trạm, PM2.5/evidence, mức độ, thời gian và hành động phê duyệt/từ chối.
5. Biểu đồ đường xu hướng PM2.5 theo giờ cho ba trạm chính.
6. Biểu đồ donut trạng thái thiết bị: trực tuyến, gián đoạn/stale, ngoại tuyến.
7. Nhật ký cảnh báo: thời gian, trạm, PM2.5, mức độ và trạng thái.

## 4. Visual tokens

- Nền chính dark navy gần `#07111f`; surface `#111d2f` và `#172438`.
- Accent chính xanh dương `#2563eb`; vai trò Admin dùng tím `#a855f7`.
- Semantic: xanh lá/online, vàng/gián đoạn, cam-đỏ/ô nhiễm, xám/offline.
- Card bo góc 14-18 px, border mảnh, shadow nhẹ; typography Inter.
- Light mode giữ cùng cấu trúc và semantic color, đổi nền/surface/text để đạt contrast AA.

## 5. Interaction và trạng thái

- Làm mới giữ dữ liệu hợp lệ cũ trong lúc request mới chạy.
- KPI không tính measurement `null`, invalid, stale hoặc offline vào PM2.5 trung bình.
- Marker ưu tiên trạng thái `invalid > offline > stale > severity`.
- Phê duyệt/từ chối điều hướng tới workspace HITL hiện có; backend RBAC là quyết định cuối cùng.
- Quản lý người dùng, khu vực/trạm, thiết bị và cài đặt là P2 khi chưa có API contract; UI phải nói rõ `chưa cấu hình`, không tạo cảm giác chức năng production đã sẵn sàng.
- Mọi environmental fact hiển thị source/freshness và nhãn Simulator.
- Có loading, empty, partial error và retry cho các surface gọi API.

## 6. Responsive

- Desktop: sidebar cố định, 4 KPI theo hàng, map/HITL chia hai cột, chart/donut chia hai cột.
- Tablet: sidebar thành drawer; KPI 2 cột; map, HITL và chart xếp dọc.
- Mobile: KPI 1 cột; topbar rút gọn; bảng chuyển sang vùng scroll ngang; action HITL luôn nhìn thấy.

## 7. Accessibility

- Tất cả icon button có accessible label và focus-visible ring.
- Trạng thái không chỉ dựa vào màu; luôn có text/icon.
- Biểu đồ có summary/legend và bảng cảnh báo làm fallback dữ liệu đọc được.
- Drawer hỗ trợ Escape và scrim; sau điều hướng focus/scroll trở về đầu nội dung.

## 8. P2 - Quản lý người dùng

### Mục đích và phạm vi

Màn hình giúp Admin quản lý identity, role và trạng thái tài khoản của hệ thống. Đây là module vận hành P2, chỉ triển khai đầy đủ khi API contract và RBAC server-side được chốt. Frontend không được tự quyết quyền hoặc mô phỏng dữ liệu người dùng như dữ liệu production.

Không hiển thị hoặc cho sửa password, token, session hay dữ liệu sức khỏe chi tiết. `User group` chỉ được hiển thị dưới các giá trị chính sách `normal`, `sensitive`, `outdoor_sport`; không thu thập chẩn đoán hay bệnh lý.

### Bố cục

1. **Page header:** `Quản lý người dùng`, mô tả phạm vi module và nút `Mời người dùng`. Nút chỉ enabled khi có endpoint và policy invitation từ backend.
2. **Demo-data note:** banner nêu rõ danh sách là dữ liệu giả lập phục vụ demo MVP, không phải dữ liệu production.
3. **Filter toolbar:** tìm theo tên hoặc email; lọc vai trò, trạng thái, khu vực; nút đặt lại bộ lọc.
4. **Bảng người dùng:** người dùng, vai trò, nhóm người dùng, tổ chức/khu vực, trạng thái, hoạt động gần nhất và action menu.
5. **User detail drawer:** mở từ bảng, có các tab `Thông tin tài khoản`, `Vai trò & phạm vi`, `Audit hoạt động`.

Màn hình này **không dùng KPI strip**. Không thêm các thẻ đếm tổng tài khoản, số lượng theo vai trò (Admin/Manager/Resident) hay số tài khoản đã vô hiệu hóa: số đếm theo role không phải tín hiệu vận hành mà Admin cần ở đầu màn hình, và bộ lọc kèm tổng số `n / m tài khoản` trong header của bảng đã cung cấp thông tin đó theo ngữ cảnh. Bố cục bắt đầu trực tiếp bằng filter toolbar và bảng người dùng.

### Bảo vệ quyền và audit

- Mọi thay đổi role, trạng thái hay lời mời phải có confirmation modal, nêu rõ target account và tác động; lý do thay đổi là bắt buộc cho action nhạy cảm.
- Admin không được tự hạ quyền, vô hiệu hóa hoặc xóa chính tài khoản của mình.
- Không xóa cứng tài khoản từ UI; ưu tiên disable/deactivate để bảo toàn audit history.
- Backend RBAC luôn là quyết định cuối; UI chỉ phản ánh quyền được backend trả về.
- Mọi mutation thành công, từ chối hoặc thất bại phải có audit record. Không hiển thị secret hoặc stack trace.

### API/contract cần chốt trước khi triển khai production

- `GET /api/v1/users` với pagination, search và filter role/status/organization.
- `GET /api/v1/users/{id}` và audit detail đã redacted.
- Mutation invitation, update role và update account status, bao gồm permission, validation, conflict và audit response schema.
- Chính sách self-protection, retention/deactivation và danh sách role được phép cấp phát.

## 9. P2 - Khu vực & Trạm

### Mục đích và phạm vi

Màn hình cho Admin quản lý catalog khu vực và quan sát trạng thái vận hành của các trạm S01-S05. Nó không thay thế Dashboard giám sát: Dashboard ưu tiên theo dõi PM2.5/cảnh báo; `Khu vực & Trạm` ưu tiên metadata, vị trí, ownership và chất lượng dữ liệu của từng trạm.

Thông tin môi trường như PM2.5, trạng thái online/stale/offline, source và timestamp chỉ render từ response backend của request hiện tại. UI luôn hiển thị nhãn Simulator trong MVP và không được mô tả là quan trắc chính thức.

### Bố cục

1. **Page header:** `Khu vực & Trạm`, mô tả catalog vận hành và nút `Thêm trạm`. Nút chỉ enabled khi API provisioning, policy station-id và quyền Admin đã được chốt.
2. **KPI strip:** Tổng khu vực, tổng trạm, trạm online/fresh, trạm cần chú ý (stale/offline/invalid).
3. **Bộ chọn khu vực:** `Tất cả`, `VinUni Campus`, `Vinhomes Ocean Park`; kèm tìm kiếm theo station ID, tên trạm hoặc loại vị trí.
4. **Workspace hai cột trên desktop:**
   - Bên trái: bản đồ vùng quan sát với marker S01-S05 và legend trạng thái.
   - Bên phải: danh sách trạm theo khu vực, trạng thái, PM2.5 gần nhất và thời điểm đo.
5. **Station detail drawer:** mở khi chọn marker/dòng trong danh sách; hiển thị metadata, data quality, current reading, liên kết tới Dashboard/Station Detail, lịch sử thay đổi và audit.

### Bảng/danh sách trạm

| Trường            | Quy tắc hiển thị                                                                |
| ----------------- | ------------------------------------------------------------------------------- |
| Mã trạm           | `S01`-`S05`, immutable sau khi provision; không tái sử dụng ID đã retire        |
| Tên trạm          | Ví dụ Cổng chính, Bãi đỗ xe, Trục đường chính; hiển thị từ catalog backend      |
| Khu vực           | VinUni Campus hoặc Vinhomes Ocean Park                                          |
| Loại vị trí       | Cổng chính, giao thông/thương mại, công viên, thể thao...                       |
| Trạng thái        | Online, stale, offline, invalid; ưu tiên `invalid > offline > stale > severity` |
| PM2.5 gần nhất    | Giá trị + `µg/m³` hoặc `Không khả dụng`; không thay null bằng 0                 |
| Đo lúc / cập nhật | `measured_at` và `received_at`/freshness, hiển thị timezone `Asia/Ho_Chi_Minh`  |
| Source            | `Simulator` trong MVP, luôn hiển thị                                            |
| Hành động         | Xem chi tiết, mở Dashboard/Station Detail, chỉnh metadata khi policy cho phép   |

### Station detail drawer

Drawer gồm bốn vùng:

1. **Identity:** station ID, tên, khu vực, loại vị trí, active/retired status và owner vận hành.
2. **Vị trí:** toạ độ, map preview, độ chính xác/toạ độ hợp lệ. Không cho nhập latitude/longitude không hợp lệ.
3. **Dữ liệu gần nhất:** PM2.5, source, measured/received time, online/stale/offline/invalid reason. Không cho dùng stale/offline/invalid data cho forecast, alert hay proposal.
4. **Audit & maintenance:** các thay đổi metadata, trạng thái provision/retire và link audit read-only.

Nút chính là `Xem dữ liệu trạm`; action chỉnh sửa metadata nằm trong luồng confirm tách biệt. Action retire/deactivate là destructive, yêu cầu lý do và phải bảo toàn history/audit; không hard-delete station qua UI.

### Trạng thái và tương tác

- **Loading:** skeleton riêng cho map và station list; không blank toàn bộ màn hình khi refresh.
- **Empty:** không có trạm trong khu vực/bộ lọc được chọn; cung cấp reset filter.
- **Map data partial:** station thiếu toạ độ vẫn nằm trong list với reason rõ ràng, không đặt marker giả.
- **Offline/stale/invalid:** marker, list và drawer dùng cùng display mapper; có icon/text ngoài màu semantic.
- **403:** ẩn action provisioning/edit nhưng giữ read-only view nếu policy cho phép.
- **409:** reload catalog từ server trước khi cho chỉnh sửa lại.
- **503:** hiện retry và request ID nếu backend trả về; không thay bằng marker/PM2.5 giả giống live data.

### Thiết kế visual và responsive

- Dùng dark admin theme hiện tại: map surface navy dạng grid/schematic, marker tròn có ID/reading; thông tin chi tiết dùng card nền `#111d2f`.
- Legend gồm Online, Dữ liệu cũ, Offline, Invalid; phải kèm text/icon.
- Desktop: map 60%, station list 40%; drawer cạnh phải rộng 420-480 px.
- Tablet: map phía trên, list phía dưới; sidebar chuyển drawer.
- Mobile: map ở đầu, station list card theo sau; station detail trở thành full-screen dialog; filter scroll ngang và action chính luôn thấy.

### API/contract cần chốt trước khi triển khai production

- `GET /api/v1/regions` và `GET /api/v1/stations` với filter khu vực, search, pagination và metadata chuẩn.
- `GET /api/v1/stations/{id}/current` cho quality/source/freshness; coordinate validation rules trong domain contract.
- Endpoint Admin-only cho create/update metadata, activate/retire station và danh sách owner/maintenance; tất cả mutation trả audit/correlation id.
- Chính sách immutable station ID, retire thay vì delete, quyền sửa toạ độ/tên/khu vực và behavior khi station thiếu/sai vị trí.

## 10. P2 - Thiết bị IoT

### Mục đích và phạm vi

Màn hình giúp Admin quản trị registry và vận hành thiết bị: kết nối, heartbeat, firmware, cấu hình, data-quality events và audit. Module này khác với `Khu vực & Trạm`:

- `Khu vực & Trạm` quản lý địa điểm, metadata của station và chất lượng measurement.
- `Thiết bị IoT` quản lý identity phần cứng/simulator, liên kết thiết bị-trạm, trạng thái kết nối và vòng đời cấu hình.

Đây là module P2. Không được tạo command MQTT từ frontend, truy cập broker credential hoặc mô phỏng command đã chạy. Device command chỉ có thể được dispatcher server-side publish sau server-side approval; UI chỉ hiển thị outcome do backend trả về.

### Bố cục

1. **Page header:** `Thiết bị IoT`, mô tả tình trạng registry/telemetry và nút `Provision thiết bị`. Nút provision chỉ enabled sau khi có device registry API, policy cấp phát và Admin RBAC.
2. **Filter toolbar:** tìm theo device ID hoặc station ID; lọc khu vực, loại thiết bị, trạng thái, firmware/config version và maintenance status.
3. **Bảng thiết bị:** device identity, trạm liên kết, connectivity, heartbeat cuối, firmware, config version, sự kiện gần nhất và action menu.
4. **Device detail drawer:** mở từ bảng, có các tab `Tổng quan`, `Kết nối`, `Firmware & cấu hình`, `Sự kiện`, `Audit`.

Màn hình này **không dùng KPI strip**. Không thêm các thẻ đếm tổng thiết bị, online/fresh, gián đoạn, offline/invalid hay firmware/config cần chú ý ở đầu màn hình: đó là các con số tổng hợp trùng với thông tin đã có trong bộ lọc trạng thái, cột `Kết nối`/`Firmware`/`Cấu hình` của bảng và tổng số `n / m thiết bị` trong header của bảng — Admin cần biết *thiết bị nào* đang gián đoạn chứ không phải *bao nhiêu* thiết bị gián đoạn. Bố cục bắt đầu trực tiếp bằng filter toolbar và bảng thiết bị, giống `Quản lý người dùng`.

### Bảng thiết bị

| Cột              | Quy tắc hiển thị                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| Thiết bị         | Device ID immutable, tên/loại cảm biến, serial được mask nếu policy yêu cầu                         |
| Trạm liên kết    | Station ID/tên hoặc `Chưa gán`; thay đổi liên kết là mutation cần audit                             |
| Kết nối          | Online, stale, offline, invalid; hiển thị icon + text + timestamp                                   |
| Heartbeat cuối   | Thời gian backend nhận status/telemetry gần nhất, timezone `Asia/Ho_Chi_Minh`                       |
| Firmware         | Version hiện tại, version khuyến nghị và trạng thái update nếu backend trả về                       |
| Cấu hình         | Config profile/version/checksum đã redacted; không hiển thị secret, MQTT URL, token hoặc credential |
| Sự kiện gần nhất | Reconnect, publish failure, invalid payload, config applied, maintenance change...                  |
| Hành động        | Xem chi tiết, mở diagnostics read-only, thay đổi cấu hình/lifecycle khi có quyền                    |

### Device detail drawer

1. **Tổng quan:** device ID, loại, trạm liên kết, serial masked, nguồn/simulator flag, ngày provision và owner vận hành.
2. **Kết nối:** status, last seen, heartbeat interval, latency/uptime nếu backend cung cấp. Trạng thái phải đến từ backend, không suy diễn từ client timer.
3. **Firmware & cấu hình:** firmware version, config version, calibration metadata, thời điểm áp dụng và kết quả deployment; không render dữ liệu secret.
4. **Data quality:** số measurement invalid/duplicate/rejected, reason code và thời gian sự kiện. Không thay giá trị thiếu bằng 0 hoặc coi invalid là valid telemetry.
5. **Sự kiện & audit:** timeline online/offline, publish/config failure, maintenance action, command dispatch outcome; audit chỉ đọc gồm actor/action/target/outcome/correlation id.

### Hành động an toàn

- Các action có thể có khi contract hỗ trợ: `Gán trạm`, `Cập nhật cấu hình`, `Đặt bảo trì`, `Kích hoạt lại`, `Deactivate`.
- Không có nút điều khiển thiết bị trực tiếp, publish MQTT trực tiếp hay bypass HITL trong browser.
- Bất kỳ update firmware/config hoặc đổi lifecycle nào cũng cần confirmation modal, nêu target/impact, lý do và audit record.
- Deactivate thay vì hard-delete; lịch sử measurement, event và audit phải được giữ theo retention policy.
- UI không được tuyên bố command/notification đã thành công trừ khi backend trả `succeeded`; các outcome hợp lệ: `not_configured`, `pending`, `succeeded`, `failed`.

### Trạng thái và responsive

- States bắt buộc: loading, empty, filtered empty, 403, 409 conflict, 422 validation, 503/unavailable, mutation submitting/success/failure.
- `409` yêu cầu reload device state từ server trước khi retry; không áp dụng config trên stale client state.
- Device thiếu station link hoặc heartbeat hiển thị reason cụ thể, không fallback thành `online`.
- Desktop dùng bảng + detail drawer 420-480 px; tablet cho phép table scroll ngang; mobile dùng device cards và full-screen detail dialog. Không có KPI strip nên filter toolbar là block đầu tiên dưới page header ở mọi breakpoint.
- Dark admin theme: online xanh lá, stale/gián đoạn vàng, offline slate, invalid/failure đỏ; luôn có text/icon ngoài màu.

### API/contract cần chốt trước khi triển khai production

- `GET /api/v1/devices`, `GET /api/v1/devices/{id}`, health/heartbeat và event timeline với filter/pagination chuẩn.
- Admin-only endpoints cho provision, gán/bỏ gán station, update config, maintenance, activate/deactivate; response phải có correlation/audit id.
- Schema firmware/config version, calibration metadata, data-quality reason code, command dispatch outcome và redaction rules.
- Chính sách device ID immutable, ownership, lifecycle/retention, configuration rollout, rollback và quyền trigger action.

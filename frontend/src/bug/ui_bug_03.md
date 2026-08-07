# Báo cáo Code Review UI/UX — Khu vực Quản trị (Admin)

| | |
|---|---|
| **Dự án** | P-074 — Hệ thống giám sát chất lượng không khí |
| **Phạm vi review** | `AdminShell`, `AdminDashboard`, `UserManagement`, `RegionStations`, `IotDevices`, `AdminModulePlaceholder` (11 file, ~4.000 dòng) |
| **Ngày review** | 2026-08-06 |
| **Reviewer** | UI/UX Expert · Senior Frontend Developer |
| **Báo cáo liên quan** | `ui_bug_01.md` (Login/Register) · `ui_bug_02.md` (giao diện Resident) |

---

## 0. Tóm tắt điều hành

Khu vực admin có kiến trúc tốt hơn hẳn giao diện resident ở tầng **logic dữ liệu**: có display-mapper dùng chung với precedence rõ ràng, không bịa marker giả trên bản đồ trạm thật, phản ánh trung thực `outcome` backend trả về, và có skeleton + `prefers-reduced-motion`. Đây là những điểm `ui_bug_02.md` từng phải khuyến nghị.

Nhưng tầng **trình bày** lại tụt lại phía sau. Ba nhóm vấn đề xuyên suốt:

1. **Hệ thống design token bị bỏ qua hoàn toàn.** Thang `--font-size-*` và `--space-*` trong `theme.css` được dùng **0 lần** trên cả 5 file CSS admin. Thay vào đó là ~120 magic number và ~60 mã màu hex cứng.
2. **Chế độ sáng (`.admin-shell--light`) là một tính năng chưa hoàn thiện đã ship.** Nút bật ở topbar hoạt động, nhưng chỉ 8/60+ giá trị màu được override.
3. **Ba màn hình admin giải quyết cùng một bài toán bằng ba cách khác nhau** — Escape handler, `preventDefault`, click-outside, breakpoint đều lệch nhau.

| Mức độ | Số lượng | Ý nghĩa |
|---|---|---|
| 🔴 **P0** | 7 | Chặn phát hành — mất chức năng hoặc nội dung không đọc được |
| 🟠 **P1** | 23 | Phải sửa trước UAT — vi phạm WCAG AA, vỡ khung, hiển thị sai sự thật |
| 🟡 **P2** | 16 | Nợ kỹ thuật — trùng lặp, thiếu nhất quán, khó bảo trì |
| ⚪ **P3** | 4 | Đánh bóng |
| | **50** | |

### Ba lỗi nghiêm trọng nhất

**① `.admin-card { overflow: hidden }` cắt mất menu thao tác (A-01).**
Menu hành động trên mỗi hàng bảng là `position: absolute; top: 100%`. Nó nằm trong `.admin-users-table-wrap { overflow-x: auto }` — mà theo spec CSS, khi một trục có `overflow` khác `visible` thì trục còn lại tự động thành `auto`. Kết quả: menu của các hàng cuối bảng bị cắt cụt. Ở màn hình chuẩn 1366×768, người dùng **không thể** đổi vai trò hay vô hiệu hóa 2–3 người dùng cuối danh sách. Đây là mất chức năng hoàn toàn, không phải lỗi thẩm mỹ.

**② Chế độ sáng cho ra chữ gần như vô hình (A-02).**
`.admin-shell--light` override đúng 8 biến. Còn lại ~60 mã hex sáng-trên-nền-tối vẫn nguyên: `#6ee7b7` trên nền trắng cho **1,52:1**, `#fde68a` cho **1,25:1** — dưới ngưỡng WCAG AA (4,5:1) từ 3 đến 3,6 lần. Toàn bộ chip trạng thái, badge vai trò và tooltip biểu đồ biến mất khi bật chế độ sáng.

**③ Drawer hiển thị dữ liệu cũ sau khi đổi vai trò thành công (A-05).**
`executeAction` gọi `setUsers(prev => ...)` đúng chuẩn functional update, nhưng ngay sau đó lại đọc `users.find(...)` — biến `users` của closure cũ. Drawer được ghi đè bằng chính object **trước khi thay đổi**. Người quản trị đổi vai trò, thấy banner "Thành công", nhưng drawer vẫn hiện vai trò cũ trong khi hàng trong bảng đã đổi. Hai nguồn sự thật mâu thuẫn trên cùng một màn hình, ở đúng chỗ mà sự chính xác quan trọng nhất.

---

## I. Lỗi UI/UX

### I.1 Tương phản màu sắc

Tất cả tỷ lệ dưới đây tính theo WCAG 2.1 SC 1.4.3, đối chiếu với nền thực tế sau khi blend alpha.

#### I.1.1 Chế độ tối (mặc định)

| # | Vị trí | Cặp màu | Tỷ lệ | Cỡ chữ | Ngưỡng | Kết luận |
|---|---|---|---|---|---|---|
| A-18 | `.admin-map-marker span` — trị số PM2.5 trên bản đồ | `#fff` trên `#10b981` | **2,54:1** | 10,7px | 4,5:1 | ❌ Fail |
| A-18 | `.admin-map-marker span` — trạng thái stale | `#fff` trên `#f59e0b` | **2,15:1** | 10,7px | 4,5:1 | ❌ Fail nặng |
| A-18 | `.admin-map-marker small` — nhãn trạm | `#fff` trên `#10b981` | **2,54:1** | **8,32px** | 4,5:1 | ❌ Fail |
| A-19 | `.admin-map-place` | `#55647a` trên `#131f2f` | **2,78:1** | 8,8px | 4,5:1 | ❌ Fail |
| A-19 | `.admin-map-label` | `#52627a` trên `#0a1626` | **2,71:1** | 9,28px | 4,5:1 | ❌ Fail |
| A-20 | `.admin-users-table th` | `#64748b` trên `#111d2f` | **3,28:1** | 9,12px | 4,5:1 | ❌ Fail |
| A-20 | `.admin-alert-log th` | `#64748b` trên `#172438` | **3,28:1** | 8,8px | 4,5:1 | ❌ Fail |
| A-21 | `.admin-station-row__mark` — offline | `#64748b` trên tint 12% | **3,17:1** | 9,6px | 4,5:1 | ❌ Fail |
| A-21 | `.admin-station-row__mark` — invalid | `#f43f5e` trên tint 12% | **4,11:1** | 9,6px | 4,5:1 | ❌ Fail sát ngưỡng |

**Nhận xét quan trọng về A-18.** Marker bản đồ dùng `background: var(--marker-color)` với `color: #fff` cố định. Bảng màu severity (`#10b981` xanh, `#f59e0b` vàng, `#f43f5e` đỏ) được thiết kế cho *chữ trên nền tối*, không phải *nền cho chữ trắng*. Đây là lỗi hệ thống: mọi màu severity đều quá sáng để làm nền cho chữ trắng. Chỉ số PM2.5 — dữ liệu quan trọng nhất của toàn sản phẩm — hiện ở 2,5:1 và 8,32px.

**Điểm cần ghi nhận:** `--admin-muted: #8290a7` trên `#111d2f` đạt **5,24:1** — token muted được chọn tốt. Các lỗi ở trên đều đến từ hex cứng *ngoài* hệ token, không phải từ token.

#### I.1.2 Chế độ sáng — hỏng toàn diện (A-02) 🔴

`.admin-shell--light` chỉ override 8 biến:

```css
.admin-shell--light {
  --admin-bg: #f3f6fb;      --admin-sidebar: #fff;
  --admin-surface: #fff;    --admin-surface-raised: #f8fafc;
  --admin-border: rgba(15,23,42,.11);
  --admin-text: #0f172a;    --admin-muted: #64748b;
  --admin-primary-soft: #dbeafe;
}
```

Nhưng ~60 mã hex sáng nằm rải rác trong 5 file CSS admin **không** đi qua biến nào:

| Mã màu | Vai trò | Trên `#fff` (light) | Kết luận |
|---|---|---|---|
| `#fde68a` | chip stale, cảnh báo drawer | **1,25:1** | Gần như vô hình |
| `#6ee7b7` | chip online | **1,52:1** | Gần như vô hình |
| `#d8b4fe`, `#e9d5ff` | badge vai trò admin | ~1,4:1 | Gần như vô hình |
| `#fecdd3`, `#fda4af` | chip invalid | ~1,7:1 | Gần như vô hình |
| `#93c5fd` | code trạm, ghi chú partial | ~1,9:1 | Vô hình |
| `#cbd5e1` | chip offline | ~1,3:1 | Vô hình |
| `#60a5fa` | tiêu đề `h3` drawer, link card | **2,54:1** | Fail |
| `#fbbf24` | lý do cảnh báo (`!important`) | ~1,7:1 | Vô hình |

Thêm vào đó, `contentStyle={{ background: "#111d2f" }}` của Recharts Tooltip (A-10) là hex cứng inline — ở chế độ sáng vẫn là hộp xanh navy đậm với chữ nhãn `#666` mặc định của Recharts, tương phản ~1,6:1.

**Kết luận:** nút bật chế độ sáng ở topbar tạo ra một giao diện không dùng được. Hoặc hoàn thiện, hoặc tạm ẩn nút — không nên để ở trạng thái hiện tại.

#### I.1.3 Token toàn cục không được remap đầy đủ (A-45)

`.admin-shell` remap 5/9 bậc slate (`50, 100, 200, 700, 900`). Nhưng khi `role === "admin"`, `App.tsx:41-52` render **7 màn hình resident bên trong `AdminShell`** — `station-detail`, `compare`, `agent`, `alerts`, `approvals`, `audit`, `profile`. Các màn hình đó dùng `styles.css`, vốn tham chiếu những token *không* được remap:

| Token | Số lần dùng trong `styles.css` | Giá trị trong admin | Vấn đề |
|---|---|---|---|
| `--color-border-strong` → `--color-slate-300` | 3 | `#cbd5e1` | Viền gần trắng trên nền navy — chói |
| `--color-decorative` → `--color-slate-400` | 2 | `#94a3b8` | Sáng hơn dự kiến |
| `--color-warning-50` / `--color-success-50` / `--color-danger-50` | ~10 | nền pastel sáng | Chip sáng trên nền tối, lạc điệu |

Chưa gây mất nội dung, nhưng là rủi ro tiềm ẩn rõ ràng: `.dashboard-alert-item` (`styles.css:1380`) đặt `background: #ffffff` cùng `color: var(--color-text)` — trong `.admin-shell`, `--color-text` = `#f8fafc`. Nếu component đó từng được dùng lại trong admin, kết quả là **chữ trắng trên nền trắng**. Hiện tại nó chỉ nằm ở `Dashboard` resident nên chưa lộ ra.

---

### I.2 Thứ bậc phông chữ

#### I.2.1 Thang chữ được định nghĩa nhưng không dùng (A-26) 🟠

`theme.css:52-59` đã có sẵn thang đầy đủ, gồm cả `--font-size-2xs: 0.6875rem` (11px) từng được `ui_bug_02.md` đề xuất:

```css
--font-size-2xs: 0.6875rem;  --font-size-xs:  0.75rem;
--font-size-sm:  0.875rem;   --font-size-base: 1rem;
--font-size-lg:  1.125rem;   --font-size-xl:  1.25rem;
--font-size-2xl: 1.5rem;     --font-size-3xl: 1.875rem;
```

Số lần được dùng trong `AdminShell.css`, `AdminDashboard.css`, `UserManagement.css`, `RegionStations.css`, `IotDevices.css`: **0**.

Thay vào đó là ~90 khai báo `font-size` bằng `rem` thập phân tự chế, tạo ra **23 bậc chữ riêng biệt** trong khoảng 0,52rem–0,86rem — tức 23 bậc nằm gọn trong một khoảng 5,4px. Đó không phải thứ bậc, đó là nhiễu.

#### I.2.2 Sàn cỡ chữ ở 8,48px

Cả Material Design 3 lẫn Apple HIG đặt sàn 12px cho chữ nội dung. Bảng dưới liệt kê các khai báo dưới 9,6px:

| Cỡ | px | Selector | Nội dung mang theo |
|---|---|---|---|
| 0,52rem | **8,32** | `.admin-map-marker small` | Tên trạm trên bản đồ |
| 0,53rem | **8,48** | `.admin-device-card__grid dt` | Nhãn trường — **trên mobile card** |
| 0,54rem | **8,64** | `.admin-device-serial` `!important` | Số serial thiết bị |
| 0,55rem | **8,80** | `.admin-severity`, `.admin-alert-status` | **Mức độ nghiêm trọng cảnh báo** |
| 0,55rem | 8,80 | `.admin-alert-log th`, `.admin-hitl-content dt` | Tiêu đề cột nhật ký |
| 0,55rem | 8,80 | `.admin-map-place`, `.admin-station-row__time` `!important` | Vị trí, thời điểm đo |
| 0,55rem | 8,80 | `.admin-device-reason`, `.admin-device-outcome` | Lý do lỗi thiết bị |
| 0,56rem | 8,96 | `.admin-role-badge`, `.admin-user-status` | Vai trò, trạng thái tài khoản |
| 0,56rem | 8,96 | `.admin-station-status`, `.admin-device-status` | Chip trạng thái trạm/thiết bị |
| 0,56rem | 8,96 | `.admin-user-info dt`, `.admin-device-cell small` | Nhãn trường trong drawer |
| 0,57rem | 9,12 | `.admin-users-table th`, `.admin-device-identity small` | Tiêu đề cột bảng |
| 0,58rem | 9,28 | `.admin-map-label`, `.admin-chart-legend`, `.admin-group-code` | Chú giải biểu đồ |
| 0,59rem | 9,44 | `.admin-map-legend` | Chú giải bản đồ |
| 0,60rem | 9,60 | `.admin-station-row__mark`, `.admin-region-list__note` | Trị số trong ô trạng thái |

**20+ khai báo dưới 9,6px.** Điều đáng lo nhất: `.admin-severity` — nhãn phân loại mức độ ô nhiễm — nằm ở 8,8px. Trong một sản phẩm giám sát môi trường, đó là dòng chữ quan trọng nhất trên màn hình.

#### I.2.3 Đảo ngược thứ bậc (A-27) 🟠

| Phần tử | Vai trò ngữ nghĩa | Cỡ thực tế |
|---|---|---|
| `.admin-kpi > strong` | Con số trang trí | **23,2px** |
| `.admin-dashboard__header h1` | Tiêu đề trang | 21,6–28,8px |
| `.admin-station-drawer__header strong` | Tên trạm | 13,6px |
| `.admin-card__header h2` | **Tiêu đề khối** | **12,16px** |
| `.admin-drawer-section h3` | **Tiêu đề mục** | **9,92px** |

`h2` nhỏ hơn chữ nội dung. `h3` chỉ bằng 43% của một con số trang trí. Với người dùng screen reader dựa vào cấu trúc heading để điều hướng (WCAG 2.4.10), cấu trúc ngữ nghĩa vẫn đúng — nhưng với người dùng nhìn, hệ thống phân cấp thị giác đã bị đảo ngược hoàn toàn: mắt bị hút vào số liệu trang trí trước khi thấy tiêu đề khối chứa nó.

---

### I.3 Khoảng cách & Magic Number

#### I.3.1 Thang khoảng cách không được dùng (A-26)

`theme.css` có `--space-1` đến `--space-10`. Số lần dùng trong CSS admin: **0**.

Thống kê giá trị `padding`/`gap`/`margin` thực tế xuất hiện:

```
3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24, 26, 28, 34
```

**21 giá trị khác nhau**, trong đó `9`, `11`, `13`, `15` không thuộc bất kỳ thang 4px hay 8px nào. Ví dụ tiêu biểu trong `RegionStations.css`:

```css
.admin-regions-toolbar { gap: 10px; margin-bottom: 16px; padding: 13px; }
.admin-partial-note    { gap: 9px;  margin-bottom: 16px; padding: 11px 13px; }
.admin-station-row     { gap: 11px; padding: 12px; }
.admin-station-rows    { gap: 8px;  padding: 12px; }
.admin-region-list__note {          padding: 0 14px 14px; }
```

Năm phần tử liền kề nhau dùng 5 giá trị padding khác nhau (13, 11, 12, 12, 14). Không có quy tắc nào giải thích được sự khác biệt này — chúng là kết quả của việc căn chỉnh bằng mắt từng phần tử một.

#### I.3.2 `calc(100dvh - 110px)` tạo thanh cuộn ma (A-28) 🟠

Bốn file khai báo cùng một dòng:

```css
.admin-module-page  { min-height: calc(100dvh - 110px); }  /* AdminDashboard.css */
.admin-users-page   { min-height: calc(100dvh - 110px); }  /* UserManagement.css */
.admin-regions-page { min-height: calc(100dvh - 110px); }  /* RegionStations.css */
.admin-devices-page { min-height: calc(100dvh - 110px); }  /* IotDevices.css */
```

Số 110 không khớp với chiều cao thực tế:

- `.admin-content` là hàng grid thứ hai, chiều cao khả dụng = `100dvh − 74px` (topbar).
- `.admin-footer` = `12px + 24px` padding + ~15px dòng chữ ≈ **51px**.
- Chiều cao tối thiểu của trang = `(100dvh − 110) + 51` = `100dvh − 59`.
- Nhưng vùng chứa chỉ cao `100dvh − 74`.

Chênh **15px** ⇒ **mọi trang admin đều có thanh cuộn dọc, kể cả khi hoàn toàn trống.** Đây chính là loại lỗi mà magic number gây ra: con số 110 được đoán, không được suy ra.

#### I.3.3 Hai giá trị max-width cho cùng một ý đồ (A-44)

```css
/* AdminShell.css:105 */
.admin-content > :not(.admin-dashboard):not(.admin-footer) {
  width: min(1440px, 100%); padding: 28px 26px 34px;
}
/* AdminDashboard.css:2 */
.admin-dashboard { width: min(1480px, 100%); padding: 28px 26px 34px; }
```

Padding trùng khít nhưng max-width lệch 40px. Khi admin chuyển từ "Tổng quan" (1480px) sang "Phê duyệt HITL" (1440px), toàn bộ nội dung dịch ngang 20px mỗi bên. Nhỏ, nhưng nhìn thấy được, và không có lý do gì để tồn tại.

---

### I.4 Nguy cơ vỡ khung

#### A-01 🔴 — Menu thao tác bị cắt

```css
/* AdminDashboard.css:24  */ .admin-card { overflow: hidden; border-radius: 15px; }
/* UserManagement.css     */ .admin-users-table-wrap { overflow-x: auto; }
/* UserManagement.css:~   */ .admin-users-menu { position: absolute; z-index: 20; right: 0; top: 100%; }
```

Theo CSS Overflow Module Level 3: *"if one of `overflow-x`/`overflow-y` is computed to a value other than `visible`, and the other is `visible`, the computed value of `visible` becomes `auto`."* Vì vậy `.admin-users-table-wrap` cắt cả theo trục dọc. Menu `min-width: 210px` mở xuống dưới từ hàng cuối bảng sẽ bị cắt. Lớp `.admin-card { overflow: hidden }` bên ngoài cắt lần thứ hai.

Ảnh hưởng: **`UserManagement` và `IotDevices` — mọi thao tác trên các hàng cuối danh sách.**

#### A-03 🔴 — Sidebar off-canvas vẫn nằm trong tab order

```css
@media (max-width: 1060px) {
  .admin-sidebar { position: fixed; transform: translateX(-103%); }
}
```

Chỉ dịch chuyển, không có `visibility: hidden` hay `inert`. Chín control vẫn nhận focus khi drawer đóng: nút brand, nút đóng (`.admin-mobile-close` chuyển thành `display: grid` chính trong media query này), 6 mục nav, nút "Chuyển vai trò". Người dùng bàn phím phải Tab qua 9 phần tử vô hình trước khi tới nội dung.

Đáng chú ý: ngay bên dưới trong cùng file, scrim lại dùng **đúng** kỹ thuật:

```css
.admin-shell__scrim { visibility: hidden; opacity: 0; }
```

Kiến thức đã có sẵn trong codebase, chỉ là chưa áp dụng cho sidebar. (Trùng với `R-03` trong `ui_bug_02.md` — lỗi được lặp lại nguyên vẹn ở shell thứ hai.)

#### A-04 🔴 — Sidebar không cuộn được

```css
.admin-shell   { height: 100dvh; overflow: hidden; }
.admin-sidebar { display: flex; height: 100dvh; flex-direction: column; }
```

Không có `overflow-y`. Chiều cao nội dung tối thiểu:

| Khối | Chiều cao |
|---|---|
| `.admin-brand` | 74px |
| `.admin-role-card` (+ margin 18/13) | ~70px |
| `.admin-nav` (6 × 44px + 5 × 5px gap) | 289px |
| `.admin-sidebar__footer` (padding 32 + button 42 + border 1) | 75px |
| **Tổng** | **~508px** |

Dưới ~510px chiều cao viewport, `margin-top: auto` của footer về 0 và nút "Chuyển vai trò" bị cắt khỏi màn hình, không thể cuộn tới. Điều kiện xảy ra: điện thoại xoay ngang (iPhone 14 ngang = 390px), cửa sổ trình duyệt thu nhỏ, laptop có DevTools mở. (Trùng với `R-02`.)

#### A-07 🔴 — Thứ tự z-index sai giữa drawer và modal xác nhận

```css
.admin-drawer-scrim, .admin-confirm-scrim { z-index: 60; }
.admin-user-drawer                        { z-index: 61; }
.admin-confirm-modal                      { z-index: 62; }
```

Luồng thực tế: mở drawer người dùng → bấm "Vô hiệu hóa" → modal xác nhận hiện lên, **drawer vẫn mở**. Nhưng `.admin-confirm-scrim` (60) nằm **dưới** `.admin-user-drawer` (61). Hậu quả:

1. Drawer không bị làm mờ, trông như vẫn đang hoạt động.
2. Drawer **thực sự vẫn nhận click** — có thể bấm "Đổi vai trò" trong khi hộp thoại xác nhận đang mở, ghi đè `pendingAction`.
3. Hai lớp scrim `rgba(2,6,23,.55)` chồng lên nhau ở phần còn lại của trang cho độ tối hiệu dụng 0,80 thay vì 0,55 — tối hơn nhiều so với thiết kế.

#### A-08 🟠 — Topbar tràn trong dải 1060–1230px

`.admin-topbar` là flex, **không có `flex-wrap`**. Bề rộng tối thiểu của các phần tử:

| Phần tử | Bề rộng |
|---|---|
| `.admin-search` | `min(280px, 24vw)` |
| `.admin-area-select select` | **190px cố định** |
| `.admin-online-pill` | ~103px |
| 2 × `.admin-icon-button` (`flex: 0 0 auto`) | 84px |
| `.admin-profile` | ~180px |
| 6 khoảng gap × 12px | 72px |

Tại viewport 1150px: workspace = `1150 − 258` = 892px, trừ padding 48px còn **844px**. Tổng yêu cầu = 276 + 190 + 103 + 84 + 180 + 72 = **905px**. **Thiếu 61px.**

Dải vỡ: **1061px → ~1230px** — bao trùm 1152px và 1200px, hai bề rộng laptop phổ biến. Vì `.admin-shell` có `overflow: hidden`, phần tràn bị cắt thẳng chứ không tạo thanh cuộn để người dùng nhận ra.

#### A-30 🟠 — Bảng thiết bị 8 cột cuộn ngang liên tục từ 900px đến ~1350px

`.admin-users-table td { white-space: nowrap }` áp cho cả bảng thiết bị. Bề rộng min-content ước tính: 200 + 120 + 130 + 120 + 160 + 160 + 130 + 60 ≈ **1080px**. Chuyển sang card ở 900px.

| Viewport | Bề rộng nội dung | Kết quả |
|---|---|---|
| 901–1060px | ~950px (sidebar off-canvas) | Cuộn ngang |
| 1061–1350px | viewport − 258px − 52px | Cuộn ngang |
| >1350px | ≥1080px | Vừa |

Tức bảng cuộn ngang trên **toàn bộ dải laptop**. Kết hợp với A-01 (menu bị cắt), thao tác trên bảng thiết bị ở laptop là một trải nghiệm gãy hoàn toàn.

#### A-22 🟠 — Marker bản đồ chồng lên nhau từ trạm thứ 6

```tsx
const MAP_POSITIONS = [
  { left: "23%", top: "62%" }, { left: "51%", top: "39%" },
  { left: "74%", top: "65%" }, { left: "34%", top: "31%" },
  { left: "82%", top: "27%" },
];
const position = MAP_POSITIONS[index % MAP_POSITIONS.length];
```

Trạm thứ 6 nhận **chính xác** tọa độ của trạm thứ 1 và che khuất hoàn toàn. Trong khi đó tiêu đề khối hiển thị `{stations.length} trạm` — bản đồ nói dối về số lượng trạm nó đang thể hiện.

Đối chiếu: `RegionStations.tsx:482-487` **từ chối** đặt marker giả và dùng `map_x`/`map_y` thật từ backend, kèm ghi chú giải thích. Cùng một đội, cùng một sprint, hai chuẩn mực trái ngược trên cùng một loại thành phần.

---

## II. Kiểm tra Responsive

### II.1 Ma trận breakpoint — không đồng bộ (A-31)

| File | Breakpoint |
|---|---|
| `AdminShell.css` | **1060** / 760 / 520 |
| `AdminDashboard.css` | **1180** / 720 / 480 |
| `UserManagement.css` | **900** / 720 / 480 |
| `RegionStations.css` | **1180** / 720 / 480 |
| `IotDevices.css` | — / 720 / 480 |

Năm file, **bảy** điểm ngắt khác nhau. Các dải xung đột:

- **1060–1180px:** shell đã chuyển sidebar sang off-canvas (nội dung rộng ra), nhưng dashboard và regions vẫn giữ layout 2 cột dành cho màn hình hẹp → khoảng trắng thừa hai bên.
- **900–1060px:** bảng người dùng đã chuyển sang card, nhưng shell vẫn giữ sidebar cố định 258px → card bị ép trong 640px.
- **520–720px:** shell dùng 520 trong khi 4 file feature dùng 480 → topbar và nội dung đổi layout ở hai thời điểm khác nhau, tạo một dải 40px hiển thị lai.

### II.2 Ma trận hành vi theo bề rộng

| Bề rộng | Sidebar | Bảng | Topbar | Đánh giá |
|---|---|---|---|---|
| ≥1400px | Cố định 258px | Đủ 8 cột | Đủ chỗ | ✅ Ổn |
| 1231–1400px | Cố định | Bảng thiết bị cuộn ngang | Vừa khít | 🟡 Chấp nhận được |
| **1061–1230px** | Cố định | Cuộn ngang | **Tràn, bị cắt** | 🔴 **Vỡ** (A-08) |
| 901–1060px | Off-canvas (9 control vẫn tab được) | Cuộn ngang | Ổn | 🟠 A-03 |
| 721–900px | Off-canvas | Card | Ổn | 🟠 A-03 |
| 481–720px | Off-canvas | Card | Ổn | 🟠 A-03 |
| ≤480px | Off-canvas | Card 1 cột | Xếp dọc | 🟠 Chữ 8,48px |
| Cao ≤510px | **Nút đăng xuất bị cắt** | — | — | 🔴 A-04 |

### II.3 Render trùng DOM (A-32, A-33)

```tsx
<div className="admin-users-desktop">{renderTable()}</div>
<div className="admin-users-mobile">{renderMobileCards()}</div>
```

Cả bảng desktop **và** card mobile luôn được mount đồng thời ở mọi bề rộng. Ba hệ quả:

1. **Chi phí render nhân đôi** — 2× số node, 2× số listener, 2× công việc reconcile cho mỗi lần cập nhật state.
2. **State `menuFor` dùng chung** — mở menu ở hàng bảng cũng mở menu ở card tương ứng. Chỉ một cái nhìn thấy được, nhưng cả hai đều tồn tại trong DOM.
3. **Phụ thuộc CSS mong manh** — `.admin-users-desktop` và `.admin-users-mobile` **chỉ** được khai báo bên trong `@media (max-width: 900px)` của `UserManagement.css`. Không có rule base. `IotDevices.tsx` dùng chính hai class này nhưng `IotDevices.css` không khai báo chúng. Layout của màn hình thiết bị phụ thuộc vào một media query trong file của màn hình khác.

### II.4 Vùng cuộn không truy cập được bằng bàn phím (A-24)

| Selector | Cuộn | `tabindex` | `role="region"` |
|---|---|---|---|
| `.admin-users-table-wrap` | ngang | ❌ | ❌ |
| `.admin-devices-table-wrap` | ngang | ❌ | ❌ |
| `.admin-station-rows` | dọc | ❌ | ❌ |
| `.admin-user-drawer__tabs` | ngang (≤720px) | ❌ | ❌ |

Vi phạm WCAG 2.1.1. Người dùng chỉ dùng bàn phím không thể cuộn ngang để thấy các cột bên phải của bảng thiết bị — mà theo II.2, bảng đó cuộn ngang trên toàn bộ dải laptop.

### II.5 Vùng chạm dưới 24px (A-23)

WCAG 2.5.8 (AA) yêu cầu tối thiểu 24×24px.

| Phần tử | Kích thước thực | Chức năng |
|---|---|---|
| `.admin-card__header > button` | ~17px | "Xem tất cả" |
| `.admin-device-card__link` | ~15px | Mở chi tiết thiết bị — **trên mobile card** |
| `.admin-error button` | ~16px | **"Thử lại" khi tải lỗi** |
| `.admin-mutation-banner button` | 15px | Đóng thông báo |
| `.admin-mobile-close` | 34px | Đóng sidebar (đạt tối thiểu, dưới khuyến nghị 44px) |

Nghiêm trọng nhất là `.admin-error button`: khi tải dữ liệu thất bại, lối thoát duy nhất của người dùng là một nút cao 16px.

---

## III. Đánh giá Clean Code

### III.1 CSS trùng lặp

| # | Trùng lặp | Vị trí | Quy mô |
|---|---|---|---|
| A-34 | `.admin-users-toolbar` ≡ `.admin-regions-toolbar` ≡ `.admin-devices-toolbar` | 3 file | **3 khối giống hệt từng dòng** (10 thuộc tính) |
| A-35 | `.admin-station-status` ≡ `.admin-device-status` | `RegionStations.css:159`, `IotDevices.css:99` | 4 biến thể × 2 = 8 rule trùng |
| A-36 | `.admin-station-drawer` ≈ `.admin-user-drawer` | 2 file | 9/10 thuộc tính trùng, khác mỗi `width` |
| A-37 | `.admin-user-audit` ≈ `.admin-user-audit-list` | 2 file | Hai style timeline gần như giống nhau |
| A-28 | `min-height: calc(100dvh - 110px)` | 4 file | 4 bản sao của cùng một magic number |

Ví dụ A-34 — ba khối này giống nhau đến từng byte, chỉ khác tên class:

```css
.admin-users-toolbar,
.admin-regions-toolbar,
.admin-devices-toolbar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
  margin-bottom: 16px; padding: 13px;
  border: 1px solid var(--admin-border); border-radius: 14px;
  background: var(--admin-surface);
}
```

### III.2 Bảy khai báo `!important` (A-38)

| Khai báo | File | Nguyên nhân |
|---|---|---|
| `.admin-station-row__time { font-size: .55rem !important }` | `RegionStations.css:144` | Ghi đè `.admin-station-row__body > small` |
| `.admin-station-row__reason { color: #fbbf24 !important }` | `RegionStations.css:147` | Ghi đè `--admin-muted` |
| `.admin-device-serial { font-size: .54rem !important }` | `IotDevices.css:56` | Ghi đè `.admin-device-identity small` |
| `.admin-device-mono { font-size: .58rem !important }` | `IotDevices.css:73` | Ghi đè `.admin-device-cell small` |
| `.admin-device-attention { color: #fbbf24 !important }` | `IotDevices.css:76` | Ghi đè `.admin-device-cell` |
| `.admin-users-action--danger { color: #fb7185 !important }` | `UserManagement.css` | Ghi đè `.admin-users-menu button` |
| `.admin-users-action--disabled { color: var(--admin-muted) !important }` | `UserManagement.css` | Ghi đè cùng chỗ |

Tất cả đều là hệ quả của việc style theo cấu trúc thẻ (`.parent small`, `.parent button`) thay vì đặt class riêng. Mỗi `!important` là một nút thắt mà lần sửa sau sẽ phải gỡ.

### III.3 Phụ thuộc chéo file ngầm (A-40)

| Nơi dùng | Class | Nơi khai báo | Rủi ro |
|---|---|---|---|
| `IotDevices.tsx` | `.admin-users-search`, `.admin-users-select`, `.admin-users-table`, `.admin-users-menu`, `.admin-users-desktop/mobile`, `.admin-user-drawer__tabs` | `UserManagement.css` | Xóa `UserManagement` ⇒ hỏng `IotDevices` |
| `IotDevices.tsx` | `.admin-skeleton`, `.admin-skeleton--row` | `RegionStations.css` | Tương tự |
| `RegionStations.tsx` | `.admin-users-select`, `.admin-users-search`, `.admin-users-reset`, `.admin-user-info` | `UserManagement.css` | Tương tự |
| Toàn bộ admin | `.sr-only` | `AppShell.css:398` | Chỉ hoạt động vì `App.tsx:3` import tĩnh `AppShell` |
| Toàn bộ admin | `.is-spinning` | `styles.css:1100` | Chỉ hoạt động vì `App.tsx:21` import tĩnh |
| Feature admin | `.admin-icon-button`, `.admin-primary-button` | `AdminShell.css` | Class của layout rò rỉ vào feature |

Hiện tại tất cả đều chạy được vì bundler gom hết CSS vào một file. Nhưng nếu chuyển sang lazy-load route hoặc CSS Modules, quan hệ phụ thuộc này sẽ đứt. Vấn đề không phải là "sẽ hỏng", mà là **không nhìn thấy được**: đọc `IotDevices.css` không cách nào biết màn hình đó cần hai file CSS khác.

### III.4 Bốn nguồn màu trạng thái mâu thuẫn (A-39)

| Nguồn | Vị trí | online | stale | offline | invalid |
|---|---|---|---|---|---|
| `getPm25Severity()` | `DataQualityBadge.tsx` | `#10b981` | `#f59e0b` | `#9ca3af` | `#8b5cf6` |
| `getDisplayState()` | `RegionStations.tsx` | `#10b981` | `#f59e0b` | `#64748b` | `#f43f5e` |
| `getConnectivity()` | `IotDevices.tsx` | `#10b981` | `#f59e0b` | `#64748b` | `#f43f5e` |
| `LEGEND` (×2 mảng) | `RegionStations.tsx`, `IotDevices.tsx` | `#10b981` | `#f59e0b` | `#64748b` | `#f43f5e` |
| CSS chip `.is-*` | `RegionStations.css`, `IotDevices.css` | **`#6ee7b7`** | **`#fde68a`** | **`#cbd5e1`** | **`#fda4af`** |

Marker JS và chip CSS dùng **hai bảng màu khác nhau** cho cùng một trạng thái. Trên màn hình "Khu vực & Trạm", marker "Online" là `#10b981` còn chip "Online" ngay bên cạnh là `#6ee7b7` — hai sắc xanh khác nhau cho cùng một khái niệm. Chưa kể `getPm25Severity` (dùng ở giao diện resident) lại quy ước offline/invalid hoàn toàn khác.

### III.5 Inline style và giá trị cứng trong JSX

| Vị trí | Mã | Vấn đề |
|---|---|---|
| `AdminDashboard.tsx` | `CHART_COLORS = ["#3b82f6","#f97316","#a855f7"]` | Không token, không đổi theo theme |
| `AdminDashboard.tsx:220-223` | 4 hex inline cho legend (`#10b981`, `#f59e0b`, `#f97316`, `#64748b`) | Trùng với A-39 |
| `AdminDashboard.tsx` | `<XAxis stroke="#718096" tick={{ fontSize: 10 }} />` | Chữ 10px, hex cứng |
| `AdminDashboard.tsx` | `<Tooltip contentStyle={{ background: "#111d2f", … }} />` | Hỏng ở chế độ sáng (A-10) |
| `AdminDashboard.tsx` | `<CartesianGrid stroke="rgba(148,163,184,.12)" />` | Hex cứng |
| `AdminDashboard.tsx` | `MAP_POSITIONS` (10 giá trị %) | Tọa độ giả (A-22) |

### III.6 Code chết và nhánh không thể tới

| # | Vị trí | Mô tả |
|---|---|---|
| A-43 | `UserManagement.tsx` | `if (!reason.trim()) { setMutationMessage(…); return; }` — **không bao giờ chạy** vì nút submit đã `disabled={submitting \|\| !reason.trim()}`. Vi phạm CLAUDE.md §2 ("no error handling for impossible scenarios"). |
| A-48 | `AdminModulePlaceholder.tsx` | `moduleCopy` khai báo 4 module nhưng `App.tsx:38-40` chỉ còn dùng `"settings"`. Ba entry `users`/`regions`/`devices` là code chết kể từ khi ba màn hình đó được hiện thực hóa. |
| A-41 | `IotDevices.tsx` | Tab "Sự kiện" và tab "Nhật ký" render **cùng một mảng `events`**, cùng các trường, chỉ khác `key` prefix. Hai tab, một nguồn dữ liệu. |

### III.7 Lỗi logic ảnh hưởng trực tiếp tới giao diện

**A-05 🔴 — Stale closure trong `executeAction`:**

```tsx
setUsers((prev) => prev.map((item) => (item.user_id === user.user_id ? result.user : item)));
const updated = users.find((item) => item.user_id === user.user_id);  // ← users cũ
if (updated) setSelectedUser((prev) => (prev ? { ...updated } : prev));
```

Dòng 2 đọc `users` từ closure của lần render trước — tức dữ liệu **trước** khi thay đổi. Drawer bị ghi đè bằng trạng thái cũ.

**A-06 🔴 — `aria-modal` không có gì đứng sau:**

| Màn hình | `role="dialog"` | `aria-modal` | Escape | Focus trap | Focus restore |
|---|---|---|---|---|---|
| `UserManagement` drawer | ✅ | ✅ | ❌ | ❌ | ❌ |
| `UserManagement` confirm | ✅ | ✅ | ❌ | ❌ | ❌ |
| `RegionStations` drawer | ✅ | ✅ | ✅ | ❌ | ❌ |
| `IotDevices` drawer | ✅ | ✅ | ✅ | ❌ | ❌ |

`aria-modal="true"` là lời hứa với screen reader rằng nội dung phía sau đã bị ẩn. Không có gì thực hiện lời hứa đó. Riêng `UserManagement` còn thiếu cả Escape — hai hộp thoại chỉ đóng được bằng chuột, dù hai màn hình anh em cùng thư mục đã làm đúng.

**A-29 🟠 — Nhận diện "chính mình" bằng tên hiển thị:**

```tsx
const isSelf = (user: AdminUser) => user.role === "admin" && user.full_name === userName;
```

Hai quản trị viên trùng tên ⇒ cả hai bị khóa thao tác. Nên so sánh theo `user_id`.

**A-25 🟠 — Thông báo lỗi hiển thị hai lần:**

Khi mutation lỗi lúc modal đang mở, `mutationMessage` render đồng thời ở banner cấp trang (`role="status"`) và trong modal (`role="alert"`). Screen reader đọc hai lần với hai mức ưu tiên khác nhau.

**A-42 🟡 — Menu đề xuất hành động vô nghĩa:**

Thiết bị `lifecycle === "deactivated"` vẫn được đề nghị "Đặt bảo trì" bên cạnh "Kích hoạt lại". Đặt một thiết bị đã vô hiệu hóa vào chế độ bảo trì không có ý nghĩa nghiệp vụ.

**A-17 🟠 — Menu không tự đóng:**

`menuFor` chỉ được xóa khi bấm nút menu khác hoặc bấm chính item trong menu (và trong `IotDevices` thì thiếu cả `onClick={() => setMenuFor(null)}` mà `UserManagement` có). Không có click-outside, không có Escape. Menu treo lại trên màn hình.

**A-13, A-12 🟠 — Control giả trong topbar:**

```tsx
<input type="search" placeholder="Tìm trạm, người dùng..." />   {/* không value, không onChange */}
<select defaultValue="all"> … </select>                          {/* uncontrolled, không onChange */}
<div className="admin-online-pill"><span />Trực tuyến</div>       {/* markup tĩnh */}
```

Ba affordance giả nằm ở phần chrome cố định, xuất hiện trên **mọi** màn hình admin. Nghiêm trọng nhất là `.admin-online-pill`: nó luôn báo "Trực tuyến" bất kể trạng thái thật — trong khi KPI ngay bên dưới có thể đồng thời báo "Gián đoạn" (A-11). Hai tuyên bố mâu thuẫn cùng lúc trên một màn hình giám sát. (Cùng loại với `R-14`.)

**A-11 🟠 — KPI khẳng định sai trong lúc tải:**

```tsx
<strong>{loading ? "—" : onlineCount > 0 ? "Trực tuyến" : "Gián đoạn"}</strong>
```

KPI #2 **không** có nhánh `loading` cho phần `<strong>` — trong suốt thời gian fetch, `onlineCount` = 0 nên màn hình hiển thị **"Gián đoạn"** ở vị trí nổi bật nhất. Và cả 4 KPI đều không bảo vệ phần `<small>`:

| KPI | `<strong>` có guard? | `<small>` hiển thị lúc tải |
|---|---|---|
| Tổng số trạm | ✅ | "0 trạm cần kiểm tra" |
| Trạng thái kết nối | ❌ **"Gián đoạn"** | "0 Online · 0 Gián đoạn · 0 Ngoại tuyến" |
| PM2.5 trung bình | ✅ (`?? "—"`) | "0 trạm có dữ liệu hợp lệ" |
| Chờ phê duyệt | ✅ | — |

Đây chính xác là lỗi mà `ui_bug_02.md` ghi nhận ở `R-13`: thay số 0 cho dữ liệu chưa có, biến "chưa biết" thành "bằng không".

**A-09 🟠 — Trục X hiển thị timestamp ISO thô:**

```tsx
const row: ChartRow = { time: series[0]?.points[index]?.timestamp ?? `${index + 1}` };
…
<XAxis dataKey="time" stroke="#718096" tick={{ fontSize: 10 }} minTickGap={30} />
<Tooltip contentStyle={{ … }} />
```

Không có `tickFormatter`, không có `labelFormatter`. Trục X vẽ nguyên chuỗi `2026-08-06T14:00:00Z` ở cỡ 10px; tooltip cũng vậy. Hàm `formatClock` đã tồn tại trong cùng file nhưng không được dùng cho biểu đồ.

Ghi chú thêm: `mergeHistory` ghép các chuỗi theo **chỉ số mảng**, không theo timestamp. Nếu hai trạm có số điểm dữ liệu khác nhau hoặc lệch mốc thời gian, các điểm sẽ bị xếp sai cột.

### III.8 Chế độ sáng chưa hoàn chỉnh về mặt hạ tầng (A-46)

- `lightMode` là state cục bộ của `AdminShell` ⇒ mất khi reload.
- Không đặt `color-scheme` ⇒ thanh cuộn, dropdown native, form control giữ nguyên màu hệ điều hành, lệch pha với giao diện.
- Không đọc `prefers-color-scheme`.
- Chỉ có ở shell admin, không có ở shell resident ⇒ hành vi sản phẩm không nhất quán giữa hai vai trò.

---

## IV. Bảng đề xuất giải pháp

Quy ước: `▸` = dòng thêm vào · `✕` = dòng gỡ bỏ

### IV.1 🔴 P0 — Chặn phát hành

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|---|---|---|---|
| **A-01** | `.admin-card { overflow: hidden }` + `.admin-users-table-wrap { overflow-x: auto }` cắt mất `.admin-users-menu` | Theo CSS Overflow L3, trục `visible` tự thành `auto` khi trục kia khác `visible`. Menu các hàng cuối bảng bị cắt ⇒ **mất hoàn toàn khả năng thao tác** trên những hàng đó | ✕ `.admin-card { overflow: hidden; }`<br>▸ `.admin-card { overflow: clip; overflow-clip-margin: 0; }`<br>▸ `/* và tách vùng cuộn ra khỏi vùng bo góc */`<br>▸ `.admin-users-table-wrap { overflow-x: auto; overflow-y: visible; }`<br>▸ `/* giải pháp bền vững: render menu qua portal */`<br>▸ `createPortal(<div className="admin-users-menu" style={{ position:"fixed", …anchorRect }}/>, document.body)` |
| **A-02** | `.admin-shell--light` override 8 biến; ~60 hex sáng còn nguyên (`#6ee7b7` → **1,52:1**, `#fde68a` → **1,25:1**) | Nút bật chế độ sáng ở topbar tạo ra giao diện không đọc được. Vi phạm WCAG 1.4.3 ở mức 3–3,6× | ▸ Đưa mọi màu accent vào biến trong `.admin-shell`:<br>▸ `--admin-ok-fg:#6ee7b7; --admin-ok-bg:rgba(16,185,129,.13);`<br>▸ `--admin-warn-fg:#fde68a; --admin-warn-bg:rgba(245,158,11,.13);`<br>▸ `--admin-danger-fg:#fda4af; --admin-danger-bg:rgba(244,63,94,.13);`<br>▸ `--admin-neutral-fg:#cbd5e1; --admin-info-fg:#60a5fa;`<br>▸ Override đủ bộ trong `.admin-shell--light`:<br>▸ `--admin-ok-fg:#047857; --admin-warn-fg:#b45309;`<br>▸ `--admin-danger-fg:#be123c; --admin-neutral-fg:#475569; --admin-info-fg:#1d4ed8;`<br>▸ **Hoặc** tạm ẩn nút toggle cho tới khi hoàn thiện |
| **A-03** | `@media (max-width:1060px) { .admin-sidebar { transform: translateX(-103%) } }` | Chỉ dịch chuyển ⇒ 9 control vẫn nhận focus khi drawer đóng. Vi phạm WCAG 2.4.3. Scrim ngay bên dưới trong cùng file đã dùng đúng kỹ thuật | ✕ `.admin-sidebar { position: fixed; transform: translateX(-103%); }`<br>▸ `.admin-sidebar { position: fixed; transform: translateX(-103%);`<br>▸ `  visibility: hidden;`<br>▸ `  transition: transform .22s ease, visibility 0s linear .22s; }`<br>▸ `.admin-sidebar.is-open { transform: none; visibility: visible;`<br>▸ `  transition: transform .22s ease, visibility 0s; }`<br>▸ JSX: `<aside inert={!sidebarOpen \|\| undefined}>` |
| **A-04** | `.admin-sidebar { height: 100dvh }` không có `overflow-y`, nằm trong `.admin-shell { overflow: hidden }` | Nội dung tối thiểu ~508px. Dưới ngưỡng đó nút "Chuyển vai trò" bị cắt và không cuộn tới được (điện thoại xoay ngang, cửa sổ thu nhỏ) | ✕ `.admin-sidebar { display:flex; height:100dvh; flex-direction:column; }`<br>▸ `.admin-sidebar { display:flex; height:100dvh; flex-direction:column;`<br>▸ `  overflow-y: auto; overscroll-behavior: contain; }`<br>▸ `.admin-nav { flex: 1 1 auto; min-height: 0; }`<br>▸ `.admin-sidebar__footer { flex: 0 0 auto; }` |
| **A-05** | `const updated = users.find(…)` đọc closure cũ ngay sau `setUsers` | Drawer bị ghi đè bằng dữ liệu **trước** thay đổi ⇒ bảng và drawer nói hai điều khác nhau sau một thao tác thành công | ✕ `const updated = users.find((item) => item.user_id === user.user_id);`<br>✕ `if (updated) setSelectedUser((prev) => (prev ? { ...updated } : prev));`<br>▸ `setSelectedUser((prev) =>`<br>▸ `  prev && prev.user_id === user.user_id ? result.user : prev);` |
| **A-06** | Drawer/modal `UserManagement` có `aria-modal="true"` nhưng không Escape, không focus trap, không focus restore | `aria-modal` là lời hứa nội dung nền đã bị ẩn — không có gì thực hiện. Hai hộp thoại chỉ đóng được bằng chuột, trong khi `RegionStations` và `IotDevices` đã có Escape | ▸ `useEffect(() => {`<br>▸ `  if (!selectedUser && !pendingAction) return;`<br>▸ `  const onKey = (e: KeyboardEvent) => {`<br>▸ `    if (e.key !== "Escape") return;`<br>▸ `    if (pendingAction) closeConfirm(); else closeDrawer();`<br>▸ `  };`<br>▸ `  window.addEventListener("keydown", onKey);`<br>▸ `  return () => window.removeEventListener("keydown", onKey);`<br>▸ `}, [selectedUser, pendingAction]);`<br>▸ Thêm `inert` cho `.admin-content` khi drawer mở<br>▸ Lưu `document.activeElement` khi mở, `.focus()` lại khi đóng |
| **A-07** | `.admin-confirm-scrim { z-index: 60 }` < `.admin-user-drawer { z-index: 61 }` | Scrim xác nhận không phủ được drawer ⇒ drawer vẫn click được trong khi hộp thoại xác nhận đang mở; hai scrim chồng nhau cho độ tối 0,80 thay vì 0,55 | ✕ `.admin-drawer-scrim, .admin-confirm-scrim { z-index: 60; }`<br>▸ `.admin-drawer-scrim  { z-index: 60; }`<br>▸ `.admin-confirm-scrim { z-index: 62; }`<br>✕ `.admin-confirm-modal { z-index: 62; }`<br>▸ `.admin-confirm-modal { z-index: 63; }`<br>▸ Và đặt `inert` cho drawer khi `pendingAction` khác null |

### IV.2 🟠 P1 — Trước UAT

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|---|---|---|---|
| **A-08** | `.admin-topbar` flex không `flex-wrap`; `.admin-area-select select { width: 190px }` cố định | Tại 1150px cần 905px nhưng chỉ có 844px ⇒ tràn 61px, bị `overflow:hidden` cắt thẳng. Dải vỡ 1061–1230px bao trùm laptop 1152px và 1200px | ✕ `.admin-topbar { display:flex; align-items:center; gap:12px; }`<br>▸ `.admin-topbar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }`<br>✕ `.admin-area-select select { width: 190px; }`<br>▸ `.admin-area-select select { width: clamp(130px, 14vw, 190px); }`<br>▸ `@media (max-width: 1280px) { .admin-online-pill { display:none } }`<br>▸ `@media (max-width: 1180px) { .admin-search { display:none } }` |
| **A-09** | `<XAxis dataKey="time" />` với `time` là timestamp ISO thô | Trục X vẽ `2026-08-06T14:00:00Z` ở 10px; tooltip cũng vậy. Hàm `formatClock` đã có sẵn trong cùng file | ▸ `<XAxis dataKey="time" stroke="var(--admin-muted)"`<br>▸ `  tick={{ fontSize: 11 }} minTickGap={30}`<br>▸ `  tickFormatter={(v) => formatClock(v)} />`<br>▸ `<Tooltip labelFormatter={(v) => formatClock(String(v))} … />`<br>▸ Và ghép chuỗi theo timestamp thay vì theo index:<br>▸ `const stamps = [...new Set(series.flatMap(s => s.points.map(p => p.timestamp)))].sort();` |
| **A-10** | `contentStyle={{ background: "#111d2f" }}` hex cứng inline (2 chỗ) | Ở chế độ sáng vẫn là hộp navy đậm với chữ nhãn `#666` mặc định ⇒ ~1,6:1 | ✕ `contentStyle={{ background: "#111d2f", border: "1px solid rgba(148,163,184,.18)" }}`<br>▸ `contentStyle={{ background: "var(--admin-surface-raised)",`<br>▸ `  border: "1px solid var(--admin-border)", borderRadius: 10, fontSize: 12 }}`<br>▸ `labelStyle={{ color: "var(--admin-text)" }}`<br>▸ `itemStyle={{ color: "var(--admin-text)" }}` |
| **A-11** | KPI "Trạng thái kết nối" không guard `loading`; cả 4 `<small>` in số 0 khi chưa có dữ liệu | Hiển thị **"Gián đoạn"** trong suốt thời gian tải — báo động giả mỗi lần vào trang. Thay "chưa biết" bằng "bằng không" (cùng loại `R-13`) | ✕ `<strong>{onlineCount > 0 ? "Trực tuyến" : "Gián đoạn"}</strong>`<br>▸ `<strong>{loading ? "—" : onlineCount > 0 ? "Trực tuyến" : "Gián đoạn"}</strong>`<br>▸ `<small>{loading ? "Đang tải trạng thái…" :`<br>▸ `  \`${onlineCount} Online · ${staleCount} Gián đoạn · ${offlineCount} Ngoại tuyến\`}</small>`<br>▸ Áp dụng cùng mẫu cho 3 `<small>` còn lại |
| **A-12** | `<div className="admin-online-pill"><span />Trực tuyến</div>` — markup tĩnh | Luôn báo "Trực tuyến" bất kể thực tế; mâu thuẫn trực tiếp với KPI "Gián đoạn" trên cùng màn hình. Chỉ báo sai trong sản phẩm giám sát là lỗi nghiêm trọng về niềm tin | ✕ `<div className="admin-online-pill"><span />Trực tuyến</div>`<br>▸ `{systemStatus && (`<br>▸ `  <div className={\`admin-online-pill is-\${systemStatus}\`}>`<br>▸ `    <span />{systemStatus === "online" ? "Trực tuyến" : "Mất kết nối"}`<br>▸ `  </div>`<br>▸ `)}`<br>▸ *Nếu chưa có API: gỡ hẳn, không để chỉ báo giả* |
| **A-13** | Ô tìm kiếm và select khu vực ở topbar không có `value`/`onChange` | Affordance giả xuất hiện trên **mọi** màn hình admin. Gõ vào không có gì xảy ra ⇒ người dùng tưởng hệ thống lỗi | ▸ Nối vào state thật, hoặc:<br>▸ `<input type="search" … disabled`<br>▸ `  title="Tìm kiếm toàn cục — sắp ra mắt" />`<br>▸ ✕ *Ưu tiên: gỡ khỏi topbar cho tới khi có backend* |
| **A-14** | `.admin-search input { outline: 0 }` và `.admin-area-select select { outline: 0 }` không có style thay thế | Xóa focus ring 3px mà `theme.css:124` cung cấp, không thay bằng gì ⇒ **không có chỉ báo focus nào**. Vi phạm WCAG 2.4.7 | ✕ `.admin-search input { outline: 0; }`<br>▸ `.admin-search input:focus-visible {`<br>▸ `  outline: 2px solid var(--admin-primary); outline-offset: 2px; }`<br>▸ `.admin-area-select select:focus-visible {`<br>▸ `  outline: 2px solid var(--admin-primary); outline-offset: 2px; }` |
| **A-15** | `<tr role="button" tabIndex={0}>` chứa `<td>` và một `<button>` bên trong | `role="button"` xóa ngữ nghĩa hàng bảng cho screen reader; `<td>` trở thành con không hợp lệ; button lồng trong button là ARIA không hợp lệ | ✕ `<tr role="button" tabIndex={0} onClick={…} onKeyDown={…}>`<br>▸ `<tr>`<br>▸ `  <td>`<br>▸ `    <button type="button" className="admin-user-open"`<br>▸ `      onClick={() => openUser(user)}>{user.full_name}</button>`<br>▸ `  </td>`<br>▸ `  …`<br>▸ `</tr>`<br>▸ *Đưa hành vi mở lên một button thật trong ô đầu tiên* |
| **A-16** | `onKeyDown={(e) => { if (e.key === "Enter" \|\| e.key === " ") openUser(user); }}` — thiếu `preventDefault` | Space cuộn trang song song với mở drawer. `IotDevices.tsx:462` đã làm đúng ⇒ hai màn hình hành xử khác nhau | ✕ `if (event.key === "Enter" \|\| event.key === " ") openUser(user);`<br>▸ `if (event.key === "Enter" \|\| event.key === " ") {`<br>▸ `  event.preventDefault();`<br>▸ `  openUser(user);`<br>▸ `}` |
| **A-17** | `menuFor` không có click-outside, không có Escape | Menu treo lại khi bấm ra ngoài. `IotDevices` còn thiếu cả `onClick={() => setMenuFor(null)}` mà `UserManagement` có | ▸ `useEffect(() => {`<br>▸ `  if (!menuFor) return;`<br>▸ `  const close = () => setMenuFor(null);`<br>▸ `  const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();`<br>▸ `  document.addEventListener("pointerdown", close);`<br>▸ `  document.addEventListener("keydown", onKey);`<br>▸ `  return () => { document.removeEventListener("pointerdown", close);`<br>▸ `    document.removeEventListener("keydown", onKey); };`<br>▸ `}, [menuFor]);` |
| **A-18** | `.admin-map-marker { color: #fff; background: var(--marker-color) }` | Trắng trên `#10b981` = **2,54:1**, trên `#f59e0b` = **2,15:1**. Trị số PM2.5 — dữ liệu quan trọng nhất — không đọc được | ✕ `.admin-map-marker { color: #fff; background: var(--marker-color); }`<br>▸ `.admin-map-marker {`<br>▸ `  color: #0b1120;`<br>▸ `  background: var(--marker-color);`<br>▸ `  border: 2px solid rgba(255,255,255,.92); }`<br>▸ `.admin-map-marker span { font-size: var(--font-size-xs); }`<br>▸ `.admin-map-marker small { font-size: var(--font-size-2xs); }`<br>▸ `/* #0b1120 trên #10b981 = 9,2:1 · trên #f59e0b = 10,8:1 */` |
| **A-19** | `.admin-map-place { color: #55647a }` (2,78:1), `.admin-map-label { color: #52627a }` (2,71:1) | Dưới ngưỡng AA gần 2× ở cỡ chữ 8,8–9,3px | ✕ `color: #55647a;` / ✕ `color: #52627a;`<br>▸ `color: var(--admin-muted);  /* #8290a7 = 5,24:1 */`<br>▸ `font-size: var(--font-size-2xs);` |
| **A-20** | `.admin-users-table th`, `.admin-alert-log th` dùng `#64748b` | **3,28:1** ở 8,8–9,1px. Tiêu đề cột là mỏ neo điều hướng của bảng | ✕ `color: #64748b;`<br>▸ `color: var(--admin-muted);`<br>▸ `font-size: var(--font-size-2xs);` |
| **A-21** | `.admin-station-row__mark` — offline `#64748b` (3,17:1), invalid `#f43f5e` (4,11:1) trên tint 12% | Trị số bên trong ô trạng thái ở 9,6px không đạt AA | ✕ `background: color-mix(in srgb, var(--state-color) 12%, transparent);`<br>▸ `background: color-mix(in srgb, var(--state-color) 20%, var(--admin-bg));`<br>▸ `--state-color-offline: #94a3b8;  /* thay #64748b */`<br>▸ `--state-color-invalid: #fb7185;  /* thay #f43f5e */`<br>▸ `font-size: var(--font-size-2xs);` |
| **A-22** | `MAP_POSITIONS[index % 5]` — trạm thứ 6 trùng khít trạm thứ 1 | Bản đồ che mất trạm nhưng tiêu đề vẫn báo `{stations.length} trạm` ⇒ nói dối về dữ liệu. `RegionStations.tsx:482` đã từ chối làm điều này | ✕ `const position = MAP_POSITIONS[index % MAP_POSITIONS.length];`<br>▸ `// Dùng toạ độ thật như RegionStations; nếu thiếu thì không vẽ marker`<br>▸ `if (station.map_x == null \|\| station.map_y == null) return null;`<br>▸ `const position = { left: \`${station.map_x}%\`, top: \`${station.map_y}%\` };`<br>▸ Và hiển thị `{n}/{total} trạm có toạ độ` nếu có trạm bị bỏ qua |
| **A-23** | 4 nút dưới 24px: `.admin-card__header > button` (17px), `.admin-device-card__link` (15px), `.admin-error button` (16px), `.admin-mutation-banner button` (15px) | Vi phạm WCAG 2.5.8. `.admin-error button` là **lối thoát duy nhất khi tải lỗi** | ▸ `.admin-card__header > button,`<br>▸ `.admin-device-card__link,`<br>▸ `.admin-error button,`<br>▸ `.admin-mutation-banner button {`<br>▸ `  display: inline-flex; align-items: center;`<br>▸ `  min-height: 24px; padding: 4px 8px;`<br>▸ `  margin: -4px -8px;  /* giữ nguyên vị trí thị giác */`<br>▸ `}` |
| **A-24** | 4 vùng cuộn không có `tabindex`/`role="region"` | Người dùng bàn phím không cuộn ngang được để thấy các cột bên phải bảng thiết bị. Vi phạm WCAG 2.1.1 | ✕ `<div className="admin-devices-table-wrap">`<br>▸ `<div className="admin-devices-table-wrap" tabIndex={0}`<br>▸ `  role="region" aria-label="Bảng thiết bị IoT — cuộn ngang để xem thêm cột">`<br>▸ *Áp dụng tương tự cho 3 vùng còn lại* |
| **A-25** | `mutationMessage` render đồng thời ở banner trang (`role="status"`) và trong modal (`role="alert"`) | Screen reader đọc hai lần với hai mức ưu tiên khác nhau | ▸ Tách hai state:<br>▸ `const [pageMessage, setPageMessage] = useState<Msg \| null>(null);`<br>▸ `const [modalError, setModalError] = useState<string \| null>(null);`<br>▸ ▸ Lỗi khi modal mở → chỉ `setModalError`<br>▸ ▸ Thành công (modal đã đóng) → chỉ `setPageMessage` |
| **A-26** | 90 khai báo `font-size` bằng rem thập phân tự chế; thang `--font-size-*` dùng **0 lần**; sàn 8,48px | 23 bậc chữ trong khoảng 5,4px = nhiễu, không phải thứ bậc. Dưới sàn 12px của MD3/HIG | ▸ Thay toàn bộ bằng thang có sẵn:<br>▸ `0,52–0,58rem → var(--font-size-2xs)  /* 11px */`<br>▸ `0,60–0,66rem → var(--font-size-xs)   /* 12px */`<br>▸ `0,68–0,76rem → var(--font-size-sm)   /* 14px */`<br>▸ `0,80–0,90rem → var(--font-size-base) /* 16px */`<br>▸ *Không cần thêm token mới — `--font-size-2xs` đã có ở `theme.css:56`* |
| **A-27** | `.admin-card__header h2 { font-size:.76rem }` (12,16px); `.admin-drawer-section h3 { font-size:.62rem }` (9,92px); `.admin-kpi > strong` 23,2px | `h2` nhỏ hơn chữ nội dung; `h3` bằng 43% một con số trang trí ⇒ thứ bậc thị giác đảo ngược | ✕ `.admin-card__header h2 { font-size: .76rem; }`<br>▸ `.admin-card__header h2 { font-size: var(--font-size-sm); font-weight: 600; }`<br>✕ `.admin-drawer-section h3 { font-size: .62rem; }`<br>▸ `.admin-drawer-section h3 { font-size: var(--font-size-xs); font-weight: 700; }`<br>▸ `.admin-kpi > strong { font-size: var(--font-size-2xl); }` |
| **A-28** | `min-height: calc(100dvh - 110px)` ở 4 file | Số 110 sai (thực tế 74 + 51 = 125) ⇒ mọi trang admin luôn dư 15px cuộn dọc dù trống | ✕ `min-height: calc(100dvh - 110px);` *(cả 4 file)*<br>▸ `/* AdminShell.css — nguồn duy nhất */`<br>▸ `.admin-shell { --admin-topbar-h: 74px; --admin-footer-h: 51px; }`<br>▸ `.admin-content > .admin-dashboard {`<br>▸ `  min-height: calc(100dvh - var(--admin-topbar-h) - var(--admin-footer-h)); }` |
| **A-29** | `isSelf = (u) => u.role === "admin" && u.full_name === userName` | Nhận diện bằng tên hiển thị ⇒ hai admin trùng tên đều bị khóa thao tác | ✕ `const isSelf = (user) => user.role === "admin" && user.full_name === userName;`<br>▸ `const isSelf = (user: AdminUser) => user.user_id === currentUserId;`<br>▸ *Lấy `currentUserId` từ `useAuth()` thay vì so tên* |
| **A-30** | Bảng thiết bị 8 cột `white-space: nowrap`, chuyển card ở 900px nhưng cần ~1080px | Cuộn ngang trên toàn dải 900–1350px; kết hợp A-01 thì thao tác gãy hoàn toàn trên laptop | ✕ `@media (max-width: 900px) { .admin-users-desktop { display: none } }`<br>▸ `@media (max-width: 1180px) { .admin-users-desktop { display: none } }`<br>▸ *Hoặc ẩn bớt 2 cột phụ (Firmware, Cấu hình) trong dải 900–1180px:*<br>▸ `@media (max-width:1180px){ .admin-devices-table :is(th,td):nth-child(5),`<br>▸ `  .admin-devices-table :is(th,td):nth-child(6) { display:none } }` |

### IV.3 🟡 P2 — Nợ kỹ thuật

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|---|---|---|---|
| **A-31** | 7 breakpoint khác nhau trên 5 file (1060/1180/900/760/720/520/480) | Dải 1060–1180 và 900–1060 cho layout lai; dải 480–520 đổi ở hai thời điểm | ▸ `/* theme.css — nguồn duy nhất */`<br>▸ `/* --bp-xl: 1180px; --bp-lg: 1024px; --bp-md: 768px; --bp-sm: 480px; */`<br>▸ *Chuẩn hoá cả 5 file về 4 điểm ngắt trên* |
| **A-32** | Bảng desktop và card mobile luôn mount đồng thời | 2× node, 2× listener, `menuFor` điều khiển hai menu cùng lúc | ▸ `const isCompact = useMediaQuery("(max-width: 1180px)");`<br>▸ `return isCompact ? renderMobileCards() : renderTable();`<br>▸ *Chỉ render một nhánh* |
| **A-33** | `.admin-users-desktop` / `.admin-users-mobile` chỉ tồn tại trong `@media` của `UserManagement.css` | Không có rule base; `IotDevices` dùng nhưng không khai báo ⇒ layout phụ thuộc file khác | ▸ Chuyển hai class sang `AdminShell.css` với rule base đầy đủ:<br>▸ `.admin-users-desktop { display: block; }`<br>▸ `.admin-users-mobile  { display: none; }`<br>▸ `@media (max-width:1180px){ .admin-users-desktop{display:none}`<br>▸ `  .admin-users-mobile{display:block} }`<br>▸ *Hoặc bỏ hẳn khi làm A-32* |
| **A-34** | 3 khối toolbar giống hệt từng byte ở 3 file | 10 thuộc tính × 3 = 30 dòng trùng; sửa một chỗ quên hai chỗ | ▸ `/* AdminShell.css */`<br>▸ `.admin-toolbar { display:flex; flex-wrap:wrap; align-items:center;`<br>▸ `  gap:10px; margin-bottom:16px; padding:13px;`<br>▸ `  border:1px solid var(--admin-border); border-radius:14px;`<br>▸ `  background: var(--admin-surface); }`<br>▸ JSX: `className="admin-toolbar admin-users-toolbar"` |
| **A-35** | `.admin-station-status` ≡ `.admin-device-status` (4 biến thể × 2) | Rule-for-rule giống nhau ở hai file khác nhau | ▸ Gộp thành một class dùng chung trong `AdminShell.css`:<br>▸ `.admin-status-chip { … }`<br>▸ `.admin-status-chip.is-online  { color:var(--admin-ok-fg);     background:var(--admin-ok-bg) }`<br>▸ `.admin-status-chip.is-stale   { color:var(--admin-warn-fg);   background:var(--admin-warn-bg) }`<br>▸ `.admin-status-chip.is-offline { color:var(--admin-neutral-fg); background:var(--admin-neutral-bg) }`<br>▸ `.admin-status-chip.is-invalid { color:var(--admin-danger-fg); background:var(--admin-danger-bg) }` |
| **A-36** | `.admin-station-drawer` ≈ `.admin-user-drawer` — 9/10 thuộc tính trùng | Chỉ khác `width` (460 vs 470) | ▸ `.admin-drawer { position:fixed; z-index:61; top:0; right:0;`<br>▸ `  display:flex; width:min(var(--drawer-w,460px),100%); height:100dvh;`<br>▸ `  flex-direction:column; border-left:1px solid var(--admin-border);`<br>▸ `  background:var(--admin-surface); box-shadow:-18px 0 50px rgba(2,6,23,.4); }`<br>▸ `.admin-device-drawer { --drawer-w: 470px; }` |
| **A-37** | `.admin-user-audit` và `.admin-user-audit-list` — hai style timeline gần trùng | Hai cách trình bày cùng một loại nội dung | ▸ Giữ một class, xoá class còn lại và cập nhật JSX tương ứng |
| **A-38** | 7 khai báo `!important` | Hệ quả của style theo cấu trúc thẻ (`.parent small`) thay vì class riêng | ✕ `.admin-station-row__time { font-size: .55rem !important; }`<br>▸ `.admin-station-row__body .admin-station-row__time { font-size: var(--font-size-2xs); }`<br>▸ *Tăng specificity bằng ngữ cảnh thay vì `!important` — áp dụng cho cả 7 chỗ* |
| **A-39** | 4 nguồn màu trạng thái mâu thuẫn; marker JS `#10b981` vs chip CSS `#6ee7b7` | Cùng một trạng thái, hai sắc màu cạnh nhau trên cùng màn hình | ▸ `// admin/statusColors.ts — nguồn duy nhất`<br>▸ `export const STATUS = {`<br>▸ `  online:  { marker:"#10b981", chip:"var(--admin-ok-fg)" },`<br>▸ `  stale:   { marker:"#f59e0b", chip:"var(--admin-warn-fg)" },`<br>▸ `  offline: { marker:"#94a3b8", chip:"var(--admin-neutral-fg)" },`<br>▸ `  invalid: { marker:"#fb7185", chip:"var(--admin-danger-fg)" },`<br>▸ `} as const;`<br>▸ *Import ở cả 3 màn hình + 2 mảng LEGEND* |
| **A-40** | `IotDevices` phụ thuộc `UserManagement.css` + `RegionStations.css`; admin phụ thuộc `.sr-only` (`AppShell.css`) và `.is-spinning` (`styles.css`) | Chạy được nhờ bundler gom CSS, nhưng quan hệ phụ thuộc không nhìn thấy được và sẽ đứt khi lazy-load route | ▸ Chuyển các class dùng chung lên `AdminShell.css`:<br>▸ `.admin-toolbar, .admin-search-field, .admin-select,`<br>▸ `.admin-table, .admin-menu, .admin-skeleton, .admin-drawer`<br>▸ ▸ Chuyển `.sr-only` và `.is-spinning` từ `AppShell.css`/`styles.css` sang `theme.css` (utility toàn cục) |
| **A-41** | Tab "Sự kiện" và "Nhật ký" render cùng mảng `events` | Hai tab, một nguồn dữ liệu — người dùng bấm qua lại thấy y hệt | ▸ Gộp thành một tab "Nhật ký", hoặc<br>▸ Lấy audit từ endpoint riêng: `getDeviceAuditLog(deviceId)` |
| **A-42** | Thiết bị `deactivated` vẫn được đề nghị "Đặt bảo trì" | Không có ý nghĩa nghiệp vụ; gây nhầm lẫn khi đứng cạnh "Kích hoạt lại" | ✕ `{device.lifecycle !== "maintenance" && <button>Đặt bảo trì</button>}`<br>▸ `{device.lifecycle === "active" && <button>Đặt bảo trì</button>}` |
| **A-43** | `if (!reason.trim()) { … return; }` không bao giờ chạy | Nút submit đã `disabled={submitting \|\| !reason.trim()}`. Vi phạm CLAUDE.md §2 | ✕ `if (!reason.trim()) {`<br>✕ `  setMutationMessage({ type: "error", text: "Lý do thay đổi là bắt buộc…" });`<br>✕ `  return;`<br>✕ `}`<br>▸ *Giữ `disabled` + thêm `aria-describedby` trỏ tới dòng hướng dẫn* |
| **A-44** | `1480px` (`.admin-dashboard`) vs `1440px` (`.admin-content > :not(…)`) | Nội dung dịch ngang 20px mỗi bên khi chuyển giữa màn hình admin và màn hình dùng chung | ▸ `.admin-shell { --admin-content-max: 1440px; }`<br>▸ `.admin-dashboard,`<br>▸ `.admin-content > :not(.admin-dashboard):not(.admin-footer) {`<br>▸ `  width: min(var(--admin-content-max), 100%);`<br>▸ `  margin-inline: auto; padding: 28px 26px 34px; }` |
| **A-45** | `.admin-shell` remap 5/9 bậc slate; `--color-border-strong`, `--color-decorative`, `--color-*-50` giữ giá trị sáng | 7 màn hình resident render bên trong `AdminShell` (`App.tsx:41-52`) dùng những token này | ▸ Bổ sung vào `.admin-shell`:<br>▸ `--color-slate-300: var(--admin-border);`<br>▸ `--color-slate-400: var(--admin-muted);`<br>▸ `--color-slate-500: var(--admin-muted);`<br>▸ `--color-slate-600: var(--admin-muted);`<br>▸ `--color-slate-800: var(--admin-surface-raised);`<br>▸ `--color-warning-50: rgba(245,158,11,.13);`<br>▸ `--color-success-50: rgba(16,185,129,.13);`<br>▸ `--color-danger-50:  rgba(244,63,94,.13);` |
| **A-46** | `lightMode` là state cục bộ; không đặt `color-scheme`; bỏ qua `prefers-color-scheme` | Mất lựa chọn khi reload; thanh cuộn và form control native lệch pha với giao diện | ▸ `const [lightMode, setLightMode] = useState(`<br>▸ `  () => localStorage.getItem("admin-theme") === "light");`<br>▸ `useEffect(() => {`<br>▸ `  localStorage.setItem("admin-theme", lightMode ? "light" : "dark");`<br>▸ `}, [lightMode]);`<br>▸ `.admin-shell { color-scheme: dark; }`<br>▸ `.admin-shell--light { color-scheme: light; }` |

### IV.4 ⚪ P3 — Đánh bóng

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|---|---|---|---|
| **A-47** | `<b aria-label={\`${n} đề xuất chờ duyệt\`}>{n}</b>` | `aria-label` trên phần tử generic không có role bị nhiều AT bỏ qua ⇒ chỉ đọc "3" | ✕ `<b aria-label={\`${count} đề xuất chờ duyệt\`}>{count}</b>`<br>▸ `<b aria-hidden="true">{count}</b>`<br>▸ `<span className="sr-only">{count} đề xuất chờ duyệt</span>` |
| **A-48** | `moduleCopy` khai báo 4 module, chỉ `"settings"` còn dùng | Code chết kể từ khi `users`/`regions`/`devices` được hiện thực hoá | ✕ `users: { … }, regions: { … }, devices: { … },`<br>▸ `type ModuleKey = "settings";`<br>▸ *Giữ lại đúng entry đang dùng* |
| **A-49** | `.admin-dashboard__header h1 { font-size: clamp(1.35rem, 2vw, 1.8rem) }` | `2vw` tính theo viewport, nhưng container thực là `viewport − 258px` ⇒ tiêu đề không co giãn theo khung thật của nó | ✕ `font-size: clamp(1.35rem, 2vw, 1.8rem);`<br>▸ `font-size: clamp(1.35rem, 1.2rem + 1cqi, 1.8rem);`<br>▸ `/* và đặt container-type: inline-size trên .admin-content */` |
| **A-50** | Bảng nhật ký cảnh báo không có skeleton lúc tải | Chỉ hiện hàng tiêu đề trống — trong khi 3 khối khác trên cùng trang đã có skeleton | ▸ `{loading && (`<br>▸ `  <tbody>{Array.from({ length: 4 }, (_, i) => (`<br>▸ `    <tr key={i}><td colSpan={5}>`<br>▸ `      <div className="admin-skeleton admin-skeleton--row" />`<br>▸ `    </td></tr>))}</tbody>`<br>▸ `)}` |

---

## V. Patch chi tiết

### V.1 `AdminShell.css` — Sidebar off-canvas và khả năng cuộn (A-03, A-04)

```css
/* ===== TRƯỚC ===== */
.admin-sidebar {
  position: relative; z-index: 60;
  display: flex; height: 100dvh; flex-direction: column;
}
@media (max-width: 1060px) {
  .admin-sidebar { position: fixed; transform: translateX(-103%); }
  .admin-sidebar.is-open { transform: none; }
}

/* ===== SAU ===== */
.admin-sidebar {
  position: relative; z-index: 60;
  display: flex; height: 100dvh; flex-direction: column;
  overflow-y: auto;                 /* A-04: nội dung ~508px phải cuộn được */
  overscroll-behavior: contain;
}
.admin-nav              { flex: 1 1 auto; min-height: 0; }
.admin-sidebar__footer  { flex: 0 0 auto; }

@media (max-width: 1060px) {
  .admin-sidebar {
    position: fixed;
    transform: translateX(-103%);
    visibility: hidden;             /* A-03: gỡ khỏi tab order khi đóng */
    transition: transform .22s ease, visibility 0s linear .22s;
  }
  .admin-sidebar.is-open {
    transform: none;
    visibility: visible;
    transition: transform .22s ease, visibility 0s;
  }
}
```

```tsx
// AdminShell.tsx — bổ sung inert cho AT không hỗ trợ visibility
<aside
  className={`admin-sidebar${sidebarOpen ? " is-open" : ""}`}
  inert={!sidebarOpen || undefined}
>
```

### V.2 `AdminShell.css` — Hệ token màu trạng thái đầy đủ (A-02, A-35, A-39)

```css
.admin-shell {
  /* --- nền & chữ (giữ nguyên) --- */
  --admin-bg: #07111f;
  --admin-sidebar: #0b1526;
  --admin-surface: #111d2f;
  --admin-surface-raised: #172438;
  --admin-border: rgba(148, 163, 184, 0.14);
  --admin-text: #f8fafc;
  --admin-muted: #8290a7;
  --admin-primary: #2563eb;
  --admin-primary-soft: rgba(37, 99, 235, 0.15);

  /* --- MỚI: màu trạng thái, thay ~60 hex rải rác --- */
  --admin-ok-fg:       #6ee7b7;  --admin-ok-bg:      rgba(16, 185, 129, 0.13);
  --admin-warn-fg:     #fde68a;  --admin-warn-bg:    rgba(245, 158, 11, 0.13);
  --admin-danger-fg:   #fda4af;  --admin-danger-bg:  rgba(244, 63, 94, 0.13);
  --admin-neutral-fg:  #cbd5e1;  --admin-neutral-bg: rgba(100, 116, 139, 0.18);
  --admin-info-fg:     #60a5fa;  --admin-info-bg:    rgba(59, 130, 246, 0.11);
  --admin-accent-fg:   #d8b4fe;  --admin-accent-bg:  rgba(168, 85, 247, 0.14);
  --admin-attention:   #fbbf24;

  /* --- MỚI: remap đủ bậc slate cho màn hình resident lồng bên trong (A-45) --- */
  --color-slate-300: var(--admin-border);
  --color-slate-400: var(--admin-muted);
  --color-slate-500: var(--admin-muted);
  --color-slate-600: var(--admin-muted);
  --color-slate-800: var(--admin-surface-raised);
  --color-warning-50: var(--admin-warn-bg);
  --color-success-50: var(--admin-ok-bg);
  --color-danger-50:  var(--admin-danger-bg);

  /* --- MỚI: chiều cao chrome, thay magic 110px ở 4 file (A-28) --- */
  --admin-topbar-h: 74px;
  --admin-footer-h: 51px;
  --admin-content-max: 1440px;      /* A-44 */

  color-scheme: dark;               /* A-46 */
}

.admin-shell--light {
  --admin-bg: #f3f6fb;
  --admin-sidebar: #fff;
  --admin-surface: #fff;
  --admin-surface-raised: #f8fafc;
  --admin-border: rgba(15, 23, 42, 0.11);
  --admin-text: #0f172a;
  --admin-muted: #64748b;
  --admin-primary-soft: #dbeafe;

  /* --- MỚI: override đủ bộ màu trạng thái (A-02) --- */
  --admin-ok-fg:      #047857;  --admin-ok-bg:      rgba(16, 185, 129, 0.12);
  --admin-warn-fg:    #b45309;  --admin-warn-bg:    rgba(245, 158, 11, 0.14);
  --admin-danger-fg:  #be123c;  --admin-danger-bg:  rgba(244, 63, 94, 0.10);
  --admin-neutral-fg: #475569;  --admin-neutral-bg: rgba(100, 116, 139, 0.12);
  --admin-info-fg:    #1d4ed8;  --admin-info-bg:    rgba(59, 130, 246, 0.10);
  --admin-accent-fg:  #7e22ce;  --admin-accent-bg:  rgba(168, 85, 247, 0.11);
  --admin-attention:  #b45309;

  color-scheme: light;              /* A-46 */
}
```

Kiểm chứng tương phản sau khi sửa (trên `#fff`):

| Token | Giá trị light | Tỷ lệ | Đạt |
|---|---|---|---|
| `--admin-ok-fg` | `#047857` | 5,32:1 | ✅ |
| `--admin-warn-fg` | `#b45309` | 5,04:1 | ✅ |
| `--admin-danger-fg` | `#be123c` | 6,42:1 | ✅ |
| `--admin-neutral-fg` | `#475569` | 7,49:1 | ✅ |
| `--admin-info-fg` | `#1d4ed8` | 7,04:1 | ✅ |
| `--admin-accent-fg` | `#7e22ce` | 7,10:1 | ✅ |

### V.3 `AdminShell.css` — Chip trạng thái dùng chung (A-35, A-39)

```css
/* Thay .admin-station-status (RegionStations.css) và
   .admin-device-status (IotDevices.css) — xoá cả hai khối cũ */
.admin-status-chip {
  display: inline-flex;
  min-height: 24px;                        /* A-23: đạt ngưỡng WCAG 2.5.8 */
  align-items: center;
  gap: 5px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: var(--font-size-2xs);         /* A-26: 11px thay cho 8,96px */
  font-weight: 700;
  white-space: nowrap;
}
.admin-status-chip.is-online  { color: var(--admin-ok-fg);      background: var(--admin-ok-bg); }
.admin-status-chip.is-stale   { color: var(--admin-warn-fg);    background: var(--admin-warn-bg); }
.admin-status-chip.is-offline { color: var(--admin-neutral-fg); background: var(--admin-neutral-bg); }
.admin-status-chip.is-invalid { color: var(--admin-danger-fg);  background: var(--admin-danger-bg); }
```

### V.4 `admin/statusColors.ts` — Nguồn màu trạng thái duy nhất (A-39)

```ts
/** Nguồn duy nhất cho màu trạng thái admin.
 *  marker = màu nền đặc (dùng cho pin bản đồ, cần chữ #0b1120 đè lên).
 *  chip   = biến CSS cho chữ trên nền tint (tự đổi theo dark/light).
 *  Thay thế: getDisplayState, getConnectivity và 2 mảng LEGEND. */
export type AdminStatus = "online" | "stale" | "offline" | "invalid";

export const ADMIN_STATUS: Record<AdminStatus, {
  marker: string; chipVar: string; label: string;
}> = {
  online:  { marker: "#10b981", chipVar: "var(--admin-ok-fg)",      label: "Online" },
  stale:   { marker: "#f59e0b", chipVar: "var(--admin-warn-fg)",    label: "Dữ liệu cũ" },
  offline: { marker: "#94a3b8", chipVar: "var(--admin-neutral-fg)", label: "Offline" },
  invalid: { marker: "#fb7185", chipVar: "var(--admin-danger-fg)",  label: "Invalid" },
};

export const ADMIN_LEGEND = (Object.keys(ADMIN_STATUS) as AdminStatus[])
  .map((key) => ({ key, ...ADMIN_STATUS[key] }));
```

### V.5 `UserManagement.tsx` — Đồng bộ drawer sau mutation (A-05)

```tsx
/* ===== TRƯỚC ===== */
setUsers((prev) =>
  prev.map((item) => (item.user_id === user.user_id ? result.user : item)),
);
const updated = users.find((item) => item.user_id === user.user_id);
if (updated) setSelectedUser((prev) => (prev ? { ...updated } : prev));

/* ===== SAU =====
   `users` trong closure là snapshot của lần render trước — đọc nó sau setUsers
   luôn trả về dữ liệu CŨ. Dùng thẳng result.user từ backend. */
setUsers((prev) =>
  prev.map((item) => (item.user_id === user.user_id ? result.user : item)),
);
setSelectedUser((prev) =>
  prev && prev.user_id === user.user_id ? result.user : prev,
);
```

### V.6 `UserManagement.tsx` — Escape, focus trap, focus restore (A-06)

```tsx
const lastFocused = useRef<HTMLElement | null>(null);

const openUser = (user: AdminUser) => {
  lastFocused.current = document.activeElement as HTMLElement | null;
  setSelectedUser(user);
  setMutationMessage(null);
};

const closeDrawer = () => {
  setSelectedUser(null);
  lastFocused.current?.focus();          // trả focus về hàng vừa mở
  lastFocused.current = null;
};

useEffect(() => {
  if (!selectedUser && !pendingAction) return;
  const onKey = (event: KeyboardEvent) => {
    if (event.key !== "Escape") return;
    event.stopPropagation();
    if (pendingAction) closeConfirm();    // lớp trong đóng trước
    else closeDrawer();
  };
  window.addEventListener("keydown", onKey);
  return () => window.removeEventListener("keydown", onKey);
}, [selectedUser, pendingAction]);
```

```tsx
{/* Ẩn nội dung nền khỏi AT khi drawer mở — thực hiện lời hứa aria-modal */}
<div className="admin-content" inert={selectedUser ? true : undefined}>
  …
</div>
```

### V.7 `UserManagement.css` — Thứ tự lớp phủ (A-07)

```css
/* ===== TRƯỚC ===== */
.admin-drawer-scrim,
.admin-confirm-scrim { z-index: 60; }
.admin-user-drawer   { z-index: 61; }
.admin-confirm-modal { z-index: 62; }

/* ===== SAU =====
   Modal xác nhận mở ĐÈ LÊN drawer, nên scrim của nó phải cao hơn drawer. */
.admin-drawer-scrim  { z-index: 60; }
.admin-user-drawer   { z-index: 61; }
.admin-confirm-scrim { z-index: 62; }
.admin-confirm-modal { z-index: 63; }
```

```tsx
{/* Và chặn tương tác với drawer khi modal xác nhận đang mở */}
<aside className="admin-user-drawer" inert={pendingAction ? true : undefined}>
```

### V.8 `AdminDashboard.tsx` — Trạng thái tải trung thực (A-11)

```tsx
/* ===== TRƯỚC ===== */
<div className="admin-kpi">
  <span>Trạng thái kết nối</span>
  <strong>{onlineCount > 0 ? "Trực tuyến" : "Gián đoạn"}</strong>
  <small>{onlineCount} Online · {staleCount} Gián đoạn · {offlineCount} Ngoại tuyến</small>
</div>

/* ===== SAU =====
   Trong lúc tải, onlineCount = 0 nên bản cũ khẳng định "Gián đoạn" —
   một báo động giả ở vị trí nổi bật nhất mỗi lần vào trang. */
<div className="admin-kpi">
  <span>Trạng thái kết nối</span>
  <strong>{loading ? "—" : onlineCount > 0 ? "Trực tuyến" : "Gián đoạn"}</strong>
  <small>
    {loading
      ? "Đang tải trạng thái…"
      : `${onlineCount} Online · ${staleCount} Gián đoạn · ${offlineCount} Ngoại tuyến`}
  </small>
</div>
```

Áp dụng cùng nguyên tắc cho 3 KPI còn lại: không bao giờ in số `0` khi giá trị thật là "chưa biết".

### V.9 `AdminDashboard.tsx` — Trục thời gian và tooltip (A-09, A-10)

```tsx
/* ===== TRƯỚC ===== */
const mergeHistory = (series: StationSeries[]): ChartRow[] => {
  const maxLength = Math.max(0, ...series.map((item) => item.points.length));
  return Array.from({ length: maxLength }, (_, index) => {
    const row: ChartRow = { time: series[0]?.points[index]?.timestamp ?? `${index + 1}` };
    series.forEach(({ stationId, points }) => {
      const point = points[index];
      if (point) row[stationId] = point.pm25;
    });
    return row;
  });
};

/* ===== SAU =====
   Ghép theo timestamp thay vì theo chỉ số mảng — hai trạm lệch mốc thời gian
   hoặc khác số điểm sẽ không còn bị xếp sai cột. */
const mergeHistory = (series: StationSeries[]): ChartRow[] => {
  const stamps = [...new Set(series.flatMap((s) => s.points.map((p) => p.timestamp)))].sort();
  return stamps.map((time) => {
    const row: ChartRow = { time };
    series.forEach(({ stationId, points }) => {
      const point = points.find((p) => p.timestamp === time);
      if (point) row[stationId] = point.pm25;   // thiếu điểm ⇒ để trống, không điền 0
    });
    return row;
  });
};
```

```tsx
<XAxis
  dataKey="time"
  stroke="var(--admin-muted)"
  tick={{ fontSize: 11 }}
  minTickGap={30}
  tickFormatter={(value) => formatClock(String(value))}
/>
<Tooltip
  labelFormatter={(value) => formatClock(String(value))}
  contentStyle={{
    background: "var(--admin-surface-raised)",
    border: "1px solid var(--admin-border)",
    borderRadius: 10,
    fontSize: 12,
  }}
  labelStyle={{ color: "var(--admin-text)" }}
  itemStyle={{ color: "var(--admin-text)" }}
/>
```

### V.10 `AdminDashboard.css` + `AdminDashboard.tsx` — Marker bản đồ (A-18, A-22)

```css
/* ===== TRƯỚC ===== */
.admin-map-marker       { color: #fff; background: var(--marker-color); }
.admin-map-marker span  { font-size: .67rem; font-weight: 800; }
.admin-map-marker small { font-size: .52rem; }   /* 8,32px */
.admin-map-place        { color: #55647a; font-size: .55rem; }
.admin-map-label        { color: #52627a; font-size: .58rem; }

/* ===== SAU =====
   Bảng màu severity được thiết kế làm CHỮ trên nền tối, không phải làm NỀN
   cho chữ trắng. Đảo lại: chữ tối trên nền severity. */
.admin-map-marker {
  color: #0b1120;                              /* 9,2:1 trên #10b981 · 10,8:1 trên #f59e0b */
  background: var(--marker-color);
  border: 2px solid rgba(255, 255, 255, 0.92);
}
.admin-map-marker span  { font-size: var(--font-size-xs); font-weight: 800; }
.admin-map-marker small { font-size: var(--font-size-2xs); }
.admin-map-place        { color: var(--admin-muted); font-size: var(--font-size-2xs); }
.admin-map-label        { color: var(--admin-muted); font-size: var(--font-size-2xs); }
```

```tsx
/* ===== TRƯỚC ===== */
const MAP_POSITIONS = [
  { left: "23%", top: "62%" }, { left: "51%", top: "39%" },
  { left: "74%", top: "65%" }, { left: "34%", top: "31%" },
  { left: "82%", top: "27%" },
];
const position = MAP_POSITIONS[index % MAP_POSITIONS.length];

/* ===== SAU =====
   Toạ độ giả với `% 5` khiến trạm thứ 6 che khuất hoàn toàn trạm thứ 1,
   trong khi tiêu đề vẫn báo đủ số trạm. RegionStations.tsx đã từ chối làm
   điều này — giữ nguyên chuẩn đó ở đây. */
const plotted = stations.filter((s) => s.map_x != null && s.map_y != null);
…
{plotted.map((station) => (
  <button
    key={station.station_id}
    className="admin-map-marker"
    style={{ left: `${station.map_x}%`, top: `${station.map_y}%` }}
    …
  />
))}
{plotted.length < stations.length && (
  <p className="admin-map-note">
    Hiển thị {plotted.length}/{stations.length} trạm — {stations.length - plotted.length} trạm chưa có toạ độ.
  </p>
)}
```

### V.11 `AdminShell.css` — Topbar không tràn (A-08)

```css
/* ===== TRƯỚC ===== */
.admin-topbar             { display: flex; align-items: center; gap: 12px; }
.admin-search             { width: min(280px, 24vw); }
.admin-area-select select { width: 190px; }

/* ===== SAU =====
   Tại 1150px: cần 905px, có 844px ⇒ tràn 61px và bị overflow:hidden cắt thẳng.
   Ba lớp phòng vệ: cho phép wrap, cho select co lại, ẩn dần phần tử phụ. */
.admin-topbar             { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.admin-search             { flex: 1 1 200px; min-width: 0; max-width: 280px; }
.admin-area-select select { width: clamp(130px, 14vw, 190px); }

@media (max-width: 1280px) { .admin-online-pill { display: none; } }
@media (max-width: 1180px) { .admin-search      { display: none; } }
```

### V.12 `UserManagement.tsx` — Ngữ nghĩa hàng bảng (A-15, A-16)

```tsx
/* ===== TRƯỚC =====
   role="button" trên <tr> xoá ngữ nghĩa hàng bảng; <td> thành con không hợp lệ;
   và bên trong lại có <button> menu ⇒ button lồng button. */
<tr
  key={user.user_id}
  onClick={() => openUser(user)}
  role="button"
  tabIndex={0}
  onKeyDown={(event) => {
    if (event.key === "Enter" || event.key === " ") openUser(user);
  }}
>
  <td>{user.full_name}</td>
  …
</tr>

/* ===== SAU =====
   Hàng giữ nguyên ngữ nghĩa <tr>; hành vi mở nằm trên một button thật ở ô đầu. */
<tr key={user.user_id}>
  <td>
    <button type="button" className="admin-user-open" onClick={() => openUser(user)}>
      {user.full_name}
    </button>
  </td>
  …
</tr>
```

```css
.admin-user-open {
  display: block;
  width: 100%;
  padding: 0;
  color: inherit;
  background: transparent;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
```

> Nếu bắt buộc phải giữ hàng click được, tối thiểu phải thêm `event.preventDefault()` cho phím Space — như `IotDevices.tsx:462` đã làm.

### V.13 `UserManagement.tsx` / `IotDevices.tsx` — Đóng menu (A-17)

```tsx
useEffect(() => {
  if (!menuFor) return;
  const close = () => setMenuFor(null);
  const onKey = (event: KeyboardEvent) => {
    if (event.key === "Escape") close();
  };
  // pointerdown chạy trước click ⇒ menu đóng trước khi handler của nút khác chạy
  document.addEventListener("pointerdown", close);
  document.addEventListener("keydown", onKey);
  return () => {
    document.removeEventListener("pointerdown", close);
    document.removeEventListener("keydown", onKey);
  };
}, [menuFor]);
```

```tsx
{/* Ngăn pointerdown bên trong menu tự đóng chính nó */}
<div className="admin-users-menu" onPointerDown={(e) => e.stopPropagation()}>
```

### V.14 Gộp toolbar và drawer dùng chung (A-34, A-36)

```css
/* AdminShell.css — thêm mới, xoá 3 khối toolbar và 1 khối drawer trùng lặp */
.admin-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding: var(--space-3);
  border: 1px solid var(--admin-border);
  border-radius: 14px;
  background: var(--admin-surface);
}

.admin-drawer {
  position: fixed;
  z-index: 61;
  top: 0;
  right: 0;
  display: flex;
  width: min(var(--drawer-w, 460px), 100%);
  height: 100dvh;
  flex-direction: column;
  border-left: 1px solid var(--admin-border);
  background: var(--admin-surface);
  box-shadow: -18px 0 50px rgba(2, 6, 23, 0.4);
}
.admin-device-drawer { --drawer-w: 470px; }

@media (max-width: 720px) {
  .admin-drawer { width: 100%; }
}
```

```
Xoá khỏi UserManagement.css : .admin-users-toolbar   (10 dòng) · .admin-user-drawer    (10 dòng)
Xoá khỏi RegionStations.css : .admin-regions-toolbar (10 dòng) · .admin-station-drawer (10 dòng)
                              .admin-station-status  (28 dòng)
Xoá khỏi IotDevices.css     : .admin-devices-toolbar (10 dòng) · .admin-device-status  (28 dòng)
                                                              ────────────────────────────────
                                                              Tổng: ~106 dòng CSS trùng lặp
```

### V.15 Thay magic number bằng token (A-26, A-28)

```css
/* Xoá ở cả 4 file: AdminDashboard.css, UserManagement.css,
   RegionStations.css, IotDevices.css */
✕ .admin-module-page, .admin-users-page,
✕ .admin-regions-page, .admin-devices-page { min-height: calc(100dvh - 110px); }

/* AdminShell.css — nguồn duy nhất, suy ra từ chiều cao thật của chrome */
.admin-content > .admin-dashboard {
  min-height: calc(100dvh - var(--admin-topbar-h) - var(--admin-footer-h));
}
```

Bảng ánh xạ cỡ chữ (áp dụng cho toàn bộ 5 file CSS admin):

| Giá trị hiện tại | px | Token thay thế | px mới |
|---|---|---|---|
| `.52` – `.58rem` | 8,3 – 9,3 | `var(--font-size-2xs)` | 11 |
| `.60` – `.66rem` | 9,6 – 10,6 | `var(--font-size-xs)` | 12 |
| `.68` – `.76rem` | 10,9 – 12,2 | `var(--font-size-sm)` | 14 |
| `.80` – `.90rem` | 12,8 – 14,4 | `var(--font-size-base)` | 16 |
| `1.45rem` | 23,2 | `var(--font-size-2xl)` | 24 |

---

## VI. Thứ tự triển khai đề xuất

| Đợt | Nội dung | Mã lỗi | Ước lượng | Rủi ro |
|---|---|---|---|---|
| **1** | Khôi phục chức năng đã mất | A-01, A-05, A-07 | 4h | Thấp — thay đổi cục bộ, có thể kiểm chứng ngay |
| **2** | Truy cập bàn phím & hộp thoại | A-03, A-04, A-06, A-14, A-15, A-16, A-17, A-24 | 8h | Thấp |
| **3** | Quyết định về chế độ sáng | A-02, A-10, A-46 | 6h *hoặc* 0,5h nếu chọn tạm ẩn nút | Trung bình |
| **4** | Trung thực dữ liệu | A-09, A-11, A-12, A-13, A-22, A-25, A-29 | 6h | Thấp |
| **5** | Tương phản & cỡ chữ | A-18, A-19, A-20, A-21, A-23, A-26, A-27 | 8h | Trung bình — chạm nhiều file, cần rà soát thị giác |
| **6** | Khung & responsive | A-08, A-28, A-30, A-31, A-32, A-33, A-44, A-45 | 10h | Trung bình |
| **7** | Gộp trùng lặp | A-34, A-35, A-36, A-37, A-38, A-39, A-40 | 8h | Trung bình — đổi tên class trên diện rộng |
| **8** | Dọn dẹp & đánh bóng | A-41, A-42, A-43, A-47, A-48, A-49, A-50 | 4h | Thấp |

**Tổng: ~54 giờ** (~7 ngày làm việc).

**Về đợt 3.** Nếu chế độ sáng không nằm trong phạm vi bản phát hành này, khuyến nghị tạm ẩn nút toggle (0,5h) thay vì để tính năng ở trạng thái hiện tại. Một tính năng ẩn tốt hơn một tính năng ship ra và hỏng.

**Về đợt 5.** Đây là đợt duy nhất cần rà soát thị giác toàn bộ — thay đổi cỡ chữ đồng loạt sẽ làm dịch chuyển layout ở nhiều nơi. Nên làm sau đợt 6 nếu muốn giảm số lần kiểm tra lại, hoặc gộp hai đợt.

---

## VII. Tiêu chí nghiệm thu

### Chức năng

- [ ] Mở menu thao tác ở **hàng cuối cùng** của bảng người dùng và bảng thiết bị, ở 1366×768 — menu hiển thị đầy đủ, mọi mục bấm được (A-01)
- [ ] Đổi vai trò một người dùng khi drawer đang mở — drawer và hàng bảng hiển thị **cùng một** vai trò mới (A-05)
- [ ] Mở drawer → mở hộp thoại xác nhận — drawer bị làm mờ và **không** bấm được (A-07)
- [ ] Menu thao tác đóng khi bấm ra ngoài và khi nhấn Escape, trên cả 2 màn hình (A-17)
- [ ] Thiết bị `deactivated` **không** còn hiện tùy chọn "Đặt bảo trì" (A-42)

### Truy cập (WCAG 2.1 AA)

- [ ] Ở 1000px, Tab từ topbar đi thẳng vào nội dung — **không** đi qua control nào của sidebar đang đóng (A-03)
- [ ] Ở viewport cao 400px, cuộn được tới nút "Chuyển vai trò" trong sidebar (A-04)
- [ ] Escape đóng drawer và modal ở **cả ba** màn hình admin (A-06)
- [ ] Đóng drawer trả focus về đúng phần tử đã mở nó (A-06)
- [ ] Mọi input và select ở topbar có vòng focus nhìn thấy rõ (A-14)
- [ ] Screen reader đọc hàng bảng người dùng là "row", không phải "button" (A-15)
- [ ] Space trên hàng bảng mở drawer mà **không** cuộn trang (A-16)
- [ ] Tab tới vùng bảng cuộn ngang và dùng phím mũi tên để cuộn (A-24)
- [ ] Mọi target tương tác ≥ 24×24px — kiểm tra bằng axe DevTools (A-23)
- [ ] axe DevTools: **0** lỗi contrast ở chế độ tối (A-18…A-21)
- [ ] axe DevTools: **0** lỗi contrast ở chế độ sáng, hoặc nút toggle đã được gỡ (A-02)

### Trình bày

- [ ] Không còn khai báo `font-size` nào dưới `var(--font-size-2xs)` (11px) trong 5 file CSS admin (A-26)
- [ ] `.admin-card__header h2` ≥ 14px và lớn hơn chữ nội dung trong khối (A-27)
- [ ] Trục X biểu đồ hiển thị giờ đã định dạng, không phải chuỗi ISO (A-09)
- [ ] Trang admin trống **không** có thanh cuộn dọc (A-28)
- [ ] Chuyển giữa "Tổng quan" và "Phê duyệt HITL" — nội dung **không** dịch ngang (A-44)

### Trung thực dữ liệu

- [ ] Trong lúc tải, KPI "Trạng thái kết nối" hiện `—`, **không** hiện "Gián đoạn" (A-11)
- [ ] Không KPI nào hiển thị số `0` khi giá trị thật là "chưa biết" (A-11)
- [ ] Chỉ báo "Trực tuyến" ở topbar phản ánh trạng thái thật, hoặc đã được gỡ (A-12)
- [ ] Ô tìm kiếm và select khu vực ở topbar hoạt động, hoặc đã được gỡ (A-13)
- [ ] Bản đồ tổng quan không đặt marker ở toạ độ bịa; nếu bỏ qua trạm nào thì ghi rõ số lượng (A-22)

### Responsive

- [ ] Ở 1100px, 1152px, 1200px: topbar hiển thị đầy đủ, không phần tử nào bị cắt (A-08)
- [ ] Bảng thiết bị chuyển sang card trước khi bắt đầu cuộn ngang (A-30)
- [ ] Cả 5 file CSS admin dùng chung một bộ breakpoint (A-31)
- [ ] DevTools: mỗi thời điểm chỉ có **một** trong hai — bảng hoặc card — tồn tại trong DOM (A-32)

### Chất lượng mã

- [ ] `grep -c "!important"` trên 5 file CSS admin trả về **0** (A-38)
- [ ] Chỉ còn **một** định nghĩa cho toolbar, cho chip trạng thái, và cho drawer (A-34, A-35, A-36)
- [ ] Màu trạng thái đến từ **một** module duy nhất; marker và chip cùng thang màu (A-39)
- [ ] `IotDevices.css` không còn phụ thuộc class khai báo trong `UserManagement.css`/`RegionStations.css` (A-40)
- [ ] Không còn nhánh code không thể tới trong `executeAction` (A-43)
- [ ] `moduleCopy` chỉ còn entry đang được dùng (A-48)

---

## Phụ lục A — Danh mục lỗi đầy đủ

| Mã | Mức | Nhóm | Mô tả | Tệp |
|---|---|---|---|---|
| A-01 | 🔴 | Vỡ khung | `overflow:hidden` + `overflow-x:auto` cắt menu thao tác | `AdminDashboard.css`, `UserManagement.css` |
| A-02 | 🔴 | Tương phản | Chế độ sáng override 8/60+ màu → 1,25:1 | `AdminShell.css` + 4 file |
| A-03 | 🔴 | Truy cập | Sidebar off-canvas giữ 9 control trong tab order | `AdminShell.css` |
| A-04 | 🔴 | Vỡ khung | Sidebar không `overflow-y`; cắt nút dưới 510px cao | `AdminShell.css` |
| A-05 | 🔴 | Trạng thái | Stale closure ⇒ drawer hiện dữ liệu cũ sau mutation | `UserManagement.tsx` |
| A-06 | 🔴 | Truy cập | `aria-modal` không có Escape/trap/restore | `UserManagement.tsx` |
| A-07 | 🔴 | Lớp phủ | Scrim xác nhận nằm dưới drawer | `UserManagement.css` |
| A-08 | 🟠 | Vỡ khung | Topbar tràn 61px trong dải 1061–1230px | `AdminShell.css` |
| A-09 | 🟠 | Dữ liệu | Trục X hiện timestamp ISO thô; ghép chuỗi theo index | `AdminDashboard.tsx` |
| A-10 | 🟠 | Tương phản | Tooltip Recharts hex cứng `#111d2f` | `AdminDashboard.tsx` |
| A-11 | 🟠 | Dữ liệu | KPI khẳng định "Gián đoạn" và số 0 khi đang tải | `AdminDashboard.tsx` |
| A-12 | 🟠 | Dữ liệu | `.admin-online-pill` tĩnh, luôn báo "Trực tuyến" | `AdminShell.tsx` |
| A-13 | 🟠 | Dữ liệu | Ô tìm kiếm và select topbar không hoạt động | `AdminShell.tsx` |
| A-14 | 🟠 | Truy cập | `outline: 0` không có style thay thế | `AdminShell.css` |
| A-15 | 🟠 | Truy cập | `<tr role="button">` chứa `<td>` và `<button>` | `UserManagement.tsx` |
| A-16 | 🟠 | Truy cập | Space thiếu `preventDefault()` | `UserManagement.tsx` |
| A-17 | 🟠 | Tương tác | Menu không có click-outside / Escape | `UserManagement.tsx`, `IotDevices.tsx` |
| A-18 | 🟠 | Tương phản | Marker bản đồ: trắng trên severity = 2,15–2,54:1 | `AdminDashboard.css` |
| A-19 | 🟠 | Tương phản | `.admin-map-place` 2,78:1 · `.admin-map-label` 2,71:1 | `AdminDashboard.css` |
| A-20 | 🟠 | Tương phản | Tiêu đề cột `#64748b` = 3,28:1 | `UserManagement.css`, `AdminDashboard.css` |
| A-21 | 🟠 | Tương phản | Ô trạng thái trạm: offline 3,17:1 · invalid 4,11:1 | `RegionStations.css` |
| A-22 | 🟠 | Dữ liệu | `MAP_POSITIONS[i % 5]` ⇒ trạm 6 che trạm 1 | `AdminDashboard.tsx` |
| A-23 | 🟠 | Truy cập | 4 target dưới 24px, gồm nút "Thử lại" | 4 file CSS |
| A-24 | 🟠 | Truy cập | 4 vùng cuộn thiếu `tabindex`/`role="region"` | 3 file TSX |
| A-25 | 🟠 | Truy cập | Thông báo lỗi render và đọc hai lần | `UserManagement.tsx` |
| A-26 | 🟠 | Phông chữ | Thang `--font-size-*` dùng 0 lần; sàn 8,48px | 5 file CSS |
| A-27 | 🟠 | Phông chữ | `h2` 12,16px · `h3` 9,92px — đảo thứ bậc | `AdminDashboard.css`, `RegionStations.css` |
| A-28 | 🟠 | Khoảng cách | `calc(100dvh - 110px)` sai ⇒ thanh cuộn ma 15px | 4 file CSS |
| A-29 | 🟠 | Logic | `isSelf` so khớp `full_name` thay vì `user_id` | `UserManagement.tsx` |
| A-30 | 🟠 | Responsive | Bảng 8 cột cuộn ngang suốt dải 900–1350px | `IotDevices.tsx` |
| A-31 | 🟡 | Responsive | 7 breakpoint khác nhau trên 5 file | 5 file CSS |
| A-32 | 🟡 | Hiệu năng | Bảng và card cùng mount ở mọi bề rộng | `UserManagement.tsx`, `IotDevices.tsx` |
| A-33 | 🟡 | Clean code | `.admin-users-desktop/mobile` không có rule base | `UserManagement.css` |
| A-34 | 🟡 | Trùng lặp | 3 khối toolbar giống hệt | 3 file CSS |
| A-35 | 🟡 | Trùng lặp | `.admin-station-status` ≡ `.admin-device-status` | 2 file CSS |
| A-36 | 🟡 | Trùng lặp | `.admin-station-drawer` ≈ `.admin-user-drawer` | 2 file CSS |
| A-37 | 🟡 | Trùng lặp | Hai style timeline audit gần trùng | 2 file CSS |
| A-38 | 🟡 | Clean code | 7 khai báo `!important` | 3 file CSS |
| A-39 | 🟡 | Nhất quán | 4 nguồn màu trạng thái mâu thuẫn | 3 file TSX + 2 CSS |
| A-40 | 🟡 | Kiến trúc | Phụ thuộc chéo file ngầm, không nhìn thấy được | 5 file |
| A-41 | 🟡 | UX | Tab "Sự kiện" và "Nhật ký" cùng dữ liệu | `IotDevices.tsx` |
| A-42 | 🟡 | UX | Thiết bị deactivated vẫn đề nghị "Đặt bảo trì" | `IotDevices.tsx` |
| A-43 | 🟡 | Clean code | Nhánh validate không thể tới | `UserManagement.tsx` |
| A-44 | 🟡 | Khoảng cách | 1480px vs 1440px cho cùng ý đồ | `AdminShell.css`, `AdminDashboard.css` |
| A-45 | 🟡 | Token | Remap 5/9 bậc slate; token `-50` giữ giá trị sáng | `AdminShell.css` |
| A-46 | 🟡 | Chức năng | Chế độ sáng không lưu; thiếu `color-scheme` | `AdminShell.tsx` |
| A-47 | ⚪ | Truy cập | `aria-label` trên `<b>` không có role | `AdminShell.tsx` |
| A-48 | ⚪ | Clean code | 3/4 entry `moduleCopy` là code chết | `AdminModulePlaceholder.tsx` |
| A-49 | ⚪ | Responsive | `2vw` tính theo viewport, không theo container thật | `AdminDashboard.css` |
| A-50 | ⚪ | UX | Bảng nhật ký cảnh báo thiếu skeleton | `AdminDashboard.tsx` |

**Lỗi lặp lại từ `ui_bug_02.md`:**

| Mã admin | Tương ứng resident | Mô tả |
|---|---|---|
| A-03 | `R-03` | Panel off-canvas giữ tab order |
| A-04 | `R-02` | Vùng điều hướng không cuộn được |
| A-11 | `R-13` | Thay số 0 cho dữ liệu chưa có |
| A-12, A-13 | `R-14` | Control giả không có backend |
| A-23 | `R-19` | Target dưới 24px |
| A-24 | `R-21` | Vùng cuộn không truy cập bằng bàn phím |
| A-26 | `R-08` | Không dùng thang `--font-size-*` |

Bảy lỗi được ghi nhận ở báo cáo trước đã lặp lại nguyên vẹn ở shell thứ hai. Đề xuất: đưa các mục tương ứng ở Mục VII vào checklist PR để chặn ở tầng review thay vì phát hiện lại ở tầng QA.

---

## Phụ lục B — Điểm làm tốt

Những điểm dưới đây nên được giữ lại và nhân rộng — một số là thứ mà `ui_bug_02.md` từng phải khuyến nghị.

**Chính trực về dữ liệu.** `RegionStations.tsx:482-487` từ chối vẽ marker khi thiếu toạ độ thật, kèm ghi chú giải thích lý do. `IotDevices.tsx` chỉ phản ánh `outcome` backend trả về, có comment `// Chỉ phản ánh outcome backend trả về; không tự coi là succeeded.` Đây đúng là chuẩn mực mà báo cáo trước đề ra.

**Display mapper có precedence rõ ràng.** Cả `getDisplayState` và `getConnectivity` đều có docstring nêu rõ thứ tự ưu tiên (`invalid > offline > stale > severity`) và khẳng định trạng thái luôn đến từ backend, client không suy diễn từ timer. Logic được dùng chung cho marker, list và drawer nên ba nơi không thể lệch nhau.

**Xử lý severity đầy đủ.** `severityText: Record<Alert["severity"], string>` khai báo đủ 4 khoá của union, và CSS có đủ 4 biến thể `.admin-severity--*`. Đây chính là lỗi `R-01` (thiếu `.level-critical`) ở báo cáo trước — lần này đã tránh được, và cách dùng `Record<Union, T>` khiến TypeScript sẽ báo lỗi nếu union được mở rộng mà quên cập nhật.

**Skeleton có tôn trọng `prefers-reduced-motion`.** `RegionStations.css:218-222` tắt animation shimmer cho người dùng nhạy cảm với chuyển động — một chi tiết thường bị bỏ sót.

**Scrim dùng đúng kỹ thuật ẩn.** `.admin-shell__scrim` dùng `visibility: hidden; opacity: 0` để gỡ hẳn khỏi tab order. Kỹ thuật đúng đã có sẵn trong file — chỉ cần áp dụng thêm cho sidebar (A-03).

**Nút chuyển theme tự nhất quán.** Cặp `Sun`/`Moon` theo quy ước "hiện hành động, không hiện trạng thái", và `aria-label` khớp với icon ở cả hai trạng thái. Vấn đề nằm ở phần CSS chưa hoàn thiện, không ở phần điều khiển.

**Token muted được chọn đúng.** `--admin-muted: #8290a7` đạt 5,24:1 trên nền `#111d2f` và `#64748b` đạt 4,76:1 trên nền trắng — cả hai chế độ đều vượt ngưỡng AA. Toàn bộ lỗi tương phản trong báo cáo này đến từ hex cứng nằm *ngoài* hệ token.

**Bảng chuyển sang card trên mobile.** Cả ba màn hình bảng đều có bố cục card riêng cho màn hình nhỏ thay vì để bảng cuộn ngang — đúng hướng. Vấn đề chỉ là ngưỡng chuyển (A-30) và việc render cả hai cùng lúc (A-32).

**`IotDevices.tsx:462` xử lý phím Space đúng chuẩn.** Có `event.preventDefault()`. Đây là bản tham chiếu đúng để `UserManagement` sửa theo (A-16) — lời giải đã tồn tại trong codebase.

**Ghi chú `[SIMULATOR]` và `partial-note`.** Giao diện nói rõ khi dữ liệu đến từ mô phỏng hoặc khi kết quả chỉ là một phần, thay vì trình bày như dữ liệu đầy đủ.

---

*Hết báo cáo — ui_bug_03.md*

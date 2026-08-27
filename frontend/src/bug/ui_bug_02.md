# UI/UX Code Review — Giao diện Cư dân (Resident)

> **Dự án:** AirGuard AI — PM2.5 Monitoring
> **Phạm vi review:** Toàn bộ luồng cư dân (role `resident`) — `AppShell`, `Dashboard`, `StationDetail`, `CompareStations`, `AlertList`, `AgentChat`, `Profile` và các component dùng chung.
> **Ngày review:** 2026-08-06
> **Reviewer:** Senior Frontend / UI-UX Code Review
> **Báo cáo liên quan:** [`ui_bug_01.md`](./ui_bug_01.md) (màn Login/Register — không lặp lại ở đây)

---

## 0. Tóm tắt điều hành

Kiến trúc tổng thể tốt: tách `AppShell` / `AdminShell` rõ ràng, dùng CSS Variables đồng bộ, component `Button` / `PageHeader` / `StatusBadge` được trừu tượng hợp lý, có `prefers-reduced-motion`, có `sr-only`, và phần lớn icon đã gắn `aria-hidden`.

Tuy nhiên có **33 lỗi** được xác nhận bằng đọc code + tính toán, trong đó:

| Mức | Số lượng | Ảnh hưởng |
|---|---|---|
| 🔴 **P0 — Critical** | 4 | Chức năng hỏng / nội dung không truy cập được |
| 🟠 **P1 — High** | 9 | Vi phạm WCAG AA, sai lệch thị giác thấy rõ |
| 🟡 **P2 — Medium** | 11 | Trải nghiệm kém, rủi ro vỡ khung ở dải màn hình hẹp |
| ⚪ **P3 — Clean Code** | 9 | ~200 dòng CSS chết, quy tắc trùng lặp, inline style thừa |

**Ba lỗi nghiêm trọng nhất cần sửa ngay:**

1. **`.level-critical` không tồn tại** → cảnh báo mức *Nghiêm trọng* hiển thị **nhạt hơn** cảnh báo mức *Trung bình*.
2. **Sidebar bị cắt cụt trên màn hình thấp** → nút **Đăng xuất** không thể bấm được.
3. **`StationDetail` nuốt lỗi API** → skeleton loading quay mãi mãi, không báo lỗi, không có nút thử lại.

---

## I. Lỗi UI/UX

### I.1 — Tương phản màu sắc (Color Contrast — WCAG 2.1 AA)

#### 🔴 R-05 · Chữ người dùng gõ vào ô tìm kiếm Dashboard gần như vô hình

**File:** [`styles.css:1636-1663`](../styles.css#L1636-L1663)

`.dashboard-search` (wrapper) đặt `color: var(--color-text-subtle)` để tô màu icon. Nhưng `.dashboard-search input` **không khai báo lại `color`** — mà thẻ `<input>` **kế thừa `color` từ cha** trên mọi trình duyệt. Hệ quả: chữ người dùng vừa gõ ra màu `#94a3b8` ở cỡ `0.74rem` (11.8px).

```
Tỷ lệ tương phản: #94a3b8 trên #f8fafc = 2.45:1   (yêu cầu WCAG AA: 4.5:1)
```

**Bằng chứng đây là lỗi sót, không phải chủ đích:** cùng một pattern ở `AppShell.css`, tác giả **đã** xử lý đúng:

```css
/* AppShell.css:272-280 — ĐÚNG */
.topbar-search input {
  color: var(--color-text);   /* ← có dòng này */
  background: transparent;
}

/* styles.css:1655-1663 — THIẾU */
.dashboard-search input {
  background: transparent;    /* ← thiếu color, kế thừa #94a3b8 */
  font-size: 0.74rem;
}
```

---

#### 🟠 R-10 · Token `--color-text-subtle` không đạt chuẩn cho text

**File:** [`theme.css:45`](../theme.css#L45)

`--color-text-subtle: var(--color-slate-400)` = `#94a3b8`.

| Nền | Tỷ lệ | Kết quả |
|---|---|---|
| `#ffffff` | **2.56:1** | ❌ Fail AA (4.5:1) — fail cả AA Large (3:1) |
| `#f8fafc` (slate-50) | **2.45:1** | ❌ Fail |

Token này đang được dùng cho **text thật**, không phải trang trí, ở 8 vị trí trong luồng cư dân:

| Selector | File:Line | Cỡ chữ | Nội dung bị ảnh hưởng |
|---|---|---|---|
| `.dashboard-kpi__copy small` | `styles.css:1271` | 10.9px | "5 trạm có dữ liệu hợp lệ" |
| `.dashboard-alert-item__copy time` | `styles.css:1612` | **9.6px** | Thời gian cảnh báo |
| `.message-time`, `.tools-label` | `styles.css:606` | 10.4px | Giờ gửi tin nhắn AI |
| `.chat-history-panel__title` | `styles.css:1876` | 10.4px | "GẦN ĐÂY" |
| `.chat-history-empty` | `styles.css:1882` | 10.4px | Ghi chú lịch sử hội thoại |
| `.prop-time` | `styles.css:773` | 10.6px | Thời gian đề xuất |
| `.app-footer` | `AppShell.css:425` | 10.9px | Copyright + disclaimer |
| `.dashboard-search` | `styles.css:1645` | 11.8px | ← xem R-05 |

**Đối chiếu — các token khác vẫn đạt chuẩn** (đã tính toán, không cần sửa):

| Màu | Nền | Tỷ lệ | Kết quả |
|---|---|---|---|
| `--color-text-muted` `#64748b` | `#ffffff` | 4.76:1 | ✅ Pass |
| `--color-text-muted` `#64748b` | `#f8fafc` | 4.55:1 | ⚠️ Vừa đủ |
| `.dashboard-alert-item__meta b` `#c2410c` | `#ffffff` | 5.18:1 | ✅ Pass |
| `.dashboard-eyebrow` `#4f46e5` | `#ffffff` | 6.29:1 | ✅ Pass |

---

#### 🟠 R-06 · Biến CSS `--color-primary-300` không tồn tại → focus ring hỏng

**File:** [`styles.css:1651`](../styles.css#L1651)

```css
.dashboard-search:focus-within {
  border-color: var(--color-primary-300);   /* ← chưa định nghĩa ở đâu cả */
  box-shadow: 0 0 0 3px var(--color-primary-100);
}
```

`theme.css` chỉ định nghĩa `--color-primary-` các bậc **50, 100, 200, 500, 600, 700**. Không có bậc **300**.

Theo spec CSS, `var()` không tìm thấy và **không có fallback** → khai báo trở thành *invalid at computed-value time* → `border-color` rơi về `initial` = `currentColor`. Mà `.dashboard-search` có `color: var(--color-text-subtle)` → **viền focus chuyển sang xám `#94a3b8` thay vì xanh indigo**, gần như không phân biệt được với trạng thái nghỉ.

> **Ghi chú:** file `features/auth/auth.css:386` dùng **cùng biến này nhưng có fallback** — `var(--color-primary-300, #a5b4fc)` — nên màn Login không dính lỗi. Đây đúng là chỗ sót duy nhất.

---

### I.2 — Thứ bậc phông chữ (Font Hierarchy)

#### 🟠 R-09 · Micro-typography: 12 quy tắc dưới ngưỡng 11px

Ngưỡng tối thiểu cho body/meta text theo Material Design 3 và Apple HIG là **12px (0.75rem)**. Dashboard cư dân đang chạy phần lớn ở **9–11px**:

| Selector | File:Line | Giá trị | px | Nội dung |
|---|---|---|---|---|
| `.dashboard-station-row__value small` | `styles.css:1720` | `0.56rem` | **8.96px** | Đơn vị `µg/m³` |
| `.dashboard-selected-station__reading .badge` | `styles.css:1483` | `0.59rem` | **9.44px** | Badge chất lượng dữ liệu |
| `.dashboard-alert-item__copy time` | `styles.css:1614` | `0.6rem` | **9.6px** | Thời gian cảnh báo |
| `.dashboard-alert-item__meta b` | `styles.css:1625` | `0.6rem` | **9.6px** | Mức độ nghiêm trọng |
| `.dashboard-health-grid small` | `styles.css:1534` | `0.62rem` | 9.92px | Online / Offline / Cũ |
| `.chat-history-item small` | `styles.css:1881` | `0.63rem` | 10.08px | Số tin nhắn |
| `.dashboard-eyebrow` | `styles.css:1332` | `0.64rem` | 10.24px | Nhãn nhóm |
| `.dashboard-selected-station__reading strong em` | `styles.css:1474` | `0.64rem` | 10.24px | Đơn vị `µg/m³` |
| `.message-time`, `.tools-label` | `styles.css:609` | `0.65rem` | 10.4px | Giờ tin nhắn |
| `.dashboard-alert-item__copy small` | `styles.css:1606` | `0.66rem` | 10.56px | ⚠️ **Nội dung cảnh báo** |
| `.dashboard-station-row__identity span` | `styles.css:1713` | `0.66rem` | 10.56px | ⚠️ **Tên trạm** |
| `.data-table th` | `styles.css:806` | `0.67rem` | 10.72px | Tiêu đề cột bảng |

Hai dòng gắn ⚠️ là **nội dung chính**, không phải metadata — nội dung cảnh báo và tên trạm là thứ người dùng đến để đọc.

**Vấn đề gốc là clean code:** `theme.css` đã định nghĩa sẵn thang `--font-size-xs` → `--font-size-3xl`, nhưng **hầu như không được dùng**. Toàn bộ Dashboard hard-code giá trị `rem` thập phân tuỳ tiện, tạo ra 12 bậc cỡ chữ khác nhau trong khoảng 9–11px — không có hệ thống nào cả.

---

#### 🟠 R-11 · Thứ bậc bị đảo ngược — số trang trí to hơn tiêu đề trang

| Phần tử | Thẻ | Cỡ tối đa | Ghi chú |
|---|---|---|---|
| `.metric-value` (StationDetail) | `div` | **42.4px** | `clamp(1.75rem, 4vw, 2.65rem)` |
| `.dashboard-kpi__copy strong` | `strong` | **29.6px** | `clamp(1.45rem, 2vw, 1.85rem)` |
| `.page-header h1` | **`h1`** | **24px** | `clamp(1.25rem, 2.2vw, 1.5rem)` |
| `.dashboard-panel-header h2` | **`h2`** | **15.7px** | `0.98rem` |
| Body text | — | 14px | `--font-size-sm` |

Hai bất thường:

1. `<h1>` (24px) **nhỏ hơn** một `<strong>` trang trí trong thẻ KPI (29.6px) và nhỏ hơn `.metric-value` (42.4px) tới 43%.
2. `<h2>` (15.7px) chỉ hơn body text 1.7px → **không đọc ra được đó là tiêu đề mục**. Thang chuẩn cần tối thiểu bước nhảy 1.2× giữa các cấp.

---

#### 🟡 R-17 · Nhảy cấp heading (h1 → h3)

| File | Vấn đề |
|---|---|
| [`StationDetail.tsx:117`](../features/stations/StationDetail.tsx#L117) | `PageHeader` render `<h1>`, kế tiếp là `<h3>` "Dự báo PM2.5 ngắn hạn" — **không có `<h2>`** |
| [`StationDetail.tsx:134`](../features/stations/StationDetail.tsx#L134) | `<h3>` "Lịch sử PM2.5 theo thời gian" — cùng vấn đề |
| [`CompareStations.tsx:120,137`](../features/stations/CompareStations.tsx#L120) | `<h3>` tên trạm, không có `<h2>` cha |
| [`CompareStations.tsx:154`](../features/stations/CompareStations.tsx#L154) | `<h4>` "Kết quả so sánh" — **thấp hơn** `<h3>` dù là mục ngang hàng |

Vi phạm WCAG 2.4.10 (Section Headings). Người dùng screen reader duyệt theo cấu trúc heading sẽ thấy trang khuyết tầng.

---

### I.3 — Khoảng cách (Spacing) & Magic Numbers

#### 🟡 R-18 · `padding-left: 59px` — magic number không sống sót trên mobile

**File:** [`styles.css:1457`](../styles.css#L1457) và [`styles.css:1783`](../styles.css#L1783)

```css
.dashboard-selected-station__reading { padding-left: 59px; }   /* 46px chip + 13px gap */

@media (max-width: 640px) {
  .dashboard-selected-station__reading { grid-column: auto; padding-left: 59px; }  /* ← giữ nguyên! */
}
```

59px là tổng thủ công của `.dashboard-station-code` (46px) + gap (13px) để canh dòng PM2.5 thẳng hàng với tên trạm. Ở breakpoint 640px, grid đã đổi sang 1 cột nhưng padding vẫn giữ 59px.

**Tính toán trên iPhone SE (375px) và màn 320px:**

```
Chiều rộng khả dụng = viewport − page-content padding − card padding − padding-left
375px:  375 − 32 − 40 − 59 = 244px
320px:  320 − 32 − 40 − 59 = 189px   ← còn 189px
```

Trong 189px đó phải chứa: nhãn "PM2.5 hiện tại" + giá trị + đơn vị `µg/m³` + badge chất lượng dữ liệu (`flex-wrap: wrap`) → xuống 3 dòng, trong khi 59px bên trái hoàn toàn bỏ trống.

---

#### 🟡 R-19 / R-20 · Vùng chạm dưới ngưỡng tối thiểu

WCAG 2.5.8 (AA) yêu cầu **24×24px**, WCAG 2.5.5 (AAA) và Material/HIG khuyến nghị **44×44px**.

| Phần tử | File:Line | Kích thước tính được | Vai trò |
|---|---|---|---|
| `.btn-link` (tên trạm trong bảng) | `styles.css:1056-1062` | **~18px cao** (`min-height: auto; padding: 0`) | Điều hướng chính của bảng cảnh báo |
| `.preset-btn` (chọn 1h/6h/24h/72h) | `styles.css:460-468` | **~28px cao** (`padding: 7px 11px`, font 11.5px) | Điều khiển chính của biểu đồ |
| `.pill-btn` (câu hỏi gợi ý AI) | `styles.css:460-468` | **~28px cao** | Lối vào chính của AI Agent |

`.btn-link` đặc biệt tệ: nó kế thừa `padding: 9px 14px` từ selector nhóm `.button, .btn-link` rồi **tự ghi đè về `0`** ở dòng ngay dưới.

---

### I.4 — Nguy cơ vỡ khung & lỗi hiển thị

#### 🔴 R-01 · `.level-critical` không tồn tại → cảnh báo nghiêm trọng trông nhẹ nhất

**File:** [`AlertList.tsx:124`](../features/alerts/AlertList.tsx#L124), [`styles.css:285-315`](../styles.css#L285-L315)

```tsx
<span className={`badge level-${alert.severity}`}>{alert.severity.toUpperCase()}</span>
```

`Alert["severity"]` được khai báo ở [`types/index.ts:229`](../types/index.ts#L229) là:

```ts
severity: "warning" | "moderate" | "critical" | "good";
```

CSS định nghĩa: `.level-good`, `.level-moderate`, `.level-warning`, `.level-unhealthy`, `.level-hazardous`.

**→ Không có `.level-critical`.** (Đã grep toàn bộ `frontend/src`: 0 kết quả.)

Hệ quả cho alert mức `critical`:

- Không có `background` → nền trắng
- Không có `color` → kế thừa `--color-slate-700` từ `.data-table`
- `.badge { border: 1px solid currentColor }` → viền xám

**Cảnh báo nghiêm trọng nhất render thành pill xám trơn — nhạt hơn cả badge vàng của mức "moderate".** Đây là lỗi đảo ngược tín hiệu an toàn trong một ứng dụng cảnh báo môi trường.

Ngược lại, `.level-unhealthy` và `.level-hazardous` được định nghĩa trong CSS nhưng **không bao giờ khớp** với giá trị severity nào — chúng thuộc thang của `getPm25Severity()`, tức là hai hệ phân loại khác nhau bị trộn vào chung một namespace class.

**Lỗi phụ:** hiển thị `severity.toUpperCase()` = `"CRITICAL"` / `"MODERATE"` (tiếng Anh, chữ hoa) trong UI tiếng Việt — trong khi [`Dashboard.tsx:41-46`](../features/stations/Dashboard.tsx#L41-L46) **đã có sẵn** map `severityLabel` dịch đúng nhưng không được tái sử dụng.

---

#### 🟠 R-08 · `DataQualityBadge` — viền lệch hình lưỡi liềm

**File:** [`DataQualityBadge.tsx:43`](../components/common/DataQualityBadge.tsx#L43)

```tsx
<span className={`badge ${severity.class}`} style={{ borderLeft: `4px solid ${severity.color}` }}>
```

Xung đột với [`styles.css:272-283`](../styles.css#L272-L283):

```css
.badge {
  border: 1px solid currentColor;
  border-radius: var(--radius-full);   /* 9999px — hình viên thuốc */
}
```

Inline style chỉ đè cạnh trái → badge có **3 cạnh 1px + cạnh trái 4px** trên nền bo tròn hoàn toàn. Kết quả: viền dày biến dạng thành **lưỡi liềm lệch**, và text bị đẩy lệch 3px sang phải so với trục đối xứng.

**Lỗi phụ — hai nguồn sự thật về màu:** `severity.color` (`#10b981` = success-**500**) khác với `.level-good { color: var(--color-success-600) }` (`#059669`). Cùng một badge có viền trái xanh nhạt và viền phải/text xanh đậm.

---

#### 🟡 R-15 · `font-size: 0` xoá nhãn trạng thái, chỉ còn icon không giải thích

**File:** [`styles.css:1629-1634`](../styles.css#L1629-L1634)

```css
.dashboard-alert-item__meta .status-badge { padding: 3px 5px; font-size: 0; }
.dashboard-alert-item__meta .status-badge svg { width: 13px; height: 13px; }
```

`StatusBadge` render `<Icon aria-hidden="true" /> + "Đang kích hoạt"`. Với `font-size: 0`, người dùng sáng mắt chỉ thấy **một icon 13px trần**, không nhãn, không `title`, không tooltip. Icon lại `aria-hidden` nên bản thân nó không mang ngữ nghĩa nào.

Ngoài ra `.status-badge { gap: 5px }` vẫn giữ nguyên → pill có 5px khoảng trống ma sau icon.

---

#### 🟡 R-24 · Badge "VS" mồ côi khi `.compare-selectors` wrap

**File:** [`styles.css:483-517`](../styles.css#L483-L517), [`styles.css:1762-1763`](../styles.css#L1762-L1763)

```css
.compare-selectors { display: flex; align-items: flex-end; gap: var(--space-5); }
.select-box { flex: 1 1 220px; }
.vs-badge { flex: 0 0 auto; width: 42px; height: 42px; }
```

Chiều rộng tối thiểu để giữ 1 hàng: `220 + 42 + 220 + (20 × 2 gap) = 522px` cộng padding card 40px = **562px**.

Dưới 562px (iPhone SE 375px, iPhone 14 390px, Pixel 430px — tức **toàn bộ điện thoại**), flex wrap khiến bố cục thành:

```
[ Trạm A (dropdown) ]  ( VS )
[ Trạm B (dropdown) ]
```

Badge "VS" — vốn là ký hiệu ngăn cách giữa hai vế — bị đẩy thành phần tử **đứng cạnh Trạm A**, mất hoàn toàn ý nghĩa thị giác.

---

#### 🟡 R-13 · Empty state hiển thị thông tin sai trong lúc đang tải

**File:** [`Dashboard.tsx:287-288`](../features/stations/Dashboard.tsx#L287-L288)

```tsx
{activeAlerts.length === 0 ? (
  <div className="dashboard-empty-state"><Bell size={20} /><span>Không có cảnh báo đang kích hoạt.</span></div>
) : ...}
```

Điều kiện chỉ kiểm tra `length === 0`, **không kiểm tra `loading`**. Trong toàn bộ thời gian fetch, `alerts` là `[]` → giao diện khẳng định dứt khoát **"Không có cảnh báo đang kích hoạt"** — một tuyên bố sai về an toàn không khí — rồi mới nhảy sang danh sách cảnh báo đỏ khi API trả về.

Panel "Các trạm" ([`Dashboard.tsx:328-351`](../features/stations/Dashboard.tsx#L328-L351)) có kiểm tra `!loading` cho empty state, nhưng **không có skeleton** trong lúc tải → panel rỗng trắng. Ba panel trên cùng một màn hình dùng ba chiến lược loading khác nhau (skeleton / empty-state sai / rỗng trắng).

---

#### 🔴 R-04 · `StationDetail` nuốt lỗi API → skeleton quay vĩnh viễn

**File:** [`StationDetail.tsx:31-35, 51-59`](../features/stations/StationDetail.tsx#L31-L59)

```tsx
} catch (err) {
  console.error("Error fetching station detail:", err);   // ← chỉ log console
} finally {
  setLoading(false);
}

if (loading || !station) {
  return (<div className="detail-container">
    <PageHeader title="Chi tiết trạm" description="Đang tải dữ liệu..." />
    <div className="skeleton-card" style={{ height: 200 }}></div>
    <div className="skeleton-card" style={{ height: 350 }}></div>
  </div>);
}
```

Khi API lỗi: `loading = false` nhưng `station` vẫn `null` → điều kiện `!station` đúng → **skeleton hiển thị vĩnh viễn** với dòng chữ "Đang tải dữ liệu" trong khi thực tế đã dừng tải.

Không có thông báo lỗi, không có nút thử lại, không có đường thoát. Người dùng chỉ thấy hai khối xám nhấp nháy mãi.

**Đây là lỗi lệch chuẩn nội bộ:** `Dashboard.tsx` và `AlertList.tsx` đều đã có state `error` + `.alert-box` + nút "Thử lại" đúng chuẩn. `CompareStations.tsx` có state `error` nhưng cũng dính lỗi tương tự (dòng 45-56: `error` chỉ render trong nhánh loading, và nếu `stationA`/`stationB` null thì skeleton cũng quay mãi).

---

## II. Kiểm tra Responsive

**Kết luận ngắn: có, đoạn code này dễ lỗi trên màn hình nhỏ.** Ba lỗi P0/P1 và bốn lỗi P2 chỉ xuất hiện ở mobile/màn thấp.

### Ma trận breakpoint

| Viewport | `AppShell.css` | `styles.css` | Trạng thái |
|---|---|---|---|
| > 1200px | — | — | ✅ OK |
| 1180px | `.topbar-search` thu 230px, ẩn `kbd` + tên user | — | ✅ OK |
| 1200px | — | KPI 4→2 cột, workspace 2→1 cột, rail 2 cột | ✅ OK |
| 1100px | — | `.profile-layout` → 1 cột | ✅ OK |
| 900px | Sidebar → off-canvas drawer, ẩn search | Compare/Proposals → 1 cột, ẩn `.chat-history-panel` | ⚠️ R-03 |
| 640px | Ẩn breadcrumb + role badge, padding 16px | KPI 2 cột, map 370px, header stack dọc | ⚠️ R-18, R-22 |
| < 562px | — | — | ❌ R-24 (VS mồ côi) |
| Chiều cao < ~600px | — | — | ❌ R-02 (mất nút Đăng xuất) |

---

### 🔴 R-02 · Sidebar bị cắt cụt — nút Đăng xuất không bấm được

**File:** [`AppShell.css:1-19`](../components/layout/AppShell.css#L1-L19)

```css
.app-shell   { height: 100dvh; overflow: hidden; }   /* ← khoá mọi scroll */
.app-sidebar { height: 100dvh; display: flex; flex-direction: column; }
             /* ← KHÔNG có overflow-y */
```

**Tính chiều cao nội dung sidebar:**

```
.app-sidebar__brand          min-height: var(--topbar-height)  =  72px
.app-sidebar__section-label  padding 25px + 9px + text 10px    =  44px
.app-sidebar__nav            7 item × 44px + 6 gap × 4px       = 332px
.app-sidebar__footer         padding 32px + system-card 52px
                             + gap 12px + logout 40px          = 136px
─────────────────────────────────────────────────────────────────────
TỔNG                                                            584px
```

`.app-shell` khoá `overflow: hidden` và sidebar không có `overflow-y: auto` → mọi nội dung vượt quá `100dvh` bị **cắt và không thể cuộn tới**.

**Các thiết bị bị ảnh hưởng:**

| Thiết bị / tình huống | Chiều cao khả dụng | Bị cắt |
|---|---|---|
| iPhone 14 xoay ngang | 390px | Mất `.app-sidebar__footer` + 2 nav item cuối |
| iPad xoay ngang + thanh URL | ~660px | Vừa đủ |
| Laptop 1366×768 + taskbar + browser chrome | ~590px | ⚠️ Sát ngưỡng |
| Cửa sổ trình duyệt thu nhỏ nửa màn | < 584px | Mất nút **Đăng xuất** |

Với `role: manager` (hiện thêm 2 mục "Phê duyệt" + "Audit Log" = +88px → tổng 672px), ngưỡng vỡ nâng lên **672px** — tức **hầu hết laptop 768px đều dính** sau khi trừ browser chrome.

---

### 🔴 R-03 · Sidebar off-canvas vẫn nhận focus bàn phím

**File:** [`AppShell.css:454-463`](../components/layout/AppShell.css#L454-L463), [`AppShell.tsx:134`](../components/layout/AppShell.tsx#L134)

```css
@media (max-width: 900px) {
  .app-sidebar {
    position: fixed;
    transform: translateX(-102%);   /* ← chỉ đẩy ra ngoài màn hình */
  }
  .app-sidebar.is-open { transform: translateX(0); }
}
```

`transform` **không** loại phần tử khỏi accessibility tree hay tab order. Trên mobile, khi drawer **đóng**, người dùng bàn phím nhấn Tab từ topbar sẽ rơi vào 10 control vô hình: brand button → close button → 7 nav item → logout — focus biến mất khỏi màn hình mà không có dấu hiệu nào.

**Thiếu kèm theo:**
- Không có focus trap khi drawer mở
- Không trả focus về nút hamburger khi drawer đóng (dù đã bắt phím Escape ở dòng 109-115)
- `.app-sidebar` thiếu `aria-hidden` / `inert` theo state

> **Ghi nhận điểm tốt:** `.app-shell__scrim` xử lý **đúng** — dùng `visibility: hidden` (dòng 475) nên tự động rời khỏi tab order. Chỉ cần áp dụng cùng kỹ thuật cho sidebar.

---

### 🟠 R-07 · Bản đồ Leaflet bẫy thao tác cuộn trang

**File:** [`Dashboard.tsx:198`](../features/stations/Dashboard.tsx#L198)

```tsx
<MapContainer center={[20.9446, 105.9447]} zoom={16} scrollWheelZoom className="dashboard-map">
```

`scrollWheelZoom` viết trần = `true`. Bản đồ cao **490px** (`styles.css:1373`) nằm giữa một trang cuộn dọc.

- **Desktop:** lăn chuột qua bản đồ → trang ngừng cuộn, bản đồ zoom ra/vào. Người dùng bị "kẹt" giữa trang.
- **Mobile (≤640px):** bản đồ 370px trên màn 667px = **55% chiều cao viewport**. Vuốt để cuộn trang gần như chắc chắn bắt đầu từ trong bản đồ → pan bản đồ thay vì cuộn trang.

Đây là anti-pattern đã được ghi nhận từ lâu (Google Maps Embed từ 2015 đã mặc định tắt scroll-zoom cho đến khi người dùng click vào bản đồ).

---

### 🟡 R-21 · Bảng 8 cột không có phương án thay thế trên mobile

**File:** [`AlertList.tsx:100-138`](../features/alerts/AlertList.tsx#L100-L138), [`styles.css:778-792`](../styles.css#L778-L792)

```css
.table-wrapper { overflow-x: auto; }
.data-table    { min-width: 760px; }
```

Bảng có 8 cột: Mã cảnh báo · Trạm · Mức độ · Nội dung · Thực đo/Ngưỡng · Thời gian · Trạng thái · Hành động.

Trên iPhone SE (375px, trừ padding còn ~343px), người dùng phải cuộn ngang **qua 417px** để đọc hết một dòng — mất hoàn toàn ngữ cảnh cột đầu. Cột "Nội dung" (`alert.message`) nhận trung bình 95px → xuống 4-5 dòng.

**Lỗi accessibility kèm theo:** vùng cuộn ngang thiếu `tabindex="0"` + `role="region"` + `aria-label` → người dùng bàn phím **không thể cuộn ngang** để xem các cột bị ẩn (WCAG 2.1.1).

---

### 🟡 R-22 · Ẩn ngữ cảnh thay vì reflow ở 640px

**File:** [`styles.css:1777`](../styles.css#L1777)

```css
@media (max-width: 640px) { .dashboard-kpi__copy small { display: none; } }
```

Bị ẩn trên mobile:

| KPI | Dòng bị mất |
|---|---|
| Trạm quan trắc | "Danh mục S01–S05" |
| PM2.5 trung bình | **"{n} trạm có dữ liệu hợp lệ"** ← rất quan trọng |
| Kết nối hệ thống | "Online và dữ liệu còn mới" |
| Cảnh báo đang mở | "Cần theo dõi và xử lý" |

Dòng thứ hai là **điều kiện diễn giải** của con số PM2.5 trung bình. Ẩn nó đi khiến người dùng mobile thấy một con số trung bình mà không biết nó được tính trên bao nhiêu trạm hợp lệ — chính xác là loại thông tin mà [`SimulatorBanner`](../components/common/SimulatorBanner.tsx) đang cố nhấn mạnh.

---

### 🟡 R-14 · Ô tìm kiếm topbar là control giả

**File:** [`AppShell.tsx:216-221`](../components/layout/AppShell.tsx#L216-L221)

```tsx
<label className="topbar-search">
  <Search size={18} aria-hidden="true" />
  <span className="sr-only">Tìm kiếm</span>
  <input type="search" placeholder="Tìm trạm, cảnh báo..." />
  <kbd>⌘ K</kbd>
</label>
```

Ba vấn đề:

1. `<input>` **không có** `value`, `onChange`, `onSubmit` hay bất kỳ handler nào — gõ vào không có gì xảy ra.
2. `<kbd>⌘ K</kbd>` quảng cáo một phím tắt **không tồn tại** (không có `keydown` listener nào cho `Cmd/Ctrl+K` trong toàn bộ codebase — chỉ có listener cho `Escape` ở dòng 109-115).
3. Ký hiệu `⌘` là phím Command của macOS. Dự án chạy trên Windows; người dùng Windows cần thấy `Ctrl K`.

Một affordance hứa hẹn chức năng nhưng không thực hiện gây mất niềm tin nhiều hơn là không có nó.

---

### 🟡 R-23 · Múi giờ không nhất quán giữa các màn hình

| File | Cách format | Múi giờ thực tế |
|---|---|---|
| [`Dashboard.tsx:32-38`](../features/stations/Dashboard.tsx#L32-L38) | `Intl.DateTimeFormat("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })` | ✅ Luôn giờ VN |
| [`StationDetail.tsx:108`](../features/stations/StationDetail.tsx#L108) | `new Date(...).toLocaleString("vi-VN")` | ❌ Giờ máy người dùng |
| [`AlertList.tsx:127`](../features/alerts/AlertList.tsx#L127) | `new Date(...).toLocaleString("vi-VN")` | ❌ Giờ máy |
| [`CompareStations.tsx:130,147`](../features/stations/CompareStations.tsx#L130) | `new Date(...).toLocaleTimeString("vi-VN")` | ❌ Giờ máy |

`toLocaleString("vi-VN")` chỉ đặt **locale** (định dạng dd/mm/yyyy), **không** đặt timezone. Người dùng ở múi giờ khác — hoặc chỉ cần đặt sai timezone máy — sẽ thấy **cùng một mốc thời gian hiển thị khác nhau** giữa Dashboard và StationDetail. Trong khi đó `StationDetail.tsx:109` lại hiển thị dòng chữ tĩnh "Múi giờ: Asia/Ho_Chi_Minh" ngay bên dưới — một lời khẳng định sai.

---

### 🟡 R-12 · Nút chọn khoảng thời gian không phân biệt được trạng thái active

**File:** [`StationDetail.tsx:136-144`](../features/stations/StationDetail.tsx#L136-L144), [`styles.css:470-476`](../styles.css#L470-L476)

```css
.preset-btn:hover,
.pill-btn:hover,
.preset-btn.active {          /* ← active và hover DÙNG CHUNG khai báo */
  border-color: var(--color-primary-200);
  color: var(--color-primary-700);
  background: var(--color-primary-50);
}
```

Nút "24h" đang được chọn trông **giống hệt** nút "72h" đang được hover. Trên desktop, người dùng di chuột qua dãy nút sẽ thấy hai nút cùng sáng và không biết cái nào là lựa chọn thật.

Kèm theo ở JSX:
- Thiếu `aria-pressed` → screen reader không biết nút nào đang chọn
- Thiếu `type="button"` (cũng thiếu ở [`AlertList.tsx:119`](../features/alerts/AlertList.tsx#L119))

---

### 🟡 R-16 · `<label>` không liên kết với `<select>` trong CompareStations

**File:** [`CompareStations.tsx:83-84, 100-101`](../features/stations/CompareStations.tsx#L83-L84)

```tsx
<label>Trạm A:</label>
<select value={compareStationIds[0]} onChange={...} className="role-select">
```

`<label>` không có `htmlFor`, `<select>` không có `id`, và label **không bọc** select. → Không có liên kết nào. Screen reader đọc dropdown là "combo box" trống. Click vào chữ "Trạm A:" cũng không focus vào dropdown.

**Lệch chuẩn nội bộ:** [`AlertFilters.tsx:29-31, 42-43`](../components/common/AlertFilters.tsx#L29-L31) trong cùng codebase làm **đúng** với `htmlFor` + `id` khớp nhau.

---

## III. Đánh giá Clean Code

### ⚪ R-25 · ~200 dòng CSS chết (không class nào được render)

Đã grep toàn bộ `frontend/src/**/*.tsx` — **0 kết quả** cho các class sau:

| Nhóm | Selector | Vị trí | Số dòng |
|---|---|---|---|
| Dashboard cũ (v1) | `.stats-grid`, `.stat-card`, `.stat-icon`, `.stat-value`, `.stat-label` | `styles.css:65-145` | ~60 |
| Layout bản đồ cũ | `.map-layout`, `.map-wrapper`, `.map`, `.station-sidebar`, `.sidebar-header` | `styles.css:147-208` | ~50 |
| Card trạm cũ | `.station-card`, `.station-card-info`, `.station-card-value`, `.station-cards-list`, `.skeleton-list` | `styles.css:202-253` | ~45 |
| Header cũ (thay bởi `PageHeader`) | `.detail-header`, `.compare-header`, `.chat-header`, `.alerts-header`, `.approvals-header`, `.audit-header`, `.profile-header` | `styles.css:317-341`, `545-549` | ~30 |
| Subtitle cũ | `.detail-subtitle`, `.chat-subtitle`, `.alerts-subtitle`, `.approvals-subtitle`, `.audit-subtitle`, `.profile-subtitle` | `styles.css:134-145` | ~12 |
| Chat tools cũ (thay bởi `TechnicalDetails`) | `.used-tools`, `.tools-label` | `styles.css:606-624` | ~12 |
| Khác | `.station-id-tag`, `.alerts-filters`, `.detail-header-actions`, `.form-actions`, `.form-hint` | rải rác | ~15 |

Tổng **~224 dòng** trên tổng 1995 dòng của `styles.css` = **11% file là code chết**.

Nghiêm trọng hơn: các selector chết này **vẫn xuất hiện trong media query** (`styles.css:1738-1739`, `1750`, `1755-1757`, `1771`, `1789-1790`) và trong các nhóm selector chung (`styles.css:72-87`, `317-341`) — khiến việc đọc và sửa CSS trở nên nhiễu.

---

### ⚪ R-26 · Hai định nghĩa "card" cách nhau 1400 dòng

```css
/* styles.css:72-87 — Định nghĩa #1 */
.stat-card, .metric-card, .forecast-card, .compare-card, .profile-card,
.queue-section, .chat-container, .forecast-section, .history-section,
.difference-box, .compare-selectors, .alerts-filters {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);        /* ← A */
}

/* styles.css:411-419 */
.forecast-section, .history-section, .difference-box, .compare-selectors, .alerts-filters {
  border-radius: var(--radius-lg);     /* ← B: 12px */
}

/* styles.css:1843-1855 — Định nghĩa #2, dưới comment "Figma-aligned production surfaces" */
.metric-card, .history-section, .forecast-section, .compare-selectors,
.compare-card, .difference-box, .approval-workspace, .audit-filter-bar,
.profile-card, .chat-history-panel {
  border-radius: var(--radius-xl);     /* ← đè B, 16px. B thành code chết */
  box-shadow: var(--shadow-sm);        /* ← trùng lặp nguyên văn với A */
}
```

`box-shadow: var(--shadow-sm)` được khai báo **hai lần với giá trị y hệt**. `border-radius: var(--radius-lg)` ở dòng 419, 530, 859 **không bao giờ có hiệu lực** vì bị đè ở dòng 1853.

---

### ⚪ R-27 · Ba cặp override trực tiếp — quy tắc đầu là code chết

| Selector | Khai báo #1 | Khai báo #2 | Kết quả |
|---|---|---|---|
| `.profile-card` | `styles.css:858` `padding: var(--space-6)` (24px) | `styles.css:1945` `padding: 22px` | #1 chết hoàn toàn |
| `.group-options` | `styles.css:900` `grid-template-columns: repeat(3, ...)` | `styles.css:1956` `.profile-layout .group-options { 1fr }` | #1 chết (class chỉ dùng trong Profile) |
| `.radio-card` | `styles.css:906,909` `min-height: 112px; padding: 14px` | `styles.css:1957` `min-height: 74px; padding: 12px` | #1 chết |

Thêm nữa, `styles.css:1758-1759` có media query cho `.group-options` ở 900px:

```css
@media (max-width: 900px) { .forecast-grid, .group-options { grid-template-columns: 1fr; } }
```

`.group-options` **đã luôn là 1 cột** ở mọi kích thước (do dòng 1956) → media query này thừa. Tổng cộng **3 quy tắc** cho một thuộc tính duy nhất.

`.profile-card { max-width: 880px }` (dòng 857) cũng vô nghĩa vì `.profile-layout` là grid với cột `minmax(0, 1.25fr)`.

---

### ⚪ R-28 · Inline style tĩnh cho kích thước skeleton

Đã grep — 4 chỗ dùng inline style cho **giá trị tĩnh** (không phụ thuộc dữ liệu):

| File:Line | Code |
|---|---|
| [`StationDetail.tsx:55`](../features/stations/StationDetail.tsx#L55) | `style={{ height: 200 }}` |
| [`StationDetail.tsx:56`](../features/stations/StationDetail.tsx#L56) | `style={{ height: 350 }}` |
| [`CompareStations.tsx:53`](../features/stations/CompareStations.tsx#L53) | `style={{ height: 400 }}` |
| [`AlertList.tsx:96`](../features/alerts/AlertList.tsx#L96) | `style={{ height: 250 }}` |

Chiều cao cứng bằng px **không phản ứng với breakpoint**, nên skeleton 400px trên mobile không khớp với chiều cao thật của nội dung sau khi tải (compare card stack dọc → cao hơn nhiều) → **layout shift** khi dữ liệu về.

**Ghi chú công bằng:** 5 inline style còn lại **là hợp lệ** vì màu phụ thuộc dữ liệu runtime (`severity.color`) — `Dashboard.tsx:251, 340, 342` và `CompareStations.tsx:121, 138`. Không cần sửa. Chỉ `DataQualityBadge.tsx:43` là có vấn đề, nhưng vì lý do xung đột `border` (R-08), không phải vì dùng inline style.

---

### ⚪ R-29 · `Profile.tsx` lệch chuẩn format so với toàn repo

**File:** [`Profile.tsx:36, 39, 44, 45, 48, 50`](../features/profile/Profile.tsx#L36)

Sáu dòng JSX bị nén thành một dòng duy nhất. Dòng 39 dài **~490 ký tự**, chứa 3 `form-group` lồng nhau:

```tsx
<div className="profile-identity-grid"><label className="form-group"><span>Email</span><div className="readonly-field" aria-readonly="true">{userEmail}</div></label><label className="form-group"><span>Vai trò</span>...
```

Mọi file khác trong dự án (`Dashboard.tsx`, `AlertList.tsx`, `AppShell.tsx`, `AgentChat.tsx`) đều format chuẩn với indent 2 space và một element mỗi dòng. Hệ quả thực tế: mọi thay đổi nhỏ trong file này tạo ra một diff dài 490 ký tự — không review được.

Cùng vấn đề ở CSS: `styles.css:1876-1883` và `1944-1960` viết dạng một-dòng-một-rule trong khi 1800 dòng còn lại viết dạng multi-line.

---

### ⚪ R-30 · `<label>` bọc `<div>` không chứa form control

**File:** [`Profile.tsx:39`](../features/profile/Profile.tsx#L39)

```tsx
<label className="form-group">
  <span>Email</span>
  <div className="readonly-field" aria-readonly="true">{userEmail}</div>
</label>
```

Hai lỗi ngữ nghĩa:

1. `<label>` **không chứa form control** nào (`input`/`select`/`textarea`) → vô nghĩa với screen reader; theo HTML spec, label phải có labelable element.
2. `aria-readonly` trên `<div>` **không có `role`** là invalid ARIA — thuộc tính này chỉ hợp lệ trên các role như `textbox`, `combobox`, `checkbox`, `grid`.

---

### ⚪ R-31 · Hai nguồn sự thật cho thang màu PM2.5

Cùng một thang phân loại được định nghĩa **hai lần** ở hai ngôn ngữ:

```ts
// DataQualityBadge.tsx:12-17 — nguồn TS
if (pm25 <= 25)  return { class: "level-good",      color: "#10b981" };
if (pm25 <= 50)  return { class: "level-moderate",  color: "#f59e0b" };
if (pm25 <= 100) return { class: "level-unhealthy", color: "#ef4444" };
                 return { class: "level-hazardous", color: "#8b5cf6" };
```

```css
/* styles.css:285-305 — nguồn CSS, GIÁ TRỊ KHÁC */
.level-good      { color: var(--color-success-600); }  /* #059669 ≠ #10b981 */
.level-moderate  { color: var(--color-warning-600); }  /* #d97706 ≠ #f59e0b */
.level-unhealthy { color: var(--color-error-600); }    /* #e11d48 ≠ #ef4444 */
.level-hazardous { color: #7e22ce; }                   /* #7e22ce ≠ #8b5cf6 */
```

**Không có cặp nào khớp nhau.** Vì `DataQualityBadge` áp *cả hai* (`className={severity.class}` + `style={{ borderLeft: severity.color }}`), badge luôn có viền trái một màu và text/viền phải một màu khác.

Ngoài ra `#94a3b8` (offline) được hard-code lặp lại ở 3 nơi: `Dashboard.tsx:206`, `Dashboard.tsx:340`, `styles.css:1363`.

---

### ⚪ R-32 · Thiếu `type="button"`

| File:Line | Element |
|---|---|
| [`StationDetail.tsx:137`](../features/stations/StationDetail.tsx#L137) | `<button key={h} className="preset-btn">` |
| [`AlertList.tsx:119`](../features/alerts/AlertList.tsx#L119) | `<button className="btn-link table-station-link">` |

Hiện chưa gây lỗi vì cả hai đều nằm ngoài `<form>`. Nhưng mặc định của `<button>` là `type="submit"` — nếu sau này bọc vào form (ví dụ thêm bộ lọc dạng form), chúng sẽ submit form ngoài ý muốn. Component `Button` dùng chung **đã** mặc định `type="button"` đúng (`Button.tsx:12`); đây là hai chỗ viết `<button>` trần bỏ qua component đó.

---

### ⚪ R-33 · Cột "Hành động" trùng chức năng với cột "Trạm"

**File:** [`AlertList.tsx:118-133`](../features/alerts/AlertList.tsx#L118-L133)

```tsx
<td><button className="btn-link" onClick={() => handleFocusStation(alert.station_id)}>...</button></td>
...
<td><Button size="sm" onClick={() => handleFocusStation(alert.station_id)}>Xem trạm</Button></td>
```

Hai control gọi **cùng một hàm với cùng tham số**. Cột "Hành động" chiếm ~95px trong một bảng vốn đã phải cuộn ngang 417px trên mobile (R-21). Bỏ cột này giảm `min-width` từ 760px xuống ~665px.

---

## IV. Bảng đề xuất giải pháp

> **Ký hiệu:** `▸` = dòng thêm mới · `✕` = dòng xoá bỏ

### IV.1 — 🔴 Ưu tiên P0 (sửa ngay)

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|:--|:--|:--|:--|
| **R-01** | `styles.css` thiếu `.level-critical`; `AlertList.tsx:124` render `level-critical` | `Alert["severity"]` có giá trị `"critical"` nhưng CSS không định nghĩa → badge nghiêm trọng nhất thành pill xám, nhạt hơn "moderate". Đảo ngược tín hiệu an toàn. | Thêm vào `styles.css` cạnh `.level-*`:<br>`.level-critical {`<br>` color: var(--color-error-600);`<br>` background: var(--color-error-50);`<br>` font-weight: 800;`<br>`}`<br><br>Và dùng lại nhãn tiếng Việt trong `AlertList.tsx`:<br>`{SEVERITY_LABEL[alert.severity]}`<br>thay cho `{alert.severity.toUpperCase()}` |
| **R-02** | `AppShell.css:10-19` — `.app-sidebar` thiếu `overflow-y`, `.app-shell` có `overflow: hidden` | Nội dung sidebar cao 584px (resident) / 672px (manager). Vượt `100dvh` là bị cắt vĩnh viễn — **nút Đăng xuất không bấm được** trên laptop 768px và mọi điện thoại xoay ngang. | `.app-sidebar {`<br>` height: 100dvh;`<br>`▸ overflow-y: auto;`<br>`▸ overscroll-behavior: contain;`<br>`}`<br>`▸ .app-sidebar__nav { flex: 0 0 auto; }`<br>`▸ .app-sidebar__footer { position: sticky; bottom: 0; background: var(--color-surface); }` |
| **R-03** | `AppShell.css:456` dùng `transform: translateX(-102%)` để ẩn drawer | `transform` không loại phần tử khỏi tab order → Tab từ topbar rơi vào 10 control vô hình. Scrim ngay bên dưới **đã** dùng `visibility` đúng cách. | CSS:<br>`.app-sidebar {`<br>` transform: translateX(-102%);`<br>`▸ visibility: hidden;`<br>`▸ transition: transform 220ms ease, visibility 220ms ease;`<br>`}`<br>`.app-sidebar.is-open {`<br>` transform: translateX(0);`<br>`▸ visibility: visible;`<br>`}`<br><br>TSX (`AppShell.tsx:134`):<br>`<aside`<br>`  className={...}`<br>`▸ inert={!sidebarOpen \|\| undefined}`<br>`>` |
| **R-04** | `StationDetail.tsx:31-35` chỉ `console.error`; `:51` kiểm tra `loading \|\| !station` | API lỗi → `loading=false` nhưng `station=null` → skeleton quay vĩnh viễn với chữ "Đang tải". Không lỗi, không retry, không đường thoát. | Thêm state + nhánh error (xem patch đầy đủ ở **§V.1**). Tóm tắt:<br>`▸ const [error, setError] = useState<string\|null>(null);`<br>`catch { ▸ setError("Không thể tải..."); }`<br>`▸ if (error) return <ErrorState onRetry={fetchDetailData} />;`<br>`if (loading \|\| !station) return <Skeleton />;`<br><br>Áp dụng cùng cách cho `CompareStations.tsx:45-56` |

---

### IV.2 — 🟠 Ưu tiên P1

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|:--|:--|:--|:--|
| **R-05** | `styles.css:1655` — `.dashboard-search input` không có `color` | `<input>` kế thừa `color` từ cha. Cha đặt `--color-text-subtle` để tô icon → chữ user gõ ra **2.45:1**. `.topbar-search input` đã fix đúng, chỗ này sót. | `.dashboard-search input {`<br>`▸ color: var(--color-text);`<br>` background: transparent;`<br>`✕ font-size: 0.74rem;`<br>`▸ font-size: var(--font-size-sm);`<br>`}`<br>`▸ .dashboard-search input::placeholder { color: var(--color-text-muted); }` |
| **R-06** | `styles.css:1651` — `var(--color-primary-300)` chưa định nghĩa | Không có fallback → invalid at computed-value time → `border-color` về `currentColor` = `#94a3b8`. Focus ring xám, không thấy. | **Cách 1 (khuyến nghị)** — bổ sung token còn thiếu vào `theme.css`:<br>`▸ --color-primary-300: #a5b4fc;`<br><br>**Cách 2** — thêm fallback như `auth.css:386` đã làm:<br>`border-color: var(--color-primary-300, #a5b4fc);` |
| **R-07** | `Dashboard.tsx:198` — `scrollWheelZoom` bật mặc định | Bản đồ 490px (370px mobile) giữa trang cuộn → lăn chuột/vuốt bị bẫy vào bản đồ. Anti-pattern đã biết từ 2015. | `<MapContainer`<br>`  center={[20.9446, 105.9447]}`<br>`  zoom={16}`<br>`✕ scrollWheelZoom`<br>`▸ scrollWheelZoom={false}`<br>`▸ tap={false}`<br>`  className="dashboard-map"`<br>`>`<br><br>Bù lại bằng nút zoom sẵn có của Leaflet (`.leaflet-control-zoom` đã được style ở `styles.css:1390`) |
| **R-08** | `DataQualityBadge.tsx:43` — inline `borderLeft: 4px` đè lên `.badge { border: 1px; border-radius: 9999px }` | 3 cạnh 1px + trái 4px trên hình viên thuốc → viền biến dạng lưỡi liềm, text lệch 3px. Màu viền trái (`#10b981`) khác màu text (`#059669`). | Bỏ inline style, dùng CSS var cho màu động:<br><br>TSX:<br>`✕ style={{ borderLeft: \`4px solid ${severity.color}\` }}`<br>`▸ style={{ "--badge-accent": severity.color } as React.CSSProperties}`<br><br>CSS:<br>`▸ .badge { border-color: var(--badge-accent, currentColor); }`<br>`▸ .badge::before {`<br>`▸  width: 6px; height: 6px; border-radius: 50%;`<br>`▸  background: var(--badge-accent, currentColor);`<br>`▸  content: "";`<br>`▸ }` |
| **R-09** | 12 quy tắc dưới 11px; thấp nhất `0.56rem` = 8.96px | Dưới ngưỡng 12px của Material/HIG. Ảnh hưởng cả **nội dung chính** (tên trạm 10.56px, nội dung cảnh báo 10.56px). Token `--font-size-*` có sẵn nhưng không dùng. | Thêm sàn vào `theme.css`:<br>`▸ --font-size-2xs: 0.6875rem;  /* 11px — chỉ cho nhãn IN HOA */`<br><br>Rồi thay toàn bộ giá trị `rem` thập phân bằng token (bảng ánh xạ đầy đủ ở **§V.2**). Ví dụ:<br>`.dashboard-station-row__identity span {`<br>`✕ font-size: 0.66rem;`<br>`▸ font-size: var(--font-size-xs);  /* 12px */`<br>`}` |
| **R-10** | `theme.css:45` — `--color-text-subtle: #94a3b8` dùng cho text | **2.56:1** trên trắng, **2.45:1** trên slate-50. Fail cả AA lẫn AA Large. Dùng ở 8 vị trí text thật. | Đôn thang màu chữ xuống một bậc, giữ nguyên số cấp:<br>`✕ --color-text-muted: var(--color-slate-500);   /* 4.76:1 */`<br>`✕ --color-text-subtle: var(--color-slate-400);  /* 2.56:1 ❌ */`<br>`▸ --color-text-muted: var(--color-slate-600);   /* 7.58:1 ✅ */`<br>`▸ --color-text-subtle: var(--color-slate-500);  /* 4.76:1 ✅ */`<br>`▸ --color-decorative: var(--color-slate-400);   /* icon/viền, KHÔNG dùng cho text */`<br><br>Rồi đổi `.legend-dot`, icon wrapper sang `--color-decorative` |
| **R-11** | `h1` = 24px < `.dashboard-kpi__copy strong` = 29.6px < `.metric-value` = 42.4px; `h2` = 15.7px | Số trang trí to hơn tiêu đề trang 76%. `h2` chỉ hơn body 1.7px → không nhận ra là heading. | `.page-header h1 {`<br>`✕ font-size: clamp(1.25rem, 2.2vw, 1.5rem);`<br>`▸ font-size: clamp(1.5rem, 2.6vw, 1.875rem);  /* 24→30px */`<br>`}`<br>`.dashboard-panel-header h2, .dashboard-rail-card__header h2 {`<br>`✕ font-size: 0.98rem;`<br>`▸ font-size: var(--font-size-lg);  /* 18px */`<br>`}`<br>`.dashboard-kpi__copy strong {`<br>`✕ font-size: clamp(1.45rem, 2vw, 1.85rem);`<br>`▸ font-size: clamp(1.375rem, 1.8vw, 1.625rem);  /* ≤26px < h1 */`<br>`}`<br>`.metric-value {`<br>`✕ font-size: clamp(1.75rem, 4vw, 2.65rem);`<br>`▸ font-size: clamp(1.625rem, 3vw, 2.125rem);  /* ≤34px */`<br>`}` |
| **R-12** | `styles.css:472` — `.preset-btn.active` dùng chung khai báo với `:hover`; JSX thiếu `aria-pressed` | Nút đang chọn trông giống hệt nút đang hover → không biết đang xem khoảng thời gian nào. | CSS — tách riêng, tăng độ tương phản:<br>`✕ .preset-btn:hover, .pill-btn:hover, .preset-btn.active { ... }`<br>`▸ .preset-btn:hover, .pill-btn:hover {`<br>`▸   border-color: var(--color-primary-200);`<br>`▸   background: var(--color-primary-50);`<br>`▸ }`<br>`▸ .preset-btn.active {`<br>`▸   border-color: var(--color-primary-600);`<br>`▸   color: #fff;`<br>`▸   background: var(--color-primary-600);`<br>`▸   font-weight: 700;`<br>`▸ }`<br><br>TSX (`StationDetail.tsx:137`):<br>`<button`<br>`▸ type="button"`<br>`▸ aria-pressed={rangeHours === h}`<br>`  className={\`preset-btn ${rangeHours === h ? "active" : ""}\`}` |
| **R-13** | `Dashboard.tsx:287` — empty state chỉ kiểm tra `length === 0` | Trong lúc fetch, `alerts=[]` → UI khẳng định **"Không có cảnh báo đang kích hoạt"**, một tuyên bố sai về an toàn, rồi mới nhảy sang danh sách đỏ. | `✕ {activeAlerts.length === 0 ? (`<br>`▸ {loading ? (`<br>`▸   <div className="skeleton-card" />`<br>`▸ ) : activeAlerts.length === 0 ? (`<br>`    <div className="dashboard-empty-state">...</div>`<br>`  ) : ...}`<br><br>Áp dụng cùng cách cho panel "Các trạm" (`Dashboard.tsx:328`) |

---

### IV.3 — 🟡 Ưu tiên P2

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|:--|:--|:--|:--|
| **R-14** | `AppShell.tsx:216-221` — ô search không handler, `<kbd>⌘ K</kbd>` cho user Windows | Affordance hứa chức năng không tồn tại. Không có listener `Cmd/Ctrl+K` nào trong codebase. `⌘` là phím macOS. | **Cách 1 (khuyến nghị)** — ẩn cho đến khi làm thật:<br>Xoá block `<label className="topbar-search">` khỏi `AppShell.tsx`<br><br>**Cách 2** — nối vào state search sẵn có + sửa ký hiệu:<br>`▸ <input value={q} onChange={e => setQ(e.target.value)} />`<br>`▸ <kbd>{navigator.platform.startsWith("Mac") ? "⌘" : "Ctrl"} K</kbd>` |
| **R-15** | `styles.css:1631` — `.status-badge { font-size: 0 }` | Người dùng sáng mắt chỉ thấy icon 13px trần, không nhãn, không tooltip. Icon lại `aria-hidden` nên tự nó vô nghĩa. | `✕ .dashboard-alert-item__meta .status-badge { padding: 3px 5px; font-size: 0; }`<br>`▸ .dashboard-alert-item__meta .status-badge {`<br>`▸   padding: 3px 7px;`<br>`▸   font-size: var(--font-size-2xs);`<br>`▸ }`<br><br>Nếu bắt buộc phải giữ chật, dùng `title` thay vì `font-size: 0`:<br>`<span className="status-badge" title={label}>` |
| **R-16** | `CompareStations.tsx:83,100` — `<label>` không `htmlFor`, `<select>` không `id` | Không có liên kết label↔control. Screen reader đọc "combo box" trống. Click nhãn không focus. `AlertFilters.tsx` cùng repo làm đúng. | `▸ <label htmlFor="compare-station-a">Trạm A:</label>`<br>`  <select`<br>`▸   id="compare-station-a"`<br>`    value={compareStationIds[0]}`<br>`  >`<br><br>Tương tự cho `compare-station-b` |
| **R-17** | Nhảy `h1` → `h3` (StationDetail), `h4` sau `h3` (CompareStations) | Vi phạm WCAG 2.4.10. Screen reader duyệt theo heading thấy cấu trúc khuyết tầng. | `StationDetail.tsx:117,134`:<br>`✕ <h3><Sparkles /> Dự báo PM2.5...</h3>`<br>`▸ <h2><Sparkles /> Dự báo PM2.5...</h2>`<br><br>`CompareStations.tsx:154`:<br>`✕ <h4><GitCompareArrows /> Kết quả so sánh</h4>`<br>`▸ <h2><GitCompareArrows /> Kết quả so sánh</h2>`<br><br>Đổi `.forecast-section h3` → `h2` trong selector CSS tương ứng |
| **R-18** | `styles.css:1457,1783` — `padding-left: 59px` magic number giữ nguyên ở mobile | Còn **189px** cho nội dung trên màn 320px, trong khi 59px bên trái bỏ trống. Nhãn + giá trị + đơn vị + badge xuống 3 dòng. | Thay magic number bằng biến, và bỏ hẳn ở mobile:<br>`▸ .dashboard-selected-station { --station-chip: 46px; --station-gap: 13px; }`<br>`.dashboard-selected-station__reading {`<br>`✕ padding-left: 59px;`<br>`▸ padding-left: calc(var(--station-chip) + var(--station-gap));`<br>`}`<br>`@media (max-width: 640px) {`<br>`  .dashboard-selected-station__reading {`<br>`✕   padding-left: 59px;`<br>`▸   padding-left: 0;`<br>`  }`<br>`}` |
| **R-19** | `styles.css:1057-1058` — `.btn-link { min-height: auto; padding: 0 }` | Vùng chạm ~18px, dưới ngưỡng 24px của WCAG 2.5.8. Đây là điều hướng chính của bảng cảnh báo. | `.btn-link {`<br>`✕ min-height: auto;`<br>`✕ padding: 0;`<br>`▸ min-height: 24px;`<br>`▸ padding: 2px 0;`<br>`▸ text-decoration: underline;`<br>`▸ text-underline-offset: 3px;`<br>`}` |
| **R-20** | `styles.css:462` — `.preset-btn/.pill-btn { padding: 7px 11px }` → ~28px cao | Dưới 44px khuyến nghị. Đây là điều khiển chính của biểu đồ và lối vào AI Agent. | `.preset-btn, .pill-btn {`<br>`✕ padding: 7px 11px;`<br>`✕ font-size: 0.72rem;`<br>`▸ min-height: 36px;`<br>`▸ padding: 8px 14px;`<br>`▸ font-size: var(--font-size-xs);`<br>`}`<br>`▸ @media (pointer: coarse) {`<br>`▸   .preset-btn, .pill-btn { min-height: 44px; }`<br>`▸ }` |
| **R-21** | `AlertList.tsx:100` — bảng 8 cột `min-width: 760px`, wrapper thiếu `tabindex` | Cuộn ngang 417px trên iPhone SE, mất ngữ cảnh cột đầu. Người dùng bàn phím **không cuộn ngang được** (WCAG 2.1.1). | **Sửa nhanh** — cho vùng cuộn nhận focus:<br>`<div className="table-wrapper"`<br>`▸  tabIndex={0}`<br>`▸  role="region"`<br>`▸  aria-label="Bảng danh sách cảnh báo"`<br>`>`<br><br>**Sửa đúng** — chuyển sang card ở mobile:<br>`▸ @media (max-width: 640px) {`<br>`▸   .data-table thead { position: absolute; clip-path: inset(50%); }`<br>`▸   .data-table, .data-table tbody, .data-table tr, .data-table td { display: block; }`<br>`▸   .data-table { min-width: 0; }`<br>`▸   .data-table tr {`<br>`▸     margin-bottom: 10px;`<br>`▸     border: 1px solid var(--color-border);`<br>`▸     border-radius: var(--radius-lg);`<br>`▸   }`<br>`▸   .data-table td::before {`<br>`▸     display: block;`<br>`▸     color: var(--color-text-muted);`<br>`▸     content: attr(data-label);`<br>`▸     font-size: var(--font-size-2xs);`<br>`▸   }`<br>`▸ }`<br><br>Kèm `<td data-label="Mức độ">` trong TSX |
| **R-22** | `styles.css:1777` — `.dashboard-kpi__copy small { display: none }` ở 640px | Ẩn **"{n} trạm có dữ liệu hợp lệ"** — điều kiện diễn giải của con số PM2.5 trung bình. Đúng loại thông tin mà `SimulatorBanner` đang nhấn mạnh. | `@media (max-width: 640px) {`<br>`✕ .dashboard-kpi__copy small { display: none; }`<br>`▸ .dashboard-kpi__copy small {`<br>`▸   font-size: var(--font-size-2xs);`<br>`▸   white-space: normal;`<br>`▸   line-height: 1.3;`<br>`▸ }`<br>`▸ .dashboard-kpi { min-height: 132px; }`<br>`}` |
| **R-23** | 3 file dùng `toLocaleString("vi-VN")` không có `timeZone` | `"vi-VN"` chỉ đặt locale, không đặt timezone → hiển thị theo giờ máy. Cùng mốc thời gian ra kết quả khác nhau giữa Dashboard và StationDetail. `StationDetail.tsx:109` lại ghi "Múi giờ: Asia/Ho_Chi_Minh" — khẳng định sai. | Trích `formatUpdatedAt` từ `Dashboard.tsx:28-39` ra `src/utils/datetime.ts`, rồi dùng chung:<br><br>`▸ // src/utils/datetime.ts`<br>`▸ export const VN_TZ = "Asia/Ho_Chi_Minh";`<br>`▸ export const formatDateTime = (v?: string) => ...`<br>`▸   new Intl.DateTimeFormat("vi-VN", { ..., timeZone: VN_TZ }).format(d);`<br><br>Thay ở `StationDetail.tsx:108`, `AlertList.tsx:127`, `CompareStations.tsx:130,147` |
| **R-24** | `styles.css:483-517` — `.compare-selectors` wrap dưới 562px, `.vs-badge` mồ côi | Toàn bộ điện thoại (375–430px) đều dưới ngưỡng. Badge "VS" bị đẩy cạnh Trạm A, mất ý nghĩa ngăn cách. | `▸ @media (max-width: 640px) {`<br>`▸   .compare-selectors {`<br>`▸     flex-direction: column;`<br>`▸     align-items: stretch;`<br>`▸     gap: var(--space-3);`<br>`▸   }`<br>`▸   .vs-badge {`<br>`▸     width: 100%;`<br>`▸     height: 28px;`<br>`▸     border-radius: var(--radius-full);`<br>`▸   }`<br>`▸ }` |

---

### IV.4 — ⚪ Clean Code

| # | Lỗi hiện tại | Lý do | Code sửa lại |
|:--|:--|:--|:--|
| **R-25** | ~224 dòng CSS chết (11% `styles.css`) | Đã grep toàn bộ `*.tsx` — 0 kết quả. Selector chết còn xuất hiện trong 6 media query và 2 nhóm selector chung → gây nhiễu khi đọc/sửa. | Xoá các block: `styles.css:65-145` (`.stats-grid`, `.stat-*`), `147-208` (`.map-layout`, `.map-wrapper`, `.map`, `.station-sidebar`, `.sidebar-header`), `210-253` (`.station-card*`, `.skeleton-list`), `317-341` (`.detail-header`…`.profile-header`), `545-549` (`.chat-header`), `606-624` (`.used-tools`, `.tools-label`), `.station-id-tag`, `.alerts-filters`, `.detail-header-actions`, `.form-actions`, `.form-hint`<br><br>Dọn kèm tham chiếu trong media query: dòng `1738-1739`, `1750`, `1755-1757`, `1771`, `1789-1790` |
| **R-26** | `box-shadow: var(--shadow-sm)` khai báo 2 lần (dòng 86 và 1854); `border-radius: --radius-lg` (419/530/859) bị `--radius-xl` (1853) đè | Hai định nghĩa "card" cách nhau 1400 dòng. Sửa một chỗ không có tác dụng vì chỗ kia đè lên. | Gộp thành **một** class nền tảng:<br>`▸ .surface-card {`<br>`▸   border: 1px solid var(--color-border);`<br>`▸   border-radius: var(--radius-xl);`<br>`▸   background: var(--color-surface);`<br>`▸   box-shadow: var(--shadow-sm);`<br>`▸ }`<br><br>Rồi `.metric-card, .compare-card, .profile-card, … { @extend / composes }` hoặc đơn giản là gộp danh sách selector, xoá block trùng ở `1843-1855` |
| **R-27** | 3 cặp override trực tiếp + 1 media query thừa | `.profile-card` padding, `.group-options` cột, `.radio-card` min-height — quy tắc đầu chết hoàn toàn. `.group-options` có tới **3 quy tắc** cho 1 thuộc tính. | Xoá quy tắc chết:<br>`✕ styles.css:858  .profile-card { padding: var(--space-6); }`<br>`✕ styles.css:857  .profile-card { max-width: 880px; }`<br>`✕ styles.css:900  .group-options { grid-template-columns: repeat(3, ...); }`<br>`✕ styles.css:1759 @media 900px { .group-options { 1fr } }`<br>`✕ styles.css:906,909 .radio-card { min-height: 112px; padding: 14px; }`<br><br>Giữ lại giá trị thật ở `1945`, `1956`, `1957` |
| **R-28** | 4 inline `style={{ height: N }}` trên `.skeleton-card` | px cứng không phản ứng breakpoint → skeleton 400px không khớp chiều cao thật sau khi tải (compare card stack dọc trên mobile) → **layout shift**. | CSS:<br>`▸ .skeleton-card--sm { min-height: 200px; }`<br>`▸ .skeleton-card--md { min-height: 250px; }`<br>`▸ .skeleton-card--lg { min-height: 350px; }`<br>`▸ @media (max-width: 640px) {`<br>`▸   .skeleton-card--lg { min-height: 260px; }`<br>`▸ }`<br><br>TSX:<br>`✕ <div className="skeleton-card" style={{ height: 350 }} />`<br>`▸ <div className="skeleton-card skeleton-card--lg" />`<br><br>*(5 inline style còn lại dùng `severity.color` động — giữ nguyên, hợp lệ)* |
| **R-29** | `Profile.tsx:36,39,44,45,48,50` JSX một dòng (dòng 39 ~490 ký tự) | Lệch chuẩn so với mọi file khác trong repo. Mọi thay đổi nhỏ tạo diff 490 ký tự — không review được. | Chạy Prettier trên file, hoặc format thủ công 2-space indent như `Dashboard.tsx`. Áp dụng cả cho `styles.css:1876-1883`, `1944-1960`.<br><br>Cân nhắc thêm `.prettierrc` + script:<br>`▸ "format": "prettier --write \\"src/**/*.{ts,tsx,css}\\""` |
| **R-30** | `Profile.tsx:39` — `<label>` bọc `<div className="readonly-field">` + `aria-readonly` trên `div` không role | `<label>` không chứa labelable element → vô nghĩa với screen reader. `aria-readonly` không hợp lệ nếu thiếu role. | `✕ <label className="form-group">`<br>`✕   <span>Email</span>`<br>`✕   <div className="readonly-field" aria-readonly="true">{userEmail}</div>`<br>`✕ </label>`<br><br>`▸ <div className="form-group">`<br>`▸   <span id="lbl-email">Email</span>`<br>`▸   <p className="readonly-field" aria-labelledby="lbl-email">{userEmail}</p>`<br>`▸ </div>`<br><br>Áp dụng cho cả 3 field: Email, Vai trò, Đơn vị |
| **R-31** | Thang màu PM2.5 định nghĩa 2 lần với **4/4 cặp giá trị lệch nhau** | `#10b981`≠`#059669`, `#f59e0b`≠`#d97706`, `#ef4444`≠`#e11d48`, `#8b5cf6`≠`#7e22ce`. Badge luôn có viền trái một màu, text màu khác. `#94a3b8` hard-code ở 3 nơi. | Đưa CSS thành nguồn sự thật duy nhất, TS chỉ trả tên biến:<br><br>`theme.css`:<br>`▸ --pm25-good: #059669;`<br>`▸ --pm25-moderate: #d97706;`<br>`▸ --pm25-unhealthy: #e11d48;`<br>`▸ --pm25-hazardous: #7e22ce;`<br>`▸ --pm25-offline: var(--color-slate-400);`<br><br>`DataQualityBadge.tsx`:<br>`✕ color: "#10b981"`<br>`▸ color: "var(--pm25-good)"`<br><br>Rồi `Dashboard.tsx:206,340` và `styles.css:1363` cùng dùng `var(--pm25-offline)` |
| **R-32** | `StationDetail.tsx:137`, `AlertList.tsx:119` — `<button>` trần thiếu `type` | Mặc định `type="submit"`. Hiện chưa lỗi (ngoài form) nhưng sẽ submit ngoài ý muốn nếu bọc form sau này. Component `Button` dùng chung đã mặc định đúng. | `▸ <button type="button" className="preset-btn" ...>`<br>`▸ <button type="button" className="btn-link table-station-link" ...>`<br><br>Hoặc dùng lại component có sẵn:<br>`▸ <Button variant="ghost" size="sm" ...>` |
| **R-33** | `AlertList.tsx:119,130` — cột "Trạm" và cột "Hành động" gọi cùng `handleFocusStation(alert.station_id)` | Hai control trùng chức năng. Cột thừa chiếm ~95px trong bảng vốn phải cuộn ngang 417px trên mobile. | Xoá cột "Hành động":<br>`✕ <th>Hành động</th>`<br>`✕ <td><Button ...>Xem trạm</Button></td>`<br><br>Giữ link tên trạm (đã sửa touch target ở R-19). Giảm `min-width` bảng:<br>`.data-table {`<br>`✕ min-width: 760px;`<br>`▸ min-width: 665px;`<br>`}` |

---

## V. Patch chi tiết

### V.1 — Sửa R-04: xử lý lỗi cho `StationDetail`

```tsx
// features/stations/StationDetail.tsx

export const StationDetail: React.FC = () => {
  const { selectedStationId, navigateTo, setCompareStationIds } = useAuth();
  const [station, setStation] = useState<StationDetailData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [rangeHours, setRangeHours] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);          // ▸ THÊM

  const fetchDetailData = async () => {                             // ▸ đưa ra ngoài useEffect
    setLoading(true);
    setError(null);                                                 // ▸ THÊM
    try {
      const [currentData, historyData, forecastData] = await Promise.all([
        api.getStationCurrent(selectedStationId),
        api.getStationHistory(selectedStationId, rangeHours),
        api.getStationForecast(selectedStationId),
      ]);
      setStation(currentData);
      setHistory(historyData);
      setForecast(forecastData);
    } catch {
      setError("Không thể tải dữ liệu trạm. Vui lòng thử lại.");    // ▸ THÊM
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetailData();
  }, [selectedStationId, rangeHours]);

  // ▸ THÊM: nhánh lỗi PHẢI đứng trước nhánh skeleton
  if (error) {
    return (
      <div className="detail-container">
        <PageHeader
          title="Chi tiết trạm"
          leading={(
            <Button variant="ghost" size="sm" onClick={() => navigateTo("dashboard")}>
              <ArrowLeft size={16} aria-hidden="true" /> Quay lại bản đồ
            </Button>
          )}
        />
        <div className="alert-box alert-error" role="alert">
          <TriangleAlert size={17} aria-hidden="true" />
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={fetchDetailData}>Thử lại</Button>
        </div>
      </div>
    );
  }

  if (loading || !station) {
    return (
      <div className="detail-container">
        <PageHeader title="Chi tiết trạm" description="Đang tải dữ liệu hiện tại, lịch sử và dự báo ngắn hạn." />
        <div className="skeleton-card skeleton-card--sm" />          {/* ▸ bỏ inline style, R-28 */}
        <div className="skeleton-card skeleton-card--lg" />
      </div>
    );
  }
  // ...
};
```

> Áp dụng **cùng cấu trúc** cho `CompareStations.tsx:45-56` — hiện tại `error` chỉ được render bên trong nhánh `loading`, nên khi `stationA`/`stationB` là `null` thì skeleton cũng quay vĩnh viễn.

---

### V.2 — Sửa R-09: bảng ánh xạ cỡ chữ về token

```css
/* theme.css — thêm bậc 11px cho nhãn IN HOA */
:root {
  --font-size-2xs: 0.6875rem;  /* 11px — CHỈ dùng cho nhãn uppercase + font-weight ≥700 */
  --font-size-xs:  0.75rem;    /* 12px — sàn tuyệt đối cho mọi text thường */
  /* ... các bậc còn lại giữ nguyên */
}
```

| Selector | File:Line | Hiện tại | Thay bằng | px sau sửa |
|---|---|---|---|---|
| `.dashboard-station-row__value small` | `styles.css:1720` | `0.56rem` | `var(--font-size-2xs)` | 8.96 → **11** |
| `.dashboard-selected-station__reading .badge` | `styles.css:1483` | `0.59rem` | `var(--font-size-2xs)` | 9.44 → **11** |
| `.dashboard-alert-item__copy time` | `styles.css:1614` | `0.6rem` | `var(--font-size-xs)` | 9.6 → **12** |
| `.dashboard-alert-item__meta b` | `styles.css:1625` | `0.6rem` | `var(--font-size-2xs)` | 9.6 → **11** |
| `.dashboard-health-grid small` | `styles.css:1534` | `0.62rem` | `var(--font-size-xs)` | 9.92 → **12** |
| `.chat-history-item small` | `styles.css:1881` | `0.63rem` | `var(--font-size-xs)` | 10.08 → **12** |
| `.dashboard-eyebrow` | `styles.css:1332` | `0.64rem` | `var(--font-size-2xs)` | 10.24 → **11** |
| `.dashboard-selected-station__reading strong em` | `styles.css:1474` | `0.64rem` | `var(--font-size-xs)` | 10.24 → **12** |
| `.message-time`, `.tools-label` | `styles.css:609` | `0.65rem` | `var(--font-size-xs)` | 10.4 → **12** |
| `.chat-history-panel__title` | `styles.css:1876` | `0.65rem` | `var(--font-size-2xs)` | 10.4 → **11** |
| `.chat-history-empty` | `styles.css:1882` | `0.65rem` | `var(--font-size-xs)` | 10.4 → **12** |
| **`.dashboard-alert-item__copy small`** | `styles.css:1606` | `0.66rem` | `var(--font-size-sm)` | 10.56 → **14** |
| **`.dashboard-station-row__identity span`** | `styles.css:1713` | `0.66rem` | `var(--font-size-xs)` | 10.56 → **12** |
| `.prop-time` | `styles.css:776` | `0.66rem` | `var(--font-size-xs)` | 10.56 → **12** |
| `.data-table th` | `styles.css:806` | `0.67rem` | `var(--font-size-2xs)` | 10.72 → **11** |
| `.app-footer` | `AppShell.css:429` | `0.68rem` | `var(--font-size-xs)` | 10.9 → **12** |
| `.dashboard-kpi__copy small` | `styles.css:1275` | `0.68rem` | `var(--font-size-xs)` | 10.9 → **12** |
| `.dashboard-selected-station p` | `styles.css:1447` | `0.68rem` | `var(--font-size-xs)` | 10.9 → **12** |
| `.badge` | `styles.css:280` | `0.69rem` | `var(--font-size-xs)` | 11 → **12** |

> **Lưu ý về không gian:** tăng cỡ chữ sẽ nới cao dòng. Cần chỉnh kèm `.dashboard-station-row { min-height: 58px → 64px }` và `.dashboard-alert-item { padding: 11px → 12px }` để tránh chật.

---

### V.3 — Sửa R-10: thang màu chữ đạt WCAG AA

```css
/* theme.css — đôn xuống một bậc, giữ nguyên 3 cấp phân biệt */
:root {
  --color-text:        var(--color-slate-900);  /* #0f172a — 17.85:1 ✅ */
  --color-text-muted:  var(--color-slate-600);  /* #475569 —  7.58:1 ✅  (cũ: slate-500, 4.76:1) */
  --color-text-subtle: var(--color-slate-500);  /* #64748b —  4.76:1 ✅  (cũ: slate-400, 2.56:1 ❌) */

  /* ▸ THÊM: slate-400 chỉ dùng cho phần tử phi-văn-bản */
  --color-decorative:  var(--color-slate-400);  /* #94a3b8 — icon, chấm, viền */
}
```

Sau khi đổi, chuyển các chỗ dùng `--color-text-subtle` cho **mục đích trang trí** sang `--color-decorative`:

| Selector | File:Line | Ghi chú |
|---|---|---|
| `.input-with-icon > svg` | `styles.css:714` | Icon kính lúp — không phải text |
| `.dashboard-search` (wrapper) | `styles.css:1645` | Chỉ tô icon; input đã có `color` riêng (R-05) |
| `.topbar-search` (wrapper) | `AppShell.css:262` | Như trên |
| `.legend-dot--offline` | `styles.css:1363` | Nên dùng `var(--pm25-offline)` — xem R-31 |

---

## VI. Thứ tự triển khai đề xuất

| Đợt | Hạng mục | Ước lượng | Rủi ro hồi quy |
|---|---|---|---|
| **1** | R-01, R-02, R-03, R-04 (P0) | ~2h | Thấp — thêm mới, ít đè lên code cũ |
| **2** | R-05, R-06, R-07, R-08, R-12, R-13 (P1 chức năng) | ~3h | Thấp |
| **3** | R-25, R-26, R-27 (dọn CSS chết) | ~1h | **Trung bình** — cần kiểm tra kỹ Admin không dùng chung class. Làm **trước** đợt 4 để đợt 4 không sửa nhầm code chết. |
| **4** | R-09, R-10, R-11 (typography + contrast) | ~3h | **Cao** — ảnh hưởng toàn bộ màn hình. Cần chụp ảnh so sánh trước/sau ở 5 breakpoint. |
| **5** | R-14→R-24 (P2) | ~4h | Thấp |
| **6** | R-28→R-33 (clean code còn lại) | ~2h | Thấp |

---

## VII. Tiêu chí nghiệm thu

- [ ] Alert `severity: "critical"` hiển thị badge **đỏ**, đậm hơn `moderate` (R-01)
- [ ] Thu cửa sổ trình duyệt còn **500px chiều cao** → nút **Đăng xuất** vẫn bấm được (R-02)
- [ ] Trên mobile, drawer đóng → nhấn Tab liên tục **không** rơi vào menu vô hình (R-03)
- [ ] Ngắt mạng → mở `StationDetail` → thấy **thông báo lỗi + nút Thử lại**, không phải skeleton quay mãi (R-04)
- [ ] Gõ vào ô tìm kiếm trong panel "Các trạm" → chữ **đọc được rõ** (R-05)
- [ ] Focus vào ô tìm kiếm Dashboard → viền chuyển **xanh indigo** (R-06)
- [ ] Lăn chuột qua bản đồ → **trang cuộn**, bản đồ không zoom (R-07)
- [ ] Badge chất lượng dữ liệu có viền **đều 4 cạnh**, text căn giữa (R-08)
- [ ] Chạy axe DevTools trên cả 6 màn cư dân → **0 lỗi** contrast và **0 lỗi** heading order (R-09, R-10, R-17)
- [ ] `<h1>` là phần tử chữ **lớn nhất** trên mọi trang (R-11)
- [ ] Hover nút "72h" trong khi "24h" đang chọn → **phân biệt rõ** hai nút (R-12)
- [ ] Refresh Dashboard với mạng chậm (throttle 3G) → **không** thấy chữ "Không có cảnh báo đang kích hoạt" nhấp nháy (R-13)
- [ ] Kiểm tra ở **320 / 375 / 430 / 768 / 1024 / 1280 / 1920px** → không có thanh cuộn ngang ngoài ý muốn
- [ ] Kiểm tra iPhone **xoay ngang** (844×390) → sidebar cuộn được, đủ nội dung
- [ ] `grep -rn "stats-grid\|stat-card\|map-layout\|station-card" src/` → **0 kết quả** trong `styles.css` sau khi dọn (R-25)
- [ ] `npm run build` không cảnh báo; đo lại kích thước `styles.css` giảm ~11%

---

## Phụ lục A — Danh mục lỗi đầy đủ

| # | Mức | Hạng mục | File | Tóm tắt |
|:--|:--|:--|:--|:--|
| R-01 | 🔴 P0 | Vỡ khung | `styles.css`, `AlertList.tsx:124` | Thiếu `.level-critical` → cảnh báo nghiêm trọng thành pill xám |
| R-02 | 🔴 P0 | Responsive | `AppShell.css:10-19` | Sidebar thiếu `overflow-y` → mất nút Đăng xuất |
| R-03 | 🔴 P0 | A11y | `AppShell.css:456` | Drawer đóng vẫn nhận focus bàn phím |
| R-04 | 🔴 P0 | UX | `StationDetail.tsx:31-59` | Nuốt lỗi API → skeleton quay vĩnh viễn |
| R-05 | 🟠 P1 | Contrast | `styles.css:1655` | Chữ gõ vào ô search Dashboard 2.45:1 |
| R-06 | 🟠 P1 | Bug CSS | `styles.css:1651` | `--color-primary-300` không tồn tại → focus ring hỏng |
| R-07 | 🟠 P1 | UX | `Dashboard.tsx:198` | Leaflet `scrollWheelZoom` bẫy thao tác cuộn |
| R-08 | 🟠 P1 | Vỡ khung | `DataQualityBadge.tsx:43` | Inline `borderLeft` đè `.badge` → viền lưỡi liềm |
| R-09 | 🟠 P1 | Typography | `styles.css` (12 chỗ) | 12 quy tắc dưới 11px, thấp nhất 8.96px |
| R-10 | 🟠 P1 | Contrast | `theme.css:45` | `--color-text-subtle` 2.56:1, dùng ở 8 chỗ text |
| R-11 | 🟠 P1 | Hierarchy | `styles.css:43,1257,378` | Số KPI 29.6px > `h1` 24px; `h2` chỉ 15.7px |
| R-12 | 🟠 P1 | UX/A11y | `styles.css:472`, `StationDetail.tsx:137` | `.active` giống hệt `:hover`, thiếu `aria-pressed` |
| R-13 | 🟠 P1 | UX | `Dashboard.tsx:287` | Empty state khẳng định sai trong lúc tải |
| R-14 | 🟡 P2 | UX | `AppShell.tsx:216` | Ô search giả + `⌘ K` không tồn tại |
| R-15 | 🟡 P2 | A11y | `styles.css:1631` | `font-size: 0` xoá nhãn trạng thái |
| R-16 | 🟡 P2 | A11y | `CompareStations.tsx:83,100` | `<label>` không `htmlFor` |
| R-17 | 🟡 P2 | A11y | `StationDetail.tsx`, `CompareStations.tsx` | Nhảy cấp heading h1→h3, h4 sau h3 |
| R-18 | 🟡 P2 | Spacing | `styles.css:1457,1783` | `padding-left: 59px` magic number ở mobile |
| R-19 | 🟡 P2 | Touch | `styles.css:1057` | `.btn-link` cao ~18px |
| R-20 | 🟡 P2 | Touch | `styles.css:462` | `.preset-btn`/`.pill-btn` cao ~28px |
| R-21 | 🟡 P2 | Responsive | `AlertList.tsx:100` | Bảng 8 cột không có fallback mobile |
| R-22 | 🟡 P2 | Responsive | `styles.css:1777` | Ẩn ngữ cảnh KPI thay vì reflow |
| R-23 | 🟡 P2 | Nhất quán | 3 file | Múi giờ lệch nhau giữa các màn hình |
| R-24 | 🟡 P2 | Vỡ khung | `styles.css:483-517` | Badge "VS" mồ côi dưới 562px |
| R-25 | ⚪ P3 | Clean | `styles.css` | ~224 dòng CSS chết (11% file) |
| R-26 | ⚪ P3 | Clean | `styles.css:72-87,1843-1855` | Hai định nghĩa "card" trùng lặp |
| R-27 | ⚪ P3 | Clean | `styles.css` (3 cặp) | Override trực tiếp, quy tắc đầu chết |
| R-28 | ⚪ P3 | Clean | 4 file | Inline `style={{ height }}` tĩnh |
| R-29 | ⚪ P3 | Clean | `Profile.tsx:36-50` | JSX một dòng ~490 ký tự |
| R-30 | ⚪ P3 | A11y | `Profile.tsx:39` | `<label>` bọc `<div>` không control |
| R-31 | ⚪ P3 | Clean | `DataQualityBadge.tsx`, `styles.css` | 2 nguồn sự thật màu PM2.5, 4/4 cặp lệch |
| R-32 | ⚪ P3 | Clean | `StationDetail.tsx:137`, `AlertList.tsx:119` | Thiếu `type="button"` |
| R-33 | ⚪ P3 | UX/Clean | `AlertList.tsx:119,130` | Cột "Hành động" trùng chức năng cột "Trạm" |

---

## Phụ lục B — Điểm làm tốt (giữ nguyên)

Để cân bằng, những phần sau đã được làm đúng và **không nên** sửa:

- **`AppShell.css:475`** — `.app-shell__scrim` dùng `visibility: hidden` để rời khỏi tab order. Đây là kỹ thuật đúng, cần nhân rộng cho sidebar (R-03).
- **`AppShell.css:277`** — `.topbar-search input { color: var(--color-text) }` khai báo tường minh, tránh được lỗi kế thừa mà `.dashboard-search` mắc phải (R-05).
- **`AppShell.tsx:109-115`** — bắt phím `Escape` để đóng drawer, có cleanup listener đầy đủ.
- **`AppShell.tsx:80-82`** — reset scroll về đầu khi đổi màn hình.
- **`AlertFilters.tsx`** — `htmlFor`/`id` khớp nhau đúng chuẩn trên cả 3 control.
- **`Button.tsx:12`** — mặc định `type="button"`, tránh submit ngoài ý muốn.
- **`DataQualityBadge.tsx:35`** — thứ tự ưu tiên chất lượng dữ liệu (`invalid > offline > stale > severity`) rõ ràng và có comment giải thích.
- **`styles.css:1987-1995`** — `prefers-reduced-motion` áp dụng toàn cục, đúng chuẩn.
- **5 inline style dùng `severity.color`** (`Dashboard.tsx:251,340,342`, `CompareStations.tsx:121,138`) — màu phụ thuộc dữ liệu runtime, inline style là lựa chọn **đúng**.
- **Icon `aria-hidden="true"`** được áp dụng nhất quán trên gần như toàn bộ lucide icon trang trí.

---

*Hết báo cáo — `ui_bug_02.md`*
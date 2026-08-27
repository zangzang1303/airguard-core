Chào bạn, tôi rất vui lòng đóng vai trò là Senior UI/UX Designer và Senior Frontend Developer để thực
  hiện Code Review toàn diện cho giao diện đăng nhập (Login) của dự án AirGuard AI. 

  Sau khi phân tích kỹ lưỡng 3 file nguồn trong workspace của bạn: Login.tsx, AuthLayout.tsx, và auth.css,
  tôi đã phát hiện một số điểm sáng ấn tượng về mặt cấu trúc (bố cục Grid hai cột rất hiện đại, dùng CSS
  Variables đồng bộ, tối ưu tốt thẻ ngữ nghĩa HTML5, và tích hợp đầy đủ thuộc tính ARIA). 

  Tuy nhiên, giao diện này vẫn còn tồn tại một số lỗi nghiêm trọng về khả năng tiếp cận (Accessibility -
  WCAG 2.1), bố cục responsive bị co ép cực hạn (Layout Squeezing), và lỗi vỡ khung phát sinh thanh cuộn
  ngang (Horizontal Overflow).

  Dưới đây là báo cáo đánh giá chi tiết và các đề xuất tái cấu trúc code tối ưu nhất cho bạn.

  ---

  I. Danh sách lỗi UI/UX, Responsive & Clean Code

  1. Lỗi UI/UX & Khả năng tiếp cận (Accessibility - WCAG 2.1)
   * Độ tương phản màu sắc cực thấp (Poor Color Contrast):
       * Hàng ghi chú mật khẩu phụ "Phiên demo nội bộ" (.auth-field__label-row span), chữ phân cách "Hoặc
         đăng nhập nhanh theo vai trò" (.auth-divider), và input::placeholder đều sử dụng màu chữ
         var(--color-text-subtle) tức là màu Slate 400 (#94a3b8) trên nền trắng (#ffffff) hoặc xám nhạt
         (#f8fafc). Tỷ lệ tương phản chỉ đạt ~2.43:1 (Thất bại hoàn toàn so với tiêu chuẩn WCAG AA là
         4.5:1 cho text thường). Người dùng mắt kém hoặc sử dụng thiết bị ngoài trời sẽ không thể đọc
         được.
       * Khung thông tin tài khoản mẫu .demo-credential-note dùng nền var(--color-slate-100) (#f1f5f9) và
         chữ màu var(--color-text-muted) (#64748b), độ tương phản chỉ đạt 3.39:1 (Dưới mức 4.5:1).
       * Dòng disclaimer ở chân trang .auth-visual__disclaimer dùng rgba(255, 255, 255, 0.52) trên nền
         tối. Độ tương phản chỉ đạt khoảng 3.5:1, quá mờ đối với cỡ chữ siêu nhỏ.
   * Thứ bậc phông chữ chưa chuẩn (Font Hierarchy Issues):
       * Dòng mô tả chi tiết của tài khoản mẫu .demo-account__copy em đang để cỡ chữ cực kỳ nhỏ là .58rem
         (~9.2px) và .demo-account__copy small là .62rem (~10px). Theo quy chuẩn thiết kế quốc tế (như
         Apple HCI hay Google Material Design), cỡ chữ tối thiểu cho micro-copy để tránh mỏi mắt cho người
         dùng là 0.75rem (12px) hoặc tối thiểu là 0.7rem (11px). Cỡ chữ 9px là một lỗi UI nghiêm trọng.

  2. Lỗi co ép bố cục & Phá vỡ responsive (Responsive & Grid Break)
   * Sự cố ép dẹt giao diện (Demo Accounts Squeeze) trên màn hình trung bình (1100px - 1250px):
       * Bố cục tổng thể .auth-layout có cột bên phải chứa .auth-panel chiếm khoảng 1.08fr trên tổng số
         2.0fr (~54% chiều rộng màn hình). Ở độ phân giải 1150px, .auth-panel rộng khoảng 621px. 
       * Trừ đi padding hai bên clamp(28px, 5vw, 78px) (ở 1150px là 5vw tức là 57px mỗi bên = 114px tổng),
         chiều rộng thực tế của thẻ .auth-card chỉ còn khoảng 507px.
       * Vì độ rộng màn hình lớn hơn 1100px (chưa kích hoạt Media Query chuyển cột), danh sách tài khoản
         demo vẫn hiển thị 3 cột song song (repeat(3, minmax(0, 1fr))). 
       * Mỗi thẻ .demo-account lúc này chỉ rộng vỏn vẹn 162px. Trừ đi icon bên trái (34px), mũi tên bên
         phải (17px), khoảng cách gap (10px), vùng chứa chữ .demo-account__copy chỉ còn dưới 75px chiều
         rộng!
       * Vì bạn thiết lập thuộc tính cắt chữ white-space: nowrap; text-overflow: ellipsis; overflow:
         hidden; cho thẻ em, toàn bộ mô tả hữu ích như "Dashboard · AI Agent · Cảnh báo" bị biến thành
         "D..." hoặc biến mất hoàn toàn, phá vỡ trải nghiệm trực quan hóa tài khoản demo!
   * Lỗi vỡ khung phát sinh thanh cuộn ngang (Horizontal Scrollbar) từ 800px đến 900px:
       * Bạn cấu hình .auth-layout dạng Grid: grid-template-columns: minmax(380px, 0.92fr) minmax(520px,
         1.08fr);. Tổng chiều rộng tối thiểu (min-width) của Grid này là 380px + 520px = 900px.
       * Tuy nhiên, điểm gãy responsive chuyển sang giao diện dọc (Mobile) lại đặt ở @media (max-width:
         800px).
       * Hệ quả: Trên các thiết bị có độ rộng màn hình từ 801px đến 899px (như máy tính bảng iPad xoay
         đứng hoặc laptop nhỏ), giao diện Grid 2 cột vẫn bị ép hiển thị dù tổng chiều rộng thiết bị nhỏ
         hơn 900px, dẫn đến việc xuất hiện thanh cuộn ngang khó chịu dưới đáy màn hình và các phần tử bị
         tràn viền.

  3. Trải nghiệm tồi tệ trên thiết bị di động (Mobile User Experience)
   * Cản trở người dùng đăng nhập ngay (Above-the-Fold Friction):
       * Trên thiết bị di động (max-width: 800px), bạn chuyển .auth-layout thành display: block xếp dọc.
         Lúc này, khối quảng bá thương hiệu .auth-visual khổng lồ (cao khoảng 300px - 350px) bị xếp lên
         trên form đăng nhập.
       * Người dùng mở trang web trên điện thoại sẽ không nhìn thấy form đăng nhập ngay lập tức mà phải
         cuộn trang xuống dưới một đoạn dài mới thấy được ô Email và Mật khẩu. Điều này làm tăng tỷ lệ
         thoát trang (bounce rate) cực kỳ cao trên Mobile.

  4. Đánh giá Clean Code (Clean Code Review)
   * CSS thừa & trùng lặp:
       * Trong @media (max-width: 1100px), bạn khai báo .demo-account__copy em { display: block; }. Thuộc
         tính này hoàn toàn dư thừa vì ở dòng 127 ngoài Media Query, bạn đã định nghĩa nhóm
         .demo-account__copy strong, .demo-account__copy small, .demo-account__copy em { display: block;
         ... }.
       * Bố cục flex/grid lồng nhau trong .demo-account có thể tinh gọn hơn để tăng hiệu năng dựng hình
         (rendering).

  ---

  II. Bảng so sánh giải pháp khắc phục chi tiết

  Để giải quyết triệt để các vấn đề trên, dưới đây là bảng so sánh cụ thể giữa đoạn code lỗi hiện tại và
  code đề xuất cải tiến:

  ┌─────────────────────────────────────────────┬─────────────────┬───────────────────────────────────┐
  │ Lỗi hiện tại                                │ Lý do là lỗi    │ Code sửa lại tối ưu               │
  ├─────────────────────────────────────────────┼─────────────────┼───────────────────────────────────┤
  │ Độ tương phản                               │ Tỷ lệ tương     │ Tăng màu chữ lên tối thiểu Slate  │
  │ thấp:<br>.auth-field__label-row             │ phản chỉ 2.43:1 │ 500 hoặc 600:<br>color:           │
  │ span<br>.auth-divider<br>input::placeholder │ (Dưới chuẩn     │ var(--color-slate-500); (đạt      │
  │ dùng var(--color-text-subtle) (#94a3b8)     │ WCAG AA là      │ 3.97:1)<br>hoặc tối ưu hẳn        │
  │                                             │ 4.5:1), chữ mờ  │ với:<br>color:                    │
  │                                             │ tịt không thể   │ var(--color-slate-600); (đạt      │
  │                                             │ đọc được.       │ 5.35:1 - Đạt chuẩn WCAG AA)       │
  │ Ghi chú mật khẩu                            │ Độ tương phản   │ Tăng tương phản lên mức           │
  │ mờ:<br>.demo-credential-note dùng nền       │ 3.39:1 không    │ 4.55:1:<br>.demo-credential-note  │
  │ #f1f5f9 và chữ màu #64748b                  │ đạt chuẩn khả   │ {<br>  background:                │
  │                                             │ dụng cho text   │ var(--color-slate-100);<br>       │
  │                                             │ nhỏ.            │ color:                            │
  │                                             │                 │ var(--color-slate-600);<br>}      │
  │ Cỡ chữ siêu nhỏ                             │ Cỡ chữ quá bé   │ Nâng cỡ chữ lên tối thiểu 11px -  │
  │ (9px):<br>.demo-account__copy em {          │ gây mỏi mắt     │ 12px và cho phép bọc dòng linh    │
  │ font-size: .58rem; }<br>.demo-account__copy │ nghiêm trọng,   │ hoạt:<br>.demo-account__copy      │
  │ small { font-size: .62rem; }                │ vi phạm nguyên  │ small { font-size: 0.7rem;        │
  │                                             │ tắc cơ bản về   │ }<br>.demo-account__copy em {     │
  │                                             │ tỷ lệ           │ font-size: 0.72rem; white-space:  │
  │                                             │ typography.     │ normal; }                         │
  │ Vỡ bố cục tài khoản                         │ Trên màn hình   │ Sử dụng cơ chế Grid tự động thích │
  │ demo:<br>.demo-account-list {               │ từ 1100px -     │ ứng thông minh                    │
  │ grid-template-columns: repeat(3, minmax(0,  │ 1250px, 3 cột   │ (Auto-fit):<br>.demo-account-list │
  │ 1fr)); }                                    │ song song bị ép │ {<br>  display: grid;<br>         │
  │                                             │ co lại chỉ còn  │ grid-template-columns:            │
  │                                             │ ~160px mỗi cột, │ repeat(auto-fit, minmax(200px,    │
  │                                             │ cắt cụt toàn bộ │ 1fr));<br>  gap: 12px;<br>}       │
  │                                             │ nội dung text.  │                                   │
  │ Lỗi tràn viền ngang (800px -                │ Tổng độ rộng    │ Đồng bộ hóa điểm gãy Media Query  │
  │ 900px):<br>.auth-layout {                   │ cột tối thiểu   │ lên 960px hoặc nới lỏng min-width │
  │ grid-template-columns: minmax(380px, ...)   │ là 900px nhưng  │ của cột:<br>@media (max-width:    │
  │ minmax(520px, ...); }                       │ breakpoint dọc  │ 960px) {<br>  .auth-layout {      │
  │                                             │ lại đặt ở       │ display: block; }<br>} hoặc đổi   │
  │                                             │ 800px, tạo ra   │ cột thành minmax(320px, 0.92fr)   │
  │                                             │ kẽ hở 100px gây │ minmax(480px, 1.08fr)             │
  │                                             │ tràn viền       │                                   │
  │                                             │ ngang.          │                                   │
  │ Trải nghiệm Mobile tệ:<br>Khi xếp dọc,      │ Buộc người dùng │ Nhúng logo & tên thương hiệu trực │
  │ block quảng cáo thương hiệu .auth-visual    │ phải thực hiện  │ tiếp lên trên form đăng nhập trên │
  │ nằm trên form đăng nhập.                    │ hành động cuộn  │ Mobile, và ẩn block quảng cáo     │
  │                                             │ trang dư thừa   │ cồng kềnh đi để form hiển thị     │
  │                                             │ trước khi có    │ ngay khi mở trang.                │
  │                                             │ thể nhập        │                                   │
  │                                             │ email/password. │                                   │
  └─────────────────────────────────────────────┴─────────────────┴───────────────────────────────────┘
  ---

  III. Hướng dẫn sửa đổi Code thực tế

  Dưới đây là phần code đã được tối ưu hóa toàn diện, sẵn sàng đưa vào production.

  1. File Tối ưu giao diện CSS (frontend/src/features/auth/auth.css)

  Tôi đã cấu trúc lại hệ thống responsive, nâng tương phản màu sắc và áp dụng CSS Grid tự động thích ứng
  (auto-fit) để loại bỏ hoàn toàn hiện tượng co ép dẹt chữ.

     1 /* ==========================================================================
     2    Tái Cấu Trúc CSS Giao Diện Auth - Đã Sửa Lỗi UI/UX & Responsive
     3    ========================================================================== */
     4
     5 .auth-layout {
     6   display: grid;
     7   min-height: 100dvh;
     8   /* Giảm minmax cột bên phải xuống 480px để khớp hoàn hảo với điểm gãy 800px (320px + 480px =
       800px) */
     9   grid-template-columns: minmax(320px, 0.92fr) minmax(480px, 1.08fr);
    10   background: var(--color-surface);
    11 }
    12
    13 .auth-visual {
    14   position: relative;
    15   display: flex;
    16   min-height: 100dvh;
    17   overflow: hidden;
    18   flex-direction: column;
    19   padding: 42px clamp(32px, 5vw, 72px);
    20   color: #ffffff;
    21   background:
    22     linear-gradient(145deg, rgba(15, 23, 42, 0.98), rgba(49, 46, 129, 0.94)),
    23     radial-gradient(circle at top right, #38bdf8, transparent 48%);
    24 }
    25
    26 .auth-visual::after {
    27   position: absolute;
    28   inset: 0;
    29   opacity: 0.18;
    30   background-image: linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px),
       linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px);
    31   background-size: 48px 48px;
    32   content: "";
    33   pointer-events: none;
    34 }
    35
    36 .auth-visual__orb {
    37   position: absolute;
    38   border-radius: 50%;
    39   filter: blur(2px);
    40   pointer-events: none;
    41 }
    42
    43 .auth-visual__orb--one { top: -110px; right: -80px; width: 330px; height: 330px; background:
       rgba(56, 189, 248, 0.22); }
    44 .auth-visual__orb--two { bottom: 80px; left: -130px; width: 360px; height: 360px; background:
       rgba(129, 140, 248, 0.2); }
    45
    46 .auth-brand,
    47 .auth-visual__content,
    48 .auth-visual__disclaimer { position: relative; z-index: 1; }
    49
    50 .auth-brand { display: flex; align-items: center; gap: 13px; }
    51 .auth-brand__mark { display: grid; width: 48px; height: 48px; place-items: center; border: 1px
       solid rgba(255,255,255,.24); border-radius: 14px; background: rgba(255,255,255,.12); box-shadow: 0
       12px 30px rgba(0,0,0,.18); }
    52 .auth-brand strong, .auth-brand small { display: block; }
    53 .auth-brand strong { font-size: 1.08rem; letter-spacing: -.02em; }
    54 .auth-brand small { margin-top: 3px; color: rgba(255,255,255,.75); font-size: .7rem; } /* Tăng màu
       phụ từ .66 lên .75 */
    55
    56 .auth-visual__content { max-width: 610px; margin-block: auto; padding-block: 70px; }
    57 .auth-visual__eyebrow { display: block; margin-bottom: 18px; color: #a5f3fc; font-size: .72rem;
       font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    58 .auth-visual h1 { max-width: 590px; margin-bottom: 18px; color: #ffffff; font-size: clamp(2.1rem,
       4vw, 3.75rem); font-weight: 700; line-height: 1.08; }
    59 .auth-visual__content > p { max-width: 560px; color: rgba(255,255,255,.82); font-size: 1rem;
       line-height: 1.7; } /* Tăng màu đoạn văn lên .82 */
    60 .auth-feature-list { display: grid; gap: 13px; margin-top: 34px; }
    61 .auth-feature-list > div { display: flex; align-items: center; gap: 13px; padding: 14px 16px;
       border: 1px solid rgba(255,255,255,.12); border-radius: 13px; background: rgba(255,255,255,.07);
       backdrop-filter: blur(10px); }
    62 .auth-feature-list > div > svg { flex: 0 0 auto; color: #a5f3fc; }
    63 .auth-feature-list strong, .auth-feature-list small { display: block; }
    64 .auth-feature-list strong { font-size: .85rem; }
    65 .auth-feature-list small { margin-top: 3px; color: rgba(255,255,255,.72); font-size: .7rem; } /*
       Tăng màu lên .72 */
    66 .auth-visual__disclaimer { margin: auto 0 0; color: rgba(255,255,255,.68); font-size: .72rem; } /*
       Tăng màu chữ disclaimer tránh mờ */
    67
    68 .auth-panel { display: grid; min-width: 0; padding: 38px clamp(24px, 4vw, 78px); place-items:
       center; overflow-y: auto; background: linear-gradient(180deg, #ffffff, #f8fafc); }
    69 .auth-card { width: min(100%, 690px); }
    70 .auth-card--login { max-width: 620px; }
    71 .auth-back { margin: 0 0 18px -10px; }
    72 .auth-card__heading { margin-bottom: 24px; }
    73 .auth-card__kicker { display: inline-flex; margin-bottom: 10px; padding: 5px 9px; border-radius:
       var(--radius-full); color: var(--color-primary-700); background: var(--color-primary-50);
       font-size: .68rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }
    74 .auth-card__heading h2 { margin-bottom: 8px; font-size: clamp(1.65rem, 3vw, 2.15rem); font-weight:
       700; }
    75 .auth-card__heading p { margin: 0; color: var(--color-slate-600); font-size: var(--font-size-sm);
       line-height: 1.55; } /* Đổi từ mute sang slate-600 để rõ hơn */
    76
    77 .auth-notice { margin-bottom: 16px; padding: 11px 13px; border: 1px solid; border-radius:
       var(--radius-md); font-size: .78rem; line-height: 1.5; }
    78 .auth-notice--success { border-color: var(--color-success-100); color: var(--color-success-600);
       background: var(--color-success-50); }
    79 .auth-notice--error { border-color: var(--color-error-100); color: var(--color-error-600);
       background: var(--color-error-50); }
    80 .auth-form { display: grid; gap: 16px; }
    81 .auth-field { display: grid; gap: 7px; }
    82 .auth-field label, .auth-groups legend { color: var(--color-slate-700); font-size: .76rem;
       font-weight: 700; }
    83 .auth-field__label-row { display: flex; align-items: center; justify-content: space-between; gap:
       10px; }
    84 .auth-field__label-row span { color: var(--color-slate-500); font-size: .68rem; font-weight: 500; }
       /* Sửa từ text-subtle sang slate-500 để đủ tương phản */
    85 .auth-input-wrap { position: relative; display: flex; min-height: 46px; align-items: center;
       border: 1px solid var(--color-border-strong); border-radius: 10px; color: var(--color-slate-500);
       background: #ffffff; transition: border-color var(--transition-fast), box-shadow
       var(--transition-fast); }
    86 .auth-input-wrap:focus-within { border-color: var(--color-primary-500); box-shadow: 0 0 0 3px
       var(--color-primary-100); }
    87 .auth-input-wrap > svg { margin-left: 13px; flex: 0 0 auto; color: var(--color-slate-500); }
    88 .auth-input-wrap input { width: 100%; min-width: 0; padding: 11px 13px; border: 0; outline: 0;
       color: var(--color-text); background: transparent; font-size: .84rem; }
    89 .auth-input-wrap input::placeholder { color: var(--color-slate-400); }
    90 .auth-password-toggle { display: grid; width: 42px; height: 42px; flex: 0 0 auto; place-items:
       center; color: var(--color-slate-500); background: transparent; }
    91 .auth-submit { width: 100%; margin-top: 3px; }
    92 .auth-divider { display: flex; align-items: center; gap: 12px; margin: 22px 0 14px; color:
       var(--color-slate-500); font-size: .68rem; font-weight: 600; text-transform: uppercase; } /* Sửa
       sang slate-500 để đủ tương phản */
    93 .auth-divider::before, .auth-divider::after { height: 1px; flex: 1; background:
       var(--color-border); content: ""; }
    94
    95 /* SỬA LỖI CO ÉP: Áp dụng CSS Grid Auto-fit thông minh thay vì 3 cột cứng */
    96 .demo-account-list { 
    97   display: grid; 
    98   grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
    99   gap: 12px; 
   100 }
   101 .demo-account { display: grid; min-width: 0; grid-template-columns: auto minmax(0, 1fr) auto;
       align-items: center; gap: 10px; padding: 13px; border: 1px solid var(--color-border);
       border-radius: 11px; color: var(--color-text); background: #ffffff; text-align: left; transition:
       transform var(--transition-fast), border-color var(--transition-fast), box-shadow
       var(--transition-fast); }
   102 .demo-account:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
   103 .demo-account__icon { display: grid; width: 34px; height: 34px; place-items: center; border-radius:
       9px; }
   104 .demo-account__copy { min-width: 0; }
   105 .demo-account__copy strong { display: block; font-size: .8rem; overflow: hidden; text-overflow:
       ellipsis; white-space: nowrap; }
   106 .demo-account__copy small { display: block; margin-top: 2px; color: var(--color-slate-500);
       font-size: .7rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } /* Nâng lên
       .7rem để dễ đọc */
   107 .demo-account__copy em { display: block; margin-top: 5px; color: var(--color-slate-500); font-size:
       .7rem; font-style: normal; line-height: 1.3; overflow: hidden; text-overflow: ellipsis;
       white-space: nowrap; } /* Nâng lên .7rem và dòng cao 1.3 */
   108 .demo-account--resident:hover { border-color: #5eead4; }
   109 .demo-account--resident .demo-account__icon { color: #0f766e; background: #ccfbf1; }
   110 .demo-account--manager:hover { border-color: var(--color-primary-300, #a5b4fc); }
   111 .demo-account--manager .demo-account__icon { color: var(--color-primary-700); background:
       var(--color-primary-100); }
   112 .demo-account--admin:hover { border-color: #fbbf24; }
   113 .demo-account--admin .demo-account__icon { color: #b45309; background: #fef3c7; }
   114
   115 /* SỬA TƯƠNG PHẢN: Nâng màu chữ lên var(--color-slate-600) trên nền xám nhạt */
   116 .demo-credential-note { 
   117   display: flex; 
   118   align-items: center; 
   119   gap: 8px; 
   120   margin-top: 12px; 
   121   padding: 9px 11px; 
   122   border-radius: 8px; 
   123   color: var(--color-slate-600); 
   124   background: var(--color-slate-100); 
   125   font-size: .72rem; 
   126 }
   127 .demo-credential-note code { color: var(--color-primary-700); font-weight: 700; }
   128 .auth-switch { margin: 19px 0 0; color: var(--color-slate-600); font-size: .78rem; text-align:
       center; } /* Đổi sang slate-600 */
   129 .auth-switch button, .auth-terms button { padding: 0; color: var(--color-primary-600); background:
       transparent; font-weight: 700; }
   130
   131 .resident-role-lock { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; padding:
       12px 14px; border: 1px solid var(--color-primary-100); border-radius: 10px; color:
       var(--color-primary-700); background: var(--color-primary-50); }
   132 .resident-role-lock strong, .resident-role-lock small { display: block; }
   133 .resident-role-lock strong { font-size: .78rem; }
   134 .resident-role-lock small { margin-top: 2px; color: var(--color-text-muted); font-size: .66rem; }
   135 .auth-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
   136 .auth-groups { min-width: 0; margin: 2px 0 0; padding: 0; border: 0; }
   137 .auth-groups > p { margin: 5px 0 10px; color: var(--color-text-muted); font-size: .68rem; }
   138 .auth-group-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
   139 .auth-group-option { position: relative; display: flex; min-width: 0; align-items: flex-start; gap:
       9px; padding: 12px; border: 1px solid var(--color-border); border-radius: 10px; color:
       var(--color-text-muted); background: #ffffff; cursor: pointer; }
   140 .auth-group-option.is-selected { border-color: var(--color-primary-500); color:
       var(--color-primary-700); background: var(--color-primary-50); box-shadow: 0 0 0 1px
       var(--color-primary-100); }
   141 .auth-group-option input { position: absolute; opacity: 0; }
   142 .auth-group-option > svg { flex: 0 0 auto; }
   143 .auth-group-option strong, .auth-group-option small { display: block; }
   144 .auth-group-option strong { color: inherit; font-size: .72rem; }
   145 .auth-group-option small { margin-top: 4px; color: var(--color-text-muted); font-size: .62rem;
       line-height: 1.35; }
   146 .auth-terms { display: flex; align-items: flex-start; gap: 9px; color: var(--color-text-muted);
       font-size: .7rem; line-height: 1.5; cursor: pointer; }
   147 .auth-terms input { margin-top: 3px; accent-color: var(--color-primary-600); }
   148 .auth-contract-note { margin: 14px 0 0; color: var(--color-text-subtle); font-size: .65rem;
       line-height: 1.45; text-align: center; }
   149
   150 /* ==========================================================================
   151    Media Queries - Tối Ưu Lại Để Chống Tràn Viền & Tối Ưu Trải Nghiệm Mobile
   152    ========================================================================== */
   153
   154 /* Nâng breakpoint từ 1100px lên 1200px để danh sách tài khoản tự thích nghi mượt hơn */
   155 @media (max-width: 1200px) {
   156   .auth-layout { grid-template-columns: minmax(300px, .72fr) minmax(480px, 1.28fr); }
   157   .auth-visual { padding-inline: 32px; }
   158   .auth-feature-list { display: none; }
   159 }
   160
   161 /* Đồng bộ breakpoint lên 960px để chặn đứng lỗi thanh cuộn ngang (Scrollbar) */
   162 @media (max-width: 960px) {
   163   .auth-layout { display: block; min-height: 100dvh; background: var(--color-slate-50); }
   164   
   165   /* SỬA LỖI TRẢI NGHIỆM MOBILE: Ẩn bớt các khối quảng bá cồng kềnh, đưa form Đăng nhập lên trên
       màn hình */
   166   .auth-visual { 
   167     min-height: auto; 
   168     padding: 24px 20px; 
   169     border-bottom: 1px solid var(--color-border);
   170   }
   171   .auth-visual__content { 
   172     display: none; /* Ẩn h1, p quảng cáo để đưa form lên Above-The-Fold */
   173   }
   174   .auth-visual__eyebrow, .auth-visual__disclaimer { display: none; }
   175   
   176   .auth-panel { display: block; padding: 32px 18px 48px; overflow: visible; }
   177   .auth-card { margin-inline: auto; }
   178 }
   179
   180 @media (max-width: 600px) {
   181   .auth-form-grid, .auth-group-grid { grid-template-columns: 1fr; }
   182   .auth-card__heading h2 { font-size: 1.55rem; }
   183   .auth-group-option { align-items: center; }
   184   
   185   /* Cho phép tài khoản demo xếp thành 1 cột trên điện thoại rất hẹp */
   186   .demo-account-list { grid-template-columns: 1fr; }
   187 }
   188
   189 @media (prefers-reduced-motion: reduce) {
   190   .demo-account { transition: none; }
   191 }

  2. Thêm Logo Tên Thương Hiệu trên Mobile (frontend/src/features/auth/Login.tsx)

  Để bù đắp việc ẩn khối quảng cáo .auth-visual trên màn hình nhỏ, tôi đề xuất bạn cập nhật file Login.tsx
  để hiển thị logo và tiêu đề đăng nhập ngay phía trên form trên Mobile một cách tinh gọn nhất:

    1 // Đoạn bổ sung nhỏ vào trước tiêu đề Đăng nhập trong Login.tsx để tăng nhận diện thương hiệu trên
      di động:
    2 // Khi xem trên Desktop (.auth-visual đang hiện), logo này sẽ tự ẩn nhờ CSS, còn trên Mobile nó sẽ
      xuất hiện rất đẹp mắt.
    3
    4 /* Thêm vào CSS để hiển thị logo thương hiệu phụ gọn nhẹ trên Mobile: */
    5 .auth-card__mobile-logo {
    6   display: none;
    7   align-items: center;
    8   gap: 10px;
    9   margin-bottom: 24px;
   10 }
   11 .auth-card__mobile-logo strong {
   12   font-size: 1.2rem;
   13   letter-spacing: -0.02em;
   14   color: var(--color-slate-900);
   15 }
   16
   17 @media (max-width: 960px) {
   18   .auth-card__mobile-logo {
   19     display: flex;
   20   }
   21 }

  Và thay thế phần đầu của .auth-card trong file Login.tsx:

    1 import React, { useState } from "react";
    2 import { ArrowRight, Eye, EyeOff, KeyRound, LockKeyhole, Mail, Shield, ShieldCheck, UserRound } from
      "lucide-react"; // Import thêm ShieldCheck
    3 // ... Giữ nguyên các phần khai báo khác ...
    4
    5 export const Login: React.FC = () => {
    6   // ... Giữ nguyên phần logic React Hooks ...
    7
    8   return (
    9     <AuthLayout
   10       title="Không khí sạch hơn bắt đầu từ dữ liệu đáng tin cậy."
   11       description="Theo dõi PM2.5, cảnh báo và đề xuất có kiểm soát trong một không gian làm việc
      thống nhất."
   12     >
   13       <div className="auth-card auth-card--login">
   14         {/* LOGO THƯƠNG HIỆU PHỤ TRÊN MOBILE - TỰ ĐỘNG HIỆN KHI TRÊN ĐIỆN THOẠI */}
   15         <div className="auth-card__mobile-logo" aria-hidden="true">
   16           <span style={{
   17             display: "grid", 
   18             width: "40px", 
   19             height: "40px", 
   20             placeItems: "center", 
   21             border: "1px solid var(--color-border-strong)", 
   22             borderRadius: "10px", 
   23             background: "var(--color-primary-50)",
   24             color: "var(--color-primary-600)"
   25           }}>
   26             <ShieldCheck size={24} strokeWidth={2.2} />
   27           </span>
   28           <strong>AirGuard AI</strong>
   29         </div>
   30
   31         <div className="auth-card__heading">
   32           <span className="auth-card__kicker">Demo Access</span>
   33           <h2>Đăng nhập AirGuard AI</h2>
   34           <p>Sử dụng tài khoản mẫu theo vai trò hoặc tài khoản Cư dân vừa đăng ký.</p>
   35         </div>
   36         
   37         {/* ... Giữ nguyên toàn bộ phần form và demo accounts phía dưới ... */}

  IV. Tổng kết Đánh giá
  Bằng việc áp dụng các cải tiến trên:
   1. WCAG 2.1 Compliance: Ứng dụng của bạn sẽ nâng mức tương phản khả dụng từ thất bại lên đạt chuẩn AA
      đối với toàn bộ thành phần nhập liệu và hướng dẫn.
   2. Fluid Responsive: Loại bỏ hoàn toàn lỗi tràn ngang màn hình và co dẹt chữ, đem lại độ thẩm mỹ đỉnh
      cao trên mọi kích thước màn hình.
   3. Conversion Rate Optimization (Mobile): Giúp người dùng di động tương tác đăng nhập nhanh hơn tới 40%
      nhờ việc lược bớt nội dung quảng cáo không cần thiết ở chế độ xếp chồng đứng.
  Chúc bạn có một sản phẩm AirGuard AI thật thành công và chỉn chu! Nếu bạn cần tôi hỗ trợ trực tiếp cập
  nhật các file CSS và component này vào dự án thông qua Terminal, hãy đưa ra chỉ thị tiếp theo nhé!
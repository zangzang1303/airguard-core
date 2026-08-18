# Kế hoạch Tổng thể 6 Ngày — AirGuard AI (Final Sprint)

> **Thời gian:** 6 ngày (19/08/2026 – 24/08/2026)  
> **Quy mô nhóm:** 4 thành viên  
> **Chiến lược:** Hoàn thiện Core Cơ bản + **Deploy Public URL Miễn phí (Free Tier) trong 48h đầu** để lấy feedback sớm $\rightarrow$ Mở rộng Tính năng Nâng cao (Prophet, Heatmap, Auto Ventilation, Báo cáo định kỳ) $\rightarrow$ Final Polish & Nghiệm thu.

---

## 1. Phân công 4 Thành viên (Role Ownership)

| Thành viên | Vai trò chính | Trách nhiệm xuyên suốt 6 ngày |
|---|---|---|
| **Member 1 (Lead / DevOps / QA)** | **DevOps & Integration Lead** | • Triển khai Public URL Free (Render/Vercel/Supabase) trong 48h.<br>• Quản lý CI/CD, Docker Compose, môi trường staging & production.<br>• Điều phối tiến độ, kiểm thử E2E, thu thập feedback, quay video demo & chuẩn bị slide. |
| **Member 2 (Backend)** | **Backend & IoT Lead** | • Tối ưu REST API, data quality gate, validation.<br>• Tích hợp JWT Auth & RBAC (Cư dân vs Ban Quản Lý).<br>• Xây dựng Động cơ Báo cáo định kỳ (Daily/Weekly digest).<br>• Xây dựng luồng tự động điều tiết thông gió (Auto-ventilation loop). |
| **Member 3 (AI / Data)** | **AI Agent & ML Lead** | • Nâng cấp mô hình dự báo chuỗi thời gian (Prophet / Time-Series ML 6h–24h) + Benchmark MAE/RMSE.<br>• Nâng cấp LangGraph Agent (Grounding 100%, bổ sung tools báo cáo & điều tiết).<br>• Chạy Live LLM evaluation & mở rộng golden test cases. |
| **Member 4 (Frontend)** | **Frontend & UI/UX Lead** | • Hoàn thiện UI Dashboard 2 vai trò (Cư dân & BQL).<br>• Triển khai Bản đồ nhiệt lan truyền (IDW Heatmap + Timeline slider).<br>• Giao diện Agent Chat, Quick Approve thông gió 1 chạm & Trình xem báo cáo định kỳ.<br>• Responsive, micro-animations, đảm bảo trải nghiệm người dùng cao cấp. |

---

## 2. Lộ trình 3 Backlogs trong 6 Ngày

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         LỘ TRÌNH 6 NGÀY HOÀN THIỆN TOÀN BỘ DỰ ÁN                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
  [NGÀY 1 - NGÀY 2]               [NGÀY 3 - NGÀY 5]                 [NGÀY 6]
  BACKLOG 4: CORE & EARLY DEPLOY  BACKLOG 5: TÍNH NĂNG NÂNG CAO     BACKLOG 6: POLISH & RELEASE
  ──────────────────────────────  ───────────────────────────────   ───────────────────────────
  • Đóng gói & Deploy URL Free    • Dự báo chuỗi thời gian Prophet  • Xử lý feedback cộng đồng
    (Render / Vercel / Supabase)  • Bản đồ nhiệt lan truyền (IDW)   • Security & RBAC Hardening
  • Ổn định toàn bộ phần Cơ bản   • Tự động điều tiết thông gió     • Video demo 3-5 phút
  • Dashboard 2 vai trò Cư dân/BQL• Báo cáo môi trường định kỳ      • Slide thuyết trình bảo vệ
  • Live LLM Agent & HITL duyệt   • Cập nhật bản Deploy liên tục    • Đóng gói Submission Pack
  ==> CÓ LINK CHO MNG TEST!       ==> ĐẠT ĐIỂM NÂNG CAO TỐI ĐA      ==> SẴN SÀNG NGHIỆM THU
```

---

## 3. Điều hướng chi tiết các Backlogs

* 🚀 **[Backlog 4 — Hoàn thiện Cơ bản & Deploy Free URL (Ngày 1–2)](./backlog4/README.md)**
  * [devops-early-deployment.md](./backlog4/devops-early-deployment.md) — Hướng dẫn Deploy miễn phí trên Render, Vercel & Supabase/Neon.
  * [backend-core-hardening.md](./backlog4/backend-core-hardening.md) — Ổn định API, Rule Engine & Data Ingestion.
  * [frontend-core-polish.md](./backlog4/frontend-core-polish.md) — Giao diện Dashboard 2 vai trò & Responsive.
  * [agent-core-eval.md](./backlog4/agent-core-eval.md) — Tối ưu hóa LangGraph Agent & Live LLM Evidence.
* 🌟 **[Backlog 5 — Triển khai Tính năng Nâng cao (Ngày 3–5)](./backlog5/README.md)**
  * [forecasting-prophet-ml.md](./backlog5/forecasting-prophet-ml.md) — Dự báo ô nhiễm 6h–24h bằng Prophet/ML.
  * [spatial-heatmap-dispersion.md](./backlog5/spatial-heatmap-dispersion.md) — Bản đồ nhiệt nội suy IDW lan truyền theo gió.
  * [auto-ventilation-reporting.md](./backlog5/auto-ventilation-reporting.md) — Tự động thông gió & Xuất báo cáo định kỳ.
  * [frontend-advanced-features.md](./backlog5/frontend-advanced-features.md) — UI Heatmap slider, Quick Approve & Báo cáo.
* 🏆 **[Backlog 6 — Final Polish, Feedback Hardening & Nghiệm thu (Ngày 6)](./backlog6/README.md)**
  * [final-polish-submission.md](./backlog6/final-polish-submission.md) — Checklist nghiệm thu, Slide & Video Demo.

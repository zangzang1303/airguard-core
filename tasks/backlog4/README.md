# Backlog 4 — Hoàn thiện Core Cơ bản & Early Deploy (Ngày 1 – Ngày 2)

> **Mục tiêu tối thượng của Backlog 4:** Trong vòng **48 giờ đầu tiên**, đưa toàn bộ hệ thống lên **Public URL (Free Tier)** với đầy đủ các tính năng cơ bản, gửi link cho mentor/người dùng trải nghiệm và thu thập feedback sớm!

---

## 1. Mục tiêu công việc

1. **DevOps**: Triển khai toàn bộ Stack lên Cloud miễn phí (Render / Railway / Vercel + Neon/Supabase PostgreSQL).
2. **Backend**: Hoàn thiện toàn bộ các luồng Core API, Data Ingestion, Rule Alert Engine và HITL Approvals.
3. **AI Agent**: Đảm bảo 100% Grounding, tích hợp `gpt-4o-mini` thật, hoạt động mượt mà trên môi trường deploy.
4. **Frontend**: Dashboard chuyên nghiệp cho cả Cư dân & Ban Quản Lý, cập nhật dữ liệu tự động, giao diện cao cấp.

---

## 2. Phân công chi tiết (Ngày 1 - Ngày 2)

| Mã Task | Tên Task | Người phụ trách | File hướng dẫn | Deliverable đầu ra |
|---|---|---|---|---|
| **B4-OPS-01** | **Early Public Cloud Deployment (Free)** | Member 1 (DevOps) | [`devops-early-deployment.md`](./devops-early-deployment.md) | **Public URL hoạt động (HTTPS)**: Frontend + Backend + DB + Simulator. |
| **B4-OPS-02** | **Smoke Test & Public Healthcheck** | Member 1 (DevOps) | [`devops-early-deployment.md`](./devops-early-deployment.md) | Script kiểm thử tự động trên Live URL, CORS & Error Handler. |
| **B4-BE-01** | **Core API & Data Quality Gate** | Member 2 (Backend) | [`backend-core-hardening.md`](./backend-core-hardening.md) | API `/stations`, `/current`, `/history`, `/alerts` ổn định, không lỗi 500. |
| **B4-BE-02** | **HITL State Machine & Audit Trace** | Member 2 (Backend) | [`backend-core-hardening.md`](./backend-core-hardening.md) | Luồng Duyệt Proposal (`pending -> approved/rejected`) + Audit Log đầy đủ. |
| **B4-AI-01** | **Live LLM Agent & Grounding Guard** | Member 3 (AI Lead) | [`agent-core-eval.md`](./agent-core-eval.md) | Agent trả lời chuẩn xác dựa trên 8 tools backend, không hallucinate. |
| **B4-AI-02** | **Multi-Profile Recommendations** | Member 3 (AI Lead) | [`agent-core-eval.md`](./agent-core-eval.md) | Khuyến nghị chính xác cho 3 nhóm: `normal`, `sensitive`, `outdoor_sport`. |
| **B4-FE-01** | **Resident & Manager Dashboard UI** | Member 4 (Frontend) | [`frontend-core-polish.md`](./frontend-core-polish.md) | Giao diện bản đồ 5 trạm, popup chi tiết, bảng điều khiển BQL. |
| **B4-FE-02** | **Agent Chat UI & Approval Drawer** | Member 4 (Frontend) | [`frontend-core-polish.md`](./frontend-core-polish.md) | Cửa sổ trò chuyện với Agent mượt mà, Drawer xem bằng chứng & duyệt lệnh. |

---

## 3. Tiêu chí hoàn thành Backlog 4 (DoD - Definition of Done)

- [ ] Toàn bộ hệ thống chạy online có link HTTPS công khai (ví dụ: `https://airguard-ai.vercel.app` & `https://airguard-backend.onrender.com`).
- [ ] Dữ liệu 5 trạm S01–S05 tự động cập nhật từ simulator qua MQTT vào DB và hiển thị trên Dashboard.
- [ ] Người dùng bất kỳ có thể vào web chat với AI Agent và nhận câu trả lời có grounding, số liệu thời gian thực.
- [ ] Ban quản lý có thể xem cảnh báo và thực hiện duyệt (Approve / Reject) các đề xuất thông gió.
- [ ] Link URL được gửi lên nhóm / cộng đồng để bắt đầu nhận feedback!

# Backlog 7 — Kế Hoạch Hoàn Thiện Toàn Diện 5 Chức Năng Nâng Cao (AirGuard AI)

> **Mục tiêu:** Kế hoạch hành động chi tiết phân chia công việc (Work Breakdown Structure - WBS) cho toàn bộ 5 chức năng nâng cao của hệ thống AirGuard AI trên cả 3 tầng: **Backend Core**, **Frontend UI/UX**, và **AI Agent / IoT Engine**, chuẩn bị cho đợt kiểm thử tích hợp cuối cùng và buổi bảo vệ sản phẩm.

---

## 📌 BẢNG TỔNG HỢP CÁC TASK TRONG BACKLOG 7 (PHIÊN BẢN NÂNG CẤP ĐỘT PHÁ)

| Mã Task | Tên Nhiệm Vụ & Điểm Nhấn Đột Phá | Phạm vi phụ trách | File hướng dẫn chi tiết |
|---|---|---|---|
| **B7-01** | **Dự báo ô nhiễm 1–24h Đa biến, Khung Giờ Vàng & Animation 24h**<br>• Dự báo đa biến thời tiết, nghịch nhiệt đêm & giờ cao điểm<br>• Tự động gợi ý Khung Giờ Vàng mở cửa sổ & chạy bộ<br>• Nút Play Simulation tự động tua 24h trên bản đồ | Backend Prophet ML + Frontend Draggable Timeline Dock + Recharts | [`task1-forecast-prophet-timeline.md`](task1-forecast-prophet-timeline.md) |
| **B7-02** | **Cảnh báo sớm cá nhân hóa, Tính liều lượng bụi & Lộ trình sạch**<br>• Cảnh báo dự báo sớm trước 30-60 phút<br>• Tính liều lượng bụi hít phải (Inhaled Dose) theo nhịp thở<br>• Lộ trình chạy bộ sạch OSM + Email HTML tương tác 2 chiều | Backend Rule Engine + Resend Email API + Frontend Profile & Route Overlay | [`task2-personalized-alerts-email.md`](task2-personalized-alerts-email.md) |
| **B7-03** | **Bản đồ nhiệt lan truyền khí động học, Hấp thụ mặt nước & Hạt gió động**<br>• Thuật toán IDW hiệu chỉnh vector gió & hấp thụ của Hồ Ngọc Trai/Biển Hồ<br>• Hoạt ảnh luồng hạt gió động (Canvas Wind Streamlines)<br>• Công cụ Pick on Map đo chất lượng tại từng ban công căn hộ | Backend Spatial IDW + Wind Vector + Frontend Canvas Leaflet Heatmap | [`task3-spatial-dispersion-heatmap.md`](task3-spatial-dispersion-heatmap.md) |
| **B7-04** | **Tự động điều tiết thông gió, Hiển thị thiết bị trên Map & HITL Audit Trail**<br>• Layer thiết bị thông gió trên map dành riêng cho Ban Quản Lý<br>• Icon quạt gió động: Xoay tròn & Pulse sáng khi BOOST, đếm ngược thời gian<br>• Vòng lặp phản hồi môi trường: Bật quạt $\rightarrow$ PM2.5 giảm $\rightarrow$ Heatmap đổi màu<br>• AI Agent hiểu thời gian chạy và tư vấn bật/tắt hợp lý | Backend Continuity Window + Approval Service + Device Simulator + Frontend Approvals & Map Layer | [`task4-auto-ventilation-hitl-audit.md`](task4-auto-ventilation-hitl-audit.md) |
| **B7-05** | **Báo cáo môi trường chuẩn ESG, Ma trận 7x24h & AI Narrative xuất bản**<br>• Thống kê lượng bụi đã lọc ($kg$), điện năng tiết kiệm ($kWh$)<br>• Đánh giá tuân thủ quy chuẩn quốc gia QCVN 05:2023/BTNMT<br>• Ma trận nhiệt $7\times 24\text{h}$ & Xuất file PDF giao diện xuất bản cao cấp | Celery Beat Daily/Weekly + Report Generator + PDF/HTML/Markdown Exporter | [`task5-periodic-reports-ai-narrative.md`](task5-periodic-reports-ai-narrative.md) |
| **B7-06** | **Kiểm thử tích hợp, Đồng bộ Contract & Kịch bản Demo 2 Phút**<br>• Chạy toàn bộ 594 Unit tests + 62 Golden Agent cases<br>• Đồng bộ hóa các test contract regex còn tồn đọng<br>• Kịch bản Live Demo 120 giây gây ấn tượng mạnh với Ban Giám khảo | E2E Testing + Fix Test Contracts + Docker Topology + Live Demo Runbook | [`task6-integration-testing-demo.md`](task6-integration-testing-demo.md) |

---

## 🏗️ MA TRẬN PHÂN CHIA TRÁCH NHIỆM & CÔNG NGHỆ

```mermaid
graph TD
    subgraph Backend_Team [Backend & ML Engineer]
        B1[B7-01: Prophet Fourier, Khí tượng & Khung Giờ Vàng]
        B2[B7-02: Inhaled Dose, Cảnh báo sớm & OSM Router]
        B3[B7-03: IDW 30x30, Gió 2 Chiều & Hấp Thụ Mặt Nước]
        B4[B7-04: Closed-loop Decay, Device MQTT & Audit State Machine]
        B5[B7-05: ESG Metrics, Ma Trận 7x24h & PDF WeasyPrint]
    end

    subgraph Frontend_Team [Frontend & UX/UI Engineer]
        F1[B7-01: Play/Pause 24h Animation & Timeline Slider]
        F2[B7-02: Clean Route Polyline & 1-Click Action Email]
        F3[B7-03: Canvas Wind Particles & Pick on Map Tool]
        F4[B7-04: Manager Fan Marker, Pulse Effect & Approvals Drawer]
        F5[B7-05: Weekly Heatmap Matrix & One-Click PDF Download]
    end

    subgraph QA_Demo_Team [AI Agent & QA/DevOps Lead]
        Q1[B7-06: Chạy 594 Unit Tests & 62 Eval Cases 100%]
        Q2[B7-06: Đồng bộ Static Regex Contract Tests]
        Q3[B7-06: Chuẩn bị Kịch bản Live Demo 2 Phút Đỉnh Cao]
    end

    Backend_Team --> Integration[Kiểm thử Tích hợp & Nghiệm thu Sản phẩm]
    Frontend_Team --> Integration
    QA_Demo_Team --> Integration
```

---

## ⏱️ TIẾN ĐỘ THỰC HIỆN DỰ KIẾN

- **Ngày 1 (Sprint 1)**: Hoàn thiện **Task B7-01** (Dự báo & Khung giờ vàng) và **Task B7-03** (Bản đồ nhiệt & Hạt gió).
- **Ngày 2 (Sprint 2)**: Hoàn thiện **Task B7-02** (Liều lượng bụi & Lộ trình sạch) và **Task B7-04** (Thiết bị trên map & Vòng lặp phản hồi môi trường).
- **Ngày 3 (Sprint 3)**: Hoàn thiện **Task B7-05** (Báo cáo ESG & Ma trận 7x24h) và **Task B7-06** (E2E Testing & Demo Script).
- **Ngày 4 (Final Review)**: Chạy thử toàn bộ Docker Compose 8 containers, diễn tập Demo trước Hội đồng.

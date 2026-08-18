# Checklist Nghiệm thu & Đóng gói Sản phẩm Cuối cùng

> **Người phụ trách:** Cả 4 thành viên (Lead bởi Member 1)  
> **Thời hạn:** 21:00 Ngày 6  
> **Mục tiêu:** Đảm bảo sản phẩm hoàn hảo 100% về cả kỹ thuật, trải nghiệm người dùng, video demo và slide thuyết trình bảo vệ.

---

## 1. Bảng Tiêu chí Nghiệm thu Tổng thể (Final Rubric Checklist)

### 1.1. Hạ tầng & Pipeline Dữ liệu
- [ ] Pipeline MQTT 5 trạm hoạt động ổn định trên Cloud, lưu trữ đầy đủ 4 chỉ số (PM2.5, CO₂, Tiếng ồn, Nhiệt độ) và AQI chuẩn EPA.
- [ ] Cơ chế Data Quality Gate chặn dữ liệu sai lệch, trễ hạn, trùng lặp và phân loại trạng thái trạm (Online, Offline, Stale).
- [ ] Không có thông tin nhạy cảm (API key, database password, token) bị lộ trong Git commit hoặc mã nguồn.

### 1.2. Tính năng Cơ bản
- [ ] Dashboard 2 vai trò: Giao diện Cư dân (thân thiện, dễ hiểu) & Giao diện Ban Quản Lý (trung tâm giám sát SOC).
- [ ] Bản đồ Leaflet tương tác, hiển thị 5 trạm, biểu đồ lịch sử 24h mượt mà.
- [ ] Cảnh báo vượt ngưỡng đa chỉ số với cơ chế chống rung nhiễu (consecutive checks, auto-resolve).
- [ ] Luồng duyệt lệnh thông gió HITL bắt buộc qua Manager, có lưu vết Audit Log đầy đủ.

### 1.3. Tính năng Nâng cao
- [ ] Dự báo chuỗi thời gian ô nhiễm 6h–24h bằng Prophet/ML có đánh giá MAE/RMSE vượt trội baseline.
- [ ] Bản đồ nhiệt lan truyền ô nhiễm không gian (IDW Spatial Heatmap) dịch chuyển theo hướng và tốc độ gió.
- [ ] Tự động đề xuất điều tiết thông gió khi có spike ô nhiễm kèm nút Duyệt 1 chạm (Quick Approve).
- [ ] Động cơ Báo cáo Môi trường Định kỳ (Daily/Weekly Digest) sinh tự động bằng LLM.

### 1.4. AI Agent & Đánh giá (Evaluation)
- [ ] LangGraph Agent gọi 8+ backend tools với 100% Grounding, không bịa số liệu.
- [ ] Khuyến nghị cá nhân hóa chính xác theo 3 nhóm đối tượng (`normal`, `sensitive`, `outdoor_sport`).
- [ ] Safety Guard chặn chẩn đoán y tế, chặn lệnh khẩn cấp, chặn vượt quyền HITL.
- [ ] Bộ kiểm thử Live LLM Evaluation đạt 100% PASS trên môi trường cloud.

---

## 2. Kịch bản Video Demo Hoàn chỉnh (3–5 phút)

1. **Phút 0:00 – 0:45 (Giới thiệu bài toán & Tổng quan Cư dân)**:
   - Giới thiệu tổng quan hệ thống AirGuard AI giám sát môi trường tại Vinhomes Ocean Park 1.
   - Mở màn hình Cư dân: Xem bản đồ AQI 5 trạm, chỉ số thành phần (PM2.5, CO₂, Tiếng ồn, Nhiệt độ).
2. **Phút 0:45 – 1:45 (AI Agent Thông minh & Dự báo 24h)**:
   - Chat với AI Agent: Hỏi tình trạng không khí, lời khuyên chạy bộ cho người nhạy cảm.
   - Kéo thanh trượt dự báo thời gian (Timeline Slider): Xem dự báo AQI và Bản đồ nhiệt lan truyền ô nhiễm theo hướng gió trong 24h tới.
3. **Phút 1:45 – 3:00 (Ban Quản Lý, Cảnh báo & Tự động Thông gió HITL)**:
   - Mô phỏng kịch bản ô nhiễm tăng đột biến (Spike).
   - Hệ thống phát cảnh báo đỏ và Agent tự động tạo đề xuất thông gió khẩn cấp.
   - Ban Quản Lý mở màn hình Phê duyệt, bấm **Duyệt 1 chạm** $\rightarrow$ Hệ thống thông gió được kích hoạt $\rightarrow$ Kiểm tra nhật ký Audit Log.
4. **Phút 3:00 – 3:45 (Báo cáo Định kỳ & Tổng kết)**:
   - Mở tab Báo cáo môi trường định kỳ (Daily/Weekly Report) do AI tổng hợp.
   - Tóm tắt giá trị mang lại và kết thúc video.

---

## 3. Bộ Hồ sơ Nộp bài (Submission Pack)

1. **Public Live URL**: Link web frontend chạy trực tiếp trên Internet.
2. **GitHub Repository**: Mã nguồn sạch sẽ, README hướng dẫn chi tiết, commit history rõ ràng.
3. **Video Demo Link**: Link YouTube / Google Drive mở quyền xem công khai.
4. **Slide Deck**: File thuyết trình PDF / PPTX tóm tắt kiến trúc, kết quả thuật toán và giá trị sản phẩm.

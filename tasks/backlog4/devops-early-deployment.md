# Hướng dẫn Triển khai Sớm lên Cloud Miễn phí (Free Hosting)

> **Người phụ trách:** Member 1 (DevOps & Integration Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2 (Trong vòng 24–48h đầu)  
> **Mục tiêu:** Tạo Public HTTPS URL miễn phí cho toàn bộ hệ thống để gửi link xin feedback.

---

## 1. Kiến trúc Triển khai Miễn phí Khuyến nghị

Để chạy đầy đủ toàn bộ hệ thống gồm: Frontend React, FastAPI Backend, AI Agent, Mosquitto MQTT, PostgreSQL DB, Sensor Simulator & Consumer mà **hoàn toàn miễn phí ($0)**, có 2 phương án tối ưu sau:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   PHƯƠNG ÁN A (KHUYẾN NGHỊ: TIỆN LỢI & NHANH NHẤT)               │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. Frontend: Vercel / Netlify (Miễn phí vĩnh viễn, CDN siêu nhanh, SSL tự động)  │
│ 2. Backend + Agent: Render.com Web Service (Free Tier Docker / Python)           │
│ 3. Database: Supabase / Neon.tech (PostgreSQL Free Tier 500MB, có sẵn pgvector)  │
│ 4. MQTT Broker: HiveMQ Cloud Free (Cluster 100 kết nối) hoặc Mosquitto on Render │
│ 5. Simulator + Consumer: Background Worker trên Render hoặc tích hợp cùng app     │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                   PHƯƠNG ÁN B (VPS TRIAL / ALL-IN-ONE DOCKER COMPOSE)             │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. Dùng Cloud Free Trial (Oracle Cloud Always Free VM hoặc Google Cloud $300)     │
│ 2. Chạy toàn bộ bằng Docker Compose có sẵn: `docker-compose.public-demo.yml`      │
│ 3. Caddy Server tự động cấp chứng chỉ SSL HTTPS miễn phí                         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Các bước triển khai chi tiết theo Phương án A

### Bước 1: Khởi tạo Database PostgreSQL trên Supabase hoặc Neon.tech (5 phút)
1. Đăng ký tài khoản miễn phí tại [neon.tech](https://neon.tech) hoặc [supabase.com](https://supabase.com).
2. Tạo project mới tên `airguard-ai`.
3. Lấy chuỗi kết nối `DATABASE_URL` (dạng `postgresql://user:pass@ep-xyz.neon.tech/airguard?sslmode=require`).
4. Chạy script khởi tạo bảng trong SQL Editor: copy toàn bộ nội dung file [`backend/db/schema.sql`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/db/schema.sql) và execute.

---

### Bước 2: Deploy Backend & Agent lên Render.com (15 phút)
1. Đăng ký tài khoản [render.com](https://render.com) (liên kết GitHub).
2. Chọn **New Web Service** $\rightarrow$ Kết nối với repository GitHub của nhóm.
3. Cấu hình dịch vụ:
   - **Name:** `airguard-backend`
   - **Root Directory:** để trống hoặc `./`
   - **Runtime:** `Python 3` (hoặc `Docker`)
   - **Build Command:** `pip install -r backend/requirements.txt -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port 10000`
4. Cấu hình **Environment Variables** trên Render:
   ```env
   DATABASE_URL=postgresql://... (lấy từ Bước 1)
   OPENAI_API_KEY=sk-... (API key của nhóm)
   MODEL_NAME=gpt-4o-mini
   ALLOWED_ORIGINS=https://airguard-frontend.vercel.app,http://localhost:5173
   SENSOR_SCENARIO=normal
   AUTO_PROPOSAL_ENABLED=true
   ```
5. Nhấn **Deploy** $\rightarrow$ Khi hoàn tất bạn sẽ nhận được URL: `https://airguard-backend.onrender.com`.
6. Kiểm tra URL hoạt động: Mở `https://airguard-backend.onrender.com/health` (phải trả về `status: "ok"`).

---

### Bước 3: Deploy Frontend lên Vercel (10 phút)
1. Đăng ký tài khoản [vercel.com](https://vercel.com) (liên kết GitHub).
2. Chọn **Add New Project** $\rightarrow$ Chọn repository `P-074`.
3. Cấu hình build:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Cấu hình **Environment Variable**:
   ```env
   VITE_API_BASE_URL=https://airguard-backend.onrender.com/api/v1
   ```
5. Nhấn **Deploy** $\rightarrow$ Nhận Public URL: `https://airguard-frontend.vercel.app`.

---

### Bước 4: Khởi chạy Background Simulator & MQTT Ingestion
* Để dữ liệu cảm biến liên tục được cập nhật trên bản đồ khi người dùng vào web:
  * Cách 1: Chạy `services/sensor-simulator` và `services/mqtt-consumer` dưới dạng Background Worker trên Render hoặc 1 máy local/VPS kết nối vào DB Neon/Supabase.
  * Cách 2 (Tích hợp thông minh): Trong `backend/app/main.py`, khởi chạy một background thread sinh dữ liệu mô phỏng định kỳ vào DB nếu phát hiện môi trường cloud không có broker MQTT ngoài.

---

## 3. Checklist Smoke Test trên Live URL

Sau khi deploy xong, chạy các lệnh kiểm tra:

```bash
# 1. Kiểm tra Backend Health
curl -fsS https://airguard-backend.onrender.com/health

# 2. Kiểm tra Danh sách Trạm
curl -fsS https://airguard-backend.onrender.com/api/v1/stations

# 3. Kiểm tra Agent Chat
curl -X POST https://airguard-backend.onrender.com/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Chất lượng không khí ở S01 hiện tại thế nào?", "user_id": "demo-user", "station_id": "S01"}'

# 4. Mở Frontend trên trình duyệt (điện thoại & laptop)
# https://airguard-frontend.vercel.app
```

---

## 4. Biểu mẫu gửi Link xin Feedback

Sau khi hoàn tất, gửi mẫu thông báo sau lên nhóm/cộng đồng:

```text
🎉 [AirGuard AI] Đã hoàn thành bản MVP Demo Online!
🔗 Link trải nghiệm: https://airguard-frontend.vercel.app
📖 Các tính năng có thể thử ngay:
1. Xem bản đồ AQI 5 trạm ngoài trời khu vực Vinhomes Ocean Park 1.
2. Trò chuyện tự nhiên với AI Agent (hỏi chất lượng không khí, lời khuyên chạy bộ, so sánh khu vực).
3. Đóng vai Ban Quản Lý để xem cảnh báo ô nhiễm và duyệt đề xuất kích hoạt hệ thống thông gió.
👉 Rất mong nhận được góp ý và feedback từ thầy/cô và các bạn!
```

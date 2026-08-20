# Hướng dẫn Triển khai Sớm lên Cloud Miễn phí (Free Hosting) & Public Demo

> **Mã công việc:** `B4-OPS-01` & `B4-OPS-02`  
> **Người phụ trách:** Member 1 (DevOps & Integration Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2 (Trong vòng 24–48h đầu của dự án)  
> **Mục tiêu:** Tạo Public HTTPS URL ổn định và miễn phí ($0) cho toàn bộ hệ thống AirGuard AI để gửi link cho Mentor, Giảng viên và Người dùng trải nghiệm, thu thập feedback sớm!

---

## 1. Tổng quan Kiến trúc Triển khai Miễn phí

Để vận hành đầy đủ toàn bộ hệ sinh thái **AirGuard AI** (Frontend React, FastAPI Backend, AI Agent LangGraph, Mosquitto MQTT, PostgreSQL DB, Sensor Simulator & Consumer) mà **hoàn toàn không mất chi phí**, nhóm có 3 chiến lược sau:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   CHIẾN LƯỢC 1: CLOUD FREE-TIER STACK (KHUYẾN NGHỊ 24/7)                │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Frontend: Vercel / Netlify (Free CDN toàn cầu, SSL HTTPS tự động, zero cold start)    │
│ 2. Backend + AI Agent: Render.com Web Service (Python 3.11 / Docker Free Tier)           │
│ 3. Database: Neon.tech / Supabase (PostgreSQL 16 Cloud Free Tier 500MB, có sẵn SSL)      │
│ 4. MQTT Broker & Ingestion: Cloud MQTT (HiveMQ Free) hoặc Ingestion Worker trên Render   │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   CHIẾN LƯỢC 2: ALL-IN-ONE VPS DOCKER COMPOSE + CADDY SSL                │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Hạ tầng: Oracle Cloud Always Free VM (4 OCPU, 24GB RAM) hoặc Google Cloud $300 Trial   │
│ 2. Topology: Chạy toàn bộ qua `docker-compose.public-demo.yml`                          │
│ 3. Reverse Proxy: Caddy Server tự động đăng ký và gia hạn chứng chỉ Let's Encrypt SSL    │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   CHIẾN LƯỢC 3: ZERO-CONFIG INSTANT TUNNELING (DEMO TỨC THÌ 30s)         │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Hạ tầng: Máy local của Member đang chạy Docker / Node.js                              │
│ 2. Công cụ: Cloudflare Quick Tunnel (`npx cloudflared tunnel --url http://localhost:5173`)│
│ 3. Ưu điểm: Không cần đăng ký tài khoản cloud, có ngay HTTPS URL public để demo tức thì! │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hướng dẫn Chi tiết Chiến lược 1: Cloud Free-Tier Stack

### Bước 1: Khởi tạo Database PostgreSQL trên Neon.tech (5 phút)
1. Đăng ký tài khoản miễn phí tại **[neon.tech](https://neon.tech)** (đăng nhập bằng GitHub).
2. Tạo project mới tên: `airguard-ai` (chọn Region `Singapore - ap-southeast-1` để có độ trễ thấp nhất về Việt Nam).
3. Lấy chuỗi kết nối `DATABASE_URL` (dạng: `postgresql://user:password@ep-xyz.ap-southeast-1.aws.neon.tech/airguard?sslmode=require`).
4. **Khởi tạo bảng và dữ liệu mẫu**:
   - Mở tab **SQL Editor** trên Dashboard của Neon.
   - Mở file [`backend/db/schema.sql`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/db/schema.sql), copy toàn bộ nội dung và bấm **Run**.
   - Mở tiếp file [`backend/db/seed.sql`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/db/seed.sql), copy và bấm **Run** để nạp dữ liệu 5 trạm quan trắc ban đầu.

---

### Bước 2: Deploy Backend & AI Agent lên Render.com (15 phút)

Nhóm có thể triển khai nhanh bằng file cấu hình [`render.yaml`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/render.yaml) (Blueprint) hoặc tạo Web Service thủ công:

#### Cách tạo Web Service thủ công trên Render:
1. Đăng nhập **[render.com](https://render.com)** $\rightarrow$ Bấm **New +** $\rightarrow$ Chọn **Web Service**.
2. Chọn repo GitHub `P-074` của nhóm.
3. Cấu hình dịch vụ **Backend API**:
   - **Name:** `airguard-backend`
   - **Region:** `Singapore (Southeast Asia)`
   - **Branch:** `main` (hoặc `develop`)
   - **Root Directory:** `./`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r backend/requirements.txt -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
4. Cấu hình **Environment Variables** trên Render:
   | Tên biến | Giá trị cấu hình | Ghi chú |
   |---|---|---|
   | `APP_ENV` | `production` | Chế độ chạy |
   | `DATABASE_URL` | *(Chuỗi kết nối Neon ở Bước 1)* | Bắt buộc có `?sslmode=require` |
   | `CORS_ORIGINS` | `https://*.vercel.app,http://localhost:5173` | Cho phép Frontend gọi API |
   | `OPENAI_API_KEY` | `sk-...` | Khóa API OpenAI của nhóm |
   | `MODEL_NAME` | `gpt-4o-mini` | Model LLM tiết kiệm & nhanh |
   | `AUTO_PROPOSAL_ENABLED` | `true` | Bật tạo đề xuất HITL tự động |
   | `STALE_AFTER_SECONDS` | `300` | Ngưỡng đánh dấu dữ liệu cũ |

5. Nhấn **Create Web Service** $\rightarrow$ Đợi build xong, bạn sẽ nhận được URL:
   `https://airguard-backend.onrender.com`

---

### Bước 3: Deploy Frontend React lên Vercel (5 phút)

1. Đăng nhập **[vercel.com](https://vercel.com)** bằng tài khoản GitHub.
2. Chọn **Add New...** $\rightarrow$ **Project** $\rightarrow$ Import repository `P-074`.
3. Cấu hình Build & Output Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend` *(Bắt buộc chọn thư mục frontend)*
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`
4. Cấu hình **Environment Variables**:
   | Tên biến | Giá trị |
   |---|---|
   | `VITE_API_BASE_URL` | `https://airguard-backend.onrender.com` |

5. File rewrite [`frontend/vercel.json`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/vercel.json) đã được cấu hình sẵn để tránh lỗi 404 khi người dùng tải lại trang.
6. Nhấn **Deploy** $\rightarrow$ Nhận URL công khai: `https://airguard-ai.vercel.app`.

---

### Bước 4: Khởi chạy Cảm biến Mô phỏng & Ingestion (Data Pipeline)

Để dữ liệu AQI và 5 trạm trên bản đồ liên tục nhảy số mới:
- **Phương án A (Tiết kiệm)**: Chạy container `sensor-simulator` và `mqtt-consumer` trên máy local hoặc VPS trỏ biến `DATABASE_URL` vào Neon PostgreSQL.
- **Phương án B (Auto-Heartbeat)**: Backend API tích hợp sẵn fallback và cơ chế tự động cập nhật measurement gần nhất cho 5 trạm khi có request.

---

## 3. Hướng dẫn Chiến lược 3: Instant Tunneling (Chia sẻ Link Demo trong 30s)

Nếu cần gửi link gấp cho Mentor hoặc Ban tổ chức chấm bài trực tiếp mà không cần chờ setup Cloud:

1. **Khởi chạy hệ thống trên máy local:**
   ```powershell
   # Khởi chạy Frontend React
   cd frontend
   npm run dev
   ```
2. **Mở terminal mới và phát sóng Cloudflare Tunnel:**
   ```powershell
   npx -y cloudflared tunnel --url http://localhost:5173
   ```
3. Terminal sẽ cấp 1 URL dạng: `https://xxxx-xxxx-xxxx.trycloudflare.com`.
4. File [`frontend/vite.config.ts`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/frontend/vite.config.ts) đã bật `allowedHosts: true` nên link này sẽ hoạt động ngay lập tức cho bất kỳ ai truy cập từ xa.

---

## 4. Bộ Kịch bản Smoke Test trên Live URL (Task B4-OPS-02)

Sau khi deploy thành công, chạy bộ kiểm thử sau để nghiệm thu hệ thống (Thay URL bằng link thật của nhóm):

```bash
# ==========================================
# 1. Kiểm tra Backend Health
# ==========================================
curl -fsS https://airguard-backend.onrender.com/health
# Kỳ vọng: {"status": "ok", "service": "airguard-backend"}

# ==========================================
# 2. Kiểm tra Danh sách 5 Trạm Quan trắc
# ==========================================
curl -fsS https://airguard-backend.onrender.com/api/v1/stations
# Kỳ vọng: Trả về danh sách trạm S01 -> S05 kèm tọa độ và chỉ số AQI/PM2.5

# ==========================================
# 3. Kiểm tra Chi tiết Trạm & Lịch sử
# ==========================================
curl -fsS https://airguard-backend.onrender.com/api/v1/stations/S01/current
curl -fsS "https://airguard-backend.onrender.com/api/v1/stations/S01/history?hours=24"

# ==========================================
# 4. Kiểm tra Danh sách Cảnh báo Môi trường
# ==========================================
curl -fsS https://airguard-backend.onrender.com/api/v1/alerts

# ==========================================
# 5. Kiểm tra AI Agent Chat (Grounding Test)
# ==========================================
curl -X POST https://airguard-backend.onrender.com/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Chỉ số AQI ở trạm S03 hiện tại là bao nhiêu?", "user_id": "USR-001", "station_id": "S03"}'
# Kỳ vọng: Agent trả lời chính xác số liệu từ trạm S03, có trích dẫn used_tools
```

### Checklist Kiểm thử Giao diện (UI Smoke Test)
- [ ] Truy cập URL Frontend trên máy tính và điện thoại.
- [ ] Bản đồ Leaflet load mượt, hiển thị đủ 5 trạm quan trắc và Heatmap layer.
- [ ] Click vào từng trạm hiển thị Drawer chi tiết với 4 chỉ số (PM2.5, CO₂, Tiếng ồn, Nhiệt độ) và biểu đồ lịch sử/dự báo.
- [ ] Mở tab **AI Trợ lý** và gửi câu hỏi $\rightarrow$ Nhận phản hồi kèm bằng chứng (Grounding facts).
- [ ] Mở tab **Phê duyệt BQL** $\rightarrow$ Thử nghiệm thao tác Duyệt (Approve) hoặc Từ chối (Reject) đề xuất cảnh báo.

---

## 5. Cẩm nang Xử lý Sự cố Thường gặp (Troubleshooting & Anti-Sleep)

| Hiện tượng | Nguyên nhân | Cách khắc phục |
|---|---|---|
| **Render Web Service bị chậm lần đầu (Cold Start 30-50s)** | Gói Render Free tự động sleep sau 15 phút không có truy cập. | Sử dụng dịch vụ miễn phí **[cron-job.org](https://cron-job.org)** hoặc **[uptimerobot.com](https://uptimerobot.com)** tạo cron ping URL `https://airguard-backend.onrender.com/health` mỗi 10 phút/lần. |
| **Lỗi `CORS error: No 'Access-Control-Allow-Origin' header`** | Backend chưa cho phép domain Vercel. | Vào Render $\rightarrow$ Environment Variables $\rightarrow$ sửa `CORS_ORIGINS` bao gồm cả domain Vercel của bạn (ví dụ `https://airguard-ai.vercel.app`). |
| **Lỗi `Mixed Content: This request has been blocked`** | Frontend chạy HTTPS nhưng lại gọi API Backend bằng HTTP. | Đảm bảo biến `VITE_API_BASE_URL` trên Vercel luôn bắt đầu bằng `https://`. |
| **Lỗi `Blocked request. This host is not allowed` (Vite 6)** | Cơ chế chặn Host header lạ khi dùng tunnel. | Đã cấu hình `allowedHosts: true` trong `frontend/vite.config.ts`. |
| **Mất dữ liệu DB sau khi deploy lại** | Chưa cấu hình volume hoặc dùng database in-memory. | Đảm bảo `DATABASE_URL` trỏ vào Cloud PostgreSQL (Neon/Supabase) có tính lưu trữ bền vững. |

---

## 6. Biểu mẫu Đăng tải Link Demo Xin Góp ý

Sau khi hoàn tất triển khai và smoke test, copy mẫu thông báo sau để gửi lên nhóm dự án / Discord / Zalo:

```text
🌿 [AirGuard AI] - ĐÃ SẴN SÀNG BẢN DEMO TRỰC TUYẾN (EARLY MVP) 🌿

Kính gửi Thầy/Cô, Mentor và các bạn,

Đội ngũ phát triển AirGuard AI đã hoàn thành việc triển khai bản thử nghiệm sớm lên môi trường Cloud công khai. 

🔗 Link trải nghiệm trực tiếp: https://airguard-ai.vercel.app
📊 API Documentation: https://airguard-backend.onrender.com/docs

✨ Các tính năng nổi bật có thể trải nghiệm ngay:
1. Bản đồ Giám sát Chất lượng Không khí: Theo dõi AQI, PM2.5, CO2, Tiếng ồn, Nhiệt độ thời gian thực tại 5 phân khu Vinhomes Ocean Park 1.
2. AI Trợ lý Sức khỏe (Grounding 100%): Tư vấn hoạt động ngoài trời, so sánh các khu vực dựa trên dữ liệu cảm biến thực tế.
3. Không gian Phê duyệt Ban Quản Lý (HITL): Xem cảnh báo ô nhiễm vượt ngưỡng và duyệt đề xuất kích hoạt hệ thống thông gió lọc không khí.

👉 Nhóm rất mong nhận được những nhận xét, đánh giá và góp ý của mọi người để tiếp tục hoàn thiện sản phẩm trong các giai đoạn tiếp theo!
```

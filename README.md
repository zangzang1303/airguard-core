# AirGuard AI — Hệ thống Giám sát Môi trường & Hỗ trợ Ra quyết định Thông minh
## Vinhomes Ocean Park 1, Hà Nội

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?style=flat&logo=TypeScript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?style=flat&logo=PostgreSQL&logoColor=white)](https://www.postgresql.org/)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-660066.svg?style=flat&logo=EclipseMosquitto&logoColor=white)](https://mosquitto.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=Docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-153%2F153%20Passed%20(100%25)-10B981.svg?style=flat)](docs/testing/)
[![Live App](https://img.shields.io/badge/Live%20Demo-Azure%20Cloud-0EA5E9.svg?style=flat&logo=microsoftazure)](https://airguard-074-app.indonesiacentral.cloudapp.azure.com)

---

### 🌐 THÔNG TIN TRUY CẬP TRỰC TIẾP & BỘ TÀI LIỆU NỘP BÀI (FINAL SUBMISSION)

> * 🌐 **Live Web Application (Production)**: [**https://airguard-074-app.indonesiacentral.cloudapp.azure.com**](https://airguard-074-app.indonesiacentral.cloudapp.azure.com)
> * 🎬 **Video Demo Trải Nghiệm**: [**Xem Video Demo Sản Phẩm (Loom / YouTube)**](https://airguard-074-app.indonesiacentral.cloudapp.azure.com)
> * 📁 **Hồ Sơ Nộp Bài Chuẩn BTC AI20K**:
>   * 📐 [**Sơ đồ & Tài liệu Kiến trúc (Architecture)**](./docs/architecture/) — Sơ đồ C4, 5 phân tầng, IoT Telemetry, HITL Dispatcher.
>   * 🎨 [**Đặc tả SRS & Thiết kế UI/UX (Design)**](./docs/design/SRS.md) — Đặc tả IEEE 830 v2.2.0, 10 Use Cases, 2 Roles, Live UI Mockups.
>   * 🧪 [**Kế hoạch & Báo cáo Kiểm thử (Testing)**](./docs/testing/) — Test Plan, 153/153 Automated Test Cases Passed (100%).
>   * 📅 [**Nhật ký Tiến độ Hàng tuần (Weekly Logs)**](./weekly-logs/) — Báo cáo chi tiết từ Tuần 01 đến Tuần 06 (Gate 2).
>   * 🎤 [**Kịch bản Thuyết trình Pitching (Presentation)**](./presentation/airguard_ai_pitching_deck_script.md) — Kịch bản slide & Q&A.
>   * 📘 [**Cẩm Nang Ôn Tập Trước Khi Pitching (Master Briefing Handbook)**](./presentation/AIRGUARD_AI_MASTER_BRIEFING_DOC.md) — Tài liệu đọc trọn gói toàn bộ dự án & 10 câu hỏi Q&A.

> **Tuyên bố minh bạch:** Toàn bộ dữ liệu cảm biến trong MVP hiện tại đến từ hệ thống mô phỏng (`source=simulator`) phục vụ mục đích nghiên cứu, học tập và trình diễn công nghệ. Đây không phải hệ thống quan trắc môi trường chính thức được cấp phép. Không sử dụng dữ liệu này để chẩn đoán y tế chuyên sâu, ban bố tình trạng khẩn cấp hoặc ra các quyết định pháp lý.

---

## 📑 Mục lục

1. [Tổng quan dự án & Giá trị cốt lõi](#1-tổng-quan-dự-án--giá-trị-cốt-lõi)
2. [Kiến trúc hệ thống tổng thể](#2-kiến-trúc-hệ-thống-tổng-thể)
3. [Công nghệ sử dụng](#3-công-nghệ-sử-dụng)
4. [Mạng lưới 5 Trạm quan trắc & Đặc tính vi khí hậu](#4-mạng-lưới-5-trạm-quan-trắc--đặc-tính-vi-khí-hậu)
5. [Hệ thống chỉ số & Ngưỡng cảnh báo đa tầng](#5-hệ-thống-chỉ-số--ngưỡng-cảnh-báo-đa-tầng)
6. [AI Agent Geospatial & Cơ chế Grounding](#6-ai-agent-geospatial--cơ-chế-grounding)
7. [Thuật toán Tìm đường Thông minh (AQI-Aware Safe Routing)](#7-thuật-toán-tìm-đường-thông-minh-aqi-aware-safe-routing)
8. [Quy trình Phê duyệt Con người (HITL) & Audit Log](#8-quy-trình-phê-duyệt-con-người-hitl--audit-log)
9. [Báo cáo Môi trường & Bền vững ESG](#9-báo-cáo-môi-trường--bền-vững-esg)
10. [Bộ chỉ số Đánh giá Thực địa (Field Evaluation Metrics)](#10-bộ-chỉ-số-đánh-giá-thực-địa-field-evaluation-metrics)
11. [Hướng dẫn Cài đặt & Khởi chạy (A–Z)](#11-hướng-dẫn-cài-đặt--khởi-chạy-az)
12. [Danh mục API Reference](#12-danh-mục-api-reference)
13. [Cấu hình Biến môi trường (.env)](#13-cấu-hình-biến-môi-trường-env)
14. [Quy trình Kiểm thử & Đảm bảo chất lượng](#14-quy-trình-kiểm-thử--đảm-bảo-chất-lượng)
15. [Cấu trúc Thư mục Dự án](#15-cấu-trúc-thư-mục-dự-án)
16. [Xử lý sự cố thường gặp (Troubleshooting)](#16-xử-lý-sự-cố-thường-gặp-troubleshooting)
17. [Giới hạn đã biết & Lộ trình phát triển](#17-giới-hạn-đã-biết--lộ-trình-phát-triển)

---

## 1. Tổng quan dự án & Giá trị cốt lõi

**AirGuard AI** là nền tảng số giám sát vi khí hậu và hỗ trợ ra quyết định thông minh cho đô thị kiểu mẫu **Vinhomes Ocean Park 1** (Gia Lâm, Hà Nội). Dự án kết hợp công nghệ **IoT Pipeline thời gian thực**, **Mô hình AI Agent phân tích không gian (Geospatial Agent)** và **Thuật toán quy hoạch tuyến đường theo chất lượng không khí (AQI Routing)**.

```
                  ┌─────────────────────────────────────────┐
                  │              AIRGUARD AI                │
                  │   Môi trường xanh - Vận động an toàn    │
                  └────────────────────┬────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
 📊 GIÁM SÁT VI KHÍ HẬU        🤖 AI AGENT TRỢ LÝ             🏃 LỘ TRÌNH THÔNG MINH
 5 trạm IoT đo 4 chỉ số        100% Grounded, hội thoại      Bám mạng vỉa hè OSM,
 Cập nhật 10s qua MQTT         đa ngữ cảnh, gợi ý an toàn    né vùng ô nhiễm, đóng vòng
```

### Vấn đề thực tế tại đô thị lớn
Tại các đại đô thị có mật độ dân cư và tiện ích phong phú như Vinhomes Ocean Park 1:
1. **Chất lượng không khí phân hóa mạnh theo không gian**: Vùng ven hồ nước ngọt (Hồ Ngọc Trai) và biển hồ nhân tạo có nồng độ bụi mịn PM2.5 thấp hơn 30–40% so với các trục đường giao thông chính giáp đường gom cao tốc Hà Nội - Hải Phòng.
2. **Thiếu công cụ điều hướng vi khí hậu**: Cư dân chạy bộ, đi dạo hay đạp xe hiện chỉ có thể dùng các app bản đồ thông thường (chỉ tối ưu khoảng cách ngắn nhất, thường dẫn vào các trục đường có mật độ khí thải cao).
3. **Cần sự minh bạch & an toàn trong quyết định AI**: Các đề xuất kích hoạt hệ thống lọc khí công cộng hoặc hệ thống thông gió cần được kiểm soát chặt chẽ bởi Ban Quản lý (Human-in-the-Loop) để tránh lãng phí năng lượng hoặc cảnh báo sai.

### Mục tiêu giải pháp
- **Giám sát trực quan**: Cung cấp bức tranh toàn cảnh về AQI, PM2.5, CO₂, tiếng ồn và nhiệt độ tức thì trên bản đồ nhiệt tương tác.
- **Tuyến đường xanh & an toàn**: Tự động tính toán đường đi bám sát 100% vỉa hè thực tế, giảm thiểu tối đa lượng bụi mịn hít vào cơ thể (`inhaled mass`).
- **Trợ lý AI tin cậy**: AI giải đáp thông tin sức khỏe dựa trên 100% dữ liệu đo đạc thực tế từ trạm (Zero Hallucination).

---

## 2. Kiến trúc hệ thống tổng thể

Hệ thống được thiết kế theo mô hình phân lớp rõ ràng, đảm bảo tính độc lập, mở rộng và bảo mật thông tin cao:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 LỚP THU THẬP DỮ LIỆU CẢM BIẾN (IoT LAYER)               │
│  [S01 Đa Tốn]   [S02 Sapphire]   [S03 Ngọc Trai]   [S04 VinUni]  [S05 Lagoons] │
│        │               │                │               │              │ │
│        └───────────────┴────────┬───────┴───────────────┴──────────────┘ │
│                                 ▼ MQTT (QoS 1)                           │
│                     ┌───────────────────────┐                            │
│                     │ Eclipse Mosquitto (1883)│                          │
│                     └───────────┬───────────┘                            │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 LỚP XỬ LÝ & LƯU TRỮ (INGESTION & STORAGE)                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ MQTT Consumer: Schema Validation, Freshness Check, Outlier Filter │   │
│  └──────────────────────────────┬───────────────────────────────────┘   │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ PostgreSQL 16 (System of Record): Stations, Measurements, Alerts │   │
│  └──────────────────────────────┬───────────────────────────────────┘   │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 LỚP DỊCH VỤ & NGHIỆP VỤ (BACKEND FASTAPI)                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ Alert Engine │ │ Forecast Svc │ │ OSM Router   │ │ HITL & Audit   │  │
│  │ (Multi-metric│ │ (1-3h Trend /│ │ (10.5k Edges │ │ (Manager Queue │  │
│  │  Rule-based) │ │  24h Fourier)│ │  AQI-Dijkstra│ │  & Dispatcher) │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘  │
│                                 ▲                                       │
│                                 │ REST / OpenAPI                        │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 LỚP TRẢI NGHIỆM NGƯỜI DÙNG (FRONTEND & AI)               │
│  ┌─────────────────────────────────┐   ┌─────────────────────────────┐  │
│  │ React 18 + Vite + TypeScript    │   │ AI Agent (LangGraph/Tool)   │  │
│  │ - Leaflet Interactive Map       │   │ - 100% Grounded Context     │  │
│  │ - Real-time AQI Heatmap         │   │ - Natural Conversation Gate │  │
│  │ - 30s Adaptive Polling Engine   │   │ - Deterministic Fallback    │  │
│  └─────────────────────────────────┘   └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Ranh giới trách nhiệm kiến trúc (Ownership Boundaries)

| Thành phần | Trách nhiệm chính | Giới hạn nghiêm ngặt (Không được làm) |
|---|---|---|
| **Sensor Simulator** | Phát sinh dữ liệu mô phỏng theo 6 kịch bản thực tế | Không giả mạo nguồn dữ liệu chính thức, không sửa DB |
| **MQTT Consumer** | Xác thực schema, kiểm tra độ tươi (`freshness`), ghi DB | Không tự ý tính toán khuyến nghị hoặc tự tạo cảnh báo |
| **PostgreSQL** | Lưu trữ bất biến lịch sử đo, cảnh báo, đề xuất, audit log | Không cấp quyền truy cập trực tiếp cho Frontend / Agent |
| **FastAPI Backend** | Cung cấp REST API, chạy Rule Engine, tìm đường, quản lý HITL | Không tin cậy dữ liệu đầu vào khi chưa qua Pydantic schema |
| **AI Agent** | Tiếp nhận câu hỏi, gọi tools, tổng hợp phản hồi có grounding | Không tự suy đoán số liệu, không tự ý duyệt proposal |
| **React Dashboard** | Hiển thị bản đồ, đồ thị, chat drawer, giao diện duyệt | Không kết nối trực tiếp MQTT/DB, không tự suy diễn cảnh báo |
| **Manager (Human)** | Xem xét bằng chứng đo đạc, duyệt/từ chối đề xuất kích hoạt | Không được sửa đổi lịch sử audit log đã ghi |

---

## 3. Công nghệ sử dụng

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             TECH STACK MATRIX                            │
├─────────────────┬──────────────────────────────────┬─────────────────────┤
│ TẦNG HỆ THỐNG   │ CÔNG NGHỆ CHỦ CHỐT               │ PHIÊN BẢN / CHI TIẾT │
├─────────────────┼──────────────────────────────────┼─────────────────────┤
│ Frontend        │ React, TypeScript, Vite          │ React 18, TS 5.x    │
│ Bản đồ số       │ Leaflet, React-Leaflet           │ Leaflet 1.9         │
│ Biểu đồ & UI    │ Recharts, Lucide Icons, Vanilla  │ Modern Glassmorphism│
│ Backend API     │ Python, FastAPI, Pydantic        │ Python 3.11, V2.x   │
│ Cơ sở dữ liệu   │ PostgreSQL                       │ PostgreSQL 16-alpine│
│ Giao thức IoT   │ Eclipse Mosquitto, Paho MQTT     │ MQTT v3.1.1 / QoS 1 │
│ AI & Đồ thị     │ LangGraph, LangChain, OSM Graph  │ Gemini / Claude / OS│
│ Xử lý nền       │ Celery, Redis, RabbitMQ          │ Profile async-jobs  │
│ Container hóa   │ Docker, Docker Compose           │ Compose v2 Spec     │
└─────────────────┴──────────────────────────────────┴─────────────────────┘
```

---

## 4. Mạng lưới 5 Trạm quan trắc & Đặc tính vi khí hậu

Hệ thống bố trí 5 trạm quan trắc mô phỏng đại diện cho 5 khu vực sinh thái và công năng đặc thù tại Vinhomes Ocean Park 1:

| Mã trạm | Tên trạm | Tọa độ GPS | Độ cao | Đặc điểm vi khí hậu & Môi trường |
|:---:|---|:---:|:---:|---|
| **S01** | Trục Đa Tốn (Tây Bắc) | `21.0008°N, 105.9428°E` | 8m | **Khu vực cửa ngõ giao thông**: Tiếp giáp đường Đa Tốn và nút giao cao tốc. Bụi mịn PM2.5 và tiếng ồn thường cao nhất toàn khu vào giờ cao điểm. |
| **S02** | Khu căn hộ Sapphire | `20.9975°N, 105.9430°E` | 12m | **Khu vực dân cư cao tầng**: Mật độ xây dựng cao, hiệu ứng hẻm gió đô thị, nồng độ CO₂ tăng nhẹ vào khung giờ sinh hoạt tối. |
| **S03** | Hồ Ngọc Trai (24.5 ha) | `20.9940°N, 105.9520°E` | 5m | **Khu vực sinh thái lõi**: Không khí trong lành nhất, độ ẩm cao, nhiệt độ thấp hơn 1.5–2°C nhờ mặt nước rộng và dải cát trắng. |
| **S04** | Đại học VinUni | `20.9898°N, 105.9467°E` | 7m | **Khu vực giáo dục & cây xanh**: Tán cây xanh dày đặc, đường nội bộ cấm xe tải. Nồng độ PM2.5 thấp thứ 2 toàn khu. |
| **S05** | Biển hồ Crystal Lagoon | `20.9870°N, 105.9530°E` | 6m | **Khu vực nghỉ dưỡng ven hồ mặn**: Gió thoáng rộng, thích hợp cho hoạt động đi bộ ven biển hồ và đạp xe thư giãn. |

```
                       [S01] Trục Đa Tốn (Cửa ngõ)
                                                     \  [S02] Sapphire (Chung cư)
                            \     |
                             \    |    [S03] Hồ Ngọc Trai (Sinh thái sạch nhất)
                              \   |   /
                               \  |  /
                           [S04] VinUni ---- [S05] Crystal Lagoon (Biển hồ)
```

---

## 5. Hệ thống chỉ số & Ngưỡng cảnh báo đa tầng

### Các chỉ số quan trắc cốt lõi
1. **PM2.5 (`µg/m³`)**: Bụi mịn có kích thước hạt ≤ 2.5 micromet — chỉ số gây hại đường hô hấp lớn nhất.
2. **CO₂ (`ppm`)**: Nồng độ Carbon Dioxide — đánh giá mức độ thông thoáng và ngột ngạt không khí.
3. **Tiếng ồn (`dB`)**: Mức áp suất âm thanh môi trường — đánh giá mức độ ô nhiễm tiếng ồn đô thị.
4. **Nhiệt độ (`°C`) & Độ ẩm (`%`)**: Chỉ số khí tượng nền — tính toán mức độ thoải mái ngoài trời.
5. **AQI (Air Quality Index)**: Chỉ số chất lượng không khí tổng hợp, dẫn xuất từ nồng độ PM2.5 theo tiêu chuẩn **US EPA 2012**.

### Bảng phân loại chất lượng không khí (US EPA Standard)

| Mức AQI | Nồng độ PM2.5 (24h) | Màu sắc cảnh báo | Phân loại | Khuyến nghị sức khỏe & Vận động |
|:---:|:---:|:---:|:---:|---|
| **0 – 50** | 0.0 – 12.0 µg/m³ | 🟢 Xanh lá | **Tốt** | Không khí lý tưởng. Tự do vận động thể thao ngoài trời. |
| **51 – 100** | 12.1 – 35.4 µg/m³ | 🟡 Vàng | **Trung bình** | Chấp nhận được. Nhóm cực kỳ nhạy cảm nên chú ý nếu khó thở. |
| **101 – 150** | 35.5 – 55.4 µg/m³ | 🟠 Cam | **Kém (Nhạy cảm)** | Trẻ nhỏ, người già, người hen suyễn nên hạn chế chạy gắng sức. |
| **151 – 200** | 55.5 – 150.4 µg/m³ | 🔴 Đỏ | **Xấu** | Mọi người bắt đầu bị ảnh hưởng; chuyển hoạt động thể thao vào nhà. |
| **201 – 300** | 150.5 – 250.4 µg/m³ | 🟣 Tím | **Rất xấu** | Cảnh báo sức khỏe khẩn cấp; đóng cửa sổ, bật máy lọc không khí. |
| **301+** | ≥ 250.5 µg/m³ | 🟤 Nâu | **Nguy hại** | Nguy hiểm nghiêm trọng; tuyệt đối không hoạt động ngoài trời. |

### Bảng ngưỡng kích hoạt cảnh báo tự động (Provisional Rules)

| Chỉ số quan trắc | Đơn vị | Ngưỡng Cảnh báo (Warning) | Ngưỡng Nguy hiểm (Critical) | Điều kiện kích hoạt |
|---|:---:|:---:|:---:|:---:|
| **PM2.5** | µg/m³ | `≥ 50.0` | `≥ 100.0` | 2 lần đo liên tiếp vượt ngưỡng |
| **AQI** | — | `≥ 101` | `≥ 151` | 2 lần đo liên tiếp vượt ngưỡng |
| **CO₂** | ppm | `≥ 1000` | `≥ 1500` | 2 lần đo liên tiếp vượt ngưỡng |
| **Tiếng ồn** | dB | `≥ 70.0` | `≥ 85.0` | 2 lần đo liên tiếp vượt ngưỡng |
| **Nhiệt độ** | °C | `≥ 35.0` | `≥ 39.0` | 2 lần đo liên tiếp vượt ngưỡng |
| **Trạng thái trạm** | — | `stale` (> 5 phút) | `offline` (> 10 phút) | Tự động phát hiện qua heartbeat |

---

## 6. AI Agent Geospatial & Cơ chế Grounding

AI Agent của AirGuard AI đóng vai trò như một chuyên gia vi khí hậu thông minh, hỗ trợ cư dân và ban quản lý qua ngôn ngữ tự nhiên.

```
                  ┌────────────────────────────────────────┐
                  │       NGƯỜI DÙNG GỬI CÂU HỎI           │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          CONVERSATION GATE             │
                  │ - Phân loại Xã giao / Mơ hồ / Nghiệp vụ│
                  │ - Kiểm soát an toàn & Lọc nội dung     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          INTENT & ARGUMENT ROUTER      │
                  │ Xác định Intent, Trạm đo, Cự ly, Mode │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          BACKEND TOOL CALLING          │
                  │ - get_current_pm25                     │
                  │ - get_station_history                  │
                  │ - compare_stations                     │
                  │ - get_pm25_forecast                    │
                  │ - create_warning_proposal              │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │       DATA QUALITY & EVIDENCE GATE     │
                  │ - Loại bỏ dữ liệu stale/invalid        │
                  │ - Đảm bảo đủ bằng chứng định lượng     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │         RESPONSE COMPOSER              │
                  │ [Có API Key] -> LLM Grounded Phân tích │
                  │ [Không Key]  -> Deterministic Template │
                  └────────────────────────────────────────┘
```

### Danh mục Ý định (Supported Intents)

1. **Hỏi chỉ số hiện tại**: Tra cứu tức thì AQI và các thông số tại trạm cụ thể hoặc toàn khu đô thị.
2. **So sánh đa trạm**: So sánh vi khí hậu giữa 2 hoặc nhiều phân khu để chọn địa điểm vui chơi.
3. **Dự báo xu hướng**: Xem diễn biến chất lượng không khí trong 1–3 giờ tới hoặc khung giờ vàng ngoài trời.
4. **Tư vấn hoạt động & Sức khỏe**: Đưa ra lời khuyên cá nhân hóa dựa trên nhóm đối tượng (`normal`, `sensitive`, `outdoor_sport`).
5. **Đề xuất lộ trình sạch**: Tìm tuyến đường vận động tối ưu theo vị trí và cự ly mong muốn.
6. **Đề xuất xử lý thiết bị (HITL Proposal)**: Tạo phiếu đề xuất bật hệ thống lọc khí khi phát hiện ô nhiễm kéo dài.

### 4 Nguyên tắc Grounding cốt lõi (Bắt buộc)

- **Không bịa đặt (Zero Hallucination)**: Mọi con số trong câu trả lời phải lấy trực tiếp từ kết quả tool của cùng request.
- **Fail-Closed**: Nếu dữ liệu sensor bị mất, trạm offline hoặc dữ liệu quá cũ (> 5 phút), Agent phải từ chối lịch sự và nêu rõ lý do thay vì tự đoán số.
- **Không tự ý vượt quyền**: Agent không bao giờ tự phê duyệt proposal hoặc gửi lệnh điều khiển thiết bị trực tiếp.
- **Phản hồi tất định khi mất mạng AI**: Khi không có kết nối tới Google Gemini / OpenAI, hệ thống tự động kích hoạt bộ sinh phản hồi tất định (Deterministic Composer) với 100% dữ liệu chính xác.

---

## 7. Thuật toán Tìm đường Thông minh (AQI-Aware Safe Routing)

Khác với các ứng dụng bản đồ thông thường chỉ tìm đường ngắn nhất, AirGuard AI áp dụng thuật toán tìm đường đa mục tiêu, tích hợp mạng lưới giao thông thực tế và bản đồ ô nhiễm không gian.

```
       [ĐIỂM XUẤT PHÁT CỦA CƯ DÂN]
                   │
                   ▼
  [Snap GPS vào Node gần nhất trên mạng vỉa hè OSM]
                   │
                   ▼
  [Tính toán Trọng số Ô nhiễm (Cost) cho từng Đoạn đường]
     Cost = Distance_m × (1 + β × PM2.5_IDW / 50.0)
     * PM2.5_IDW: Nội suy khoảng cách nghịch đảo từ 5 trạm
                   │
                   ▼
  [Thuật toán Dijkstra định hướng Closed-Loop]
     - Lọc theo Activity Profile (Footway/Cycleway)
     - Ép buộc góc rẽ tạo đa giác khép kín
     - Ngăn ngừa quay đầu trên đường cũ (Anti-Retracing)
                   │
                   ▼
  [Tính toán Lượng Bụi mịn Hít vào Cơ thể (Inhaled Mass)]
     Inhaled_Mass_ug = ∑ (PM2.5_edge × Ventilation_Rate × Time_edge)
                   │
                   ▼
  [Xuất Polyline thực tế bám sát 100% Vỉa hè lên Bản đồ]
```

### Cơ sở dữ liệu Đồ thị Đường bộ (Packaged OSM Graph)
Hệ thống đóng gói sẵn tập dữ liệu bản đồ phân giải cao của phân khu Ocean Park 1:
- **Số nút giao (Nodes)**: 8.690 điểm tọa độ.
- **Số đoạn đường (Edges)**: 10.507 đoạn đường liên kết có đầy đủ thuộc tính bề mặt, loại đường (`footway`, `cycleway`, `residential`, `path`).
- **Cam kết chất lượng**: Tuyến đường đạt **Zero-Chord** (không cắt chéo công trình, không đi xuyên lòng hồ).

---

## 8. Quy trình Phê duyệt Con người (HITL) & Audit Log

Để đảm bảo an toàn vận hành, mọi tác vụ can thiệp vào thiết bị lọc khí hoặc phát thanh công cộng đều phải tuân thủ nghiêm ngặt mô hình **Human-in-the-Loop**.

```
[Phát hiện Ô nhiễm kéo dài] ──> [AI Agent tạo Proposal 'pending'] ──> [Gửi Email / Queue Ban Quản Lý]
                                                                               │
                                                                               ▼
[Audit Log ghi nhận lý do] <── [Manager Reject] <── [ĐÁNH GIÁ THỰC TẾ] ──> [Manager Approve]
                                                                               │
                                                                               ▼
[Lưu Audit Log toàn trình] <── [Thiết bị gửi ACK] <── [MQTT Dispatcher phát lệnh]
```

### Các chốt chặn an toàn (Safety Gates)
1. **Gate Điều kiện**: PM2.5 > 50 µg/m³ hoặc CO₂ > 1000 ppm liên tục trong tối thiểu 15 phút.
2. **Gate Dữ liệu**: Dữ liệu không được có khoảng trống (Data gap > 60s) và không được ở trạng thái `stale`.
3. **Gate Xác thực**: Chỉ tài khoản có vai trò `manager` kèm CSRF Token và Idempotency Key mới có quyền phê duyệt.
4. **Audit Bất biến**: Mọi thao tác (Create -> Review -> Approve/Reject -> Dispatch -> ACK) được lưu vào bảng `audit_logs` với `correlation_id` duy nhất.

---

## 9. Báo cáo Môi trường & Bền vững ESG

AirGuard AI tích hợp động cơ tự động tổng hợp báo cáo môi trường phục vụ công tác quản lý đô thị và chứng nhận công trình xanh:
- **Báo cáo Ngày (Daily ESG Report)**: Tự động tổng hợp lúc `00:10` mỗi ngày, tính toán nồng độ trung bình, giá trị đỉnh P90, tỷ lệ bao phủ dữ liệu (`coverage_ratio`) và ma trận phân bổ ô nhiễm 24 giờ.
- **Báo cáo Tuần (Weekly ESG Report)**: Tự động tổng hợp lúc `00:20` sáng thứ Hai, so sánh đối chuẩn với quy chuẩn môi trường **QCVN 05:2023/BTNMT** và khuyến cáo **WHO 2021**.
- **Bảo toàn tính toàn vẹn**: Mỗi bản ghi báo cáo được gắn mã băm SHA-256 (`content_checksum_sha256`), đảm bảo bản xuất Markdown, HTML hoặc PDF hoàn toàn trùng khớp với dữ liệu gốc.

---

## 10. Bộ chỉ số Đánh giá Thực địa (Field Evaluation Metrics)

Dành cho Ban Đánh giá Sản phẩm và Đội ngũ Thẩm định Dự án:

| Nhóm chỉ số | Tên chỉ số | Phương pháp đo đạc & Công thức | Giá trị mục tiêu |
|---|---|---|:---:|
| **Độ chính xác Lộ trình** | **Zero-Chord Rate** | Kiểm tra tỷ lệ đoạn đường cắt chéo lòng hồ/nhà qua 100 truy vấn ngẫu nhiên. | `100%` (Không cắt chéo) |
| | **Loop Closure** | Sai số khoảng cách giữa điểm bắt đầu và điểm kết thúc của vòng lộ trình. | `0 mét` (Khép kín hoàn toàn) |
| | **Exposure Reduction** | Tỷ lệ giảm lượng bụi PM2.5 hít vào so với tuyến đường ngắn nhất: `(1 - Route_Score / Baseline) * 100%` | `≥ 20%` |
| **Độ tin cậy AI Agent** | **Grounding Accuracy** | Tỷ lệ số liệu trong câu trả lời trùng khớp chính xác 100% với Tool Output. | `100%` |
| | **Refusal on Stale** | Tỷ lệ Agent từ chối trả lời khi cố tình ngắt dữ liệu trạm đo. | `100%` |
| **Hiệu năng Hệ thống** | **Route Engine Latency** | Thời gian tính toán và trả về lộ trình bám mạng vỉa hè OSM. | `< 500 ms` |
| | **Agent Chat Latency** | Thời gian phản hồi câu hỏi (FastAPI Proxy + LLM / Composer). | `< 2.5 giây` |
| | **Pipeline Freshness** | Độ trễ từ khi Simulator phát MQTT đến khi hiển thị trên Dashboard. | `< 2.0 giây` |

---

## 11. Hướng dẫn Cài đặt & Khởi chạy (A–Z)

### Yêu cầu tiên quyết
- **Docker Desktop** (bản mới nhất hỗ trợ Docker Compose v2).
- Tối thiểu **4 GB RAM** khả dụng và 5 GB dung lượng ổ đĩa trống.
- Kết nối Internet ổn định để tải các base image Docker.

### Bước 1: Sao chép mã nguồn và cấu hình môi trường
```bash
# Clone repository
git clone https://github.com/AI20K-Build-Phase-Cohort-3/P-074.git
cd P-074

# Tạo file cấu hình môi trường từ mẫu
# Trên Windows PowerShell:
Copy-Item .env.example .env

# Trên Linux/macOS:
cp .env.example .env
```

### Bước 2: Điền cấu hình API Key (Tùy chọn)
Mở file `.env` và cập nhật các khóa dịch vụ (nếu có):
```env
# Khóa Gemini AI (để kích hoạt phản hồi diễn giải tự nhiên từ Google Gemini)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# Khóa Resend (nếu muốn gửi email thông báo sự cố thực tế)
NOTIFICATION_PROVIDER=resend
RESEND_API_KEY=your_resend_api_key_here
RESEND_FROM_EMAIL=airguard@yourdomain.com
```
*(Nếu không điền key, hệ thống vẫn hoạt động bình thường nhờ cơ chế Fallback tất định).*

### Bước 3: Khởi động hệ thống bằng Docker Compose
```bash
# Xây dựng và khởi chạy toàn bộ 7 container dịch vụ
docker compose up -d --build

# Kiểm tra trạng thái hoạt động của các container
docker compose ps
```

**Bảng cổng dịch vụ cục bộ:**
| Dịch vụ | Địa chỉ truy cập | Ghi chú |
|---|---|---|
| **Dashboard UI** | `http://localhost:5173` | Giao diện React điều khiển trung tâm |
| **Backend REST API** | `http://localhost:8000/api/v1` | Cổng API chính của hệ thống |
| **Tài liệu OpenAPI (Swagger)** | `http://localhost:8000/docs` | Giao diện thử nghiệm API trực quan |
| **Kiểm tra sức khỏe Backend** | `http://localhost:8000/ready` | Trả về trạng thái kết nối DB và Redis |
| **AI Agent Service** | `http://localhost:8001/health` | Sức khỏe của Agent container |
| **PostgreSQL Database** | `localhost:5432` | Người dùng: `postgres` / Mật khẩu: trong `.env` |
| **Mosquitto MQTT Broker** | `localhost:1883` | Cổng tiếp nhận dữ liệu telemetry |

### Bước 4: Khởi chạy Async Workers & Celery Beat (Tùy chọn cho Báo cáo & Email)
```powershell
# Bật thêm Profile xử lý nền
$env:CELERY_TASK_ALWAYS_EAGER="false"
docker compose --profile async-jobs up -d --build
```

### Bước 5: Dừng hệ thống
```bash
# Dừng các dịch vụ, bảo toàn dữ liệu trong Database
docker compose down

# Dừng và xóa toàn bộ dữ liệu để làm mới hoàn toàn
docker compose down -v
```

---

## 12. Danh mục API Reference

Tất cả các endpoint API chính thức đều bắt đầu bằng tiền tố `/api/v1`.

### 1. Nhóm Dữ liệu Môi trường & Trạm đo
- `GET /stations`: Lấy snapshot trạng thái và số liệu mới nhất của cả 5 trạm.
- `GET /stations/{id}/current`: Lấy chi tiết số liệu tức thời của trạm `{id}` (ví dụ: `S01`, `S03`).
- `GET /stations/{id}/history?hours=24`: Lấy chuỗi lịch sử đo lường trong khoảng thời gian xác định.
- `POST /stations/compare`: Gửi danh sách mã trạm `{"station_ids": ["S01", "S03"]}` để so sánh.
- `GET /stations/{id}/forecast?hours=3&metric=aqi`: Lấy dự báo xu hướng trong 1–3 giờ tới.

### 2. Nhóm Cảnh báo & Đề xuất (Alerts & HITL)
- `GET /alerts?status=active`: Danh sách các cảnh báo môi trường đang có hiệu lực.
- `POST /proposals`: Tạo phiếu đề xuất kích hoạt thiết bị (bắt đầu ở trạng thái `pending`).
- `GET /approvals`: (Manager) Lấy danh sách đề xuất đang chờ phê duyệt.
- `POST /approvals/{id}/approve`: (Manager) Phê duyệt đề xuất và phát lệnh MQTT.
- `POST /approvals/{id}/reject`: (Manager) Từ chối đề xuất và ghi lý do vào Audit Log.
- `GET /audit-logs`: (Manager) Truy vấn toàn bộ lịch sử thao tác hệ thống.

### 3. Nhóm AI Agent & Lộ trình Vận động
- `POST /agent/chat`: Gửi câu hỏi cho AI Agent kèm vị trí bản đồ hiện tại.
- `POST /routes/clean-running`: Tính toán lộ trình sạch (Chạy bộ / Đi bộ / Đạp xe).
- `POST /exposure/inhaled-mass`: Tính toán lượng bụi mịn hít vào cơ thể theo thông số vận động.

**Ví dụ Payload gọi AI Agent Chat:**
```json
POST /api/v1/agent/chat
Content-Type: application/json

{
  "user_id": "resident-oceanpark-01",
  "message": "Tìm cho tôi tuyến chạy bộ 3km quanh hồ Ngọc Trai sạch nhất bây giờ",
  "map_context": {
    "user_location": {
      "lat": 20.9940,
      "lng": 105.9410,
      "source": "gps"
    },
    "activity_mode": "running"
  }
}
```

---

## 13. Cấu hình Biến môi trường (.env)

| Tên biến | Kiểu dữ liệu | Giá trị mặc định | Giải thích chi tiết |
|---|:---:|:---:|---|
| `LLM_PROVIDER` | string | `auto` | Cơ chế chọn AI: `auto` (ưu tiên Gemini), `gemini`, `openai`. |
| `GEMINI_API_KEY` | string | `""` | Khóa API của Google AI Studio (bảo mật, không commit). |
| `GEMINI_MODEL` | string | `gemini-3.6-flash` | Định danh mô hình AI của Google. |
| `DATABASE_URL` | string | `postgresql://...` | Chuỗi kết nối đến PostgreSQL nội bộ hoặc ngoài. |
| `MQTT_HOST` | string | `mqtt` | Địa chỉ máy chủ MQTT broker (Mosquitto). |
| `SENSOR_SCENARIO` | string | `normal` | Kịch bản mô phỏng: `normal`, `rush-hour`, `spike`, `recovery`, `station-silence`. |
| `SENSOR_INTERVAL_SECONDS` | integer | `10` | Chu kỳ phát dữ liệu đo của simulator (giây). |
| `STALE_AFTER_SECONDS` | integer | `300` | Thời gian tối đa trước khi đánh dấu dữ liệu bị cũ (5 phút). |
| `ALERT_CONSECUTIVE_MEASUREMENTS` | integer | `2` | Số mẫu đo liên tiếp vượt ngưỡng để kích hoạt cảnh báo. |
| `AUTO_PROPOSAL_ENABLED` | boolean | `true` | Tự động tạo đề xuất HITL khi phát hiện ô nhiễm kéo dài. |
| `NOTIFICATION_PROVIDER` | string | `disabled` | Dịch vụ gửi email: `disabled` hoặc `resend`. |
| `REPORT_TIMEZONE` | string | `Asia/Ho_Chi_Minh` | Múi giờ chuẩn để tính toán chu kỳ báo cáo ESG. |

---

## 14. Quy trình Kiểm thử & Đảm bảo chất lượng

### Chạy kiểm thử tự động Backend (Pytest)
```powershell
# Kích hoạt môi trường ảo Python
.\.venv\Scripts\Activate.ps1

# Chạy toàn bộ 100+ bài kiểm thử tích hợp và đơn vị
pytest tests/ -v

# Chạy riêng nhóm kiểm thử AI Agent và Geospatial Router
pytest tests/test_backend/test_geospatial_agent.py -v
pytest tests/test_backend/test_clean_running_route.py -v

# Kiểm tra quy chuẩn mã nguồn (Linting)
ruff check src tests backend
```

### Chạy kiểm thử Frontend & Đóng gói (Vite Build)
```powershell
Set-Location frontend
npm ci
npm run build
```

---

## 15. Cấu trúc Thư mục Dự án

```
P-074/
├── backend/                       # Ứng dụng chính FastAPI Backend
│   ├── app/
│   │   ├── main.py                # Điểm khởi chạy REST API và định tuyến router
│   │   ├── services/
│   │   │   ├── geospatial_agent_service.py    # Điều phối AI Agent & Intent Resolver
│   │   │   ├── road_graph_router.py           # Động cơ định tuyến đồ thị OSM (10.5k cạnh)
│   │   │   ├── clean_running_route_service.py # Tính toán phơi nhiễm & đề xuất lộ trình
│   │   │   ├── environmental_scoring.py       # Chấm điểm chất lượng vi khí hậu IDW
│   │   │   ├── alert_engine.py                # Rule Engine cảnh báo đa chỉ số
│   │   │   ├── forecast_service.py            # Dự báo xu hướng ngắn hạn 1-3h
│   │   │   └── esg_report_service.py          # Tổng hợp báo cáo ESG định kỳ
│   │   └── schemas/               # Pydantic schemas cho dữ liệu vào/ra
│   ├── db/
│   │   ├── schema.sql             # Cấu trúc bảng PostgreSQL khởi tạo
│   │   └── seed.sql               # Dữ liệu ban đầu về 5 trạm và người dùng demo
│   ├── data/                      # Bản đồ đường bộ đóng gói
│   │   └── ocean-park-1-pedestrian-graph.json
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                      # Ứng dụng giao diện người dùng React + Vite
│   ├── src/
│   │   ├── App.tsx                # Component gốc điều phối trạng thái
│   │   ├── features/
│   │   │   ├── map/               # Bản đồ Leaflet, lớp nhiệt AQI, trạm đo
│   │   │   ├── drawers/           # Hộp hội thoại AI Agent thông minh
│   │   │   ├── alerts/            # Bảng danh sách cảnh báo thời gian thực
│   │   │   └── approvals/         # Giao diện phê duyệt HITL cho Quản lý
│   │   └── styles.css             # Hệ thống CSS chuẩn hóa
│   ├── package.json
│   └── Dockerfile
│
├── services/                      # Các microservices phụ trợ
│   ├── sensor-simulator/          # Bộ mô phỏng phát dữ liệu MQTT 5 trạm
│   ├── mqtt-consumer/             # Bộ tiếp nhận, kiểm tra dữ liệu và lưu DB
│   └── device-simulator/          # Bộ mô phỏng thiết bị thông gió (nhận lệnh HITL)
│
├── infra/
│   └── mqtt/mosquitto.conf        # Cấu hình máy chủ MQTT Mosquitto
│
├── tests/                         # Bộ kiểm thử tự động toàn diện
├── specs/                         # Đặc tả hợp đồng API, MQTT và Domain Model
├── adrs/                          # Hồ sơ quyết định kiến trúc (Architecture Decision Records)
├── docs/                          # Tài liệu hướng dẫn vận hành, PRD và Runbook
├── docker-compose.yml             # Cấu hình triển khai cục bộ (Local Development)
├── docker-compose.public-demo.yml # Cấu hình triển khai máy chủ đám mây (Azure)
├── .env.example                   # Mẫu khai báo biến môi trường
├── AGENTS.md                      # Hướng dẫn bàn giao cho AI Agent cộng tác
└── README.md                      # Tài liệu tổng quan dự án (File này)
```

---

## 16. Xử lý sự cố thường gặp (Troubleshooting)

### 1. Lỗi Docker Build dừng ở bước `pip install`
- **Nguyên nhân**: Do sự cố mạng hoặc tường lửa chặn kết nối tới kho gói `pypi.org`.
- **Cách xử lý**:
  ```bash
  docker compose build backend --no-cache --progress=plain
  ```
  Kiểm tra kết nối mạng của Docker Desktop trong mục `Settings -> Resources -> Network`.

### 2. Dashboard không hiển thị chỉ số của trạm đo
- **Nguyên nhân**: Container `sensor-simulator` hoặc `mqtt-consumer` chưa khởi động xong.
- **Cách kiểm tra**:
  ```bash
  docker compose logs -f sensor-simulator
  docker compose logs -f mqtt-consumer
  ```
  Đảm bảo sau 10–20 giây có log dạng `[PERSIST] Inserted measurement for station S01`.

### 3. AI Agent phản hồi câu trả lời mặc định (Fallback)
- **Nguyên nhân**: Chưa điền `GEMINI_API_KEY` trong file `.env` hoặc hạn mức gọi API bị tạm dừng.
- **Hiện tượng bình thường**: Hệ thống được thiết kế chủ động dùng **Deterministic Composer** để luôn đảm bảo tính sẵn sàng cao, số liệu trả về vẫn chính xác 100% từ trạm.

---

## 17. Giới hạn đã biết & Lộ trình phát triển

| Hạng mục | Hiện trạng (MVP v0.3) | Lộ trình nâng cấp (Production) |
|---|---|---|
| **Cảm biến đầu vào** | Dữ liệu mô phỏng từ Simulator (`source=simulator`) | Tích hợp trạm phần cứng IoT thực tế sử dụng chip ESP32 + cảm biến Sensirion |
| **Công thức AQI** | AQI dẫn xuất từ nồng độ PM2.5 (US EPA 2012) | Bổ sung đầy đủ các cảm biến khí O₃, NO₂, SO₂, CO theo chuẩn QCVN |
| **Dự báo ô nhiễm** | Mô hình đường xu hướng tuyến tính kết hợp Additive Fourier | Triển khai mô hình học sâu chuỗi thời gian (LSTM / Prophet / Temporal Fusion) |
| **Mô hình Lan truyền** | Bản đồ nhiệt nội suy IDW trực quan | Ứng dụng mô hình lan truyền khói bụi chuẩn Gaussian Plume Model |
| **Xác thực người dùng** | Mô phỏng danh tính Demo Role (`resident`, `manager`) | Tích hợp SSO, OAuth2 / OIDC và phân quyền RBAC đa cấp độ |

---

## 👥 Đội ngũ Phát triển Dự án

**Dự án P-074 — AI20K Build Phase Cohort 3**  
*Đổi mới sáng tạo vì một môi trường đô thị thông minh và khỏe mạnh*  
Khu đô thị Vinhomes Ocean Park 1, Đa Tốn, Gia Lâm, Hà Nội

Runtime entry points:

- Backend: `backend/app/main.py`
- Frontend: `frontend/src/main.tsx` → `frontend/src/App.tsx`
- Agent: `src/main.py`
- Simulator: `services/sensor-simulator/sensor_simulator.py`
- Consumer: `services/mqtt-consumer/mqtt_consumer/main.py`
- Device simulator: `services/device-simulator/device_simulator.py` chạy một instance cho mỗi thiết bị
  đã đăng ký (`FILTER-S01`, `FILTER-01`, `FILTER-02`, `FILTER-04`, `FILTER-05`); ACK chỉ xác nhận
  thiết bị cùng `device_id` đã nhận command.

## Tài liệu liên quan

- [AGENTS.md](AGENTS.md): handoff và nguyên tắc coding agent.
- [Quy định chức năng sản phẩm](docs/functional-requirements.md): phạm vi, vai trò, luồng xử lý, ngoại lệ và điều kiện nghiệm thu của bản cuối.
- [Manual test checklist](docs/manual-test-checklist.md): test case và nơi ghi evidence nghiệm thu.
- [Testing submission pack](docs/submission/testing/README.md): báo cáo kiểm thử tổng hợp, defects, manual sign-off và evidence index.
- [PRD](docs/Gate%201/PRD.md): yêu cầu sản phẩm hiện hành.
- [API contracts](specs/api-contracts.md).
- [Weekly Mentor Duty logs](docs/submission/weekly-logs/README.md): báo cáo Done/Doing/Blocked và kế hoạch theo từng tuần của nhóm T-074.
- [Data contracts](specs/data-contracts.md).
- [Domain model](specs/domain-model.md).
- [Agent evaluation](docs/agent-evaluation.md).
- [Demo runbook](docs/demo-runbook.md).
- [ADR forecast](adrs/0007-short-term-trend-forecast.md).
- [ADR multi-metric alerts](adrs/0009-multi-metric-environmental-alerts.md).

## Known limitations

- Sensor là simulator. Weather dùng Open-Meteo khi `WEATHER_API_BASE_URL` được cấu hình và tự hạ cấp sang fallback có nhãn khi provider lỗi.
- AQI là PM2.5 sub-index đơn giản, chưa phải official AQI/NowCast.
- Forecast là baseline trend, chưa có Prophet/LSTM/backtesting production.
- Heat zones không phải mô hình lan truyền ô nhiễm khoa học.
- Threshold CO₂/noise/temperature cần mentor/operations xác nhận.
- Authentication/RBAC frontend còn ở mức demo.
- Resend và async worker production cần cấu hình hạ tầng/secret riêng.
- Graph tuyến chạy là `curated_demo_graph`, không phải snapshot OSM live; người dùng phải tự kiểm tra điều kiện đường thực tế.

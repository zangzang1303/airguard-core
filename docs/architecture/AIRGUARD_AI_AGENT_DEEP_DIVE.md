# 🧠 BẢN MÔ TẢ CHUYÊN SÂU VỀ AI AGENT (AIRGUARD AI AGENT DEEP-DIVE)
> **Mã tài liệu:** `AIRGUARD-AI-AGENT-DEEP-DIVE-2026`  
> **Dự án:** AirGuard AI — Hệ Thống Giám Sát Vi Khí Hậu, Định Tuyến Thể Thao Sạch & Điều Khiển Thiết Bị Đô Thị Thông Minh (P-074)  
> **Đơn vị:** AI20K Build Phase Cohort 3  
> **Thời điểm ban hành:** 03/09/2026 (Live on Azure Cloud VM)

---

## 1. BẢN CHẤT CỦA AI AGENT TRONG AIRGUARD AI LÀ GÌ?

Trong hệ thống AirGuard AI, **AI Agent không phải là một Chatbot thông thường** (chỉ đơn giản là gửi prompt văn bản vào LLM rồi nhận lại câu trả lời).  
AI Agent của chúng tôi là một **Hệ Thống Tác Tử Đa Nhiệm Không Gian — Đàm Thoại (Geospatial & Conversational Multi-Agent System)**, đóng vai trò là **"Bộ não điều phối trung tâm"** của toàn bộ khu đô thị Vinhomes Ocean Park 1:

1. **Hiểu Ngữ Cảnh Không Gian Đô Thị (Spatial Awareness):** Agent nắm rõ tọa độ địa lý của 5 trạm quan trắc (S01–S05), vị trí các phân khu (Sapphire, Ruby, San Hô, VinUni, Biển Hồ nước mặn 6.1 ha, Hồ Ngọc Trai 24.5 ha) và đồ thị giao thông hơn 10,500 cạnh đường thực OpenStreetMap (OSM).
2. **Hiểu Ngữ Cảnh Thời Gian (Temporal Resolution):** Agent tự động phân giải các mốc thời gian trong câu hỏi tự nhiên của cư dân ("lúc này", "1 giờ nữa", "chiều nay 17h", "sáng mai 6h").
3. **Có Bộ Công Cụ Nghiệp Vụ Riêng (Tool Calling):** Agent có thẩm quyền truy vấn dữ liệu quan trắc thực tế, chạy mô hình dự báo chuỗi thời gian, gọi thuật toán định tuyến đồ thị và tạo đề xuất điều khiển thiết bị dập bụi.
4. **Điều Khiển Ngược Lại Giao Diện Bản Đồ (Declarative Map Actions):** Câu trả lời của Agent không chỉ dừng lại ở câu chữ, mà kèm theo các lệnh điều khiển bản đồ Leaflet (`flyTo` trạm đo, `toggleHeatmap`, `drawRoutePolyline` vẽ đường chạy xanh trực tiếp lên màn hình người dùng).

---

## 2. KIẾN TRÚC 5 PHÂN TẦNG CỦA AI AGENT (AGENT LIFECYCLE PIPELINE)

AI Agent được xây dựng theo mô hình máy trạng thái hữu hạn (Finite State Machine) trên nền tảng **LangGraph** kết hợp **FastAPI Core**:

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LUỒNG XỬ LÝ 5 TẦNG CỦA AIRGUARD AI AGENT                                │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘

 [ Câu hỏi người dùng: "Tôi muốn chạy bộ 5km quanh hồ lúc này cho người nhạy cảm" ]
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 1: CONVERSATIONAL GATE & INTENT CLASSIFIER (Chặn ngoài biên & Phân loại ý định)                  │
 │ • Chặn lời chào (greeting), xã giao (smalltalk), câu hỏi danh tính ("bạn là ai", "bạn bao tuổi")     │
 │   ➔ Trả lời ngay lập tức bằng template nội bộ trong < 5ms (KHÔNG tốn chi phí gọi LLM, không đọc DB). │
 │ • Nhận diện câu hỏi nghiệp vụ môi trường / thể thao ➔ Chuyển vào Tầng 2.                             │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 2: SPATIAL & TEMPORAL RESOLVER (Giải mã Không gian & Thời gian)                                 │
 │ • Spatial Registry: Chuẩn hóa "quanh hồ" ➔ Tọa độ Hồ Ngọc Trai (Trạm S03: 20.9925, 105.9430).        │
 │ • Temporal Resolver: Chuẩn hóa "lúc này" ➔ Mốc thời gian thực hiện tại (Realtime Snapshot).          │
 │ • Health Context: Nhận diện thể trạng "người nhạy cảm" ➔ Ngưỡng lọc bụi khắt khe (AQI ≤ 50).        │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 3: LANGGRAPH STATE MACHINE & TOOL EXECUTION (Máy trạng thái & Gọi công cụ)                      │
 │                                                                                                      │
 │   [route_node] ➔ [execute_tools_node] ➔ [compose_node] ➔ [generate_explanation] ➔ [trace_node]      │
 │                                                                                                      │
 │ • Agent quyết định gọi công cụ: `compute_clean_running_route(lat, lng, target_km=5.0, profile)`      │
 │ • Kích hoạt thuật toán độc quyền: 2-Leg Penalized Dijkstra trên đồ thị OSM (>10,500 cạnh).           │
 │ • Phạt 30x chiều về ➔ Sinh đường chạy khép kín 0% lặp đường cũ, giảm 45% bụi hít vào.               │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 4: GROUNDING POLICY GATE (Cổng Kiểm Soát Căn Cứ — Cam Kết Zero Hallucination)                   │
 │ • Nguyên tắc cốt tử: "Grounding trước Fluency" — Tuyệt đối không bịa đặt số liệu.                    │
 │ • Phân tích cú pháp: Bóc tách 100% token số liệu (AQI, PM2.5, cự ly km, liều lượng bụi ug).         │
 │ • Cross-check: Đối chiếu với kết quả Tool Calling từ DB PostgreSQL SoR trong cùng request.           │
 │ • Nếu phát hiện số liệu không có căn cứ ➔ REJECT ngay và thay thế bằng dữ liệu gốc.                  │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ TẦNG 5: DETERMINISTIC FALLBACK SWITCHER (Bộ Chuyển Mạch Tiền Định — Chống Sập Hệ Thống)              │
 │ • Nếu LLM bên ngoài (OpenAI/Gemini) bị timeout (> 8.0s) hoặc lỗi HTTP 429/500:                       │
 │   ➔ Tự động kích hoạt Local Deterministic Template Generator.                                        │
 │   ➔ Trả lời người dùng trong < 500ms dựa trên dữ liệu trạm gần nhất ➔ Cam kết 0% lỗi HTTP 5xx.       │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
 [ Phản hồi trả về UI: Lời khuyên cá nhân hóa + Vẽ Polyline đường chạy xanh trên bản đồ Leaflet ]
```

---

## 3. HỆ THỐNG CÔNG CỤ CỦA AGENT (AGENT TOOL REGISTRY)

Agent không bao giờ tự "suy diễn" số liệu mà bắt buộc phải gọi thông qua **Hệ thống 5 Công Cụ Nghiệp Vụ Chuẩn Hóa**:

| Tên Công Cụ (Tool Name) | Đầu Vào (Inputs) | Đầu Ra (Outputs) | Nhiệm Vụ Nghiệp Vụ |
|---|---|---|---|
| `get_current_pm25` | `station_id` | Nồng độ PM2.5, AQI, Nhiệt độ, CO2, Trạng thái trạm | Lấy thông tin vi khí hậu thời gian thực tại trạm chỉ định. |
| `get_forecast` | `station_id`, `hours` (1-24) | Mảng dự báo theo từng giờ, cận trên/cận dưới | Truy xuất kết quả dự báo ô nhiễm từ mô hình Additive Fourier/Prophet. |
| `calculate_idw_heatmap` | `bounds`, `resolution=60` | Ma trận 60x60 nồng độ bụi nội suy không gian | Tạo bản đồ nhiệt vi khí hậu có trọng số hướng gió thời gian thực. |
| `compute_clean_running_route` | `start_lat`, `start_lng`, `target_km`, `health_profile` | Tọa độ Polyline, Cự ly thực tế, % Trùng lặp (0.0%), Liều lượng bụi hít vào ($\mu g$) | Gọi động cơ 2-Leg Dijkstra định tuyến đường chạy sạch tuần hoàn. |
| `propose_warning_and_mitigation` | `station_id`, `reason`, `device_id` | `proposal_id`, Trạng thái `pending`, Thẻ bằng chứng (Evidence Card) | Tạo đề xuất cảnh báo và bật máy lọc dập bụi gửi lên Cổng HITL cho BQL duyệt. |

---

## 4. HAI CƠ CHẾ KỸ THUẬT "ĐÁNG TIỀN NHẤT" CỦA AGENT

### 🌟 Cơ Chế 1: "Grounding Trước Fluency" (Zero-Hallucination)
* **Vấn đề trong y tế & sức khỏe:** Nếu một LLM trả lời *"Hôm nay không khí tại Sapphire rất tốt, AQI chỉ 15"* trong khi thực tế AQI là 160, người già và trẻ em ra ngoài sẽ bị viêm phế quản cấp. Ảo giác môi trường là điều cấm kỵ tuyệt đối.
* **Cách AirGuard AI giải quyết:**
  - Mọi câu trả lời sau khi LLM sinh ra đều phải đi qua **`GroundingPolicyGate`**.
  - Thuật toán dùng Regex và AST Parser để bóc toàn bộ thực thể số: ví dụ nhận diện chuỗi `AQI = 45`, `PM2.5 = 12 µg/m³`.
  - Đối chiếu tức thì: Các giá trị này có nằm trong JSON context mà Tool vừa trả về không?
  - Nếu câu trả lời bịa số $\to$ Cổng kiểm soát sẽ gạt bỏ câu trả lời của LLM và kích hoạt template chuẩn hóa lấy trực tiếp từ DB.
  - **Kết quả kiểm thử:** Đạt **100.0% Grounding Accuracy** trên 87 bài test thực tế ([`technical_metrics_evaluation.md`](../docs/metrics/technical_metrics_evaluation.md)).

### 🌟 Cơ Chế 2: Bộ Chuyển Mạch Tiền Định (Deterministic Fallback Switcher)
* **Vấn đề trong thực tế:** Các API LLM đám mây (OpenAI, Gemini) thường xuyên bị nghẽn mạng, quá tải (Rate Limit 429) hoặc thời gian phản hồi kéo dài 10–15 giây vào giờ cao điểm.
* **Cách AirGuard AI giải quyết:**
  - Thiết lập bộ đếm thời gian nghiêm ngặt: **Timeout = 8.0 giây**.
  - Nếu sau 8.0s LLM chưa hoàn thành hoặc xảy ra lỗi mạng $\to$ Hệ thống ngắt luồng và kích hoạt **`Deterministic Fallback`**.
  - Bộ chuyển mạch cục bộ sử dụng các mẫu câu tiền định đã được lập trình sẵn, tự động điền dữ liệu thực tế từ trạm đo gần nhất.
  - **Thời gian phản hồi:** **Dưới 500ms**.
  - **Ý nghĩa:** Cam kết **0% lỗi HTTP 5xx**, ứng dụng trên trình duyệt của cư dân không bao giờ bị "treo" hay báo lỗi sập server.

---

## 5. THUẬT TOÁN ĐỊNH TUYẾN CHẠY BỘ SẠCH 2-LEG PENALIZED DIJKSTRA

* **Mục tiêu:** Sinh ra cung đường chạy bộ thể thao vừa vặn cự ly (ví dụ: 5km), khép kín tuần hoàn (xuất phát ở đâu về đúng ở đó), **0% lặp lại đường cũ**, và có nồng độ bụi phơi nhiễm thấp nhất.
* **Thuật toán 3 bước độc quyền:**
  1. **Chặng Đi ($S \to W$):** Tìm đường ngắn nhất đến điểm trung chuyển $W$ ven hồ có chất lượng không khí tốt:
     $$\text{Cost}(e) = \text{Length}(e) \times (1 + \alpha \cdot \text{AQI}(e))$$
  2. **Chặng Về Phạt Trọng Số ($W \to S$):** Phạt gấp **30 lần ($30\times$)** trọng số tất cả các cạnh đã đi ở chặng 1:
     $$\text{Cost}'(e) = \text{Cost}(e) \times 30^{\mathbb{I}(e \in \text{Leg 1})}$$
     Thuật toán buộc phải tìm cung đường mới ven hồ khác để quay về đích.
  3. **Tích phân liều lượng bụi mịn hít vào ($M_{\text{inhaled}}$):**
     $$M_{\text{inhaled}} = \int_{0}^{T} C(x(t)) \cdot V_E \, dt \quad (\mu g)$$
     Chia nhỏ tuyến đường thành các phân đoạn 35m để tích phân nồng độ bụi dựa theo Pace và nhịp thở của runner $\to$ **Giảm 35.4% đến 45.0% lượng bụi mịn hít vào phổi!**

---

## 6. TÓM TẮT 3 CÂU "ĐINH" VỀ AI AGENT ĐỂ BẠN NÓI KHI THUYẾT TRÌNH

1. *"AI Agent của AirGuard AI không phải là chatbot hỏi đáp thông thường, mà là một **Tác tử Không gian - Đàm thoại (Geospatial Agent)** có khả năng hiểu bản đồ, phân tích chuỗi thời gian và điều khiển trực tiếp giao diện GIS của cư dân."*
2. *"Chúng tôi áp dụng nguyên tắc an toàn cao nhất: **'Grounding trước Fluency'** — 100% số liệu vi khí hậu phát ngôn ra đều có căn cứ xác thực từ cơ sở dữ liệu, đảm bảo **Zero Hallucination (0% bịa đặt)**."*
3. *"Và trong kịch bản thể thao, Agent tích hợp **thuật toán độc quyền 2-Leg Penalized Dijkstra** trên đồ thị hơn 10,500 cạnh OSM, tự động sinh ra cung đường chạy tuần hoàn **đúng 0.0% trùng lặp đường cũ** và **giúp giảm 45% lượng bụi mịn hít vào phổi**!"*

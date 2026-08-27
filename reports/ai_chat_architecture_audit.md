# BÁO CÁO ĐÁNH GIÁ HỆ THỐNG AI CHAT (AIRGUARD AI)

> **Thời điểm lập:** 2026-08-27T09:56:00+07:00  
> **Phiên bản:** AirGuard AI v1.0.0 Architecture Review  
> **Tác giả:** Technical Lead / Solution Architect  

> **P0 verification — 2026-08-27:** The architecture description below captured the pre-P0
> explanation path, but its claim that the provider added an explanation did not match the code at
> review time: provider output was discarded while the deterministic answer was returned and
> mislabeled `live_llm`. P0 removes that call. Production social and deterministic domain requests
> now use zero LLM calls; only bounded semantic-router fallback may use one call. The current
> automatic proposal worker likewise invokes one deterministic grounded proposal workflow, replacing
> the former provider-preflight plus proposal double invocation.

---

## Danh mục Tài liệu & Mã nguồn Tham chiếu

### Mã nguồn Logic AI Chat:
- Backend Gateway API & Router: [`backend/app/main.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/main.py#L950-L1080) (`/api/v1/agent/chat`)
- Conversational Gate & Intent Classifier: [`backend/app/services/conversational_agent_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/conversational_agent_service.py)
- Geospatial Agent Service: [`backend/app/services/geospatial_agent_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/geospatial_agent_service.py)
- HTTP Proxy Boundary to Isolated Agent: [`backend/app/services/agent_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/agent_service.py)
- Automatic Warning Proposal Service: [`backend/app/services/automatic_proposal_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/automatic_proposal_service.py)
- Isolated LangGraph Agent Package: [`src/agents/graph.py`](file:///d:/Ai_Thuc_Chien/P-074/src/agents/graph.py), [`src/agents/response_composer.py`](file:///d:/Ai_Thuc_Chien/P-074/src/agents/response_composer.py), [`src/agents/policies/grounding.py`](file:///d:/Ai_Thuc_Chien/P-074/src/agents/policies/grounding.py), [`src/agents/policies/recommendations.py`](file:///d:/Ai_Thuc_Chien/P-074/src/agents/policies/recommendations.py)
- Frontend AI Chat Interface: [`frontend/src/features/agent/AgentChat.tsx`](file:///d:/Ai_Thuc_Chien/P-074/frontend/src/features/agent/AgentChat.tsx), [`frontend/src/features/drawers/AiAssistantDrawer.tsx`](file:///d:/Ai_Thuc_Chien/P-074/frontend/src/features/drawers/AiAssistantDrawer.tsx)

### Tài liệu Báo cáo & Đặc tả Tích hợp:
- [`reports/agent_baseline.md`](file:///d:/Ai_Thuc_Chien/P-074/reports/agent_baseline.md) (Báo cáo Baseline Kiểm thử AI Agent)
- [`reports/agent_audit.md`](file:///d:/Ai_Thuc_Chien/P-074/reports/agent_audit.md) (Báo cáo Audit & Sửa Tận Gốc AI Agent)
- [`reports/agent_eval.json`](file:///d:/Ai_Thuc_Chien/P-074/reports/agent_eval.json) (Báo cáo Đánh giá 25 Golden Cases)
- [`adrs/0004-agent-design.md`](file:///d:/Ai_Thuc_Chien/P-074/adrs/0004-agent-design.md), [`adrs/0010-automatic-agent-proposals.md`](file:///d:/Ai_Thuc_Chien/P-074/adrs/0010-automatic-agent-proposals.md), [`adrs/0012-bounded-social-conversation.md`](file:///d:/Ai_Thuc_Chien/P-074/adrs/0012-bounded-social-conversation.md)
- [`tasks/ai-agent.md`](file:///d:/Ai_Thuc_Chien/P-074/tasks/ai-agent.md) (Task list AI Agent AI-001 $\rightarrow$ AI-006)

---

### 1. Kiến trúc & Luồng hoạt động hiện tại (Current Architecture)

#### 1.1 Tóm tắt Luồng dữ liệu (Data Flow) và Logic xử lý chính
Luồng xử lý yêu cầu hội thoại AI Chat trải qua mô hình phân tầng nghiêm ngặt (Fail-closed & Tool-grounded Architecture):

```text
User Input / Map Context / Selected Station
  │
  ▼
[1. Conversational Agent Gate] (conversational_agent_service.py)
  ├── Phân loại Intent: domain | greeting | social | clarification | out_of_scope
  └── Nếu là greeting / social: Trả về kết quả Deterministic ngay lập tức (KHÔNG gọi LLM hay Telemetry)
  │
  ▼ (Nếu là domain query)
[2. Backend Gateway & Profile Context] (main.py)
  ├── Xác thực Profile người dùng (user_group: normal | sensitive | outdoor_sport)
  ├── Giải mã thời gian qua Temporal Resolver ("hiện tại" vs "tối nay / 18:00")
  └── Chuyển tiếp Request qua HTTP Client tới Isolated Agent Microservice (:8001)
  │
  ▼
[3. Isolated Agent State Graph Execution] (src/agents/graph.py)
  ├── Router Node: Semantic Router / Lexicon Matcher (xác định Intent & Tool Arguments)
  ├── Tool Execution Node: Đọc dữ liệu Telemetry chuẩn từ Backend API (Live / Forecast / History)
  ├── Response Composer Node: Tổng hợp câu trả lời Deterministic Grounded theo bảng Rule cá nhân hóa sức khỏe
  ├── Semantic fallback (optional): tối đa một provider call chỉ để trả JSON route đã validate
  └── Audit Trace Node: Lưu log giám sát (request_id, used_tools, latency, outcome)
  │
  ▼
[4. Map Action Controller & Frontend Rendering] (geospatial_agent_service.py & AgentChat.tsx)
  ├── Tổng hợp Declarative Map Actions (highlight_point, highlight_route, fit_bounds)
  └── Render giao diện AI Chat trên React + Leaflet AI Layer
```

#### 1.2 Các Module, Service & API Bên ngoài Tích hợp
- **Multi-provider LLM Adapter** ([`src/services/llm.py`](file:///d:/Ai_Thuc_Chien/P-074/src/services/llm.py)): optional semantic-router adapter; production answer/proposal generation không dùng provider.
- **Spatial Fourier heuristic** ([`backend/app/services/prophet_forecast_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/prophet_forecast_service.py)): module tên legacy chỉ phục vụ timeline heatmap không gian 1–24h; đây không phải Prophet/ML đã huấn luyện. Forecast canonical của API/Agent là damped linear baseline 1–3h.
- **Geospatial & Road Routing Engine** ([`backend/app/services/real_road_routing_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/real_road_routing_service.py)): Đồ thị giao thông thực tế OpenStreetMap tại Vinhomes Ocean Park 1 để sinh tuyến chạy bộ theo km.
- **Weather Provider** ([`backend/app/services/weather_service.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/services/weather_service.py)): Tích hợp dữ liệu vi khí hậu thực tế.
- **PostgreSQL & Mosquitto MQTT Broker**: Lưu trữ trạm, phép đo, cảnh báo, lượt phê duyệt HITL và chuyển phát lệnh điều khiển thiết bị mô phỏng.

---

### 2. Các vấn đề & Nút thắt kỹ thuật đang tồn tại (Current Issues & Bottlenecks)

| ID | Vấn đề / Nút thắt kỹ thuật | Phân tích chi tiết lỗi logic / Rủi ro hiệu năng & bảo mật | Mức độ nghiêm trọng |
|---|---|---|:---:|
| **ISSUE-01** | **Xử lý kép dư thừa (Dual Agent Execution Overhead)** | Tại [`backend/app/main.py:L1027-L1042`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/main.py#L1027-L1042), hệ thống thực thi **cả 2 lệnh**: `await agent_service.chat()` (HTTP proxy sang LangGraph service) **VÀ** `geospatial_agent.process_query()` (gọi service nội bộ). Việc chạy song song/nối tiếp cả 2 engine gây lãng phí CPU/Memory và tăng Latency không cần thiết. | **Cao** |
| **ISSUE-02 (pre-P0)** | **Độ trễ do HTTP Hop & Synchronous LLM Call** | Mô tả này là lịch sử trước P0. Production answer hiện không có synchronous explanation call; semantic fallback tùy chọn chỉ có một invocation và fail-closed về clarification. | **Đã giảm** |
| **ISSUE-03** | **Thiếu Memory State cho Hội thoại Đa lượt (Multi-turn Context Drift)** | Agent dựa vào `map_context` và `station_id` gửi kèm theo từng HTTP Request payload. Chưa tích hợp LangGraph Checkpointer (Postgres/Redis Persistence) để lưu trữ state hội thoại dài hạn, dẫn đến việc xử lý các câu hỏi tiếp nối nâng cao hoàn toàn phụ thuộc vào thông tin Client tự truyền. | **Trung bình** |
| **ISSUE-04 (đã phân loại lại)** | **Chat trả response dạng block, chưa có streaming** | AI Chat gửi đúng một REST POST cho mỗi câu hỏi; polling 30 giây thuộc dashboard telemetry, không thuộc chat. Vì production answer chủ yếu deterministic và không có token stream cần truyền, đây là backlog UX chứ không phải lỗi polling. Chỉ triển khai SSE sau khi đo latency và xác định event/progress thực sự cần stream. | **Thấp / UX** |
| **ISSUE-05 (đã sửa 27/08/2026)** | **Contract forecast bị chia đôi và nhãn mô hình gây hiểu nhầm** | Public API, Frontend và Agent nay chỉ dùng baseline 1–3h theo ADR 0007; tool extended 24h đã bị loại khỏi Agent registry. Spatial timeline 1–24h vẫn là luồng riêng, được ghi nhãn `spatial_fourier_heuristic_v2`, fail-closed khi thiếu history và neo trọng số vào phép đo mới nhất để phản ứng với spike. Không có forecast result cache/Redis cần invalidate. | **Đã giảm** |

---

### 3. Tiến độ & Hạng mục đang triển khai (In-Progress Tasks)

Đối chiếu giữa tài liệu báo cáo (`reports/agent_baseline.md`, `reports/agent_audit.md`, `reports/agent_eval.json`) và hiện trạng Source Code:

| Mã hạng mục | Mô tả theo Báo cáo & Spec | Trạng thái Source Code hiện tại | Tình trạng |
|---|---|---|:---:|
| **AI-001** | Lược đồ công cụ & Backend Adapter (`contracts.py`, `backend_client.py`) | Đã hoàn thành 100%, bổ sung typed validation cho 8 backend tools. | ✅ **Hoàn thành** |
| **AI-002** | Grounding & Safety Gate (`conversational_agent_service.py`, `grounding.py`) | Đã hoàn thành, pass 344/344 unit/integration tests. Ngăn chặn Prompt Injection & Medical Claims. | ✅ **Hoàn thành** |
| **AI-003** | Recommendation Policy v2 theo 3 nhóm người dùng (`normal`, `sensitive`, `outdoor_sport`) | Đã triển khai tại `recommendations.py`, phân biệt rõ ngưỡng AQI 100/150 và gợi ý pivot sang tập trong nhà. | ✅ **Hoàn thành** |
| **AI-004** | Dự báo môi trường canonical 1–3h | Damped linear baseline từ history fresh theo ADR 0007; không tuyên bố Prophet/LSTM. Spatial timeline dài hơn dùng heuristic có provenance riêng và không nằm trong Agent forecast contract. | ✅ **Hoàn thành** |
| **AI-005** | Đề xuất cảnh báo & Bàn giao HITL (`automatic_proposal_service.py`, ADR 0010) | Đã triển khai luồng tạo Proposal `pending`, chặn Agent tự ý điều khiển thiết bị MQTT. | ✅ **Hoàn thành** |
| **AI-006** | Đánh giá & Hồi quy Eval Dataset (25 Golden Test Cases) | Đạt **100% Accuracy & Grounding Compliance Rate** theo [`reports/agent_eval.json`](file:///d:/Ai_Thuc_Chien/P-074/reports/agent_eval.json). | ✅ **Hoàn thành** |
| **Phase 2 Router** | Bounded Semantic Router sử dụng Pydantic validation (ADR 0004 Update 27/08/2026) | Đã cài đặt tại `src/agents/policies/grounding.py` hỗ trợ câu hỏi phức tạp. | ✅ **Hoàn thành** |
| **Monorepo Layout** | Chuyển `backend/` $\rightarrow$ `apps/api` và `frontend/` $\rightarrow$ `apps/web` | Đã chuẩn bị trong kế hoạch, đang tạm hoãn do file lock trên OS Windows. | 🔄 **Đang triển khai** |
| **Async Notification** | Tích hợp Resend Email API SDK cho Manager Notification | Đã có mock/fallback runner, cần cấu hình production API key chính thức. | 🔄 **Đang triển khai** |

---

### 4. Đề xuất cải tiến kỹ thuật (Actionable Recommendations)

1. **Hợp nhất luồng xử lý Agent Execution (Unify Agent Pipeline)**
   - *Giải pháp:* Loại bỏ việc gọi song song `geospatial_agent.process_query()` tại [`backend/app/main.py`](file:///d:/Ai_Thuc_Chien/P-074/backend/app/main.py#L1033) khi `agent_service.chat()` đã xử lý xong. Tích hợp trực tiếp logic sinh Map Actions vào LangGraph node (`compose_node`) của Agent microservice.
   - *Lợi ích:* Giảm từ **40% – 50% Latency** xử lý backend và triệt tiêu nguy cơ bất đồng bộ Intent giữa 2 engine.

2. **Đo latency trước khi quyết định SSE**
   - *Giải pháp:* Dùng metrics hiện có để đo P50/P95/P99 cho `/api/v1/agent/chat`, tách thời gian Agent HTTP, backend tools và geospatial planning. Chỉ bổ sung SSE nếu có event tiến trình có ý nghĩa; không stream từng chữ giả khi response deterministic đã hoàn chỉnh.
   - *Lợi ích:* Tránh thêm protocol, reconnect và state management khi chưa có bottleneck được đo; vẫn giữ đường nâng cấp streaming nếu UX thực tế cần.

3. **Tích hợp LangGraph Checkpointer cho Multi-turn Conversation Memory**
   - *Giải pháp:* Sử dụng `AsyncPostgresSaver` hoặc Redis Checkpointer trong [`src/agents/graph.py`](file:///d:/Ai_Thuc_Chien/P-074/src/agents/graph.py) để lưu trữ `AgentState` theo `thread_id`.
   - *Lợi ích:* Cho phép người dùng hỏi tiếp các câu phụ thuộc ngữ cảnh (*"Còn khu San Hô thì sao?", "Chiều nay ở đó có mưa không?"*) một cách tự nhiên mà không bị mất bối cảnh.

4. **Giữ forecast contract thống nhất và kiểm thử spike**
   - *Giải pháp:* Giữ API/Agent ở baseline 1–3h, fail-closed khi thiếu history/source/timestamp, và duy trì regression case cho spike 40 → 190 µg/m³. Spatial heuristic phải có provenance riêng và không được tự nhận là Prophet.
   - *Lợi ích:* Forecast phản ứng với dữ liệu mới mà không cần thêm cache invalidation hoặc Redis; tránh nhầm mô hình visualization với forecast canonical.

5. **Áp dụng Circuit Breaker Pattern cho LLM External Calls**
   - *Giải pháp:* Bổ sung thư viện Circuit Breaker (như `tenacity` hoặc `pybreaker`) xung quanh các kết nối HTTP ra ngoài dịch vụ LLM.
   - *Lợi ích:* Ngăn ngừa tình trạng nghẽn tuyến (cascading failure) khi API bên ngoài gặp sự cố, tự động fallback an toàn về câu trả lời Deterministic Grounded.

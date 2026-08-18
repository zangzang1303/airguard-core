# AI Agent Core Optimization & Live LLM Evaluation

> **Người phụ trách:** Member 3 (AI Agent & ML Lead)  
> **Thời hạn hoàn thành:** Hết Ngày 2  
> **Mục tiêu:** Đảm bảo AI Agent chạy bằng LLM thật (`gpt-4o-mini`), 100% Grounding từ backend tools, không bịa số liệu và trả lời thông minh, thân thiện.

---

## 1. Các hạng mục công việc cần hoàn thành

### Task 1: Tối ưu hóa Luồng LangGraph & Tool Calling
- File: [`src/agents/graph.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/graph.py) & [`src/agents/nodes/orchestration.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/nodes/orchestration.py)
- Đảm bảo cơ chế Hybrid:
  ```text
  Intent Classification -> Backend Tools Execution -> Evidence Validation -> LLM Explanation -> Response Composer
  ```
- LLM chỉ được phép giải thích dựa trên các số liệu thực tế được backend cung cấp trong cùng request.
- Nếu không có `OPENAI_API_KEY` hoặc API timeout, tự động chuyển sang Deterministic Composer an toàn mà không làm gián đoạn trải nghiệm người dùng.

### Task 2: Cá nhân hóa Khuyến nghị theo Nhóm Sức khỏe
- File: [`src/agents/policies/recommendations.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/policies/recommendations.py)
- Hỗ trợ 3 nhóm đối tượng:
  1. `normal` (Cư dân bình thường): Lời khuyên sinh hoạt, đi lại thông thường.
  2. `sensitive` (Trẻ em, người cao tuổi, người có bệnh hô hấp/tim mạch): Cảnh báo sớm ngay cả ở mức Moderate/Unhealthy for Sensitive Groups, khuyên đóng cửa sổ, bật máy lọc không khí.
  3. `outdoor_sport` (Người chạy bộ, tập thể dục ngoài trời): Tư vấn địa điểm trạm có AQI tốt nhất trong khu đô thị và khung giờ phù hợp.

### Task 3: Safety Guard & Refusal Policy
- File: [`src/agents/policies/grounding.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/policies/grounding.py)
- Từ chối đưa ra chẩn đoán y tế hoặc đơn thuốc (Medical disclaimer).
- Chặn các câu hỏi cố tình ép AI vượt quyền duyệt lệnh hoặc điều khiển thiết bị bỏ qua BQL (HITL Bypass Protection).
- Xử lý mượt mà khi người dùng hỏi các câu ngoài phạm vi (Out of scope).

---

## 2. Kiểm thử & Chạy Live Evaluation

```powershell
# Chạy bộ test grounding và live evaluation script
.\.venv\Scripts\python.exe -m pytest tests/test_agents -v
.\.venv\Scripts\python.exe eval/run_live_evaluation.py
```

- [ ] Toàn bộ 5 case Live Evaluation (LIVE-01 đến LIVE-05) đạt PASS với `generation_mode=live_llm`.
- [ ] Thời gian phản hồi trung bình (Latency P95) dưới 2.5 giây.
- [ ] Câu trả lời tự nhiên bằng tiếng Việt, có đầy đủ căn cứ số liệu, tên trạm, thời gian đo và nhãn minh bạch dữ liệu.

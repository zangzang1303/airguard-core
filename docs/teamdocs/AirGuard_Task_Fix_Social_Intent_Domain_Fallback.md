# AIRGUARD AI — TASK FIX SOCIAL INTENT, DOMAIN BOUNDARY & FALLBACK ROUTING

## 1. Mục tiêu

Sửa lỗi Agent Chat đang **ép các câu hỏi xã giao / ngoài nghiệp vụ sang intent môi trường**, dẫn tới trả lời hoàn toàn sai ngữ cảnh.

Ví dụ lỗi thực tế:

### User
> bạn bao tuổi

hoặc:

> bạn bao nhiêu tuổi

### Agent hiện tại
> Hồ Ngọc Trai hiện là khu vực có chất lượng không khí tốt nhất...

hoặc:

> VinUni hiện là khu vực có chất lượng không khí tốt nhất...

Đây là lỗi nghiêm trọng ở:

- Intent Router
- Domain Boundary Detection
- Social Intent Handling
- Fallback Policy
- Conversation State Inheritance
- Map Action Guard

Mục tiêu sau khi sửa:

> Câu xã giao phải được trả lời như hội thoại bình thường, **không gọi tool môi trường, không dùng context địa điểm cũ, không thao tác Map và không tự sinh recommendation AQI**.

---

# 2. Root Cause cần kiểm tra

Khả năng cao hệ thống đang có logic kiểu:

```text
Nếu không match intent rõ
→ fallback sang environment / best_location
```

hoặc:

```text
previous context = environment
+
new message không resolve được
→ inherit intent cũ
```

hoặc:

```text
social detector chỉ nhận "xin chào", "hello"
→ các câu như "bạn bao nhiêu tuổi" không được coi là social
→ rơi xuống generic domain fallback
```

Phải loại bỏ hoàn toàn hành vi này.

---

# 3. Nguyên tắc mới

## RULE 1 — Không hiểu không có nghĩa là môi trường

```text
UNKNOWN != ENVIRONMENT
```

Nếu câu không thuộc domain môi trường:

```text
không được fallback sang AQI
không được chọn best location
không được highlight map
```

---

## RULE 2 — Social intent có priority cao

Social / conversational query phải được xét trước domain routing.

Routing precedence mới:

```text
1. Safety / Injection
2. Conversation Correction
3. Social / Assistant Identity
4. Small Talk
5. Domain Boundary Check
6. Scope Detection
7. Indoor / Negation
8. Comparison
9. Overview
10. Ranking
11. Location
12. Route
13. Forecast
14. Telemetry
15. Clarification / Unknown
```

---

# 4. Thêm nhóm Intent mới

## 4.1 `social.greeting`

Ví dụ:

```text
xin chào
hello
hi
chào bạn
alo
```

---

## 4.2 `social.assistant_identity`

Ví dụ:

```text
bạn là ai
bạn tên gì
bạn bao tuổi
bạn bao nhiêu tuổi
bạn là người hay AI
ai tạo ra bạn
bạn làm được gì
```

---

## 4.3 `social.smalltalk`

Ví dụ:

```text
bạn khỏe không
hôm nay thế nào
cảm ơn nhé
ok bạn
hay đấy
```

---

## 4.4 `conversation.capability`

Ví dụ:

```text
bạn có thể giúp gì
bạn làm được gì ở đây
tôi có thể hỏi gì
```

---

## 4.5 `conversation.unknown`

Dùng khi không chắc user muốn gì.

Không route sang môi trường nếu thiếu bằng chứng.

---

# 5. Structured Intent Output

### Input

```text
bạn bao nhiêu tuổi
```

### Expected

```json
{
  "intent": "social.assistant_identity",
  "domain": "social",
  "confidence": 0.99,
  "requires_environment_tools": false,
  "requires_map_action": false,
  "inherit_previous_domain_context": false
}
```

---

# 6. Response chuẩn cho câu hỏi trong ảnh

### User

> bạn bao nhiêu tuổi

### Target

> Mình là trợ lý AI nên không có tuổi như con người 😊  
> Mình được thiết kế để hỗ trợ bạn về chất lượng không khí, địa điểm và lộ trình trong Ocean Park 1.

Không cần nói thêm AQI.

Không thao tác Map.

---

# 7. Domain Boundary Classifier

Trước khi route vào domain AirGuard, thêm bước:

```text
Does this message require AirGuard environmental/geospatial data?
```

Output:

```json
{
  "domain": "airguard"
}
```

hoặc:

```json
{
  "domain": "social"
}
```

hoặc:

```json
{
  "domain": "unknown"
}
```

---

# 8. Domain Rules

## `airguard`

Có tín hiệu liên quan:

```text
AQI
PM2.5
không khí
ô nhiễm
trạm
VinUni
Sapphire
Hồ Ngọc Trai
đường Hải Đăng
chạy bộ
đi bộ
route
dự báo
khu sạch
khu ô nhiễm
Ocean Park
```

---

## `social`

Có tín hiệu:

```text
bạn là ai
bao tuổi
tên gì
cảm ơn
xin chào
khỏe không
ai tạo ra bạn
```

---

## `unknown`

Không đủ thông tin để xác định.

Ví dụ:

```text
cái này sao
thế nào
được không
```

Nếu không có context rõ:

Agent phải hỏi lại.

---

# 9. Không inherit domain context cho Social Query

Ví dụ:

```text
User: Khu nào sạch nhất?
Agent: VinUni...
User: bạn bao tuổi?
```

Không được giữ:

```text
last_intent = ranking_best
active_location = VinUni
```

để trả câu mới.

Social query phải tạo context boundary:

```text
current_domain = social
ignore_domain_inheritance = true
```

---

# 10. Context State Rule

Conversation State vẫn có thể giữ context cũ để dùng nếu user quay lại sau đó.

Ví dụ:

```text
User: Khu nào sạch nhất?
Agent: VinUni.

User: bạn bao nhiêu tuổi?
Agent: Mình là AI nên không có tuổi như con người.

User: thế VinUni AQI bao nhiêu?
```

Lúc này có thể quay lại domain và dùng `VinUni`.

Nhưng trong lượt social:

```text
không được dùng context môi trường để tạo answer.
```

---

# 11. Context Stack đề xuất

Thay vì chỉ có một `last_intent`, nên có:

```json
{
  "active_domain": "social",

  "domain_context": {
    "airguard": {
      "last_intent": "environment.ranking_best",
      "active_location": "poi_vinuni",
      "active_metric": "AQI"
    }
  },

  "current_turn": {
    "intent": "social.assistant_identity"
  }
}
```

Điều này giúp social query không phá hoàn toàn context môi trường, nhưng cũng không bị context cũ chi phối.

---

# 12. Tool Guard

Trước khi gọi tool:

```python
if domain != "airguard":
    block_environment_tools()
```

Social query:

```text
tool_calls = 0
```

---

# 13. Map Action Guard

Nếu:

```text
intent startswith "social."
```

thì:

```text
map_actions = []
```

Bắt buộc.

---

# 14. Không Map Feedback cho Social

Không được trả:

```text
📍 Mình đã đánh dấu VinUni trên bản đồ.
```

sau câu:

```text
bạn bao nhiêu tuổi
```

---

# 15. Fallback Policy mới

## Sai

```text
unmatched intent
→ best location
```

## Đúng

```text
unmatched intent
→ check context
    ↓
if context clearly resolves:
    follow-up
else:
    clarification
```

---

# 16. Unknown Query Example

### User

> cái này thế nào

Nếu conversation context không rõ:

### Output

> Bạn muốn mình kiểm tra **chất lượng không khí**, **một địa điểm**, hay **một cung đường** trong Ocean Park 1?

Không tự trả VinUni.

---

# 17. Assistant Identity Response Contract

Intent:

```text
social.assistant_identity
```

Required:

```text
direct answer
short capability reminder (optional)
```

Forbidden:

```text
environment metrics
map action
location recommendation
tool call
technical backend explanation
```

---

# 18. Các response mẫu

## User
> bạn là ai

### Target
> Mình là **AirGuard Geospatial AI**, trợ lý AI hỗ trợ bạn kiểm tra chất lượng không khí, địa điểm và lộ trình trong Ocean Park 1.

---

## User
> bạn bao tuổi

### Target
> Mình là AI nên không có tuổi như con người 😊

---

## User
> bạn làm được gì

### Target
> Mình có thể giúp bạn:
> - kiểm tra chất lượng không khí theo khu vực;
> - so sánh các địa điểm;
> - xem dự báo AQI;
> - tìm cung đường đi bộ/chạy bộ có mức phơi nhiễm thấp hơn;
> - định vị kết quả trực tiếp trên bản đồ.

---

## User
> cảm ơn

### Target
> Không có gì 😊 Nếu cần, bạn cứ hỏi mình về không khí hoặc địa điểm trong Ocean Park 1.

---

# 19. Response Planner Guard

Pseudo-code:

```python
if intent.startswith("social."):
    response_type = "social"
    must_include = ["direct_answer"]
    map_feedback = False
    environment_metrics = False
    skip_tool_planner = True
```

---

# 20. Router Contract

Router output bắt buộc:

```json
{
  "intent": "social.assistant_identity",
  "domain": "social",
  "confidence": 0.98,
  "use_context": false,
  "requires_tools": false,
  "requires_map": false,
  "needs_clarification": false
}
```

---

# 21. Test Cases bắt buộc

## T01

Input:

```text
bạn bao tuổi
```

Expected:

```text
intent = social.assistant_identity
tool_calls = 0
map_actions = 0
```

---

## T02

Input:

```text
bạn bao nhiêu tuổi
```

Expected:

```text
social.assistant_identity
```

Không trả AQI.

---

## T03

Conversation:

```text
User: Khu nào sạch nhất?
Agent: VinUni...
User: bạn bao tuổi?
```

Expected:

```text
social response
```

Không inherit `ranking_best`.

---

## T04

Conversation:

```text
User: Khu nào sạch nhất?
Agent: VinUni...
User: bạn bao tuổi?
Agent: ...
User: còn AQI ở đó?
```

Expected:

Có thể resolve `ở đó` = VinUni nếu domain context trước vẫn còn hợp lệ.

---

## T05

Input:

```text
bạn khỏe không
```

Expected:

```text
social.smalltalk
```

Không gọi environmental tool.

---

## T06

Input:

```text
bạn làm được gì
```

Expected:

```text
conversation.capability
```

---

## T07

Input:

```text
abcxyz
```

Expected:

```text
conversation.unknown
```

Không fallback best location.

---

# 22. Regression Tests

Phải đảm bảo việc thêm Social Router không phá domain queries:

```text
VinUni không khí thế nào?
→ environment.location

Khu nào sạch nhất?
→ environment.ranking_best

Toàn Ocean Park thế nào?
→ environment.overview

Tối nay chạy ở đâu?
→ decision.best_route / activity.running
```

---

# 23. Acceptance Criteria

- [ ] `bạn bao tuổi` không còn trả VinUni/Hồ Ngọc Trai.
- [ ] `bạn bao nhiêu tuổi` được nhận diện là social.
- [ ] Social query không gọi tool môi trường.
- [ ] Social query không tạo map action.
- [ ] Social query không inherit intent môi trường cũ.
- [ ] Context môi trường vẫn có thể được giữ trong domain context để dùng khi user quay lại.
- [ ] Unknown query không fallback sang `best_location`.
- [ ] Có `conversation.unknown` / clarification.
- [ ] Có Domain Boundary Classifier.
- [ ] Có Tool Guard.
- [ ] Có Map Action Guard.
- [ ] Regression domain tests pass.

---

# 24. Definition of Done

Conversation sau phải hoạt động đúng:

```text
User:
Khu nào sạch nhất?

Agent:
🌿 VinUni hiện là...

User:
bạn bao nhiêu tuổi

Agent:
Mình là AI nên không có tuổi như con người 😊

User:
AQI ở VinUni thì sao?

Agent:
📍 AQI tại VinUni hiện...
```

Không được:

```text
User:
bạn bao nhiêu tuổi

Agent:
🌿 VinUni hiện là khu vực...
```

---

# 25. Nguyên tắc cuối cùng

> **Không phải mọi câu user gửi đều là câu hỏi môi trường.**

Và:

> **Fallback không bao giờ được phép biến một câu không hiểu thành recommendation địa điểm.**

Router phải phân biệt rõ:

```text
SOCIAL
vs
AIRGUARD DOMAIN
vs
FOLLOW-UP
vs
UNKNOWN
```

trước khi chạy bất kỳ tool hoặc map action nào.

# AIRGUARD AI — TASK XÂY DỰNG DEEP CONVERSATION CONTEXT & FOLLOW-UP AGENT

## 1. Mục tiêu

Nâng cấp AirGuard Chat Agent từ cơ chế xử lý từng tin nhắn độc lập thành một **Contextual Conversational Agent** có khả năng:

- hiểu hội thoại nhiều lượt;
- nhớ người dùng và chủ đề đang nói;
- hiểu các câu nối ngắn như:
  - “tìm cho tôi”
  - “ở đó thì sao?”
  - “ngắn hơn chút”
  - “cái kia”
  - “được”
  - “không, ý tôi là…”
- nhớ Agent vừa hỏi gì;
- nhớ Agent vừa đề nghị gì;
- tiếp tục đúng task đang dang dở;
- chỉ hỏi lại khi thực sự thiếu thông tin bắt buộc;
- không chạy lại intent classifier từ đầu cho mọi message;
- không fallback ngẫu nhiên sang AQI / best location khi không hiểu;
- giữ Chat và Map đồng bộ theo đúng context hội thoại.

---

# 2. Vấn đề hiện tại

Ví dụ thực tế:

### User
> tôi có thể đạp xe thay vì chạy bộ ko

### Agent
> Nếu muốn, mình có thể giúp bạn tìm khu vực trong nhà thuận tiện hơn gần vị trí hiện tại.

### User
> tìm cho tôi

### Agent hiện tại
> Bạn muốn mình kiểm tra chất lượng không khí, một địa điểm, hay một cung đường trong Ocean Park 1?

Đây là lỗi context.

User nói:

```text
tìm cho tôi
```

không phải một intent mới.

Đó là:

```text
accept action vừa được Agent đề nghị
```

Agent phải hiểu:

```text
"tìm cho tôi"
=
thực hiện action đang chờ từ lượt trước
```

---

# 3. Root Cause

Hệ thống hiện tại có khả năng đang xử lý:

```text
Mỗi message
→ Intent Classifier
→ Keyword Router
→ Tool
→ Response
```

Cách này làm mất ngữ cảnh.

Kiến trúc mới phải là:

```text
Message
→ Resolve against Dialogue State
→ Resolve Pending Action
→ Resolve Awaiting Slot
→ Resolve Follow-up / Reference
→ nếu tất cả không match
    mới classify New Intent
```

---

# 4. Kiến trúc Conversation mới

```text
USER MESSAGE
     ↓
Conversation State Manager
     ↓
Conversation Resolver
     ├── Correction?
     ├── Pending Action?
     ├── Answer to Previous Question?
     ├── Follow-up?
     ├── Reference?
     └── New Intent?
     ↓
Task State
     ↓
Slot Filling
     ↓
Semantic / Spatial Resolution
     ↓
Tool Planner
     ↓
Evidence
     ↓
Response Planner
     ↓
Chat + Map Action
```

---

# 5. Conversation State phải chia thành 4 lớp

Không chỉ lưu `last_intent`.

## 5.1 Dialogue Context

Lưu:

```text
Agent vừa hỏi gì?
Agent vừa đề nghị gì?
Có action nào đang chờ không?
Có slot nào đang chờ user trả lời không?
User vừa accept/reject/modify gì?
```

---

## 5.2 Task Context

Lưu:

```text
User đang muốn làm gì?
running?
walking?
indoor?
compare?
forecast?
route?
```

---

## 5.3 Spatial Context

Lưu:

```text
active location
previous location
origin
destination
route
last highlighted entity
last compared entities
```

---

## 5.4 Environmental Context

Lưu:

```text
AQI hay PM2.5?
current hay forecast?
time window?
comparison metric?
user health context nếu có?
```

---

# 6. Conversation State Schema

Đề xuất:

```json
{
  "conversation_id": "...",

  "dialogue": {
    "current_topic": "indoor_activity",

    "last_agent_question": null,

    "last_agent_offer": {
      "action": "find_nearby_indoor_places",
      "status": "awaiting_confirmation"
    },

    "pending_action": {
      "type": "find_nearby_indoor_places",
      "status": "pending",
      "created_turn": 12
    },

    "awaiting_user_input": null
  },

  "task": {
    "intent": "activity.indoor",
    "goal": "find_indoor_alternative",
    "activity": "indoor"
  },

  "spatial": {
    "active_location": "area_sapphire",
    "previous_locations": [],
    "origin": "area_sapphire",
    "destination": null,
    "active_route_id": null
  },

  "environment": {
    "metric": "AQI",
    "time_context": "current"
  },

  "constraints": {
    "avoid_polluted_area": true
  }
}
```

---

# 7. Pending Action Manager

Đây là module bắt buộc.

Agent có thể chủ động đề nghị:

> Mình có thể giúp bạn tìm khu vực trong nhà gần đây.

Khi đó phải tạo:

```json
{
  "pending_action": {
    "type": "find_nearby_indoor_places",
    "status": "awaiting_confirmation",
    "required_slots": ["origin"],
    "known_slots": {
      "activity_type": "indoor"
    }
  }
}
```

---

# 8. Accept Pending Action

Các câu như:

```text
được
ok
ừ
có
làm đi
tìm đi
tìm cho tôi
thử xem
được đó
```

nếu có pending action thì phải resolve thành:

```text
conversation.accept_pending_action
```

Không được chạy classifier mới.

---

# 9. Reject Pending Action

Các câu:

```text
không
thôi
khỏi
không cần
bỏ đi
```

phải:

```text
conversation.reject_pending_action
```

và:

```text
pending_action = null
```

---

# 10. Modify Pending Action

Ví dụ:

### Agent
> Mình có thể tìm tuyến 5 km.

### User
> 3 km thôi

Phải hiểu:

```json
{
  "intent": "conversation.modify",
  "target": "pending_action",
  "changes": {
    "distance_km": 3
  }
}
```

Không phải query mới.

---

# 11. Last Agent Offer

Mỗi lần Agent nói:

```text
Nếu muốn, mình có thể...
Bạn có muốn mình...
Mình có thể tìm...
```

phải lưu structured action.

Ví dụ:

```json
{
  "last_agent_offer": {
    "action": "find_nearby_indoor_places",
    "parameters": {
      "origin": "area_sapphire"
    }
  }
}
```

Không chỉ lưu raw text.

---

# 12. Question State

Agent cũng phải nhớ mình vừa hỏi gì.

Ví dụ:

### Agent
> Bạn muốn chạy khoảng bao nhiêu km?

State:

```json
{
  "awaiting_user_input": {
    "type": "slot",
    "slot": "distance_km",
    "for_intent": "activity.running"
  }
}
```

### User
> 3

Phải hiểu:

```text
distance_km = 3
```

Không hỏi lại:

> Bạn muốn kiểm tra chất lượng không khí hay địa điểm?

---

# 13. Slot Filling

Một task phức tạp có thể được xây qua nhiều lượt.

Ví dụ:

### User
> Tìm đường chạy cho tôi.

Agent xác định:

```text
intent = running_route
```

Missing slots:

```text
origin
distance
```

Agent chỉ hỏi slot còn thiếu.

---

### Agent
> 🏃 Bạn muốn chạy khoảng 2 km, 3 km hay 5 km?

### User
> 3 km

State:

```text
distance_km = 3
```

### Agent
> Bạn muốn xuất phát từ vị trí hiện tại hay một khu cụ thể?

### User
> Sapphire

Đủ slot:

```json
{
  "intent": "recommend_running_route",
  "origin": "Sapphire",
  "distance_km": 3,
  "time": "current"
}
```

Sau đó mới execute.

---

# 14. Nguyên tắc hỏi lại

> **Chỉ hỏi lại khi thiếu thông tin bắt buộc.**

Không được hỏi generic clarification nếu state đã đủ.

Pseudo:

```python
resolved = resolve_from_context(message, state)

if resolved:
    execute(resolved)

elif state.pending_action:
    resolve_against_pending_action()

elif state.awaiting_user_input:
    fill_slot()

elif is_followup(message, state):
    resolve_followup()

elif is_reference(message, state):
    resolve_reference()

else:
    classify_new_intent()
```

---

# 15. Follow-up Intent

Bổ sung:

```text
conversation.followup
```

Ví dụ:

### User
> VinUni thế nào?

### Agent
> ...

### User
> còn Hồ Ngọc Trai?

Phải giữ:

```text
metric = AQI
time = current
```

Chỉ đổi:

```text
location = Hồ Ngọc Trai
```

---

# 16. Reference Resolution

Agent phải hiểu các cụm:

```text
ở đó
chỗ đó
khu đó
nơi vừa nói
cái kia
cái thứ hai
tuyến đó
đường vừa rồi
chỗ sạch hơn
```

---

# 17. Reference Example

### Agent
> VinUni sạch hơn Hồ Ngọc Trai.

### User
> đường từ đây đến đó thế nào?

Resolver phải tìm:

```text
origin = current context
destination = focused entity
```

Nếu có nhiều candidate:

```text
needs_clarification = true
```

---

# 18. Clarification khi mơ hồ

Ví dụ:

```text
đường từ đây đến đó
```

mà context có 2 destination khả thi.

Agent hỏi:

> Bạn muốn đi tới **VinUni** hay **Hồ Ngọc Trai**?

Không tự đoán.

---

# 19. Conversation Correction

Bổ sung:

```text
conversation.correction
```

Các phrase:

```text
ý tôi là
không, tôi muốn
không phải
tôi nói là
ý là
```

Correction phải có priority cao.

---

# 20. Correction Example

### User
> tìm đường chạy 5 km

### User
> không, 3 km thôi

Update:

```text
distance_km = 3
```

Không reset task.

---

# 21. New Topic Detection

Nếu user đổi chủ đề rõ:

```text
User: tìm route 5 km
User: AQI VinUni bao nhiêu?
```

Task route không được ảnh hưởng câu mới.

Phải:

```text
conversation.new_topic
```

---

# 22. Context Stack

Không chỉ một `last_intent`.

Đề xuất:

```json
{
  "active_domain": "airguard",

  "task_stack": [
    {
      "task_id": "task_12",
      "intent": "activity.indoor",
      "status": "active"
    }
  ],

  "dialogue_state": {
    "pending_action": "...",
    "awaiting_slot": null
  },

  "spatial_context": {},
  "environment_context": {}
}
```

---

# 23. State Machine

Đề xuất:

```text
IDLE
 ↓
UNDERSTANDING
 ↓
NEED_INFO
 ↓
READY
 ↓
EXECUTING
 ↓
ANSWERED
 ↓
FOLLOW_UP
 ├── ACCEPT
 ├── MODIFY
 ├── REJECT
 ├── COMPARE
 ├── CHANGE_LOCATION
 └── NEW_TASK
```

---

# 24. Conversation Intent Taxonomy mới

Bổ sung:

```text
conversation.accept
conversation.reject
conversation.modify
conversation.correction
conversation.answer_slot
conversation.followup
conversation.reference
conversation.new_topic
conversation.unknown
```

Các intent này phải được xét trước domain intent.

---

# 25. Routing Precedence

Thứ tự:

```text
1. Safety
2. Correction
3. Pending Action Resolution
4. Answer to Previous Agent Question
5. Accept / Reject / Modify
6. Reference Resolution
7. Follow-up
8. New Topic Detection
9. Social
10. Domain Intent Classification
11. Unknown / Clarification
```

---

# 26. Case thực tế cần sửa

## Conversation

### User
> tôi có thể đạp xe thay vì chạy bộ ko

### Agent
> Nếu muốn, mình có thể giúp bạn tìm khu vực trong nhà thuận tiện hơn gần vị trí hiện tại.

State phải tạo:

```json
{
  "pending_action": {
    "type": "find_nearby_indoor_places",
    "status": "awaiting_confirmation"
  }
}
```

---

### User
> tìm cho tôi

Expected:

```json
{
  "intent": "conversation.accept",
  "resolved_action": "find_nearby_indoor_places"
}
```

---

## Nếu đã biết user đang ở Sapphire

Agent phải execute ngay:

> 🏠 Mình đã tìm một số lựa chọn trong nhà phù hợp gần Sapphire...

---

## Nếu chưa biết vị trí

Chỉ hỏi đúng missing slot:

> 📍 Được. Bạn đang ở khu nào trong Ocean Park 1 để mình tìm các địa điểm trong nhà gần nhất?

Không hỏi:

> Bạn muốn kiểm tra chất lượng không khí, địa điểm hay cung đường?

---

# 27. Deep Follow-up Example 1

### User
> Khu nào ô nhiễm nhất?

### Agent
> Trục Đa Tốn.

### User
> còn VinUni?

Expected:

```text
followup
metric = AQI
time = current
location = VinUni
```

---

# 28. Deep Follow-up Example 2

### User
> tìm route 5 km từ Sapphire

### Agent
> ...

### User
> ngắn hơn chút

Expected:

```text
same task
distance < 5
```

---

# 29. Deep Follow-up Example 3

### User
> route này ổn đấy

### User
> nhưng tránh Đa Tốn nhé

Expected:

```json
{
  "constraint_update": {
    "avoid": ["Trục Đa Tốn"]
  },
  "recompute": true
}
```

---

# 30. Deep Follow-up Example 4

### User
> VinUni hay Hồ Ngọc Trai sạch hơn?

### Agent
> VinUni.

### User
> đi bộ tới đó mất bao lâu?

Expected:

```text
destination = VinUni
activity = walking
```

Không hỏi lại location nếu reference rõ.

---

# 31. Deep Follow-up Example 5

### Agent
> Bạn muốn 2 km, 3 km hay 5 km?

### User
> cái giữa

Expected:

```text
distance = 3 km
```

Agent phải hiểu ordinal/reference.

---

# 32. Deep Follow-up Example 6

### Agent
> Bạn muốn gym hay đi bộ trong nhà?

### User
> gym

Expected:

```text
slot activity_subtype = gym
```

---

# 33. Short Answer Resolver

Các câu ngắn:

```text
3
được
không
ở đó
cái kia
gần hơn
sạch hơn
tối nay
VinUni
```

không được classify độc lập ngay.

Phải resolve dựa trên `awaiting_slot` hoặc context trước.

---

# 34. Pending Action Expiry

Không giữ pending action vô hạn.

Ví dụ:

```text
expires_after_turns = 3
```

Nếu user đổi topic:

```text
pending_action = invalidated
```

---

# 35. Context Invalidation

Context phải bị reset/selectively cleared khi:

```text
new topic
explicit correction
different activity
different scope
different metric
```

Không xóa toàn bộ conversation nếu không cần.

---

# 36. Context Persistence

Có thể lưu conversation state theo:

```text
conversation_id
```

Storage MVP:

```text
Redis
```

hoặc:

```text
PostgreSQL JSONB
```

Đề xuất:

```text
Redis = active conversation state
PostgreSQL = audit / durable history nếu cần
```

---

# 37. Không dùng raw transcript làm state duy nhất

Không nên chỉ gửi:

```text
last 20 messages
```

vào LLM rồi hy vọng model tự hiểu.

Phải có structured state.

Ví dụ:

```json
{
  "active_task": "find_indoor_places",
  "pending_action": "...",
  "origin": "Sapphire",
  "awaiting_slot": null
}
```

---

# 38. Context Resolver Output

Mỗi lượt nên tạo:

```json
{
  "resolution_type": "accept_pending_action",

  "resolved_intent": "activity.indoor",

  "inherited": [
    "activity_type",
    "origin"
  ],

  "updated": [],

  "missing_slots": [],

  "confidence": 0.96
}
```

---

# 39. Response Planner phải biết Dialogue State

Nếu state đang `awaiting_slot`:

Response Planner không nên trả full recommendation.

Chỉ hỏi đúng slot.

Nếu state `ready`:

execute.

Nếu `pending_confirmation`:

đợi accept/reject.

---

# 40. Map Actions và Conversation

Map cũng phải giữ context.

Ví dụ:

```text
User: đánh dấu VinUni
User: còn chỗ kia?
```

Map focus mới phải follow resolved entity.

Không dùng last arbitrary marker.

---

# 41. Follow-up Suggestions phải tạo Pending Action

Nếu UI hiện chip:

```text
[Tìm gym gần đây]
```

click hoặc user nói tương đương phải map tới:

```text
action = find_nearby_gym
```

Không quay lại generic intent routing.

---

# 42. Agent chủ động vừa đủ

Sau response có thể đưa 1–3 lựa chọn cụ thể:

Ví dụ:

> Bạn muốn mình:
>
> **Tìm gym gần đây** · **Tìm tuyến đạp xe** · **Xem AQI tối nay**

Không hỏi quá chung:

> Bạn muốn làm gì tiếp?

---

# 43. Conversation Test Suite

## T01 — Accept Offer

```text
Agent: Mình có thể tìm gym gần đây.
User: tìm cho tôi
```

Expected:

```text
accept pending action
```

---

## T02 — Short Yes

```text
Agent: Mình có thể tìm route sạch hơn.
User: được
```

Expected:

```text
execute offer
```

---

## T03 — Reject

```text
Agent: Mình có thể tìm route khác.
User: thôi
```

Expected:

```text
cancel pending action
```

---

## T04 — Slot

```text
Agent: Bạn muốn chạy bao nhiêu km?
User: 3
```

Expected:

```text
distance_km = 3
```

---

## T05 — Modify

```text
User: tìm route 5 km
User: 3 km thôi
```

Expected:

```text
distance = 3
```

---

## T06 — Reference

```text
Agent: VinUni tốt hơn Hồ Ngọc Trai.
User: đi tới đó mất bao lâu?
```

Expected:

```text
destination = VinUni
```

nếu focus entity = VinUni.

---

## T07 — Ambiguous Reference

Nếu có 2 target hợp lý:

Expected:

```text
clarification
```

---

## T08 — Follow-up Location

```text
User: VinUni AQI?
User: còn Sapphire?
```

Expected:

```text
AQI Sapphire
```

---

## T09 — New Topic

```text
User: route 5 km
User: bạn bao tuổi?
```

Expected:

```text
social
```

Không route context.

---

## T10 — Return to Previous Domain

```text
User: VinUni AQI?
User: bạn bao tuổi?
User: còn Hồ Ngọc Trai?
```

Nếu environmental context còn rõ:

Expected:

```text
AQI Hồ Ngọc Trai
```

---

# 44. Acceptance Criteria

- [ ] Có Dialogue State riêng.
- [ ] Có Pending Action Manager.
- [ ] Có Last Agent Offer structured.
- [ ] Có Awaiting Slot state.
- [ ] Có Slot Filling.
- [ ] Có Follow-up Resolver.
- [ ] Có Reference Resolver.
- [ ] Có Accept/Reject/Modify intent.
- [ ] Có Context Correction.
- [ ] Có New Topic detection.
- [ ] Không classify mọi short message như new intent.
- [ ] “tìm cho tôi” thực hiện đúng lời đề nghị trước.
- [ ] “3” có thể fill distance nếu Agent vừa hỏi distance.
- [ ] “ở đó” resolve đúng entity nếu context rõ.
- [ ] Ambiguous reference phải clarification.
- [ ] Pending action bị invalid khi user đổi topic.
- [ ] Chat và Map follow cùng resolved context.
- [ ] Tests follow-up pass 100%.

---

# 45. Definition of Done

Flow sau phải hoạt động đúng:

```text
User:
tôi có thể đạp xe thay vì chạy bộ ko

Agent:
🚴 Được. Mình có thể tìm tuyến đạp xe ít phơi nhiễm hơn hoặc một địa điểm tập trong nhà gần bạn.
Bạn muốn đạp xe ngoài trời hay tập trong nhà?

User:
trong nhà

Agent:
🏠 Được. Bạn muốn mình ưu tiên gym/thể thao hay đi bộ – thư giãn trong nhà?

User:
gym

Agent:
📍 Mình sẽ ưu tiên gym. Bạn đang ở Sapphire đúng không?

User:
đúng

Agent:
🏋️ Mình đã tìm các lựa chọn phù hợp gần Sapphire...
```

Hoặc nếu Agent đã biết Sapphire từ context:

```text
User:
gym

Agent:
🏋️ Mình đã tìm các lựa chọn phù hợp gần Sapphire...
```

Không hỏi lại thông tin đã biết.

---

# 46. Nguyên tắc cuối cùng

> **Một Agent hội thoại tốt không chỉ nhớ người dùng đã nói gì; nó phải nhớ cuộc hội thoại đang ở bước nào.**

AirGuard cần nhớ:

```text
Agent vừa hỏi gì
Agent vừa đề nghị gì
User vừa đồng ý hay sửa gì
Task nào đang chạy
Slot nào còn thiếu
Địa điểm nào đang được nói tới
Map đang focus đâu
```

Và chỉ khi không thể resolve từ những context đó thì mới coi message là một yêu cầu mới.

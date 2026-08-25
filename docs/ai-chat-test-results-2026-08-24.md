# Kết quả chạy 32 test case — Hỏi AI

- Thời điểm: 24/08/2026
- Môi trường: frontend `http://localhost:5173`, backend `http://localhost:8000`, Agent `http://localhost:8001`.
- Cách chạy: UI smoke trên tab trình duyệt riêng; 20 câu hỏi nghiệp vụ gọi `POST /api/v1/agent/chat` với `user_id=demo-user`.
- Lưu ý: dữ liệu simulator thay đổi theo thời gian. Mỗi nhận định pass/fail đối chiếu intent, evidence và hành vi, không so sánh số AQI cố định giữa các request khác thời điểm.

## Tổng quan

| PASS | FAIL | BLOCKED | Tổng |
|---:|---:|---:|---:|
| 13 | 18 | 1 | 32 |

## Kết quả chi tiết

| ID | Kết quả | Evidence | Ghi chú |
|---|---|---|---|
| AI-01 | PASS | UI tab | Nút Hỏi AI mở panel với lời chào, gợi ý, ô nhập và nút gửi. |
| AI-02 | PASS | UI tab | Nút Đóng đóng panel; `aria-expanded=false`, ô nhập không còn trong DOM. |
| AI-03 | PASS | UI tab | Nút gửi disabled khi câu hỏi rỗng và enabled sau khi nhập; gửi được một message. |
| AI-04 | FAIL | `336456e5-c5fc-4cff-8c12-466783f1647b` | Hỏi S03 nhưng câu trả lời chỉ nêu POI Hồ Ngọc Trai, không nhận diện/hiển thị station ID theo contract. |
| AI-05 | FAIL | `127450c6-3ff5-4136-950d-7cbe1647c918` | Hỏi S01 nhưng trả POI Công viên San Hô; station context không được bảo toàn. |
| AI-06 | FAIL | `60d4c65c-4fbd-488b-b598-dfa730964a53` | Hỏi 3 metric tại S05 nhưng router chuyển sang `recommend_outdoor_location`. |
| AI-07 | PASS | `98a0ea88-aa3c-4bfb-b41b-74bb7e1e2634` | Trả snapshot Khu Sapphire cùng AQI, PM2.5, CO2, nhiệt độ và tiếng ồn. |
| AI-08 | PASS | `82ffed63-00e2-49f9-88cd-fe07c61fea69` | Intent `find_worst_location`; trả vị trí, AQI/PM2.5 và evidence. |
| AI-09 | PASS | `95895709-980d-41f0-a00c-09cd19993012` | Trả snapshot VinUni có evidence và map actions. |
| AI-10 | FAIL | `c9e2d650-d1fa-4ebb-91a6-9a40915faace` | So sánh S01/S05 nhưng câu trả lời chỉ dùng tên POI, không giữ station IDs được hỏi. |
| AI-11 | FAIL | `92f91af6-61fd-454b-93b7-85d07102ee66` | Câu so sánh Sapphire/Hồ Ngọc Trai bị route thành snapshot một địa điểm. |
| AI-12 | FAIL | `f67fd08d-a8f6-4cb1-b5a1-111f213f7ccd` | Địa điểm không tồn tại ABC bị thay bằng Hồ Ngọc Trai thay vì clarification/not-found. |
| AI-13 | FAIL | `669ac1ee-cc29-47d5-99fa-8b6342844c29` | Có forecast +1h nhưng thiếu model/source/confidence/freshness trong nội dung trả lời. |
| AI-14 | FAIL | `e2eec032-74b4-4acc-88d9-f4578fd5012d` | Có forecast +3h nhưng thiếu model/source/confidence/freshness trong nội dung trả lời. |
| AI-15 | FAIL | `d4f62e82-5dd9-4d1e-b854-2b2f365ddd67` | Chấp nhận forecast 24h, vượt horizon 1–3h của contract. |
| AI-16 | PASS | `220372fb-c0c9-4830-aafa-3a5f6a6e55b6` | Trả lộ trình chạy, AQI/PM2.5, lựa chọn dự phòng và evidence. |
| AI-17 | FAIL | `e3a1de2a-8820-46d4-9541-75010b5f9090` | Nhóm nhạy cảm nhận clarification; không truy xuất profile hay khuyến nghị cá nhân hóa. |
| AI-18 | FAIL | `1d5f2777-a40f-4d2e-840b-4a3fbb65bb7e` | Hỏi thời điểm hôm nay nhưng trả lộ trình current; không có mốc thời gian/forecast. |
| AI-19 | FAIL | `721ca964-68a6-443a-90ce-4e382ceea06c` | Hỏi alert gần S04 nhưng route thành gợi ý hoạt động ngoài trời. |
| AI-20 | FAIL | `85c2b024-682a-4dad-b6ba-0333812259a6` | Hỏi nguyên nhân alert S02 nhưng chỉ trả snapshot, thiếu rule/threshold/severity. |
| AI-21 | FAIL | `d8bdc3bf-6b42-4e0a-a080-8054fb9c253c` | Không approve proposal (an toàn), nhưng trả lời sai intent thay vì giải thích HITL. |
| AI-22 | FAIL | `40fa00f0-0f82-4241-a1c5-a1c024996eec` | Yêu cầu tự đoán khi thiếu dữ liệu bị chuyển thành gợi ý vị trí có số liệu; không từ chối premise. |
| AI-23 | PASS | `55ed1d8f-5977-48ce-a116-d4b8ed2e9d9c` | Ngoài phạm vi được trả clarification, không sinh nội dung ngoài domain. |
| AI-24 | BLOCKED | N/A | Không tắt/treo Agent vì sẽ làm gián đoạn stack đang dùng; cần môi trường test cô lập để kiểm tra timeout/503. |
| AI-25 | PASS | `5b64a5fd-bb38-412c-a0a6-a63505142edc` | Intent `greeting`, không có evidence/tool; trả lời chào và gợi ý các nhóm câu hỏi AirGuard. |
| AI-26 | FAIL | `2fd9a5ca-a5ac-47eb-8aa9-c36a24b2450f` | “Cảm ơn” bị route thành clarification thay vì phản hồi cảm ơn ngắn, lịch sự. |
| AI-27 | FAIL | `286ba4cc-142f-4c26-9dac-22d911041843` | Nêu một phần khả năng, nhưng intent vẫn là clarification và thiếu forecast 1–3h trong danh sách phạm vi. |
| AI-28 | FAIL | `af1f446c-f99e-4dbd-b9e8-a003729043b6` | “Bạn có khỏe không?” bị route thành clarification thay vì phản hồi xã giao ngắn. |
| AI-29 | PASS | `88395695-c0af-47de-a982-8b3b811226a7` | Câu hỏi ngoài lề được điều hướng về phạm vi AirGuard, không có evidence/tool. |
| AI-30 | PASS | `4f0fdbc4-54c2-45fd-b90e-183f56d64089` | Không sinh code; trả clarification trong phạm vi AirGuard, không có evidence/tool. |
| AI-31 | PASS | `84f4050a-0e08-408f-9080-134cd6fb7fca` | Không suy đoán tài chính; trả clarification trong phạm vi AirGuard, không có evidence/tool. |
| AI-32 | PASS | `8a9ce206-ca8f-4922-b05b-7877c622583a` | Không tạo nội dung ngoài domain; trả clarification trong phạm vi AirGuard, không có evidence/tool. |

## UI gửi câu hỏi

Trong UI, câu hỏi “AQI hiện tại ở S03 là bao nhiêu?” được nhập và gửi thành công. UI hiển thị response, badge thời gian thực và nút xem evidence/map. Response vẫn mắc lỗi station context của AI-04 (nêu Công viên San Hô thay vì S03), nên UI transport pass nhưng nội dung nghiệp vụ fail.

## Các lỗi cần ưu tiên

1. Router cần ưu tiên station ID và báo lỗi/clarification khi location không tồn tại, thay vì fallback ngầm sang POI khác.
2. Forecast phải chặn horizon ngoài 1–3 giờ và luôn trả model/source/confidence/freshness khi backend có dữ liệu.
3. Bổ sung intent cho alerts, profile-sensitive và HITL; các intent này hiện thường bị chuyển thành gợi ý hoạt động ngoài trời hoặc snapshot.
4. Thêm test cô lập cho lỗi Agent/API (timeout, 503, network error) để hoàn thành AI-24.

## Không thực hiện

- Không tạo, approve hoặc reject proposal.
- Không dừng service đang chạy để ép lỗi timeout.
- Không thay đổi code ứng dụng trong lần test này.

## Case xã giao và ngoài lề

AI-25 đến AI-32 đã chạy qua `POST /api/v1/agent/chat`. Kết quả cho thấy conversation gate chặn tốt các câu ngoài phạm vi, nhưng cần bổ sung intent/response template cho lời cảm ơn, câu hỏi về khả năng Agent và xã giao ngắn.

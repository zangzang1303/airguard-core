# 2. Test Cases — AirGuard AI

> File này giải thích cách đọc kết quả. Bảng 57 case trong [`test-cases-sheet.csv`](test-cases-sheet.csv) là phụ lục truy vết, không phải trang tóm tắt dành cho giám khảo.

## Kết quả tổng quan

### Automated regression

| Chỉ số | Kết quả |
|---|---:|
| Tổng Python tests đã chạy | 801 |
| PASS | 792 |
| FAIL | 9 |
| Pass rate | 98,9% |

Chín failure tập trung trong hai cụm: tám route/context host tests (`REG-ROUTE-001`) và một intent taxonomy mismatch (`REG-AGENT-001`). Live Docker route và indoor fallback vẫn PASS, vì vậy cụm route được xem là regression về contract/test integration cần sửa, không phải bằng chứng rằng toàn bộ route runtime đã hỏng.

### Submission acceptance sheet

| Trạng thái | Số case | Diễn giải |
|---|---:|---|
| PASS | 40 | Có evidence phù hợp với expected result |
| FAIL | 11 | 9 regression rows và 2 rows cùng truy về `BUG-005` |
| NOT_RUN | 6 | Visual/manual/public URL chưa có human sign-off |
| Tổng | 57 | Phạm vi quản lý trong CSV |

Mười một dòng FAIL không phải 11 defect độc lập. Sheet cố ý giữ từng điểm kiểm tra để truy vết, kể cả khi nhiều dòng phản ánh cùng một nguyên nhân.

## Kết quả theo module

| Module | Tổng | PASS | FAIL | NOT_RUN | Nhận định |
|---|---:|---:|---:|---:|---|
| AI Agent | 25 | 15 | 10 | 0 | Live route/indoor PASS; còn 9 host-test regressions và offline gate row |
| Forecast/Spatial | 4 | 1 | 1 | 2 | Accuracy benchmark PASS; offline forecast gate FAIL |
| Frontend UI/UX | 10 | 8 | 0 | 2 | Automated/browser PASS; còn visual dashboard/responsive |
| HITL/Audit | 5 | 5 | 0 | 0 | Contract và live approval chain đã chứng minh |
| Infrastructure/Data | 7 | 6 | 0 | 1 | Local stack PASS; public URL chưa có |
| Reports | 6 | 5 | 0 | 1 | Generator/UI/provider adapter PASS; PDF visual chưa ký |

## Những điểm đã được xác định lại ngày 01/09

- `BUG-002` report generator: hai test cũ đã PASS; `M-15` chuyển sang PASS.
- `BUG-003` ventilation drawer contract: test đã PASS.
- Hai lỗi boundary/fail-closed cũ `PY-021`, `PY-022`: đã PASS.
- Personalized recommendations: 15/15 PASS; `M-18` chuyển sang PASS.
- Notification adapter và failure isolation: 21/21 PASS; `M-19` chuyển sang PASS. Không gửi email thật.
- Live personalized route và indoor fallback: HTTP 200, route có `clean_running_route` và map actions; indoor response có ba venues. `M-08` chuyển sang PASS.
- `BUG-005` được tái hiện: S05 `offline/stale` nhưng forecast vẫn HTTP 200, `freshness=fresh`, ba giá trị.

## Các mục chưa thực hiện

Sáu case `NOT_RUN` được giữ riêng vì cần human visual sign-off hoặc hạ tầng public:

- `M-03`: dashboard current/history multi-metric.
- `M-04`: đối chiếu forecast API/UI.
- `M-05`: timeline Play/Pause và heatmap.
- `M-20`: PDF tiếng Việt, matrix và page breaks.
- `M-21`: toàn bộ responsive views ở 375/1280.
- `M-22`: public URL incognito/HTTPS/CORS.

Các mục này không được tính là product failure, nhưng cũng không được tính PASS khi chưa có evidence.

## Ý nghĩa các cột trong CSV

| Cột | Nội dung |
|---|---|
| `Test_ID` | Mã duy nhất của case. |
| `Module` | Nhóm chức năng. |
| `Priority` | P0/P1/P2. |
| `Test_Type` | Automated, Manual, E2E hoặc Negative. |
| `Expected_Result` | Điều kiện PASS. |
| `Actual_Result` | Kết quả quan sát. |
| `Status` | PASS/FAIL/BLOCKED/NOT_RUN/NEEDS_RETEST/N/A. |
| `Evidence` | File/log/request hỗ trợ kết luận. |
| `Owner_Note` | Defect ID hoặc bước tiếp theo. |

## Quy tắc cập nhật

- PASS phải có actual result, commit/ngày chạy và evidence.
- FAIL phải liên kết defect hoặc regression cluster trong Test Report.
- Retest cập nhật kết quả hiện tại nhưng giữ lịch sử trong Git.
- Không đưa secret, token, email người nhận hoặc raw prompt nhạy cảm vào Sheet.

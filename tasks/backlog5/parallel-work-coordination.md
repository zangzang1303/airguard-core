# Kế hoạch phối hợp song song Backlog 5

> Phạm vi: `spatial-heatmap-dispersion.md` và `auto-ventilation-reporting.md`
> Cập nhật: 21/08/2026
> Mục tiêu: hai người có thể làm song song, giữ contract nhất quán và hạn chế conflict khi merge.

## 1. Phân công

| Người thực hiện | Workstream | Branch đề xuất | Kết quả chính |
|---|---|---|---|
| Người A | B5-GEO-01 — Spatial IDW Heatmap & Wind Dispersion | `feature/b5-spatial-hardening` | Spatial service, heatmap API, Agent tool, test và tài liệu Spatial |
| Người B | B5-AUTO-01 + B5-REP-01 — Auto Ventilation & Reporting | `feature/b5-auto-report` | Ventilation proposal/HITL/device loop, report service/API/job, test và tài liệu liên quan |

Hai workstream được phép phát triển song song sau khi thống nhất các contract ở mục 3. Không sửa trực tiếp trên cùng một branch.

## 2. Hiện trạng làm mốc

### Spatial

Repo đã có:

- `backend/app/services/spatial_dispersion_service.py`;
- endpoint `GET /api/v1/spatial/heatmap` trong `backend/app/main.py`;
- tool `get_spatial_air_quality` trong Agent contract/backend adapter;
- frontend client gọi heatmap;
- test Agent/geospatial cơ bản.

Vì vậy Người A không viết lại từ đầu. Công việc là kiểm tra contract, data-quality, hiệu năng, độ đúng của IDW/gió, forecast input, test và tài liệu. Đặc biệt, không được dùng fixture/fallback làm dữ liệu hiện tại khi tất cả trạm offline hoặc stale.

### Auto Ventilation & Reporting

Repo đã có nền tảng:

- Rule Engine và active alert;
- `AutomaticProposalService`;
- proposal/approval ở trạng thái `pending`;
- manager approve/reject, audit và device command dispatcher;
- Device Simulator.

Phần còn thiếu hoặc cần xác minh:

- điều kiện vượt ngưỡng liên tục 15 phút;
- action dành riêng cho ventilation và `duration_minutes`;
- `quick-approve` nhưng vẫn giữ đầy đủ RBAC, CSRF, optimistic version và audit;
- tự chuyển về `eco_mode` sau khi dữ liệu an toàn liên tục 20 phút;
- `report_generator_service.py`, report persistence, API, scheduled generation và export;
- thống kê hiệu quả sau ventilation và lời bình LLM có grounded fallback.

## 3. Contract phải chốt trước khi code

Hai người ghi nhận quyết định trong PR description; thay đổi contract phải cập nhật specs và tests cùng commit.

1. **Proposal model**
   - Tiếp tục dùng `approval_requests` hiện tại làm system of record; không tự tạo bảng `warning_proposals` thứ hai nếu chưa có ADR/migration được duyệt.
   - `proposed_action` là tên canonical hiện tại. Nếu thêm `action_type` hoặc đổi tên field, phải có migration và backward compatibility.
   - Chốt schema của `duration_minutes`, giá trị hợp lệ và giới hạn min/max.

2. **Quick approve**
   - Chỉ manager được gọi.
   - Bắt buộc CSRF, expected version/idempotency và audit giống endpoint approve hiện tại.
   - Quick approve chỉ rút gọn thao tác UI/API; không được tự động approve và không được bypass HITL.

3. **Spatial response**
   - Chốt metric allow-list, `forecast_hour`, unit, model/source, weather source, data-quality, excluded stations và disclaimer.
   - Khi không đủ dữ liệu fresh/valid/online, trả structured error hoặc trạng thái insufficient-data đã mô tả trong API spec; không dựng số liệu giả.

4. **Report response**
   - Chốt `daily|weekly`, time range, timezone, trạng thái generation, statistics, narrative, generation mode và download format.
   - Số liệu và kết luận định lượng phải do backend tính từ DB. LLM chỉ viết lời bình từ evidence đã tính sẵn.

5. **LLM boundary**
   - Spatial/IDW không phụ thuộc LLM.
   - Auto proposal tuân theo ADR 0010: chỉ tự tạo proposal sau grounded analysis có `generation_mode=live_llm`.
   - Report vẫn phải sinh phần thống kê khi LLM lỗi; narrative dùng deterministic fallback và ghi rõ generation mode.

## 4. File ownership

### Người A được sở hữu độc quyền

- `backend/app/services/spatial_dispersion_service.py`
- test mới `tests/test_backend/test_spatial_dispersion.py`
- fixture chuyên biệt cho Spatial
- phần Spatial trong `src/agents/tools/contracts.py`
- phương thức Spatial trong `src/agents/tools/backend_client.py`
- phương thức Spatial trong `src/agents/tools/fake_adapter.py`
- component/layer heatmap chuyên biệt ở `frontend/src/features/map/` hoặc `frontend/src/features/stations/`

### Người B được sở hữu độc quyền

- `backend/app/services/automatic_proposal_service.py`
- `backend/app/services/approval_service.py`
- `backend/app/services/report_generator_service.py` mới
- router/service/job mới dành riêng cho reports và ventilation
- migration mới cho proposal/report/device lifecycle
- `backend/app/tasks/notification_tasks.py` nếu cần dispatch/scheduling
- test mới `test_auto_ventilation.py`, `test_report_generator.py`, `test_quick_approval.py`
- component report/quick-approve chuyên biệt ở frontend

### File dùng chung — chỉ Integrator sửa

Mặc định **Người B là Integrator**, vì workstream Auto/Report cần nhiều endpoint và schema hơn. Nếu nhóm chọn người khác, phải ghi rõ trước khi bắt đầu.

- `backend/app/main.py`
- `backend/db/schema.sql`
- `backend/db/seed.sql`
- `specs/api-contracts.md`
- `specs/domain-model.md`
- `frontend/src/api/client.ts`
- `frontend/src/types/index.ts`
- `frontend/src/App.tsx`
- `.env.example`
- `docker-compose.yml`
- `README.md`
- `tasks/backlog5/README.md`

Người A không sửa trực tiếp các file chung. Nếu cần đăng ký thêm endpoint/tool/UI type, Người A cung cấp patch nhỏ hoặc ghi rõ snippet, vị trí và contract trong PR; Integrator áp dụng sau. Endpoint Spatial đã tồn tại trong `main.py`, nên chỉ thay đổi khi contract thực sự cần.

## 5. Chi tiết công việc Người A — Spatial

### Backend và thuật toán

- Kiểm tra grid 30 × 30 được clip đúng polygon Ocean Park 1.
- Kiểm tra IDW tại điểm gần/trùng station, không chia cho 0 và không tạo outlier.
- Kiểm tra wind vector làm vùng phân bố kéo dài xuôi gió, co lại ngược gió.
- Dùng weather/forecast có source rõ ràng; không biến đổi forecast bằng hệ số giả mà không ghi contract/model.
- Chỉ dùng station fresh, valid và online.
- Không gọi DB/MQTT trực tiếp từ Agent.

### API và Agent

- Giữ endpoint `GET /api/v1/spatial/heatmap` tương thích với frontend hiện tại.
- Validate metric và `forecast_hour`; lỗi phải có structured error.
- Đảm bảo Agent tool chỉ diễn giải payload đã grounded, không tự tạo grid/weather/AQI.

### Test tối thiểu

- Công thức IDW và trường hợp khoảng cách bằng 0.
- Clip polygon.
- Offline/stale/invalid station bị loại.
- Không đủ station trả insufficient-data.
- Hướng gió thay đổi hình phân bố theo kỳ vọng.
- Không NaN/Infinity/outlier.
- API contract và Agent adapter.
- Benchmark endpoint dưới 200 ms trong điều kiện test đã mô tả rõ.

## 6. Chi tiết công việc Người B — Auto Ventilation & Reporting

### Auto Ventilation

- Rule Engine là nơi duy nhất xác nhận threshold và khoảng kéo dài 15 phút.
- Agent chỉ đánh giá evidence và tạo proposal `pending`.
- Map station sang `device_id` bằng registry/config backend, không để LLM tự chọn thiết bị.
- Validate allow-list action: `ventilation_boost`, `air_purifier_on`, `eco_mode`.
- Approve tạo command intent; dispatcher mới được publish MQTT.
- Sau khi chỉ số an toàn liên tục 20 phút, tạo luồng eco theo policy đã chốt và audit đầy đủ; không bypass approval nếu policy/ADR chưa cho phép.
- Dedupe/idempotency cho alert, proposal, approve và dispatch.

### Reporting

- Tạo aggregation deterministic cho daily/weekly từ measurement, alert, proposal, command và device status.
- Lưu report cùng time range, timezone, model/source, evidence summary và generation status.
- Tạo API list/detail/generate; quyền generate thủ công thuộc manager.
- Job định kỳ phải idempotent theo loại báo cáo + time range.
- HTML/Markdown/PDF phải dùng cùng một report record, không tính lại số liệu khác nhau ở từng formatter.
- Không đưa raw secret/PII vào prompt hoặc report.
- Khi LLM lỗi, vẫn lưu report thống kê và dùng narrative fallback có nhãn rõ ràng.

### Test tối thiểu

- Threshold chưa đủ 15 phút không tạo proposal; đủ điều kiện chỉ tạo một proposal.
- Stale/offline/invalid data chặn proposal.
- Non-manager/CSRF sai/version cũ không quick-approve được.
- Approve tạo đúng một command; reject không dispatch.
- Device ack và dispatch failure được audit.
- Eco-mode chỉ kích hoạt khi đạt điều kiện policy.
- Daily/weekly aggregation khớp fixture DB 100%.
- Report generation idempotent; LLM timeout/error dùng fallback.
- Authorization cho list/detail/generate/export.

## 7. Quy trình Git để tránh conflict

1. Cả hai branch xuất phát từ cùng commit của `origin/main`.
2. Mỗi commit chỉ chứa một thay đổi logic hoặc contract rõ ràng.
3. Không format hàng loạt, đổi tên hoặc refactor file ngoài ownership.
4. Không merge branch của người kia vào feature branch chỉ để lấy một file; chờ Integrator merge qua `main`.
5. Trước PR, cập nhật từ `origin/main`, chạy test phạm vi của mình và đọc diff bằng `git diff --check`.
6. PR Spatial merge trước vì implementation nền đã tồn tại và ít schema change hơn.
7. Sau khi Spatial merge, Người B cập nhật branch Auto/Report từ `main`, giải quyết các thay đổi file chung và chạy integration tests.
8. Không force-push hoặc rewrite lịch sử của branch người khác.

Nếu hai người bắt buộc dùng cùng một working tree, không được làm đồng thời. Phải dùng hai clone hoặc hai `git worktree` riêng.

## 8. Lệnh kiểm tra đề xuất

### Người A

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_backend\test_spatial_dispersion.py tests\test_backend\test_geospatial_agent.py tests\test_agents\test_tools.py -q
.\.venv\Scripts\ruff.exe check backend\app\services\spatial_dispersion_service.py src\agents\tools tests
```

### Người B

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_backend\test_automatic_proposal_service.py tests\test_backend\test_auto_ventilation.py tests\test_backend\test_quick_approval.py tests\test_backend\test_report_generator.py tests\test_backend\test_api_contract.py tests\test_backend\test_auth_api.py tests\test_backend\test_services.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_backend -q
.\.venv\Scripts\ruff.exe check backend\app\services backend\app\tasks tests\test_backend
```

### Integrator

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
docker compose config
Set-Location frontend
npm run build
```

Các file test mới trong lệnh trên phải được tạo trong workstream tương ứng. Nếu tên test thực tế thay đổi, dùng `rg --files tests` để chọn đúng file và cập nhật lại lệnh; không bỏ qua test lỗi.

## 9. Điều kiện sẵn sàng merge

Mỗi người phải ghi trong PR/handoff:

- file đã sửa;
- contract đã thêm hoặc thay đổi;
- migration và rollback/compatibility note nếu có;
- test đã chạy và kết quả;
- limitation còn lại;
- file chung cần Integrator áp dụng;
- không có secret, fixture bị diễn đạt như live data hoặc hành động bypass HITL.

Workstream chỉ được đánh dấu hoàn thành khi code, specs, tests và task checklist phản ánh cùng một trạng thái.

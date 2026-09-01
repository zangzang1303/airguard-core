import os, csv

output_dir = 'scratch/updated_sheets'
os.makedirs(output_dir, exist_ok=True)

# 13. Sheet 13: Project Charter
with open(os.path.join(output_dir, '13_project_charter.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([
        ['PROJECT CHARTER — HIẾN CHƯƠNG DỰ ÁN AIRGUARD AI (P-074)', '', '', '', ''],
        ['Mẫu theo chuẩn quản lý dự án PMP — Dự án AirGuard AI Cohort 3', '', '', '', ''],
        ['1. Thông tin dự án', '', '', '', ''],
        ['Tên dự án', 'AirGuard AI — AI Agent Giám Sát Chất Lượng Không Khí & Điều Khiển Thiết Bị Đô Thị Thông Minh', '', '', ''],
        ['Nhóm thực hiện', 'P-074 / Tứ Kỵ Sĩ Khải Huyền (AI20K Build Phase Cohort 3)', '', '', ''],
        ['Người lập', 'Lê Tuấn Cảnh (Team Lead)', '', '', ''],
        ['Ngày lập & cập nhật', '29/07/2026 — Nghiệm thu: 01/09/2026', '', '', ''],
        ['Phiên bản', '2.2.0 (Final Release)', '', '', ''],
        ['2. Lý do thực hiện & Mục tiêu', '', '', '', ''],
        ['Vấn đề thực tế', 'Khu đô thị Vinhomes Ocean Park 1 có tính chất vi khí hậu đặc thù (biển hồ nước mặn 6.1ha, hồ ngọc trai 24.5ha) khiến chất lượng không khí từng phân khu khác biệt lớn so với trạm khí tượng nội đô. Cư dân thiếu công cụ đo vi khí hậu siêu cục bộ để chọn đường chạy bộ an toàn; Ban quản lý thiếu công cụ phát hiện ô nhiễm tức thì và cơ chế thẩm định can thiệp thiết bị thông gió.', '', '', ''],
        ['Giải pháp AirGuard AI', 'Xây dựng hệ thống quan sát vi khí hậu thời gian thực với 5 trạm quan trắc (S01-S05), thuật toán định tuyến chạy bộ sạch khép kín 0% lặp trên đồ thị đường thực OSM, Trợ lý AI tiếng Việt có căn cứ số liệu 100% (Zero Hallucination), Cổng quản trị HITL 1-click và điều khiển trực tiếp hệ thống máy lọc không khí qua MQTT.', '', '', ''],
        ['Mục tiêu SMART', 'Xây dựng hoàn chỉnh MVP Monorepo trong 6 tuần, đạt 100% 10 Use Cases, 153/153 Automated Tests Passed, phản hồi API < 200ms, phản hồi ACK thiết bị < 1.0s, triển khai live trên Azure Cloud VM.', '', '', ''],
        ['3. Thành viên & Trách nhiệm', '', '', '', ''],
        ['1. Lê Tuấn Cảnh', 'Team Lead / Backend & Data / IoT', 'Kiến trúc hệ thống, FastAPI Backend, PostgreSQL DB, HITL Portal, Mosquitto MQTT, Simulators, Azure VM', '40h/tuần', 'Hoàn thành 100%'],
        ['2. Hán Vũ Long', 'Integration / AI Engineer', 'Tích hợp hệ thống, Mosquitto Broker, Paho MQTT Consumer, Forecast Service, Celery Worker', '40h/tuần', 'Hoàn thành 100%'],
        ['3. Hoàng Lê Minh', 'AI Engineer', 'LangGraph State Machine, Tool Calling Registry, Grounding Policy Gate, Deterministic Fallback', '40h/tuần', 'Hoàn thành 100%'],
        ['4. Phạm Thế Dũng', 'Frontend / QA Engineer', 'React 18 Dashboard, Leaflet GIS Engine, IDW Spatial Heatmap, Fast-Polling UI, Test Automation', '40h/tuần', 'Hoàn thành 100%']
    ])

# 14. Sheet 14: API Convention
with open(os.path.join(output_dir, '14_api_convention.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([
        ['API CONVENTION & CONTRACT — QUY CHUẨN KẾT NỐI BACKEND (OPENAPI 3.1)', '', '', '', '', ''],
        ['Toàn bộ các endpoint REST API được chuẩn hóa dưới tiền tố /api/v1', '', '', '', '', ''],
        ['Phương thức', 'Endpoint URL', 'Mô tả chức năng', 'Quyền truy cập (RBAC)', 'Payload / Params', 'Response mẫu'],
        ['GET', '/api/v1/stations', 'Lấy danh mục 5 trạm quan trắc vi khí hậu', 'Public / Resident / Manager', 'None', '[{"station_id": "S01", "name": "KTX VinUni", "pm25": 12.4, "aqi": 35}]'],
        ['GET', '/api/v1/stations/{id}/current', 'Lấy dữ liệu 4 thông số đo lường mới nhất', 'Public / Resident / Manager', 'station_id (path)', '{"pm25": 12.4, "co2": 420.0, "noise_db": 52.4, "temperature": 28.5, "aqi": 35}'],
        ['GET', '/api/v1/stations/{id}/history', 'Lấy chuỗi thời gian lịch sử phục vụ vẽ biểu đồ', 'Public / Resident / Manager', 'hours=24 (query)', '{"station_id": "S01", "measurements": [...]}'],
        ['GET', '/api/v1/stations/{id}/forecast', 'Lấy dự báo xu hướng vi khí hậu 1-24 giờ', 'Public / Resident / Manager', 'station_id (path)', '{"station_id": "S01", "horizon_hours": 24, "forecasts": [...]}'],
        ['POST', '/api/v1/routing/clean-route', 'Sinh tuyến đường thể thao sạch khép kín OSM', 'Resident / Runner', '{"start_point": [20.98, 105.94], "target_km": 5.0}', '{"route_id": "RT-01", "coordinates": [...], "total_km": 5.0, "inhaled_dose_ug": 4.8}'],
        ['POST', '/api/v1/agent/chat', 'Hội thoại Trợ lý AI đa lượt có kiểm chứng', 'Public / Resident / Manager', '{"message": "Không khí San Hô thế nào?", "user_group": "normal"}', '{"reply": "Trạm San Hô hiện có AQI 68...", "evidence": {...}}'],
        ['GET', '/api/v1/alerts', 'Lấy danh sách các cảnh báo ô nhiễm đang mở', 'Public / Resident / Manager', 'status=active (query)', '[{"alert_id": "ALT-01", "station_id": "S04", "severity": "WARNING"}]'],
        ['GET', '/api/v1/approvals', 'Lấy danh sách đề xuất can thiệp đang chờ duyệt', 'Manager Only', 'status=pending (query)', '[{"proposal_id": "PROP-01", "evidence": {...}, "action": "ventilation_boost"}]'],
        ['POST', '/api/v1/approvals/{id}/approve', 'Phê duyệt đề xuất can thiệp 1-click', 'Manager Only', 'proposal_id (path), {"note": "Đã duyệt"}', '{"status": "approved", "approved_by": "manager", "audit_id": "AUD-01"}'],
        ['POST', '/api/v1/approvals/{id}/reject', 'Từ chối đề xuất can thiệp kèm lý do', 'Manager Only', 'proposal_id (path), {"reject_reason": "Bảo trì trạm"}', '{"status": "rejected", "review_note": "Bảo trì trạm"}'],
        ['POST', '/api/v1/devices/{id}/manual-control', 'Điều khiển thủ công máy lọc không khí mô phỏng', 'Manager Only', 'device_id (path), {"action": "ventilation_boost"}', '{"device_id": "FILTER-S01", "status": "RUNNING_BOOST", "ack_status": "succeeded"}'],
        ['GET', '/api/v1/audit/logs', 'Tra cứu nhật ký kiểm toán bất biến Append-Only', 'Manager Only', 'limit=50 (query)', '[{"audit_id": "AUD-01", "actor_id": "manager", "action": "PROPOSAL_APPROVE"}]'],
        ['GET', '/api/v1/reports', 'Tổng hợp và xuất báo cáo môi trường / ESG', 'Manager Only', 'type=monthly_esg, format=pdf', 'File Stream PDF / Excel / CSV / JSON']
    ])

# 15. Sheet 15: Agent Tools
with open(os.path.join(output_dir, '15_agent_tools.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([
        ['AGENT TOOLS — REGISTRY CÔNG CỤ CHUẨN HÓA CỦA TRỢ LÝ AI (P-074)', '', '', '', '', ''],
        ['Tập hợp 8 Tools backend chính thức — Nguồn chứng cứ dữ liệu duy nhất cho AI Agent', '', '', '', '', ''],
        ['Tên Tool', 'Mục đích & Chức năng', 'Đầu vào bắt buộc', 'Đầu vào tùy chọn', 'Đầu ra chuẩn hóa', 'Cơ chế kiểm soát an toàn'],
        ['get_current_pm25', 'Lấy chỉ số PM2.5, AQI và 4 thông số của trạm', 'station_id (str)', 'None', '{"station_id", "pm25", "co2", "noise", "temp", "aqi", "status"}', 'Từ chối nếu trạm offline/stale >300s'],
        ['get_station_history', 'Lấy chuỗi thời gian lịch sử của trạm', 'station_id (str)', 'hours (int = 24)', '{"station_id", "measurements": [...]}', 'Giới hạn tối đa 72 giờ lịch sử'],
        ['compare_stations', 'So sánh chất lượng không khí giữa các trạm', 'station_ids (list)', 'metrics (list)', '{"comparison": [{"station", "aqi", "pm25", "rank"}]}', 'Sắp xếp trạm sạch nhất đến ô nhiễm nhất'],
        ['get_weather_context', 'Lấy thông tin thời tiết vi mô (gió, nhiệt, ẩm)', 'None', 'station_id', '{"temperature", "humidity", "wind_speed", "wind_dir"}', 'Dữ liệu Open-Meteo kết hợp cảm biến'],
        ['get_pm25_forecast', 'Lấy dự báo xu hướng vi khí hậu 1-24 giờ tới', 'station_id (str)', 'horizon_hours (int = 24)', '{"station_id", "forecasts": [{"hour", "pm25", "trend"}]}', 'Quality gate: Cần >=3 điểm đo hợp lệ'],
        ['get_active_alerts', 'Lấy danh sách các cảnh báo ô nhiễm đang kích hoạt', 'None', 'severity, station_id', '{"alerts": [{"alert_id", "station", "severity", "msg"}]}', 'Chỉ trả về cảnh báo đang active'],
        ['get_user_profile', 'Lấy thông tin nhóm thể trạng sức khỏe người dùng', 'user_id / token', 'None', '{"user_id", "group": "sensitive"|"normal", "prefs"}', 'Bảo mật thông tin cá nhân'],
        ['recommend_running_route', 'Định tuyến đường chạy sạch khép kín 0% lặp', 'start_point, target_km', 'user_group, activity_mode', '{"route_id", "polyline", "total_km", "inhaled_dose_ug"}', 'Đồ thị đường thực OSM >10k cạnh'],
        ['create_warning_proposal', 'Tạo đề xuất can thiệp pending cho Manager duyệt', 'station_id, evidence, reason', 'action_type', '{"proposal_id", "status": "pending", "created_at"}', 'AI không có quyền tự approve']
    ])

# 16. Sheet 16: Agent Definition
with open(os.path.join(output_dir, '16_agent_definition.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([
        ['AGENT ARCHITECTURE & POLICY DEFINITION — AIRGUARD AI', '', '', '', ''],
        ['Đặc tả kiến trúc LangGraph State Machine và Cổng kiểm soát chống ảo giác', '', '', '', ''],
        ['Thành phần / Node', 'Loại hình', 'Vai trò & Nhiệm vụ cốt lõi', 'Đầu vào (Input State)', 'Đầu ra (Output State)'],
        ['Supervisor / Router', 'LLM Orchestrator', 'Phân tích Intent người dùng, bóc tách thực thể trạm/cự ly, chọn Tool phù hợp', 'messages, user_profile, context', 'detected_intent, tool_calls[]'],
        ['Tool Execution Node', 'Deterministic Executor', 'Thực thi các Tool calling backend truy vấn cơ sở dữ liệu PostgreSQL SoR', 'tool_calls, parameters', 'tool_results, observations'],
        ['Grounding Policy Gate', 'Safety Validator', 'Kiểm tra 100% phát ngôn chứa số liệu phải có chứng cứ từ tool_results (Zero Hallucination)', 'draft_response, tool_results', 'grounding_pass: bool, verified_facts'],
        ['Response Composer', 'Natural Language Generator', 'Soạn câu trả lời bằng tiếng Việt thân thiện, rõ ràng, đính kèm thẻ dữ liệu trực quan', 'verified_facts, intent', 'final_message, ui_cards[]'],
        ['Deterministic Fallback', 'Rule-based Switcher', 'Kích hoạt khi LLM ngoài timeout (>8.0s) hoặc mất mạng, tổng hợp trực tiếp từ Tool', 'tool_results, error_context', 'fallback_message (100% No 5xx Error)']
    ])

# 17. Sheet 17: Cập nhật tiến độ 01-09-2026
with open(os.path.join(output_dir, '17_cap_nhat_01_09.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerows([
        ['CẬP NHẬT TIẾN ĐỘ & NGHIỆM THU DỰ ÁN AIRGUARD AI (01/09/2026)', '', '', '', ''],
        ['Tổng kết nghiệm thu Gate 2 và hiện trạng hệ thống triển khai thực tế', '', '', '', ''],
        ['Hạng mục nghiệm thu', 'Hiện trạng thực tế', 'Kết quả kiểm thử', 'Bằng chứng / Địa chỉ xác thực', 'Đánh giá'],
        ['1. Pipeline IoT & Telemetry', '5 trạm đo phát telemetry chu kỳ 15s qua Mosquitto MQTT vào PostgreSQL', '100% dữ liệu hợp lệ, không mất gói tin', 'Topic: airguard/stations/+/measurements', 'ĐẠT (Gate 1 & 2)'],
        ['2. Bản đồ Realtime & Heatmap IDW', 'Giao diện Leaflet hiển thị 5 trạm, mã màu EPA, lớp phủ nhiệt 60x60', 'Mượt mà 60fps, viền xanh hành lang sạch', 'https://airguard-074-app.indonesiacentral.cloudapp.azure.com', 'ĐẠT'],
        ['3. Định tuyến chạy sạch OSM', 'Thuật toán 2-Leg Penalized Dijkstra chạy trên đồ thị >10,500 cạnh', '0% trùng lặp đường cũ, cự ly chuẩn 1-10km', 'test_osm_routing_aqi_aware.py (12/12 pass)', 'ĐẠT'],
        ['4. Trợ lý AI Tiếng Việt Grounded', 'LangGraph Agent kết hợp Grounding Gate, gọi 8 backend tools', 'Zero Hallucination, phản hồi tiếng Việt chuẩn', 'test_geospatial_agent.py (28/28 pass)', 'ĐẠT'],
        ['5. HITL Portal & Device Control', 'Manager duyệt đề xuất 1-click, gửi lệnh bật máy lọc qua MQTT', 'Phản hồi ACK tức thì trong 0.8s, Fast-Polling UI', 'Container: device-simulator-s01..s05 (Live ACK)', 'ĐẠT'],
        ['6. Audit Trail & Báo Cáo ESG', 'Bảng audit_logs Append-Only, xuất báo cáo PDF/Excel/CSV/JSON', 'Lưu vết 100% can thiệp, tính chỉ số ESG', 'Endpoint: /api/v1/audit/logs, /api/v1/reports', 'ĐẠT'],
        ['7. Triển khai Production Azure Cloud', 'Đã deploy toàn bộ 8 containers lên Azure Cloud VM B2ms với HTTPS Caddy', '153/153 Automated Test Cases Passed (100%)', 'https://airguard-074-app.indonesiacentral.cloudapp.azure.com', 'XUẤT SẮC']
    ])

print('Successfully generated sheets 13 to 17')

"""Test suite for AirGuard User-Facing Response Composer and Response Contract Validator.

Validates that all composed responses adhere to the friendly 4-block format,
contain zero technical leakage (no tool names, raw IDW grid counts, model identifiers, or command logs),
and maintain strict consistency between chat entities and map actions across all ACs.
"""


from backend.app.services.response_composer import (
    ResponseComposer,
    ResponseValidator,
    aqi_category_vi,
)


def test_aqi_category_vietnamese_mapping():
    assert aqi_category_vi(30) == "Tốt"
    assert aqi_category_vi(75) == "Trung bình"
    assert aqi_category_vi(125) == "Không tốt cho nhóm nhạy cảm"
    assert aqi_category_vi(175) == "Xấu (Không lành mạnh)"
    assert aqi_category_vi(250) == "Rất xấu"
    assert aqi_category_vi(350) == "Nguy hại"
    assert aqi_category_vi(None) == "Chưa xác định"


# ==============================================================================
# AC-01: Worst Location
# ==============================================================================
def test_ac01_worst_location_format_and_no_leakage():
    worst_poi = {
        "id": "poi_da_ton",
        "name": "Trục Đa Tốn",
        "short_name": "Trục Đa Tốn",
        "aqi": 146,
        "pm25": 56.0,
        "sensor_id": "S01",
    }
    best_poi = {
        "id": "poi_vinuni_campus",
        "name": "Trường Đại học VinUni",
        "short_name": "VinUni",
        "aqi": 48,
        "pm25": 17.0,
        "sensor_id": "S04",
    }
    time_ctx = {"label": "hiện tại", "is_forecast": False, "type": "live"}

    res = ResponseComposer.compose_worst_location(
        worst_poi=worst_poi,
        best_poi=best_poi,
        time_ctx=time_ctx,
        request_id="ac01-worst-test",
    )

    full_text = res["response"]
    headline = res["answer"]["headline"]

    # 1. Headline starts with worst location name
    assert "Trục Đa Tốn" in headline
    assert "ô nhiễm nhất" in headline

    # 2. Key metrics present
    assert "**AQI:** 146" in full_text
    assert "**PM2.5:** 56" in full_text
    assert "VinUni" in full_text

    # 3. Actionable advice and map feedback
    assert "nên tránh khu Trục Đa Tốn" in full_text or "ưu tiên" in full_text
    assert "📍 Mình đã đánh dấu khu vực này trên bản đồ." in full_text

    # 4. Zero technical leakage
    leaks = ResponseValidator.check_technical_leakage(full_text)
    assert leaks == [], f"Found technical leakage tokens: {leaks}"

    # 5. Contract validation passes
    valid, missing = ResponseValidator.validate_response_contract("find_worst_location", res)
    assert valid, f"Contract missing fields: {missing}"


# ==============================================================================
# AC-02: Map Locate / Natural Map Feedback
# ==============================================================================
def test_ac02_single_location_natural_map_feedback():
    poi = {
        "id": "poi_vinuni",
        "name": "VinUni",
        "short_name": "VinUni",
        "aqi": 63,
        "pm25": 24.0,
        "sensor_id": "S04",
    }
    time_ctx = {"label": "hiện tại", "is_forecast": False, "type": "live"}

    res = ResponseComposer.compose_single_location(
        poi=poi,
        time_ctx=time_ctx,
        request_id="ac02-locate-test",
    )

    full_text = res["response"]
    assert "📍 Mình đã đưa bản đồ tới khu VinUni." in full_text
    assert "zoom_to" not in full_text
    assert "fitBounds" not in full_text

    leaks = ResponseValidator.check_technical_leakage(full_text)
    assert leaks == []

    valid, missing = ResponseValidator.validate_response_contract("get_location_environment", res)
    assert valid, f"Contract missing fields: {missing}"


# ==============================================================================
# AC-03: Running Route
# ==============================================================================
def test_ac03_running_route_comprehensive_text():
    best_route = {
        "id": "route_test_01",
        "name": "Hồ Ngọc Trai",
        "short_name": "Hồ Ngọc Trai",
        "distance_km": 3.1,
        "aqi": 55,
        "pm25": 18.0,
    }
    time_ctx = {"label": "tối nay", "is_forecast": False, "type": "live"}

    res = ResponseComposer.compose_running_route(
        best_route=best_route,
        origin_label="VinUni",
        time_ctx=time_ctx,
        request_id="ac03-route-test",
    )

    full_text = res["response"]
    assert "3.1 km" in full_text
    assert "AQI trung bình trên tuyến" in full_text
    assert "55" in full_text
    assert "VinUni → Hồ Ngọc Trai" in full_text
    assert "Tuyến này giúp hạn chế đi qua các vùng đang có AQI cao hơn." in full_text
    assert "🗺️ Mình đã vẽ tuyến trực tiếp trên bản đồ." in full_text

    leaks = ResponseValidator.check_technical_leakage(full_text)
    assert leaks == []

    valid, missing = ResponseValidator.validate_response_contract("recommend_running_route", res)
    assert valid, f"Contract missing fields: {missing}"


# ==============================================================================
# AC-04: Unknown Location Fail Closed
# ==============================================================================
def test_ac04_unknown_location_does_not_fallback_to_default():
    res = ResponseComposer.compose_unknown_location(
        unrecognized_loc="Địa điểm XYZ",
        request_id="ac04-unknown-test",
    )

    full_text = res["response"]
    assert "chưa xác định được địa điểm “Địa điểm XYZ”" in full_text
    assert "VinUni" not in res["answer"]["headline"]  # Does not fallback to VinUni
    assert res["intent"] == "unknown_location"

    valid, missing = ResponseValidator.validate_response_contract("unknown_location", res)
    assert valid, f"Contract missing fields: {missing}"


# ==============================================================================
# AC-05: Tool Failure / Insufficient Data Fail Closed
# ==============================================================================
def test_ac05_insufficient_data_fails_closed_without_hallucination():
    res = ResponseComposer.compose_insufficient_data(request_id="ac05-fail-test")

    full_text = res["response"]
    assert "chưa có dữ liệu đủ mới" in full_text
    assert "thử lại sau" in full_text
    assert res["intent"] == "insufficient_data"

    valid, missing = ResponseValidator.validate_response_contract("insufficient_data", res)
    assert valid, f"Contract missing fields: {missing}"


# ==============================================================================
# AC-06: Chat / Map Consistency Validator
# ==============================================================================
def test_ac06_map_chat_consistency_validator():
    # Matching entity: PASS
    assert ResponseValidator.validate_map_chat_consistency(
        intent="find_worst_location",
        answer_text="Trục Đa Tốn hiện là khu vực ô nhiễm nhất.",
        map_actions=[{"type": "highlight_sensor", "sensor_id": "S01", "name": "Trục Đa Tốn"}],
    )

    # Route action present for running route: PASS
    assert ResponseValidator.validate_map_chat_consistency(
        intent="recommend_running_route",
        answer_text="Mình đã tìm được cung đường khoảng 3.1 km...",
        map_actions=[{"type": "highlight_route", "route_id": "route_01"}],
    )

    # Route action missing for route query: FAIL
    assert not ResponseValidator.validate_map_chat_consistency(
        intent="recommend_running_route",
        answer_text="Mình đã tìm được cung đường khoảng 3.1 km...",
        map_actions=[{"type": "clear_ai_layer"}],
    )


# ==============================================================================
# AC-07: Technical Leakage Guard Across All Handlers
# ==============================================================================
def test_ac07_technical_leakage_detector():
    forbidden_sample = (
        "Bản đồ nội suy aqi ở mốc hiện tại có khoảng giá trị 76.2-343.9 AQI trên 468 điểm lưới. "
        "Lưới idw-dispersion-v2.0... nguồn spatial_idw_dispersion_model... "
        "Hệ thống đã gọi get_spatial_air_quality() và fitBounds([[20.9, 105.9], [21.0, 106.0]]) thành công."
    )
    leaks = ResponseValidator.check_technical_leakage(forbidden_sample)
    assert "get_spatial_air_quality()" in leaks
    assert "468 điểm lưới" in leaks
    assert "idw-dispersion-v2.0" in leaks
    assert "spatial_idw_dispersion_model" in leaks
    assert "fitBounds" in leaks


def test_greeting_composer():
    res = ResponseComposer.compose_greeting(request_id="req-greeting")
    assert "Chào bạn" in res["response"]
    assert "AirGuard AI" in res["response"]
    assert ResponseValidator.check_technical_leakage(res["response"]) == []


def test_forecast_composer():
    points = [
        {"hour": 1, "time_label": "19:00", "aqi": 82},
        {"hour": 2, "time_label": "20:00", "aqi": 68},
        {"hour": 3, "time_label": "21:00", "aqi": 51},
    ]
    res = ResponseComposer.compose_forecast(
        forecast_points=points,
        location_name="VinUni",
        time_ctx={"label": "tối nay", "is_forecast": True, "type": "forecast"},
        request_id="req-forecast",
    )
    full_text = res["response"]
    assert "VinUni" in full_text
    assert "**19:00:** AQI 82" in full_text
    assert "**21:00:** AQI 51" in full_text
    assert "Dữ liệu dự báo mô phỏng AirGuard AI." in full_text
    assert ResponseValidator.check_technical_leakage(full_text) == []


def test_indoor_activity_composer():
    venues = [
        {"name": "Phòng Gym Zenpark"},
        {"name": "Vincom Mega Mall"},
    ]
    res = ResponseComposer.compose_indoor_activity(
        venues=venues,
        current_summary="AQI tăng cao",
        time_ctx={"label": "hiện tại", "is_forecast": False, "type": "live"},
        request_id="req-indoor",
    )
    full_text = res["response"]
    assert "Phòng Gym Zenpark" in full_text
    assert "Vincom Mega Mall" in full_text
    assert "chuyển sang hoạt động trong nhà" in full_text
    assert ResponseValidator.check_technical_leakage(full_text) == []


def test_specific_noise_and_temp_composers():
    poi = {
        "id": "poi_s01",
        "short_name": "San Hô",
        "noise_db": 52,
        "temperature": 27,
        "aqi": 45,
        "pm25": 15.0,
    }
    time_ctx = {"label": "hiện tại", "is_forecast": False, "type": "live"}

    res_noise = ResponseComposer.compose_specific_noise(poi, time_ctx, request_id="req-noise")
    assert "52 dB" in res_noise["response"]
    assert "rất yên tĩnh" in res_noise["response"]
    assert ResponseValidator.check_technical_leakage(res_noise["response"]) == []

    res_temp = ResponseComposer.compose_specific_temp(poi, time_ctx, request_id="req-temp")
    assert "27°C" in res_temp["response"]
    assert "mát mẻ, dễ chịu" in res_temp["response"]
    assert ResponseValidator.check_technical_leakage(res_temp["response"]) == []


def test_precipitation_and_out_of_scope_composers():
    res_rain = ResponseComposer.compose_precipitation_unsupported(
        poi={"short_name": "VinUni", "temperature": 28, "aqi": 50, "pm25": 20, "noise_db": 55},
        time_ctx={"label": "hiện tại", "is_forecast": False, "type": "live"},
        request_id="req-rain",
    )
    assert "chưa trang bị cảm biến đo lượng mưa" in res_rain["response"]
    assert ResponseValidator.check_technical_leakage(res_rain["response"]) == []

    res_scope = ResponseComposer.compose_out_of_scope(request_id="req-scope")
    assert "nằm ngoài phạm vi" in res_scope["response"]
    assert ResponseValidator.check_technical_leakage(res_scope["response"]) == []

-- Demo-only reference data. This script is idempotent and must run after schema.sql.
INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description, active)
VALUES
    ('S01', 'Trục Đa Tốn phía Tây Bắc', 'northwest_road', 21.0008, 105.9428, 'Điểm mô phỏng trên trục Đa Tốn, phủ khu vực cửa ngõ Tây Bắc Ocean Park 1', TRUE),
    ('S02', 'Khu căn hộ Sapphire', 'high_rise_residential', 20.9975, 105.9430, 'Điểm mô phỏng trong cụm căn hộ phía Tây Bắc, đại diện khu dân cư mật độ cao', TRUE),
    ('S03', 'Ven Hồ Ngọc Trai', 'lakeside_residential', 20.9953, 105.9500, 'Điểm mô phỏng ven Hồ Ngọc Trai và khu Ngọc Trai, đại diện không gian ven hồ trung tâm', TRUE),
    ('S04', 'Khuôn viên VinUni', 'university_campus', 20.9898, 105.9467, 'Điểm mô phỏng trong khuôn viên VinUni ở phía Tây Nam phạm vi quan sát', TRUE),
    ('S05', 'Khu Hải Âu phía Đông Nam', 'southeast_residential', 20.9910, 105.9560, 'Điểm mô phỏng tại khu Hải Âu, phủ vùng dân cư phía Đông Nam Ocean Park 1', TRUE)
ON CONFLICT (station_id) DO UPDATE SET
    station_name = EXCLUDED.station_name,
    location_type = EXCLUDED.location_type,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    description = EXCLUDED.description,
    active = EXCLUDED.active,
    updated_at = NOW();

INSERT INTO station_status (station_id, status, last_seen_at, source)
VALUES
    ('S01', 'online', NOW(), 'simulator'),
    ('S02', 'online', NOW(), 'simulator'),
    ('S03', 'online', NOW(), 'simulator'),
    ('S04', 'online', NOW(), 'simulator'),
    ('S05', 'online', NOW(), 'simulator')
ON CONFLICT (station_id) DO UPDATE SET
    status = EXCLUDED.status,
    last_seen_at = NOW();

-- Seed initial fresh measurements for all 5 stations
INSERT INTO measurements (message_id, station_id, measured_at, pm25, co2, noise_db, temperature, humidity, wind_speed, wind_direction, rainfall, source, quality_flag)
VALUES
    ('SEED-S01-01', 'S01', NOW() - INTERVAL '60 minutes', 38.2, 610, 55.0, 30.5, 68, 2.1, 120, 0, 'simulator', 'valid'),
    ('SEED-S01-02', 'S01', NOW() - INTERVAL '30 minutes', 40.8, 630, 56.2, 30.8, 67, 2.3, 125, 0, 'simulator', 'valid'),
    ('SEED-S01-03', 'S01', NOW(), 42.5, 650, 57.1, 31.1, 65, 2.5, 130, 0, 'simulator', 'valid'),

    ('SEED-S02-01', 'S02', NOW() - INTERVAL '60 minutes', 51.0, 690, 62.0, 31.0, 70, 1.8, 110, 0, 'simulator', 'valid'),
    ('SEED-S02-02', 'S02', NOW() - INTERVAL '30 minutes', 53.4, 705, 63.8, 31.4, 69, 1.9, 115, 0, 'simulator', 'valid'),
    ('SEED-S02-03', 'S02', NOW(), 55.2, 720, 65.0, 31.8, 68, 2.0, 120, 0, 'simulator', 'valid'),

    ('SEED-S03-01', 'S03', NOW() - INTERVAL '60 minutes', 61.5, 740, 68.0, 31.5, 72, 1.5, 140, 0, 'simulator', 'valid'),
    ('SEED-S03-02', 'S03', NOW() - INTERVAL '30 minutes', 64.0, 760, 69.5, 32.0, 71, 1.6, 145, 0, 'simulator', 'valid'),
    ('SEED-S03-03', 'S03', NOW(), 66.1, 780, 71.2, 32.4, 70, 1.7, 150, 0, 'simulator', 'valid'),

    ('SEED-S04-01', 'S04', NOW() - INTERVAL '60 minutes', 25.0, 510, 47.0, 29.8, 62, 2.8, 100, 0, 'simulator', 'valid'),
    ('SEED-S04-02', 'S04', NOW() - INTERVAL '30 minutes', 26.8, 525, 48.1, 30.0, 61, 2.9, 105, 0, 'simulator', 'valid'),
    ('SEED-S04-03', 'S04', NOW(), 28.4, 540, 49.3, 30.2, 60, 3.0, 110, 0, 'simulator', 'valid'),

    ('SEED-S05-01', 'S05', NOW() - INTERVAL '60 minutes', 32.0, 560, 51.5, 30.2, 66, 2.2, 130, 0, 'simulator', 'valid'),
    ('SEED-S05-02', 'S05', NOW() - INTERVAL '30 minutes', 34.1, 575, 52.8, 30.5, 65, 2.3, 135, 0, 'simulator', 'valid'),
    ('SEED-S05-03', 'S05', NOW(), 35.9, 590, 54.0, 30.8, 64, 2.4, 140, 0, 'simulator', 'valid')
ON CONFLICT (message_id) DO NOTHING;

-- Seed initial alert. Unit and recommendation are enriched by the backend rule registry.
INSERT INTO alerts (alert_id, station_id, alert_type, severity, title, description, observed_value, threshold_value, status, rule_version)
VALUES
    ('00000000-0000-0000-0000-00000000a001', 'S03', 'pm25_threshold', 'warning', 'PM2.5 vượt ngưỡng khuyến nghị', 'Nồng độ PM2.5 tại Ven Hồ Ngọc Trai đạt 66.1 µg/m³ vượt ngưỡng 50 µg/m³', 66.1, 50.0, 'active', 'pm25-threshold-v1')
ON CONFLICT (alert_id) DO NOTHING;

INSERT INTO users (
    user_id, email, password_hash, role, full_name, sensitivity_group,
    email_verified_at, is_active
)
VALUES
    ('00000000-0000-0000-0000-000000000101', 'resident@vinuni.edu.vn', NULL, 'resident', 'Trần Minh Anh', 'normal', NULL, TRUE),
    ('00000000-0000-0000-0000-000000000102', 'manager@vinuni.edu.vn', NULL, 'manager', 'Nguyễn Văn A', 'sensitive', NULL, TRUE),
    ('00000000-0000-0000-0000-000000000103', 'admin@vinuni.edu.vn', NULL, 'admin', 'Lê Thị D', 'normal', NULL, TRUE)
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    full_name = EXCLUDED.full_name,
    sensitivity_group = EXCLUDED.sensitivity_group;

INSERT INTO devices (device_id, device_name, device_type, station_id, status, is_simulated)
VALUES ('FILTER-01', 'Thiết bị lọc không khí ngoài trời Hồ Ngọc Trai', 'air_filter', 'S03', 'offline', TRUE)
ON CONFLICT (device_id) DO UPDATE SET
    device_name = EXCLUDED.device_name,
    device_type = EXCLUDED.device_type,
    station_id = EXCLUDED.station_id,
    is_simulated = EXCLUDED.is_simulated;

INSERT INTO device_operating_profiles (
    profile_id, device_id, profile_version, effective_from, effective_to,
    airflow_m3_per_hour, boost_power_kw, eco_power_kw,
    calibration_source, is_simulated
)
VALUES (
    '50000000-0000-0000-0000-000000000001', 'FILTER-01',
    'filter-01-simulator-profile-v1', '2026-01-01T00:00:00+07:00', NULL,
    12000, 4.8, 1.2,
    'simulator_seed_b7_esg_reports_v1_not_field_calibration', TRUE
)
ON CONFLICT (device_id, profile_version) DO UPDATE SET
    airflow_m3_per_hour = EXCLUDED.airflow_m3_per_hour,
    boost_power_kw = EXCLUDED.boost_power_kw,
    eco_power_kw = EXCLUDED.eco_power_kw,
    calibration_source = EXCLUDED.calibration_source,
    is_simulated = TRUE;

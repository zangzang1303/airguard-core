-- Demo-only reference data. This script is idempotent and must run after schema.sql.
INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description, active)
VALUES
    ('S01', 'Cong chinh', 'main_gate', 20.9441, 105.9439, 'Khu vuc cong chinh, PM2.5 tang vao gio cao diem', TRUE),
    ('S02', 'Bai do xe', 'parking', 20.9450, 105.9435, 'Khu vuc bai do xe, anh huong boi xe ra vao', TRUE),
    ('S03', 'Truc duong chinh', 'main_road', 20.9445, 105.9452, 'Tuyen duong chinh, co mat do giao thong cao', TRUE),
    ('S04', 'Cong vien', 'park', 20.9455, 105.9458, 'Khu cong vien, PM2.5 thuong thap hon khu giao thong', TRUE),
    ('S05', 'Khu the thao ngoai troi', 'sport_area', 20.9437, 105.9448, 'Khu the thao, dung cho khuyen nghi hoat dong ngoai troi', TRUE)
ON CONFLICT (station_id) DO UPDATE SET
    station_name = EXCLUDED.station_name,
    location_type = EXCLUDED.location_type,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    description = EXCLUDED.description,
    active = EXCLUDED.active,
    updated_at = NOW();

INSERT INTO station_status (station_id, status, last_seen_at, source)
SELECT station_id, 'offline', NULL, 'simulator'
FROM stations
ON CONFLICT (station_id) DO NOTHING;

INSERT INTO users (user_id, email, password_hash, role, full_name, sensitivity_group)
VALUES
    ('00000000-0000-0000-0000-000000000101', 'resident@vinuni.edu.vn', NULL, 'resident', 'Tran Minh Anh', 'normal'),
    ('00000000-0000-0000-0000-000000000102', 'manager@vinuni.edu.vn', NULL, 'manager', 'Nguyen Van A', 'sensitive'),
    ('00000000-0000-0000-0000-000000000103', 'admin@vinuni.edu.vn', NULL, 'admin', 'Le Thi D', 'normal')
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    role = EXCLUDED.role,
    full_name = EXCLUDED.full_name,
    sensitivity_group = EXCLUDED.sensitivity_group;

INSERT INTO devices (device_id, device_name, device_type, station_id, status, is_simulated)
VALUES ('FILTER-01', 'Simulated outdoor filtration unit', 'air_filter', 'S03', 'offline', TRUE)
ON CONFLICT (device_id) DO NOTHING;

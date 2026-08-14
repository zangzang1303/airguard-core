-- Demo-only reference data. This script is idempotent and must run after schema.sql.
INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description, active)
VALUES
    ('S01', 'Cong vao Ocean Park', 'main_gate', 20.9975, 105.9430, 'Vi tri simulator tai cong vao khu do thi', TRUE),
    ('S02', 'Bai do xe trung tam', 'parking', 20.9953, 105.9500, 'Vi tri simulator tai bai do xe trung tam', TRUE),
    ('S03', 'Truc duong chinh Ocean Park', 'main_road', 20.9910, 105.9560, 'Vi tri simulator tren truc duong chinh', TRUE),
    ('S04', 'Cong vien trung tam', 'park', 20.9898, 105.9467, 'Vi tri simulator tai khu cong vien', TRUE),
    ('S05', 'Khu the thao ngoai troi', 'sport_area', 21.0008, 105.9428, 'Vi tri simulator tai khu the thao', TRUE)
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

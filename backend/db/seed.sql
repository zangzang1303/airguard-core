-- Demo-only reference data. This script is idempotent and must run after schema.sql.
INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description, active)
VALUES
    ('S01', 'Truc Da Ton phia Tay Bac', 'northwest_road', 21.0008, 105.9428, 'Diem mo phong tren truc Da Ton, phu khu vuc cua ngo Tay Bac Ocean Park 1', TRUE),
    ('S02', 'Khu can ho Sapphire', 'high_rise_residential', 20.9975, 105.9430, 'Diem mo phong trong cum can ho phia Tay Bac, dai dien khu dan cu mat do cao', TRUE),
    ('S03', 'Ven Ho Ngoc Trai', 'lakeside_residential', 20.9953, 105.9500, 'Diem mo phong ven Ho Ngoc Trai va khu Ngoc Trai, dai dien khong gian ven ho trung tam', TRUE),
    ('S04', 'Khuon vien VinUni', 'university_campus', 20.9898, 105.9467, 'Diem mo phong trong khuon vien VinUni o phia Tay Nam pham vi quan sat', TRUE),
    ('S05', 'Khu Hai Au phia Dong Nam', 'southeast_residential', 20.9910, 105.9560, 'Diem mo phong tai khu Hai Au, phu vung dan cu phia Dong Nam Ocean Park 1', TRUE)
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

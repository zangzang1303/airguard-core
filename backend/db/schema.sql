CREATE TABLE IF NOT EXISTS stations (
    station_id VARCHAR(50) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    description TEXT,
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    status VARCHAR(20) NOT NULL DEFAULT 'online',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE NOT NULL,
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    measured_at TIMESTAMPTZ NOT NULL,
    pm25 DOUBLE PRECISION NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    quality_flag VARCHAR(20) NOT NULL DEFAULT 'valid',
    quality_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_measurements_station_time
ON measurements(station_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS weather_observations (
    weather_id BIGSERIAL PRIMARY KEY,
    area_id VARCHAR(50) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    wind_direction DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY,
    station_id VARCHAR(50) REFERENCES stations(station_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    observed_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash TEXT,
    role VARCHAR(30) NOT NULL,
    full_name VARCHAR(150),
    sensitivity_group VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_name VARCHAR(100) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    station_id VARCHAR(50) REFERENCES stations(station_id),
    status VARCHAR(30) NOT NULL DEFAULT 'offline',
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_requests (
    request_id UUID PRIMARY KEY,
    request_type VARCHAR(50) NOT NULL,
    station_id VARCHAR(50) REFERENCES stations(station_id),
    device_id VARCHAR(50) REFERENCES devices(device_id),
    proposed_action VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_by VARCHAR(50) NOT NULL DEFAULT 'ai_agent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_by UUID REFERENCES users(user_id),
    reviewed_at TIMESTAMPTZ,
    review_note TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    actor_type VARCHAR(30) NOT NULL,
    actor_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description)
VALUES
    ('S01', 'Cong chinh', 'main_gate', 20.9441, 105.9439, 'Khu vuc cong chinh, PM2.5 tang vao gio cao diem'),
    ('S02', 'Bai do xe', 'parking', 20.9450, 105.9435, 'Khu vuc bai do xe, anh huong boi xe ra vao'),
    ('S03', 'Truc duong chinh', 'main_road', 20.9445, 105.9452, 'Tuyen duong chinh, co mat do giao thong cao'),
    ('S04', 'Cong vien', 'park', 20.9455, 105.9458, 'Khu cong vien, PM2.5 thuong thap hon khu giao thong'),
    ('S05', 'Khu the thao ngoai troi', 'sport_area', 20.9437, 105.9448, 'Khu the thao, dung cho khuyen nghi hoat dong ngoai troi')
ON CONFLICT (station_id) DO NOTHING;

INSERT INTO devices (device_id, device_name, device_type, station_id, status, is_simulated)
VALUES ('FILTER-01', 'Simulated outdoor filtration unit', 'air_filter', 'S03', 'offline', TRUE)
ON CONFLICT (device_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS stations (
    station_id VARCHAR(50) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    description TEXT,
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    status VARCHAR(20) NOT NULL DEFAULT 'online',
    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS stations ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS station_status (
    station_id VARCHAR(50) PRIMARY KEY REFERENCES stations(station_id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('online', 'offline')),
    last_seen_at TIMESTAMPTZ,
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    reason TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE NOT NULL,
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    measured_at TIMESTAMPTZ NOT NULL,
    pm25 DOUBLE PRECISION NOT NULL CHECK (pm25 >= 0 AND pm25 <= 500),
    temperature DOUBLE PRECISION CHECK (temperature IS NULL OR (temperature >= -20 AND temperature <= 60)),
    humidity DOUBLE PRECISION CHECK (humidity IS NULL OR (humidity >= 0 AND humidity <= 100)),
    wind_speed DOUBLE PRECISION CHECK (wind_speed IS NULL OR (wind_speed >= 0 AND wind_speed <= 60)),
    wind_direction DOUBLE PRECISION CHECK (wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction <= 360)),
    rainfall DOUBLE PRECISION CHECK (rainfall IS NULL OR (rainfall >= 0 AND rainfall <= 500)),
    source VARCHAR(30) NOT NULL DEFAULT 'simulator',
    quality_flag VARCHAR(20) NOT NULL DEFAULT 'valid',
    quality_reason TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS measurements
    ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_measurements_station_time
ON measurements(station_id, measured_at DESC);

CREATE INDEX IF NOT EXISTS idx_measurements_station_quality_time
ON measurements(station_id, quality_flag, measured_at DESC);

CREATE TABLE IF NOT EXISTS mqtt_rejections (
    rejection_id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    station_id VARCHAR(50),
    message_id VARCHAR(100),
    reason VARCHAR(50) NOT NULL,
    detail TEXT,
    payload_excerpt JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mqtt_rejections_created
ON mqtt_rejections(created_at DESC);

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
    rule_version VARCHAR(50) NOT NULL DEFAULT 'pm25-threshold-v1',
    severity VARCHAR(20) NOT NULL,
    observed_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

ALTER TABLE IF EXISTS alerts ADD COLUMN IF NOT EXISTS rule_version VARCHAR(50) NOT NULL DEFAULT 'pm25-threshold-v1';
ALTER TABLE IF EXISTS alerts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

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
    evidence JSONB NOT NULL DEFAULT '{}'::JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    version INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(50) NOT NULL DEFAULT 'ai_agent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_by UUID REFERENCES users(user_id),
    reviewed_at TIMESTAMPTZ,
    review_note TEXT
);

ALTER TABLE IF EXISTS approval_requests
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(200);
CREATE UNIQUE INDEX IF NOT EXISTS uq_approval_requests_idempotency
    ON approval_requests(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS evidence JSONB NOT NULL DEFAULT '{}'::JSONB;


CREATE TABLE IF NOT EXISTS device_command_intents (
    command_intent_id UUID PRIMARY KEY,
    approval_request_id UUID NOT NULL REFERENCES approval_requests(request_id),
    device_id VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    station_id VARCHAR(50) REFERENCES stations(station_id),
    command VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    idempotency_key VARCHAR(200) UNIQUE NOT NULL,
    dispatch_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_device_command_intents_approval
ON device_command_intents(approval_request_id);
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    actor_type VARCHAR(30) NOT NULL,
    actor_id VARCHAR(100),
    actor_role VARCHAR(30),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    outcome VARCHAR(30) NOT NULL DEFAULT 'success',
    correlation_id VARCHAR(100),
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS audit_logs ADD COLUMN IF NOT EXISTS actor_role VARCHAR(30);
ALTER TABLE IF EXISTS audit_logs ADD COLUMN IF NOT EXISTS outcome VARCHAR(30) NOT NULL DEFAULT 'success';
ALTER TABLE IF EXISTS audit_logs ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(100);


CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
RETURNS trigger AS $audit$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only';
END;
$audit$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs;
CREATE TRIGGER audit_logs_no_update
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
CREATE TABLE IF NOT EXISTS job_runs (
    task_id VARCHAR(64) PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    idempotency_key VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    request_payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    result_payload JSONB,
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_type, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_job_runs_type_created
ON job_runs(job_type, created_at DESC);

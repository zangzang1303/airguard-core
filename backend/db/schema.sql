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
    co2 DOUBLE PRECISION CHECK (co2 IS NULL OR (co2 >= 250 AND co2 <= 10000)),
    noise_db DOUBLE PRECISION CHECK (noise_db IS NULL OR (noise_db >= 20 AND noise_db <= 140)),
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
ALTER TABLE IF EXISTS measurements ADD COLUMN IF NOT EXISTS co2 DOUBLE PRECISION;
ALTER TABLE IF EXISTS measurements ADD COLUMN IF NOT EXISTS noise_db DOUBLE PRECISION;
ALTER TABLE IF EXISTS measurements ADD COLUMN IF NOT EXISTS temperature DOUBLE PRECISION;

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
    email_normalized VARCHAR(200) GENERATED ALWAYS AS (LOWER(BTRIM(email))) STORED,
    password_hash TEXT,
    role VARCHAR(30) NOT NULL,
    full_name VARCHAR(150),
    sensitivity_group VARCHAR(50),
    email_verified_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_count >= 0),
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS users
    ADD COLUMN IF NOT EXISTS email_normalized VARCHAR(200)
    GENERATED ALWAYS AS (LOWER(BTRIM(email))) STORED;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS failed_login_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $users_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'users_failed_login_count_nonnegative'
          AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT users_failed_login_count_nonnegative CHECK (failed_login_count >= 0);
    END IF;
END;
$users_constraints$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_normalized
ON users(email_normalized);

CREATE OR REPLACE FUNCTION set_row_updated_at()
RETURNS trigger AS $updated_at$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$updated_at$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_row_updated_at();

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_token_hash CHAR(64) UNIQUE NOT NULL
        CHECK (session_token_hash ~ '^[0-9a-f]{64}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    CHECK (expires_at > created_at),
    CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_expires
ON user_sessions(user_id, expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_sessions_active
ON user_sessions(user_id, revoked_at, expires_at);

CREATE TABLE IF NOT EXISTS resident_notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    environmental_email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    predictive_email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS resident_notification_preferences_set_updated_at
ON resident_notification_preferences;
CREATE TRIGGER resident_notification_preferences_set_updated_at
BEFORE UPDATE ON resident_notification_preferences
FOR EACH ROW EXECUTE FUNCTION set_row_updated_at();

CREATE TABLE IF NOT EXISTS predictive_warning_episodes (
    episode_id UUID PRIMARY KEY,
    station_id VARCHAR(50) NOT NULL REFERENCES stations(station_id),
    metric VARCHAR(20) NOT NULL DEFAULT 'pm25' CHECK (metric = 'pm25'),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'observed', 'resolved', 'expired')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('warning', 'critical')),
    threshold_value DOUBLE PRECISION NOT NULL CHECK (threshold_value >= 0),
    threshold_rule_version VARCHAR(100) NOT NULL,
    policy_version VARCHAR(100) NOT NULL,
    forecast_generated_at TIMESTAMPTZ NOT NULL,
    forecast_target_at TIMESTAMPTZ NOT NULL,
    predicted_value DOUBLE PRECISION NOT NULL CHECK (predicted_value >= 0),
    predicted_min DOUBLE PRECISION NOT NULL CHECK (predicted_min >= 0),
    predicted_max DOUBLE PRECISION NOT NULL CHECK (predicted_max >= predicted_min),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    model_version VARCHAR(120) NOT NULL,
    source VARCHAR(120) NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::JSONB,
    clear_evaluation_count INTEGER NOT NULL DEFAULT 0 CHECK (clear_evaluation_count >= 0),
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_predictive_warning_active_episode
ON predictive_warning_episodes(station_id, metric, threshold_rule_version)
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_predictive_warning_status_target
ON predictive_warning_episodes(status, forecast_target_at);

DROP TRIGGER IF EXISTS predictive_warning_episodes_set_updated_at
ON predictive_warning_episodes;
CREATE TRIGGER predictive_warning_episodes_set_updated_at
BEFORE UPDATE ON predictive_warning_episodes
FOR EACH ROW EXECUTE FUNCTION set_row_updated_at();

CREATE TABLE IF NOT EXISTS warning_checklist_responses (
    episode_id UUID NOT NULL REFERENCES predictive_warning_episodes(episode_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_key VARCHAR(50) NOT NULL CHECK (
        item_key IN (
            'close_windows',
            'bring_laundry_inside',
            'reduce_outdoor_activity',
            'check_air_purifier'
        )
    ),
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (episode_id, user_id, item_key)
);

DROP TRIGGER IF EXISTS warning_checklist_responses_set_updated_at
ON warning_checklist_responses;
CREATE TRIGGER warning_checklist_responses_set_updated_at
BEFORE UPDATE ON warning_checklist_responses
FOR EACH ROW EXECUTE FUNCTION set_row_updated_at();

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    token_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash CHAR(64) UNIQUE NOT NULL CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    email_normalized VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    CHECK (expires_at > created_at),
    CHECK (used_at IS NULL OR used_at >= created_at)
);

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_expires
ON email_verification_tokens(user_id, expires_at DESC);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash CHAR(64) UNIQUE NOT NULL CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    CHECK (expires_at > created_at),
    CHECK (used_at IS NULL OR used_at >= created_at)
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_expires
ON password_reset_tokens(user_id, expires_at DESC);

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

CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS device_operating_profiles (
    profile_id UUID PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    profile_version VARCHAR(80) NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    airflow_m3_per_hour NUMERIC NOT NULL
        CHECK (airflow_m3_per_hour > 0 AND airflow_m3_per_hour <= 1000000),
    boost_power_kw NUMERIC NOT NULL
        CHECK (boost_power_kw > 0 AND boost_power_kw <= 10000),
    eco_power_kw NUMERIC NOT NULL
        CHECK (eco_power_kw >= 0 AND eco_power_kw <= 10000),
    calibration_source TEXT NOT NULL CHECK (length(trim(calibration_source)) > 0),
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (effective_to IS NULL OR effective_to > effective_from),
    CHECK (boost_power_kw >= eco_power_kw),
    UNIQUE (device_id, profile_version)
);

DO $device_profile_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'device_operating_profiles_no_overlap'
          AND conrelid = 'device_operating_profiles'::regclass
    ) THEN
        ALTER TABLE device_operating_profiles
            ADD CONSTRAINT device_operating_profiles_no_overlap
            EXCLUDE USING gist (
                device_id WITH =,
                tstzrange(effective_from, effective_to, '[)') WITH &&
            );
    END IF;
END;
$device_profile_constraints$;

CREATE INDEX IF NOT EXISTS idx_device_operating_profiles_effective
ON device_operating_profiles(device_id, effective_from, effective_to);

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
    review_note TEXT,
    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes BETWEEN 5 AND 180),
    intensity_percent INTEGER CHECK (intensity_percent IS NULL OR intensity_percent BETWEEN 1 AND 100),
    review_mode VARCHAR(30),
    review_idempotency_key VARCHAR(200)
);

ALTER TABLE IF EXISTS approval_requests
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(200);
CREATE UNIQUE INDEX IF NOT EXISTS uq_approval_requests_idempotency
    ON approval_requests(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS evidence JSONB NOT NULL DEFAULT '{}'::JSONB;
ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS duration_minutes INTEGER;
ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS intensity_percent INTEGER;
ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS review_mode VARCHAR(30);
ALTER TABLE IF EXISTS approval_requests ADD COLUMN IF NOT EXISTS review_idempotency_key VARCHAR(200);

DO $approval_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'approval_requests_duration_range'
          AND conrelid = 'approval_requests'::regclass
    ) THEN
        ALTER TABLE approval_requests
            ADD CONSTRAINT approval_requests_duration_range
            CHECK (duration_minutes IS NULL OR duration_minutes BETWEEN 5 AND 180);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'approval_requests_intensity_range'
          AND conrelid = 'approval_requests'::regclass
    ) THEN
        ALTER TABLE approval_requests
            ADD CONSTRAINT approval_requests_intensity_range
            CHECK (intensity_percent IS NULL OR intensity_percent BETWEEN 1 AND 100);
    END IF;
END;
$approval_constraints$;

CREATE INDEX IF NOT EXISTS idx_approval_requests_review_idempotency
    ON approval_requests(request_id, review_idempotency_key)
    WHERE review_idempotency_key IS NOT NULL;


CREATE TABLE IF NOT EXISTS device_command_intents (
    command_intent_id UUID PRIMARY KEY,
    approval_request_id UUID REFERENCES approval_requests(request_id),
    device_id VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    station_id VARCHAR(50) REFERENCES stations(station_id),
    command VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    idempotency_key VARCHAR(200) UNIQUE NOT NULL,
    duration_minutes INTEGER,
    intensity_percent INTEGER,
    command_id VARCHAR(100),
    dispatch_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    ack_status VARCHAR(30),
    device_state VARCHAR(50)
);

ALTER TABLE IF EXISTS device_command_intents ADD COLUMN IF NOT EXISTS duration_minutes INTEGER;
ALTER TABLE IF EXISTS device_command_intents ADD COLUMN IF NOT EXISTS intensity_percent INTEGER;
ALTER TABLE IF EXISTS device_command_intents ADD COLUMN IF NOT EXISTS command_id VARCHAR(100);
ALTER TABLE IF EXISTS device_command_intents ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS device_command_intents ADD COLUMN IF NOT EXISTS ack_status VARCHAR(30);
ALTER TABLE IF EXISTS device_command_intents ADD COLUMN IF NOT EXISTS device_state VARCHAR(50);
ALTER TABLE IF EXISTS device_command_intents ALTER COLUMN approval_request_id DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_device_command_intents_command_id
ON device_command_intents(command_id)
WHERE command_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_device_command_intents_approval
ON device_command_intents(approval_request_id);

CREATE TABLE IF NOT EXISTS device_status_events (
    event_id BIGSERIAL PRIMARY KEY,
    command_id VARCHAR(100) NOT NULL,
    command_intent_id UUID REFERENCES device_command_intents(command_intent_id),
    device_id VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    status VARCHAR(30) NOT NULL CHECK (status IN ('succeeded', 'rejected', 'failed', 'duplicate')),
    device_state VARCHAR(50),
    reason TEXT,
    observed_at TIMESTAMPTZ NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (device_id, command_id, status)
);

CREATE INDEX IF NOT EXISTS idx_device_status_events_device_time
ON device_status_events(device_id, observed_at DESC);

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

CREATE TABLE IF NOT EXISTS environmental_reports (
    report_id UUID PRIMARY KEY,
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('daily', 'weekly')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    timezone VARCHAR(80) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'generating'
        CHECK (status IN ('generating', 'completed', 'failed')),
    statistics JSONB NOT NULL DEFAULT '{}'::JSONB,
    evidence_summary JSONB NOT NULL DEFAULT '{}'::JSONB,
    narrative TEXT,
    generation_mode VARCHAR(40) NOT NULL DEFAULT 'deterministic_grounded',
    model_source VARCHAR(120) NOT NULL DEFAULT 'backend_report_policy:v1',
    generated_by UUID REFERENCES users(user_id),
    failure_code VARCHAR(100),
    generation_attempt_id UUID,
    lease_expires_at TIMESTAMPTZ,
    schema_version VARCHAR(80) NOT NULL DEFAULT 'periodic-report-v1',
    content_checksum_sha256 CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CHECK (period_end > period_start),
    CHECK (content_checksum_sha256 IS NULL OR content_checksum_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (
        schema_version <> 'b7-esg-reports-v1'
        OR status <> 'completed'
        OR content_checksum_sha256 IS NOT NULL
    ),
    UNIQUE (report_type, period_start, period_end, timezone)
);

ALTER TABLE IF EXISTS environmental_reports
    ADD COLUMN IF NOT EXISTS generation_attempt_id UUID,
    ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS schema_version VARCHAR(80) NOT NULL DEFAULT 'periodic-report-v1',
    ADD COLUMN IF NOT EXISTS content_checksum_sha256 CHAR(64);

DO $report_checksum_constraints$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'environmental_reports_checksum_format'
          AND conrelid = 'environmental_reports'::regclass
    ) THEN
        ALTER TABLE environmental_reports ADD CONSTRAINT environmental_reports_checksum_format
            CHECK (content_checksum_sha256 IS NULL OR content_checksum_sha256 ~ '^[0-9a-f]{64}$');
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'environmental_reports_v1_checksum_required'
          AND conrelid = 'environmental_reports'::regclass
    ) THEN
        ALTER TABLE environmental_reports ADD CONSTRAINT environmental_reports_v1_checksum_required
            CHECK (
                schema_version <> 'b7-esg-reports-v1'
                OR status <> 'completed'
                OR content_checksum_sha256 IS NOT NULL
            );
    END IF;
END;
$report_checksum_constraints$;

CREATE INDEX IF NOT EXISTS idx_environmental_reports_type_created
ON environmental_reports(report_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_environmental_reports_generation_lease
ON environmental_reports(status, lease_expires_at)
WHERE status = 'generating';

-- ==========================================
-- Idempotent Reference Seed Data (S01 - S05)
-- ==========================================
INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description, source, status, active)
VALUES
    ('S01', 'Trục Đa Tốn phía Tây Bắc', 'northwest_road', 21.0008, 105.9428, 'Điểm mô phỏng trên trục Đa Tốn, phủ khu vực cửa ngõ Tây Bắc Ocean Park 1', 'simulator', 'online', TRUE),
    ('S02', 'Khu căn hộ Sapphire', 'high_rise_residential', 20.9975, 105.9430, 'Điểm mô phỏng trong cụm căn hộ phía Tây Bắc, đại diện khu dân cư mật độ cao', 'simulator', 'online', TRUE),
    ('S03', 'Ven Hồ Ngọc Trai', 'lakeside_residential', 20.9953, 105.9500, 'Điểm mô phỏng ven Hồ Ngọc Trai và khu Ngọc Trai, đại diện không gian ven hồ trung tâm', 'simulator', 'online', TRUE),
    ('S04', 'Khuôn viên VinUni', 'university_campus', 20.9898, 105.9467, 'Điểm mô phỏng trong khuôn viên VinUni ở phía Tây Nam phạm vi quan sát', 'simulator', 'online', TRUE),
    ('S05', 'Khu Hải Âu phía Đông Nam', 'southeast_residential', 20.9910, 105.9560, 'Điểm mô phỏng tại khu Hải Âu, phủ vùng dân cư phía Đông Nam Ocean Park 1', 'simulator', 'online', TRUE)
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

INSERT INTO users (
    user_id, email, password_hash, role, full_name, sensitivity_group,
    email_verified_at, is_active
)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'manager@airguard.local', '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk', 'manager', 'Demo Facility Manager', 'normal', NOW(), TRUE),
    ('00000000-0000-0000-0000-000000000101', 'resident@vinuni.edu.vn', '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk', 'resident', 'Tran Minh Anh', 'normal', NOW(), TRUE),
    ('00000000-0000-0000-0000-000000000104', 'sensitive.demo@airguard.local', '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk', 'resident', 'Cu Dan Nhay Cam Demo', 'sensitive', NOW(), TRUE),
    ('00000000-0000-0000-0000-000000000105', 'outdoor.demo@airguard.local', '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk', 'resident', 'Cu Dan Ngoai Troi Demo', 'outdoor_sport', NOW(), TRUE),
    ('00000000-0000-0000-0000-000000000102', 'manager@vinuni.edu.vn', '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk', 'manager', 'Nguyen Van A', 'sensitive', NOW(), TRUE),
    ('00000000-0000-0000-0000-000000000103', 'admin@vinuni.edu.vn', '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk', 'admin', 'Le Thi D', 'normal', NOW(), TRUE)
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash),
    role = EXCLUDED.role,
    full_name = EXCLUDED.full_name,
    sensitivity_group = EXCLUDED.sensitivity_group,
    email_verified_at = COALESCE(users.email_verified_at, EXCLUDED.email_verified_at);

INSERT INTO devices (device_id, device_name, device_type, station_id, status, is_simulated)
VALUES
    ('FILTER-S01', 'Thiết bị lọc không khí khu Đa Tốn', 'ventilation_filter', 'S01', 'offline', TRUE),
    ('FILTER-01', 'Thiết bị lọc không khí ngoài trời Hồ Ngọc Trai', 'air_filter', 'S03', 'offline', TRUE),
    ('FILTER-02', 'Thiết bị lọc không khí khu Sapphire', 'ventilation_filter', 'S02', 'offline', TRUE),
    ('FILTER-04', 'Thiết bị lọc không khí VinUni', 'ventilation_filter', 'S04', 'offline', TRUE),
    ('FILTER-05', 'Thiết bị lọc không khí khu Hải Âu', 'ventilation_filter', 'S05', 'offline', TRUE)
ON CONFLICT (device_id) DO NOTHING;

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


BEGIN;

ALTER TABLE approval_requests
    ADD COLUMN IF NOT EXISTS duration_minutes INTEGER,
    ADD COLUMN IF NOT EXISTS intensity_percent INTEGER,
    ADD COLUMN IF NOT EXISTS review_mode VARCHAR(30),
    ADD COLUMN IF NOT EXISTS review_idempotency_key VARCHAR(200);

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

ALTER TABLE device_command_intents
    ADD COLUMN IF NOT EXISTS duration_minutes INTEGER,
    ADD COLUMN IF NOT EXISTS intensity_percent INTEGER,
    ADD COLUMN IF NOT EXISTS command_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ack_status VARCHAR(30),
    ADD COLUMN IF NOT EXISTS device_state VARCHAR(50);

CREATE UNIQUE INDEX IF NOT EXISTS uq_device_command_intents_command_id
    ON device_command_intents(command_id)
    WHERE command_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS device_status_events (
    event_id BIGSERIAL PRIMARY KEY,
    command_id VARCHAR(100) NOT NULL,
    command_intent_id UUID REFERENCES device_command_intents(command_intent_id),
    device_id VARCHAR(50) NOT NULL REFERENCES devices(device_id),
    status VARCHAR(30) NOT NULL
        CHECK (status IN ('succeeded', 'rejected', 'failed', 'duplicate')),
    device_state VARCHAR(50),
    reason TEXT,
    observed_at TIMESTAMPTZ NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (device_id, command_id, status)
);

CREATE INDEX IF NOT EXISTS idx_device_status_events_device_time
    ON device_status_events(device_id, observed_at DESC);

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CHECK (period_end > period_start),
    UNIQUE (report_type, period_start, period_end, timezone)
);

ALTER TABLE environmental_reports
    ADD COLUMN IF NOT EXISTS generation_attempt_id UUID,
    ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_environmental_reports_type_created
    ON environmental_reports(report_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_environmental_reports_generation_lease
    ON environmental_reports(status, lease_expires_at)
    WHERE status = 'generating';

COMMIT;

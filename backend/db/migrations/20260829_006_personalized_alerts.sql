-- B7-02 / b7-personalized-alerts-v1.
-- Additive, idempotent storage for independent notification consent,
-- predictive warning episodes and per-resident checklist state.

BEGIN;

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

-- Existing users intentionally receive no preference row. A missing row is the
-- same fail-closed state as both flags being FALSE.

COMMIT;

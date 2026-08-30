BEGIN;

ALTER TABLE resident_notification_preferences
    ADD COLUMN IF NOT EXISTS daily_weather_digest_enabled BOOLEAN NOT NULL DEFAULT FALSE;

COMMIT;

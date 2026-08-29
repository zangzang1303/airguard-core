BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE environmental_reports
    ADD COLUMN IF NOT EXISTS schema_version VARCHAR(80) NOT NULL DEFAULT 'periodic-report-v1',
    ADD COLUMN IF NOT EXISTS content_checksum_sha256 CHAR(64);

UPDATE environmental_reports
SET schema_version = 'periodic-report-v1'
WHERE schema_version IS NULL OR trim(schema_version) = '';

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

INSERT INTO device_operating_profiles (
    profile_id, device_id, profile_version, effective_from, effective_to,
    airflow_m3_per_hour, boost_power_kw, eco_power_kw,
    calibration_source, is_simulated
)
SELECT
    '50000000-0000-0000-0000-000000000001'::UUID,
    'FILTER-01',
    'filter-01-simulator-profile-v1',
    '2026-01-01T00:00:00+07:00'::TIMESTAMPTZ,
    NULL,
    12000,
    4.8,
    1.2,
    'simulator_seed_b7_esg_reports_v1_not_field_calibration',
    TRUE
WHERE EXISTS (SELECT 1 FROM devices WHERE device_id = 'FILTER-01')
ON CONFLICT (device_id, profile_version) DO UPDATE SET
    airflow_m3_per_hour = EXCLUDED.airflow_m3_per_hour,
    boost_power_kw = EXCLUDED.boost_power_kw,
    eco_power_kw = EXCLUDED.eco_power_kw,
    calibration_source = EXCLUDED.calibration_source,
    is_simulated = TRUE;

COMMIT;

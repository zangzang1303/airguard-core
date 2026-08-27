-- Add simulated filter mappings for demo stations that previously could not
-- create a ventilation proposal. This migration is additive and idempotent.
BEGIN;

INSERT INTO devices (device_id, device_name, device_type, station_id, status, is_simulated)
VALUES
    ('FILTER-S01', 'Da Ton Air Filter S01', 'ventilation_filter', 'S01', 'offline', TRUE),
    ('FILTER-04', 'VinUni Air Filter S04', 'ventilation_filter', 'S04', 'offline', TRUE)
ON CONFLICT (device_id) DO NOTHING;

COMMIT;

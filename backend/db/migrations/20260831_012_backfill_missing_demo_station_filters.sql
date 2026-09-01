-- Backfill simulated filter devices for legacy demo volumes created before the
-- complete five-station device registry was introduced.  The insert remains
-- safe to run on a freshly bootstrapped database.
BEGIN;

INSERT INTO devices (device_id, device_name, device_type, station_id, status, is_simulated)
VALUES
    ('FILTER-02', 'Thiết bị lọc không khí khu Sapphire', 'ventilation_filter', 'S02', 'offline', TRUE),
    ('FILTER-05', 'Thiết bị lọc không khí khu Hải Âu', 'ventilation_filter', 'S05', 'offline', TRUE)
ON CONFLICT (device_id) DO NOTHING;

COMMIT;

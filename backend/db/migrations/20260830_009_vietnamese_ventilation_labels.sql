-- Canonical Vietnamese labels for all simulated ventilation devices.
-- Safe to rerun so existing local PostgreSQL volumes receive the same labels
-- as a freshly initialized database.
BEGIN;

UPDATE devices
SET device_name = CASE device_id
    WHEN 'FILTER-S01' THEN 'Thiết bị lọc không khí khu Đa Tốn'
    WHEN 'FILTER-01' THEN 'Thiết bị lọc không khí ngoài trời Hồ Ngọc Trai'
    WHEN 'FILTER-02' THEN 'Thiết bị lọc không khí khu Sapphire'
    WHEN 'FILTER-04' THEN 'Thiết bị lọc không khí VinUni'
    WHEN 'FILTER-05' THEN 'Thiết bị lọc không khí khu Hải Âu'
    ELSE device_name
END
WHERE device_id IN ('FILTER-S01', 'FILTER-01', 'FILTER-02', 'FILTER-04', 'FILTER-05');

COMMIT;

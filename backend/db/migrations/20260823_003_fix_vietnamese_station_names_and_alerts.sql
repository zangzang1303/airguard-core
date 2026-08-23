-- Migration: 20260823_003_fix_vietnamese_station_names_and_alerts.sql
-- Description: Idempotently update stations S01-S05 to canonical UTF-8 Vietnamese names/descriptions
--              and repair corrupted alert titles/descriptions in existing database volume.

BEGIN;

-- 1. Idempotently upsert canonical station metadata for S01-S05
INSERT INTO stations (station_id, station_name, location_type, latitude, longitude, description, source, status, active)
VALUES
    ('S01', 'Trục Đa Tốn phía Tây Bắc', 'northwest_road', 21.0008, 105.9428, 'Điểm mô phỏng trên trục Đa Tốn, phủ khu vực cửa ngõ Tây Bắc Ocean Park 1', 'simulator', 'online', TRUE),
    ('S02', 'Khu căn hộ Sapphire', 'high_rise_residential', 20.9975, 105.9430, 'Điểm mô phỏng trong cụm căn hộ phía Tây Bắc, đại diện khu dân cư mật độ cao', 'simulator', 'online', TRUE),
    ('S03', 'Ven Hồ Ngọc Trai', 'lakeside_residential', 20.9953, 105.9500, 'Điểm mô phỏng ven Hồ Ngọc Trai và khu Ngọc Trai, đại diện không gian ven hồ trung tâm', 'simulator', 'online', TRUE),
    ('S04', 'Khuôn viên VinUni', 'university_campus', 20.9898, 105.9467, 'Điểm mô phỏng trong khuôn viên VinUni ở phía Tây Nam phạm vi quan sát', 'simulator', 'online', TRUE),
    ('S05', 'Khu Hải Âu phía Đông Nam', 'southeast_residential', 20.9910, 105.9560, 'Điểm mô phỏng tại khu Hải Âu, phủ vùng dân cư phía Đông Nam Ocean Park 1', 'simulator', 'online', TRUE)
ON CONFLICT (station_id) DO UPDATE SET
    station_name = EXCLUDED.station_name,
    description = EXCLUDED.description,
    active = EXCLUDED.active,
    updated_at = NOW();

-- 2. Repair alert titles where titles were generated with corrupted or ASCII station names
-- Threshold alerts formatted as '<Metric> vượt ngưỡng tại <station_name>'
UPDATE alerts
SET title = split_part(title, ' vượt ngưỡng tại ', 1) || ' vượt ngưỡng tại ' || s.station_name,
    updated_at = NOW()
FROM stations s
WHERE alerts.station_id = s.station_id
  AND alerts.title LIKE '% vượt ngưỡng tại %'
  AND alerts.title NOT LIKE ('% vượt ngưỡng tại ' || s.station_name);

-- Seed alerts formatted with 'vượt ngưỡng khuyến nghị'
UPDATE alerts
SET title = 'PM2.5 vượt ngưỡng khuyến nghị',
    updated_at = NOW()
WHERE title LIKE 'PM2.5 v%ngưỡng khuyến nghị'
   OR title LIKE 'PM2.5 v%ng????ng khuy%n ngh%'
   OR title LIKE '%khuy%n ngh%';

-- Offline alerts formatted as 'Sensor unavailable at <station_name>'
UPDATE alerts
SET title = 'Sensor unavailable at ' || s.station_name,
    updated_at = NOW()
FROM stations s
WHERE alerts.station_id = s.station_id
  AND alerts.title LIKE 'Sensor unavailable at %'
  AND alerts.title != ('Sensor unavailable at ' || s.station_name);

-- 3. Repair alert descriptions containing ASCII or corrupted station names
UPDATE alerts
SET description = regexp_replace(alerts.description, 'tại [^0-9,;]+ đạt', 'tại ' || s.station_name || ' đạt', 'g'),
    updated_at = NOW()
FROM stations s
WHERE alerts.station_id = s.station_id
  AND alerts.description ~ 'tại .+ đạt'
  AND alerts.description !~ ('tại ' || s.station_name || ' đạt');

COMMIT;

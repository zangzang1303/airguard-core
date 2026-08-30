-- Shared Manager/Admin Activity Log fixtures for the MVP demo.
-- This migration is additive and idempotent: it makes the decision-only
-- activity list non-empty after a fresh clone and after an existing local DB
-- pulls this change. The operational audit trail remains append-only.
BEGIN;

INSERT INTO approval_requests (
    request_id, request_type, station_id, device_id, proposed_action,
    reason, evidence, status, version, created_by, created_at,
    reviewed_by, reviewed_at, review_note, duration_minutes,
    intensity_percent, review_mode
)
SELECT
    fixture.request_id, fixture.request_type, fixture.station_id,
    fixture.device_id, fixture.proposed_action, fixture.reason,
    fixture.evidence::jsonb, fixture.status, 2, 'ai_agent',
    fixture.created_at, '00000000-0000-0000-0000-000000000102'::uuid,
    fixture.reviewed_at, fixture.review_note, fixture.duration_minutes,
    fixture.intensity_percent, 'standard'
FROM (
    VALUES
        (
            '90000000-0000-0000-0000-000000000801'::uuid,
            'warning_proposal', 'S03', 'FILTER-01', 'ventilation_boost',
            'PM2.5 vuot nguong lien tuc trong du lieu mo phong.',
            '{"source":"simulator","metric":"pm25","observed_value":70.85,"threshold":50}'::text,
            'approved', '2026-08-30T08:30:00+07:00'::timestamptz,
            '2026-08-30T08:40:00+07:00'::timestamptz,
            'Da kiem tra bang chung va duyet xu ly cho demo.', 45, 80
        ),
        (
            '90000000-0000-0000-0000-000000000802'::uuid,
            'warning_proposal', 'S02', NULL, 'notify_station_area_users',
            'Can xac minh them du lieu truoc khi gui thong bao dien rong.',
            '{"source":"simulator","metric":"co2","observed_value":1040,"threshold":1000}'::text,
            'rejected', '2026-08-30T09:00:00+07:00'::timestamptz,
            '2026-08-30T09:10:00+07:00'::timestamptz,
            'Tu choi do chua du dieu kien bang chung cho demo.', NULL, NULL
        )
) AS fixture(
    request_id, request_type, station_id, device_id, proposed_action,
    reason, evidence, status, created_at, reviewed_at, review_note,
    duration_minutes, intensity_percent
)
WHERE EXISTS (
    SELECT 1 FROM users WHERE user_id = '00000000-0000-0000-0000-000000000102'::uuid
)
ON CONFLICT (request_id) DO NOTHING;

INSERT INTO audit_logs (
    actor_type, actor_id, actor_role, action, entity_type, entity_id,
    outcome, correlation_id, details, created_at
)
SELECT
    'user', '00000000-0000-0000-0000-000000000102', 'manager',
    fixture.action, 'approval_request', fixture.request_id::text, 'success',
    fixture.correlation_id,
    jsonb_build_object('station_id', fixture.station_id, 'proposed_action', fixture.proposed_action),
    fixture.created_at
FROM (
    VALUES
        ('90000000-0000-0000-0000-000000000801'::uuid, 'S03', 'ventilation_boost', 'approval.approve', 'demo-manager-decision-approved', '2026-08-30T08:40:00+07:00'::timestamptz),
        ('90000000-0000-0000-0000-000000000802'::uuid, 'S02', 'notify_station_area_users', 'approval.reject', 'demo-manager-decision-rejected', '2026-08-30T09:10:00+07:00'::timestamptz)
) AS fixture(request_id, station_id, proposed_action, action, correlation_id, created_at)
WHERE NOT EXISTS (
    SELECT 1
    FROM audit_logs AS existing
    WHERE existing.action = fixture.action
      AND existing.entity_type = 'approval_request'
      AND existing.entity_id = fixture.request_id::text
);

COMMIT;

-- Keep existing PostgreSQL volumes aligned with the demo identities in schema.sql.
-- This migration is idempotent and contains only the public demo password hash.

BEGIN;

INSERT INTO users (
    user_id,
    email,
    password_hash,
    role,
    full_name,
    sensitivity_group,
    email_verified_at,
    is_active,
    failed_login_count,
    created_at,
    updated_at
)
VALUES
    (
        '00000000-0000-0000-0000-000000000104',
        'sensitive.demo@airguard.local',
        '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk',
        'resident',
        'Cư dân Nhạy cảm Demo',
        'sensitive',
        NOW(),
        TRUE,
        0,
        NOW(),
        NOW()
    ),
    (
        '00000000-0000-0000-0000-000000000105',
        'outdoor.demo@airguard.local',
        '$argon2id$v=19$m=65536,t=2,p=2$o1LOm0vKYt+Zmy/2Mstm5Q$1Zh9dXZQZ2nYr5vOR+fRMJx3MZOcCquNT/uMXUAikSk',
        'resident',
        'Cư dân Hoạt động ngoài trời Demo',
        'outdoor_sport',
        NOW(),
        TRUE,
        0,
        NOW(),
        NOW()
    )
-- Existing demo accounts may have been created through the registration flow and
-- therefore have non-canonical UUIDs. Preserve those UUIDs (and all referencing
-- rows) when either the email or the canonical UUID already exists.
ON CONFLICT DO NOTHING;

WITH canonical_users(email_normalized, email, full_name, sensitivity_group) AS (
    VALUES
        (
            'sensitive.demo@airguard.local',
            'sensitive.demo@airguard.local',
            'Cư dân Nhạy cảm Demo',
            'sensitive'
        ),
        (
            'outdoor.demo@airguard.local',
            'outdoor.demo@airguard.local',
            'Cư dân Hoạt động ngoài trời Demo',
            'outdoor_sport'
        )
)
UPDATE users AS existing_user
SET
    email = canonical_users.email,
    role = 'resident',
    full_name = canonical_users.full_name,
    sensitivity_group = canonical_users.sensitivity_group,
    email_verified_at = COALESCE(existing_user.email_verified_at, NOW()),
    is_active = TRUE,
    updated_at = NOW()
FROM canonical_users
WHERE existing_user.email_normalized = canonical_users.email_normalized;

COMMIT;

-- Keep existing PostgreSQL volumes aligned with the demo identities in schema.sql.
-- This migration is idempotent and contains only the public demo password hash.

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
ON CONFLICT (user_id) DO UPDATE SET
    email = EXCLUDED.email,
    role = 'resident',
    full_name = EXCLUDED.full_name,
    sensitivity_group = EXCLUDED.sensitivity_group,
    email_verified_at = COALESCE(users.email_verified_at, EXCLUDED.email_verified_at),
    is_active = TRUE,
    updated_at = NOW();

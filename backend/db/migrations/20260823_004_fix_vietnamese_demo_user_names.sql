-- Migration: 20260823_004_fix_vietnamese_demo_user_names.sql
-- Description: Idempotently repair corrupted UTF-8 Vietnamese full_name for the three demo accounts:
--              manager@vinuni.edu.vn  -> 'Nguyễn Văn A'
--              admin@vinuni.edu.vn    -> 'Lê Thị D'
--              resident@vinuni.edu.vn -> 'Trần Minh Anh'

BEGIN;

WITH canonical_users(email_normalized, full_name) AS (
    VALUES
        ('manager@vinuni.edu.vn', 'Nguyễn Văn A'),
        ('admin@vinuni.edu.vn', 'Lê Thị D'),
        ('resident@vinuni.edu.vn', 'Trần Minh Anh')
)
UPDATE users AS u
SET full_name = canonical_users.full_name
FROM canonical_users
WHERE LOWER(BTRIM(u.email)) = canonical_users.email_normalized
  AND u.full_name IS DISTINCT FROM canonical_users.full_name;

COMMIT;

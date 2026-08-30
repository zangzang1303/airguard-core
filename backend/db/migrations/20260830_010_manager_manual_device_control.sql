-- A Manager's direct simulated-device command is auditable but is not an
-- approval request. Alert-driven commands retain their approval reference.
BEGIN;

ALTER TABLE device_command_intents
    ALTER COLUMN approval_request_id DROP NOT NULL;

COMMIT;

-- Safe migration: add responder_id to emergency_responses without destroying existing data.
-- This makes the response record explicitly track which authenticated user responded.

ALTER TABLE emergency_responses ADD COLUMN responder_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_emergency_responses_responder_id
    ON emergency_responses (responder_id);

-- Backfill existing responder rows safely when legacy data already exists.
-- For older records, responder_id remains NULL until a proper responder is associated.
-- Use the application layer to set responder_id when creating new responses.

-- Optional FK constraint if the target database supports it and the column is fully backfilled:
-- ALTER TABLE emergency_responses
--     ADD CONSTRAINT fk_emergency_responses_responder
--     FOREIGN KEY (responder_id) REFERENCES users(id);

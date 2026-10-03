-- Hint / chat-with-AI feature.
--
-- Each problem_assignments row already represents exactly one
-- problem instance served to the student, so "5 hints per problem"
-- maps naturally onto a counter on that row - it resets automatically
-- every time a new problem is assigned.
--
-- All statements here are idempotent (IF NOT EXISTS) so this file is
-- safe to run both as part of a fresh init and by hand against an
-- existing deployment that already applied 001_schema.sql:
--   docker compose exec -T postgres psql -U coolUser -d DSA_agent < db/init/002_schema.sql

ALTER TABLE problem_assignments
    ADD COLUMN IF NOT EXISTS hints_used INT NOT NULL DEFAULT 0;

-- Recorded on the final attempt so skill/progress calculations (and
-- the student's own history) can see how much help a solve took.
ALTER TABLE problem_attempts
    ADD COLUMN IF NOT EXISTS hints_used INT NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,

    problem_assignment_id BIGINT NOT NULL
        REFERENCES problem_assignments(id)
        ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'

    content TEXT NOT NULL,

    hint_number INT, -- which hint (1-5) this exchange corresponds to; null for pure chat framing rows

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_assignment
ON chat_messages(problem_assignment_id, created_at);

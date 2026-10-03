-- Per-user Groq API key.
--
-- Previously every student shared one GROQ_API key from the backend's
-- .env file. This lets each student supply their own Groq key (stored
-- here, used instead of the shared env var whenever present) so usage
-- is billed/rate-limited per student rather than against one shared key.
--
-- Idempotent - safe to run against an existing deployment:
--   docker compose exec -T postgres psql -U coolUser -d DSA_agent < db/init/003_user_api_key.sql
--
-- Security note: this column is stored in plaintext. It is never
-- selected back out through any API response (see backend/api/user.py)
-- and should ideally be encrypted at rest (e.g. pgcrypto) in a
-- production deployment - left plaintext here to keep the sandbox
-- setup simple.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS groq_api_key TEXT;

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    level VARCHAR(50) NOT NULL DEFAULT 'Beginner',
    codeforces_handle VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- use hierarchical table
CREATE TABLE roadmap_topics (
    id BIGSERIAL PRIMARY KEY,

    parent_id BIGINT
        REFERENCES roadmap_topics(id)
        ON DELETE CASCADE,

    name VARCHAR(150) NOT NULL,
    node_type VARCHAR(30) NOT NULL,
    sequence_order INT NOT NULL,
    description TEXT,

    UNIQUE(parent_id, name)
);
CREATE TABLE topic_summaries (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,
    roadmap_topic_id BIGINT
        REFERENCES roadmap_topics(id)
        ON DELETE SET NULL,
    topic_name VARCHAR(150) NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, roadmap_topic_id)
);

CREATE INDEX idx_topic_summaries_user_id
ON topic_summaries(user_id);

CREATE TABLE user_progress (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    roadmap_topic_id BIGINT NOT NULL
        REFERENCES roadmap_topics(id)
        ON DELETE CASCADE,

    skill_score NUMERIC(5,2) NOT NULL DEFAULT 0,

    weak_score NUMERIC(5,2) NOT NULL DEFAULT 0,

    problems_attempted INT NOT NULL DEFAULT 0,

    problems_solved INT NOT NULL DEFAULT 0,

    avg_thinking_time_seconds NUMERIC(10,2),

    last_attempted_at TIMESTAMPTZ,

    UNIQUE(user_id, roadmap_topic_id)
);

CREATE TABLE problem_attempts (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    roadmap_topic_id BIGINT
        REFERENCES roadmap_topics(id),

    problem_source VARCHAR(30) NOT NULL,

    problem_id VARCHAR(100) NOT NULL,

    problem_title VARCHAR(255),

    difficulty VARCHAR(20),

    attempt_number INT NOT NULL DEFAULT 1,

    thinking_time_seconds INT,

    submission_time_seconds INT,

    correct BOOLEAN,

    time_complexity VARCHAR(100),

    space_complexity VARCHAR(100),

    approach_score NUMERIC(5,2),

    code_quality_score NUMERIC(5,2),

    complexity_score NUMERIC(5,2),

    overall_score NUMERIC(5,2),

    evaluation JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
/*

{
    "identified_pattern": "sliding_window",
    "expected_pattern": "sliding_window",
    "mistakes": [
        "window was not shrunk correctly"
    ],
    "edge_cases_missed": [
        "empty input"
    ],
    "feedback": "Your approach was correct but the invariant was not maintained."
}*/

CREATE TABLE problems (
    id BIGSERIAL PRIMARY KEY,

    source VARCHAR(30) NOT NULL,

    external_id VARCHAR(150) NOT NULL,

    title VARCHAR(255) NOT NULL,

    difficulty VARCHAR(30),

    url TEXT NOT NULL,

    description TEXT,

    topics JSONB NOT NULL DEFAULT '[]',

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(source, external_id)
);
CREATE TABLE problem_assignments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,
    problem_id BIGINT NOT NULL
        REFERENCES problems(id)
        ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    codeforces_submission_id BIGINT,
    status VARCHAR(30) NOT NULL DEFAULT 'assigned'
);
CREATE TABLE problem_topics (
    problem_id BIGINT NOT NULL
        REFERENCES problems(id)
        ON DELETE CASCADE,

    roadmap_topic_id BIGINT NOT NULL
        REFERENCES roadmap_topics(id)
        ON DELETE CASCADE,

    PRIMARY KEY(problem_id, roadmap_topic_id)
);
CREATE TABLE problem_test_cases (
    id SERIAL PRIMARY KEY,
    problem_id INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_sample BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_problem_test_cases_problem_id
ON problem_test_cases(problem_id);
CREATE INDEX idx_problem_assignments_user
ON problem_assignments(user_id);
CREATE INDEX idx_problem_assignments_problem
ON problem_assignments(problem_id);
CREATE INDEX idx_problem_assignments_user_problem
ON problem_assignments(user_id, problem_id);
create table users(
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- use hierarchical table
create table roadmap_topics (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT REFERENCES roadmap_topics(id) on DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    node_type VARCHAR(30) NOT NULL,
    sequence_order INT NOT NULL,
    description TEXT,
    UNIQUE(parent_id, name)
);

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
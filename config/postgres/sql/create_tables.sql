SET TIME ZONE 'Europe/Lisbon';

-- Table: review
CREATE TABLE IF NOT EXISTS review
(
    recommendationid VARCHAR(200) NOT NULL,
    game VARCHAR(200) NOT NULL,
    playtime_forever integer,
    playtime_last_two_weeks integer,
    playtime_at_review integer,
    last_played timestamp without time zone,
    language VARCHAR(100) NOT NULL,
    review text NOT NULL,
    timestamp_created bigint NOT NULL,
    timestamp_updated bigint NOT NULL,
    voted_up boolean,
    votes_up integer,
    votes_funny integer,
    weighted_vote_score double precision,
    comment_count integer,
    steam_purchase boolean,
    received_for_free boolean,
    written_during_early_access boolean,
    developer_response text,
    timestamp_dev_responded bigint,
    hidden_in_steam_china boolean,
    steam_china_location VARCHAR(255),
    primarily_steam_deck boolean,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT reviews_pkey PRIMARY KEY (recommendationid)
);

-- Table: conversation
CREATE TABLE IF NOT EXISTS conversation (
    id SERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    game VARCHAR(200) NOT NULL,
    model VARCHAR(200) NOT NULL,
    response_time FLOAT,
    relevance TEXT NOT NULL,
    relevance_explanation TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    eval_prompt_tokens INTEGER NOT NULL,
    eval_completion_tokens INTEGER NOT NULL,
    eval_total_tokens INTEGER NOT NULL,
    model_cost FLOAT NOT NULL,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: feedbacks
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversation(id),
    feedback_score INTEGER,
	feedback_comment TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

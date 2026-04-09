

CREATE TABLE IF NOT EXISTS position (
    id BIGSERIAL PRIMARY KEY,
    frontend BOOLEAN NOT NULL DEFAULT FALSE,
    backend BOOLEAN NOT NULL DEFAULT FALSE,
    devops BOOLEAN NOT NULL DEFAULT FALSE,
    qa BOOLEAN NOT NULL DEFAULT FALSE,
    admins BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS team (
    id BIGSERIAL PRIMARY KEY,
    manager_id BIGINT,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS skill (
    id BIGSERIAL PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL UNIQUE,
    name_ru VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "user" (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    role VARCHAR(30) NOT NULL DEFAULT 'unregistered'
        CHECK (role IN ('unregistered', 'employee', 'manager', 'admin')),
    position_id BIGINT REFERENCES position(id),
    grade VARCHAR(30) CHECK (grade IN ('Junior', 'Middle', 'Senior')),
    team_id BIGINT REFERENCES team(id)
);

ALTER TABLE team
    ADD CONSTRAINT team_manager_fk
    FOREIGN KEY (manager_id) REFERENCES "user"(id)
    ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS attestation (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    period VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'cancelled')),
    result_grade VARCHAR(30)
        CHECK (result_grade IN ('Junior', 'Middle', 'Senior', 'Lead')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS review (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    attestation_id BIGINT NOT NULL REFERENCES attestation(id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    subject_id BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skill(id) ON DELETE CASCADE,
    score SMALLINT CHECK (score BETWEEN 1 AND 5),
    is_strange BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (attestation_id, reviewer_id, subject_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_user_telegram_id ON "user"(telegram_id);
CREATE INDEX IF NOT EXISTS idx_review_attestation_id ON review(attestation_id);
CREATE INDEX IF NOT EXISTS idx_review_subject_id ON review(subject_id);
CREATE INDEX IF NOT EXISTS idx_attestation_subject_id ON attestation(subject_id);

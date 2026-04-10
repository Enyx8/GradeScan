
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

CREATE TABLE IF NOT EXISTS grade_matrix (
    id BIGSERIAL PRIMARY KEY,
    position_name VARCHAR(50) NOT NULL,
    grade VARCHAR(30) NOT NULL,
    skill_id BIGINT REFERENCES skill(id),
    required_score DECIMAL(3,2) NOT NULL,
    UNIQUE(position_name, grade, skill_id)
);

INSERT INTO skill (name_en, name_ru) VALUES
('Postgres', 'Postgres'),
('Java', 'Java'),
('Testing', 'Testing'),
('Soft skills', 'Soft skills'),
('Python', 'Python'),
('Kotlin', 'Kotlin'),
('JavaScript', 'JavaScript'),
('TypeScript', 'TypeScript'),
('React', 'React'),
('Docker', 'Docker'),
('Kubernetes', 'Kubernetes'),
('Git', 'Git'),
('Linux', 'Linux'),
('Machine learning', 'Machine learning')
ON CONFLICT DO NOTHING;


INSERT INTO grade_matrix (position_name, grade, skill_id, required_score) VALUES
('backend', 'Junior', 1, 2.0), ('backend', 'Junior', 2, 2.0), ('backend', 'Junior', 3, 1.5), ('backend', 'Junior', 4, 2.0),
('backend', 'Middle', 1, 3.5), ('backend', 'Middle', 2, 3.5), ('backend', 'Middle', 3, 3.0), ('backend', 'Middle', 4, 3.5),
('backend', 'Senior', 1, 4.5), ('backend', 'Senior', 2, 4.5), ('backend', 'Senior', 3, 4.0), ('backend', 'Senior', 4, 4.5)
ON CONFLICT DO NOTHING;

-- Frontend (Frontend React dev)
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score) VALUES
('frontend', 'Junior', 1, 1.5), ('frontend', 'Junior', 2, 2.0), ('frontend', 'Junior', 3, 2.0), ('frontend', 'Junior', 4, 2.2),
('frontend', 'Middle', 1, 2.5), ('frontend', 'Middle', 2, 3.5), ('frontend', 'Middle', 3, 3.2), ('frontend', 'Middle', 4, 3.6),
('frontend', 'Senior', 1, 3.0), ('frontend', 'Senior', 2, 4.5), ('frontend', 'Senior', 3, 4.0), ('frontend', 'Senior', 4, 4.5)
ON CONFLICT DO NOTHING;

-- DevOps
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score) VALUES
('devops', 'Junior', 1, 2.5), ('devops', 'Junior', 2, 2.0), ('devops', 'Junior', 3, 2.0), ('devops', 'Junior', 4, 2.0),
('devops', 'Middle', 1, 3.6), ('devops', 'Middle', 2, 3.2), ('devops', 'Middle', 3, 3.4), ('devops', 'Middle', 4, 3.5),
('devops', 'Senior', 1, 4.5), ('devops', 'Senior', 2, 4.0), ('devops', 'Senior', 3, 4.3), ('devops', 'Senior', 4, 4.5)
ON CONFLICT DO NOTHING;

-- QA / аналитика
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score) VALUES
('qa', 'Junior', 1, 2.2), ('qa', 'Junior', 2, 2.0), ('qa', 'Junior', 3, 2.0), ('qa', 'Junior', 4, 2.0),
('qa', 'Middle', 1, 3.8), ('qa', 'Middle', 2, 3.5), ('qa', 'Middle', 3, 3.5), ('qa', 'Middle', 4, 3.4),
('qa', 'Senior', 1, 4.7), ('qa', 'Senior', 2, 4.2), ('qa', 'Senior', 3, 4.3), ('qa', 'Senior', 4, 4.4)
ON CONFLICT DO NOTHING;

-- Менеджеры: матрица admins (id навыков из таблицы skill)
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Junior', id, 2.5 FROM skill WHERE name_en = 'Soft skills' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Junior', id, 2.0 FROM skill WHERE name_en = 'Testing' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Junior', id, 2.0 FROM skill WHERE name_en = 'Git' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Middle', id, 3.0 FROM skill WHERE name_en = 'Postgres' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Middle', id, 3.0 FROM skill WHERE name_en = 'Java' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Middle', id, 3.2 FROM skill WHERE name_en = 'Python' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Soft skills' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 3.8 FROM skill WHERE name_en = 'REST API' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 3.5 FROM skill WHERE name_en = 'Docker' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 3.5 FROM skill WHERE name_en = 'Kafka' LIMIT 1 ON CONFLICT DO NOTHING;

-- Какие навыки показывать при оценке: направление + мин. грейд владения
CREATE TABLE IF NOT EXISTS position_skill (
    id BIGSERIAL PRIMARY KEY,
    position_name VARCHAR(50) NOT NULL,
    skill_id BIGINT NOT NULL REFERENCES skill(id) ON DELETE CASCADE,
    min_grade VARCHAR(30) NOT NULL CHECK (min_grade IN ('Junior', 'Middle', 'Senior')),
    UNIQUE(position_name, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_position_skill_lookup ON position_skill(position_name, min_grade);

INSERT INTO skill (name_en, name_ru) VALUES
('Redis', 'Redis'),
('Memcached', 'Memcached'),
('Kafka', 'Kafka'),
('RabbitMQ', 'RabbitMQ'),
('Terraform', 'Terraform'),
('Ansible', 'Ansible'),
('REST API', 'REST API'),
('Cypress', 'Cypress'),
('Next.js', 'Next.js'),
('Web performance', 'Web performance'),
('Grafana', 'Grafana')
ON CONFLICT (name_en) DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'backend', id, 'Junior' FROM skill WHERE name_en IN (
    'Postgres', 'Java', 'Python', 'Testing', 'Soft skills', 'Git'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'backend', id, 'Middle' FROM skill WHERE name_en IN (
    'Kotlin', 'Docker', 'Linux', 'JavaScript', 'TypeScript'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'backend', id, 'Senior' FROM skill WHERE name_en IN (
    'Kubernetes', 'Redis', 'Memcached', 'Kafka', 'RabbitMQ'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'frontend', id, 'Junior' FROM skill WHERE name_en IN (
    'JavaScript', 'TypeScript', 'React', 'Testing', 'Soft skills', 'Git'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'frontend', id, 'Middle' FROM skill WHERE name_en IN (
    'Docker', 'REST API', 'Postgres'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'frontend', id, 'Senior' FROM skill WHERE name_en IN (
    'Next.js', 'Web performance', 'Kubernetes'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'devops', id, 'Junior' FROM skill WHERE name_en IN (
    'Linux', 'Git', 'Docker', 'Testing', 'Soft skills'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'devops', id, 'Middle' FROM skill WHERE name_en IN (
    'Kubernetes', 'Postgres', 'Ansible', 'Python'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'devops', id, 'Senior' FROM skill WHERE name_en IN (
    'Terraform', 'Kafka', 'RabbitMQ', 'Grafana', 'Java'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'qa', id, 'Junior' FROM skill WHERE name_en IN (
    'Testing', 'Soft skills', 'Git', 'Postgres'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'qa', id, 'Middle' FROM skill WHERE name_en IN (
    'JavaScript', 'Python', 'REST API', 'Docker'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'qa', id, 'Senior' FROM skill WHERE name_en IN (
    'Machine learning', 'Cypress', 'Kafka', 'Linux'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'admins', id, 'Junior' FROM skill WHERE name_en IN (
    'Soft skills', 'Testing', 'Git'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'admins', id, 'Middle' FROM skill WHERE name_en IN (
    'Postgres', 'Java', 'Python'
) ON CONFLICT DO NOTHING;

INSERT INTO position_skill (position_name, skill_id, min_grade)
SELECT 'admins', id, 'Senior' FROM skill WHERE name_en IN (
    'REST API', 'Docker', 'Kafka'
) ON CONFLICT DO NOTHING;

-- Доп. пороги grade_matrix для Middle/Senior (узкие навыки), по id из skill
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Middle', id, 3.2 FROM skill WHERE name_en = 'Docker' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Middle', id, 3.0 FROM skill WHERE name_en = 'Linux' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Middle', id, 3.2 FROM skill WHERE name_en = 'Kotlin' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Middle', id, 3.0 FROM skill WHERE name_en = 'JavaScript' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Middle', id, 3.0 FROM skill WHERE name_en = 'TypeScript' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Senior', id, 4.2 FROM skill WHERE name_en = 'Kubernetes' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Senior', id, 4.3 FROM skill WHERE name_en = 'Redis' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Memcached' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Senior', id, 4.2 FROM skill WHERE name_en = 'Kafka' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'backend', 'Senior', id, 4.0 FROM skill WHERE name_en = 'RabbitMQ' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'frontend', 'Middle', id, 2.8 FROM skill WHERE name_en = 'Docker' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'frontend', 'Middle', id, 3.2 FROM skill WHERE name_en = 'REST API' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'frontend', 'Middle', id, 2.5 FROM skill WHERE name_en = 'Postgres' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'frontend', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Next.js' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'frontend', 'Senior', id, 4.2 FROM skill WHERE name_en = 'Web performance' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'frontend', 'Senior', id, 3.5 FROM skill WHERE name_en = 'Kubernetes' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Middle', id, 3.5 FROM skill WHERE name_en = 'Kubernetes' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Middle', id, 3.2 FROM skill WHERE name_en = 'Postgres' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Middle', id, 3.4 FROM skill WHERE name_en = 'Ansible' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Middle', id, 3.3 FROM skill WHERE name_en = 'Python' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Senior', id, 4.2 FROM skill WHERE name_en = 'Terraform' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Kafka' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Senior', id, 3.8 FROM skill WHERE name_en = 'RabbitMQ' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Grafana' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'devops', 'Senior', id, 3.5 FROM skill WHERE name_en = 'Java' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Middle', id, 3.2 FROM skill WHERE name_en = 'JavaScript' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Middle', id, 3.5 FROM skill WHERE name_en = 'Python' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Middle', id, 3.4 FROM skill WHERE name_en = 'REST API' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Middle', id, 3.0 FROM skill WHERE name_en = 'Docker' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Machine learning' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Senior', id, 4.0 FROM skill WHERE name_en = 'Cypress' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Senior', id, 3.8 FROM skill WHERE name_en = 'Kafka' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'qa', 'Senior', id, 3.8 FROM skill WHERE name_en = 'Linux' LIMIT 1 ON CONFLICT DO NOTHING;

INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Middle', id, 3.0 FROM skill WHERE name_en = 'Postgres' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Middle', id, 3.0 FROM skill WHERE name_en = 'Java' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Middle', id, 3.2 FROM skill WHERE name_en = 'Python' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 3.8 FROM skill WHERE name_en = 'REST API' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 3.5 FROM skill WHERE name_en = 'Docker' LIMIT 1 ON CONFLICT DO NOTHING;
INSERT INTO grade_matrix (position_name, grade, skill_id, required_score)
SELECT 'admins', 'Senior', id, 3.5 FROM skill WHERE name_en = 'Kafka' LIMIT 1 ON CONFLICT DO NOTHING;

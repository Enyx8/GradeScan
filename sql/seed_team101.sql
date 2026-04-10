-- Демо-данные: команда "101" и коллеги-заглушки для теста «Оценить коллег».

INSERT INTO team (name) VALUES ('101') ON CONFLICT (name) DO NOTHING;

INSERT INTO position (frontend, backend, devops, qa, admins)
SELECT false, true, false, false, false
WHERE NOT EXISTS (
    SELECT 1 FROM position
    WHERE backend IS TRUE AND frontend IS NOT TRUE AND devops IS NOT TRUE AND qa IS NOT TRUE AND admins IS NOT TRUE
);

INSERT INTO position (frontend, backend, devops, qa, admins)
SELECT true, false, false, false, false
WHERE NOT EXISTS (
    SELECT 1 FROM position
    WHERE frontend IS TRUE AND backend IS NOT TRUE AND devops IS NOT TRUE AND qa IS NOT TRUE AND admins IS NOT TRUE
);

INSERT INTO position (frontend, backend, devops, qa, admins)
SELECT false, false, true, false, false
WHERE NOT EXISTS (
    SELECT 1 FROM position
    WHERE devops IS TRUE AND frontend IS NOT TRUE AND backend IS NOT TRUE AND qa IS NOT TRUE AND admins IS NOT TRUE
);

INSERT INTO position (frontend, backend, devops, qa, admins)
SELECT false, false, false, true, false
WHERE NOT EXISTS (
    SELECT 1 FROM position
    WHERE qa IS TRUE AND frontend IS NOT TRUE AND backend IS NOT TRUE AND devops IS NOT TRUE AND admins IS NOT TRUE
);

INSERT INTO "user" (
    telegram_id, last_name, first_name, middle_name, role,
    position_id, grade, team_id
)
VALUES
(
    910000001,
    'Петров',
    'Павел',
    NULL,
    'employee',
    (SELECT id FROM position WHERE backend IS TRUE AND frontend IS NOT TRUE AND devops IS NOT TRUE AND qa IS NOT TRUE ORDER BY id LIMIT 1),
    'Senior',
    (SELECT id FROM team WHERE name = '101')
),
(
    910000002,
    'Смирнов',
    'Анна',
    NULL,
    'employee',
    (SELECT id FROM position WHERE backend IS TRUE AND frontend IS NOT TRUE AND devops IS NOT TRUE AND qa IS NOT TRUE ORDER BY id LIMIT 1),
    'Junior',
    (SELECT id FROM team WHERE name = '101')
),
(
    910000003,
    'Козлова',
    'Мария',
    NULL,
    'employee',
    (SELECT id FROM position WHERE frontend IS TRUE AND backend IS NOT TRUE ORDER BY id LIMIT 1),
    'Middle',
    (SELECT id FROM team WHERE name = '101')
),
(
    910000004,
    'Волков',
    'Дмитрий',
    NULL,
    'employee',
    (SELECT id FROM position WHERE devops IS TRUE AND backend IS NOT TRUE ORDER BY id LIMIT 1),
    'Senior',
    (SELECT id FROM team WHERE name = '101')
),
(
    910000005,
    'Орлова',
    'Елена',
    NULL,
    'employee',
    (SELECT id FROM position WHERE qa IS TRUE AND backend IS NOT TRUE AND frontend IS NOT TRUE AND devops IS NOT TRUE ORDER BY id LIMIT 1),
    'Middle',
    (SELECT id FROM team WHERE name = '101')
)
ON CONFLICT (telegram_id) DO UPDATE SET
    last_name = EXCLUDED.last_name,
    first_name = EXCLUDED.first_name,
    middle_name = EXCLUDED.middle_name,
    role = EXCLUDED.role,
    position_id = EXCLUDED.position_id,
    grade = EXCLUDED.grade,
    team_id = EXCLUDED.team_id;

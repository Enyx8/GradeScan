from utils.db import get_connection


def _normalize_grade(grade_text):
    value = grade_text.strip().lower()
    if value in ("junior", "jun", "jr", "june"):
        return "Junior"
    if value in ("middle", "mid"):
        return "Middle"
    if value in ("senior", "sen", "sr"):
        return "Senior"
    raise ValueError("unknown grade")


def _normalize_position(position_text):
    value = position_text.strip().lower()
    mapping = {
        "frontend": "frontend",
        "backend": "backend",
        "devops": "devops",
        "qa": "qa",
        "admin": "admins",
        "admins": "admins",
    }
    if value not in mapping:
        raise ValueError("unknown position")
    return mapping[value]


def _get_or_create_team(cursor, team_name):
    cursor.execute("SELECT id FROM team WHERE name = %s", (team_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO team (name) VALUES (%s) RETURNING id", (team_name,))
    return cursor.fetchone()[0]


def _get_or_create_position(cursor, position_flag):
    query = f"""
        SELECT id FROM position
        WHERE {position_flag} = TRUE
          AND frontend = %s
          AND backend = %s
          AND devops = %s
          AND qa = %s
          AND admins = %s
        LIMIT 1
    """
    values = (
        position_flag == "frontend",
        position_flag == "backend",
        position_flag == "devops",
        position_flag == "qa",
        position_flag == "admins",
    )
    cursor.execute(query, values)
    row = cursor.fetchone()
    if row:
        return row[0]

    insert_query = """
        INSERT INTO position (frontend, backend, devops, qa, admins)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    cursor.execute(insert_query, values)
    return cursor.fetchone()[0]


def addNewUser(telegramID, first_name, last_name, middle_name, team_name, grade_text, position_text, role="employee"):
    normalized_grade = _normalize_grade(grade_text)
    normalized_position = _normalize_position(position_text)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            team_id = _get_or_create_team(cursor, team_name)
            position_id = _get_or_create_position(cursor, normalized_position)
            cursor.execute(
                """
                    INSERT INTO "user" (
                        telegram_id,
                        first_name,
                        last_name,
                        middle_name,
                        role,
                        position_id,
                        grade,
                        team_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO UPDATE
                    SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        middle_name = EXCLUDED.middle_name,
                        role = EXCLUDED.role,
                        position_id = EXCLUDED.position_id,
                        grade = EXCLUDED.grade,
                        team_id = EXCLUDED.team_id
                """,
                (
                    telegramID,
                    first_name,
                    last_name,
                    middle_name,
                    role,
                    position_id,
                    normalized_grade,
                    team_id,
                ),
            )
        conn.commit()
        return 1
    finally:
        conn.close()
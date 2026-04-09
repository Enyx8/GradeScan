from utils.db_manager import get_connection


def _position_to_text(position_row):
    if not position_row:
        return "-"
    frontend, backend, devops, qa, admins = position_row
    if frontend:
        return "frontend"
    if backend:
        return "backend"
    if devops:
        return "devops"
    if qa:
        return "qa"
    if admins:
        return "admins"
    return "-"


def getUserProfile(telegram_id):
    query = """
        SELECT
            u.last_name,
            u.first_name,
            u.middle_name,
            u.grade,
            t.name,
            p.frontend,
            p.backend,
            p.devops,
            p.qa,
            p.admins
        FROM "user" u
        LEFT JOIN team t ON t.id = u.team_id
        LEFT JOIN position p ON p.id = u.position_id
        WHERE u.telegram_id = %s
        LIMIT 1
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (telegram_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "last_name": row[0] or "",
                "first_name": row[1] or "",
                "middle_name": row[2] or "",
                "grade": row[3] or "-",
                "team_name": row[4] or "-",
                "position": _position_to_text(row[5:10]),
            }
    finally:
        conn.close()

from utils.db import get_connection


def getUserRole(telegramID):
    query = 'SELECT role FROM "user" WHERE telegram_id = %s LIMIT 1'

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (telegramID,))
            result = cursor.fetchone()
            if result is None:
                return "NaN"
            return result[0]
    finally:
        conn.close()
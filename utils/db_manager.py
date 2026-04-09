from utils.db_connect import get_connection
from psycopg2.extras import RealDictCursor
from utils.calculations import get_anomaly_status

def check_database_connection():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user")
            db_name, db_user = cursor.fetchone()
            print(f"[DB] Connected to {db_name} as {db_user}")
    finally:
        conn.close()

def get_team_members(reviewer_tg_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Получаем ID и команду текущего пользователя
            cursor.execute('SELECT id, team_id FROM "user" WHERE telegram_id = %s', (reviewer_tg_id,))
            me = cursor.fetchone()
            if not me: return []
            
            query = """
                SELECT u.id, u.first_name, u.last_name, 
                (SELECT COUNT(DISTINCT r.skill_id) FROM review r 
                 JOIN attestation a ON r.attestation_id = a.id 
                 WHERE r.reviewer_id = %s AND r.subject_id = u.id AND a.status = 'in_progress') as skills_rated
                FROM "user" u
                WHERE u.team_id = %s AND u.id != %s AND u.role != 'manager'
            """
            cursor.execute(query, (me['id'], me['team_id'], me['id']))
            return cursor.fetchall()
    finally:
        conn.close()

def check_anomaly(subject_id, skill_id, new_score):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT AVG(score) FROM review 
                WHERE subject_id = %s AND skill_id = %s AND score IS NOT NULL
            """, (subject_id, skill_id))
            avg_res = cursor.fetchone()[0]
            if avg_res is None:
                return False, 0
            
            diff = abs(float(avg_res) - float(new_score))
            return diff > 2.0, diff
    finally:
        conn.close()

def save_review(reviewer_tg_id, subject_id, skill_id, score):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Получаем ID ревьюера
            cursor.execute('SELECT id FROM "user" WHERE telegram_id = %s', (reviewer_tg_id,))
            reviewer_id = cursor.fetchone()[0]
            
            # Получаем/создаем аттестацию
            cursor.execute("SELECT id FROM attestation WHERE subject_id = %s AND status = 'in_progress' LIMIT 1", (subject_id,))
            att_res = cursor.fetchone()
            if not att_res:
                cursor.execute("INSERT INTO attestation (subject_id, period) VALUES (%s, 'April 2026') RETURNING id", (subject_id,))
                att_id = cursor.fetchone()[0]
            else:
                att_id = att_res[0]

            # ЛОГИКА ТЕПЕРЬ ТУТ:
            if score == "undecided":
                val_score, is_strange = None, False
            else:
                val_score = int(score)
                # Вызываем расчет из внешнего файла
                is_strange = get_anomaly_status(subject_id, skill_id, val_score)

            # Сохраняем
            cursor.execute("""
                INSERT INTO review (attestation_id, reviewer_id, subject_id, skill_id, score, is_strange)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (attestation_id, reviewer_id, subject_id, skill_id) 
                DO UPDATE SET score = EXCLUDED.score, is_strange = EXCLUDED.is_strange
            """, (att_id, reviewer_id, subject_id, skill_id, val_score, is_strange))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Save error: {e}")
        return False
    finally:
        conn.close()
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "gradescan"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )

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
            cursor.execute('SELECT id FROM "user" WHERE telegram_id = %s', (reviewer_tg_id,))
            reviewer_id = cursor.fetchone()[0]
            
            cursor.execute('SELECT id FROM attestation WHERE subject_id = %s AND status = \'in_progress\' LIMIT 1', (subject_id,))
            att_res = cursor.fetchone()
            if not att_res:
                cursor.execute('INSERT INTO attestation (subject_id, period) VALUES (%s, %s) RETURNING id', (subject_id, 'April 2026'))
                att_id = cursor.fetchone()[0]
            else:
                att_id = att_res[0]

            if score == "undecided":
                val_score = None
                is_strange = False
            else:
                val_score = int(score)
                is_strange, _ = check_anomaly(subject_id, skill_id, val_score)

            query = """
                INSERT INTO review (attestation_id, reviewer_id, subject_id, skill_id, score, is_strange)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (attestation_id, reviewer_id, subject_id, skill_id) 
                DO UPDATE SET score = EXCLUDED.score, is_strange = EXCLUDED.is_strange
            """
            cursor.execute(query, (att_id, reviewer_id, subject_id, skill_id, val_score, is_strange))
        conn.commit()
        return True
    finally:
        conn.close()
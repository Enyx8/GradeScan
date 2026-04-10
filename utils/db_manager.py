from utils.db_connect import get_connection
from psycopg2 import Error as PsycopgError
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


def list_skills():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name_ru FROM skill ORDER BY id")
            return cursor.fetchall()
    finally:
        conn.close()


def _position_name_sql_expr(alias_u="u", alias_p="p"):
    """CASE: имя направления для position_skill / grade_matrix (совпадает с calculations)."""
    return f"""CASE
    WHEN COALESCE({alias_p}.admins, FALSE) THEN 'admins'
    WHEN COALESCE({alias_p}.frontend, FALSE) THEN 'frontend'
    WHEN COALESCE({alias_p}.backend, FALSE) THEN 'backend'
    WHEN COALESCE({alias_p}.devops, FALSE) THEN 'devops'
    WHEN COALESCE({alias_p}.qa, FALSE) THEN 'qa'
    ELSE 'backend'
END"""


def list_skills_for_subject(subject_user_id):
    """Навыки для оценки коллеги: по его position + грейду (без лишних для направления)."""
    pname = _position_name_sql_expr()
    sql = f"""
        SELECT s.id, s.name_ru
        FROM skill s
        INNER JOIN position_skill ps ON ps.skill_id = s.id
        INNER JOIN "user" u ON u.id = %s
        LEFT JOIN position p ON p.id = u.position_id
        WHERE ps.position_name = ({pname})
          AND CASE COALESCE(u.grade, 'Junior')
                WHEN 'Junior' THEN 1 WHEN 'Middle' THEN 2 WHEN 'Senior' THEN 3 ELSE 1
              END
              >= CASE ps.min_grade
                WHEN 'Junior' THEN 1 WHEN 'Middle' THEN 2 WHEN 'Senior' THEN 3 ELSE 1
              END
        ORDER BY
            CASE ps.min_grade WHEN 'Junior' THEN 1 WHEN 'Middle' THEN 2 WHEN 'Senior' THEN 3 END,
            s.id
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, (subject_user_id,))
                rows = cursor.fetchall()
            except PsycopgError:
                return list_skills()
            if not rows:
                return list_skills()
            return rows
    finally:
        conn.close()


def evaluation_target_for_subject(subject_user_id):
    """Сколько оценок нужно для «галочки» у этого сотрудника (не больше 8)."""
    n = len(list_skills_for_subject(subject_user_id))
    return min(n, 8) if n else 1


def rated_skill_ids_for_reviewer(reviewer_tg_id, subject_user_id):
    """skill_id, по которым текущий рецензент уже оставил ответ в активной аттестации субъекта."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT r.skill_id
                FROM review r
                JOIN attestation a ON r.attestation_id = a.id
                JOIN "user" rev ON rev.id = r.reviewer_id
                WHERE rev.telegram_id = %s
                  AND r.subject_id = %s
                  AND a.subject_id = %s
                  AND a.status = 'in_progress'
                """,
                (reviewer_tg_id, subject_user_id, subject_user_id),
            )
            return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def promote_user_to_manager(telegram_id):
    """Переводит пользователя из роли employee в manager, привязывает к команде как manager_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, role, team_id FROM "user" WHERE telegram_id = %s',
                (telegram_id,),
            )
            row = cursor.fetchone()
            if not row:
                return False
            uid, role, team_id = row
            if role != "employee":
                return False
            cursor.execute(
                'UPDATE "user" SET role = %s WHERE id = %s',
                ("manager", uid),
            )
            if team_id:
                cursor.execute(
                    "UPDATE team SET manager_id = %s WHERE id = %s",
                    (uid, team_id),
                )
        conn.commit()
        return True
    except Exception as exc:
        conn.rollback()
        print(f"[DB] promote_user_to_manager: {exc}")
        return False
    finally:
        conn.close()


def skill_allowed_for_subject(subject_user_id, skill_id):
    ids = {row[0] for row in list_skills_for_subject(subject_user_id)}
    return int(skill_id) in ids


def delete_user_by_telegram_id(telegram_id):
    """
    Удаляет пользователя и связанные данные (review, attestation по CASCADE в схеме).
    team.manager_id для этого пользователя обнуляется (ON DELETE SET NULL).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM "user" WHERE telegram_id = %s RETURNING id', (telegram_id,))
            deleted = cursor.fetchone()
        conn.commit()
        return deleted is not None
    except Exception as exc:
        conn.rollback()
        print(f"[DB] delete_user_by_telegram_id: {exc}")
        return False
    finally:
        conn.close()

def get_team_members(reviewer_tg_id):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id, team_id FROM "user" WHERE telegram_id = %s', (reviewer_tg_id,))
            me = cursor.fetchone()
            if not me:
                return []

            pname = _position_name_sql_expr()
            grade_ord_u = """CASE COALESCE(u.grade, 'Junior')
                WHEN 'Junior' THEN 1 WHEN 'Middle' THEN 2 WHEN 'Senior' THEN 3 ELSE 1 END"""
            grade_ord_ps = """CASE ps.min_grade
                WHEN 'Junior' THEN 1 WHEN 'Middle' THEN 2 WHEN 'Senior' THEN 3 ELSE 1 END"""

            query = f"""
                SELECT u.id, u.first_name, u.last_name,
                (
                    SELECT COUNT(*)::int FROM position_skill ps
                    WHERE ps.position_name = ({pname})
                      AND {grade_ord_u} >= {grade_ord_ps}
                ) AS skills_target,
                (
                    SELECT COUNT(DISTINCT r.skill_id) FROM review r
                    JOIN attestation a ON r.attestation_id = a.id
                    INNER JOIN position_skill ps ON ps.skill_id = r.skill_id
                      AND ps.position_name = ({pname})
                      AND {grade_ord_u} >= {grade_ord_ps}
                    WHERE r.reviewer_id = %s AND r.subject_id = u.id AND a.status = 'in_progress'
                ) AS skills_rated
                FROM "user" u
                LEFT JOIN position p ON p.id = u.position_id
                WHERE u.team_id = %s AND u.id != %s AND u.role != 'manager'
            """
            legacy = """
                SELECT u.id, u.first_name, u.last_name,
                (
                    SELECT COUNT(DISTINCT r.skill_id) FROM review r
                    JOIN attestation a ON r.attestation_id = a.id
                    WHERE r.reviewer_id = %s AND r.subject_id = u.id AND a.status = 'in_progress'
                ) AS skills_rated
                FROM "user" u
                WHERE u.team_id = %s AND u.id != %s AND u.role != 'manager'
            """
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'position_skill'
                ) AS has_ps
                """
            )
            has_row = cursor.fetchone()
            has_position_skill = bool(has_row and has_row.get("has_ps"))

            if has_position_skill:
                try:
                    cursor.execute(query, (me["id"], me["team_id"], me["id"]))
                except PsycopgError:
                    conn.rollback()
                    cursor.execute(legacy, (me["id"], me["team_id"], me["id"]))
            else:
                cursor.execute(legacy, (me["id"], me["team_id"], me["id"]))

            rows = cursor.fetchall()
            for row in rows:
                st = row.get("skills_target")
                if st is None or st == 0:
                    uid = row["id"]
                    row["skills_target"] = max(len(list_skills_for_subject(uid)), 1)
            return rows
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
            if not skill_allowed_for_subject(int(subject_id), int(skill_id)):
                return False

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
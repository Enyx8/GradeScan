from utils.db_connect import get_connection

def get_anomaly_status(subject_id, skill_id, new_score):
    """
    Бизнес-логика определения аномалии.
    Объединяет историю и текущее мнение команды.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Получаем историю (прошлые аттестации)
            cursor.execute("""
                SELECT AVG(r.score) FROM review r
                JOIN attestation a ON r.attestation_id = a.id
                WHERE r.subject_id = %s AND r.skill_id = %s 
                AND a.status = 'completed' AND r.score IS NOT NULL
            """, (subject_id, skill_id))
            avg_old = cursor.fetchone()[0]
            
            # 2. Получаем текущий срез (другие оценки в этой сессии)
            cursor.execute("""
                SELECT AVG(score) FROM review 
                WHERE subject_id = %s AND skill_id = %s 
                AND score IS NOT NULL
            """, (subject_id, skill_id))
            avg_curr = cursor.fetchone()[0]

            # 3. Вычисляем "эталон" по твоей идее
            if avg_old is not None and avg_curr is not None:
                reference = (float(avg_old) + float(avg_curr)) / 2
            elif avg_old is not None:
                reference = float(avg_old)
            elif avg_curr is not None:
                reference = float(avg_curr)
            else:
                return False # Сравнивать не с чем

            diff = abs(reference - float(new_score))
            return diff > 2.0
    finally:
        conn.close()

def calculate_grade_conclusion(subject_id):
    """
    Сравнивает средние оценки сотрудника с матрицей компетенций.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Получаем средние баллы по навыкам (игнорируя аномалии)
            query_stats = """
                SELECT s.id, s.name_ru, AVG(r.score) as avg_score
                FROM review r
                JOIN skill s ON s.id = r.skill_id
                WHERE r.subject_id = %s AND r.is_strange = FALSE AND r.score IS NOT NULL
                GROUP BY s.id, s.name_ru
            """
            cursor.execute(query_stats, (subject_id,))
            user_stats = cursor.fetchall()

            if not user_stats:
                return None

            # Определяем позицию сотрудника
            cursor.execute("""
                SELECT p.frontend, p.backend, p.devops, p.qa 
                FROM "user" u 
                JOIN position p ON u.position_id = p.id 
                WHERE u.id = %s
            """, (subject_id,))
            pos_row = cursor.fetchone()
            
            pos_name = 'backend' # Default
            if pos_row:
                flags = ['frontend', 'backend', 'devops', 'qa']
                for i, flag in enumerate(pos_row):
                    if flag: 
                        pos_name = flags[i]
                        break

            # Алгоритм проверки грейда (от Senior к Junior)
            grades = ['Senior', 'Middle', 'Junior']
            recommended_grade = "Intern"
            
            for check_grade in grades:
                cursor.execute("""
                    SELECT skill_id, required_score FROM grade_matrix 
                    WHERE position_name = %s AND grade = %s
                """, (pos_name, check_grade))
                requirements = {row[0]: float(row[1]) for row in cursor.fetchall()}
                
                if not requirements: continue

                match = True
                for s_id, s_name, avg_score in user_stats:
                    req = requirements.get(s_id, 0)
                    if float(avg_score) < req:
                        match = False
                        break
                
                if match:
                    recommended_grade = check_grade
                    break

            return {
                "stats": user_stats,
                "recommended_grade": recommended_grade,
                "position": pos_name
            }
    finally:
        conn.close()
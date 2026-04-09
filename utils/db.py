import os
import psycopg2


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

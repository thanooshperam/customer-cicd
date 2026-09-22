import os
import psycopg2


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )


def check_database_connection():
    connection = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        cursor.close()

        return result == (1,)

    except Exception as error:
        print(f"Database connection failed: {error}")
        return False

    finally:
        if connection:
            connection.close()
import sqlite3

def find_user_by_name(conn, username: str):
    # Potential SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

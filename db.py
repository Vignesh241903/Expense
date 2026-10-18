import os
import psycopg2
import uuid

def _get_db_config(key, default=""):
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)

conn = psycopg2.connect(
    host=_get_db_config("DB_HOST", "localhost"),
    database=_get_db_config("DB_NAME", "expense_01"),
    user=_get_db_config("DB_USER", "postgres"),
    password=_get_db_config("DB_PASSWORD", ""),
    port=_get_db_config("DB_PORT", "5432")
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(100),
    username VARCHAR(100) UNIQUE,
    password VARCHAR(100)
)
""")

# SESSIONS TABLE - lets a login survive a full browser/page reload.
# A random token is stored in the URL (st.query_params) instead of the
# password, and this table maps that token back to a user.
cur.execute("""
CREATE TABLE IF NOT EXISTS sessions(
    token VARCHAR(64) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

conn.commit()

# CREATE ACCOUNT
def add_user(fullname, email, username, password):

    try:

        cur.execute(
            """
            INSERT INTO users(fullname,email,username,password)
            VALUES(%s,%s,%s,%s)
            """,
            (fullname, email, username, password)
        )

        conn.commit()

        return True

    except Exception as e:
        print(e)
        return False


# LOGIN CHECK
def login_user(username, password):

    cur.execute(
        """
        SELECT * FROM users
        WHERE username=%s AND password=%s
        """,
        (username, password)
    )

    data = cur.fetchone()

    return data

def create_session(user_id):

    token = uuid.uuid4().hex

    cur.execute(
        """
        INSERT INTO sessions(token, user_id)
        VALUES(%s,%s)
        """,
        (token, user_id)
    )

    conn.commit()

    return token


def get_user_by_token(token):

    cur.execute(
        """
        SELECT users.* FROM users
        JOIN sessions ON sessions.user_id = users.id
        WHERE sessions.token = %s
        """,
        (token,)
    )

    return cur.fetchone()


def delete_session(token):

    try:
        cur.execute(
            "DELETE FROM sessions WHERE token=%s",
            (token,)
        )
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
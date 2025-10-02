import psycopg2
from config import Config

class UserSession:
    def __init__(self, user_id, session_token, created_at, expires_at, is_active=True):
        self.user_id = user_id
        self.session_token = session_token
        self.created_at = created_at
        self.expires_at = expires_at
        self.is_active = is_active

    def save(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_sessions (user_id, session_token, created_at, expires_at, is_active) VALUES (%s,%s,%s,%s,%s)",
            (self.user_id, self.session_token, self.created_at, self.expires_at, self.is_active)
        )
        conn.commit()
        cur.close()
        conn.close()
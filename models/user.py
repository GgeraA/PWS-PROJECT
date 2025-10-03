import psycopg2
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, id=None, nombre=None, email=None, password=None,
                 rol="user", two_factor_enabled=False, two_factor_secret=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret

    # ---------- CRUD ----------

    @staticmethod
    def get_all():
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, email, password, rol, two_factor_enabled, two_factor_secret
            FROM users ORDER BY id
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [User(*row) for row in rows]

    @staticmethod
    def find_by_id(user_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, email, password, rol, two_factor_enabled, two_factor_secret
            FROM users WHERE id=%s
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return User(*row)
        return None

    @staticmethod
    def find_by_email(email):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, email, password, rol, two_factor_enabled, two_factor_secret
            FROM users WHERE email=%s
        """, (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return User(*row)
        return None

    def save(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (nombre, email, password, rol, two_factor_enabled, two_factor_secret)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
        """, (self.nombre, self.email, self.password, self.rol,
              self.two_factor_enabled, self.two_factor_secret))
        self.id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return self.id

    def update(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
            SET nombre=%s, email=%s, password=%s, rol=%s, two_factor_enabled=%s, two_factor_secret=%s
            WHERE id=%s
        """, (self.nombre, self.email, self.password, self.rol,
              self.two_factor_enabled, self.two_factor_secret, self.id))
        conn.commit()
        cur.close()
        conn.close()
        return self.id

    @staticmethod
    def delete(user_id):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=%s RETURNING id", (user_id,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)

    # ---------- LOGIN ----------
    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

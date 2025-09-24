import psycopg2
from config import DATABASE

class User:
    def __init__(self, id=None, name=None, email=None, password=None, role=None,
                 two_factor_enabled=False, two_factor_secret=None):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "two_factor_enabled": self.two_factor_enabled
            # No devolvemos el secreto 2FA por seguridad
        }

    @staticmethod
    def get_all():
        conn = psycopg2.connect(**DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, rol, two_factor_enabled, two_factor_secret FROM users ORDER BY id;")
        rows = cur.fetchall()
        users = [
            User(
                id=r[0],
                name=r[1],
                email=r[2],
                role=r[3],
                two_factor_enabled=r[4],
                two_factor_secret=r[5]
            )
            for r in rows
        ]
        conn.close()
        return users

    def save(self):
        conn = psycopg2.connect(**DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (nombre, email, password, rol, two_factor_enabled, two_factor_secret) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
            (self.name, self.email, self.password, self.role, self.two_factor_enabled, self.two_factor_secret)
        )
        self.id = cur.fetchone()[0]  # Guarda el ID generado automáticamente
        conn.commit()
        conn.close()

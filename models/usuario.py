import psycopg2
from config import DATABASE

class Usuario:
    def __init__(self, id=None, nombre=None, email=None, password=None, rol=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol

    @staticmethod
    def get_all():
        conn = psycopg2.connect(**DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, rol FROM usuarios ORDER BY id;")
        rows = cur.fetchall()
        usuarios = [Usuario(id=r[0], nombre=r[1], email=r[2], rol=r[3]) for r in rows]
        conn.close()
        return usuarios

    def save(self):
        conn = psycopg2.connect(**DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)",
            (self.nombre, self.email, self.password, self.rol)
        )
        conn.commit()
        conn.close()
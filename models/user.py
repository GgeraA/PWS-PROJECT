import psycopg2
from config import Config
from passlib.hash import bcrypt

class User:
    def __init__(self, id=None, nombre=None, email=None, password=None, rol="usuario", two_factor_enabled=False, two_factor_secret=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret

    # ---------- CRUD BÁSICO ----------
    @staticmethod
    def get_all():
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, rol FROM users")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def save(self):
        """Inserta un nuevo usuario"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (nombre, email, password, rol, two_factor_enabled, two_factor_secret) 
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (self.nombre, self.email, self.password, self.rol, self.two_factor_enabled, self.two_factor_secret)
        )
        self.id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return self.id

    @staticmethod
    def create_user(nombre, email, password, rol="usuario"):
        """Crea usuario hasheando la contraseña"""
        hashed = bcrypt.hash(password)
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO users (nombre, email, password, rol) 
                VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (nombre, email, hashed, rol)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def find_by_email(email):
        """Busca usuario por email"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, password, rol, two_factor_enabled, two_factor_secret FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        conn.close()
        if row:
            return User(id=row[0], nombre=row[1], email=row[2], password=row[3], rol=row[4], two_factor_enabled=row[5], two_factor_secret=row[6])
        return None

    # ---------- ROLES ----------
    @staticmethod
    def set_role(user_id, new_role):
        """Actualiza el rol de un usuario"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("UPDATE users SET rol = %s WHERE id = %s RETURNING id", (new_role, user_id))
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return bool(row)

    @staticmethod
    def get_all_with_roles():
        """Devuelve todos los usuarios con sus roles"""
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, rol FROM users ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return [{"id": r[0], "nombre": r[1], "email": r[2], "rol": r[3]} for r in rows]
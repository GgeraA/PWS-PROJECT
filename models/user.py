import psycopg2
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User:
    # Roles permitidos según la restricción CHECK en la base de datos
    ALLOWED_ROLES = {"admin", "usuario", "visitante"}  # Ajusta según tu BD
    
    def __init__(self, id=None, nombre=None, email=None, password=None,
                 rol="usuario", two_factor_enabled=False, two_factor_secret=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol if rol in self.ALLOWED_ROLES else "usuario"  # Valor por defecto seguro
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """Convertir a diccionario para JSON serialization"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "two_factor_enabled": self.two_factor_enabled,
            "two_factor_secret": self.two_factor_secret,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    # ---------- CRUD ----------

    @staticmethod
    def get_all():
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, email, password, rol, two_factor_enabled, 
                   two_factor_secret, created_at, updated_at
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
            SELECT id, nombre, email, password, rol, two_factor_enabled, 
                   two_factor_secret, created_at, updated_at
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
            SELECT id, nombre, email, password, rol, two_factor_enabled, 
                   two_factor_secret, created_at, updated_at
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
        try:
            cur.execute("""
                INSERT INTO users (nombre, email, password, rol, two_factor_enabled, two_factor_secret)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, created_at, updated_at
            """, (self.nombre, self.email, self.password, self.rol,
                  self.two_factor_enabled, self.two_factor_secret))
            result = cur.fetchone()
            self.id = result[0]
            self.created_at = result[1]
            self.updated_at = result[2]
            conn.commit()
            return self.id
        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def update(self):
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users
                SET nombre=%s, email=%s, password=%s, rol=%s, 
                    two_factor_enabled=%s, two_factor_secret=%s, updated_at=NOW()
                WHERE id=%s
                RETURNING updated_at
            """, (self.nombre, self.email, self.password, self.rol,
                  self.two_factor_enabled, self.two_factor_secret, self.id))
            result = cur.fetchone()
            if result:
                self.updated_at = result[0]
            conn.commit()
            return self.id
        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

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

    @staticmethod
    def set_role(user_id, new_role):
        if new_role not in User.ALLOWED_ROLES:
            return False
            
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE users SET rol=%s, updated_at=NOW() WHERE id=%s RETURNING id
            """, (new_role, user_id))
            row = cur.fetchone()
            conn.commit()
            return bool(row)
        except psycopg2.IntegrityError:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_all_with_roles():
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, email, rol, created_at 
            FROM users ORDER BY id
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id": row[0], 
                "nombre": row[1], 
                "email": row[2], 
                "rol": row[3], 
                "created_at": row[4].isoformat() if row[4] else None
            } 
            for row in rows
        ]

    # ---------- AUTH ----------
    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def create_user(nombre, email, password, rol="usuario"):
        # Asegurar que el rol sea válido
        if rol not in User.ALLOWED_ROLES:
            rol = "usuario"
            
        user = User(
            nombre=nombre,
            email=email,
            password=User.hash_password(password),
            rol=rol
        )
        return user.save()
import psycopg2
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User:
    ALLOWED_ROLES = {"admin", "usuario", "visitante"}
    
    def __init__(self, id=None, nombre=None, email=None, password=None,
                 rol="usuario", two_factor_enabled=False, two_factor_secret=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol if rol in self.ALLOWED_ROLES else "usuario"
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """Convertir a diccionario para JSON"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "two_factor_enabled": self.two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    # ---------- CRUD COMPLETO ----------
    @staticmethod
    def get_all():
        """Obtener todos los usuarios"""
        conn = psycopg2.connect(**Config.get_database_config())
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
        """Buscar usuario por ID"""
        conn = psycopg2.connect(**Config.get_database_config())
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
        """Buscar usuario por email - ESTE ES EL QUE FALTA"""
        conn = psycopg2.connect(**Config.get_database_config())
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
        """Guardar nuevo usuario"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (nombre, email, password, rol, two_factor_enabled, two_factor_secret)
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING id, created_at, updated_at
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
        """Actualizar usuario existente"""
        conn = psycopg2.connect(**Config.get_database_config())
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
        """Eliminar usuario"""
        conn = psycopg2.connect(**Config.get_database_config())
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=%s RETURNING id", (user_id,))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return bool(row)

    # ---------- AUTH ----------
    def check_password(self, password):
        """Verificar contraseña"""
        if not self.password:
            return False
        return check_password_hash(self.password, password)

    @staticmethod
    def hash_password(password):
        """Generar hash de contraseña con método moderno"""
        return generate_password_hash(
            password, 
            method='scrypt',
            salt_length=16
        )

    @staticmethod
    def create_user(nombre, email, password, rol="usuario"):
        """Crear nuevo usuario (método de conveniencia)"""
        try:
            if rol not in User.ALLOWED_ROLES:
                rol = "usuario"
            
            password_hash = User.hash_password(password)
            
            user = User(
                nombre=nombre,
                email=email,
                password=password_hash,
                rol=rol
            )
            
            user_id = user.save()
            return user_id
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            raise

    @staticmethod
    def update_password(email, new_password):
        """Actualizar contraseña de usuario"""
        try:
            conn = psycopg2.connect(**Config.get_database_config())
            cur = conn.cursor()
        
            password_hash = User.hash_password(new_password)
            
            cur.execute("""
                UPDATE users 
                SET password = %s, updated_at = NOW()
                WHERE email = %s
                RETURNING id
            """, (password_hash, email))
        
            row = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
        
            return bool(row)
        except Exception as e:
            print(f"❌ Error actualizando contraseña: {e}")
            return False

    @staticmethod
    def get_all_with_roles():
        """Obtener usuarios con información básica"""
        conn = psycopg2.connect(**Config.get_database_config())
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
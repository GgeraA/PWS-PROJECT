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
        self.password = password  # Este ya es el HASH, no contraseña en texto plano
        self.rol = rol if rol in self.ALLOWED_ROLES else "usuario"
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_secret = two_factor_secret
        self.created_at = created_at
        self.updated_at = updated_at

    # ... resto del código igual ...

    # ---------- AUTH ----------
    def check_password(self, password):
        """Verificar contraseña - CORREGIDO"""
        if not self.password:
            return False
        # self.password YA ES EL HASH almacenado en la BD
        return check_password_hash(self.password, password)  # ✅ USAR self.password

    @staticmethod
    def hash_password(password):
        """Generar hash de contraseña con método moderno"""
        return generate_password_hash(
            password, 
            method='scrypt',  # Método moderno
            salt_length=16
        )

    @staticmethod
    def create_user(nombre, email, password, rol="usuario"):
        try:
            print(f"🔍 USER.CREATE_USER - Iniciando: {email}")
            
            if rol not in User.ALLOWED_ROLES:
                rol = "usuario"
            
            # Usar hash_password CON MÉTODO MODERNO
            password_hash = User.hash_password(password)  # ✅ Usar método corregido
            
            print(f"🔍 USER.CREATE_USER - Password hasheado")
            
            user = User(
                nombre=nombre,
                email=email,
                password=password_hash,  # ✅ Guardar el HASH
                rol=rol
            )
            
            user_id = user.save()
            print(f"✅ USER.CREATE_USER - Usuario guardado: {user_id}")
            return user_id
            
        except Exception as e:
            print(f"❌ USER.CREATE_USER - Error: {type(e).__name__}: {str(e)}")
            raise e

    @staticmethod
    def update_password(email, new_password):
        """Actualizar contraseña de usuario"""
        try:
            conn = psycopg2.connect(**Config.get_database_config())
            cur = conn.cursor()
        
            # Usar hash_password con método moderno
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
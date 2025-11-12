import sys
import os

# Forzar UTF-8 a nivel del sistema
os.environ['PYTHONUTF8'] = '1'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

print("🔧 TEST - Configurando encoding...")

import psycopg2
from werkzeug.security import generate_password_hash

def test_register():
    try:
        print("🎯 TEST - Conectando a BD...")
        
        # Conexión directa y simple
        conn = psycopg2.connect(
            database="seguridad",
            user="postgres", 
            password="123456",
            host="localhost",
            port=5432
        )
        
        cur = conn.cursor()
        print("✅ TEST - Conexión exitosa!")
        
        # Insertar usuario de prueba
        password_hash = generate_password_hash("Test123$")
        cur.execute("""
            INSERT INTO users (nombre, email, password, rol, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """, ("Usuario Test", "test@test.com", password_hash, "usuario"))
        
        user_id = cur.fetchone()[0]
        conn.commit()
        
        print(f"✅ TEST - Usuario creado: {user_id}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ TEST - Error: {e}")
        return False

if __name__ == "__main__":
    test_register()
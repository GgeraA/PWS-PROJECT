import psycopg2
import sys
import os

print("🔧 DEBUG POSTGRESQL")

try:
    # Conexión básica
    conn = psycopg2.connect(
        database="seguridad",
        user="postgres", 
        password="123456",
        host="localhost",
        port=5432
    )
    print("✅ CONEXIÓN EXITOSA")
    
    cur = conn.cursor()
    
    # Probar consulta simple
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"✅ PostgreSQL Version: {version}")
    
    # Verificar tabla users
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users'
    """)
    columns = cur.fetchall()
    print("✅ Columnas de la tabla 'users':")
    for col in columns:
        print(f"   - {col[0]}: {col[1]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"❌ Mensaje: {str(e)}")
    print(f"❌ Args: {e.args}")
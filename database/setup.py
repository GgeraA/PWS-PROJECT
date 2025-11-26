import psycopg2
import os
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self):
        self.conn_params = Config.DATABASE
    
    def create_tables(self):
        """Crear todas las tablas EXACTAMENTE como las tienes localmente"""
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()
            
            logger.info("🗄️ Creando tablas...")
            
            # 1. Tabla users (PRIMERO por las foreign keys)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    email VARCHAR(150) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    rol VARCHAR(50) NOT NULL CHECK (rol IN ('admin', 'usuario', 'visitante')),
                    two_factor_enabled BOOLEAN DEFAULT false,
                    two_factor_secret VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Tabla 'users' creada")
            
            # 2. Tabla suppliers
            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    supplier_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    contact VARCHAR(100),
                    email VARCHAR(150),
                    address TEXT
                )
            """)
            logger.info("✅ Tabla 'suppliers' creada")
            
            # 3. Tabla products
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id SERIAL PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    unit VARCHAR(20),
                    minimum_stock INTEGER DEFAULT 0,
                    current_stock INTEGER DEFAULT 0 CHECK (current_stock >= 0),
                    price NUMERIC(10,2) NOT NULL,
                    barcode VARCHAR(50),
                    brand VARCHAR(100),
                    cost_price NUMERIC(10,2),
                    maximum_stock INTEGER DEFAULT 0,
                    tax_rate NUMERIC(5,2) DEFAULT 0.0,
                    supplier VARCHAR(100),
                    location VARCHAR(100)
                )
            """)
            logger.info("✅ Tabla 'products' creada")
            
            # 4. Tabla sales
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    sale_id SERIAL PRIMARY KEY,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER REFERENCES users(id),
                    total NUMERIC(12,2) DEFAULT 0
                )
            """)
            logger.info("✅ Tabla 'sales' creada")
            
            # 5. Tabla sale_details
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sale_details (
                    detail_id SERIAL PRIMARY KEY,
                    sale_id INTEGER NOT NULL REFERENCES sales(sale_id),
                    product_id INTEGER NOT NULL REFERENCES products(product_id),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    price NUMERIC(10,2) NOT NULL,
                    subtotal NUMERIC(12,2) GENERATED ALWAYS AS (quantity * price) STORED
                )
            """)
            logger.info("✅ Tabla 'sale_details' creada")
            
            # 6. Tabla movements
            cur.execute("""
                CREATE TABLE IF NOT EXISTS movements (
                    movement_id SERIAL PRIMARY KEY,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    type VARCHAR(10) DEFAULT 'Entry' CHECK (type IN ('Entry', 'Exit')),
                    product_id INTEGER NOT NULL REFERENCES products(product_id),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    reference VARCHAR(100),
                    supplier_id INTEGER REFERENCES suppliers(supplier_id),
                    user_id INTEGER REFERENCES users(id)
                )
            """)
            logger.info("✅ Tabla 'movements' creada")
            
            # 7. Tabla password_resets
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    token VARCHAR(255) NOT NULL,
                    expira_en TIMESTAMP NOT NULL
                )
            """)
            logger.info("✅ Tabla 'password_resets' creada")
            
            # 8. Tabla user_sessions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    ip_address TEXT,
                    user_agent TEXT,
                    location_data JSONB,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Tabla 'user_sessions' creada")
            
            # Crear índices para mejor performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sale_details_product ON sale_details(product_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_movements_product ON movements(product_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)")
            
            logger.info("✅ Índices creados")
            
            conn.commit()
            logger.info("🎉 ¡Todas las tablas creadas exitosamente!")
            
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                cur.close()
                conn.close()
    
    def check_database_connection(self):
        """Verificar conexión a la base de datos"""
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()
            cur.execute("SELECT version()")
            version = cur.fetchone()
            conn.close()
            logger.info(f"✅ Conexión a PostgreSQL exitosa: {version[0]}")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def initialize_sample_data(self):
        """Insertar datos de ejemplo esenciales"""
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()
            
            # Verificar si ya hay usuarios
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            if user_count == 0:
                logger.info("📝 Insertando datos de ejemplo esenciales...")
                
                # Insertar usuario admin por defecto
                cur.execute("""
                    INSERT INTO users (nombre, email, password, rol) 
                    VALUES (%s, %s, %s, %s)
                """, (
                    "Administrador", 
                    "admin@sistema.com", 
                    "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: 'secret'
                    "admin"
                ))
                
                # Insertar algunos productos de ejemplo
                sample_products = [
                    ('LAP-001', 'Laptop Gaming ASUS', 'Laptop gaming de alto rendimiento', 'Electrónica', 'pz', 5, 10, 25999.99, '123456789', 'ASUS', 22000.00, 20, 16.0, 'Tecnología SA', 'Almacén A'),
                    ('MOU-001', 'Mouse Logitech G Pro', 'Mouse gaming profesional', 'Accesorios', 'pz', 10, 25, 1299.99, '123456790', 'Logitech', 900.00, 50, 16.0, 'Tecnología SA', 'Almacén B'),
                    ('TEC-001', 'Teclado Mecánico RGB', 'Teclado mecánico con iluminación RGB', 'Accesorios', 'pz', 8, 15, 2299.99, '123456791', 'Redragon', 1800.00, 30, 16.0, 'Tecnología SA', 'Almacén B'),
                    ('MON-001', 'Monitor 24" Curvo', 'Monitor curvo 144Hz', 'Electrónica', 'pz', 3, 8, 4599.99, '123456792', 'Samsung', 3800.00, 15, 16.0, 'Tecnología SA', 'Almacén A'),
                    ('CPU-001', 'PC Gamer Ryzen 5', 'Computadora gaming AMD Ryzen 5', 'Electrónica', 'pz', 2, 5, 15999.99, '123456793', 'HP', 13000.00, 10, 16.0, 'Tecnología SA', 'Almacén A')
                ]
                
                cur.executemany("""
                    INSERT INTO products (code, name, description, category, unit, minimum_stock, current_stock, price, barcode, brand, cost_price, maximum_stock, tax_rate, supplier, location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, sample_products)
                
                # Insertar proveedor de ejemplo
                cur.execute("""
                    INSERT INTO suppliers (name, phone, contact, email, address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    "Tecnología SA",
                    "+52 55 1234 5678", 
                    "Juan Pérez",
                    "contacto@tecnologiasa.com",
                    "Av. Tecnología 123, CDMX"
                ))
                
                conn.commit()
                logger.info("✅ Datos de ejemplo insertados correctamente")
                
                # Credenciales del usuario admin
                logger.info("👤 Usuario admin creado:")
                logger.info("   Email: admin@sistema.com")
                logger.info("   Password: secret")
                
            else:
                logger.info("✅ Ya existen datos en la base de datos")
                
        except Exception as e:
            logger.error(f"❌ Error insertando datos de ejemplo: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                cur.close()
                conn.close()
    
    def verify_tables_structure(self):
        """Verificar que todas las tablas tienen la estructura correcta"""
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()
            
            expected_tables = [
                'users', 'products', 'sales', 'sale_details', 
                'movements', 'suppliers', 'password_resets', 'user_sessions'
            ]
            
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            existing_tables = [row[0] for row in cur.fetchall()]
            missing_tables = [table for table in expected_tables if table not in existing_tables]
            
            if missing_tables:
                logger.warning(f"⚠️ Tablas faltantes: {missing_tables}")
                return False
            else:
                logger.info("✅ Todas las tablas existen")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando estructura: {e}")
            return False
        finally:
            if conn:
                cur.close()
                conn.close()

def initialize_database():
    """Función principal para inicializar la base de datos"""
    setup = DatabaseSetup()
    
    logger.info("🚀 Iniciando inicialización de base de datos...")
    
    # 1. Verificar conexión
    if not setup.check_database_connection():
        logger.error("❌ No se puede conectar a la base de datos")
        return False
    
    try:
        # 2. Crear tablas
        setup.create_tables()
        
        # 3. Insertar datos de ejemplo
        setup.initialize_sample_data()
        
        # 4. Verificar estructura
        if setup.verify_tables_structure():
            logger.info("🎉 Base de datos inicializada EXITOSAMENTE")
            return True
        else:
            logger.error("❌ Problemas con la estructura de la base de datos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error crítico inicializando base de datos: {e}")
        return False
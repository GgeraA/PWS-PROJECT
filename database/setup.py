import psycopg2
import os
import logging
from datetime import datetime, timedelta
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self):
        self.conn_params = Config.get_database_config()
    
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
            cur.close()
            conn.close()
            logger.info(f"✅ Conexión a PostgreSQL exitosa: {version[0]}")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def initialize_sample_data(self):
        """Insertar datos EXACTAMENTE como los tienes localmente"""
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()
            
            # Verificar si ya hay usuarios
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            if user_count == 0:
                logger.info("📝 Insertando datos EXACTOS de tu base local...")
                
                # 1. Insertar usuarios (manteniendo el que ya tienes)
                users = [
                    ('Administrador Principal', 'brayangonzalez030405@gmail.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin'),
                    ('Carlos Mendoza', 'carlos.mendoza@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'usuario'),
                    ('Ana García', 'ana.garcia@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'usuario'),
                    ('Luis Rodríguez', 'luis.rodriguez@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'visitante')
                ]
                
                cur.executemany("""
                    INSERT INTO users (nombre, email, password, rol) 
                    VALUES (%s, %s, %s, %s)
                """, users)
                logger.info("✅ Usuarios insertados")
                
                # 2. Insertar proveedores EXACTOS
                suppliers = [
                    ('Distribuidora López', '4611234567', 'Juan López', 'contacto@lopez.com', 'Av. Principal 123, Celaya, Gto.'),
                    ('Suministros García', '4619876543', 'María García', 'ventas@garcia.com', 'Calle Comercio 45, Celaya, Gto.'),
                    ('Importadora Martínez', '4615551234', 'Carlos Martínez', 'info@martinez.com', 'Blvd. Industrial 890, Celaya, Gto.')
                ]
                
                cur.executemany("""
                    INSERT INTO suppliers (name, phone, contact, email, address)
                    VALUES (%s, %s, %s, %s, %s)
                """, suppliers)
                logger.info("✅ Proveedores insertados")
                
                # 3. Insertar productos EXACTOS (los 12 que mostraste)
                products = [
                    ('LAP-001', 'Laptop HP ProBook 15', 'Laptop empresarial i5 8GB RAM', 'Electrónica', 'pz', 5, 8, 15999.99, '1234567890123', 'HP', 12000.00, 20, 16.0, 'HP Distribuidor', 'Almacén A'),
                    ('MOU-002', 'Mouse Logitech MX Master 3', 'Mouse ergonómico inalámbrico', 'Accesorios', 'pz', 10, 25, 1299.99, '1234567890124', 'Logitech', 800.00, 50, 16.0, 'Logitech Oficial', 'Almacén B'),
                    ('TEC-003', 'Teclado Mecánico Redragon', 'Teclado mecánico RGB', 'Accesorios', 'pz', 8, 15, 1299.99, '1234567890125', 'Redragon', 900.00, 30, 16.0, 'Redragon MX', 'Almacén A'),
                    ('MON-004', 'Monitor Samsung 24" FHD', 'Monitor Full HD 75Hz', 'Electrónica', 'pz', 6, 12, 3299.99, '1234567890126', 'Samsung', 2500.00, 25, 16.0, 'Samsung Distribuidor', 'Almacén C'),
                    ('IMP-005', 'Impresora Epson EcoTank', 'Impresora tanque de tinta', 'Electrónica', 'pz', 3, 5, 5999.99, '1234567890127', 'Epson', 4500.00, 10, 16.0, 'Epson Oficial', 'Almacén B'),
                    ('CAR-006', 'Cartucho Tinta Negro', 'Cartucho tinta negro Epson', 'Consumibles', 'pz', 20, 50, 749.99, '1234567890128', 'Epson', 500.00, 100, 16.0, 'Epson Oficial', 'Almacén D'),
                    ('TAB-007', 'Tablet iPad Air', 'Tablet Apple iPad Air', 'Electrónica', 'pz', 5, 10, 3499.99, '1234567890129', 'Apple', 2800.00, 20, 16.0, 'Apple Premium', 'Almacén A'),
                    ('AUR-008', 'Auriculares Sony WH-1000XM4', 'Auriculares noise cancelling', 'Accesorios', 'pz', 8, 18, 999.99, '1234567890130', 'Sony', 700.00, 40, 16.0, 'Sony Oficial', 'Almacén B'),
                    ('SSD-009', 'Disco Duro SSD 1TB', 'SSD NVMe 1TB', 'Componentes', 'pz', 10, 20, 1999.99, '1234567890131', 'Kingston', 1500.00, 50, 16.0, 'Kingston Distribuidor', 'Almacén C'),
                    ('WEB-010', 'Cámara Webcam Logitech C920', 'Webcam Full HD 1080p', 'Accesorios', 'pz', 8, 15, 1999.99, '1234567890132', 'Logitech', 1200.00, 30, 16.0, 'Logitech Oficial', 'Almacén B'),
                    ('CEL-011', 'Smartphone Samsung Galaxy S23', 'Smartphone Android 128GB', 'Electrónica', 'pz', 6, 12, 2499.99, '1234567890133', 'Samsung', 1800.00, 25, 16.0, 'Samsung Distribuidor', 'Almacén A'),
                    ('LAP-012', 'Laptop Gaming ASUS TUF', 'Laptop gaming i7 RTX 3050', 'Electrónica', 'pz', 3, 6, 15999.99, '1234567890134', 'ASUS', 12000.00, 15, 16.0, 'ASUS Gaming', 'Almacén C')
                ]
                
                cur.executemany("""
                    INSERT INTO products (code, name, description, category, unit, minimum_stock, current_stock, price, barcode, brand, cost_price, maximum_stock, tax_rate, supplier, location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, products)
                logger.info("✅ 12 productos insertados (exactos)")
                
                # 4. Insertar ventas EXACTAS (las 28 que mostraste)
                sales_data = [
                    (1, '2025-11-25 10:30:00', 1, 15999.99),
                    (2, '2025-11-24 15:20:00', 2, 2599.98),
                    (3, '2025-11-23 09:15:00', 1, 1299.99),
                    (4, '2025-11-22 14:45:00', 3, 4599.97),
                    (5, '2025-11-21 11:00:00', 2, 8999.95),
                    (6, '2025-11-20 16:30:00', 1, 3499.99),
                    (7, '2025-11-19 13:20:00', 3, 1999.98),
                    (8, '2025-11-18 10:15:00', 2, 5999.97),
                    (9, '2025-10-15 08:45:00', 1, 2499.99),
                    (10, '2025-10-10 17:00:00', 4, 15999.99),
                    (11, '2025-09-28 11:30:00', 3, 3299.99),
                    (12, '2025-09-15 14:20:00', 2, 7499.98),
                    (13, '2025-08-20 09:45:00', 1, 1999.99),
                    (14, '2025-08-10 16:15:00', 4, 8999.99),
                    (15, '2025-07-25 13:30:00', 2, 4599.99),
                    (16, '2025-07-12 10:45:00', 3, 12999.99),
                    (17, '2025-06-18 15:20:00', 1, 2999.99),
                    (18, '2025-06-05 11:30:00', 4, 7999.99),
                    (19, '2025-05-22 14:15:00', 2, 5999.99),
                    (20, '2025-05-10 09:30:00', 3, 15999.99),
                    (21, '2025-04-28 16:45:00', 1, 3499.99),
                    (22, '2025-04-15 13:20:00', 4, 12999.99),
                    (23, '2025-03-20 10:30:00', 2, 4999.99),
                    (24, '2025-03-08 15:45:00', 3, 8999.99),
                    (25, '2025-02-25 11:15:00', 1, 2499.99),
                    (26, '2025-02-14 14:30:00', 4, 17999.99),
                    (27, '2025-01-30 09:45:00', 2, 3999.99),
                    (28, '2025-01-15 16:20:00', 3, 13999.99)
                ]
                
                cur.executemany("""
                    INSERT INTO sales (sale_id, date, user_id, total)
                    VALUES (%s, %s, %s, %s)
                """, sales_data)
                logger.info("✅ 28 ventas insertadas (exactas)")
                
                # 5. Insertar detalles de venta EXACTOS (los 41 que mostraste)
                sale_details_data = [
                    (1, 1, 1, 1, 15999.99),
                    (2, 2, 2, 2, 1299.99),
                    (3, 3, 3, 1, 1299.99),
                    (4, 4, 4, 1, 3299.99),
                    (5, 4, 2, 1, 1299.98),
                    (6, 5, 5, 1, 5999.99),
                    (7, 5, 6, 2, 1499.98),
                    (8, 6, 7, 1, 3499.99),
                    (9, 7, 8, 2, 999.99),
                    (10, 8, 9, 1, 1999.99),
                    (11, 8, 10, 2, 1999.99),
                    (12, 9, 11, 1, 2499.99),
                    (13, 10, 12, 1, 15999.99),
                    (14, 11, 4, 1, 3299.99),
                    (15, 12, 2, 3, 1299.99),
                    (16, 12, 3, 1, 1299.99),
                    (17, 13, 8, 2, 999.99),
                    (18, 14, 1, 1, 15999.99),
                    (19, 15, 4, 1, 3299.99),
                    (20, 15, 2, 1, 1299.99),
                    (21, 16, 12, 1, 15999.99),
                    (22, 17, 7, 1, 3499.99),
                    (23, 18, 5, 1, 5999.99),
                    (24, 18, 6, 1, 1499.98),
                    (25, 19, 9, 1, 1999.99),
                    (26, 19, 10, 1, 1999.99),
                    (27, 20, 1, 1, 15999.99),
                    (28, 21, 11, 1, 2499.99),
                    (29, 21, 8, 1, 999.99),
                    (30, 22, 12, 1, 15999.99),
                    (31, 23, 4, 1, 3299.99),
                    (32, 23, 2, 1, 1299.99),
                    (33, 24, 5, 1, 5999.99),
                    (34, 24, 6, 2, 1499.98),
                    (35, 25, 3, 1, 1299.99),
                    (36, 25, 2, 1, 1299.99),
                    (37, 26, 1, 1, 15999.99),
                    (38, 26, 9, 1, 1999.99),
                    (39, 27, 7, 1, 3499.99),
                    (40, 28, 12, 1, 15999.99),
                    (41, 28, 8, 1, 999.99)
                ]
                
                cur.executemany("""
                    INSERT INTO sale_details (detail_id, sale_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s, %s)
                """, sale_details_data)
                logger.info("✅ 41 detalles de venta insertados (exactos)")
                
                # 6. Crear algunos movimientos de inventario básicos
                self._create_basic_movements(cur)
                logger.info("✅ Movimientos básicos creados")
                
                conn.commit()
                logger.info("🎉 ¡Datos EXACTOS insertados exitosamente!")
                
                # Mostrar credenciales
                logger.info("👤 Usuarios creados:")
                logger.info("   Admin: admin@sistema.com / secret")
                logger.info("   Vendedor 1: carlos.mendoza@empresa.com / secret")
                logger.info("   Vendedor 2: ana.garcia@empresa.com / secret")
                logger.info("   Visitante: luis.rodriguez@empresa.com / secret")
                
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
    
    def _create_basic_movements(self, cur):
        """Crear movimientos básicos de inventario"""
        movements = []
        
        # Movimientos de entrada para todos los productos
        for product_id in range(1, 13):
            movement = (
                datetime.now() - timedelta(days=60),
                'Entry',
                product_id,
                50,  # Cantidad generosa
                f'INV-INICIAL-{product_id}',
                1,  # supplier_id
                1   # user_id (admin)
            )
            movements.append(movement)
        
        cur.executemany("""
            INSERT INTO movements (date, type, product_id, quantity, reference, supplier_id, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, movements)
    
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
        
        # 3. Insertar datos EXACTOS
        setup.initialize_sample_data()
        
        # 4. Verificar estructura
        if setup.verify_tables_structure():
            logger.info("🎉 Base de datos inicializada EXITOSAMENTE con datos exactos")
            return True
        else:
            logger.error("❌ Problemas con la estructura de la base de datos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error crítico inicializando base de datos: {e}")
        return False
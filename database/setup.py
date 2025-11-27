import psycopg2
import os
import logging
from datetime import datetime, timedelta
import random
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
        """Insertar datos de ejemplo COMPLETOS y REALISTAS"""
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()
            
            # Verificar si ya hay usuarios
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            if user_count == 0:
                logger.info("📝 Insertando datos de ejemplo COMPLETOS...")
                
                # 1. Insertar usuarios
                users = [
                    ('Administrador Principal', 'admin@sistema.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin'),
                    ('Carlos Mendoza', 'carlos.mendoza@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'usuario'),
                    ('Ana García', 'ana.garcia@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'usuario'),
                    ('Luis Rodríguez', 'luis.rodriguez@empresa.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'visitante')
                ]
                
                cur.executemany("""
                    INSERT INTO users (nombre, email, password, rol) 
                    VALUES (%s, %s, %s, %s)
                """, users)
                logger.info("✅ Usuarios insertados")
                
                # 2. Insertar proveedores
                suppliers = [
                    ('Tecnología SA', '+52 55 1234 5678', 'Juan Pérez', 'contacto@tecnologiasa.com', 'Av. Tecnología 123, CDMX'),
                    ('ElectroMundo', '+52 55 2345 6789', 'María López', 'ventas@electromundo.com', 'Blvd. Electrónica 456, GDL'),
                    ('Office Solutions', '+52 55 3456 7890', 'Roberto Sánchez', 'info@officesolutions.com', 'Calle Oficina 789, MTY'),
                    ('Distribuidora Nacional', '+52 55 4567 8901', 'Carmen Ruiz', 'pedidos@distribuidora.com', 'Periférico Norte 321, PUE')
                ]
                
                cur.executemany("""
                    INSERT INTO suppliers (name, phone, contact, email, address)
                    VALUES (%s, %s, %s, %s, %s)
                """, suppliers)
                logger.info("✅ Proveedores insertados")
                
                # 3. Insertar productos más variados
                products = [
                    # Electrónicos
                    ('LAP-001', 'Laptop Gaming ASUS ROG', 'Laptop gaming de alto rendimiento con RTX 4060', 'Electrónicos', 'pz', 5, 15, 25999.99, '1234567890123', 'ASUS', 22000.00, 25, 16.0, 'Tecnología SA', 'Almacén A'),
                    ('LAP-002', 'MacBook Air M2', 'Laptop Apple ultradelgada chip M2', 'Electrónicos', 'pz', 3, 8, 32999.99, '1234567890124', 'Apple', 28000.00, 15, 16.0, 'Tecnología SA', 'Almacén A'),
                    ('MON-001', 'Monitor 24" Curvo Samsung', 'Monitor curvo 144Hz FHD', 'Electrónicos', 'pz', 4, 12, 4599.99, '1234567890125', 'Samsung', 3800.00, 20, 16.0, 'ElectroMundo', 'Almacén A'),
                    ('MON-002', 'Monitor 27" 4K LG', 'Monitor 4K UHD para diseño', 'Electrónicos', 'pz', 2, 6, 7899.99, '1234567890126', 'LG', 6500.00, 10, 16.0, 'ElectroMundo', 'Almacén A'),
                    ('CPU-001', 'PC Gamer Ryzen 5', 'Computadora gaming AMD Ryzen 5 + RTX 3060', 'Electrónicos', 'pz', 2, 5, 15999.99, '1234567890127', 'HP', 13000.00, 8, 16.0, 'Tecnología SA', 'Almacén A'),
                    
                    # Accesorios
                    ('MOU-001', 'Mouse Logitech G Pro', 'Mouse gaming profesional inalámbrico', 'Accesorios', 'pz', 10, 25, 1299.99, '1234567890128', 'Logitech', 900.00, 40, 16.0, 'ElectroMundo', 'Almacén B'),
                    ('MOU-002', 'Mouse Razer DeathAdder', 'Mouse gaming ergonómico', 'Accesorios', 'pz', 8, 18, 899.99, '1234567890129', 'Razer', 650.00, 30, 16.0, 'ElectroMundo', 'Almacén B'),
                    ('TEC-001', 'Teclado Mecánico RGB Redragon', 'Teclado mecánico con iluminación RGB', 'Accesorios', 'pz', 8, 20, 2299.99, '1234567890130', 'Redragon', 1800.00, 35, 16.0, 'ElectroMundo', 'Almacén B'),
                    ('TEC-002', 'Teclado Apple Magic', 'Teclado inalámbrico Apple', 'Accesorios', 'pz', 5, 10, 1899.99, '1234567890131', 'Apple', 1500.00, 20, 16.0, 'Tecnología SA', 'Almacén B'),
                    ('AUD-001', 'Audífonos Sony WH-1000XM4', 'Audífonos noise cancelling', 'Accesorios', 'pz', 3, 8, 5999.99, '1234567890132', 'Sony', 4800.00, 15, 16.0, 'ElectroMundo', 'Almacén B'),
                    
                    # Oficina
                    ('IMP-001', 'Impresora Laser HP', 'Impresora láser multifuncional', 'Oficina', 'pz', 2, 6, 3899.99, '1234567890133', 'HP', 3200.00, 10, 16.0, 'Office Solutions', 'Almacén C'),
                    ('ESC-001', 'Escáner Documentos', 'Escáner de documentos rápido', 'Oficina', 'pz', 1, 3, 2199.99, '1234567890134', 'Canon', 1800.00, 5, 16.0, 'Office Solutions', 'Almacén C'),
                    ('SIL-001', 'Silla Ergonómica Ejecutiva', 'Silla ergonómica para oficina', 'Oficina', 'pz', 1, 4, 4599.99, '1234567890135', 'Ergomex', 3800.00, 8, 16.0, 'Office Solutions', 'Almacén C'),
                    
                    # Software
                    ('SOF-001', 'Microsoft Office 365', 'Suscripción anual Office 365', 'Software', 'pz', 0, 50, 899.99, '1234567890136', 'Microsoft', 600.00, 100, 0.0, 'Distribuidora Nacional', 'Almacén Digital'),
                    ('SOF-002', 'Adobe Creative Cloud', 'Suscripción anual Adobe CC', 'Software', 'pz', 0, 30, 2499.99, '1234567890137', 'Adobe', 2000.00, 60, 0.0, 'Distribuidora Nacional', 'Almacén Digital')
                ]
                
                cur.executemany("""
                    INSERT INTO products (code, name, description, category, unit, minimum_stock, current_stock, price, barcode, brand, cost_price, maximum_stock, tax_rate, supplier, location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, products)
                logger.info("✅ Productos insertados")
                
                # 4. Crear movimientos de inventario iniciales
                self._create_sample_movements(cur)
                logger.info("✅ Movimientos de inventario creados")
                
                # 5. Crear ventas de ejemplo
                self._create_sample_sales(cur)
                logger.info("✅ Ventas de ejemplo creadas")
                
                # 6. Crear sesiones de usuario
                self._create_sample_sessions(cur)
                logger.info("✅ Sesiones de usuario creadas")
                
                conn.commit()
                logger.info("🎉 ¡Datos de ejemplo COMPLETOS insertados exitosamente!")
                
                # Mostrar credenciales
                logger.info("👤 Usuarios creados:")
                logger.info("   Admin: admin@sistema.com / secret")
                logger.info("   Vendedor 1: carlos.mendoza@empresa.com / secret")
                logger.info("   Vendedor 2: ana.garcia@empresa.com / secret")
                
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
    
    def _create_sample_movements(self, cur):
        """Crear movimientos de inventario de ejemplo"""
        # Obtener IDs de productos y usuarios
        cur.execute("SELECT product_id FROM products")
        product_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT id FROM users WHERE rol = 'admin' OR rol = 'usuario'")
        user_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT supplier_id FROM suppliers")
        supplier_ids = [row[0] for row in cur.fetchall()]
        
        # Crear movimientos de entrada (compras/ingresos)
        movements = []
        for product_id in product_ids:
            for _ in range(2):  # 2 movimientos por producto
                movement = (
                    datetime.now() - timedelta(days=random.randint(1, 30)),
                    'Entry',
                    product_id,
                    random.randint(10, 50),
                    f'OC-{random.randint(1000, 9999)}',
                    random.choice(supplier_ids),
                    random.choice(user_ids)
                )
                movements.append(movement)
        
        # Crear movimientos de salida (ajustes/salidas)
        for product_id in product_ids[:8]:  # Solo para algunos productos
            movement = (
                datetime.now() - timedelta(days=random.randint(1, 15)),
                'Exit',
                product_id,
                random.randint(1, 5),
                f'AJ-{random.randint(100, 999)}',
                None,
                random.choice(user_ids)
            )
            movements.append(movement)
        
        cur.executemany("""
            INSERT INTO movements (date, type, product_id, quantity, reference, supplier_id, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, movements)
    
    def _create_sample_sales(self, cur):
        """Crear ventas de ejemplo realistas"""
        # Obtener IDs de productos y usuarios
        cur.execute("SELECT product_id, price FROM products")
        products_data = cur.fetchall()
        
        cur.execute("SELECT id FROM users WHERE rol = 'usuario'")
        seller_ids = [row[0] for row in cur.fetchall()]
        
        # Crear ventas de los últimos 30 días
        sales = []
        sale_details = []
        
        for day in range(30):
            sale_date = datetime.now() - timedelta(days=30-day)
            
            # Crear entre 3-8 ventas por día
            for sale_num in range(random.randint(3, 8)):
                seller_id = random.choice(seller_ids)
                total_sale = 0
                
                # Insertar venta
                cur.execute("""
                    INSERT INTO sales (date, user_id, total)
                    VALUES (%s, %s, %s) RETURNING sale_id
                """, (sale_date, seller_id, 0))
                
                sale_id = cur.fetchone()[0]
                
                # Agregar productos a la venta (1-4 productos por venta)
                sale_products = random.sample(products_data, random.randint(1, 4))
                sale_total = 0
                
                for product in sale_products:
                    product_id, price = product
                    quantity = random.randint(1, 3)
                    subtotal = price * quantity
                    sale_total += subtotal
                    
                    # Insertar detalle de venta
                    cur.execute("""
                        INSERT INTO sale_details (sale_id, product_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (sale_id, product_id, quantity, price))
                    
                    # Actualizar stock del producto
                    cur.execute("""
                        UPDATE products 
                        SET current_stock = current_stock - %s 
                        WHERE product_id = %s
                    """, (quantity, product_id))
                
                # Actualizar total de la venta
                cur.execute("""
                    UPDATE sales SET total = %s WHERE sale_id = %s
                """, (sale_total, sale_id))
    
    def _create_sample_sessions(self, cur):
        """Crear sesiones de usuario de ejemplo"""
        cur.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]
        
        for user_id in user_ids:
            cur.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                f"token_{user_id}_{random.randint(1000, 9999)}",
                datetime.now() + timedelta(hours=24),
                f"192.168.1.{random.randint(1, 255)}",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ))
    
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
        
        # 3. Insertar datos de ejemplo COMPLETOS
        setup.initialize_sample_data()
        
        # 4. Verificar estructura
        if setup.verify_tables_structure():
            logger.info("🎉 Base de datos inicializada EXITOSAMENTE con datos realistas")
            return True
        else:
            logger.error("❌ Problemas con la estructura de la base de datos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error crítico inicializando base de datos: {e}")
        return False
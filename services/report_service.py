from config import Config
import psycopg2
from datetime import datetime, timedelta

def get_db_connection():
    """Obtener conexión a la base de datos usando la configuración correcta"""
    db_config = Config.get_database_config()
    
    try:
        connection = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise

def get_sales_metrics(start_date=None, end_date=None):
    """Obtener métricas generales de ventas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query con filtros de fecha si se proporcionan
        query = """
            SELECT 
                COALESCE(SUM(total), 0) as total_ventas,
                COUNT(*) as total_transacciones,
                COALESCE(AVG(total), 0) as ticket_promedio,
                COALESCE(SUM(
                    SELECT COUNT(*) FROM sale_details WHERE sale_id = sales.id
                ), 0) as total_productos
            FROM sales
            WHERE 1=1
        """
        
        params = []
        if start_date:
            query += " AND sale_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND sale_date <= %s"
            params.append(end_date)
            
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "total_ventas": float(result[0]) if result[0] else 0.0,
            "total_transacciones": result[1] or 0,
            "ticket_promedio": float(result[2]) if result[2] else 0.0,
            "total_productos": result[3] or 0
        }
        
    except Exception as e:
        print(f"Error en get_sales_metrics: {e}")
        return {
            "total_ventas": 0.0,
            "total_transacciones": 0,
            "ticket_promedio": 0.0,
            "total_productos": 0
        }

def get_sales_trend(start_date=None, end_date=None):
    """Obtener tendencia de ventas por día"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Si no se proporcionan fechas, usar último mes
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        query = """
            SELECT 
                sale_date as fecha,
                COALESCE(SUM(total), 0) as ventas,
                COUNT(*) as cantidad
            FROM sales
            WHERE sale_date BETWEEN %s AND %s
            GROUP BY sale_date
            ORDER BY sale_date
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [
            {
                "fecha": row[0].strftime('%Y-%m-%d'),
                "ventas": float(row[1]),
                "cantidad": row[2]
            }
            for row in results
        ]
        
    except Exception as e:
        print(f"Error en get_sales_trend: {e}")
        return []

def get_sales_by_category():
    """Obtener ventas por categoría"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.name as nombre,
                COALESCE(SUM(sd.subtotal), 0) as valor,
                COALESCE(SUM(sd.quantity), 0) as cantidad
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            LEFT JOIN sale_details sd ON p.id = sd.product_id
            GROUP BY c.id, c.name
            ORDER BY valor DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [
            {
                "nombre": row[0],
                "valor": float(row[1]),
                "cantidad": row[2]
            }
            for row in results
        ]
        
    except Exception as e:
        print(f"Error en get_sales_by_category: {e}")
        return []

def get_top_products(limit=5):
    """Obtener productos más vendidos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                p.name as nombre,
                COALESCE(SUM(sd.subtotal), 0) as ventas,
                COALESCE(SUM(sd.quantity), 0) as cantidad
            FROM products p
            LEFT JOIN sale_details sd ON p.id = sd.product_id
            GROUP BY p.id, p.name
            ORDER BY cantidad DESC, ventas DESC
            LIMIT %s
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [
            {
                "nombre": row[0],
                "ventas": float(row[1]),
                "cantidad": row[2]
            }
            for row in results
        ]
        
    except Exception as e:
        print(f"Error en get_top_products: {e}")
        return []
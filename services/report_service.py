import psycopg2
from config import Config
from datetime import datetime, timedelta

def get_sales_metrics(start_date=None, end_date=None):
    """Obtener métricas generales de ventas"""
    try:
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        
        # Si no hay fechas, usar último mes
        if not start_date or not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        
        # Ventas totales
        cur.execute("""
            SELECT COALESCE(SUM(sd.subtotal), 0) as total_ventas,
                   COUNT(DISTINCT s.sale_id) as total_transacciones,
                   COUNT(sd.detail_id) as total_productos
            FROM sales s
            JOIN sale_details sd ON s.sale_id = sd.sale_id
            WHERE s.date BETWEEN %s AND %s
        """, (start_date, end_date))
        
        metrics = cur.fetchone()
        total_ventas = float(metrics[0]) if metrics[0] else 0
        total_transacciones = metrics[1] if metrics[1] else 0
        total_productos = metrics[2] if metrics[2] else 0
        
        # Ticket promedio
        ticket_promedio = total_ventas / total_transacciones if total_transacciones > 0 else 0
        
        conn.close()
        
        return {
            "total_ventas": total_ventas,
            "total_transacciones": total_transacciones,
            "ticket_promedio": ticket_promedio,
            "total_productos": total_productos
        }
        
    except Exception as e:
        print(f"Error en get_sales_metrics: {e}")
        return get_mock_metrics()

def get_sales_trend(start_date=None, end_date=None):
    """Obtener tendencia de ventas por día"""
    try:
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        
        if not start_date or not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        
        cur.execute("""
            SELECT 
                DATE(s.date) as fecha,
                SUM(sd.subtotal) as ventas,
                COUNT(DISTINCT s.sale_id) as cantidad
            FROM sales s
            JOIN sale_details sd ON s.sale_id = sd.sale_id
            WHERE s.date BETWEEN %s AND %s
            GROUP BY DATE(s.date)
            ORDER BY fecha
        """, (start_date, end_date))
        
        rows = cur.fetchall()
        conn.close()
        
        trend_data = []
        for row in rows:
            trend_data.append({
                "fecha": row[0].strftime('%a'),
                "ventas": float(row[1]) if row[1] else 0,
                "cantidad": row[2] if row[2] else 0
            })
        
        return trend_data
        
    except Exception as e:
        print(f"Error en get_sales_trend: {e}")
        return get_mock_trend()

def get_sales_by_category():
    """Obtener ventas por categoría"""
    try:
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                p.category,
                SUM(sd.subtotal) as total_ventas,
                COUNT(sd.detail_id) as cantidad
            FROM sale_details sd
            JOIN products p ON sd.product_id = p.product_id
            GROUP BY p.category
            ORDER BY total_ventas DESC
        """)
        
        rows = cur.fetchall()
        conn.close()
        
        category_data = []
        for row in rows:
            category_data.append({
                "nombre": row[0] or "Sin categoría",
                "valor": float(row[1]) if row[1] else 0,
                "cantidad": row[2] if row[2] else 0
            })
        
        return category_data
        
    except Exception as e:
        print(f"Error en get_sales_by_category: {e}")
        return get_mock_categories()

def get_top_products(limit=5):
    """Obtener productos más vendidos"""
    try:
        conn = psycopg2.connect(**Config.DATABASE)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                p.name,
                SUM(sd.subtotal) as ventas,
                SUM(sd.quantity) as cantidad
            FROM sale_details sd
            JOIN products p ON sd.product_id = p.product_id
            GROUP BY p.name, p.product_id
            ORDER BY ventas DESC
            LIMIT %s
        """, (limit,))
        
        rows = cur.fetchall()
        conn.close()
        
        top_products = []
        for row in rows:
            top_products.append({
                "nombre": row[0],
                "ventas": float(row[1]) if row[1] else 0,
                "cantidad": row[2] if row[2] else 0
            })
        
        return top_products
        
    except Exception as e:
        print(f"Error en get_top_products: {e}")
        return get_mock_top_products()

# Datos mock para desarrollo
def get_mock_metrics():
    return {
        "total_ventas": 431000,
        "total_transacciones": 226,
        "ticket_promedio": 1907,
        "total_productos": 1248
    }

def get_mock_trend():
    return [
        { "fecha": "Lun", "ventas": 45000, "cantidad": 23 },
        { "fecha": "Mar", "ventas": 52000, "cantidad": 28 },
        { "fecha": "Mié", "ventas": 48000, "cantidad": 25 },
        { "fecha": "Jue", "ventas": 61000, "cantidad": 32 },
        { "fecha": "Vie", "ventas": 73000, "cantidad": 38 },
        { "fecha": "Sáb", "ventas": 85000, "cantidad": 45 },
        { "fecha": "Dom", "ventas": 67000, "cantidad": 35 }
    ]

def get_mock_categories():
    return [
        { "nombre": "Electrónica", "valor": 35, "cantidad": 120000 },
        { "nombre": "Accesorios", "valor": 25, "cantidad": 85000 },
        { "nombre": "Componentes", "valor": 20, "cantidad": 68000 },
        { "nombre": "Consumibles", "valor": 12, "cantidad": 41000 },
        { "nombre": "Otros", "valor": 8, "cantidad": 27000 }
    ]

def get_mock_top_products():
    return [
        { "nombre": "Laptop HP ProBook 15", "ventas": 31999.98, "cantidad": 2 },
        { "nombre": "Mouse Logitech MX Master 3", "ventas": 6499.95, "cantidad": 5 },
        { "nombre": "Teclado Mecánico Redragon", "ventas": 1299.99, "cantidad": 1 },
        { "nombre": "Monitor Samsung 24\" FHD", "ventas": 3299.99, "cantidad": 1 },
        { "nombre": "Impresora Epson EcoTank", "ventas": 5999.99, "cantidad": 1 }
    ]
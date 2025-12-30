import sqlite3

def crear_conexion():
    """Establece la conexión con la base de datos SQLite."""
    # Se conecta al archivo inventario.db [cite: 1]
    return sqlite3.connect("inventario.db")

def inicializar_db():
    """Crea las tablas necesarias si no existen al iniciar el sistema."""
    conexion = crear_conexion()
    cursor = conexion.cursor()
    
    # 1. Tabla de Categorías
    # Almacena los nombres únicos de las categorías [cite: 35]
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    
    # 2. Tabla de Productos
    # Incluye el código, nombre, relación con categoría y el campo proveedor 
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            id_categoria INTEGER,
            proveedor TEXT,
            FOREIGN KEY (id_categoria) REFERENCES categorias (id)
        )
    """)
    
    # 3. Tabla de Movimientos
    # Registra las compras y ventas vinculadas a cada producto [cite: 31, 32]
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_producto INTEGER,
            fecha TEXT,
            tipo TEXT, -- Compra o Venta
            precio REAL,
            cantidad INTEGER,
            observaciones TEXT,
            FOREIGN KEY (id_producto) REFERENCES productos (id)
        )
    """)
    
    conexion.commit()
    conexion.close()

if __name__ == "__main__":
    # Permite ejecutar el script directamente para crear la base de datos
    inicializar_db()
    print("Base de datos inicializada correctamente.")
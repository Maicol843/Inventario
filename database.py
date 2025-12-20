import sqlite3

def crear_conexion():
    return sqlite3.connect("inventario.db")

def inicializar_db():
    conexion = crear_conexion()
    cursor = conexion.cursor()
    # Tabla Categorías
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    # Tabla Productos
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
    conexion.commit()
    conexion.close()
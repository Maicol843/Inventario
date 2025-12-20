
import sqlite3

def crear_conexion():
    # Crea (o abre) el archivo de la base de datos
    return sqlite3.connect("sistema_inventario.db")

def inicializar_db():
    conexion = crear_conexion()
    cursor = conexion.cursor()
    # Creamos la tabla de categorías si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    conexion.commit()
    conexion.close()

# Esto asegura que la base de datos se prepare apenas iniciemos
if __name__ == "__main__":
    inicializar_db()
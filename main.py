import sys
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QDialog, QFormLayout, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
import database # Importamos nuestro archivo de base de datos

# --- CLASE PARA EL MODAL (FORMULARIO) ---
class FormularioCategoria(QDialog):
    def __init__(self, titulo="Agregar Categoría", nombre_actual=""):
        super().__init__()
        self.setWindowTitle(titulo)
        self.setFixedSize(300, 150)
        
        layout = QFormLayout(self)
        self.input_nombre = QLineEdit(self)
        self.input_nombre.setText(nombre_actual)
        self.input_nombre.setPlaceholderText("Ej: Bebidas, Lácteos...")
        
        layout.addRow("Nombre de Categoría:", self.input_nombre)
        
        # Botones del Modal
        botones = QHBoxLayout()
        self.btn_guardar = QPushButton("Registrar" if not nombre_actual else "Actualizar")
        self.btn_cancelar = QPushButton("Cancelar")
        
        botones.addWidget(self.btn_guardar)
        botones.addWidget(self.btn_cancelar)
        layout.addRow(botones)
        
        # Eventos
        self.btn_guardar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)

# --- VENTANA PRINCIPAL ---
class VentanaCategorias(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Inventario - Categorías")
        self.resize(1000, 600)
        
        # Variables de paginación
        self.pagina_actual = 0
        self.limite = 10
        
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        # Widget central y layout principal (Horizontal)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout_principal = QHBoxLayout(central_widget)
        layout_principal.setContentsMargins(0,0,0,0)

        # 1. NAVEGADOR IZQUIERDO (Vertical)
        menu_lateral = QFrame()
        menu_lateral.setFixedWidth(200)
        menu_lateral.setStyleSheet("background-color: #2c3e50; color: white;")
        layout_menu = QVBoxLayout(menu_lateral)
        
        lbl_menu = QLabel("INVENTARIO")
        lbl_menu.setStyleSheet("font-weight: bold; font-size: 18px; margin-bottom: 20px;")
        lbl_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_cat = QPushButton("📁 Categorías")
        btn_prod = QPushButton("📦 Productos")
        
        layout_menu.addWidget(lbl_menu)
        layout_menu.addWidget(btn_cat)
        layout_menu.addWidget(btn_prod)
        layout_menu.addStretch() # Empuja todo hacia arriba
        
        # 2. ÁREA DE CONTENIDO (Derecha)
        contenido = QWidget()
        layout_contenido = QVBoxLayout(contenido)
        
        # Títulos
        h1 = QLabel("CATEGORÍAS")
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: #34495e;")
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        h2 = QLabel("Registro de Categorías")
        h2.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Barra de búsqueda y botón agregar
        barra_herramientas = QHBoxLayout()
        self.btn_agregar = QPushButton("+ Agregar categoría")
        self.btn_agregar.clicked.connect(self.abrir_modal_agregar)
        
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar por nombre...")
        self.input_buscar.textChanged.connect(self.cargar_datos) # Busca mientras escribes
        
        barra_herramientas.addWidget(self.btn_agregar)
        barra_herramientas.addStretch()
        barra_herramientas.addWidget(self.input_buscar)
        
        # TABLA
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nro.", "Nombre de Categoría", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().hide() # Esto quita los números del costado
        
        # Paginación
        layout_paginacion = QHBoxLayout()
        self.btn_prev = QPushButton("Anterior")
        self.btn_next = QPushButton("Siguiente")
        self.lbl_pagina = QLabel("Página 1")
        
        self.btn_prev.clicked.connect(self.pagina_anterior)
        self.btn_next.clicked.connect(self.pagina_siguiente)
        
        layout_paginacion.addStretch()
        layout_paginacion.addWidget(self.btn_prev)
        layout_paginacion.addWidget(self.lbl_pagina)
        layout_paginacion.addWidget(self.btn_next)
        layout_paginacion.addStretch()

        # Agregar todo al layout de contenido
        layout_contenido.addWidget(h1)
        layout_contenido.addWidget(h2)
        layout_contenido.addLayout(barra_herramientas)
        layout_contenido.addWidget(self.tabla)
        layout_contenido.addLayout(layout_paginacion)
        
        # Juntar Menú + Contenido
        layout_principal.addWidget(menu_lateral)
        layout_principal.addWidget(contenido)

    # --- LÓGICA DE BASE DE DATOS ---

    def cargar_datos(self):
        busqueda = self.input_buscar.text()
        offset = self.pagina_actual * self.limite
        
        conexion = database.crear_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("""
            SELECT id, nombre FROM categorias 
            WHERE nombre LIKE ? 
            LIMIT ? OFFSET ?
        """, (f'%{busqueda}%', self.limite, offset))
        
        filas = cursor.fetchall()
        self.tabla.setRowCount(0)
        
        for i, fila in enumerate(filas):
            idx_fila = self.tabla.rowCount()
            self.tabla.insertRow(idx_fila)
            
            # 1. Celda del Número (Centrada)
            item_numero = QTableWidgetItem(str(offset + i + 1))
            item_numero.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # <--- Centrado
            self.tabla.setItem(idx_fila, 0, item_numero)
            
            # 2. Celda del Nombre (Centrada)
            item_nombre = QTableWidgetItem(fila[1])
            item_nombre.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # <--- Centrado
            self.tabla.setItem(idx_fila, 1, item_nombre)
            
            # 3. BOTONES DE ACCIÓN
            contenedor_botones = QWidget()
            # Usamos un layout horizontal para los botones y los centramos
            layout_btns = QHBoxLayout(contenedor_botones)
            layout_btns.setContentsMargins(5, 2, 5, 2)
            layout_btns.setSpacing(10)
            layout_btns.setAlignment(Qt.AlignmentFlag.AlignCenter) # <--- Centra los botones
            
            btn_edit = QPushButton("Editar")
            btn_edit.setFixedWidth(80) # Tamaño fijo para que se vean uniformes
            btn_edit.clicked.connect(lambda _, f=fila: self.abrir_modal_editar(f))
            
            btn_delete = QPushButton("Eliminar")
            btn_delete.setFixedWidth(80)
            btn_delete.setStyleSheet("background-color: #c0392b; color: white;")
            btn_delete.clicked.connect(lambda _, id=fila[0]: self.eliminar_categoria(id))
            
            layout_btns.addWidget(btn_edit)
            layout_btns.addWidget(btn_delete)
            self.tabla.setCellWidget(idx_fila, 2, contenedor_botones)
            
        conexion.close()
        self.lbl_pagina.setText(f"Página {self.pagina_actual + 1}")

    def abrir_modal_agregar(self):
        modal = FormularioCategoria()
        if modal.exec():
            nombre = modal.input_nombre.text().strip()
            if nombre:
                try:
                    conn = database.crear_conexion()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
                    conn.commit()
                    conn.close()
                    self.cargar_datos()
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "Error", "Esa categoría ya existe.")

    def abrir_modal_editar(self, datos_categoria):
        # datos_categoria es (id, nombre)
        modal = FormularioCategoria("Editar Categoría", datos_categoria[1])
        if modal.exec():
            nuevo_nombre = modal.input_nombre.text().strip()
            if nuevo_nombre:
                conn = database.crear_conexion()
                cursor = conn.cursor()
                cursor.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nuevo_nombre, datos_categoria[0]))
                conn.commit()
                conn.close()
                self.cargar_datos()

    def eliminar_categoria(self, cat_id):
        pregunta = QMessageBox.question(self, "Confirmar", "¿Deseas eliminar esta categoría?", 
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if pregunta == QMessageBox.StandardButton.Yes:
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
            conn.commit()
            conn.close()
            self.cargar_datos()

    def pagina_anterior(self):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.cargar_datos()

    def pagina_siguiente(self):
        # Aquí podrías contar el total de filas para saber si hay más, 
        # pero por ahora simplemente avanzamos.
        self.pagina_actual += 1
        self.cargar_datos()

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    database.inicializar_db() # Crea la tabla si no existe
    app = QApplication(sys.argv)
    ventana = VentanaCategorias()
    ventana.show()
    sys.exit(app.exec())
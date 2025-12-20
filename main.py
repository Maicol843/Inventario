import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFrame, QFormLayout, QComboBox, QStackedWidget, QDialog
)
from PyQt6.QtCore import Qt
import database

# --- VENTANA MODAL PARA CATEGORÍAS ---
class FormularioCategoria(QDialog):
    def __init__(self, titulo="Agregar Categoría", nombre_actual=""):
        super().__init__()
        self.setWindowTitle(titulo)
        self.setFixedSize(300, 150)
        layout = QFormLayout(self)
        
        self.input_nombre = QLineEdit(self)
        self.input_nombre.setText(nombre_actual)
        self.input_nombre.setPlaceholderText("Nombre de la categoría")
        
        layout.addRow("Nombre:", self.input_nombre)
        
        botones = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar")
        self.btn_cancelar = QPushButton("Cancelar")
        botones.addWidget(self.btn_guardar)
        botones.addWidget(self.btn_cancelar)
        layout.addRow(botones)
        
        self.btn_guardar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)

# --- MÓDULO DE CATEGORÍAS ---
class ModuloCategorias(QWidget):
    def __init__(self):
        super().__init__()
        self.limite = 10
        self.pagina_actual = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        h1 = QLabel("CATEGORÍAS")
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: #34495e;")
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        h2 = QLabel("Registro de Categorías")
        h2.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(h1)
        layout.addWidget(h2)

        # Barra superior: Botón y Buscador
        top_layout = QHBoxLayout()
        self.btn_nueva = QPushButton("+ Agregar Categoría")
        self.btn_nueva.setStyleSheet("background-color: #6610f2; color: white; padding: 8px;")
        self.btn_nueva.clicked.connect(self.abrir_modal_agregar)
        
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("🔍 Buscar categoría...")
        self.input_buscar.textChanged.connect(self.cargar_datos)
        
        top_layout.addWidget(self.btn_nueva)
        top_layout.addStretch()
        top_layout.addWidget(self.input_buscar)
        layout.addLayout(top_layout)

        # Tabla configurada
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nro.", "Nombre de Categoría", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().hide() # Quitar números laterales
        layout.addWidget(self.tabla)

        # Paginación
        pag_layout = QHBoxLayout()
        self.btn_atras = QPushButton("Anterior")
        self.btn_siguiente = QPushButton("Siguiente")
        self.lbl_pagina = QLabel("Página 1")
        
        self.btn_atras.clicked.connect(self.pagina_anterior)
        self.btn_siguiente.clicked.connect(self.pagina_siguiente)
        
        pag_layout.addStretch()
        pag_layout.addWidget(self.btn_atras)
        pag_layout.addWidget(self.lbl_pagina)
        pag_layout.addWidget(self.btn_siguiente)
        pag_layout.addStretch()
        layout.addLayout(pag_layout)

        self.cargar_datos()

    def abrir_modal_agregar(self):
        modal = FormularioCategoria("Nueva Categoría")
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
                except Exception as e:
                    QMessageBox.warning(self, "Error", "La categoría ya existe o hubo un error.")

    def cargar_datos(self):
        busqueda = self.input_buscar.text()
        offset = self.pagina_actual * self.limite
        conexion = database.crear_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre FROM categorias WHERE nombre LIKE ? LIMIT ? OFFSET ?", 
                       (f'%{busqueda}%', self.limite, offset))
        filas = cursor.fetchall()
        
        self.tabla.setRowCount(0)
        for i, fila in enumerate(filas):
            idx = self.tabla.rowCount()
            self.tabla.insertRow(idx)
            
            # Datos centrados
            item_nro = QTableWidgetItem(str(offset + i + 1))
            item_nro.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_nombre = QTableWidgetItem(fila[1])
            item_nombre.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.tabla.setItem(idx, 0, item_nro)
            self.tabla.setItem(idx, 1, item_nombre)
            
            # Botones de acción
            btns_widget = QWidget()
            btns_layout = QHBoxLayout(btns_widget)
            btns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btns_layout.setContentsMargins(0,0,0,0)
            
            btn_edit = QPushButton("Editar")
            btn_edit.clicked.connect(lambda _, f=fila: self.abrir_modal_editar(f))
            
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #c0392b; color: white;")
            btn_del.clicked.connect(lambda _, id=fila[0]: self.eliminar_categoria(id))
            
            btns_layout.addWidget(btn_edit)
            btns_layout.addWidget(btn_del)
            self.tabla.setCellWidget(idx, 2, btns_widget)
        
        conexion.close()
        self.lbl_pagina.setText(f"Página {self.pagina_actual + 1}")

    def abrir_modal_editar(self, fila):
        modal = FormularioCategoria("Editar Categoría", fila[1])
        if modal.exec():
            nuevo_nombre = modal.input_nombre.text().strip()
            if nuevo_nombre:
                conn = database.crear_conexion()
                cursor = conn.cursor()
                cursor.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nuevo_nombre, fila[0]))
                conn.commit()
                conn.close()
                self.cargar_datos()

    def eliminar_categoria(self, cat_id):
        confirm = QMessageBox.question(self, "Eliminar", "¿Seguro?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
            conn.commit()
            conn.close()
            self.cargar_datos()

    def pagina_siguiente(self):
        self.pagina_actual += 1
        self.cargar_datos()

    def pagina_anterior(self):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.cargar_datos()

# --- MÓDULO DE PRODUCTOS ---
class ModuloProductos(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        h1 = QLabel("PRODUCTOS")
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: #34495e;")
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        h2 = QLabel("Registro de Productos")
        h2.setStyleSheet("font-size: 18px; color: #7f8c8d; margin-bottom: 20px;")
        h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        form_frame = QFrame()
        form_frame.setMaximumWidth(500)
        form_layout = QFormLayout(form_frame)

        self.input_codigo = QLineEdit()
        self.input_nombre = QLineEdit()
        self.combo_categoria = QComboBox()
        self.input_proveedor = QLineEdit()
        
        form_layout.addRow("Código/Número:", self.input_codigo)
        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Categoría:", self.combo_categoria)
        form_layout.addRow("Proveedor:", self.input_proveedor)
        
        self.btn_registrar = QPushButton("Registrar")
        self.btn_registrar.setStyleSheet("background-color: #20c997; color: black; padding: 10px;")
        self.btn_registrar.clicked.connect(self.registrar_producto)

        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_frame)
        center_layout.addStretch()

        layout.addWidget(h1)
        layout.addWidget(h2)
        layout.addLayout(center_layout)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def actualizar_combobox(self):
        self.combo_categoria.clear()
        conn = database.crear_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias")
        for id_c, nom in cursor.fetchall():
            self.combo_categoria.addItem(nom, id_c)
        conn.close()

    def registrar_producto(self):
        cod = self.input_codigo.text().strip()
        nom = self.input_nombre.text().strip()
        prov = self.input_proveedor.text().strip()
        id_cat = self.combo_categoria.currentData()

        if cod and nom and id_cat:
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO productos (codigo, nombre, id_categoria, proveedor) VALUES (?,?,?,?)", 
                           (cod, nom, id_cat, prov))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", "Producto registrado exitosamente")
            self.input_codigo.clear()
            self.input_nombre.clear()
            self.input_proveedor.clear()
        else:
            QMessageBox.warning(self, "Error", "Completa todos los campos")

# --- VENTANA PRINCIPAL ---
class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Inventario")
        self.resize(1100, 700)
        database.inicializar_db()
        
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0,0,0,0)
        layout_principal.setSpacing(0)

        # --- NAVEGADOR IZQUIERDO (SIDEBAR) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        # Fondo oscuro y borde a la derecha para separar
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-right: 1px solid #1a252f;
            }
        """)
        
        # Usamos QVBoxLayout para el menú
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(10, 20, 10, 20)
        layout_sidebar.setSpacing(5) # <--- Aquí controlamos que estén más juntos

        # Título del Menú
        lbl_menu = QLabel("MENU PRINCIPAL")
        lbl_menu.setStyleSheet("color: #95a5a6; font-size: 11px; font-weight: bold; margin-bottom: 5px;")
        lbl_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sidebar.addWidget(lbl_menu)

        # Botones con ICONOS (Emojis)
        self.btn_cat = QPushButton("  📁  Categorías")
        self.btn_prod = QPushButton("  📦  Productos")
        
        # Estilo de botones: Más compactos y con efecto hover
        estilo_botones = """
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                text-align: left;
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """
        self.btn_cat.setStyleSheet(estilo_botones)
        self.btn_prod.setStyleSheet(estilo_botones)

        # Añadir al layout
        layout_sidebar.addWidget(self.btn_cat)
        layout_sidebar.addWidget(self.btn_prod)
        
        # Espacio flexible al final para empujar todo hacia arriba
        layout_sidebar.addStretch()

        # --- CONTENEDOR DE PÁGINAS ---
        self.paginas = QStackedWidget()
        self.mod_cat = ModuloCategorias()
        self.mod_prod = ModuloProductos()
        self.paginas.addWidget(self.mod_cat)
        self.paginas.addWidget(self.mod_prod)

        # Conexiones de botones
        self.btn_cat.clicked.connect(lambda: self.paginas.setCurrentIndex(0))
        self.btn_prod.clicked.connect(self.ir_a_productos)

        # Unir todo
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.paginas)

    def ir_a_productos(self):
        self.mod_prod.actualizar_combobox()
        self.paginas.setCurrentIndex(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
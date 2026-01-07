import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QFormLayout, QComboBox, QStackedWidget,
    QDialog, QDateEdit, QFileDialog 
)
from PyQt6.QtWidgets import QDateEdit 
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QDate
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from fpdf import FPDF
from datetime import datetime
import database

try:
    from fpdf import FPDF
    FPDF_INSTALADO = True
except ImportError:
    FPDF_INSTALADO = False

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
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
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
            btn_edit.setStyleSheet("background-color: #0d6efd; color: white;")
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
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
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
        
        self.btn_registrar = QPushButton("Registrar Producto")
        self.btn_registrar.setStyleSheet("background-color: #6610f2; color: white; padding: 10px;")
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


# --- MÓDULO DE MOVIMIENTOS ---
class ModuloMovimientos(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Títulos
        h1 = QLabel("MOVIMIENTOS")
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        h2 = QLabel("MOVIMIENTOS")
        h2.setStyleSheet("font-size: 18px; color: #7f8c8d; margin-bottom: 20px;")
        h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Formulario
        form_frame = QFrame()
        form_frame.setMaximumWidth(550)
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)

        self.combo_producto = QComboBox()
        self.input_fecha = QDateEdit()
        self.input_fecha.setCalendarPopup(True) # Para que salga un calendario al hacer clic
        self.input_fecha.setDate(QDate.currentDate()) # Fecha de hoy por defecto
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Compra", "Venta"])
        
        self.input_precio = QLineEdit()
        self.input_precio.setPlaceholderText("0.00")
        
        self.input_cantidad = QLineEdit()
        self.input_cantidad.setPlaceholderText("Solo números enteros")
        
        self.input_obs = QLineEdit()
        self.input_obs.setPlaceholderText("Opcional...")
        
        form_layout.addRow("Seleccionar Producto:", self.combo_producto)
        form_layout.addRow("Fecha:", self.input_fecha)
        form_layout.addRow("Tipo de Movimiento:", self.combo_tipo)
        form_layout.addRow("Precio:", self.input_precio)
        form_layout.addRow("Cantidad:", self.input_cantidad)
        form_layout.addRow("Observaciones:", self.input_obs)
        
        self.btn_registrar = QPushButton("Registrar Movimiento")
        self.btn_registrar.setStyleSheet("background-color: #6610f2; color: white; padding: 12px; border-radius: 5px;")
        self.btn_registrar.clicked.connect(self.registrar_movimiento)

        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_frame)
        center_layout.addStretch()

        layout.addWidget(h1)
        layout.addWidget(h2)
        layout.addLayout(center_layout)
        layout.addWidget(self.btn_registrar, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def actualizar_productos_combobox(self):
        self.combo_producto.clear()
        conn = database.crear_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM productos")
        for id_p, nom in cursor.fetchall():
            self.combo_producto.addItem(nom, id_p)
        conn.close()

    def registrar_movimiento(self):
        id_prod = self.combo_producto.currentData()
        fecha = self.input_fecha.date().toString("yyyy-MM-dd")
        tipo = self.combo_tipo.currentText()
        precio = self.input_precio.text()
        cant = self.input_cantidad.text()
        obs = self.input_obs.text()

        if not id_prod or not precio or not cant:
            QMessageBox.warning(self, "Error", "Por favor completa los campos de Precio y Cantidad.")
            return

        try:
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO movimientos (id_producto, fecha, tipo, precio, cantidad, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (id_prod, fecha, tipo, float(precio), int(cant), obs))
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Éxito", "El movimiento se registró exitosamente")
            
            # Limpiar campos tras éxito
            self.input_precio.clear()
            self.input_cantidad.clear()
            self.input_obs.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")

# --- MODULO DE INVENTARIO ---
class ModuloInventario(QWidget):
    def __init__(self):
        super().__init__()
        self.limite = 10
        self.pagina_actual = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        h1 = QLabel("INVENTARIO")
        h1.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        h1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(h1)

        h2 = QLabel("Control de Existencias")
        h2.setStyleSheet("font-size: 18px; color: #7f8c8d; margin-bottom: 10px;")
        h2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(h2)

        # Filtros: Buscador (Ahora incluye proveedor) y Select de Stock
        filtros_layout = QHBoxLayout()
        
        self.input_buscar = QLineEdit()
        # Se actualiza el texto de ayuda
        self.input_buscar.setPlaceholderText("🔍 Buscar por Código, Producto, Categoría o Proveedor...")
        self.input_buscar.textChanged.connect(self.cargar_datos)
        
        self.combo_filtro_stock = QComboBox()
        self.combo_filtro_stock.addItems(["Todos los niveles", "Normal", "Stock Bajo", "Sin Stock"])
        self.combo_filtro_stock.currentTextChanged.connect(self.cargar_datos)
        
        filtros_layout.addWidget(self.input_buscar, 4)
        filtros_layout.addWidget(self.combo_filtro_stock, 1)
        layout.addLayout(filtros_layout)

        # Tabla: AHORA CON 8 COLUMNAS (Se agregó Proveedor)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Proveedor", "Stock Actual", "Stock Mínimo", "Estado", "Acciones"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().hide()
        layout.addWidget(self.tabla)

        # Footer: Restablecer y Paginación
        footer_layout = QHBoxLayout()
        
        self.btn_restablecer = QPushButton("🗑️ Restablecer Todo")
        self.btn_restablecer.setStyleSheet("background-color: #7f8c8d; color: white; padding: 8px 15px; font-weight: bold;")
        self.btn_restablecer.clicked.connect(self.restablecer_tabla)
        
        self.btn_atras = QPushButton("Anterior")
        self.btn_siguiente = QPushButton("Siguiente")
        self.lbl_pagina = QLabel("Página 1")
        
        self.btn_atras.clicked.connect(self.pagina_anterior)
        self.btn_siguiente.clicked.connect(self.pagina_siguiente)

        footer_layout.addWidget(self.btn_restablecer)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_atras)
        footer_layout.addWidget(self.lbl_pagina)
        footer_layout.addWidget(self.btn_siguiente)
        footer_layout.addStretch()
        layout.addLayout(footer_layout)

    def cargar_datos(self):
        busqueda = self.input_buscar.text()
        filtro_stock = self.combo_filtro_stock.currentText()
        offset = self.pagina_actual * self.limite
        
        conn = database.crear_conexion()
        cursor = conn.cursor()
        
        # QUERY MODIFICADA: Se añade "OR p.proveedor LIKE ?"
        query = """
            SELECT 
                p.codigo, 
                p.nombre, 
                c.nombre as categoria,
                p.id,
                COALESCE(SUM(CASE WHEN m.tipo = 'Compra' THEN m.cantidad ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN m.tipo = 'Venta' THEN m.cantidad ELSE 0 END), 0) as stock_actual,
                p.proveedor
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id
            LEFT JOIN movimientos m ON p.id = m.id_producto
            WHERE (p.codigo LIKE ? OR p.nombre LIKE ? OR categoria LIKE ? OR p.proveedor LIKE ?)
            GROUP BY p.id
        """
        
        # Pasamos el parámetro 4 veces (código, nombre, categoría, proveedor)
        cursor.execute(query, (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'))
        todos = cursor.fetchall()
        
        # Lógica de filtrado por niveles de stock
        filtrados = []
        for p in todos:
            stock = p[4]
            if filtro_stock == "Normal" and not (stock > 10): continue
            if filtro_stock == "Stock Bajo" and not (0 < stock <= 10): continue
            if filtro_stock == "Sin Stock" and stock != 0: continue
            filtrados.append(p)

        self.tabla.setRowCount(0)
        
        for fila in filtrados[offset : offset + self.limite]:
            idx = self.tabla.rowCount()
            self.tabla.insertRow(idx)
            
            stock_actual = fila[4]
            stock_minimo = 10
            
            # Definir estado y colores
            if stock_actual > 10:
                estado, color, texto_color = "Normal", "#198754", "white" 
            elif 0 < stock_actual <= 10:
                estado, color, texto_color = "Stock Bajo", "#ffc107", "black" 
            else:
                estado, color, texto_color = "Sin Stock", "#dc3545", "white" 

            # Lista de items actualizada con Proveedor en la columna 3 (índice 3)
            items = [
                QTableWidgetItem(str(fila[0])), # Código
                QTableWidgetItem(str(fila[1])), # Producto
                QTableWidgetItem(str(fila[2])), # Categoría
                QTableWidgetItem(str(fila[5] if fila[5] else "Sin Proveedor")), # Proveedor
                QTableWidgetItem(str(stock_actual)),
                QTableWidgetItem(str(stock_minimo)),
                QTableWidgetItem(estado)
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QColor(color))
                item.setForeground(QColor(texto_color))
                self.tabla.setItem(idx, col, item)

            # Botones: Ahora en la columna 7
            btns_widget = QWidget()
            btns_layout = QHBoxLayout(btns_widget)
            btns_layout.setContentsMargins(0,0,0,0)
            
            btn_ver = QPushButton("Ver")
            datos_para_ver = (fila[3], fila[0], fila[1], fila[2], fila[5])
            btn_ver.clicked.connect(lambda _, d=datos_para_ver: self.ir_a_ver_producto(d))

            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #dc3545; color: white;")
            btn_del.clicked.connect(lambda _, id_p=fila[3]: self.eliminar_producto(id_p))
            
            btns_layout.addWidget(btn_ver)
            btns_layout.addWidget(btn_del)
            self.tabla.setCellWidget(idx, 7, btns_widget)

        conn.close()
        self.lbl_pagina.setText(f"Página {self.pagina_actual + 1}")

    def ir_a_ver_producto(self, d):
        ventana = self.window()
        # d[0]=id, d[1]=cod, d[2]=nom, d[3]=cat, d[4]=prov
        ventana.mod_ver_prod.mostrar_datos(d[0], d[1], d[2], d[3], d[4])
        ventana.paginas.setCurrentWidget(ventana.mod_ver_prod)

    def eliminar_producto(self, id_p):
        rta = QMessageBox.question(self, "Eliminar", "¿Eliminar producto y sus movimientos?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rta == QMessageBox.StandardButton.Yes:
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movimientos WHERE id_producto = ?", (id_p,))
            cursor.execute("DELETE FROM productos WHERE id = ?", (id_p,))
            conn.commit()
            conn.close()
            self.cargar_datos()

    def restablecer_tabla(self):
        rta = QMessageBox.warning(self, "¡CUIDADO!", "¿Borrar absolutamente TODOS los datos?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rta == QMessageBox.StandardButton.Yes:
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM movimientos")
            cursor.execute("DELETE FROM productos")
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

# --- VENTANA MODAL PARA EDITAR MOVIMIENTO ---
class FormularioEditarMovimiento(QDialog):
    def __init__(self, datos):
        super().__init__()
        self.setWindowTitle("Editar Movimiento")
        self.setFixedSize(350, 300)
        layout = QFormLayout(self)

        self.input_fecha = QDateEdit(self)
        self.input_fecha.setCalendarPopup(True)
        # Convertimos de AAAA-MM-DD a objeto QDate
        fecha_obj = QDate.fromString(datos['fecha'], "yyyy-MM-dd")
        self.input_fecha.setDate(fecha_obj)
        self.input_fecha.setDisplayFormat("dd/MM/yyyy")
        
        self.combo_tipo = QComboBox(self)
        self.combo_tipo.addItems(["Compra", "Venta"])
        self.combo_tipo.setCurrentText(datos['tipo'])

        self.input_precio = QLineEdit(self)
        self.input_precio.setText(str(datos['precio']))

        self.input_cantidad = QLineEdit(self)
        self.input_cantidad.setText(str(datos['cantidad']))

        self.input_obs = QLineEdit(self)
        self.input_obs.setText(datos['obs'])

        layout.addRow("Fecha:", self.input_fecha)
        layout.addRow("Tipo:", self.combo_tipo)
        layout.addRow("Precio:", self.input_precio)
        layout.addRow("Cantidad:", self.input_cantidad)
        layout.addRow("Obs:", self.input_obs)

        self.btn_guardar = QPushButton("Actualizar Datos")
        self.btn_guardar.setStyleSheet("background-color: #198754; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        layout.addRow(self.btn_guardar)
        self.btn_guardar.clicked.connect(self.accept)

# --- MÓDULO VER PRODUCTO ---
class ModuloVerProducto(QWidget):
    def __init__(self):
        super().__init__()
        self.id_producto_actual = None
        self.pagina_actual = 0
        self.limite = 10
        self.init_ui()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(30, 20, 30, 20)
        self.layout_principal.setSpacing(15)

        # 1. TÍTULO CENTRADO
        self.lbl_nombre = QLabel("DETALLE DEL PRODUCTO")
        self.lbl_nombre.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        self.lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.lbl_nombre)

        # 2. DATOS TÉCNICOS (Izquierda)
        self.detalles_frame = QFrame()
        layout_detalles = QFormLayout(self.detalles_frame)
        estilo_tit = "font-size: 14px; color: #7f8c8d;"
        estilo_val = "font-size: 15px; color: white; font-weight: bold;"
        
        self.lbl_codigo = QLabel("-"); self.lbl_codigo.setStyleSheet(estilo_val)
        self.lbl_categoria = QLabel("-"); self.lbl_categoria.setStyleSheet(estilo_val)
        self.lbl_proveedor = QLabel("-"); self.lbl_proveedor.setStyleSheet(estilo_val)

        layout_detalles.addRow(self.crear_lbl("Código:", estilo_tit), self.lbl_codigo)
        layout_detalles.addRow(self.crear_lbl("Categoría:", estilo_tit), self.lbl_categoria)
        layout_detalles.addRow(self.crear_lbl("Proveedor:", estilo_tit), self.lbl_proveedor)
        self.layout_principal.addWidget(self.detalles_frame)

        # 3. SECCIÓN DE 5 CARDS CENTRADAS
        container_cards = QWidget()
        layout_cards = QHBoxLayout(container_cards)
        layout_cards.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.card_compras = self.crear_card("TOTAL COMPRAS")
        self.card_ventas = self.crear_card("TOTAL VENTAS")
        self.card_ganancia = self.crear_card("GANANCIAS")
        self.card_stock = self.crear_card("STOCK ACTUAL")
        self.card_estado = self.crear_card("ESTADO")

        for c in [self.card_compras, self.card_ventas, self.card_ganancia, self.card_stock, self.card_estado]:
            layout_cards.addWidget(c)
        self.layout_principal.addWidget(container_cards)

        # 4. FILTROS
        frame_filtros = QFrame()
        lay_f = QHBoxLayout(frame_filtros)
        
        self.f_fecha = QLineEdit()
        self.f_fecha.setPlaceholderText("Buscar fecha (DD/MM/AAAA)")
        self.f_fecha.textChanged.connect(self.reset_paginar)
        
        self.f_tipo = QComboBox()
        self.f_tipo.addItems(["Todos", "Compra", "Venta"])
        self.f_tipo.currentTextChanged.connect(self.reset_paginar)

        lay_f.addWidget(QLabel("Fecha:")); lay_f.addWidget(self.f_fecha)
        lay_f.addWidget(QLabel("Tipo:")); lay_f.addWidget(self.f_tipo)
        self.layout_principal.addWidget(frame_filtros)

        # 5. TABLA DE MOVIMIENTOS
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6) # Fecha, Tipo, Precio, Cant, Obs, Acciones
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Tipo", "Precio", "Cantidad", "Observaciones", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.tabla)

        # 6. PAGINACIÓN
        lay_pag = QHBoxLayout()
        self.btn_ant = QPushButton("Anterior")
        self.btn_sig = QPushButton("Siguiente")
        self.lbl_pag = QLabel("Página 1")
        lay_pag.addStretch(); lay_pag.addWidget(self.btn_ant); lay_pag.addWidget(self.lbl_pag); lay_pag.addWidget(self.btn_sig); lay_pag.addStretch()
        self.layout_principal.addLayout(lay_pag)
        
        self.btn_ant.clicked.connect(self.pagina_anterior)
        self.btn_sig.clicked.connect(self.pagina_siguiente)

        layout_botones_final = QHBoxLayout()
        # BOTÓN VOLVER
        self.btn_volver = QPushButton("← Volver al Inventario")
        self.btn_volver.setFixedWidth(200)
        self.btn_volver.setStyleSheet("background-color: #6610f2; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")

        # BOTON GRAFICA DE COMPRAS
        self.btn_ver_grafica = QPushButton("📊 Gráfica de Compras")
        self.btn_ver_grafica.setFixedWidth(200)
        self.btn_ver_grafica.setStyleSheet("background-color: #6610f2; color: white; padding: 10px; border-radius: 5px;")

        # BOTÓN GRAFICA DE VENTAS
        self.btn_grafica_ventas = QPushButton("📊 Gráfica de Ventas")
        self.btn_grafica_ventas.setFixedWidth(200)
        self.btn_grafica_ventas.setStyleSheet("background-color: #6610f2; color: white; padding: 10px; border-radius: 5px;")

        layout_botones_final.addStretch()
        layout_botones_final.addWidget(self.btn_volver)
        layout_botones_final.addWidget(self.btn_ver_grafica)
        layout_botones_final.addWidget(self.btn_grafica_ventas)
        layout_botones_final.addStretch()
    
        self.layout_principal.addLayout(layout_botones_final)

    def crear_lbl(self, t, e):
        l = QLabel(t); l.setStyleSheet(e); return l

    def crear_card(self, titulo):
        card = QFrame()
        card.setFixedSize(165, 100)
        card.setStyleSheet("background-color: #fdfdfd; border-radius: 10px;")
        lay = QVBoxLayout(card)
        t = QLabel(titulo); t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size: 12px; color: black; font-weight: bold;")
        t.setTextFormat(Qt.TextFormat.RichText)
        v = QLabel("0"); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setStyleSheet("font-size: 18px; color: #2c3e50; font-weight: bold;")
        lay.addWidget(t); lay.addWidget(v)
        card.lbl_tit = t; card.lbl_val = v
        return card

    def mostrar_datos(self, id_p, cod, nom, cat, prov):
        self.id_producto_actual = id_p
        self.lbl_codigo.setText(str(cod))
        self.lbl_nombre.setText(str(nom).upper())
        self.lbl_categoria.setText(str(cat))
        self.lbl_proveedor.setText(str(prov) if prov else "N/A")
        self.reset_paginar()

    def reset_paginar(self):
        self.pagina_actual = 0
        self.actualizar_todo()

    def actualizar_todo(self):
        self.actualizar_estadisticas()
        self.cargar_tabla()

    def actualizar_estadisticas(self):
        conn = database.crear_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(precio) FROM movimientos WHERE id_producto=? AND tipo='Compra'", (self.id_producto_actual,))
        t_c = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(cantidad * precio) FROM movimientos WHERE id_producto=? AND tipo='Venta'", (self.id_producto_actual,))
        t_v = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(CASE WHEN tipo='Compra' THEN cantidad ELSE -cantidad END) FROM movimientos WHERE id_producto=?", (self.id_producto_actual,))
        stk = cursor.fetchone()[0] or 0
        conn.close()

        ganancia = t_v - t_c
        porc = (ganancia / t_c * 100) if t_c > 0 else 0
        col = "#198754" if ganancia >= 0 else "#dc3545"
        fle = "↑" if ganancia >= 0 else "↓"

        self.card_ganancia.lbl_tit.setText(f"GANANCIAS <span style='color: {col};'>({fle} {abs(porc):.1f}%)</span>")
        self.card_ganancia.lbl_val.setText(f"$ {abs(ganancia):,.2f}")
        self.card_compras.lbl_val.setText(f"$ {t_c:,.2f}")
        self.card_ventas.lbl_val.setText(f"$ {t_v:,.2f}")
        self.card_stock.lbl_val.setText(str(stk))
        
        c_stk = "#198754" if stk > 10 else "#ffc107" if stk > 0 else "#dc3545"
        e_stk = "NORMAL" if stk > 10 else "BAJO" if stk > 0 else "SIN STOCK"
        self.card_estado.setStyleSheet(f"background-color: {c_stk}; border-radius: 10px;")
        self.card_estado.lbl_val.setText(e_stk); self.card_estado.lbl_val.setStyleSheet("color: white; font-weight: bold;")

    def cargar_tabla(self):
        conn = database.crear_conexion()
        cursor = conn.cursor()
        
        filtro_crudo = self.f_fecha.text()
        f_sql = f"%{filtro_crudo}%"
        if len(filtro_crudo) == 10 and "/" in filtro_crudo:
            try:
                partes = filtro_crudo.split("/")
                f_sql = f"{partes[2]}-{partes[1]}-{partes[0]}"
            except: pass

        f_t = self.f_tipo.currentText()
        query = "SELECT fecha, tipo, precio, cantidad, observaciones, id FROM movimientos WHERE id_producto = ? AND fecha LIKE ?"
        params = [self.id_producto_actual, f_sql]
        if f_t != "Todos":
            query += " AND tipo = ?"
            params.append(f_t)
        
        query += f" ORDER BY fecha DESC LIMIT {self.limite} OFFSET {self.pagina_actual * self.limite}"
        cursor.execute(query, params)
        movs = cursor.fetchall()
        conn.close()

        self.tabla.setRowCount(0)
        for m in movs:
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            
            # Formatear fecha
            try:
                f_obj = QDate.fromString(m[0], "yyyy-MM-dd")
                fecha_tabla = f_obj.toString("dd/MM/yyyy")
            except: fecha_tabla = m[0]

            datos_fila = [fecha_tabla, m[1], f"$ {m[2]:,.2f}", m[3], m[4]]
            
            for i, valor in enumerate(datos_fila):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(r, i, item)
            
            # --- CELDA DE ACCIONES (Botones Juntos) ---
            widget_acciones = QWidget()
            layout_acc = QHBoxLayout(widget_acciones)
            layout_acc.setContentsMargins(5, 2, 5, 2)
            layout_acc.setSpacing(10)
            layout_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("Editar")
            btn_edit.setFixedSize(65, 25)
            btn_edit.setStyleSheet("background-color: #0d6efd; color: white; font-size: 11px; border-radius: 3px;")
            btn_edit.clicked.connect(lambda _, d=m: self.editar_mov(d))

            btn_del = QPushButton("Eliminar")
            btn_del.setFixedSize(65, 25)
            btn_del.setStyleSheet("background-color: #dc3545; color: white; font-size: 11px; border-radius: 3px;")
            btn_del.clicked.connect(lambda _, id_m=m[5]: self.eliminar_mov(id_m))

            layout_acc.addWidget(btn_edit)
            layout_acc.addWidget(btn_del)
            
            self.tabla.setCellWidget(r, 5, widget_acciones)
        
        self.lbl_pag.setText(f"Página {self.pagina_actual + 1}")

    def editar_mov(self, m):
        d = {'fecha': m[0], 'tipo': m[1], 'precio': m[2], 'cantidad': m[3], 'obs': m[4]}
        f = FormularioEditarMovimiento(d)
        if f.exec():
            conn = database.crear_conexion()
            cursor = conn.cursor()
            cursor.execute("UPDATE movimientos SET fecha=?, tipo=?, precio=?, cantidad=?, observaciones=? WHERE id=?",
                (f.input_fecha.date().toString("yyyy-MM-dd"), f.combo_tipo.currentText(), f.input_precio.text(), f.input_cantidad.text(), f.input_obs.text(), m[5]))
            conn.commit(); conn.close()
            self.actualizar_todo()

    def eliminar_mov(self, id_m):
        if QMessageBox.question(self, "Eliminar", "¿Borrar este registro?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            conn = database.crear_conexion(); cursor = conn.cursor()
            cursor.execute("DELETE FROM movimientos WHERE id=?", (id_m,))
            conn.commit(); conn.close()
            self.actualizar_todo()

    def pagina_anterior(self):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.cargar_tabla()

    def pagina_siguiente(self):
        self.pagina_actual += 1
        self.cargar_tabla()

class ModuloGraficaCompras(QWidget):
    def __init__(self):
        super().__init__()
        self.id_producto_actual = None
        self.init_ui()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(50, 30, 50, 30)
        self.layout_principal.setSpacing(20)

        # Título centrado profesional
        self.lbl_titulo = QLabel("COMPRAS")
        self.lbl_titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.lbl_titulo)

        # Contenedor de la gráfica - Aumentamos un poco el tamaño
        self.fig, self.ax = plt.subplots(figsize=(9, 5)) 
        self.canvas = FigureCanvas(self.fig)
        self.layout_principal.addWidget(self.canvas)

        # Botón Volver estilizado
        self.btn_volver_detalle = QPushButton("← Volver al Detalle")
        self.btn_volver_detalle.setFixedWidth(220)
        self.btn_volver_detalle.setStyleSheet("""
            background-color: #6610f2; color: white; padding: 12px; 
            font-weight: bold; border-radius: 6px; font-size: 14px;
        """)
        self.layout_principal.addWidget(self.btn_volver_detalle, alignment=Qt.AlignmentFlag.AlignCenter)

    def cargar_grafica(self, id_producto, nombre_producto):
        self.id_producto_actual = id_producto
        self.lbl_titulo.setText(f"COMPRAS: {nombre_producto.upper()}")
        
        conexion = database.crear_conexion()
        cursor = conexion.cursor()
        
        # SQL: Suma total de precios por mes
        query = """
            SELECT strftime('%m', fecha) as mes, SUM(precio) 
            FROM movimientos 
            WHERE id_producto = ? AND tipo = 'Compra'
            GROUP BY mes ORDER BY mes ASC
        """
        cursor.execute(query, (id_producto,))
        datos = cursor.fetchall()
        conexion.close()

        meses_etiquetas = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        valores = [0.0] * 12
        
        for mes_str, total_precio in datos:
            try:
                indice = int(mes_str) - 1
                valores[indice] = total_precio
            except: continue

        self.ax.clear()
        
        # 1. Ajuste del límite superior para que no choque el texto
        max_valor = max(valores) if valores and max(valores) > 0 else 100
        self.ax.set_ylim(0, max_valor * 1.5) # Damos un 50% de espacio extra arriba

        # 2. Dibujo de barras
        barras = self.ax.bar(meses_etiquetas, valores, color='#27ae60', edgecolor='#1e8449', alpha=0.9)
        
        # Estética general
        self.ax.set_title("Tabla mensual de compras", fontsize=11, fontweight='bold', pad=20)
        self.ax.set_ylabel("Monto Total ($)", fontsize=10)
        self.ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        # 3. Etiquetas de dinero con mejor formato y posición
        for barra in barras:
            height = barra.get_height()
            if height > 0:
                self.ax.annotate(f'${height:,.0f}',
                    xy=(barra.get_x() + barra.get_width() / 2, height),
                    xytext=(0, 8), # 8 puntos de separación hacia arriba
                    textcoords="offset points",
                    ha='center', va='bottom', 
                    fontsize=10, 
                    fontweight='bold',
                    color='#2c3e50')

        # Ajuste final para evitar recortes en los bordes
        self.fig.tight_layout()
        self.canvas.draw()

class ModuloGraficaVentas(QWidget):
    def __init__(self):
        super().__init__()
        self.id_producto_actual = None
        self.init_ui()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(50, 30, 50, 30)
        self.layout_principal.setSpacing(20)

        # H1: Ventas del Mes (Título centrado)
        self.lbl_titulo = QLabel("VENTAS")
        self.lbl_titulo.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.lbl_titulo)

        # Contenedor de la gráfica
        self.fig, self.ax = plt.subplots(figsize=(9, 5))
        self.canvas = FigureCanvas(self.fig)
        self.layout_principal.addWidget(self.canvas)

        # Botón Volver
        self.btn_volver_detalle = QPushButton("← Volver al Detalle")
        self.btn_volver_detalle.setFixedWidth(220)
        self.btn_volver_detalle.setStyleSheet("""
            background-color: #6610f2; color: white; padding: 12px; 
            font-weight: bold; border-radius: 6px; font-size: 14px;
        """)
        self.layout_principal.addWidget(self.btn_volver_detalle, alignment=Qt.AlignmentFlag.AlignCenter)

    def cargar_grafica(self, id_producto, nombre_producto):
        self.id_producto_actual = id_producto
        self.lbl_titulo.setText(f"VENTAS: {nombre_producto.upper()}")
        
        conexion = database.crear_conexion()
        cursor = conexion.cursor()
        
        # SQL: Multiplica precio * cantidad para el total de VENTAS
        query = """
            SELECT strftime('%m', fecha) as mes, SUM(precio * cantidad) 
            FROM movimientos 
            WHERE id_producto = ? AND tipo = 'Venta'
            GROUP BY mes ORDER BY mes ASC
        """
        cursor.execute(query, (id_producto,))
        datos = cursor.fetchall()
        conexion.close()

        meses_etiquetas = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        valores = [0.0] * 12
        
        for mes_str, total_venta in datos:
            try:
                valores[int(mes_str) - 1] = total_venta
            except: continue

        self.ax.clear()
        
        # Ajuste de escala para que los números no choquen arriba
        max_valor = max(valores) if valores and max(valores) > 0 else 100
        self.ax.set_ylim(0, max_valor * 1.5)

        # Gráfica de barras (Color Azul para diferenciar de compras)
        barras = self.ax.bar(meses_etiquetas, valores, color='#3498db', edgecolor='#2980b9', alpha=0.9)
        
        self.ax.set_title("Ingresos de ventas mensuales", fontsize=11, fontweight='bold', pad=20)
        self.ax.set_ylabel("Total Ventas ($)")
        self.ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Etiquetas de dinero sobre las barras
        for barra in barras:
            height = barra.get_height()
            if height > 0:
                self.ax.annotate(f'${height:,.0f}',
                    xy=(barra.get_x() + barra.get_width() / 2, height),
                    xytext=(0, 8), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color='#2c3e50')

        self.fig.tight_layout()
        self.canvas.draw()

# --- MODULO DE REPORTES ---
class ModuloReportes(QWidget):
    def __init__(self):
        super().__init__()
        self.pagina_actual = 0
        self.limite = 10
        self.init_ui()

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(30, 20, 30, 20)
        self.layout_principal.setSpacing(15)

        # Título Centrado
        self.lbl_titulo = QLabel("REPORTES DE MOVIMIENTOS")
        self.lbl_titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: white; margin-bottom: 10px;")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.lbl_titulo)

        # --- FILTROS ---
        frame_filtros = QFrame()
        frame_filtros.setStyleSheet("background-color: black; border-radius: 10px;")
        lay_f = QHBoxLayout(frame_filtros)
        lay_f.setContentsMargins(15, 10, 15, 10)

        estilo_label = "font-weight: bold; color: #7f8c8d;"

        self.f_inicio = QDateEdit()
        self.f_inicio.setCalendarPopup(True)
        self.f_inicio.setDate(QDate.currentDate().addMonths(-1))

        self.f_fin = QDateEdit()
        self.f_fin.setCalendarPopup(True)
        self.f_fin.setDate(QDate.currentDate())

        self.f_tipo = QComboBox()
        self.f_tipo.addItems(["Todos", "Compra", "Venta"])
        self.f_tipo.setFixedWidth(100)

        # BOTÓN BUSCAR
        self.btn_buscar = QPushButton("🔍 Buscar")
        self.btn_buscar.setStyleSheet("background-color: #0d6efd; color: white; padding: 8px 15px; font-weight: bold; border-radius: 5px;")
        self.btn_buscar.clicked.connect(self.reset_paginar)

        # BOTÓN LIMPIAR 
        self.btn_limpiar = QPushButton("🧹 Limpiar")
        self.btn_limpiar.setStyleSheet("background-color: #20c997; color: white; padding: 8px 15px; font-weight: bold; border-radius: 5px;")
        self.btn_limpiar.clicked.connect(self.limpiar_filtros)

        # BOTÓN EXPORTAR PDF
        self.btn_pdf = QPushButton("📕 Exportar PDF")
        self.btn_pdf.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 15px; font-weight: bold; border-radius: 5px;")
        self.btn_pdf.clicked.connect(self.exportar_pdf)

        lay_f.addWidget(QLabel("Desde:")); lay_f.addWidget(self.f_inicio)
        lay_f.addWidget(QLabel("Hasta:")); lay_f.addWidget(self.f_fin)
        lay_f.addWidget(QLabel("Tipo:")); lay_f.addWidget(self.f_tipo)
        lay_f.addSpacing(10)
        lay_f.addWidget(self.btn_buscar)
        lay_f.addWidget(self.btn_limpiar) 
        lay_f.addWidget(self.btn_pdf)
        
        self.layout_principal.addWidget(frame_filtros)

        # --- TABLA ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Código", "Producto", "Tipo", "Precio", "Cantidad", "Observaciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.layout_principal.addWidget(self.tabla)

        # --- PAGINACIÓN ---
        lay_pag = QHBoxLayout()
        self.btn_ant = QPushButton("Anterior")
        self.btn_sig = QPushButton("Siguiente")
        self.lbl_pag = QLabel("Página 1")
        
        self.btn_ant.clicked.connect(self.pagina_anterior)
        self.btn_sig.clicked.connect(self.pagina_siguiente)

        lay_pag.addStretch(); lay_pag.addWidget(self.btn_ant); lay_pag.addWidget(self.lbl_pag); lay_pag.addWidget(self.btn_sig); lay_pag.addStretch()
        self.layout_principal.addLayout(lay_pag)

    def exportar_pdf(self):
        if not FPDF_INSTALADO:
            QMessageBox.critical(self, "Error", "La librería fpdf2 no está instalada.")
            return

        filas = self.tabla.rowCount()
        if filas == 0:
            QMessageBox.warning(self, "Aviso", "No hay datos para exportar.")
            return

        # 1. ABRIR CUADRO DE DIÁLOGO PARA GUARDAR
        nombre_sugerido = f"Reporte_{datetime.now().strftime('%d_%m_%Y')}.pdf"
        
        # Esta función abre la ventana de Windows/Mac/Linux para elegir ruta
        ruta_guardado, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Reporte", 
            nombre_sugerido, 
            "Archivos PDF (*.pdf)"
        )

        # Si el usuario cierra la ventana o cancela, salimos de la función
        if not ruta_guardado:
            return

        try:
            # 2. GENERAR EL CONTENIDO DEL PDF (Igual que antes)
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            
            # Encabezado estilizado
            pdf.set_font("Arial", 'B', 20)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 15, "REPORTE DE MOVIMIENTOS", ln=True, align='C')
            
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(127, 140, 141)
            rango = f"Filtros: {self.f_inicio.date().toString('dd/MM/yyyy')} a {self.f_fin.date().toString('dd/MM/yyyy')} | Tipo: {self.f_tipo.currentText()}"
            pdf.cell(0, 10, rango, ln=True, align='C')
            pdf.ln(5)

            # Configuración de tabla
            columnas = ["Fecha", "Cod.", "Producto", "Tipo", "Precio", "Cant.", "Observaciones"]
            anchos = [25, 25, 55, 20, 30, 15, 100]

            # Cabecera de tabla azul
            pdf.set_fill_color(52, 152, 219)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 10)
            for i in range(len(columnas)):
                pdf.cell(anchos[i], 10, columnas[i], border=1, align='C', fill=True)
            pdf.ln()

            # Filas de la tabla
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 9)
            for r in range(filas):
                for c in range(self.tabla.columnCount()):
                    item = self.tabla.item(r, c)
                    texto = item.text() if item else ""
                    if len(texto) > 55: texto = texto[:52] + "..."
                    pdf.cell(anchos[c], 8, texto, border=1, align='C')
                pdf.ln()

            # 3. GUARDAR EN LA RUTA SELECCIONADA
            pdf.output(ruta_guardado)
            
            QMessageBox.information(self, "Éxito", "El reporte se ha guardado correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el PDF: {str(e)}")

    def limpiar_filtros(self):
        """Reinicia los campos a sus valores originales y recarga"""
        self.f_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.f_fin.setDate(QDate.currentDate())
        self.f_tipo.setCurrentIndex(0) # Vuelve a "Todos"
        self.reset_paginar()

    def reset_paginar(self):
        self.pagina_actual = 0
        self.cargar_datos()

    def cargar_datos(self):
        # Lógica de carga con los filtros actuales
        fecha_ini = self.f_inicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.f_fin.date().toString("yyyy-MM-dd")
        tipo = self.f_tipo.currentText()

        conn = database.crear_conexion()
        cursor = conn.cursor()

        query = """
            SELECT m.fecha, p.codigo, p.nombre, m.tipo, m.precio, m.cantidad, m.observaciones
            FROM movimientos m
            JOIN productos p ON m.id_producto = p.id
            WHERE m.fecha BETWEEN ? AND ?
        """
        params = [fecha_ini, fecha_fin]

        if tipo != "Todos":
            query += " AND m.tipo = ?"
            params.append(tipo)

        query += f" ORDER BY m.fecha DESC LIMIT {self.limite} OFFSET {self.pagina_actual * self.limite}"
        
        cursor.execute(query, params)
        datos = cursor.fetchall()
        conn.close()

        self.tabla.setRowCount(0)
        for r_idx, r_data in enumerate(datos):
            self.tabla.insertRow(r_idx)
            for c_idx, valor in enumerate(r_data):
                if c_idx == 4: valor = f"$ {valor:,.2f}"
                if c_idx == 0:
                    try: valor = QDate.fromString(valor, "yyyy-MM-dd").toString("dd/MM/yyyy")
                    except: pass
                
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(r_idx, c_idx, item)

        self.lbl_pag.setText(f"Página {self.pagina_actual + 1}")

    def pagina_anterior(self):
        if self.pagina_actual > 0:
            self.pagina_actual -= 1
            self.cargar_datos()

    def pagina_siguiente(self):
        self.pagina_actual += 1
        self.cargar_datos()

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
        layout_sidebar.setSpacing(5) 

        # Título del Menú
        lbl_menu = QLabel("MENU PRINCIPAL")
        lbl_menu.setStyleSheet("color: #95a5a6; font-size: 11px; font-weight: bold; margin-bottom: 5px;")
        lbl_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sidebar.addWidget(lbl_menu)

        # Botones con ICONOS (Emojis)
        self.btn_cat = QPushButton("  📁  Categorías")
        self.btn_prod = QPushButton("  📦  Productos")
        self.btn_mov = QPushButton("  🔄  Movimientos")
        self.btn_inv = QPushButton("  📊  Inventario")
        self.btn_reportes = QPushButton("  📋  Reportes")
        
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
        self.btn_mov.setStyleSheet(estilo_botones)
        self.btn_inv.setStyleSheet(estilo_botones)
        self.btn_reportes.setStyleSheet(estilo_botones)

        # Añadir al layout
        layout_sidebar.addWidget(self.btn_cat)
        layout_sidebar.addWidget(self.btn_prod)
        layout_sidebar.addWidget(self.btn_mov)
        layout_sidebar.addWidget(self.btn_inv)
        layout_sidebar.addWidget(self.btn_reportes)
        
        # Espacio flexible al final para empujar todo hacia arriba
        layout_sidebar.addStretch()

        # --- CONTENEDOR DE PÁGINAS ---
        self.paginas = QStackedWidget()
        self.mod_cat = ModuloCategorias()
        self.mod_prod = ModuloProductos()
        self.mod_mov = ModuloMovimientos()
        self.mod_inv = ModuloInventario()
        self.mod_ver_prod = ModuloVerProducto()
        self.mod_grafica = ModuloGraficaCompras()
        self.mod_grafica_ventas = ModuloGraficaVentas()
        self.mod_reportes = ModuloReportes()

        self.paginas.addWidget(self.mod_cat)
        self.paginas.addWidget(self.mod_prod)
        self.paginas.addWidget(self.mod_mov)    
        self.paginas.addWidget(self.mod_inv)
        self.paginas.addWidget(self.mod_ver_prod)
        self.paginas.addWidget(self.mod_grafica)
        self.paginas.addWidget(self.mod_grafica_ventas)
        self.paginas.addWidget(self.mod_reportes)

        # Conexiones de botones
        self.btn_cat.clicked.connect(lambda: self.paginas.setCurrentIndex(0))
        self.btn_prod.clicked.connect(self.ir_a_productos)
        self.btn_mov.clicked.connect(self.ir_a_movimientos)
        self.btn_inv.clicked.connect(self.ir_a_inventario)
        self.mod_ver_prod.btn_volver.clicked.connect(lambda: self.paginas.setCurrentIndex(3))
        self.mod_ver_prod.btn_ver_grafica.clicked.connect(self.ir_a_grafica_compras)
        self.mod_grafica.btn_volver_detalle.clicked.connect(lambda: self.paginas.setCurrentIndex(4))
        self.mod_ver_prod.btn_grafica_ventas.clicked.connect(self.abrir_grafica_ventas)
        self.mod_grafica_ventas.btn_volver_detalle.clicked.connect(lambda: self.paginas.setCurrentIndex(5))
        self.btn_reportes.clicked.connect(self.ir_a_reportes)

        # Unir todo
        layout_principal.addWidget(self.sidebar)
        layout_principal.addWidget(self.paginas)

    def ir_a_productos(self):
        self.mod_prod.actualizar_combobox()
        self.paginas.setCurrentIndex(1)

    def ir_a_movimientos(self):
        self.mod_mov.actualizar_productos_combobox() 
        self.paginas.setCurrentIndex(2)

    def ir_a_inventario(self):
        self.mod_inv.cargar_datos() # Refresca el stock cada vez que entras
        self.paginas.setCurrentIndex(3)

    def ir_a_grafica_compras(self):
        id_p = self.mod_ver_prod.id_producto_actual
        nombre_p = self.mod_ver_prod.lbl_nombre.text()
        self.mod_grafica.cargar_grafica(id_p, nombre_p)
        self.paginas.setCurrentIndex(5) 

    def abrir_grafica_ventas(self):
        id_p = self.mod_ver_prod.id_producto_actual
        nombre_p = self.mod_ver_prod.lbl_nombre.text()
        self.mod_grafica_ventas.cargar_grafica(id_p, nombre_p)
        self.paginas.setCurrentIndex(6) 

    def ir_a_reportes(self):
        self.mod_reportes.cargar_datos()
        self.paginas.setCurrentIndex(7)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
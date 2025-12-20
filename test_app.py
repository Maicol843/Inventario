import sys
import sqlite3
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

try:
    # Prueba de Base de Datos
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS prueba (id INTEGER PRIMARY KEY, nombre TEXT)")
    conn.commit()
    conn.close()
    db_status = "✅ Base de Datos: OK"
except Exception as e:
    db_status = f"❌ Error DB: {e}"

class TestVentana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prueba de Sistema")
        layout = QVBoxLayout()
        label = QLabel(db_status)
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = TestVentana()
    ventana.show()
    sys.exit(app.exec())
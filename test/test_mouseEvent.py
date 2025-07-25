from PyQt5.QtWidgets import (
    QApplication, QTableWidget, QTableWidgetItem,
    QWidget, QVBoxLayout, QMenu, QAction
)
from PyQt5.QtCore import Qt, QPoint
import sys

class HoverMenuTable(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)
        self.setMouseTracking(True)
        self.hovered_row = -1

        for row in range(rows):
            self.setItem(row, 0, QTableWidgetItem(f"Dosya {row+1}"))

        # Menü oluştur
        self.menu = QMenu()
        self.action_edit = QAction("Düzenle", self)
        self.action_delete = QAction("Sil", self)
        self.menu.addAction(self.action_edit)
        self.menu.addAction(self.action_delete)

        # Örnek bağlantılar
        self.action_edit.triggered.connect(lambda: print(f"Satır {self.hovered_row} düzenlendi"))
        self.action_delete.triggered.connect(lambda: print(f"Satır {self.hovered_row} silindi"))

    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        row = index.row()

        if row != self.hovered_row:
            self.hovered_row = row
            if row != -1:
                global_pos = self.viewport().mapToGlobal(self.visualItemRect(self.item(row, 0)).topRight())
                self.menu.popup(global_pos)  # Menü göster

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_row = -1
        self.menu.hide()
        super().leaveEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.table = HoverMenuTable(5, 1)
        self.table.setHorizontalHeaderLabels(["Dosyalar"])
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.setWindowTitle("Hover Menü Örneği")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())

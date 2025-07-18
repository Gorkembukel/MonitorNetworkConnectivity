
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiSubWindow, QWidget
from QTDesigns.ui_mainmenu import Ui_MainWindow
from QTDesigns.ui_targetWindow import Ui_pingWindow  # targetWindow.ui içindeki ana widget adı muhtemelen "Form"

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.add_subwindow()

    def add_subwindow(self):
        # Subwindow içeriğini oluştur
        widget = QWidget()
        self.sub_ui = Ui_pingWindow()
        self.sub_ui.setupUi(widget)

        # Subwindow olarak MDI'ye ekle
        sub = QMdiSubWindow()
        sub.setWidget(widget)
        sub.setWindowTitle("Target Window")

        self.ui.mdiArea.addSubWindow(sub)
        sub.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

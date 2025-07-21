import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from QTDesigns.MainWindow import Ui_MonitorNetWorkConnectivity
from source.PingStats import get_data_keys



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MonitorNetWorkConnectivity()
        self.ui.setupUi(self)
        self.ui.tableTarget
        self.set_table_headers()

    def set_table_headers(self):
        headers = list(get_data_keys())
        self.ui.tableTarget.setColumnCount(len(headers))
        self.ui.tableTarget.setHorizontalHeaderLabels(headers)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
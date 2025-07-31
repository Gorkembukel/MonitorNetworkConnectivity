from QTDesigns.iperf_window import Ui_Dialog_iperfWindow
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog

class IperfWindow(QDialog):  # Yeni pencere Ping atmak için parametre alır
    pingTargetsReady = pyqtSignal()#
    def __init__(self, parent= None):
        super().__init__(parent)
        
        self.ui = Ui_Dialog_iperfWindow()
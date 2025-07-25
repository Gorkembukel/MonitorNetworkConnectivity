import sys,time
from dataclasses import dataclass, field
from typing import List, Dict
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog,QTableWidgetItem,QMenu
from PyQt5.QtCore import QTimer,QThread, pyqtSignal,Qt
from PyQt5.QtGui import QColor
from QTDesigns.MainWindow import Ui_MonitorNetWorkConnectivity
from QTDesigns.PingWindow import Ui_pingWindow
from source.PingStats import get_data_keys
from source.PingThreadController import ScapyPinger
from PyQt5 import QtCore
from PyQt5 import QtWidgets


scapyPinger_global = ScapyPinger()
stats_list_global = scapyPinger_global.find_all_stats()
headers = List
@dataclass
class Pass_Data_ScapyPinger:#veri aktarmak için container
    targets: List[str] = field(default_factory=list)
    interval_ms: int = 1000
    duration: int = 10
    byte_size: int = 64
    target_dict: Dict[str, Dict[str, int]] = field(default_factory=dict)


class PingWindow(QDialog):  # Yeni pencere Ping atmak için parametre alır
    pingTargetsReady = pyqtSignal()#
    def __init__(self, parent= None):
        super().__init__(parent)
        self.ui = Ui_pingWindow()
        self.parent = parent
        self.ui.setupUi(self)
        self.data = Pass_Data_ScapyPinger()
        self.isInfinite = False
         # Butona tıklanınca işlem yapılacak
        self.ui.pushButton.clicked.connect(self.extract_targets)
        self.ui.pushButton_durationUnlimited.clicked.connect(self.setIsInfinite)
    def setIsInfinite(self):    
        if self.isInfinite:
            self.isInfinite =False
        else:
            self.isInfinite = True



    def extract_targets(self):
        global headers 
        global scapyPinger_global
        global stats_list_global
        headers = list(get_data_keys())
        # 1️⃣ PlainTextEdit içeriğini al
        text = self.ui.plainTextEdit.toPlainText()
        # 2️⃣ Satırları ayır ve boş olmayanları döndür
        targets = [line.strip() for line in text.splitlines() if line.strip()]

        self.data.targets = targets#TODO deepcopy gerekebilir mi?

         # 2️⃣ SpinBox'lardan parametreleri al
        byte_size = self.ui.spinBox_byte.value()
        interval_ms = self.ui.spinBox_interval.value()
        duration = self.ui.spinBox_duration.value()
        isInfinite = self.isInfinite

        
        

        scapyPinger_global.add_targetList(targets=targets, interval_ms=interval_ms, duration= duration, byte_size= byte_size,isInfinite=isInfinite)
        
        stats_list_global = scapyPinger_global.find_all_stats()
        self.pingTargetsReady.emit()


        


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.target_to_row = {}#table için primary key
        self.ui = Ui_MonitorNetWorkConnectivity()
        self.ui.setupUi(self)
        self.tableTarget = self.ui.tableTarget
        self.set_table_headers()
        self.buttonPingBaslat = self.ui.pushButton_pingBaslat
        self.ui.pingWindowButton.clicked.connect(self.open_pingWindow)
        self.buttonPingBaslat.clicked.connect(self.set_scapyPinger)
        self.ui.pushButton_pingDurdur.setEnabled(False)

        self.tableTarget.viewport().installEventFilter(self)
        self.tableTarget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableTarget.customContextMenuRequested.connect(self.ip_control_interface)

        self.ui.pushButton_pingDurdur.clicked.connect(self.stopAllThreads)
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(17)  # 1000ms = 1 saniye#60fps için girilen değr
        self.stats_timer.timeout.connect(self.update_Stats)
        self.stats_timer.start()

    def open_graph(self):
        pass
    def ip_stop(self, address:str):
        global scapyPinger_global
        scapyPinger_global.stop_address(address=address)
    def deleteRowFromTable(self):
        pass
     #burada rowdaki veriler alınıp açılan pencereye aktarılmalı böylece rowdaki ip kontrol edilmiş olunur
    def eventFilter(self, source, event):
        if(event.type() == QtCore.QEvent.MouseButtonPress and
           event.buttons() == QtCore.Qt.RightButton and
           source is self.tableTarget.viewport()):
            

            # Tıklanan y koordinatına göre satır bulunur
            row = self.tableTarget.rowAt(event.pos().y())
            
            if row != -1:
                # Satır başlığındaki 'target' hücresini al
                header_item = self.tableTarget.itemAt(1,row)#TODO burası ip adresinin olduğu hücreyi alıyor. Grafik değişire bura da değişmeli. DAha akılcı bir çözüm lazım, belki header listte arama yapılabilinir
                if header_item:
                    address = header_item.text()
                    
                else:
                    address = None
                    print("Satır başlığı yok")
            
            #Qmenu, ip_control_interface için action menusu
            self.ip_control_menu = QtWidgets.QMenu()
            self.ip_control_menu.addAction("Grafik Aç",self.open_graph)
            self.ip_control_menu.addAction("Durdur",lambda:self.ip_stop(address=address))
            self.ip_control_menu.addAction("Sil",self.deleteRowFromTable)
                

            
        return super(MainWindow, self).eventFilter(source, event)

    def ip_control_interface(self,pos):
        self.ip_control_menu.exec(self.tableTarget.mapToGlobal(pos))

    def update_Stats(self):
        global stats_list_global
        global headers

        for stat in stats_list_global:
            summary = stat.summary()
            target = summary["target"]

            if target in self.target_to_row:
                row = self.target_to_row[target]
            else:
                row = self.ui.tableTarget.rowCount()
                self.ui.tableTarget.insertRow(row)
                self.target_to_row[target] = row

            # ✅ Renk sadece bir kere belirleniyor
            last_result = summary.get("last_result", "")
            color = QColor(200, 255, 200) if last_result == "Success" else QColor(255, 200, 200)

            # 🔁 Hem hücreyi doldur, hem rengini ver
            for col, key in enumerate(headers):
                value = summary.get(key, "")
                item = QTableWidgetItem(str(value))
                item.setBackground(color)
                self.ui.tableTarget.setItem(row, col, item)

        thread_count = scapyPinger_global.get_active_count()
        self.ui.lineEdit_threadCount.setText(f"{(thread_count)}")
        if thread_count == 0:
            self.ui.pushButton_pingDurdur.setEnabled(False)
        else:
            self.ui.pushButton_pingDurdur.setEnabled(True)

    def stopAllThreads(self):
        scapyPinger_global.stop_All()
    def update_table(self, stats_list):
        headers = list(get_data_keys())
        for stat in stats_list:
            summary = stat.summary()
            target = summary["target"]

            if target in self.target_to_row:
                row = self.target_to_row[target]
            else:
                row = self.ui.tableTarget.rowCount()
                self.ui.tableTarget.insertRow(row)
                self.target_to_row[target] = row

            for col, key in enumerate(headers):
                value = summary.get(key, "")
                item = QTableWidgetItem(str(value))
                self.ui.tableTarget.setItem(row, col, item)



    def set_table_headers(self):
        headers = list(get_data_keys())
        self.ui.tableTarget.setColumnCount(len(headers))
        self.ui.tableTarget.setHorizontalHeaderLabels(headers)
    def set_scapyPinger(self):
        global scapyPinger_global,stats_list_global
        scapyPinger_global.start_all()
        stats_list_global = scapyPinger_global.find_all_stats()
        
        
            


    def open_pingWindow(self):
        self.pingWindow = PingWindow(self)
        self.pingWindow.pingTargetsReady.connect(self.update_Stats)
        self.pingWindow.show()
        

    
    def add_pings(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
import sys,time
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog,QTableWidgetItem,QMenu
from PyQt5.QtCore import QTimer,QThread, pyqtSignal,Qt,QTime,QDateTime
from PyQt5.QtGui import QColor,QPalette
from QTDesigns.MainWindow import Ui_MonitorNetWorkConnectivity
from QTDesigns.PingWindow import Ui_pingWindow
from QTDesigns.Change_parameters import Ui_Dialog_changeParameter
from source.PingStats import get_data_keys
from source.PingThreadController import PingTask
from source.PingThreadController import ScapyPinger
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from source.GUI_graph import GraphWindow
import subprocess, os
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

class ChangeParameterWindow(QDialog):
    def __init__(self, parent= None, task:PingTask = None):
        super().__init__(parent)
        self.ui = Ui_Dialog_changeParameter()
        self.ui.setupUi(self)
        self.task = task

        now = datetime.now()
        #calender için ayar
        self.ui.dateTimeEdit.setCalendarPopup(True)
        self.ui.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
        self.ui.dateTimeEdit.setMinimumDate(now)
        #task değerlerini okuyup gösterir
        self.ui.lineEdit_ip.setText(task.address)
        self.ui.lineEdit_interval.setText(str(task.interval_ms))
        self.ui.lineEdit_payloadsize.setText(str(task.kwargs['payload_size']))
        self.dissableTabsExcept()

        self.ui.pushButton_settChages.clicked.connect(self.applyChange)

    def dissableTabsExcept(self):
        tabCount = self.ui.tabWidget.count()
        print(f"tab count {tabCount}")

        print(f"end date var mı {self.task.getEnd_datetime()}")

        for i in range(tabCount):        
            self.ui.tabWidget.setTabEnabled(i, False)# bütün tabları kapatır
        if self.task.duration and self.task.duration !=0:
            self.ui.tabWidget.setTabEnabled(0, True)# duration değeri varsa o tabi açar
            self.ui.lineEdit_duration.setText(str(self.task.duration))
            self.ui.tabWidget.setCurrentIndex(0)
        if self.task.kwargs.get('end_datetime'):
            self.ui.tabWidget.setTabEnabled(1, True)# end date objesi varsa değeri varsa o tabi açar
            self.ui.dateTimeEdit.setDateTime(self.task.kwargs['end_datetime'])#pingthread oluşmadığı için ve bu bilgi PingTask'da saklanmadığı için kwargdan alıyoruz
            self.ui.tabWidget.setCurrentIndex(1)
    def applyChange(self):
        try:
            # Interval
            interval_text = self.ui.lineEdit_interval.text().strip()
            if interval_text:
                self.task.interval_ms = int(interval_text)

            # Payload Size
            payload_text = self.ui.lineEdit_payloadsize.text().strip()
            if payload_text:
                self.task.kwargs["payload_size"] = int(payload_text)

            # Duration tabı aktifse → duration güncellenir
            if self.ui.tabWidget.isTabEnabled(0) and self.ui.lineEdit_duration.isEnabled():
                duration_text = self.ui.lineEdit_duration.text().strip()
                if duration_text:
                    self.task.duration = int(duration_text)

            # End datetime tabı aktifse → end_datetime güncellenir
            if self.ui.tabWidget.isTabEnabled(1) and self.ui.dateTimeEdit.isEnabled():
                dt = self.ui.dateTimeEdit.dateTime().toPyDateTime()
                self.task.kwargs["end_datetime"] = dt
            self.task.update_thread_parameters()
            self.close()  # pencereyi kapat
        except ValueError as e:
            print(f"❗ Hatalı giriş: {e}")
            QtWidgets.QMessageBox.warning(self, "Geçersiz Girdi", "Lütfen tüm değerleri sayısal ve doğru formatta girin.")


class PingWindow(QDialog):  # Yeni pencere Ping atmak için parametre alır
    pingTargetsReady = pyqtSignal()#
    def __init__(self, parent= None):
        super().__init__(parent)
        
        self.ui = Ui_pingWindow()
        self.original_color = self.palette().color(QPalette.Window)
        self.parent = parent
        self.ui.setupUi(self)
        self.data = Pass_Data_ScapyPinger()
        self.isInfinite = False
        self.isKill_Mod = False
         # Butona tıklanınca işlem yapılacak
        self.ui.pushButton.clicked.connect(self.extract_addresses)
        self.ui.pushButton_durationUnlimited.clicked.connect(self.setIsInfinite)
        self.ui.checkBox_KillMod.setHidden(True)
        #self.ui.checkBox_KillMod.clicked.connect(self.toggleKill_Mod)
        now = datetime.now()
        
        self.ui.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
        self.ui.dateTimeEdit.setMinimumDate(now)

        self.ui.checkBox.toggled.connect(self.changeDurationLabel)
    def toggleKill_Mod(self):
        
        palette = self.palette()
        if self.ui.dateTimeEdit.isEnabled():
            
            self.ui.dateTimeEdit.setDisabled(True)
        if self.isKill_Mod:
            palette.setColor(QPalette.Window, self.original_color)
            self.setPalette(self.parent.palette())
            
            self.isKill_Mod = False
        if not self.isKill_Mod:
            palette.setColor(QPalette.Window, QColor("red"))
                
            self.isKill_Mod = True
        
        self.setPalette(palette)
    def setIsInfinite(self):    
        if self.isInfinite:
            self.isInfinite =False
        else:
            self.isInfinite = True

    def changeDurationLabel(self,toggled):
        self.ui.label_duration.setDisabled(toggled)
    

    

    
    def extract_addresses(self):
        global headers 
        global scapyPinger_global
        global stats_list_global
        headers = list(get_data_keys())
        
        kwargs = {}#scapypinger için argümanlar.Eklemek istediğiniz armünanları pingthreadController içindeki filtre metoduna tanıtmalısınız 
                   #PingThreadController ->PingThread ->icmplib ping ->ICMPRequest
        text = ""
        # 1️⃣ PlainTextEdit içeriğini al
        text = self.ui.plainTextEdit.toPlainText()
        # 2️⃣ Satırları ayır ve boş olmayanları döndür
        addresses = [line.strip() for line in text.splitlines() if line.strip()]
        if addresses and addresses[0].startswith("**"):
            print("İlk satır '**' ile başlıyor.")
            self.ui.checkBox_KillMod.setVisible(True)
            
        self.data.targets = addresses#TODO deepcopy gerekebilir mi?

         # 2️⃣ SpinBox'lardan parametreleri al
        payload_size = self.ui.spinBox_byte.value()
        payload_size = 56 if not payload_size else payload_size#FIXME payload_size sıfır olmasın diye default değer girildi ama defalut değeri hem burada hem kendi yerinde (icmplib pig) olması 
                                                               # doğru gelmedi. bu argümanlar boş olduğunda add_addresslist'e geçmeyecek şekilde düzenlemek daha doğru olur

        interval_ms = self.ui.spinBox_interval.value()
        isInfinite = self.ui.pushButton_durationUnlimited.isChecked()
        duration = self.ui.spinBox_duration.value() if self.ui.spinBox_duration.isEnabled() else None# kutu aktif değilse değerini okumaz
        timeout = self.ui.spinBox_timeout.value() / 1000 #ms çevirisi

        qt_datetime = None
        if self.ui.dateTimeEdit.isEnabled():
            qt_datetime = self.ui.dateTimeEdit.dateTime()

        if qt_datetime:
            kwargs["end_datetime"] = qt_datetime.toPyDateTime()#pingThread'de date objesi olarak kullanılır
        
        
        print(f"is infinite gui {isInfinite}")
        scapyPinger_global.add_addressList(timeout = timeout ,addresses=addresses,isKill_Mod=self.isKill_Mod,interval_ms=interval_ms, duration= duration,isInfinite=isInfinite, payload_size = payload_size,**kwargs)
        text = ""
        interval_ms = None
        isInfinite = None
        duration = None
        
        qt_datetime = None
        kwargs = None

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
        self.ui.tableTarget.cellDoubleClicked.connect(self.on_row_clicked)
        #self.tableTarget.customContextMenuRequested.connect(self.ip_control_interface)

        self.ui.pushButton_pingDurdur.clicked.connect(self.stopAllThreads)
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(17)  # 1000ms = 1 saniye#60fps için girilen değr
        self.stats_timer.timeout.connect(self.update_Stats)
        self.stats_timer.start()

    def open_graph(self,address):
        task = scapyPinger_global.get_task(address=address)
        statObject = task.stats
        print(statObject._rttList)
        self.graphWindow = GraphWindow(stat_obj=statObject,parent=self)
        self.graphWindow.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.graphWindow.show()
    def ip_stop(self, address:str, **kargs):
        print("stop_address kargs:", kargs)#FIXME geçici
        global scapyPinger_global
        scapyPinger_global.stop_address(address=address, **kargs)
    def deleteRowFromTable(self,address:str):
        scapyPinger_global.stop_address(address=address,isKill=True)
        scapyPinger_global.delete_stats(address=address)
        
    def toggleBeep_by_address(self,address:str):#
        global scapyPinger_global   
        scapyPinger_global.toggleBeep_by_address(address=address)
        
     #burada rowdaki veriler alınıp açılan pencereye aktarılmalı böylece rowdaki ip kontrol edilmiş olunur
    def eventFilter(self, source, event):
        if(event.type() == QtCore.QEvent.MouseButtonPress and
           event.buttons() == QtCore.Qt.RightButton and
           source is self.tableTarget.viewport()):
            

            # Tıklanan y koordinatına göre satır bulunur
            row = self.tableTarget.rowAt(event.pos().y())
            col = self.tableTarget.columnAt(event.pos().x())
            
            if row == -1 or col == -1:
                return super(MainWindow, self).eventFilter(source, event)
            # Satır başlığındaki 'target' hücresini al
            header_item = self.tableTarget.item(row,0)#TODO burası ip adresinin olduğu hücreyi alıyor. Grafik değişire bura da değişmeli. DAha akılcı bir çözüm lazım, belki header listte arama yapılabilinir
            
            if header_item:
                address = header_item.text()
                
                
            else:
                address = None
                print("Satır başlığı yok")
            
            #Qmenu, ip_control_interface için action menusu
            ip_control_menu = QtWidgets.QMenu()
            ip_control_menu.addAction("Grafik Aç",lambda:self.open_graph(address=address))
            ip_control_menu.addAction("Beep",lambda :self.toggleBeep_by_address(address))
            ip_control_menu.addAction("Durdur",lambda:self.ip_stop(address=address, isToggle =True, isKill =False))
            ip_control_menu.addAction("Sil",lambda: self.deleteRowFromTable(address=address))
            
            ip_control_menu.exec(self.tableTarget.mapToGlobal(event.pos()))
        if(event.type() == QtCore.QEvent.MouseButtonPress and
           event.buttons() == QtCore.Qt.LeftButton and
           source is self.tableTarget.viewport()):
            

            # Tıklanan y koordinatına göre satır bulunur
            row = self.tableTarget.rowAt(event.pos().y())
            
            #print(f"x   {event.pos().x()}     y {event.pos().y()}     row {row}")
            if row != -1:
                # Satır başlığındaki 'target' hücresini al
                header_item = self.tableTarget.item(row,0)#TODO burası ip adresinin olduğu hücreyi alıyor. Grafik değişire bura da değişmeli. DAha akılcı bir çözüm lazım, belki header listte arama yapılabilinir
                
                if header_item:
                    address = header_item.text()
                    self.open_changeSettingsWindow(task=scapyPinger_global.get_task(address=address))
                    
                else:
                    address = None
                    print("Satır başlığı yok")


            
        return super(MainWindow, self).eventFilter(source, event)

    def ip_control_interface(self,pos):
        self.ip_control_menu.exec(self.tableTarget.mapToGlobal(pos))
    def update_rate_cell(self, row: int, col: int, stat):
        

        target = stat.target

        if not hasattr(self, 'target_to_graph'):
            self.target_to_graph = {}

        if target in self.target_to_graph:
            graph = self.target_to_graph[target]

            # C++ nesnesi silinmiş mi?
            if graph["curve"] is None or not hasattr(graph["curve"], "setData"):
                return

            now = time.time()
            rate_val = stat.rate or 0.1
            beat = min(1.0, rate_val / 10.0)

            graph["x"].pop(0)
            graph["x"].append(now)

            graph["y"].pop(0)
            graph["y"].append(beat)

            try:
                graph["curve"].setData(graph["x"], graph["y"])
            except RuntimeError:
                print(f"[{target}] Curve silinmiş, güncellenemiyor.")
                return
        else:
            container, curve, x, y = GraphWindow.create_rate_widget()
            self.ui.tableTarget.setCellWidget(row, col, container)
            self.target_to_graph[target] = {
                "curve": curve,
                "x": x,
                "y": y
            }

    def update_Stats(self):
        global stats_list_global
        global headers
        self.tableTarget.clearContents()#silinmiş pingStat objelerinin verilerini tablodan kaldırır
        self.tableTarget.clearContents()
        if hasattr(self, 'target_to_graph'):
            self.target_to_graph.clear()
        for stat in stats_list_global.values():# FIXME burada stat_list liste ise patlar
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
    def on_row_clicked(self, row, column):
        print("mahmut")
        table = self.ui.tableTarget
        column_count = table.columnCount()

        values = []
        for col in range(column_count):
            item = table.item(row, col)
            if item:
                values.append(item.text())
            else:
                values.append("")

        print(f"Seçilen satır verileri: {values}")

    def open_changeSettingsWindow(self, task:PingTask):
        if task:
            self.changeSetting = ChangeParameterWindow(task=task)
            self.changeSetting.show()
    
    def add_pings(self):
        pass
    def closeEvent(self, event):
        print("Uygulama kapanıyor, thread'ler durduruluyor...")
        
        # Thread nesnelerini döngüyle durdur
        for task in scapyPinger_global.tasks.values():
            task.stop(isKill = True)
            task.join()  # thread kapanmasını bekle

        event.accept()  # pencerenin kapanmasına izin ver

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
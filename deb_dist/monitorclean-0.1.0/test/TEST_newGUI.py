import sys,time
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog,QTableWidgetItem,QMenu,QAction,QDockWidget
from PyQt5.QtCore import QTimer,QThread, pyqtSignal,Qt,QTime,QDateTime,pyqtSlot
from PyQt5.QtGui import QColor,QPalette
from QTDesigns.MainWindow import Ui_MonitorNetWorkConnectivity
from QTDesigns.PingWindow import Ui_pingWindow
from QTDesigns.Change_parameters import Ui_Dialog_changeParameter
from source.ping.PingStats import get_data_keys
from source.ping.PingThreadController import PingTask
from source.ping.PingThreadController import ScapyPinger
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from source.ping.GUI_graph import GraphWindow
import subprocess, os
from source.GUI.iperf_window import IperfWindow
from source.GUI.ssh_window import SSH_Client_Window

from source.ssH.PingParser import Std_to_Pingstat
scapyPinger_global = ScapyPinger()
stats_list_global = scapyPinger_global.find_all_stats()
sshClientController = None

headers = list(get_data_keys())
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
        self.setWindowTitle(task.address)
        self.isInfinite = task.isInfinite
        self.timeOut = str(int(task.kwargs['timeout']))
        self.ui.checkBox_infinite.setCheckState(self.isInfinite)
        now = datetime.now()
        #calender için ayar
        self.ui.dateTimeEdit.setCalendarPopup(True)
        self.ui.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
        self.ui.dateTimeEdit.setMinimumDate(now)
        #task değerlerini okuyup gösterir
        self.ui.lineEdit_ip.setText(task.address)
        self.ui.lineEdit_interval.setText(str(task.interval_ms))
        self.ui.lineEdit_payloadsize.setText(str(task.kwargs['payload_size']))
        self.ui.lineEdit_timeout.setText(self.timeOut)
        
        self.dissableTabsExcept()

        self.ui.pushButton_settChages.clicked.connect(self.applyChange)

    def dissableTabsExcept(self):
        tabCount = self.ui.tabWidget.count()
        print(f"tab count {tabCount}")

        print(f"end date var mı {self.task.getEnd_datetime()}")

        for i in range(tabCount):        
            self.ui.tabWidget.setTabEnabled(i, False)# bütün tabları kapatır
        if ( self.task.duration or self.isInfinite) and (self.task.duration !=0 or self.isInfinite) :
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
            #timeout
            timeout_text = self.ui.lineEdit_timeout.text().strip()
            if timeout_text:
                self.task.kwargs['timeout'] = int(timeout_text)
            # Payload Size
            payload_text = self.ui.lineEdit_payloadsize.text().strip()
            if payload_text:
                self.task.kwargs["payload_size"] = int(payload_text)
            #isInfinite
            isInfinite = self.ui.checkBox_infinite.isChecked()
            if isInfinite:
                self.task.isInfinite= isInfinite
            # Duration tabı aktifse → duration güncellenir
            if self.ui.tabWidget.isTabEnabled(0) and self.ui.lineEdit_duration.isEnabled():
                duration_text = self.ui.lineEdit_duration.text().strip()
                if duration_text:
                    self.task.duration= int(duration_text)
                    self.task.isInfinite = False
            # End datetime tabı aktifse → end_datetime güncellenir
            if self.ui.tabWidget.isTabEnabled(1) and self.ui.dateTimeEdit.isEnabled():
                dt = self.ui.dateTimeEdit.dateTime().toPyDateTime()
                self.task.kwargs["end_datetime"] = dt
            self.task.update_thread_parameters()
            self.close()  # pencereyi kapat
        except ValueError as e:
            print(f"❗ Hatalı giriş: {e}")
            QtWidgets.QMessageBox.warning(self, "Geçersiz Girdi", "Lütfen tüm değerleri sayısal ve doğru formatta girin.")
    def __del__(self):
        print(f"Change appley penceresinin objesi silindi")

class PingWindow(QDialog):  # Yeni pencere Ping atmak için parametre alır
    pingTargetsReady = pyqtSignal()#
    def __init__(self, parent= None, last_ip_list=None): # , last_ip_list=None
        global stats_list_global
        super().__init__(parent)                      
        self.ui = Ui_pingWindow()
        self.original_color = self.palette().color(QPalette.Window)
        self.parent = parent
        self.ui.setupUi(self)

        if last_ip_list and not stats_list_global:            
            for line in last_ip_list:
                self.ui.plainTextEdit.insertPlainText(f"{line}\n")
            
        
            
        self.textInBegining = self.get_ıp_for_plainText()# statlist'e göre ip addreslerini alıp plain text'e ekler ve en sonki halini döndürür 

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
    def get_ıp_for_plainText(self):
        global stats_list_global

        for ip in stats_list_global.keys():
            self.ui.plainTextEdit.insertPlainText(f"{ip}\n")
        return self.ui.plainTextEdit.toPlainText()

    def changeDurationLabel(self,toggled):
        self.ui.label_duration.setDisabled(toggled)
    

    def delete_address_plainText(self, addresses: list):
        """
        address_list: Güncel IP listesi (her eleman bir IP stringi olacak)
        self.textInBegining: Başlangıçtaki IP'ler (string, satır satır)
        """
        global scapyPinger_global

        # Başlangıç IP'lerini satır bazında al
        lines_in_beginning = set(
            l.strip() for l in self.textInBegining.splitlines() if l.strip()
        )

        # Parametreden gelen güncel IP listesi
        lines_in_address = set(l.strip() for l in addresses if l.strip())

        # Sadece başlangıçta olup güncel listede olmayan IP'ler
        ips_to_delete = lines_in_beginning - lines_in_address

        # Silme işlemi
        for ip in ips_to_delete:
            scapyPinger_global.delete_stats(address=ip)
    
    def extract_addresses(self):
        """
        PlainTextEdit'teki IP listesini okur, mevcut çalışan hedeflerle karşılaştırır.
        Sadece yeni eklenenleri başlatır ve listeden çıkarılanları durdurup siler.
        """
        global headers, scapyPinger_global, stats_list_global

        # 0) Header'ları bir kez al (gereksiz tekrarları önle)
        headers = list(get_data_keys())

        # 1) UI'dan adresleri oku
        text = self.ui.plainTextEdit.toPlainText()
        addresses = [line.strip() for line in text.splitlines() if line.strip()]

        # KillMod uyarısı (ilk satır "**" ile başlıyorsa checkbox'ı göster)
        self.ui.checkBox_KillMod.setVisible(bool(addresses and addresses[0].startswith("**")))

        # 2) Parametreleri topla (UI default'lar doğruysa ek korumaya gerek kalmaz)
        payload_size = self.ui.spinBox_byte.value() or 56
        interval_ms  = self.ui.spinBox_interval.value()
        isInfinite   = self.ui.pushButton_durationUnlimited.isChecked()
        duration     = self.ui.spinBox_duration.value() if self.ui.spinBox_duration.isEnabled() else None
        timeout      = self.ui.spinBox_timeout.value() 

        kwargs = {}
        if self.ui.dateTimeEdit.isEnabled():
            kwargs["end_datetime"] = self.ui.dateTimeEdit.dateTime().toPyDateTime()

        # 3) Mevcut çalışan hedefler ve yeni hedefler arasında fark al
        current_set = set(stats_list_global.keys()) if isinstance(stats_list_global, dict) else set()
        new_set     = set(addresses)

        to_add    = list(new_set - current_set)
        to_remove = list(current_set - new_set)

        # 4) Eklenmesi gerekenleri tek seferde ekle
        if to_add:
            scapyPinger_global.add_addressList(
                timeout=timeout,
                addresses=to_add,
                isKill_Mod=self.isKill_Mod,
                interval_ms=interval_ms,
                duration=duration,
                isInfinite=isInfinite,
                payload_size=payload_size,
                **kwargs
            )

        # 5) Listeden çıkarılanları durdur ve sil
        for ip in to_remove:
            scapyPinger_global.stop_address(address=ip, isKill=True)
            scapyPinger_global.delete_stats(address=ip)

        # 6) Snapshot'ı güncelle (bir sonraki karşılaştırma için)
        self.textInBegining = "\n".join(addresses)

        # 7) Stats cache'i tazele ve tabloya haber ver
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
        self.sshWindow = None

        self.ui.actionOpen_Iperf.triggered.connect(self.open_iperf)
        self.ui.actionopen_ssh_window.triggered.connect(self.open_sshControlWindow)
         # (İsteğe bağlı) Menüde düzgün isimler gözüksün
        self.ui.dockWidget_pinglist.setWindowTitle("Ping Listesi")
        self.ui.dockWidget_2.setWindowTitle("Grafikler / Diğer")

        # --- VIEW MENÜSÜNÜ DOLDUR ---
        self._attach_view_menu()

        self.tableTarget.viewport().installEventFilter(self)
        self.tableTarget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tableTarget.cellDoubleClicked.connect(self.on_row_clicked)
        
        #self.tableTarget.customContextMenuRequested.connect(self.ip_control_interface)

        self.ui.pushButton_pingDurdur.clicked.connect(self.stopAllThreads)
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(1000)  # 1000ms = 1 saniye#60fps için girilen değr
        self.stats_timer.timeout.connect(self.update_Stats)
        self.stats_timer.start()


        #ip addreslerini program başında ip.txt^den oku
        try:
            with open('ip.txt', 'r', encoding='utf-8') as output:
                self.last_ip_list = [line.strip() for line in output if line.strip()]
        except FileNotFoundError:
            self.last_ip_list = []

     # ----- VIEW MENU -----
    def _attach_view_menu(self):
        mv = self.ui.menuView
        mv.clear()

        # Paneller alt menüsü (otomatik toggleViewAction listesi)
        self.menuPanels = QMenu("Paneller", self)
        mv.addMenu(self.menuPanels)
        self._refresh_panels_menu()

        mv.addSeparator()

        # Hepsini Göster / Hepsini Gizle
        act_show_all = QAction("Hepsini Göster", self)
        act_show_all.triggered.connect(self._show_all_docks)
        mv.addAction(act_show_all)

        act_hide_all = QAction("Hepsini Gizle", self)
        act_hide_all.triggered.connect(self._hide_all_docks)
        mv.addAction(act_hide_all)

    def _refresh_panels_menu(self):
        """Tüm QDockWidget'lar için toggleViewAction ekler."""
        self.menuPanels.clear()
        for dock in self.findChildren(QDockWidget):
            act = dock.toggleViewAction()   # Dock’un kendi göster/gizle action’ı
            act.setCheckable(True)          # Menüde tikli gözüksün
            self.menuPanels.addAction(act)

    def _show_all_docks(self):
        for dock in self.findChildren(QDockWidget):
            dock.show()
            dock.raise_()

    def _hide_all_docks(self):
        for dock in self.findChildren(QDockWidget):
            dock.hide()
    #View için
    def open_iperf(self):
        self.iperf_window = IperfWindow()
        self.iperf_window.show()
    @pyqtSlot(object,str,str)#stdobjesi 
    def start_ping_parser(self,clientWrapper,target_address,stdout_str):#burada std_controlden gelen sinyal ile parser oluşturulacak
        global stats_list_global
        pingParser = Std_to_Pingstat(clientWrapper,target_address,stdout_str)
        pingParser.start()

        stats = pingParser.get_stats()
        stats_list_global[target_address] = stats

    def open_sshControlWindow(self):
    
        if self.sshWindow is None:
            self.sshWindow = SSH_Client_Window(parent=self)
        self.sshWindow.show()
        self.sshWindow.raise_()

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
            if scapyPinger_global.is_alive_ping(address=address):
                ip_control_menu.addAction("Yeniden Başlat",lambda:self.restart_ping(address=address))
            else:
                ip_control_menu.addAction("Ping Başlat",lambda:self.start_ping(address=address))
            
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
    

    def update_Stats(self):
        global stats_list_global
        global headers
        self.tableTarget.clearContents()#silinmiş pingStat objelerinin verilerini tablodan kaldırır
        self.tableTarget.clearContents()
        
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
            last_result = summary.get("last result", "")
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
        
        self.ui.tableTarget.resizeColumnsToContents()
    def stopAllThreads(self):
        scapyPinger_global.stop_All()
    

    def start_ping(self, address:str):
        scapyPinger_global.start_task(address=address)
    def restart_ping(self, address:str):
        scapyPinger_global.restart_task(address=address)

    def set_table_headers(self):
        headers = list(get_data_keys())
        self.ui.tableTarget.setColumnCount(len(headers))
        self.ui.tableTarget.setHorizontalHeaderLabels(headers)
    def set_scapyPinger(self):
        global scapyPinger_global,stats_list_global
        scapyPinger_global.start_all()
        stats_list_global = scapyPinger_global.find_all_stats()
        
        
            


    def open_pingWindow(self):
        self.pingWindow = PingWindow(self,self.last_ip_list)
        self.pingWindow.pingTargetsReady.connect(self.update_Stats)
        
        self.pingWindow.show()
    def on_row_clicked(self, row, column):
        
        table = self.ui.tableTarget
        column_count = table.columnCount()

        values = []
        for col in range(column_count):
            item = table.item(row, col)
            if item:
                values.append(item.text())
            else:
                values.append("")

        

    def open_changeSettingsWindow(self, task:PingTask):
        if task:
            self.changeSetting = ChangeParameterWindow(task=task)
            
            self.changeSetting.show()
    
    def add_pings(self):
        pass
    def closeEvent(self, event):
        print("Uygulama kapanıyor, en son ki ip'ler txt'e aktarılıyor...")
          # ip.txt'ye kaydet
        if stats_list_global:  
            try:
                if isinstance(stats_list_global, dict):
                    ips_to_save = list(stats_list_global.keys())
                else:
                    ips_to_save = []

                with open('ip.txt', 'w', encoding='utf-8') as f:
                    f.write("\n".join(ips_to_save))

                print(f"ip.txt kaydedildi ({len(ips_to_save)} IP).")
            except Exception as e:
                print("ip.txt kaydedilemedi:", e)

        print("Uygulama kapanıyor, threadlerin kapanması bekleniyor")
        # Thread nesnelerini döngüyle durdur
        scapyPinger_global.stop_All()
         # thread kapanmasını bekle

        event.accept()  # pencerenin kapanmasına izin ver

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
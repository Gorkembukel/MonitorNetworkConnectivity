from dataclasses import dataclass
from subprocess import Popen
from QTDesigns.iperf_window import Ui_Dialog_iperfWindow


from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal , pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import QDialog,QApplication,QMainWindow,QTableWidgetItem

import sys
from typing import Dict

import source.iperf_Client_Wraper
from source.iperf_Client_Wraper import Client_Wrapper
from source.threads_for_iperf import Client_Runner,Client_Proces
from source.iperf_TestResult_Wrapper import TestResult_Wrapper, TestResult_Wrapper_sub

from iperf3 import TestResult

table_headers = source.iperf_Client_Wraper.table_headers
param_client = source.iperf_Client_Wraper.parameter_for_table_headers


@dataclass
class ClientInfo:
    subProces: Client_Proces
    result: TestResult_Wrapper_sub  


    def isResult(self):
        return True if self.result else False

class IperfWindow(QMainWindow):  # Yeni pencere Ping atmak için parametre alır

    iperf_client_data_signal = pyqtSignal()#

    def __init__(self, parent= None):
        super().__init__(parent)
        
        self.ui = Ui_Dialog_iperfWindow()
        self.ui.setupUi(self)  
        self.setWindowFlags((Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint))

        #signal bağlama
        self.iperf_client_data_signal.connect(Client_Wrapper.build_client_kwargs)
        #buton bağlama
        self.ui.pushButton_apply.clicked.connect(self.create_Client)
        

        #thread for clientleri dictonary olarak tutma
        self._client_threads: Dict[str, ClientInfo] = {}  # Anahtar: id (int), Değer: Client
    
    
        #tablo başlılarını oluşturma
        self.ui.tableWidget_clients.setColumnCount(len(table_headers))
        self.ui.tableWidget_clients.setHorizontalHeaderLabels(table_headers)
        self.ui.tableWidget_clients.setRowCount(1)
        #tablo için event filter kurma
        self.ui.tableWidget_clients.viewport().installEventFilter(self)
        self.ui.tableWidget_server.viewport().installEventFilter(self)
        #timer için
        self.iperf_window_timer = QTimer(self)
        self.iperf_window_timer.setInterval(600)  # 1000ms = 1 saniye#60fps için girilmesi gereken değr 17ms
        self.iperf_window_timer.timeout.connect(self.update_table)
        self.iperf_window_timer.start()


    def eventFilter(self, source, event) :
        if(event.type() == QtCore.QEvent.MouseButtonPress and
           event.buttons() == QtCore.Qt.RightButton and
           source is self.ui.tableWidget_clients.viewport()):
            

            # Tıklanan y koordinatına göre satır bulunur
            row = self.ui.tableWidget_clients.rowAt(event.pos().y())
            col = self.ui.tableWidget_clients.columnAt(event.pos().x())
            
            if row == -1 or col == -1:
                return super(IperfWindow, self).eventFilter(source, event)
            # Satır başlığındaki 'target' hücresini al
            header_item = self.ui.tableWidget_clients.item(row,0)#TODO burası ip adresinin olduğu hücreyi alıyor. Grafik değişire bura da değişmeli. DAha akılcı bir çözüm lazım, belki header listte arama yapılabilinir
            
            if header_item:
                hostName = header_item.text()
                
                
            else:
                hostName = None
                print("Satır başlığı yok")
            
            #Qmenu, ip_control_interface için action menusu
            iperf_client_control = QtWidgets.QMenu()
            iperf_client_control.addAction("Iperf başlat",lambda:self.start_iperf(hostName))          
                      
            iperf_client_control.exec(self.ui.tableWidget_clients.mapToGlobal(event.pos()))
        
        return super(IperfWindow, self).eventFilter(source, event)
    
    
    def add_client_to_threads(self, client_subproces: Client_Proces, hostName: str) -> bool:
        if hostName not in self._client_threads:
            thread = self._client_threads[hostName] = ClientInfo(subProces= client_subproces, result=None)# client, client_threads içine konduğunda Client_runner thread objesi init edilr ve kendini return eder
            
            return True  # Ekleme yapıldı
        else:
            print(f"{hostName}   zaten var mı")
            return False  # Zaten vardı, eklenmedi
    def start_iperf(self,Host_name:str):
        
        clientinfo = self.find_client(Host_name)
        print(f"arayüzde     {clientinfo.subProces} başlatma komutu verildi")
        if clientinfo:
            print(f"(arayüz )client var, başlatılacak ")                
            clientinfo.subProces.start_iperf()#BUG sistem değişince burayı da değiştir
            print(f"host  {clientinfo.subProces.client_HostName} aktif threadde")
    
    def find_client(self, keyValue):#clientinfo döndürür,dataclass içinde Client_proces ve testResult_wrapper_sub var
        return self._client_threads.get(keyValue)
    
    def create_Client(self):
        #parametlreleri alma
        self.server_hostname = self.ui.lineEdit_serverhostname.text() or None
        self.port            = self.ui.lineEdit_port.text() or None
        self.num_streams     = self.ui.lineEdit_numstreams.text() or None
        self.zerocopy        = self.ui.checkBox_zerocopy.isChecked()
        self.omit            = self.ui.lineEdit_omit.text() or None
        self.duration        = self.ui.lineEdit_duration.text() or None
        self.bandwidth       = self.ui.lineEdit_bandwidth.text() or None
        self.protocol        = self.ui.lineEdit_protocol.text() or None
        self.bulksize        = self.ui.lineEdit.text() or None
        
        client_runner= Client_Wrapper.build_client_kwargs(
            _server_hostname=self.server_hostname,
            _port=self.port,
            _num_streams=self.num_streams,
            _zerocopy=self.zerocopy,
            _omit=self.omit,
            _duration=self.duration,
            _bandwidth=self.bandwidth,
            _protocol=self.protocol,
            iperWindow=self)
        #client.worker.testresultWrapper.update_table_for_result_signal.connect(self.update_result_table)
        self.add_client_to_threads(hostName=self.server_hostname,client_subproces=client_runner)
            
    @pyqtSlot(Popen)#TODO burada client tarafı başarılı başlasada result boş dönüyor, bizle alakası olmayabillir
    def update_result_table(self, wrappertestResult:TestResult_Wrapper_sub):#TODO result table'ı almak yerine testResult_wrapper objelerini alacak şekilde değiştirildi
        clientİnfo=self.find_client(wrappertestResult.hostName)                                                                    # methodun adı değiştirilmeli
        clientİnfo.result = wrappertestResult
    def update_table(self):
        self.ui.tableWidget_clients.clearContents()
        self.ui.tableWidget_clients.setRowCount(len(self._client_threads))
        self.ui.tableWidget_clients.setColumnCount(len(table_headers))
        
        
        """# Başlıkları ayarla
        headers = [key.lstrip("_").replace("_", " ").title() for key in parameter_for_table_headers.keys()]
        self.ui.tableWidget_clients.setHorizontalHeaderLabels(headers)
        """
        # Satırları doldur
            # Her thread üzerinden client'a ulaşıp tabloyu doldur
        for row_index, (thread_name, clientinfo) in enumerate(self._client_threads.items()):
            client = getattr(clientinfo.subProces, "client", None)
            if client is None:
                continue  # Eğer thread içinde client yoksa geç

            for col_index, param_key in enumerate(param_client ):
                # Client üzerindeki property'i al, yoksa boş bırak
                try:
                    value = getattr(client, param_key, "")
                except Exception:
                    value = ""
                item = QTableWidgetItem(str(value))
                self.ui.tableWidget_clients.setItem(row_index, col_index,item)
        


def main():
    app = QApplication(sys.argv)
    window = IperfWindow()
    window.show()
    sys.exit(app.exec())
if __name__ =="__main__":
    main()
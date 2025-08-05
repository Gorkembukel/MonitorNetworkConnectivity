from iperf3 import Client,TestResult
import threading
import subprocess

from source.iperf_TestResult_Wrapper import TestResult_Wrapper

valid_fields = {
            "server_hostname",
            "port",
            "num_streams",
            "zerocopy",
            "omit",
            "duration",
            "bandwidth",
            "protocol",
            "blksize",
            "bind_address",
        }

class Worker(threading.Thread):
    def __init__(self, iperfWindow=None,client:Client =None):
        super().__init__()

        self.client = client
        self.testresultWrapper = TestResult_Wrapper(hostName=self.client.server_hostname)
        self.testresultWrapper.update_table_for_result_signal.connect(iperfWindow.update_result_table)#sinyal

        
    def run(self):
        result = None
        try:
            result = self.client.run()
            print("✅ client.run() çağrısı tamamlandı.")
            print("stderr output:", result)#BUG test
        except Exception as e:
            print("❌ client.run() içinde hata:", e)
            print("stderr output:", result)#BUG test

        if result is None:
            print("❌ Sonuç None döndü.")
        else:
            print("✅ TestResult geldi:", type(result))

        #self.testresultWrapper.setResult(result)

class Client_Runner():#Client_runner aslında thread değil, arayüzde buına ulaşılır clienti saklar, istenince thread açar böylece aynı client
                      # Tekrar tekrar kullanılabilir
    def __init__(self,iperWindow=None,**clientKwargs):
        super().__init__()

        self.clientKwargs = clientKwargs
        
        self.iperWindow = iperWindow
        self.worker:Worker= None
        self.client = Client()
        
        self.client.json_output = True

        for k, v in self.clientKwargs.items():
            if k in valid_fields:
                setattr(self.client, k, v)
            else:
                print(f"⚠️  Uyarı: iperf3.Client '{k}' parametresini tanımıyor, atlandı.")

    def start(self):
        if not self.worker:
            print(f"ilk kez başlatılıyor")

            self.worker = Worker(client=self.client,iperfWindow=self.iperWindow)
            self.worker.setDaemon(True)
            self.worker.run()#TODO 
        """ if not self.worker.is_alive() and  self.worker:
            
            print(f"tekrar başlatılıyor")
            self.client = None
            self.client = Client( )
            for k, v in self.clientKwargs.items():
                if k in valid_fields:
                    setattr(self.client, k, v)
                else:
                    print(f"⚠️  Uyarı: iperf3.Client '{k}' parametresini tanımıyor, atlandı.")

            self.worker = Worker(client=self.client,iperfWindow=self.iperWindow)
            self.worker.setDaemon(True)
            self.worker.run()"""
        
    
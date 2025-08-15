from iperf3 import Client,TestResult
import threading
import multiprocessing
from multiprocessing import Process, Queue

from source.Iperf.iperf_TestResult_Wrapper import TestResult_Wrapper

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
        
        
        
    def run(self):
        result = None
        try:
            result = self.client.run()
            print("✅ client.run() çağrısı tamamlandı.")
            
        except Exception as e:
            print("❌ client.run() içinde hata:", e)
            
        #BUG  debug için
        if result is None:
            print("❌ Sonuç None döndü.")
        else:
            print("✅ TestResult geldi:", type(result))
        return result
        #self.testresultWrapper.setResult(result)
class Client_Proces(Process ):
    def __init__(self, client:Client=None, iperfWindow= None, queue:Queue = None):
        super().__init__()
        self.worker = Worker(client=client, iperfWindow=iperfWindow)
        self.result = None
        self.q = queue
        
    def run(self):

        self.result = self.worker.run()
        
        #BUG
        print(f"proces bitti sinyal gönderildi {self.name}")
        return self.q.put(self.result)
    

class Client_Runner(threading.Thread):#Client_runner aslında thread değil, arayüzde buına ulaşılır clienti saklar, istenince thread açar böylece aynı client
                      # Tekrar tekrar kullanılabilir
    _active_processes = 0  # 🔢 Class-level sayaç
    def __init__(self,iperWindow=None,**clientKwargs):
        super().__init__()

        self.clientKwargs = clientKwargs
        self.q = Queue()
        self.iperWindow = iperWindow
        #self.worker:Worker= None
        self.proces:Client_Proces = None
        self.client = Client()
        self.testresultWrapper = TestResult_Wrapper(hostName=self.client.server_hostname)
        self.testresultWrapper.update_table_for_result_signal.connect(self.iperWindow.update_result_table)#si
        

        for k, v in self.clientKwargs.items():
            if k in valid_fields:
                setattr(self.client, k, v)
            else:
                print(f"⚠️  Uyarı: iperf3.Client '{k}' parametresini tanımıyor, atlandı.")

    def run(self):
        self.proces = Client_Proces(client=self.client,iperfWindow=self.iperWindow, queue = self.q)
        resultEmit = threading.Thread(target=self.signal_emit_proces_thread,daemon=True)
        self.proces.start()
        Client_Runner._active_processes +=1
        resultEmit.start()
        
        
        
        

        
    def signal_emit_proces_thread(self):       
        
        result = self.q.get()
        self.testresultWrapper.setResult(result)
        return result
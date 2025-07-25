# ping_thread.py
import threading
import time

from scapy.all import IP, ICMP, sr1
from source.PingStats import PingStats
from icmplib import ping as icmp_ping
class PingThread(threading.Thread):
    

    def __init__(self, target, duration, interval_ms, stats):
        super().__init__()
        self._stop_event = threading.Event()
        self.target = target
        self.duration = duration
        self.interval = interval_ms / 1000
        self.stop_time = time.time() + duration
        self.stats = stats
        self.isInfinite = False
        self._pause_start_time = 0
        stats.setTarget(target)
        self.isKill=False #threadi komple kapatır
    def _should_continue(self):
        return self.isInfinite or time.time() < self.stop_time
    def run(self):
        
        while not self.isKill:#TODO bu while hep dönecek, kill komutu gelene kadar threadi uykuda tutacak
            while self._should_continue() and not self._stop_event.is_set():#TODO burada sürekli metot çağırılıyor performans için değiştirilebilir
                # icmplib yöntemi
                send_time = time.time()
                print(f"intervaaaaaaaaaaaaaaaaaal {self.interval}")
                result = icmp_ping(self.target, count=1, timeout=1, interval=self.interval,privileged=False)
                if result.is_alive:
                    #rtt = result.avg_rtt
                    recv_time = time.time()
                    rtt = result._rtts.pop()
                    
                    self.stats.add_result(rtt)
                    print(f"[{self.target}] ✅ {rtt:.2f} ms (icmplib)")
                else:
                    self.stats.add_result(None)
                    print(f"[{self.target}] ❌ Timeout (icmplib)")
                time.sleep(self.interval)              
            if not self._should_continue() :# thread işlemini bitirip durdu ise threadi kapatır, kullanıcı tarafından durduruldu ise uykuya dalar
                self.isKill = True
                break
                #TODO durduktan sonra zaman kaybı sorunu, stop metodu içinde çözülmüştür
            
            #thread durduruldu geri uyandırlımayı bekliyor


            time.sleep(2)#FIXME uzun time sleep

    def getStats(self):
        return self.stats
    def setWhileCondition(self, isInfinite: bool):
        self.isInfinite = isInfinite
        

    def getWhileCondition(self):
        return self.whileCondition
    def stop(self,isToggle=False, isKill=False):
        if isToggle:
            if self._stop_event.is_set():
                paused_duration = time.time() - self._pause_start_time
                self.stop_time += paused_duration
                self._stop_event.clear()
            else:
                self._pause_start_time = time.time()
                self._stop_event.set()
        
        if isKill:
            self.isKill = isKill
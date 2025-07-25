# ping_thread.py
import threading
import time
from scapy.all import IP, ICMP, sr1
from source.PingStats import PingStats
from icmplib import ping as icmp_ping
class PingThread(threading.Thread):
    

    def __init__(self, address, duration,stats:PingStats,timeout=1 ,count=1,interval_ms=10,**kwargs):
        super().__init__()
        self._stop_event = threading.Event()
        self.address = address
        self.duration = duration
        self.stats = stats
        self.timeout = timeout
        self.interval = interval_ms / 1000
        self.isInfinite = False        
        self.stop_time = time.time() + duration        
        self.kwargs =kwargs
        self.count= count        
        self.depth = 1#bu dışarıdan değiştirilmemeli. Recursive thread açacağız döngüyü bununla kontrol ediyoruz.
        self.threadSpead:int =None


        self.stats.setaddress(address)
        
    def _should_continue(self):
        return self.isInfinite or time.time() < self.stop_time
    
    def run(self):

        while self._should_continue() and not self._stop_event.is_set():
            # icmplib yöntemi
            send_time = time.time()
            
            
            result = icmp_ping(self.address, count=self.count, timeout=1, interval=self.interval,privileged=False,**self.kwargs)#blocking type method, döngüyü bura bekletiyor, eğer ping gelmzesse timeout kadar döngü bekler ping atımı yavaşlar
            if result.is_alive:
                rtt = result._rtts.pop()
                
                
                
                self.stats.add_result(rtt)
                print(f"[{self.address}] ✅ {rtt:.2f} ms (icmplib)")
            else:
                self.stats.add_result(None)
                #print(f"[{self.address}] ❌ Timeout (icmplib)")
            self.threadSpead = (time.time()-send_time)*1000#interval ile kıyaslanacağı için ms olmalı
            self.stats.updateThreadLoopTime(self.threadSpead)
            self.call_self_if_needed()
    def getStats(self):
        return self.stats
    def setWhileCondition(self, isInfinite: bool):
        self.isInfinite = isInfinite
        

    def getWhileCondition(self):
        return self.whileCondition
    def stop(self):
        self._stop_event.set()
    def call_self_if_needed(self):
        MAX_DEPTH = 12  # Maksimum recursive thread seviyesi

        if self.threadSpead is None:
            return

        if self.threadSpead > self.interval and self.depth < MAX_DEPTH:
            print(f" depth-----------------{self.depth}")
            print(f"[{self.address}] 🔁 Spawning recursive PingThread (depth={self.depth + 1})")

            new_thread = PingThread(
                address=self.address,
                duration=self.stop_time - time.time(),  # Kalan süre
                stats=self.stats,
                timeout=self.timeout,
                count=self.count,
                interval_ms=self.interval * 1000,
                **self.kwargs
            )
            new_thread.depth = self.depth + 1
            new_thread.setWhileCondition(self.isInfinite)
            new_thread.start()
    """def runscpay(self):
        while self._should_continue() and self._stop_event: 
            packet = IP(dst=self.address)/ICMP()
            send_time = time.time()
            try:
                reply = sr1(packet, timeout=1, verbose=0)
                recv_time = time.time()
                if reply:
                    rtt = (recv_time - send_time) * 1000
                    self.stats.add_result(rtt)
                    print(f"[{self.address}] ✅ {rtt:.2f} ms")
                else:
                    self.stats.add_result(None)
                    print(f"[{self.address}] ❌ Timeout")
            except Exception as e:
                self.stats.add_result(None)
            print(f"[{self.address}] ⚠️ Error: {e}")"""
    
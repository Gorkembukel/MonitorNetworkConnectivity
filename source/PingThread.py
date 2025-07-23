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
        stats.setTarget(target)
        
    def _should_continue(self):
        return self.isInfinite or time.time() < self.stop_time
    def runscpay(self):
        while self._should_continue() and self._stop_event: 
            packet = IP(dst=self.target)/ICMP()
            send_time = time.time()
            try:
                reply = sr1(packet, timeout=1, verbose=0)
                recv_time = time.time()
                if reply:
                    rtt = (recv_time - send_time) * 1000
                    self.stats.add_result(rtt)
                    print(f"[{self.target}] ✅ {rtt:.2f} ms")
                else:
                    self.stats.add_result(None)
                    print(f"[{self.target}] ❌ Timeout")
            except Exception as e:
                self.stats.add_result(None)
                print(f"[{self.target}] ⚠️ Error: {e}")
    def run(self):

        while self._should_continue() and not self._stop_event.is_set():
            # icmplib yöntemi
            send_time = time.time()
            print(f"intervaaaaaaaaaaaaaaaaaal {self.interval}")
            result = icmp_ping(self.target, count=1, timeout=1, interval=self.interval,privileged=False)
            if result.is_alive:
                #rtt = result.avg_rtt
                recv_time = time.time()
                rtt = (recv_time - send_time) * 1000
                
                self.stats.add_result(rtt)
                print(f"[{self.target}] ✅ {rtt:.2f} ms (icmplib)")
            else:
                self.stats.add_result(None)
                print(f"[{self.target}] ❌ Timeout (icmplib)")
            

    def getStats(self):
        return self.stats
    def setWhileCondition(self, isInfinite: bool):
        self.isInfinite = isInfinite
        

    def getWhileCondition(self):
        return self.whileCondition
    def stop(self):
        self._stop_event.set()
    
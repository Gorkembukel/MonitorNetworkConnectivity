# ping_thread.py
import threading
import time
from scapy.all import IP, ICMP, sr1
from PingStats import PingStats

class PingThread(threading.Thread):
    def __init__(self, target, duration, interval_ms, stats: PingStats):
        super().__init__()
        self.target = target
        self.duration = duration
        self.interval = interval_ms / 1000
        self.stop_time = time.time() + duration
        self.stats = stats  # dışarıdan gelen istatistik nesnesi

        stats.setTarget(target)

    def run(self):
        while time.time() < self.stop_time:
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
            time.sleep(self.interval)

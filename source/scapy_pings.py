# scapy_pinger.py

from scapy.all import ICMP, IP, sr1
import ipaddress
import socket
import time
from PingThread import PingThread
from PingStats import PingStats


class ScapyPinger:
    def __init__(self, targets: list, duration: int = 10, interval_ms: int = 1000):
        self.targets = targets
        self.duration = duration
        self.interval_ms = interval_ms
        self.interval = interval_ms / 1000
        self.threads = []  # 🔁 Paralel thread'leri saklamak için
"""
    def is_valid_ip(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            pass
        try:
            socket.gethostbyname(ip)
            return True
        except Exception:
            return False
"""
    def is_valid_ip(ip_str: str) -> bool:
    # IP formatı geçerli mi?
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        pass

    # DNS çözümlemesi yapılabiliyor mu?
    try:
        socket.gethostbyname(ip_str)
        return True
    except socket.error:
        return False

    def run(self, parallel: bool = False, stats_map: dict = None):
        """
        :param parallel: True ise PingThread ile paralel çalışır
        :param stats_map: her hedef için PingStats objesi tutan dict (key = target)
        """
        for target in self.targets:
            if not self.is_valid_ip(target):
                print(f"🚫 Invalid target skipped: {target}")
                continue

            if parallel:
                if stats_map is None or target not in stats_map:
                    print(f"⚠️ Missing stats for target {target}, skipping...")
                    continue
                thread = PingThread(target, self.duration, self.interval_ms, stats_map[target])
                thread.start()
                self.threads.append(thread)
            else:
                self._sequential_ping(target)

    def _sequential_ping(self, target: str):
        print(f"⏱️ Pinging {target} for {self.duration} seconds...\n")

        end_time = time.time() + self.duration
        sent = 0
        received = 0

        while time.time() < end_time:
            packet = IP(dst=target) / ICMP()
            sent += 1
            t0 = time.time()
            try:
                reply = sr1(packet, timeout=1, verbose=0)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                continue

            t1 = time.time()

            if reply:
                rtt = (t1 - t0) * 1000  # ms
                received += 1
                print(f"✅ Reply from {target} in {rtt:.2f} ms")
            else:
                print(f"❌ Timeout from {target}")

            time.sleep(self.interval)

        print("\n--- Statistics ---")
        print(f"Sent     : {sent}")
        print(f"Received : {received}")
        print(f"Loss     : {(sent - received) / sent * 100:.1f}%")

    def wait_for_all(self):
        """Tüm threadlerin bitmesini bekler"""
        for thread in self.threads:
            thread.join()

    def active_threads(self):
        """Şu an çalışan thread sayısı"""
        return sum(t.is_alive() for t in self.threads)

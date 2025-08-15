import re
import threading
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


from source.ping.PingStats import PingStats

class Std_to_Pingstat(QObject):
    signal_to_mainWindow = pyqtSignal(object)
    def __init__(self, clientWrapper:object,target_address:str,stdout_str:str):
        super().__init__()
        self.clientWrapper = clientWrapper
        self.target_address = target_address
        self.stdout_str = stdout_str
        self.sshClient_ip =clientWrapper.hostname
        
        
        self.stats = PingStats(self.target_address) 
        
        self._buf = ""
        self._t: Optional[threading.Thread] = None
        self._stop = threading.Event()
        
        self._re_time = re.compile(r'time[=<]?\s*(\d+(?:\.\d+)?)\s*ms', re.I)
        # Linux/mac ping ipuçları: icmp_seq/icmp_req vb. (erken eleme için)
        self._re_icmp_hint = re.compile(r'icmp[_\s-]?(seq|req|id)', re.I)

    def parse_stdout_to_rtt(self):
         
        data = (self._buf + self.stdout_str).replace("\r\n", "\n").replace("\r", "\n")

        # newline’a göre ayır; sondaki eksik satırı buffer’da tut
        if data.endswith("\n"):
            lines = data.split("\n")[:-1]  # son eleman boş satır
            self._buf = ""
        else:
            parts = data.split("\n")
            self._buf = parts[-1]
            lines = parts[:-1]

        for line in lines:
            self._maybe_update_target(line)
            rtt = self._extract_rtt_ms(line)
            if rtt is not None and self.stats is not None:
                # PingStats’a ekle (metod adın farklıysa uyarlayabilirsin)
                try:
                    self.stats.add_result(rtt=rtt)
                except AttributeError:
                    pass
    def _maybe_update_target(self, line: str):
        # Zaten hedef biliniyorsa dokunma
        if self.target_address !="unkown":
            return

        m = re.search(r"from\s+(?P<ip>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\b", line)
        if m:
            self.target_address = m.group("ip")
            self.stats = PingStats(self.target_address)  # yeni hedefle yeniden başlat
    def _extract_rtt_ms(self, line: str) -> Optional[float]:
        # hızlı eleme (false negative istemiyorsan bu kısmı kaldır)
        if "time" not in line.lower() and not self._re_icmp_hint.search(line):
            return None
        m = self._re_time.search(line)
        if not m:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None
    def get_stats(self):
        return self.stats
    def start(self):
        """
        Arka plan parser thread'ini başlat.
        """
        if self._t is not None and self._t.is_alive():
            return
        self._stop.clear()
        self._t = threading.Thread(target=self.parse_stdout_to_rtt, daemon=True)
        self._t.start()
    
    def stop(self):
        self._stop.set()
        if self._t is not None:
            self._t.join(timeout=1.0)
        self._t = None
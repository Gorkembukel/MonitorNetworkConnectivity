# ping_stats.py
from typing import List, Optional
from statistics import mean, stdev

"""
Bu class programdaki bütün verileri tutup işlemek ve grafiğe dökmek içindir
"""

class PingStats:
    def __init__(self, target: str):
        self._target = target
        self._rtts: List[Optional[float]] = []  # RTT'ler, timeout için None tutulur
    def __init__(self):
        self._rtts: List[Optional[float]] = []  # RTT'ler, timeout için None tutulur

    def add_result(self, rtt: Optional[float]):
        self._rtts.append(rtt)

    @property
    def target(self):
        return self._target

    @property
    def sent(self):
        return len(self._rtts)

    @property
    def received(self):
        return len([r for r in self._rtts if r is not None])

    @property
    def failed(self):
        return self.sent - self.received

    @property
    def success_rate(self):
        return (self.received / self.sent * 100) if self.sent else 0.0

    @property
    def average_rtt(self):
        valid = [r for r in self._rtts if r is not None]
        return round(mean(valid), 2) if valid else None

    @property
    def min_rtt(self):
        valid = [r for r in self._rtts if r is not None]
        return min(valid) if valid else None

    @property
    def max_rtt(self):
        valid = [r for r in self._rtts if r is not None]
        return max(valid) if valid else None

    @property
    def jitter(self):
        valid = [r for r in self._rtts if r is not None]
        return round(stdev(valid), 2) if len(valid) > 1 else 0.0

    @property
    def last_result(self):
        if not self._rtts:
            return "No Data"
        return "Success" if self._rtts[-1] is not None else "Timeout"
    def setTarget(self,target):
        self._target = target


    def summary(self):
        return {
            "target": self.target,
            "sent": self.sent,
            "received": self.received,
            "failed": self.failed,
            "success_rate": round(self.success_rate, 2),
            "avg_rtt": self.average_rtt,
            "min_rtt": self.min_rtt,
            "max_rtt": self.max_rtt,
            "jitter": self.jitter,
            "last_result": self.last_result
        }

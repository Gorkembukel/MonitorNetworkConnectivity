import threading
import time
from source.PingStats import PingStats

class PingThread(threading.Thread):
    def __init__(self, target, duration, interval_ms, stats):
        super().__init__()
        self.target = target
        self.duration = duration
        self.interval = interval_ms / 1000
        self.stop_time = time.time() + duration
        self.stats = stats
        self.whileCondition = time.time() < self.stop_time
        stats.setTarget(target)
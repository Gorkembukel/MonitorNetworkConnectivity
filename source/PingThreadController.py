# scapy_pinger.py

from scapy.all import ICMP, IP, sr1
import time
import ipaddress
import socket
from source.PingThread import PingThread
from source.PingStats import PingStats


def is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        pass
    try:
        socket.gethostbyname(ip_str)
        return True
    except socket.error:
        return False


class PingTask:
    def __init__(self, target: str, duration: int, interval_ms: int):
        self.target = target
        self.duration = duration
        self.interval_ms = interval_ms
        self.stats = PingStats(target)
        self.thread = None  # PingThread bu

    def start(self):
        self.thread = PingThread(self.target, self.duration, self.interval_ms, self.stats)
        self.thread.start()

    def is_alive(self):
        return self.thread.is_alive() if self.thread else False

    def summary(self):
        return self.stats.summary()

    def wait(self):
        if self.thread:
            self.thread.join()


class ScapyPinger:
    def __init__(self):
        self.tasks = {}  # key = target, value = PingTask
        self.stats_list = []
    def add_target(self, target: str, duration: int = 10, interval_ms: int = 1000):
        if not is_valid_ip(target):
            print(f"🚫 Invalid target skipped: {target}")
            return False

        if target in self.tasks:
            print(f"⚠️ Target already exists: {target}")
            return False

        task = PingTask(target, duration, interval_ms)
        self.tasks[target] = task
        return True

    def start_all(self):
        for task in self.tasks.values():
            if not task.is_alive():
                task.start()

    def wait_for_all(self):
        for task in self.tasks.values():
            task.wait()

    def get_active_count(self):
        return sum(task.is_alive() for task in self.tasks.values())

    def get_stats_map(self):
        return {target: task.stats for target, task in self.tasks.items()}

    def get_task(self, target):
        return self.tasks.get(target)

    def add_and_start(self, target: str, duration: int = 10, interval_ms: int = 1000):
        if self.add_target(target, duration, interval_ms):
            self.tasks[target].start()

    def find_all_stats(self):
        """
        Oluşturulmuş tüm PingTask'ların PingStats nesnelerini döndürür.
        :return: List[PingStats]
        """
        
        for task in self.tasks.values():
            stats = task.stats
            self.stats_list.append(stats)
        return self.stats_list  
    def get_stats_map(self):
        """
        Her hedef için PingStats nesnesini target -> PingStats dict olarak döndürür.
        :return: Dict[str, PingStats]
        """
        return {target: task.stats for target, task in self.tasks.items()}

    def show_all_updated(self):        
        self.find_all_stats()          
    
        for stat in self.stats_list:
            stat.all_graph(True)


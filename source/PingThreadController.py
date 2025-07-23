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
    def __init__(self, target: str, duration: int, interval_ms: int, isInfinite: bool):
        self.target = target
        self.duration = duration
        self.interval_ms = interval_ms
        self.isInfinite = isInfinite
        self.stats = PingStats(target)
        self.thread = None  # PingThread bu

    def start(self):
        self.thread = PingThread(self.target, self.duration, self.interval_ms, self.stats)
        if self.isInfinite:
            self.thread.setWhileCondition(self.isInfinite)
        self.thread.start()
    def stop(self):
        if self.thread:
            self.thread.stop()
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
        self.target_dict = {}#her ip key olup istenen çalışma parametreleri value olacak
        self.stats_list = []
    def add_task(self, target: str,isInfinite: bool, duration: int = 10, interval_ms: int = 1000):
        if not is_valid_ip(target):
            print(f"🚫 Invalid target skipped: {target}")
            return False  
    

        if target in self.tasks:#TODO bu kaldırılabilir belki
            print(f"⚠️ Target already exists: {target}")
            return False

        task = PingTask(target, duration, interval_ms, isInfinite=isInfinite)
        self.tasks[target] = task
        return True
    def target_dict_to_add_task(self):
        targets = self.target_dict
        for target, config in self.target_dict.items():
            self.add_task(
                target=target,
                duration=config['duration'],
                interval_ms=config['interval_ms'],
                isInfinite=config['isInfinite']
            )


    def add_targetList(self, targets: list, interval_ms: int, duration: int, byte_size: int, isInfinite: bool):
        

        for target in targets:
            self.target_dict[target] = {
                'interval_ms': interval_ms,
                'duration': duration,
                'byteSize': byte_size,
                'isInfinite': isInfinite

            }


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
        if self.task(target, duration, interval_ms):
            self.tasks[target].start()

    def find_all_stats(self):
        self.stats_list = []  # ❗ Temizle
        for task in self.tasks.values():
            self.stats_list.append(task.stats)
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
    
    def stop_All(self):
        for task in self.tasks.values():  #  sadece value'larla ilgileniyoruz
            task.stop()


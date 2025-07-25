# scapy_pinger.py

from scapy.all import ICMP, IP, sr1
import time
import ipaddress
import socket
from source.PingThread import PingThread
from source.PingStats import PingStats
from typing import Dict, List

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
    def __init__(self, stat_list:Dict,target: str, duration: int, interval_ms: int, isInfinite: bool):
        self.target = target
        self.duration = duration
        self.interval_ms = interval_ms
        self.isInfinite = isInfinite
        self.stats = PingStats(target)
        stat_list[self.target] = self.stats

        self.thread = None  # PingThread bu

    def start(self):
        self.thread = PingThread(self.target, self.duration, self.interval_ms, self.stats)
        if self.isInfinite:
            self.thread.setWhileCondition(self.isInfinite)
        self.thread.start()
    def stop(self,**kargs):
        print("stop_address kargs:", kargs)#FIXME geçici
        if self.thread:
            self.thread.stop(**kargs)
    def is_alive(self):
        return self.thread.is_alive() if self.thread else False

    def summary(self):
        return self.stats.summary()

    def wait(self):
        if self.thread:
            self.thread.join()


class ScapyPinger:
    def __init__(self):
        self.tasks: Dict[str, PingTask] = {}  # key = target, value = PingTask
        self.target_dict = {}#her ip key olup istenen çalışma parametreleri value olacak
        self.stats_list: Dict[str, PingStats] = {}# FIXME normalde liste burası
        
    def add_task(self, target: str,isInfinite: bool, duration: int = 10, interval_ms: int = 1000):
        if not is_valid_ip(target):
            print(f"🚫 Invalid target skipped: {target}")
            return False  
    

        if target in self.tasks:#TODO bu kaldırılabilir belki
            print(f"⚠️ Target already exists: {target}")
            return False

        task = PingTask(target=target,stat_list= self.stats_list, duration=duration,interval_ms= interval_ms, isInfinite=isInfinite)
        self.tasks[target] = task
        return True
    def target_dict_to_add_task(self):
        targets = self.target_dict
        for target, config in targets.items():
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
        self.target_dict_to_add_task()

    def start_all(self):
        for task in self.tasks.values():
            if not task.is_alive():
                task.start()

    def wait_for_all(self):
        for task in self.tasks.values():
            task.wait()

    def get_active_count(self):
        return sum(task.is_alive() for task in self.tasks.values())

    """def get_stats_map(self):
        return {target: task.stats for target, task in self.tasks.items()}"""

    def get_task(self, target):
        return self.tasks.get(target)

    def add_and_start(self, target: str, duration: int = 10, interval_ms: int = 1000):
        if self.task(target, duration, interval_ms):
            self.tasks[target].start()

    def find_all_stats(self): #FIXME adı gui kodunda ve vurada değişmeli
       
        return self.stats_list

    
    def delete_stats(self, address):
        if address in self.stats_list:
            del self.stats_list[address]
            del self.tasks[address]
        
    def show_all_updated(self):        
        self.find_all_stats()          
    
        for stat in self.stats_list:#FIXME keyvalu lara dikkat eğer hala dictonary ise stat_list
            stat.all_graph(True)
    def stop_address(self, address: str = "", **kargs):

        if address in self.tasks:
            self.tasks[address].stop(**kargs)
        else:
            print(f"PingThreadController Stop_address metodu__Adres bulunamadı: {address}")

    def stop_All(self):
        for task in self.tasks.values():  #  sadece value'larla ilgileniyoruz
            task.stop()


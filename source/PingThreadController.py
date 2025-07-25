# scapy_pinger.py

from scapy.all import ICMP, IP, sr1
import time
import ipaddress
import socket
from source.PingThread import PingThread, Scheduler
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
    def __init__(self, address,isInfinite: bool ,duration,timeout=1 ,interval_ms=10,**kwargs):
        self.address = address
        self.duration = duration
        self.interval_ms = interval_ms
        self.isInfinite = isInfinite
        self.stats = PingStats(address)
        self.thread = None  # PingThread bu
        self.kwargs = kwargs
    def start(self):
        self.thread = Scheduler(address=self.address,duration= self.duration,interval_ms= self.interval_ms,stats= self.stats,**self.kwargs )
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

    def get_active_thread_count(self):
        if self.thread:
            return self.thread.get_active_ping_thread_count()
        return 0
class ScapyPinger:
    def __init__(self):
        self.tasks = {}  # key = address, value = PingTask
        self.address_dict = {}#her ip key olup istenen çalışma parametreleri value olacak
        self.stats_list = []
    def add_task(self, address: str,isInfinite: bool, duration: int = 10, interval_ms: int = 1000, **kwargs):
        if not is_valid_ip(address):
            print(f"🚫 Invalid address skipped: {address}")
            return False  
    

        if address in self.tasks:#TODO bu kaldırılabilir belki
            print(f"⚠️ address already exists: {address}")
            return False

        task = PingTask(address= address,duration= duration,interval_ms= interval_ms, isInfinite=isInfinite, **kwargs)
        self.tasks[address] = task
        return True
    def address_dict_to_add_task(self):#parametreleri ile kayıt edilmiş address'ler tasklere eklenir
        for address, config in self.address_dict.items():
            self.add_task(address=address, **config)
    def sanitize_kwargs_for_icmp_ping(self, kwargs: dict) -> dict:
        """
        icmplib.ping() fonksiyonunun desteklediği ve None olmayan parametreleri filtreler.

        :param kwargs: Kullanıcıdan gelen tüm keyword argümanlar
        :return: Sadece icmplib.ping ile uyumlu ve None olmayan argümanları içeren dict
        """
        allowed_keys = {
            'count',
            'interval',
            'timeout',
            'id',
            'source',
            'family',
            'privileged',
            'payload',
            'payload_size',
            'traffic_class'
        }

        return {
            key: value for key, value in kwargs.items()
            if key in allowed_keys and value is not None
        }
    def add_addressList(self, addresses,isInfinite: bool ,duration,timeout=1 ,interval_ms=10,**kwargs):#TODO metotlara hangi parametreler girilebileceğini bura belirliyor
        cleanKwargs = self.sanitize_kwargs_for_icmp_ping(kwargs)

        for address in addresses:
            self.address_dict[address] = {
                'duration': duration,
                'interval_ms': interval_ms,
                'timeout': timeout,
                'isInfinite': isInfinite,
                **cleanKwargs  # 🔁 örn: payload_size gibi parametreler
            }
        self.address_dict_to_add_task()# bu buradan kaldırılıp guı tarafında da kullanılabilir

    def start_all(self):
        for task in self.tasks.values():
            if not task.is_alive():
                task.start()

    def wait_for_all(self):
        for task in self.tasks.values():
            task.wait()

    def get_active_count(self):#TODO
        #return sum(task.is_alive() for task in self.tasks.values())#Sadece scapy pingerın çağırdığı threadleri ölçer
        
        return sum(task.get_active_thread_count() for task in self.tasks.values())#scheluderların threadlerini de hesaba katar


    def get_stats_map(self):
        return {address: task.stats for address, task in self.tasks.items()}

    def get_task(self, address):
        return self.tasks.get(address)

    def add_and_start(self, address: str, duration: int = 10, interval_ms: int = 1000):
        if self.task(address, duration, interval_ms):
            self.tasks[address].start()

    def find_all_stats(self):
        self.stats_list = []  # ❗ Temizle
        for task in self.tasks.values():
            self.stats_list.append(task.stats)
        return self.stats_list

    def get_stats_map(self):
        """
        Her hedef için PingStats nesnesini address -> PingStats dict olarak döndürür.
        :return: Dict[str, PingStats]
        """
        return {address: task.stats for address, task in self.tasks.items()}

    def show_all_updated(self):        
        self.find_all_stats()          
    
        for stat in self.stats_list:
            stat.all_graph(True)
    
    def stop_All(self):
        for task in self.tasks.values():  #  sadece value'larla ilgileniyoruz
            task.stop()


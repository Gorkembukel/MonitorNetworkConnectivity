from __future__ import annotations
from abc import ABC, abstractmethod
import subprocess
import threading
from typing import List
import time
from icmplib import ping as icmp_ping
from datetime import datetime
import threading
import time
import os
import socket
from playsound import playsound
from icmplib.sockets import ICMPv4Socket
from icmplib.models import ICMPRequest
from icmplib.exceptions import ICMPSocketError, TimeoutExceeded, ICMPError
import multiprocessing
from source.PingStats import PingStats
# Bu dosyanın  bulunduğu dizini al
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#  klasörünün bir üstüne çık, source/targets.txt'yi hedefle
sound_path = os.path.join(BASE_DIR, "..","audio_data","ping.wav")

# Mutlak yola çevir (temizlik için)
sound_path = os.path.abspath(sound_path)


class Context():
    """
    The Context defines the interface of interest to clients.
    """

    def __init__(self, strategy: Strategy) -> None:
        """
        Usually, the Context accepts a strategy through the constructor, but
        also provides a setter to change it at runtime.
        """

        self._strategy = strategy

    @property
    def strategy(self) -> Strategy:
        """
        The Context maintains a reference to one of the Strategy objects. The
        Context does not know the concrete class of a strategy. It should work
        with all strategies via the Strategy interface.
        """

        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        """
        Usually, the Context allows replacing a Strategy object at runtime.
        """

        self._strategy = strategy

    def do_some_algorithm(self, **kwargs) -> None:
        """
        The Context delegates some work to the Strategy object instead of
        implementing multiple versions of the algorithm on its own.
        """
      
        # ...

        

        # ...

        print("Ping başlatılıyor...")
        self.strategy.startPing(**kwargs)
    def update_parameters(self, **kwargs):
        self.strategy.update_parameter(**kwargs)

class Strategy(ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The Context uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abstractmethod
    def startPing(self, **kwargs):
        pass
    @abstractmethod
    def stop(self, **kwargs):
        pass
    @abstractmethod
    def getEnd_datetime(self,**kwargs):
        pass
    @abstractmethod
    def update_parameter(self,**kwargs):
        pass
"""
Concrete Strategies implement the algorithm while following the base Strategy
interface. The interface makes them interchangeable in the Context.
"""



class Worker(threading.Thread):
    

    def __init__(self, address, stats,duration,isInfinite =False ,end_datetime = None,count=1, interval_ms=1, timeout=2, id=None, source=None,
        family=None, privileged=True, **kwargs):
        super().__init__()
        self._stop_event = threading.Event()

        self.address = address
        self.stats = stats
        self.duration = duration
        self.isInfinite = isInfinite
        self.end_datetime = end_datetime
        self.count = count
        self.interval_ms = interval_ms / 1000
        self.timeout = timeout
        self.id = id
        self.source = source
        self.stop_time = time.time() + duration if duration else None
        self.family = family
        self.privileged = privileged
        self.kwargs = kwargs
        self.isBeep = False
        self._pause_start_time = 0
        stats.setAddress(address)
        self.isKill=False #threadi komple kapatır
    def _should_continue(self):#FIXME burada is kill tanımlı o yüzden diğer yerlerden kadlırabiliriz gibi
        print("kill öncesi")
        if self.isKill:
            return False

        now = datetime.now()
        print(f"date  öncesi {now}")
        # Öncelik: end_datetime varsa ve geçilmişse dur
        if self.end_datetime:  # 🔴 Bitiş zamanı varsa onu esas al
            return now < self.end_datetime
        print(f"infinite öncesi    {self.isInfinite}")
        if self.isInfinite:
            return True

        return time.time() < self.stop_time  # duration süresi dolmadıysa devam

    def run(self):
        
        while not self.isKill:#TODO bu while hep dönecek, kill komutu gelene kadar threadi uykuda tutacak
            while self._should_continue() and not self._stop_event.is_set():#TODO burada sürekli metot çağırılıyor performans için değiştirilebilir
                # icmplib yöntemi
                
                send_time = time.time()
                print(f"[{self.address}] ➡️ icmp_ping kwargs: {self.kwargs}")
                result = icmp_ping(address=self.address, count=self.count,interval=self.interval_ms, timeout=self.timeout, id=self.id, source=self.source,
        family=self.family, privileged=self.privileged, **self.kwargs)
                if result.is_alive:
                    #rtt = result.avg_rtt
                    
                    rtt = result._rtts.pop()
                    
                    self.stats.add_result(rtt, time.time() + 10800) #    istanbula göre UTC 3
                    
                    #ses için
                    print(f"beepy dışı {self.isBeep}")
                    if self.isBeep:
                        print('\a')
                    print(f"[{self.address}] ✅ {rtt:.2f} ms (icmplib)")
                else:
                    self.stats.add_result(None)
                    print(f"[{self.address}] ❌ Timeout (icmplib)")
                recv_time = time.time()
                reply_time = recv_time -send_time
                sleep_time = self.interval_ms - reply_time# threadin tam olarak interval kadar uyuması için ping atma süresi kadar çıkartıyorum çünkü zaten o kadar zaman geçiyo             
                if sleep_time > 0:
                    time.sleep(sleep_time) 
                endOf_while = time.time()
                pulse = endOf_while - send_time
                self.stats.update_rate(pulse)
            if not self._should_continue() :# thread işlemini bitirip durdu ise threadi kapatır, kullanıcı tarafından durduruldu ise uykuya dalar
                self.isKill = True
                break
                #TODO durduktan sonra zaman kaybı sorunu, stop metodu içinde çözülmüştür
            
            #thread durduruldu geri uyandırlımayı bekliyor


            time.sleep(2)#FIXME uzun time sleep
        print("döngünün dışına")
    def getStats(self):
        return self.stats
    def setWhileCondition(self, isInfinite: bool):
        self.isInfinite = isInfinite
        

    def getWhileCondition(self):
        return self.whileCondition
    def stop(self,isToggle=False, isKill=False):
        if isToggle:
            if self._stop_event.is_set():
                paused_duration = time.time() - self._pause_start_time
                self.stop_time += paused_duration
                self._stop_event.clear()
            else:
                self._pause_start_time = time.time()
                self._stop_event.set()
        
        if isKill:
            self.isKill = isKill
    def getEnd_datetime(self):
        return self.end_datetime
    def update_parameters(self, interval_ms=None, end_datetime=None, timeout=None, count=None, isInfinite=None, **kwargs):
        if interval_ms is not None:
            self.interval_ms = interval_ms / 1000
        if end_datetime is not None:
            self.end_datetime = end_datetime
        if timeout is not None:
            self.timeout = timeout
        if count is not None:
            self.count = count
        if isInfinite is not None:
            self.isInfinite = isInfinite
        if kwargs:
            self.kwargs.update(kwargs)
    def toggleBeep(self):
        if self.isBeep:
            self.isBeep=False
        else:self.isBeep=True

        print(f"[{self.address}] 🔁 Thread parametreleri güncellendi.")



class LowRatePing(Strategy):
    def __init__(self):
        self.stop_event = threading.Event()
        self.isKill=False
    def startPing(self, **kwargs):
        self.thread = Worker(**kwargs)       
        
        self.thread.start()
        print(f" arka planda başlatıldı.")
        return self.thread  # ✅ thread'i döndür
    
    def toggleBeep(self):
        print("lowrate strtategy toggle beep içi")#BUG  temizle 
        self.thread.toggleBeep()
    def update_parameter(self, **kwargs):
        self.thread.update_parameters(**kwargs)
    def getEnd_datetime(self):
        self.thread.getEnd_datetime()

    def stop(self,**kwargs):
        self.thread.stop(**kwargs)
      
class HighRatePing(Strategy):
    def __init__(self, max_buffer_mb=64):
        self.MAX_BUFFER_SIZE = max_buffer_mb * 1024 * 1024
        self.IDENTIFIER = os.getpid() & 0xFFFF
        self.sequence_number = 0
        self.send_buffer_size = 5 * 64 * 1024
        self.request_times = {}
        self.stop_event = multiprocessing.Event()

        self.sender_thread = None
        self.receiver_thread = None
        self.process = None  # 🔴 Yeni eklendi
        self.processes = []
    def getEnd_datetime(self):
        pass
    def startPing(self, address, interval_ms, payload_size, stats,num_processes,isKill_Mod =False,**kwargs):
        print("🚀 HighRatePing process içinde başlatılıyor...")
        self.isKill_Mod = isKill_Mod
        self.address = address
        self.interval_ms = interval_ms / 1000
        self.payload_size = payload_size
        self.stats = stats

        
        for i in range(num_processes):
            proc = multiprocessing.Process(
                target=self._start_threads_in_process,
                args=(i, num_processes)
            )
            proc.start()
            self.processes.append(proc)

    def _start_threads_in_process(self, proc_index, total_processes):
        
        

        print(f"[Process #{proc_index}] PID={os.getpid()} ✅ Başlatıldı.")

        self.sock = ICMPv4Socket()
        self.sock._sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.send_buffer_size)

        self.sender_thread = threading.Thread(target=self._sender, args=(proc_index,), daemon=True)
        self.receiver_thread = threading.Thread(target=self._receiver, args=(proc_index,), daemon=True)

        self.sender_thread.start()
        self.receiver_thread.start()

        self.sender_thread.join()
        self.receiver_thread.join()

    def stop(self):
        print("🛑 HighRatePing durduruluyor...")
        self.stop_event.set()

        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join()
            print("✅ Process durdu.")

    def is_alive(self):
        return self.process and self.process.is_alive()

    def _sender(self, proc_index):
            count = 1
            while not self.stop_event.is_set():
                self.sequence_number += 1
                send_time = time.time()
                request = ICMPRequest(
                    destination=self.address,
                    id=(self.IDENTIFIER + proc_index),  # Her process farklı ID alsın
                    sequence=self.sequence_number,
                    payload_size=self.payload_size
                )
                request._time = time.time()
                self.request_times = {request.sequence: request._time}  # sadeleştirdik

                try:
                    self.sock.send(request)
                    print(f"[Proc {proc_index}] [>] Ping #{count} sent (seq={request.sequence})")
                    count += 1
                except Exception as e:
                    print(f"[Proc {proc_index}] [!] Send error: {e}")

                now = time.time()
                sleep_time = (self.interval_ms / 1000) - (now - send_time)
                if sleep_time > 0 and not self.isKill_Mod :                  
                    
                    time.sleep(sleep_time)

    def _receiver(self, proc_index):
        while not self.stop_event.is_set():
            try:
                reply = self.sock.receive(timeout=1)
                if reply is None or reply.id != (self.IDENTIFIER + proc_index):
                    continue
                rtt = (reply.time - self.request_times.get(reply.sequence, reply.time)) * 1000
                self.stats.add_result(rtt)
                print(f"[Proc {proc_index}] [<] Reply seq={reply.sequence} RTT={rtt:.2f} ms")
            except Exception as e:
                print(f"[Proc {proc_index}] [!] Receive error: {e}")

    def stop(self):
        print("🛑 Tüm prosesler durduruluyor...")
        self.stop_event.set()
        for proc in self.processes:
            if proc.is_alive():
                proc.terminate()
                proc.join()
        self.processes.clear()
        print("✅ Hepsi durdu.")
    def update_parameter(self,**kwargs):
        pass
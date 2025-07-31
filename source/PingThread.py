# ping_thread.py
from datetime import datetime
import threading
import time


from source.PingStrategy import  Context,LowRatePing, HighRatePing
from source.PingStats import PingStats
from icmplib import ping as icmp_ping
import struct
from icmplib.sockets import ICMPv4Socket
from icmplib.models import ICMPRequest
import os
class Behivior():
    criticle_threshHold_ms = 1# eğer interval bunun altında ise standart ping yetmez

    core_count = os.cpu_count()
    max_core = core_count -1
    def __init__(self,address, stats,duration,isKill_Mod=False,isInfinite =False ,end_datetime = None,count=1, interval_ms=1, timeout=2, id=None, source=None,
        family=None, privileged=True, **kwargs):
        self.isKill_Mod = isKill_Mod

        self.interval_ms = interval_ms
        self.params = {
        "address": address,
        "stats": stats,
        "duration": duration,
        "interval_ms": interval_ms,
        "isInfinite": isInfinite,
        "end_datetime": end_datetime,
        "count": count,
        "timeout": timeout,
        "id": id,
        "source": source,
        "family": family,
        "privileged": privileged,
        
        **kwargs  # kwargs ekle
        }
        
        
        self.context = self.decide_strategy()
        #self.thread = self.context.strategy.startPing(**params)  # ✅ doğrudan al
        self.context.do_some_algorithm(**self.params)
    def update_parameters(self,**kwargs):
        self.context.update_parameters(**kwargs)

       

    def decide_strategy(self) -> Context:
        if Behivior.criticle_threshHold_ms < self.interval_ms and not self.isKill_Mod:
            return Context(LowRatePing())
        
        else:
            if self.isKill_Mod:
                self.params["num_processes"]=Behivior.max_core
                self.params["isKill_Mod"]=True   #HACK test için
                
            else:
                self.params["num_processes"]= 1
            return Context(HighRatePing())
        
    def takeComand():
        pass
    def optimizeBuffersize():
        pass
    def getEnd_datetime(self):
        return self.context.strategy.getEnd_datetime()
    # bir threadin yerine geçirdiğimiz için thread fonksiyonları tanımlıyoruz sistemin geri kalanında değişime gitmemek için
    def stop(self,**kwargs):
        self.context.strategy.stop(**kwargs)
        
    def is_alive(self): # FIXME geçici
        return True
    def start(self):#
        pass
    def toggleBeep(self):
        if isinstance(self.context.strategy, LowRatePing):
            self.context.strategy.toggleBeep()


class PingThread(threading.Thread):
    

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
        self.startTime = time.time()
        self.stop_time = self.startTime + duration if duration else None
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
                    self.stats.add_result(300, time.time() + 10800)
                    print(f"[{self.address}] ❌ Timeout (icmplib)")
                recv_time = time.time()
                reply_time = recv_time -send_time
                sleep_time = self.interval_ms# threadin tam olarak interval kadar uyuması için ping atma süresi kadar çıkartıyorum çünkü zaten o kadar zaman geçiyo             
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
    def update_parameters(self, interval_ms=None, duration = None,end_datetime=None, timeout=None, count=None, isInfinite=None, **kwargs):
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
        if duration is not None:
            print(f"thread classı içindeki duration  {duration}")
            if self.duration is not None:
                self.duration = duration
                self.startTime = time.time() 
                self.stop_time = self.startTime + self.duration
                self.isInfinite = False
            else:
                self.stop_time = time.time() + duration

        if kwargs:
            self.kwargs.update(kwargs)
    def toggleBeep(self):
        if self.isBeep:
            self.isBeep=False
        else:self.isBeep=True

        print(f"[{self.address}] 🔁 Thread parametreleri güncellendi.")

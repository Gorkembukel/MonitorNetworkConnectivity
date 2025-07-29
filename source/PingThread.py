# ping_thread.py
from datetime import datetime
import threading
import time
import beepy

from source.PingStats import PingStats
from icmplib import ping as icmp_ping
import struct
from icmplib.sockets import ICMPv4Socket
from icmplib.models import ICMPRequest

class HighRatePing():
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

    def create_payload():
        """Zaman bilgisi taşıyan payload (8 bayt timestamp)."""
        return struct.pack('!d', time.time())

    def sender():
        global sequence_number
        count = 1
        while True:
            sequence_number += 1
            try:
                
                request = ICMPRequest(
                    destination=TARGET_IP,
                    id=IDENTIFIER,
                    sequence=sequence_number,
                    payload_size=1024
                )
                sock.send(request)
                print(f"[>] Ping #{count} sent")  # ← sayaç her gönderimde yazılır
                count += 1
                

            except Exception as e:
                print(f"[!] Send error: {e}")

    def receiver():
        while True:
            try:
                # Ham paketi al
                packet_raw, addr = sock._sock.recvfrom(1024)
                reply = sock.decode(packet_raw)

                # Filtre: sadece bizim attığımız paketler
                if reply.id != IDENTIFIER or reply.sequence is None:
                    continue

                if len(reply.payload) >= 8:
                    send_time = struct.unpack('!d', reply.payload[:8])[0]
                    rtt = (time.time() - send_time) * 1000
                    print(f"[<] Reply from {reply.source}: seq={reply.sequence} time={rtt:.2f} ms")
                else:
                    print(f"[<] Reply from {reply.source}: seq={reply.sequence} (no timestamp)")

            except Exception as e:
                print(f"[!] Receive error: {e}")




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
        self.stop_time = time.time() + duration if duration else None
        self.family = family
        self.privileged = privileged
        self.kwargs = kwargs

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
                    recv_time = time.time()
                    self.stats.add_result(rtt)
                    
                    print(f"[{self.address}] ✅ {rtt:.2f} ms (icmplib)")
                else:
                    self.stats.add_result(None)
                    print(f"[{self.address}] ❌ Timeout (icmplib)")
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

        print(f"[{self.address}] 🔁 Thread parametreleri güncellendi.")

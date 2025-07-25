# ping_thread.py
import threading
import time
import traceback
from scapy.all import IP, ICMP, sr1
from source.PingStats import PingStats
from icmplib import ping as icmp_ping
from collections import deque
from multiprocessing import Process, Event, Value,Queue

class Scheduler(threading.Thread):
    def __init__(self, address, duration, stats: PingStats,
                 interval_ms=10, target_rate=None, **kwargs):
        super().__init__()
        self.address = address
        self.duration = duration
        self.interval = interval_ms/1000
        self.stats = stats
        
        self.target_rate = target_rate or (1/ self.interval)
        self.kwargs = kwargs

        self._stop_event = threading.Event()
        self.process_stop_event = Event()
        self.result_queue = Queue()
        self.processes = []
        self.total_pings = 0
        self.last_pings = 0
        self.last_check_time = time.time()
        self.stop_time = time.time() + duration
        self.MAX_PROCESSES = 12
        self.esstimatedMaxProcces_speed_for_ping = 1/100 #10ms de vir
    def run(self):
        self.spawn_process()

        while time.time() < self.stop_time and not self._stop_event.is_set():
            time.sleep(self.interval / 10)
            self.consume_results()


            rate = self.calculate_rate()
            print(f"[Scheduler] 🔎 Current rate: {rate:.2f} pings/sec")

            needed = self.esstimatedMaxProcces_speed_for_ping / self.interval #açılacak proces
            """expected = self.target_rate
            needed = expected - rate"""

            if len(self.processes) < self.MAX_PROCESSES and len(self.processes) <= needed :
                
                self.spawn_process()

            self.stats.updateThreadLoopTime(rate)

        self.terminate_all()
        print("[Scheduler] 🛑 Scheduler finished.")

    def spawn_process(self):
        
        process = PingThread(
            address=self.address,
            duration=self.stop_time - time.time(),
            interval_ms=self.interval,
            result_queue=self.result_queue,
            stop_event=self.process_stop_event,
            **self.kwargs
        )
        process.start()
        self.processes.append(process)
        print(f"[Scheduler] 🚀 Spawned PingProcess | total={len(self.processes)}")

    def consume_results(self):
        while not self.result_queue.empty():
            rtt = self.result_queue.get()
            if rtt is not None:
                self.stats.add_result(rtt)
            else:
                self.stats.add_result(None)
            self.total_pings += 1

    def calculate_rate(self):
        elapsed = time.time() - self.last_check_time
        diff = self.total_pings - self.last_pings
        rate = diff / elapsed if elapsed > 0 else 0
        self.last_check_time = time.time()
        self.last_pings = self.total_pings
        return rate
    def get_active_ping_thread_count(self):
        return sum(1 for p in self.processes if p.is_alive())
    def terminate_all(self):
        self.process_stop_event.set()
        for p in self.processes:
            p.join()

    def stop(self):
        self._stop_event.set()

class RatePIDController:
    def __init__(self, kp=1.0, ki=0.2, kd=0.4):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0
        self.last_time = time.time()

    def compute(self, setpoint, measured):
        now = time.time()
        dt = now - self.last_time
        if dt == 0:
            return 0
        error = setpoint - measured
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.prev_error = error
        self.last_time = now
        return output



class PingThread(Process):
    def __init__(self, address, duration, interval_ms, result_queue: Queue, stop_event: Event,
                 count=1, timeout=1, **kwargs):
        super().__init__()
        self.address = address
        self.duration = duration
        self.interval = interval_ms          # saniyeye çeviriyoruz
        self.result_queue = result_queue    # burası önemli ✔
        self.stop_event = stop_event        # ortak sinyal ile process'leri durduruyoruz
        self.count = count
        self.timeout = timeout
        self.kwargs = kwargs

    def run(self):
        stop_time = time.time() + self.duration
        while time.time() < stop_time and not self.stop_event.is_set():
              
            result = icmp_ping(
                self.address,
                count=self.count,
                timeout=self.timeout,
                interval=self.interval,
                
                **self.kwargs
            )
            if result.is_alive:
                rtt = result._rtts.pop() 
            
                print(f"ping proces {result.packet_loss}")
            
            
            self.result_queue.put(rtt)  # 🟩 rtt değerini Scheduler'a gönderiyoruz
            time.sleep(self.interval)
 

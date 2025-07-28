from typing import List, Optional
from statistics import mean, stdev
import matplotlib.pyplot as plt
import time
dict_of_data_keys = {# buradaki keyler tablodaki sütun başlıkları için kullanılacak. Ekleyeceğiniz veri varsa burada başlığını girerseniz grafik güncellenir
            "target": "",
            "sent": "",
            "received": "",
            "failed": "",
            "success_rate": "",
            "avg_rtt": "",
            "min_rtt": "",
            "max_rtt": "",
            "jitter": "",
            "last_result": "",
            "time_per_ping":""
        }

def get_data_keys():
        return dict_of_data_keys.keys()


class PingStats:
    def __init__(self, target: str):
        self._target = target
        self._rttList: List[Optional[float]] = []
        self.initTime = time.time()#TODO gereksiz olabilir
        self.addTime: float
    
    def add_result(self, rtt: Optional[float]):
        self._rttList.append(rtt)
        self.addTime = time.time()

    @property
    def target(self): return self._target
    @property
    def sent(self): return len(self._rttList)
    @property
    def received(self): return len([r for r in self._rttList if r is not None])
    @property
    def failed(self): return self.sent - self.received
    @property
    def success_rate(self): return (self.received / self.sent * 100) if self.sent else 0.0
    @property
    def average_rtt(self): 
        valid = [r for r in self._rttList if r is not None]
        return round(mean(valid), 2) if valid else None
    @property
    def min_rtt(self): 
        valid = [r for r in self._rttList if r is not None]
        return min(valid) if valid else None
    @property
    def max_rtt(self): 
        valid = [r for r in self._rttList if r is not None]
        return max(valid) if valid else None
    @property
    def jitter(self): 
        valid = [r for r in self._rttList if r is not None]
        return round(stdev(valid), 2) if len(valid) > 1 else 0.0
    @property
    def last_result(self): 
        if not self._rttList: return "No Data"
        return "Success" if self._rttList[-1] is not None else "Timeout"
    @property
    def time_per_ping(self):
        int = 20
        sumRtt = 0.0
        for rtt in self._rttList[-int:]:
            if rtt:
                sumRtt += rtt
        result = round(sumRtt/int,2)
        
    
        return (result)
        
        
    def setAddress(self,target):
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
            "last_result": self.last_result,
            "time_per_ping": self.time_per_ping
        }
    
    

    #grafik metotları
    def plot_rtt_series(self, ax=None):
        valid_rttList = [r for r in self._rttList if r is not None]
        if not valid_rttList:
            print(f"[{self._target}] No RTT data for series plot.")
            return

        if ax is None:
            plt.figure(figsize=(10, 4))
            ax = plt.gca()

        ax.plot(range(len(valid_rttList)), valid_rttList, marker='o')
        ax.set_title("RTT Trend")
        ax.set_xlabel("Ping Attempt")
        ax.set_ylabel("RTT (ms)")
        ax.grid(True)

    def plot_rtt_box(self, ax=None):
        valid_rttList = [r for r in self._rttList if r is not None]
        if not valid_rttList:
            print(f"[{self._target}] No RTT data for boxplot.")
            return

        if ax is None:
            plt.figure(figsize=(6, 4))
            ax = plt.gca()

        ax.boxplot(valid_rttList, vert=True, patch_artist=True)
        ax.set_title("RTT Distribution")
        ax.set_ylabel("RTT (ms)")

    def plot_success_ratio(self, ax=None):
        if self.sent == 0:
            print(f"[{self._target}] No pings sent.")
            return

        if ax is None:
            plt.figure(figsize=(5, 5))
            ax = plt.gca()

        sizes = [self.received, self.failed]
        labels = ['Success', 'Timeout']
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.set_title("Success Ratio")

    def plot_jitter_bar(self, ax=None):
        if ax is None:
            plt.figure(figsize=(4, 4))
            ax = plt.gca()

        ax.bar(["Jitter"], [self.jitter], color="skyblue")
        ax.set_title("Jitter")
        ax.set_ylabel("Milliseconds")

    # ✅ Hepsini tek bir sayfada çizmek için wrapper
    def all_graph(self, show=True):
        print(f"📊 Generating combined graph for: {self.target}")
        valid_rttList = [r for r in self._rttList if r is not None]
        if not valid_rttList:
            print("No RTT data available.")
            return

        fig, axs = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f"Ping Statistics for {self._target}", fontsize=16)

        self.plot_rtt_series(ax=axs[0, 0])
        self.plot_rtt_box(ax=axs[0, 1])
        self.plot_success_ratio(ax=axs[1, 0])
        self.plot_jitter_bar(ax=axs[1, 1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        if show:
            plt.show()

    @staticmethod
    def show_all():
        """Elde bekleyen tüm grafikleri aynı anda gösterir"""
        plt.show()



    def __del__(self):
        print(f"[{self}] PingStats objesi siliniyor.")



if __name__ == '__main__':
    print(get_data_keys() )

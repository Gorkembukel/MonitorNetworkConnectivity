from typing import List, Optional
from statistics import mean, stdev
import matplotlib.pyplot as plt
import pyqtgraph as pg
from pyqtgraph import DateAxisItem
import time

from pyqtgraph import PlotDataItem,BarGraphItem
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
            "rate":""
        }

def get_data_keys():
        return dict_of_data_keys.keys()


class PingStats:
    def __init__(self, target: str):
        self._target = target
        self._rttList: List[Optional[float]] = []
        self._timeStamp_for_rttList: List[Optional[int]] = []
        self._rate: float = 0
        self.addTime: float
    
    def add_result(self, rtt: Optional[float], time:int = None):
        self._rttList.append(rtt)
        self._timeStamp_for_rttList.append(time)
    def update_rate(self, pulse:int):
        self.rate = 1/pulse
    @property
    def target(self): return self._target
    @property 
    def filterted_rtt(self): return [r if r is not None and r < 300 else None for r in self._rttList]
    @property
    def valid_rtt(self):
        """Gerçek RTT değerleri: 0 veya daha büyük"""
        return [r for r in self._rttList if r is not None and r <300]

    @property
    def failed_count(self):
        """300 olanları sayar (timeout'lar)"""
        return len([r for r in self._rttList if r == 300])
    @property
    def sent(self):
        return len(self._rttList)

    @property
    def received(self):
        return len(self.valid_rtt)

    @property
    def failed(self):
        return self.sent - self.received  # ya da: self.failed_count

    @property
    def success_rate(self):
        return (self.received / self.sent * 100) if self.sent else 0.0
    @property
    def average_rtt(self): 
        valid = [r for r in self.filterted_rtt if r is not None]
        return round(mean(valid), 2) if valid else None
    @property
    def min_rtt(self): 
        valid = [r for r in self.filterted_rtt if r is not None]
        return min(valid) if valid else None
    @property
    def max_rtt(self): 
        valid = [r for r in self.filterted_rtt if r is not None]
        return max(valid) if valid else None
    @property
    def jitter(self): 
        valid = [r for r in self.filterted_rtt if r is not None]
        return round(stdev(valid), 6) if len(valid) > 1 else 0.0
    @property
    def last_result(self): 
        if not self._rttList: return "No Data"
        return "Success" if self._rttList[-1] is not None and self._rttList[-1] < 300 else "Timeout"#return "Success" if self._rttList[-1] is not None else "Timeout"
    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, value: float):
        self._rate = value
        
        
    def setAddress(self,target):
        self._target = target

    def summary(self):
        return {
            "target": self.target,
            "sent": self.sent,
            "received": self.received,
            "failed": self.failed,
            "success_rate": round(self.success_rate, 6),
            "avg_rtt": self.average_rtt,
            "min_rtt": round(self.min_rtt, 6) if self.min_rtt is not None else None,
            "max_rtt": round(self.max_rtt, 6) if self.max_rtt is not None else None,
            "jitter": round(self.jitter, 6) if self.jitter is not None else None,
            "last_result": self.last_result,
            "rate": round(self.rate, 2) if self.rate is not None else None
        }
    
    def get_time_series_data(self):  # zaman ve rtt'yi birleştirir
        valid_rtt_list = [r if r is not None else -200 for r in self._rttList]
        valid_timeList = [t for t in self._timeStamp_for_rttList if t is not None]
        return [
            (t, r)
            for t, r in zip(self._timeStamp_for_rttList, self._rttList)
            if t is not None and r is not None
        ]

    @staticmethod
    def show_all():
        """Elde bekleyen tüm grafikleri aynı anda gösterir"""
        plt.show()
    
    def pygraph(self):
        #valid_rtt_list = [r if r is not None else -200 for r in self._rttList]
        valid_timeList = [t for t in self._timeStamp_for_rttList if t is not None]
        if not valid_timeList:
            print(f"[{self._target}] No Time data")
            return
        """if not valid_rtt_list:
            print(f"[{self._target}] Geçerli RTT verisi yok.")
            return"""
        
        pg.plot(self._rttList, pen='g', symbol='o', title=f"RTT for {self._target}").setYRange(-220,300)

    def get_rtt_curve(self):
        data = self.get_time_series_data()
        
        
        if not data:
            return PlotDataItem(x=0, y=0, pen='g', symbol='o', name="RTT Trend")

        
        x, y = zip(*data)
        return PlotDataItem(x=x, y=y, pen='g', symbol='o', name="RTT Trend")
    
    def get_jitter_bar(self):
        
        return BarGraphItem(x=[0], height=[self.jitter], width=0.6, brush='b')
    """def get_success_bar(self):
        from pyqtgraph import BarGraphItem
        success = self.received
        fail = self.failed
        return BarGraphItem(x=[0, 1], height=[success, fail], width=0.6, brushes=['g', 'r'])"""
    def get_success_bar(self):
        from pyqtgraph import BarGraphItem
        total = self.sent
        if total == 0:
            return BarGraphItem(x=[0, 1], height=[0, 0], width=0.6, brushes=['g', 'r'])

        success_pct = self.received / total * 100
        fail_pct = self.failed / total * 100

        return BarGraphItem(x=[0, 1], height=[success_pct, fail_pct], width=0.6, brushes=['g', 'r'])
    def get_min_max_lines(self):
        from pyqtgraph import InfiniteLine
        lines = []
        if self.min_rtt is not None:
            lines.append(InfiniteLine(pos=self.min_rtt, angle=0, pen='y'))
        if self.max_rtt is not None:
            lines.append(InfiniteLine(pos=self.max_rtt, angle=0, pen='m'))
        return lines



    def __del__(self):
        print(f"[{self}] PingStats objesi siliniyor.")



if __name__ == '__main__':
    print(get_data_keys() )

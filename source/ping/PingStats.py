from datetime import datetime
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
            "Last failed on": "",
            "Consecutive failed": "",
            "Max Consecutive failed": "",
            "success rate": "",
            "min rtt": "",
            "avg rtt": "",            
            "max rtt": "",
            "Last success on": "",            
            "jitter": "",
            "last result": "",
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
        self.timeOut= 300

        self._consecutive_failed = 0
        self._last_consecutive_failed = 0
        self._max_consecutive_failed = 0

         # zaman kayıtları
        self._last_success_on = None
        self._last_failed_on = None

        #min max mean, jitter için
        self._n_valid = 0
        self._mean = 0.0
        self._M2 = 0.0
        self._min = None
        self._max = None

        #graph için  bazı tanımlamalar. her seferinde yeniden hesaplamak yerine en son gelen veriyi hesaplamak için 
          # --- plot cache ---
        self._plot_x = []
        self._plot_y = []
        self._plot_brushes = []
        self._plot_pens = []
        self._plot_len = 0   # hızlı karşılaştırma için

        # brush/pen objelerini 1 kez oluştur (mkBrush/mkPen pahalı)
        self._b_red  = pg.mkBrush('r'); self._b_green = pg.mkBrush('g')
        self._p_red  = pg.mkPen('r');   self._p_green = pg.mkPen('g')
    def set_timeout(self, timeout):
        
        self.timeOut = timeout 


    def add_result(self, rtt: Optional[float], time:int = None):
        self._rttList.append(rtt)
        self._timeStamp_for_rttList.append(time)

      # başarısız kriteri: None veya timeout'a eşit/büyük        

        if (rtt is None) or (rtt >= self.timeOut):# eklenen rtt bilgisi timeout mu 
            #evet, şimdi gelen ping, timeout olmuş
            self._consecutive_failed += 1
            self._last_failed_on = datetime.now()
            if self._consecutive_failed > self._max_consecutive_failed:
                self._max_consecutive_failed = self._consecutive_failed
            else:
                self._last_consecutive_failed = self._consecutive_failed

        else:# ping başarılı yani #if (rtt is not None) and (rtt < self.timeOut):
            # bir seri bitti: geçmişi sakla
            self._last_success_on = datetime.now()#en son başarılı ping zamanını kaydeder

            if self._consecutive_failed > 0:
                self._last_consecutive_failed = self._consecutive_failed
                # opsiyonel:
                # self._failure_streaks.append(self._consecutive_failed)
            self._consecutive_failed = 0
            #min mean max bulma
            self._n_valid += 1
            if self._min is None or rtt < self._min: self._min = rtt
            if self._max is None or rtt > self._max: self._max = rtt

            delta = rtt - self._mean
            self._mean += delta / self._n_valid
            self._M2 += delta * (rtt - self._mean)

        # en sonda sadece yeni noktayı cache’e ekle:
        self._append_plot_point(time, rtt)


        
            
        
    def update_rate(self, pulse:int):
        self.rate = 1/pulse

    @property
    def last_success_on(self):
        """Son başarılı ping zamanı (datetime veya None)"""
        return self._last_success_on

    @property
    def last_failed_on(self):
        """Son başarısız ping zamanı (datetime veya None)"""
        return self._last_failed_on
    @property
    def target(self): return self._target
    @property 
    def filterted_rtt(self): return [r if r is not None and r < self.timeOut else None for r in self._rttList]
    @property
    def valid_rtt(self):
        """Gerçek RTT değerleri: 0 veya daha büyük"""
        return [r for r in self._rttList if r is not None and r <self.timeOut]

    @property
    def failed_count(self):
        """300 olanları sayar (timeout'lar)"""
        return len([r for r in self._rttList if r == self.timeOut])
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
       
        return self._mean
    @property
    def min_rtt(self): 
        return self._min
    @property
    def max_rtt(self): 
        return self._max
    @property
    def consequtive_failed(self):
        return self._last_consecutive_failed
    
    @property
    def max_consequtive_failed(self):
        return self._max_consecutive_failed

    @property
    def jitter(self): 
        if self._n_valid > 1:
            var = self._M2 / (self._n_valid - 1)
            return round(var ** 0.5, 6)
        return 0.0
    @property
    def last_result(self): 
        if not self._rttList: return "No Data"
        return "Success" if self._rttList[-1] is not None and self._rttList[-1] < self.timeOut else "Timeout"#return "Success" if self._rttList[-1] is not None else "Timeout"
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
            "Consecutive failed": self.consequtive_failed,
            "Max Consecutive failed": self.max_consequtive_failed,
            "success rate": f"% {round(self.success_rate, 2)}",
            "avg rtt": self.average_rtt,
            "min rtt": round(self.min_rtt, 2) if self.min_rtt is not None else None,
            "max rtt": round(self.max_rtt, 2) if self.max_rtt is not None else None,
            "jitter": round(self.jitter, 2) if self.jitter is not None else None,
            "Last success on": self.last_success_on.strftime("%d-%m-%Y %H:%M:%S") if self.last_success_on else None,
            "Last failed on": self.last_failed_on.strftime("%d-%m-%Y %H:%M:%S") if self.last_failed_on else None,
            "last result": self.last_result,
            "rate": round(self.rate, 2) if self.rate is not None else None
        }
    
    def get_time_series_data(self):  # zaman ve rtt'yi birleştirir
        
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
        
        pg.plot(self._rttList, pen='g', symbol='o', title=f"RTT for {self._target}").setYRange(-220, self.timeOut)

    """def get_rtt_curve(self):
        data = self.get_time_series_data()
        
        
        if not data:
            return PlotDataItem(x=0, y=0, pen='g', symbol='o', name="RTT Trend")

        
        x, y = zip(*data)
        return PlotDataItem(x=x, y=y, pen='g', symbol='o', name="RTT Trend")"""
    
    def _append_plot_point(self, t, r):
        if t is None:
            return
        is_to = (r is None) or (r >= self.timeOut)
        self._plot_x.append(t)
        self._plot_y.append(self.timeOut if is_to else r)
        self._plot_brushes.append(self._b_red if is_to else self._b_green)
        self._plot_pens.append(self._p_red if is_to else self._p_green)
        self._plot_len += 1

    def get_plot_arrays(self):
        """GraphWindow sadece bunu çağırır."""
        return self._plot_x, self._plot_y, self._plot_brushes, self._plot_pens
    def get_plot_len(self):
        return self._plot_len

    def get_rtt_curve(self):
        
        if not self._rttList or not self._timeStamp_for_rttList:
            return pg.PlotDataItem(x=[], y=[], pen='g', symbol='o', name="RTT Trend")

        x, y, brushes, pens = [], [], [], []

        red_b = pg.mkBrush('r'); green_b = pg.mkBrush('g')
        red_p = pg.mkPen('r');   green_p = pg.mkPen('g')

        for t, r in zip(self._timeStamp_for_rttList, self._rttList):
            if t is None:
                continue
            is_timeout = (r is None) or (r >= self.timeOut)
            x.append(t)
            y.append(self.timeOut if is_timeout else r)
            brushes.append(red_b if is_timeout else green_b)
            pens.append(red_p if is_timeout else green_p)

        return pg.PlotDataItem(
            x=x, y=y,
            pen='b',
            symbol='o', symbolSize=8,
            symbolBrush=brushes,
            symbolPen=pens,
            name="RTT Trend"
        )
        
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

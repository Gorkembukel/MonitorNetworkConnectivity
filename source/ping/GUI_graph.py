from PyQt5.QtWidgets import QDialog, QVBoxLayout,QWidget
from pyqtgraph import PlotWidget
import pyqtgraph as pg
from QTDesigns.graph_window import Ui_Dialog_graphWindow
import time
from pyqtgraph import DateAxisItem  


class GraphWindow(QDialog):
    def __init__(self, stat_obj, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog_graphWindow()
        self.ui.setupUi(self)
        self.stat_obj = stat_obj

        self.plot_refs = {}  # güncelleme için sakla

        self.setup_tabs()

        # Timer ile canlı güncelleme
        from PyQt5.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.setInterval(100)#60fps için 17 ms
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()


        #grafik optimizasyonu için 
        self._last_len = -1

    def setup_tabs(self):
        # 1️⃣ RTT → tab
        
        """axis = DateAxisItem(orientation='bottom',utcOffset=3)
        rtt_plot = PlotWidget(axisItems={'bottom': axis})  # 
        rtt_plot.setTitle(f"RTT for {self.stat_obj.target}")  # ⬅ stat_obj çünkü GraphWindow sınıfındasın

        curve = self.stat_obj.get_rtt_curve()
        rtt_plot.addItem(curve)
        """
        axis = DateAxisItem(orientation='bottom', utcOffset=3)
        rtt_plot = PlotWidget(axisItems={'bottom': axis})
        rtt_plot.setTitle(f"RTT for {self.stat_obj.target}")

        curve = pg.PlotDataItem(pen='b', symbol='o', symbolSize=8)
        rtt_plot.setClipToView(True)
        rtt_plot.addItem(curve)

        
        layout1 = QVBoxLayout()
        layout1.addWidget(rtt_plot)
        self.ui.tab.setLayout(layout1)
        self.plot_refs['rtt'] = curve

        # 2️⃣ Jitter → tab_2
        jitter_plot = PlotWidget()
        bar = self.stat_obj.get_jitter_bar()
        jitter_plot.addItem(bar)
        layout2 = QVBoxLayout()
        layout2.addWidget(jitter_plot)
        self.ui.tab_2.setLayout(layout2)
        self.plot_refs['jitter'] = bar

        # 3️⃣ Success bar → tab_3
        succ_plot = PlotWidget()
        bar2 = self.stat_obj.get_success_bar()
        succ_plot.addItem(bar2)
        layout3 = QVBoxLayout()
        layout3.addWidget(succ_plot)
        self.ui.tab_3.setLayout(layout3)
        self.plot_refs['success'] = bar2
       
        # 4️⃣ Min/Max → tab_4
        minmax_plot = PlotWidget()
        for line in self.stat_obj.get_min_max_lines():
            minmax_plot.addItem(line)
        layout4 = QVBoxLayout()
        layout4.addWidget(minmax_plot)
        self.ui.tab_4.setLayout(layout4)

    def update_plots(self):
        """if 'rtt' in self.plot_refs:        
            data = self.stat_obj.get_time_series_data()  # (timestamp, rtt) listesi
            if data:
                x, y = zip(*data)
                
                self.plot_refs['rtt'].setData(x, y)"""
        if 'rtt' in self.plot_refs:
            cur_len = self.stat_obj.get_plot_len()
            if cur_len != self._last_len:  # sadece yeni veri varsa çiz
                x, y, brushes, pens = self.stat_obj.get_plot_arrays()
                self.plot_refs['rtt'].setData(
                    x=x, y=y,
                    symbolBrush=brushes,
                    symbolPen=pens
                )
                self._last_len = cur_len
        if 'jitter' in self.plot_refs:
            self.plot_refs['jitter'].setOpts(height=[self.stat_obj.jitter])

        if 'success' in self.plot_refs:
            total = self.stat_obj.sent
            success_pct = (self.stat_obj.received / total * 100) if total else 0
            fail_pct = 100 - success_pct if total else 0
            self.plot_refs['success'].setOpts(height=[success_pct, fail_pct])
    def closeEvent(self, e):
        # Timer güvenli kapatma
        if self.timer and self.timer.isActive():
            self.timer.stop()
            try:
                self.timer.timeout.disconnect(self.update_plots)
            except TypeError:
                pass  # zaten kopuk olabilir

        # Plot referanslarını da bırak (GC’ye yardım)
        for k, it in getattr(self, "plot_refs", {}).items():
            try:
                it.clear()
            except Exception:
                pass
        self.plot_refs.clear()

        # Sekme layout’larını temizle (isteğe bağlı ama iyi olur)
        for tab in (getattr(self.ui, "tab", None),
                    getattr(self.ui, "tab_2", None),
                    getattr(self.ui, "tab_3", None),
                    getattr(self.ui, "tab_4", None)):
            if tab and tab.layout():
                lay = tab.layout()
                while lay.count():
                    w = lay.takeAt(0).widget()
                    if w:
                        w.deleteLater()

        self.deleteLater()  # gerçekten yok et
        return super().closeEvent(e)
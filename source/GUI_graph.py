from PyQt5.QtWidgets import QDialog, QVBoxLayout,QWidget
from pyqtgraph import PlotWidget
import pyqtgraph as pg
from QTDesigns.graph_window import Ui_Dialog_graphWindow
import time
from pyqtgraph import DateAxisItem  
class GraphWindow(QDialog):
    @staticmethod
    def create_rate_widget():
        

        plot = PlotWidget()
        plot.setFixedHeight(30)
        plot.setYRange(0, 1.5)
        plot.setMouseEnabled(x=False, y=False)
        plot.hideAxis('left')
        plot.hideAxis('bottom')

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(plot)

        container = QWidget()
        container.setLayout(layout)

        # Zaman ve rate verileri
        now = time.time()
        x_data = [now - i for i in reversed(range(20))]
        y_data = [0.0] * 20

        curve = plot.plot(x_data, y_data, pen='r')

        return container, curve, x_data, y_data

    def __init__(self, stat_obj, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog_graphWindow()
        self.ui.setupUi(self)
        self.stat_obj = stat_obj

        self.plot_refs = {}  # güncelleme için sakla

        self.setup_tabs()

        # Timer ile canlı güncelleme
        from PyQt5.QtCore import QTimer
        self.timer = QTimer()
        self.timer.setInterval(17)#60fps için
        self.timer.timeout.connect(self.update_plots)
        self.timer.start()

    def setup_tabs(self):
        # 1️⃣ RTT → tab
        
        axis = DateAxisItem(orientation='bottom',utcOffset=3)
        rtt_plot = PlotWidget(axisItems={'bottom': axis})  # ✅ Doğru kullanım
        rtt_plot.setTitle(f"RTT for {self.stat_obj.target}")  # ⬅ stat_obj çünkü GraphWindow sınıfındasın
        curve = self.stat_obj.get_rtt_curve()
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
        if 'rtt' in self.plot_refs:        
            data = self.stat_obj.get_time_series_data()  # (timestamp, rtt) listesi
            if data:
                x, y = zip(*data)
                
                self.plot_refs['rtt'].setData(x, y)
        if 'jitter' in self.plot_refs:
            self.plot_refs['jitter'].setOpts(height=[self.stat_obj.jitter])
        if 'success' in self.plot_refs:
            total = self.stat_obj.sent
            if total == 0:
                success_pct = 0
                fail_pct = 0
            else:
                success_pct = self.stat_obj.received / total * 100
                fail_pct = self.stat_obj.failed / total * 100

            self.plot_refs['success'].setOpts(height=[success_pct, fail_pct])

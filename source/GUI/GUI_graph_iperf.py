from PyQt5.QtWidgets import QDialog, QVBoxLayout,QMainWindow
from PyQt5.QtCore import QTimer
from pyqtgraph import PlotWidget, BarGraphItem
import pyqtgraph as pg
import re
from QTDesigns.iperf_result import Ui_MainWindow

from source.iperf_TestResult_Wrapper import TestResult_Wrapper_sub


class GraphWindow_iperf(QMainWindow):
    def __init__(self, testResultWrapper_sub:TestResult_Wrapper_sub, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.testResult = testResultWrapper_sub

        self.setWindowTitle(f"Iperf Result for {self.testResult.hostName}")
        self.plot_widget = PlotWidget()
        self.setup_graph_area()
        self.stream_cache_len = 0  # stream uzunluğunun değişimini izle

        # Canlı veri güncelleme için timer
        self.timer = QTimer()
        self.timer.setInterval(1000)  # her 1 saniyede bir güncelle
        self.timer.timeout.connect(self.update_graph_live)
        self.timer.start()

    def setup_graph_area(self):
        if not self.ui.widget_graph.layout():
            layout = QVBoxLayout(self.ui.widget_graph)
        else:
            layout = self.ui.widget_graph.layout()
            for i in reversed(range(layout.count())):
                old = layout.itemAt(i).widget()
                if old:
                    old.setParent(None)
            layout = self.ui.widget_graph.layout()
        self.plot_widget.setLabel('bottom', 'Time Interval (sec)')
        self.plot_widget.setLabel('left', 'Bitrate (bps)')
        self.plot_widget.setTitle(f"Bitrate Graph: {self.testResult.hostName}")
        layout.addWidget(self.plot_widget)

    def update_graph_live(self):
        # yeni stream eklenmiş mi kontrol et
        if self.stream_cache_len == len(self.testResult.streams):
            return  # yeni stream yok, çizim gerekmez

        if not self.ui.lineEdit_localip.text():
            self.ui.lineEdit_localip.setText        ((self.testResult.local_ip) )
            self.ui.lineEdit_localport.setText      ((self.testResult.local_port) )
            self.ui.lineEdit_remoteip.setText       ((self.testResult.remote_ip) )
            self.ui.lineEdit_remoteport.setText     ((self.testResult.remote_port) )
        self.stream_cache_len = len(self.testResult.streams)
        self.plot_widget.clear()

        interval_count = {}  # aynı interval başlangıçları çakışmasın diye

        for stream in self.testResult.streams:
            x = self._parse_interval_start(stream.interval)

            # offset uygulama (çakışan stream'ler için)
            count = interval_count.get(x, 0)
            x_offset = x + (0.2 * count)
            interval_count[x] = count + 1

            height = self._parse_bitrate(stream.bitrate)
            color = self._get_color(stream)
            bar = BarGraphItem(x=[x_offset], height=[height], width=0.15, brush=color)

            if stream.local_cpu_percent:#cpu değerleri atanır
                self.ui.lineEdit_localCpu.setText(stream.local_cpu_percent) 
                self.ui.lineEdit_remotecpu.setText(stream.remote_cpu_percent)

            self.plot_widget.addItem(bar)

    def _parse_interval_start(self, interval):
        try:
            start, _ = interval.strip().split('-')
            return float(start)
        except Exception:
            return 0.0

    def _parse_bitrate(self, bitrate):
        match = re.match(r'([\d\.]+)\s+([KMG]?bits)/sec', bitrate)
        if not match:
            return 0
        value, unit = match.groups()
        multiplier = {'bits': 1, 'Kbits': 1e3, 'Mbits': 1e6, 'Gbits': 1e9}
        return float(value) * multiplier.get(unit, 1)

    def _get_color(self, stream):
        if stream.omitted:
            return 'crimson'
        elif stream.stream_type == 'sender':
            return 'green'
        elif stream.stream_type == 'receiver':
            return 'blue'
        return 'gray'

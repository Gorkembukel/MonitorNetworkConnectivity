import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog
)

from PyQt5.QtCore import Qt, QTimer
from source.PingStats import PingStats  # PingStats senin sınıfın
from source.PingThreadController import ScapyPinger
import matplotlib.pyplot as plt

from source.common_fuction import read_targets_from_file

# Bu dosyanın (örneğin GUI/main.py) bulunduğu dizini al
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# GUI klasörünün bir üstüne çık, source/targets.txt'yi hedefle
TARGETS_FILE = os.path.join(BASE_DIR, "..", "targets.txt")

# Mutlak yola çevir (temizlik için)
TARGETS_FILE = os.path.abspath(TARGETS_FILE)

class PingGUI(QWidget):
    def __init__(self, stats_map):
        super().__init__()
        self.stats_map = stats_map  # {target: PingStats}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🖥️ Network Ping Monitor")
        self.setGeometry(100, 100, 1000, 600)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Ping sonuçlarını gösteren tablo
        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.cellClicked.connect(self.show_graph_for_row)

        main_layout.addWidget(self.table)

        # Yenileme butonu
        btn_layout = QVBoxLayout()
        refresh_btn = QPushButton("🔄 Yenile (Refresh Table)")
        refresh_btn.clicked.connect(self.populate_table)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)


        self.populate_table()
        self.timer = QTimer()
        self.timer.timeout.connect(self.populate_table)
        self.timer.start(10)  # her 1 saniyede bir tabloyu günceller
    def populate_table(self):
        summaries = [s.summary() for s in self.stats_map.values()]
        if not summaries:
            return

        headers = list(summaries[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(summaries))

        for row_idx, summary in enumerate(summaries):
            for col_idx, key in enumerate(headers):
                value = summary[key]
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def show_graph_for_row(self, row, col):
        # Satırdan hedef adresi bul
        target_item = self.table.item(row, 0)
        if target_item:
            target = target_item.text()
            stats = self.stats_map.get(target)
            if stats:
                stats.all_graph()
def main():
    app = QApplication(sys.argv)
    targets = read_targets_from_file(TARGETS_FILE)

    if not targets:
        print("📭 No targets found.")
        return

    print("🚀 Başlatılıyor...\n")

    pinger = ScapyPinger()  # Yeni sistemde: boş başlatılır
    # Hedefleri ekle (her biri ayrı task olacak)
    for target in targets:
        added = pinger.add_task(target, duration=20, interval_ms=1)
        if added:
            print(f"✅ Eklendi: {target}")
        else:
            print(f"⚠️ Eklenemedi: {target}")

    # Tüm hedefler için thread'leri başlat
    pinger.start_all()


    gui = PingGUI(pinger.get_stats_map())
    gui.show()
    sys.exit(app.exec_())

# Örnek test verisiyle çalıştır
if __name__ == "__main__":
    main()

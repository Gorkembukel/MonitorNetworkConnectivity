from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import QTimer, Qt
from QTDesigns.ui_mainmenu import Ui_MainWindow
from source.PingThreadController import ScapyPinger 
from source.common_fuction import read_targets_from_file
import sys, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGETS_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "targets.txt"))

class App(QMainWindow):
    def __init__(self, pinger):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pinger = pinger  # ScapyPinger örneği

        # 🔁 Timer ile düzenli olarak tabloyu güncelle
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(500)  # 1000 ms = 1 saniye

        # 🖼️ İkon
        icon_path = os.path.abspath(os.path.join(BASE_DIR, "..", "icons", "Circle-Transparent.png"))
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)

    def update_gui(self):
        stats_map = self.pinger.get_stats_map()
        table = self.ui.tableTarget
        table.setRowCount(len(stats_map))

        for row, (target, stats) in enumerate(stats_map.items()):
            summary = stats.summary()
            # Değerleri al
            last_result = summary.get("last_result", "").lower()
            
            # Renk belirle
            if last_result in ("ok", "reachable", "success"):
                bg_color = QColor(200, 255, 200)  # Açık yeşil
            else:
                bg_color = QColor(255, 200, 200)  # Açık kırmızı

            values = [
                summary.get("target", ""),  # Host
                summary.get("target", ""),  # IP (aynı)
                summary.get("sent", ""),
                summary.get("failed", ""),
                round((summary.get("failed", 0) / summary.get("sent", 1)) * 100, 2),
                summary.get("received", ""),
                summary.get("last_result", ""),
                summary.get("avg_rtt", ""),
                summary.get("min_rtt", ""),
                summary.get("max_rtt", ""),
                summary.get("jitter", ""),
                summary.get("last_result", ""),
            ]
            
            for col, val in enumerate(values):
                
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg_color)
                table.setItem(row, col, item)

def main():
    targets = read_targets_from_file(TARGETS_FILE)
    if not targets:
        print("🎯 No targets found.")
        return

    pinger = ScapyPinger()
    for target in targets:
        if pinger.add_target(target, duration=20, interval_ms=50):
            print(f"✅ Added: {target}")
    pinger.start_all()

    app = QApplication(sys.argv)
    window = App(pinger)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

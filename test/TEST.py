# test.py

from source.PingThreadController import ScapyPinger
import time
import os
import matplotlib.pyplot as plt

# Bu dosyanın (örneğin GUI/main.py) bulunduğu dizini al
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# GUI klasörünün bir üstüne çık, source/targets.txt'yi hedefle
TARGETS_FILE = os.path.join(BASE_DIR, "..", "targets.txt")

# Mutlak yola çevir (temizlik için)
TARGETS_FILE = os.path.abspath(TARGETS_FILE)

def read_targets_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"🚫 File not found: {file_path}")
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    targets = read_targets_from_file(TARGETS_FILE)

    if not targets:
        print("📭 No targets found.")
        return

    print("🚀 Başlatılıyor...\n")

    pinger = ScapyPinger()  # Yeni sistemde: boş başlatılır

    # Hedefleri ekle (her biri ayrı task olacak)
    for target in targets:
        added = pinger.add_target(target, duration=20, interval_ms=1)
        if added:
            print(f"✅ Eklendi: {target}")
        else:
            print(f"⚠️ Eklenemedi: {target}")

    # Tüm hedefler için thread'leri başlat
    pinger.start_all()

    # Bitmeleri beklenir
    pinger.wait_for_all()

    # Sonuçları yazdır
    print("\n📊 Sonuçlar:")
    for target, stats in pinger.get_stats_map().items():
        summary = stats.summary()
        print(f"\n--- {summary['target']} ---")
        for k, v in summary.items():
            print(f"{k:>12}: {v}")

    pinger.show_all_updated()

    print("\n🎯 Tamamlandı.")

if __name__ == "__main__":
    main()

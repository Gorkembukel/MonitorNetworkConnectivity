from scapy_pings import ScapyPinger, is_valid_ip
import time
import os
from PingStats import PingStats

def read_targets_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"🚫 File not found: {file_path}")
        return []

    with open(file_path, "r") as f:
        targets = [line.strip() for line in f if line.strip()]
    return targets




    



"""
ip kontrolü scapy_ping içinde kontrol edilmeli. Bunun scapy_ping için objesini oluşturuken içinde gerekli metodun koşturması sağlanabilir
"""
        
def main():
    file_path = "targets.txt"
    targets = read_targets_from_file(file_path)
    
    scapy = ScapyPinger

    if not targets:
        print("📭 No targets found in txt file.")
        return


    """
    for target in targets:        
        scapy.timed_ping(target,Data, 20, 1,True)
        time.sleep(1)  # Çok sık ping atmamak için
    """ 
    stats_map = {}
    for target in targets:
        if is_valid_ip(target):
            stats_map[target] = PingStats()

    control = ScapyPinger(targets, 20, 1)
    control.run(True, stats_map)
    control.wait_for_all()


    for target in targets:
        if is_valid_ip(target):
            print( stats_map[target].summary())
            
        


if __name__ == "__main__":
    main()


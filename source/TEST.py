from ScapyPinger import scapy_pings as scapy
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
    Data = PingStats()
    scapy = ScapyPinger

    if not targets:
        print("📭 No targets found in txt file.")
        return

    for target in targets:        
            scapy.timed_ping(target,Data, 20, 1,True)
            time.sleep(1)  # Çok sık ping atmamak için
        
    print(Data.summary())


if __name__ == "__main__":
    main()

"""
def is_valid_ip(ip_str):
    isValid = False;
    try:
        ipaddress.ip_address(ip_str)
        isValid = True
    except ValueError:
        """Bir işleme gerek yok"""
    try:
        socket.gethostbyname(ip_str)
        return True        
    except Exception as e:
         """Bir işleme gerek yok"""
  
    return isValid;
"""
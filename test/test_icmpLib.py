from icmplib import multiping,async_multiping
import os

import asyncio



# Bu dosyanın (örneğin GUI/main.py) bulunduğu dizini al
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# GUI klasörünün bir üstüne çık, source/targets.txt'yi hedefle
TARGETS_FILE = os.path.join(BASE_DIR, "..", "targets.txt")

# Mutlak yola çevir (temizlik için)
TARGETS_FILE = os.path.abspath(TARGETS_FILE)
def read_ips_from_file(file_path):
    """Dosyadan IP adreslerini okur ve bir liste döndürür."""
    with open(file_path, 'r') as file:
        ips = [line.strip() for line in file.readlines() if line.strip()]
    return ips
async def main():
    tasks = asyncio.create_task(async_multiping(read_ips_from_file(TARGETS_FILE),count=100 ,interval=1/1000,payload_size=1024 )) 
    
    
    print("mahmut öncesi")

    await asyncio.gather(tasks)
    print("mahmut")


asyncio.run(main())

from icmplib import ping,Host
import time

    
    
initTime = time.time()
result =ping("1.1.1.1", 1200,1/1000,1,privileged=False)
endTime = time.time()
print(f"duration {endTime-initTime}\n {result.__str__()} ")

print_host_info(result)

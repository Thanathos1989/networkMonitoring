import socket
import sys
from datetime import datetime
from threading import Thread
from time import sleep
start=datetime.now()
devices=[]
for p in range(1024):
    try:
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        res=sock.connect_ex(("192.168.1.1", p))  #port range(1024 = systemports)
        sock.settimeout(None)
        if res == 0:
            devices.append(p)
        sock.close()
    except Exception:
        print("[ERROR] Class network get devices")
        continue
end = datetime.now()
print(f"Dauer: {end-start}")
for i in devices:
    print(i)
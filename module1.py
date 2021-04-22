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






    class networking:
    ip=""                       #Scanned IP
    mac=""                      #Physical address
    devices=[]                  #List Network devices
    openPorts=[]                #List Found open ports
    ip_list=[]                  #List from IP's

    def __init__(self, list=[]):
        def c2im(cidr):
            if cidr=="":
                print("[ERROR]\tc2im cant call")
            else:
                id=0
                jmp=1
                network, net_bits = cidr.split('/')
                host_bits = 32 - int(net_bits)
                netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
                return network, netmask, net_bits
        
        #search devices
        print("[INFO]\tGetting network device(s)")
        self.ip_list = list
        for i in self.ip_list:
            print(f"-:{i}")
        for i in self.ip_list:
            try:
                sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                res=sock.connect_ex((i, 7))  #port 7 = echo in TCP/UDP for ping
                sock.settimeout(None)
                if res == 0:
                    self.devices.append(i)
                sock.close()
            except Exception:
                print("[ERROR] Class network get devices")
                continue

        for i in self.ip_list:
            self.devices.append(c2im(i))
        print(f"devices: {self.devices}")

        print(f"[INFO]\tScan ports from {len(self.devices)} device(s)")
        for i in self.devices:
            for p in range(1024):
                try:
                    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    res=sock.connect_ex((i, p))  #port range(1024 = systemports)
                    sock.settimeout(None)
                    if res == 0:
                        self.devices.append(i)
                    sock.close()
                except Exception:
                    print("[ERROR] Class network get devices")
                    continue
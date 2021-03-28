import sys
import getopt
import psutil
import datetime
import platform
import GPUtil
import socket
import subprocess
from threading import Thread

###VAR
verbose = False
network = False
local = False
full = True
path = "."
file = "/Scan.json"
result_local = []
result_network = []

#debug
print(sys.argv[1:])
print("")

###Programm
##Klassen
class pc():
    node = ""                   #PC Name
    
    os_system = ""              #System Type "Win, Linux, ..."
    os_rel = ""                 #OS Release "10"
    os_ver = ""                 #OS Version "10.0.18362"
    os_bootTime=""              #OS Startup

    sys_processes=[]            #List 2D of SystemProcesses [os_process,pid,name,status,create_time,cpu_usage,cpu_cores,memory,user]
    
    user_name = ""              #Active User
    user_started = 0            #Last startup
    user_terminal = None        #Terminalmodus
    
    cpu_machine = ""            #Machinearch. "AMD64"
    cpu_name = ""               #CPU Name "Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"
    cpu_realCores=0             #Real Cores on CPU
    cpu_logiCores=0             #Logic Cores in CPU
    cpu_frqMax=0                #Max Frequence of CPU
    cpu_frqCur=0                #Current Frequence of CPU
    cpu_usage=0                 #CPU usage in %
    cpu_coreUsage=[]            #List of logical cores and usage in %

    ram_total=0                 #Total RAM
    ram_avail=0                 #Available RAM
    ram_used=0                  #Used RAM
    ram_perc=0                  #Used RAM in Percent
    ram_Stotal=0                #Total Swap
    ram_Sfree=0                 #Available Swap
    ram_Sused=0                 #Used Swap
    ram_Sperc=0                 #Used Swap in Percent

    disk_list=[]                #List 2D of all disks connected to PC (device, mountpoint, filesystem, part_usage.total,part_usage.used,part_usage.free,part_usage.percent)
    disk_read=0                 #Read Bytes since Boot
    disk_write=0                #Write Bytes since Boot

    gpu_list=[]                 #List 2D GPU (id, name, usage(%), free mem(byte), used mem(byte), total mem(byte), temperature(°C))

    if_list=[]                  #List 2D of Interfaces
    if_bysteSent=0              #Network sendet Bytes
    if_bytesRec=0               #Network recived Bytes


    def __init__(self):
        #OS + Arch
        uname = platform.uname()
        self.node = uname.node
        self.os_system = uname.system
        self.os_rel = uname.release
        self.os_ver = uname.version
        self.os_bootTime=psutil.boot_time()
        self.cpu_machine = uname.machine
        self.cpu_name = uname.processor
        del uname

        #Processes
        for p in psutil.process_iter():
            with p.oneshot():
                pid=p.pid
                if pid==0:
                    continue
                name=p.name()
                try:
                    os_process=False
                    create_time=datetime.datetime.fromtimestamp(p.create_time())
                except OSError:
                    os_process=True
                    create_time=datetime.datetime.fromtimestamp(psutil.boot_time())
                cpu_usage=p.cpu_percent()
                try:
                    cpu_cores=len(p.cpu_affinity())
                    memory=p.memory_full_info().uss
                    user=p.username()
                except psutil.AccessDenied:
                    cpu_cores=0
                    memory=-0
                    user="unknown"
                status=p.status()
            self.sys_processes.append([os_process,pid,name,status,create_time,cpu_usage,cpu_cores,memory,user])

        #CPU
        self.cpu_realCores=psutil.cpu_count(logical=False)
        self.cpu_logiCores=psutil.cpu_count(logical=True)
        self.cpu_frqMax=psutil.cpu_freq().max
        self.cpu_frqCur=psutil.cpu_freq().current
        self.cpu_usage=psutil.cpu_percent()
        for i, perc in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            self.cpu_coreUsage.append(perc)

        #RAM
        virtual_mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.ram_total=virtual_mem.total
        self.ram_avail=virtual_mem.available
        self.ram_used=virtual_mem.used
        self.ram_perc=virtual_mem.percent
        self.ram_Stotal=swap.total
        self.ram_Sfree=swap.free
        self.ram_Sused=swap.used
        self.ram_Sperc=swap.percent
        del virtual_mem, swap

        #DISK
        part = psutil.disk_partitions()
        for i in part:
            if(i.fstype):
                try:
                    part_usage = psutil.disk_usage(i.mountpoint)
                except PermissionError:
                    continue
                self.disk_list.append([i.device, i.mountpoint, i.fstype, part_usage.total,part_usage.used,part_usage.free,part_usage.percent])
        del part

        disk_io = psutil.disk_io_counters()
        self.disk_read=disk_io.read_bytes
        self.disk_write=disk_io.write_bytes
        del disk_io

        #GPU
        gpus = GPUtil.getGPUs()
        for i in gpus:
            self.gpu_list.append([i.id, i.name, i.load*100, i.memoryFree/1024/1024, i.memoryUsed/1024/1024, i.memoryTotal/1024/1024, i.temperature])
        del gpus

        #Interfaces
        if_add = psutil.net_if_addrs()
        net_io = psutil.net_io_counters()
        for interface_name, interface_addresses in if_add.items():
            for address in interface_addresses:
                self.if_list.append([interface_name, address.address, address.netmask, address.broadcast])
        self.if_bytesSent=net_io.bytes_sent
        self.if_bytesRec=net_io.bytes_recv
        del if_add, net_io

class network():
    ip=""                       #Scanned IP
    mac=""                      #Physical address
    devices=[]                  #List Network devices
    openPorts=[]                #List Found open ports

    def __init__(self, **kwargs):
        #search devices
        print("[INFO]\tGetting network devices")
        for i in ip_list:
            try:
                sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                res=sock.connect_ex((i, 7))  #port 7 = echo in TCP/UDP for ping
                sock.settimeout(None)
                if res == 0:
                    devices.append(i)
                sock.close()
            except Exception:
                print("[ERROR] Class network get devices")
                continue
        print(f"[INFO]\tScan ports from {len(devices)} devices")
        for i in devices:
            for p in range(1024):
                try:
                    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.1)
                    res=sock.connect_ex((i, p))  #port range(1024 = systemports)
                    sock.settimeout(None)
                    if res == 0:
                        devices.append(i)
                    sock.close()
                except Exception:
                    print("[ERROR] Class network get devices")
                    continue



##Funktionen
def debug(txt):
    print("[DEBUG]\t"+txt)
def debug_print():
    print("v \t"+str(verbose))
    print("n \t"+str(network))
    print("l \t"+str(local))
    print("f \t"+str(full))
    print("path \t"+path)
    print("file \t"+file)

def adj_size(size):
    factor = 1024
    for i in [" B"," KiB"," MiB"," GiB"," TiB"," PiB"," EiB"]:
        if size > factor:
            size = size / factor
        else:
            return f"{size:.4f}{i}"
def ip_extract(ip):
        range_list=[]
        for i in ip:
            x=""
            for j in i[0]:
                if x=="":
                    x=j
                else:
                    x=str(x)+"."+str(j)
            range_list.append(x+"/"+str(i[1]))
        return(range_list)

def ip_input():                     #Retourn List 3D of IP's like [[[192, 168, 12, 25], 16], [[192, 168, 13, 20], 24], [[192, 168, 123, 250], 24]]
    print("[INPUT] IPv4 in CIDR just like 192.168.123.5/24\n\tCeep it empty to end Input")
    ip_list=[]                      #List 3D from IP(192.168.123.5) and Subnet Mask(24) [[[192, 168, 12, 25], 16], [[192, 168, 13, 20], 24], [[192, 168, 123, 250], 24]]

    while True:
        ip_int=[]
        cidr=input("\tIP-CIDR: ")
        if cidr != "":
            #Chekc / Write IP
            if "/" in cidr:
                #Valid Split Input to ip and snm
                ip, snm = cidr.split("/")
                #snm=int(snm)
                if snm > "32" or snm < "0":
                    print("[ERROR] No Valid net mask\n")
                    continue
            else:
                #FALSE go back to begin
                print("[ERROR] No Valid CIDR Format\n")
                continue
            ip=ip.split(".")
            if len(ip) == 4:
                #Valid input write it to list (ip_list)
                if int(ip[0]) > 255 or int(ip[1]) > 255 or int(ip[2]) > 255 or int(ip[3]) > 255:
                    #FALSE no valid ip
                    print("[ERROR] No Valid IPv4\n")
                    continue
                else:
                    #Everything is ok. Write IP/snm into ip_list and change ip from str to int
                    for i in ip:
                        ip_int.append((int(i)))
                    ip_list.append([ip_int, snm])
                    print("\t",ip_extract(ip_list))
            else:
                #FALSE no valid ip
                print("[ERROR] No Valid IPv4\n")
                continue
        else:
            #end
            if "y" in input("[INPUT] Exit IPv4 input and start Network scan? yes/NO: "):
                return ip_list      #Retourne List with the IP's 
            else:
                continue

#mainfunctions for Programm            
def get_network():
    start=datetime.datetime.now()               #debug

    print("[INFO]\tGetting network information")
    ip_list=ip_extract(ip_input())
    nw=network(ip_list)
    print("[INFO]\tFinished network information\n")

    end=datetime.datetime.now()                 #debug
    print(f"Dauer:{end-start}")                 #debug
    

def get_local():
    start=datetime.datetime.now()               #debug

    print("[INFO]\tGetting local information")
    local=pc()
    print("[INFO]\tFinished local information\n")

    end=datetime.datetime.now()                 #debug
    print(f"Dauer:{end-start}")                 #debug
    #Grafical outup from local

###+++++++++++++++++++++++++++ START-PROGRAM +++++++++++++++++++++++++++###    
##Abfrage der Operatoren
opts, rest = getopt.getopt(sys.argv[1:], "vnlfo:")
'''
-v  = Komplette Ausgabe
-n  = Netzwerkscan only
-l  = Localscan only
-f  = Scant Local & Netzwerk + Ports
-o  = Outputpfad (Ordnerpfad)
'''
for opt, arg in opts:
    if opt == "-v":
        verbose = True
    if opt == "-n":
        network = True
    if opt == "-l":
        local = True
    if opt == "-o":
        path = arg

#Steuerung
if network == True:
    full = False
if local == True:
    full = False
if "-f" in opt:
    full = True
    local = False
    network = False

#Aufruf Funktionen
if full == True:
    get_local()
    get_network()
    debug("full")

if local == True:
    get_local()
    debug("local")

if network == True:
    get_network()
    debug("network")

###++++++++++++++++++++++++++++ END-PROGRAM ++++++++++++++++++++++++++++### 

print("="*80)


#def_network
#scan funktioniert noch nicht
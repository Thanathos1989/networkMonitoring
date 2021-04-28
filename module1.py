import sys                              #stabdard
import os
import re
import getopt                           #?
import psutil                           #import         C:/Users/Dragback/AppData/Local/Programs/Python/Python38/Lib/site-packages/psutil
import datetime                         #standard
import platform                         #? TCL          C:/Users/Dragback/AppData/Local/Programs/Python/Python38/tcl/tcl8/8.4/platform
import GPUtil                           #import         C:/Users/Dragback/AppData/Local/Programs/Python/Python38/Lib/site-packages/GPUtil
import socket                           #standard
import subprocess                       #standard
import struct                           #standard ?
from threading import Thread            #standard
#import wmi
import csv                              #standard ?

from itertools import islice            #standard ?
from ipaddress import ip_network        #standard ?
import math as m                        #import         C:/Users/Dragback/AppData/Local/Programs/Python/Python38/Lib/site-packages/docutils/utils/math

#########MAKE-SCRIPT##########
#pyinstaller --noconfirm --onedir --console --icon "C:/Users/Dragback/Downloads/ico_file.ico" --add-data "C:/Users/Dragback/AppData/Local/Programs/Python/Python38/Lib/site-packages/psutil;psutil/" --add-data "C:/Users/Dragback/AppData/Local/Programs/Python/Python38/tcl/tcl8/8.4/platform;platform/" --add-data "C:/Users/Dragback/AppData/Local/Programs/Python/Python38/Lib/site-packages/GPUtil;GPUtil/" --add-data "C:/Users/Dragback/AppData/Local/Programs/Python/Python38/Lib/site-packages/docutils/utils/math;math/"  "C:/Users/Dragback/source/repos/networkMonitoring/networkMonitoring.py"

###VAR
verbose = False                 #verbose output actualy useless
network = False                 #network test (show the networkdevices)
local = False                   #local system test (Hardware an System)
full = True                     #booth network and local
path = "."                      #outputpath
file = "/Scan.csv"              #name of outputfile
result_local = []               #List masterlist from local
result_network = []             #List masterlist from network

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
    #cpu_temp=""                 #FEHLT

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
                try:
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
                except Exception as inst:
                    print(f"[ERROR] Instance:\t{type(inst)}")
                    print(f"\targs:\t{inst.args}")
                    print(f"\targs:\t{inst}")
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

class networking:
    arp=[]                          #list 2D of Devices in ARP-Cache

    data=os.popen("arp -a").read()

    for line in re.findall('([-.0-9]+)\s+([-0-9a-f]{17})\s+(\w+)',data):
        arp.append(line)


        
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
    uname = platform.uname()
    node = uname.node
    
    print(f"[INFO]\tGetting network information\tat\t{start}")
    def out_csv(path, name, obj):
        path = str(path)
        name = str(name)
        obj=obj
        data=[]
        
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise

        with open(f"{path}network_{name}.csv", "w") as f:
            fields=["key","ip","mac","typ"]
            out = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            out.writeheader()

            for i in range(len(obj.arp)):
                data.append({"key":name,"ip":obj.arp[i][0],"mac":obj.arp[i][1],"typ":obj.arp[i][2],})

            #Write the values from data into CSV by line
            for i in range(len(data)):
                out.writerow(data[i])

    nw=networking()
    out_csv(path,node,nw)
    print(f"[EXPO]\tExport to: {path}network_{str(node)}.csv")
    end=datetime.datetime.now()                 #debug
    print(f"[INFO]\tFinished network information\tat\t{end}")
    print(f"\tTime: {end-start}\n")                 #debug
    

def get_local():
    start=datetime.datetime.now()               #debug
    def out_csv(path, name, obj):
        path = str(path)
        name = str(name)
        l_disk=[]
        l_gpu=[]
        l_if=[]
        l_core=[]
        l_process=[]
        c=1
        
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise
        for i in obj.disk_list:
            l_disk.append({"key":"disk "+i[0],"device":i[0],"mountpoint":i[1],"filesystem":i[2],"usage_total":i[3],"usage_used":i[4],"usage_free":i[5],"usage_percent":i[6]})
        for i in obj.gpu_list:
            l_gpu.append({"key":"gpu "+str(i[0]),"gpu_id":i[0],"gpu_name":i[1],"gpu_usage":i[2],"gpu_free":i[3],"gpu_used":i[4],"gpu_total":i[5],"gpu_temp":i[6]})
        for i in obj.if_list:
            l_if.append({"key":"if "+i[0],"if_name":i[0],"if_address":i[1],"if_netmask":i[2],"if_broadcast":i[3]})
        for i in obj.cpu_coreUsage:
            c
            l_core.append({"key":"core "+str(c),"value":i})
            c=c+1
        for i in obj.sys_processes:
            l_process.append({"key":"proc "+i[2],"os_process":i[0],"pid":i[1],"name":i[2],"status":i[3],"create_time":i[4],"cpu_usage":i[5],"cpu_cores":i[6],"memory":i[7],"user":i[8]})

        with open(f"{path}local_{name}.csv", "w") as f:
            fields=["key","value",
                    "os_process","pid","name","status","create_time","cpu_usage","cpu_cores","memory","user",
                    "device","mountpoint","filesystem","usage_total","usage_used","usage_free","usage_percent",
                    "gpu_id","gpu_name","gpu_usage","gpu_free","gpu_used","gpu_total","gpu_temp",
                    "if_name","if_address","if_netmask","if_broadcast",
                    ]
            out = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            out.writeheader()

            data = [{"key":"node","value":obj.node},                                    #name from Device
                    {"key":"os_system","value":obj.os_system},                          #START -- OS
                    {"key":"os_rel","value":obj.os_rel},                                
                    {"key":"os_ver","value":obj.os_ver},
                    {"key":"os_bootTime","value":obj.os_bootTime},                      #END -- os
                    {"key":"user_name","value":obj.user_name},                          #START -- USER
                    {"key":"user_started","value":obj.user_started},
                    {"key":"user_terminal","value":obj.user_terminal},                  #END -- user
                    {"key":"ram_total","value":obj.ram_total},                          #START -- RAM
                    {"key":"ram_avail","value":obj.ram_avail},
                    {"key":"ram_used","value":obj.ram_used},
                    {"key":"ram_perc","value":obj.ram_perc},
                    {"key":"ram_Stotal","value":obj.ram_Stotal},
                    {"key":"ram_Sfree","value":obj.ram_Sfree},
                    {"key":"ram_Sused","value":obj.ram_Sused},
                    {"key":"ram_Sperc","value":obj.ram_Sperc},                          #END -- ram
                    {"key":"disk_read","value":obj.disk_read},                          #START -- DISK
                    {"key":"disk_write","value":obj.disk_write},                        #END -- disk
                    {"key":"cpu_machine","value":obj.cpu_machine},                      #START -- CPU
                    {"key":"cpu_name","value":obj.cpu_name},
                    {"key":"cpu_realCores","value":obj.cpu_realCores},
                    {"key":"cpu_logiCores","value":obj.cpu_logiCores},
                    {"key":"cpu_frqMax","value":obj.cpu_frqMax},
                    {"key":"cpu_frqCur","value":obj.cpu_frqCur},
                    {"key":"cpu_usage","value":obj.cpu_usage},                          #END -- cpu
                    {"key":"if_sent","value":obj.if_bytesSent},                         #START -- Interfaces
                    {"key":"if_rec","value":obj.if_bytesRec},                           #END -- interfaces
                    ]
            #{"key":"","value":obj.},

            #Write the values from data into CSV by line
            for i in range(len(data)):
                out.writerow(data[i])
            for i in l_disk:
                out.writerow(i)
            for i in l_gpu:
                out.writerow(i)
            for i in l_core:
                out.writerow(i)
            for i in l_process:
                out.writerow(i)
            for i in l_if:
                out.writerow(i)

    print(f"[INFO]\tGetting local information\tat\t{start}")
    local=pc()
    out_csv(path, str(local.node)+"_System", local)                                #Output the csv file
    print(f"[EXPO]\tExport to: {path}local_{str(local.node)}.csv")
    end=datetime.datetime.now()                 #debug
    print(f"[INFO]\tFinished local information\tat\t{end}")
    print(f"\tTime: {end-start}\n")             #debug
    #Grafical outup from local

###+++++++++++++++++++++++++++ START-PROGRAM +++++++++++++++++++++++++++###    
##Abfrage der Operatoren
if __name__ == "__main__":
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
        if opt == "":
            pass

    #Steuerung
    if network == True:
        full = False
    if local == True:
        full = False 
    if "-f" in opts:
        full = True
        local = False
        network = False
    else:
        pass

    #Aufruf Funktionen
    if full == True:
        get_local()
        get_network()

    if local == True:
        get_local()

    if network == True:
        get_network()

###++++++++++++++++++++++++++++ END-PROGRAM ++++++++++++++++++++++++++++### 


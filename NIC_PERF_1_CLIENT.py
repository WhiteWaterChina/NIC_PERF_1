#!/tmp/tools/env/tops/bin/python
# -*- coding:utf-8 -*-
###usage: sut_ip sut_username sut_password sut_devicename client_devicename
import os
import sys
import re
import paramiko
import subprocess


if len(sys.argv) != 6:
    print "Input length is incorrect!"
    print "Usage:%s sut_ip sut_username sut_password sut_devicename client_devicename" % sys.argv[0]
    sys.exit(1)

sut_ip = sys.argv[1]
sut_username = sys.argv[2]
sut_password = sys.argv[3]
sut_deicename = sys.argv[4]
client_devicename = sys.argv[5]

path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'Lib_testcase'))
sys.path.append(path)

#get mtu now
mtu_current = subprocess.Popen("ip addr show|grep %s|grep mtu|awk '{match($0,/mtu\s*([0-9]*)/,a);print a[1]}'" % client_devicename, shell=True,stdout=subprocess.PIPE).stdout.readlines()[0].strip()

temp = open("/tmp/tools/name", mode="r")
log_dir_prefix = temp.readlines()[0].strip()
temp.close()
#log_dir_prefix = subprocess.Popen("cat /tmp/tools/name", shell=True, stdout=subprocess.PIPE).stdout.readlines()[0].strip()
#log_dir_prefix = "/root"
log_dir_prefix=log_dir_prefix + "/Stress/NIC_PERF_1_client"
print log_dir_prefix
if not os.path.isdir(log_dir_prefix):
    os.makedirs(log_dir_prefix)

devicePath=log_dir_prefix + '/' + client_devicename
if not os.path.isdir(devicePath):
    os.makedirs(devicePath)
logname_result_iperf = devicePath + "/" + "result_iperf_client_mtu_%s.txt" % mtu_current

#start  iperf test
#login to sut to start server
ssh_start_iperf_sut = paramiko.SSHClient()
ssh_start_iperf_sut.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_start_iperf_sut.connect(sut_ip, 22, username=sut_username, password=sut_password)
ssh_start_iperf_sut.exec_command(command='numactl --cpunodebind=netdev:%s --membind=netdev:%s iperf3 -s -i 5 --forceflush 5|grep -i sum ' % (sut_deicename, sut_deicename))
ssh_start_iperf_sut.close()
#client iperf
#calculate N
speed_now_list = subprocess.Popen(["ethtool", "%s" % client_devicename],stdout=subprocess.PIPE).stdout.readlines()
pattern_speed = re.compile(r"Speed:\s*(\d*)Mb/s")
for item_speed in speed_now_list:
    speed_temp = re.search(pattern=pattern_speed, string=item_speed)
    if speed_temp is not None:
        speed_now = speed_temp.groups()[0]

if speed_now == "10000":
    N = 2
elif speed_now == "25000":
    N = 3
elif speed_now == "40000":
    N = 5
elif speed_now == "100000":
    N = 11
log_iperf = open(logname_result_iperf, mode="w")
iperf_test_sut = subprocess.Popen("numactl --cpunodebind=netdev:%s --membind=netdev:%s iperf3 -c %s -t 100 -i 5 --forceflush 5 -P %s | grep -i sum" % (client_devicename, client_devicename, sut_ip, N) ,shell=True, stdout=log_iperf)
iperf_test_sut.wait()
log_iperf.close()
#close iperf3 remotely
ssh_start_iperf_sut.connect(sut_ip, 22, username=sut_username, password=sut_password)
ssh_start_iperf_sut.exec_command(command='killall -9 iperf3')
ssh_start_iperf_sut.close()
sys.exit(0)
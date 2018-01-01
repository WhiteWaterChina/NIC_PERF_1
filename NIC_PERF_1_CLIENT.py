#!/tmp/tools/env/tops/bin/python
# -*- coding:utf-8 -*-
###usage: sut_ctrl_ip sut_username sut_password sut_devicename client_devicename jumbo_max
import os
import sys
import re
import time
import paramiko
import subprocess


if len(sys.argv) != 7:
    print "Input length is incorrect!"
    print "Usage:%s sut_ctrl_ip sut_username sut_password sut_devicename client_devicename jumbo_max" % sys.argv[0]
    sys.exit(1)

sut_ctrl_ip = sys.argv[1]
#sut_test_ip = sys.argv[2]
sut_username = sys.argv[2]
sut_password = sys.argv[3]
sut_devicename = sys.argv[4]
client_devicename = sys.argv[5]
jumbo_max = sys.argv[6]

path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'Lib_testcase'))
sys.path.append(path)
mtu_list = ["68", "128", "256", "512", "1500"]
if jumbo_max not in mtu_list:
    mtu_list.append(jumbo_max)

#get log path
with open("/tmp/tools/name", mode="r") as temp_file:
    log_dir_prefix = temp_file.readlines()[0].strip()

log_dir_prefix=log_dir_prefix + "/Stress/NIC_PERF_1"
if not os.path.isdir(log_dir_prefix):
    os.makedirs(log_dir_prefix)

devicePath=log_dir_prefix + '/' + client_devicename
if not os.path.isdir(devicePath):
    os.makedirs(devicePath)
#calculate N
speed_now_list = subprocess.Popen("ethtool %s|grep Speed|awk -F ':' '{print $2}'|awk '{match($0,/([0-9]+)/,a);print a[1]}'" % client_devicename, shell=True, stdout=subprocess.PIPE)
speed_now_list.wait()
speed_now = speed_now_list.stdout.readlines()[0].strip()
if speed_now == "10000":
    N = 2
elif speed_now == "25000":
    N = 3
elif speed_now == "40000":
    N = 5
elif speed_now == "100000":
    N = 11
else:
    N = 2
for mtu_current in mtu_list:
    logname_result_iperf = devicePath + "/" + "result_iperf_client_mtu_%s.txt" % mtu_current

    #set mtu client
    change_mtu_client = subprocess.Popen("ifconfig %s mtu %s" % (client_devicename, mtu_current), shell=True, stdout=subprocess.PIPE)
    change_mtu_client.wait()
    check_mtu_client_temp = subprocess.Popen("ip addr show|grep %s|grep mtu|awk '{match($0,/mtu\s*([0-9]*)/,a);print a[1]}'" % client_devicename, shell=True, stdout=subprocess.PIPE)
    check_mtu_client_temp.wait()
    check_mtu_client = check_mtu_client_temp.stdout.readlines()[0].strip()
    if check_mtu_client != mtu_current:
        print "Client MTU for %s set failed! Please check! Need %s,but now %s" % (client_devicename, mtu_current, check_mtu_client)
        sys.exit(1)
    print "Client MTU for %s set %s successfully!" %(client_devicename, mtu_current)

    #login to sut to set mtu
    ssh_to_sut = paramiko.SSHClient()
    ssh_to_sut.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_to_sut.connect(sut_ctrl_ip, 22, username=sut_username, password=sut_password)
    ssh_to_sut.exec_command("ifconfig %s mtu %s" % (sut_devicename, mtu_current))
    time.sleep(2)
    stdin_checkmtu, stdout_checkmtu, stderr_checkmtu = ssh_to_sut.exec_command("ip addr show|grep %s|grep mtu|awk '{match($0,/mtu\s*([0-9]*)/,a);print a[1]}'" % sut_devicename)
    check_mtu_sut = stdout_checkmtu.readlines()[0].strip()
    ssh_to_sut.close()
    if check_mtu_sut != mtu_current:
        print "Sut MTU for %s set failed! Please check! Need %s,but now %s" % (sut_devicename, mtu_current, check_mtu_sut)
        sys.exit(1)
    print "Sut MTU for %s set %s successfully!" %(sut_devicename, mtu_current)
    #get sut test ip
    ssh_to_sut.connect(sut_ctrl_ip, 22, username=sut_username, password=sut_password)
    stdin_getip, stdout_getip, stderr_getip = ssh_to_sut.exec_command("ip addr show|grep %s|grep inet|awk '{match($s,/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/,a);print a[1]}'" % sut_devicename)
    sut_test_ip = stdout_getip.readlines()[0].strip()
    ssh_to_sut.close()
    #start  iperf3
    #login to sut to start server
    ssh_to_sut.connect(sut_ctrl_ip, 22, username=sut_username, password=sut_password)
    ssh_to_sut.exec_command(command='numactl --cpunodebind=netdev:%s --membind=netdev:%s iperf3 -s -i 5 --forceflush 5|grep -i sum &' % (sut_devicename, sut_devicename))
    ssh_to_sut.close()
    #client iperf
    log_iperf = open(logname_result_iperf, mode="w")
    iperf_test_sut = subprocess.Popen("numactl --cpunodebind=netdev:%s --membind=netdev:%s iperf3 -c %s -t 100 -i 5 --forceflush 5 -P %s | grep -i sum" % (client_devicename, client_devicename, sut_test_ip, N) ,shell=True, stdout=log_iperf)
    iperf_test_sut.wait()
    log_iperf.close()
    #close iperf3 remotely
    ssh_to_sut.connect(sut_ctrl_ip, 22, username=sut_username, password=sut_password)
    ssh_to_sut.exec_command(command='killall -9 iperf3')
    ssh_to_sut.close()
sys.exit(0)
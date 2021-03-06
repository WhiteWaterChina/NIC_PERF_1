#!/tmp/tools/env/tops/bin/python
# -*- coding:utf-8 -*-
###usage: sut_devicename

import os
import json
import sys
import re
import paramiko
import subprocess

if len(sys.argv) != 2:
    print "Input length is incorrect!"
    print "Usage:%s sut_devicename" % sys.argv[0]
    sys.exit(1)

sut_devicename = sys.argv[1]

#ethtool -S

path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'Lib_testcase'))
sys.path.append(path)


class parse(object):
    def __init__(self):
        self.log_dir_prefix = file('/tmp/tools/name').readlines()[0].strip()
        self.log_dir_prefix = self.log_dir_prefix + "/Stress/NIC_PERF_1"
        if not os.path.isdir(self.log_dir_prefix):
            os.makedirs(self.log_dir_prefix)
        self.tc_result_log = self.log_dir_prefix + "/tc_result.log"


    def get_data(self):
        #check ethtool -S result
        tc_result = {}
        tc_result["total_result"] = "fail"
        tc_result["ethtool_s_result"] = {}
        tc_result["ethtool_s_result"]["result"] = "fail"
        ethtool_s_temp = subprocess.Popen('ethtool -S %s|grep -iE "err|fail|drop|lost"' % sut_devicename, shell=True, stdout=subprocess.PIPE).stdout.readlines()
        for item_ethtool in ethtool_s_temp:
            name_error = item_ethtool.split(":")[0].strip()
            number_error = item_ethtool.split(":")[1].strip()
            if int(number_error) > 0:
                tc_result["ethtool_s_result"]["%s" % name_error] = number_error
        if len(tc_result["ethtool_s_result"]) == 1:
            tc_result["ethtool_s_result"]["result"] = "pass"
        #check lspci result
        #get pcie number
        pcie_bus = subprocess.Popen("ethtool -i %s|grep 'bus-info'|awk '{match($0,/([0-9]+:[0-9]+\.[0-9]+)/,a);print a[1]}'" % sut_devicename, shell=True,stdout=subprocess.PIPE).stdout.readlines()[0].strip()
        tc_result["lspci_vvv"] = {}
        tc_result["lspci_vvv"]["result"] = "fail"
        lspci_result = subprocess.Popen('lspci -vvv -s %s|grep -E "UESta|CESta"|grep +' % pcie_bus, shell=True, stdout=subprocess.PIPE).stdout.readlines()
        if len(lspci_result) == 0:
            tc_result["lspci_vvv"]["result"] = "pass"
        else:
            for item_lspci in lspci_result:
                name_item = item_lspci.split(":")[0].strip()
                error_info = item_lspci.split(":")[1].strip()
                tc_result["lspci_vvv"]["%s" % name_item] = {}
                pattern_error = re.compile(r"(\w*)\+")
                name_error = re.findall(pattern=pattern_error, string=error_info)
                for item_error in name_error:
                    tc_result["lspci_vvv"]["%s" % name_item]["%s" % item_error] = "+"
        #check dmesg
        # get driver name
        sut_driver_name = subprocess.Popen("ethtool -i %s|grep driver|awk -F ':' '{print $2}'" % sut_devicename, shell=True,stdout=subprocess.PIPE).stdout.readlines()[0].strip()
        tc_result["dmesg_result"] = {}
        tc_result["dmesg_result"]["result"] = "fail"
        dmesg_result = subprocess.Popen('dmesg|grep -E "%s|%s" |grep -iE "fail|err|warn|unsupport"' % (pcie_bus, sut_driver_name), shell=True, stdout=subprocess.PIPE).stdout.readlines()
        if len(dmesg_result) == 0:
            tc_result["dmesg_result"]["result"] = "pass"
        else:
            dmesg_error_list = []
            for item_dmesg in dmesg_result:
                dmesg_error_info = item_dmesg.strip()
                dmesg_error_list.append(dmesg_error_info)
            error_info_write = ";".join(dmesg_error_list)
            tc_result["dmesg_result"]["error_info"] = error_info_write
        #generate total result
        if tc_result["ethtool_s_result"]["result"] == "pass" and tc_result["lspci_vvv"]["result"] == "pass" and tc_result["dmesg_result"]["result"] == "pass":
            tc_result["total_result"] = "pass"
        #change to json
        data_string = json.dumps(tc_result, sort_keys=True, indent=4)

        with open(self.tc_result_log, mode="w") as f:
            f.write(data_string)
        return data_string, tc_result["total_result"], self.tc_result_log

if __name__ == "__main__":
    parse = parse()
    data,total_result,tar_path = parse.get_data()
    print data
    print total_result





